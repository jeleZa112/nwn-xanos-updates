#!/usr/bin/env python3
"""R28: read-only bridge from *real installed* R27 capture to native ITM/2DA audit.

Game files are read, never edited. This is NOT an action dispatcher or an APR
predictor. The old R3 native parser is imported only after a pinned SHA check.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
from datetime import datetime, timezone

R3_NAME = 'BGXAI_WEAPON_NATIVE_ITM_R3_RO.py'
R3_SHA256 = 'ed87a7a6618826c6d3901d2579a39bf280fcaeb09cd18b7b6ee159b9ebfcc74a'
R27_SCHEMA = 'BGXAI_R27_SINGLE_CALLBACK_SELECTED_RO_V1'
ITEM_RE = re.compile(r'[A-Z0-9_#\-]{1,8}\Z')
MAX_LOG_BYTES = 20_000_000
MAX_EVENTS = 64

class StopReadOnly(ValueError):
    pass


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_r3(folder: Path):
    p = folder/R3_NAME
    if p.is_symlink() or not p.is_file() or p.stat().st_size != 18641:
        raise StopReadOnly('PINNED_R3_SOURCE_MISSING_OR_SIZE')
    if sha(p.read_bytes()) != R3_SHA256:
        raise StopReadOnly('PINNED_R3_SOURCE_SHA_MISMATCH')
    spec = importlib.util.spec_from_file_location('bgxai_r3_verified_source',p)
    if spec is None or spec.loader is None:
        raise StopReadOnly('R3_IMPORT_UNAVAILABLE')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _positive_exact_int(v,lo,hi):
    return type(v) is int and lo <= v <= hi


def capture_extract(raw:bytes) -> dict:
    if not 0 < len(raw) <= MAX_LOG_BYTES:
        raise StopReadOnly('R27_LOG_LENGTH_INVALID')
    samples=[]
    session_count=0
    names=set()
    actors=set()
    for line in raw.splitlines():
        if b'[BGXR27] ' not in line:
            continue
        marker=line.split(b'[BGXR27] ',1)[1]
        if len(marker)>12000:
            raise StopReadOnly('R27_EVENT_OVERSIZE')
        try:
            rec=json.loads(marker)
        except (ValueError, UnicodeError):
            raise StopReadOnly('R27_EVENT_JSON_INVALID')
        if not isinstance(rec,dict) or rec.get('schema')!=R27_SCHEMA:
            raise StopReadOnly('R27_SCHEMA_DRIFT')
        if rec.get('type')=='SESSION':
            session_count+=1
            if session_count>1 or samples:
                raise StopReadOnly('R27_SESSION_AMBIGUOUS')
            continue
        if rec.get('type')!='R27_SINGLE_CALLBACK':
            continue
        if session_count!=1:
            raise StopReadOnly('R27_ACTION_BEFORE_SESSION')
        seq,actor=rec.get('seq'),rec.get('actor')
        if not _positive_exact_int(seq,1,MAX_EVENTS) or seq!=len(samples)+1:
            raise StopReadOnly('R27_NONCONTIGUOUS_SEQ')
        if not _positive_exact_int(actor,0,2147483647):
            raise StopReadOnly('R27_ACTOR_INVALID')
        actors.add(actor)
        if len(actors)>6:
            raise StopReadOnly('R27_TOO_MANY_ACTORS')
        if (rec.get('status')!='CURRENT_SELECTED_SAME_CALLBACK_SOURCE_CANDIDATE'
                or rec.get('sameLuaListenerInvocation') is not True
                or rec.get('ordersSent')!=0 or rec.get('localsWritten')!=0
                or rec.get('dispatchAuthorized') is not False
                or rec.get('weaponSwitchAuthorized') is not False
                or rec.get('readOnly') is not True):
            raise StopReadOnly('R27_CALLBACK_NOT_SAFE_OR_NOT_MATCHED')
        w,q=rec.get('quickWeaponsRaw'),rec.get('quiversRaw')
        if not isinstance(w,list) or not isinstance(q,list) or len(w)!=4 or len(q)!=4:
            raise StopReadOnly('R27_LOADOUT_INCOMPLETE')
        for i,record in enumerate(w+q):
            slot=35+i if i<4 else 11+i-4
            if not isinstance(record,dict) or record.get('slot')!=slot:
                raise StopReadOnly('R27_LOADOUT_SLOT_MISMATCH')
            rr=record.get('resrefRaw')
            if rr is None:
                continue
            if not isinstance(rr,str) or not ITEM_RE.fullmatch(rr):
                raise StopReadOnly('R27_RAW_ITEM_RESREF_INVALID')
            names.add(rr)
        samples.append({'sequence':seq,'actorRaw':actor,
                        'actionRaw':rec.get('actionRaw'),
                        'selectedSlotRaw':rec.get('selectedWeaponRaw'),
                        'selectedAbilityRaw':rec.get('selectedAbilityRaw'),
                        'selectedAprKeyRaw':rec.get('selectedAprKeyRaw')})
    if session_count!=1 or not samples:
        raise StopReadOnly('R27_LIVE_SESSION_OR_ACTION_MISSING')
    if len(names)==0 or len(names)>48:
        raise StopReadOnly('R27_ITEM_SET_UNAVAILABLE')
    return {'schema':'BGXAI_R28_R27_LIVE_INPUT_V1', 'sourceSha256':sha(raw),
            'r27SessionMarkers':session_count,'r27ConfirmedCallbacks':len(samples),
            'actorCount':len(actors),'observedRawItemResrefs':sorted(names),
            'samplesSelectedOnly':samples,'gameModified':False,
            'effectiveAlternateAPRVerified':False,
            'manualAndEPSQueueVerified':False, 'dispatchAuthorized':False,
            'weaponSwitchAuthorized':False}


def find_capture(reports:Path)->Path:
    if reports.is_symlink() or not reports.is_dir():
        raise StopReadOnly('R27_REPORT_DIRECTORY_MISSING_OR_LINK')
    captures=[]
    for p in reports.glob('BGXAI_R27_CONSOLE_*.log'):
        if p.is_symlink() or not p.is_file():
            raise StopReadOnly('R27_CAPTURE_UNSAFE_LINK')
        if not 0 < p.stat().st_size <= MAX_LOG_BYTES:
            raise StopReadOnly('R27_CAPTURE_UNSAFE_SIZE')
        captures.append(p)
        if len(captures)>100:
            raise StopReadOnly('R27_CAPTURE_TOO_MANY_FILES')
    if not captures:
        raise StopReadOnly('R27_CAPTURE_FILE_MISSING')
    return max(captures,key=lambda p:(p.stat().st_mtime,p.name))


def native_audit(root:Path,installed_status:dict,process_check,
                 reports:Path|None=None,r3=None) -> dict:
    if not isinstance(installed_status,dict) or installed_status.get('status')!='R27_PASSIVE_INSTALLED_AWAITING_RUNTIME_TEST':
        raise StopReadOnly('R27_NOT_INSTALLED_OR_NOT_LAST')
    process_check()  # no simultaneous game or WeiDU resource changes
    if reports is None:
        home=os.environ.get('USERPROFILE')
        if not home:
            raise StopReadOnly('USERPROFILE_MISSING')
        docs=Path(home)/'Documents'
        if docs.is_symlink():
            raise StopReadOnly('DOCUMENTS_REPARSE')
        reports=docs/'BGXAI_LIVE_REPORTS'
    source_file=find_capture(reports)
    snapshot=capture_extract(source_file.read_bytes())
    if r3 is None:
        r3=source_r3(Path(__file__).resolve().parent)
    source=r3.NativeSource(root)
    native=r3.audit(source,snapshot['observedRawItemResrefs'],
                    {'source':'R27_USER_REAL_LIVE',
                     'captureSha256':snapshot['sourceSha256'],
                     'sampleCount':snapshot['r27ConfirmedCallbacks']})
    # Raw R3 ITM/2DA results only: no dynamically effective APR or current buffs.
    result={'schema':'BGXAI_R28_NATIVE_FROM_R27_RO_V1',
            'status':'R28_NATIVE_ITEMS_RAW_READ_AWAITING_REVIEW' if native['status']=='ITM_NATIVE_ALL_ITEMS_RAW_READ'
                     else 'R28_NATIVE_ITEMS_PARTIAL_HOLD',
            'captureFileName':source_file.name,'captureSha256':snapshot['sourceSha256'],
            'liveR27Evidence':snapshot,'nativeAudit':native,
            'gameModified':False,'ordersSent':0,
            'gameplayActionOriginVerified':False,'manualAndEPSQueueVerified':False,
            'effectiveAlternateAPRVerified':False,'launcherAmmoPairVerified':False,
            'weaponSwitchAuthorized':False,'dispatchAuthorized':False}
    out=reports/('BGXAI_R28_NATIVE_FROM_R27_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json')
    if out.is_symlink() or out.exists():
        raise StopReadOnly('R28_REPORT_COLLISION')
    # Fail closed; source bytes are data, never executed. Report outside game.
    with out.open('x',encoding='utf-8',newline='\n') as handle:
        json.dump(result,handle,ensure_ascii=False,indent=2)
        handle.write('\n')
    return {'schema':result['schema'],'status':result['status'],'reportFile':str(out),
            'captureSha256':snapshot['sourceSha256'],
            'r27Samples':snapshot['r27ConfirmedCallbacks'],
            'itemsRead':len(native['items']),
            'missingItemsOrLinkedSpells':len(native['missingItemsOrLinkedSpells']),
            'gameModified':False,'weaponSwitchAuthorized':False,
            'dispatchAuthorized':False}
