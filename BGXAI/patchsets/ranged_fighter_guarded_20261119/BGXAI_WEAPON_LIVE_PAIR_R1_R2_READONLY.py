#!/usr/bin/env python3
"""BGXAI: deterministic offline pairing of installed passive R1/R2 traces.

SOURCE ONLY. No game integration, write into game, WeiDU, Lua, actions, dispatch,
APR conversion, or unproven quickslot scoring. Accepts captured source data only.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from collections import Counter

SCHEMA_R1 = 'BGXAI_WEAPON_RUNTIME_RAW_R1'
SCHEMA_R2 = 'BGXAI_WEAPON_SLOTS_RAW_R2'
MAX_FILE = 2_000_000
R1_MARKER = re.compile(r'\[BGXWP\] (\{.+\})\s*$')
R2_MARKER = re.compile(r'\[BGXW2\] (\{.+\})\s*$')
WEAPONS = (35, 36, 37, 38)
QUIVERS = (11, 12, 13, 14)
FORBIDDEN_R1_TRUE = (
    'weaponAbilityVerified', 'actualPerSlotAPRVerified',
    'buffsExhaustivelyObserved', 'manualOrderOriginVerified',
    'epsQueueVerified', 'weaponSwitchAuthorized'
)
FORBIDDEN_R2_TRUE = (
    'itemIdentityVerified', 'perSlotAPRVerified',
    'manualOrderOriginVerified', 'epsQueueVerified', 'switchAuthorized'
)

class EvidenceError(ValueError):
    pass


def regular_bytes(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise EvidenceError('UNTRUSTED_OR_MISSING_INPUT')
    size = path.stat().st_size
    if size < 1 or size > MAX_FILE:
        raise EvidenceError('INPUT_SIZE_HOLD')
    payload = path.read_bytes()
    if len(payload) != size or path.stat().st_size != size:
        raise EvidenceError('INPUT_CHANGED_DURING_READ')
    return payload


def _isint(value, lower, upper):
    return type(value) is int and lower <= value <= upper


def _valid_slot(s, index):
    if not isinstance(s, dict) or s.get('index') != index:
        return False
    if s.get('identityVerified') is not False or s.get('usableVerified') is not False or s.get('ammoVerified') is not False:
        return False
    ref=s.get('resrefRaw')
    if ref is not None and (not isinstance(ref,str) or not re.fullmatch(r'[A-Za-z0-9_]{1,8}',ref)):
        return False
    if s.get('access') not in ('NULL', 'OBJECT_RETURNED_UNVERIFIED'):
        return False
    if s['access']=='NULL' and ref is not None:
        return False
    if s['access']=='OBJECT_RETURNED_UNVERIFIED' and ref is None:
        return False
    for n in range(1,4):
        v=s.get(f'useCount{n}Raw')
        if v is not None and not _isint(v,0,65535):
            return False
    return True


def _checked_r2(event):
    if not isinstance(event,dict) or event.get('type')!='SLOTS' or event.get('schema')!=SCHEMA_R2:
        raise EvidenceError('R2_EVENT_KIND_INVALID')
    if not _isint(event.get('seq'),1,64) or not _isint(event.get('actor'),0,2147483647) or not _isint(event.get('partyIndex'),0,5):
        raise EvidenceError('R2_ID_OR_SEQUENCE_INVALID')
    if not _isint(event.get('actionRaw'),0,65535) or not _isint(event.get('selectedWeaponRaw'),0,65535):
        raise EvidenceError('R2_ACTION_OR_SELECTION_INVALID')
    if not _isint(event.get('selectedAbilityRaw'),0,65535):
        raise EvidenceError('R2_ABILITY_INVALID')
    if any(event.get(k) is not False for k in FORBIDDEN_R2_TRUE):
        raise EvidenceError('R2_UNPROVEN_FIELD_CLAIM')
    if event.get('status') != 'RAW_FIXED_SLOTS_OBSERVED_IDENTITY_UNKNOWN':
        raise EvidenceError('R2_NOT_RAW_ONLY')
    w,q=event.get('quickWeapons'),event.get('quivers')
    if not isinstance(w,list) or len(w)!=4 or not all(_valid_slot(s,i) for s,i in zip(w,WEAPONS)):
        raise EvidenceError('R2_WEAPON_SLOTS_INVALID')
    if not isinstance(q,list) or len(q)!=4 or not all(_valid_slot(s,i) for s,i in zip(q,QUIVERS)):
        raise EvidenceError('R2_QUIVER_SLOTS_INVALID')
    if not _valid_slot(event.get('offhand'),9):
        raise EvidenceError('R2_OFFHAND_INVALID')
    return event


def _checked_r1(event):
    if not isinstance(event,dict) or event.get('type')!='ACTION':
        raise EvidenceError('R1_EVENT_KIND_INVALID')
    if not _isint(event.get('sequence'),1,320) or not _isint(event.get('actor'),0,2147483647):
        raise EvidenceError('R1_ID_OR_SEQUENCE_INVALID')
    if not _isint(event.get('action'),0,65535) or not _isint(event.get('partyIndex'),0,5):
        raise EvidenceError('R1_ACTION_INVALID')
    if not _isint(event.get('selectedWeaponRaw'),0,65535):
        raise EvidenceError('R1_SELECTION_INVALID')
    if any(event.get(k) is not False for k in FORBIDDEN_R1_TRUE):
        raise EvidenceError('R1_UNPROVEN_FIELD_CLAIM')
    return event


def _extract_session(events,schema,kind,seq_key,ready_key,source):
    session=False;ready=False;actions={}
    for e in events:
        if not isinstance(e,dict):continue
        if e.get('type')=='SESSION' and e.get('schema')==schema and e.get('readOnly') is True:
            session=True;ready=False;actions={}
        elif e.get('type')=='READY' and e.get('schema')==schema and e.get(ready_key) is True and session:
            ready=True
        elif e.get('type')==kind and e.get('schema', schema)==schema and ready:
            checked = (_checked_r1(e) if kind=='ACTION' else _checked_r2(e))
            seq=checked[seq_key]
            if seq in actions and actions[seq]!=checked:
                raise EvidenceError(source+'_CONFLICTING_SEQUENCE')
            actions[seq]=checked
    if not session or not ready or not actions:
        raise EvidenceError(source+'_SESSION_READY_ACTIONS_MISSING')
    ids=sorted(actions)
    if ids != list(range(1,len(ids)+1)):
        raise EvidenceError(source+'_SEQUENCE_GAP')
    return actions


def read_r2(raw_file:Path):
    raw=regular_bytes(raw_file)
    try:events=[json.loads(line) for line in raw.decode('utf-8-sig').splitlines()]
    except (UnicodeError,ValueError) as exc:raise EvidenceError('R2_JSONL_MALFORMED') from exc
    return _extract_session(events,SCHEMA_R2,'SLOTS','seq','hookRegistered','R2')


def read_r1_console(console_file:Path):
    raw=regular_bytes(console_file)
    events=[]
    for line in raw.decode('utf-8','replace').splitlines():
        m=R1_MARKER.search(line)
        if not m:continue
        try:events.append(json.loads(m.group(1)))
        except ValueError:raise EvidenceError('R1_CONSOLE_JSON_MALFORMED')
    return _extract_session(events,SCHEMA_R1,'ACTION','sequence','observerRegistered','R1')


def pair(r1, r2):
    if not r1 or not r2 or set(r1)!=set(r2):
        raise EvidenceError('R1_R2_SEQUENCE_SET_MISMATCH')
    out=[]
    previous=None
    for seq in sorted(r2):
        s=r2[seq];a=r1[seq]
        if (s['actor'],s['partyIndex'],s['actionRaw'],s['selectedWeaponRaw']) != (a['actor'],a['partyIndex'],a['action'],a['selectedWeaponRaw']):
            raise EvidenceError('R1_R2_MISMATCH_AT_'+str(seq))
        if a.get('aprRaw') is not None and not _isint(a['aprRaw'],-500,500):
            raise EvidenceError('R1_APR_RAW_INVALID')
        selected = s['selectedWeaponRaw']
        if selected in WEAPONS:
            slot=next(x for x in s['quickWeapons'] if x['index']==selected)
            selected_kind='WEAPON_SLOT'
        elif selected in QUIVERS:
            slot=next(x for x in s['quivers'] if x['index']==selected)
            selected_kind='AMMO_SLOT_LAUNCHER_UNVERIFIED'
        else:
            slot=None;selected_kind='OTHER_SLOT_UNRESOLVED'
        ammo_counts={str(x['index']):x['useCount1Raw'] for x in s['quivers'] if x['resrefRaw'] is not None}
        delta=None
        if previous is not None:
            delta={key:ammo_counts.get(key)-previous['ammoCount1Raw'].get(key) for key in set(ammo_counts)&set(previous['ammoCount1Raw'])}
            delta={key:change for key,change in delta.items() if change != 0}
        rec={'seq':seq,'actor':s['actor'],'partyIndex':s['partyIndex'],'actionRaw':s['actionRaw'],
             'selectedSlotRaw':selected,'selectedKind':selected_kind,
             'selectedResrefRaw':slot['resrefRaw'] if slot else None,
             'aprRaw':a.get('aprRaw'),'thac0Raw':a.get('thac0Raw'),
             'strengthRaw':a.get('strengthRaw'),'dexRaw':a.get('dexRaw'),
             'improvedHasteRaw':a.get('improvedHasteRaw'),
             'ammoCount1Raw':ammo_counts, 'ammoCountDeltaSincePrevious':delta,
             'selectedItemIdentityVerified':False,'selectedLauncherForAmmoVerified':False,
             'effectiveOtherSlotsAprVerified':False,'manualOrderProven':False,
             'epsQueueProvenEmpty':False,'dispatchAuthorized':False}
        out.append(rec);previous=rec
    transitions=[]
    for p,c in zip(out,out[1:]):
        if p['selectedSlotRaw']!=c['selectedSlotRaw']:
            transitions.append({'atSequence':c['seq'],'from':p['selectedSlotRaw'],'to':c['selectedSlotRaw'],
                                'aprRawFrom':p['aprRaw'],'aprRawTo':c['aprRaw']})
    first=r2[min(r2)]
    gear={'quickWeapons':[{'index':x['index'],'resrefRaw':x['resrefRaw']} for x in first['quickWeapons']],
          'quivers':[{'index':x['index'],'resrefRaw':x['resrefRaw']} for x in first['quivers']],
          'offhand':{'index':first['offhand']['index'],'resrefRaw':first['offhand']['resrefRaw']}}
    # A resref mutation means the prior gear snapshot cannot be used as one loadout.
    loadout_resrefs_consistent=all(
        [(x['index'],x['resrefRaw']) for x in e['quickWeapons']]==[(x['index'],x['resrefRaw']) for x in first['quickWeapons']] and
        [(x['index'],x['resrefRaw']) for x in e['quivers']]==[(x['index'],x['resrefRaw']) for x in first['quivers']] and
        e['offhand']['resrefRaw']==first['offhand']['resrefRaw']
        for e in r2.values())
    selected_stats_by_raw={}
    for x in out:
        key=str(x['selectedSlotRaw'])
        selected_stats_by_raw.setdefault(key,[]).append({'seq':x['seq'],'aprRaw':x['aprRaw'],
                                                          'resrefRaw':x['selectedResrefRaw']})
    return {'status':'R1_R2_LIVE_PAIRED_READONLY','pairedActions':len(out),
            'actor':first['actor'],'portraitIndex':first['partyIndex'],
            'loadoutResrefsConstantAcrossSnapshots':loadout_resrefs_consistent,
            'gearSnapshotRaw':gear,'selectedSlotTransitions':transitions,
            'selectedSnapshotsBySlotRaw':selected_stats_by_raw,
            'ammoCountChanges':[{'seq':x['seq'],'counts':x['ammoCountDeltaSincePrevious']}
                                for x in out if x['ammoCountDeltaSincePrevious']],
            'observations':out,
            'aprRawEncodingVerified':False,'launcherAmmoAbilityMatched':False,
            'effectivePerSlotAPRVerified':False,'activeBuffsComplete':False,
            'targetDefenseVerified':False,'manualAndEPSQueueStateVerified':False,
            'perWeaponDamageVerified':False,'weaponSwitchAuthorized':False,
            'executable':False,'dispatchAuthorized':False,
            'next':'Read installed ITM abilities, selected launcher+ammo mapping and EPS/manual queue provenance; never infer all-slot APR from current selected APR.'}


def audit_files(raw_r2_file:Path,console_file:Path):
    return pair(read_r1_console(console_file),read_r2(raw_r2_file))

if __name__ == '__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('raw_r2_file',type=Path);p.add_argument('console_log',type=Path)
    args=p.parse_args()
    print(json.dumps(audit_files(args.raw_r2_file,args.console_log),indent=2,ensure_ascii=False))
