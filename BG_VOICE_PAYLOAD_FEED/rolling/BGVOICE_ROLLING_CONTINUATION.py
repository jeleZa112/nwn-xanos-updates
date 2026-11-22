"""BG Voice RU: read-only-source second-pass staging and next 24 voice A/B.

Import from the existing one updater; do not call as a standalone updater.
This module never installs into game or modifies original audio. GitHub data are
unapproved proposals (V55/V57/V70/V74), not human hearing verdicts.
"""
from __future__ import annotations
import csv
import hashlib
import html
import io
import json
import os
from pathlib import Path, PureWindowsPath
import re
import tempfile
import wave

SOURCE_ROOT = Path(r'C:\BG_VOICE_RU_MASTER\08_VOXCPM2_ALL_CHARACTERS\RUSSIAN_WAV_TWO_VERSIONS')
OUTPUT_ROOT = Path.home() / 'Documents' / 'BG_VOICE_RU' / 'FULL_PRODUCTION'
CSV_613 = 'VOICE_BACKED_613_STAGE_ONLY.csv'
CSV_QA24 = 'NEXT24_VOICE_AB_SHA_GATED.csv'
SID = re.compile(r'[A-Z0-9]{4,16}\Z')
CHAR = re.compile(r'[A-Za-z0-9_]{3,120}\Z')
HEX = re.compile(r'[0-9a-f]{64}\Z')
BLOCK = {'OH85856','OH80404','OH89888','KORGAN57'}


def sha(data:bytes)->str:return hashlib.sha256(data).hexdigest()

def _safe_bytes(path: Path, expected: str, max_bytes=16*1024*1024):
    if not HEX.fullmatch(expected): raise ValueError('INVALID_EXPECTED_SHA')
    if path.is_symlink() or path.parent.is_symlink(): raise ValueError('SOURCE_SYMLINK_FORBIDDEN')
    if not path.is_file(): raise FileNotFoundError('SOURCE_ABSENT')
    if path.stat().st_size>max_bytes:raise ValueError('SOURCE_TOO_LARGE')
    b=path.read_bytes()
    if sha(b)!=expected: raise ValueError('SOURCE_SHA_MISMATCH')
    with wave.open(io.BytesIO(b),'rb') as w:
        if (w.getnchannels(),w.getsampwidth(),w.getframerate())!=(1,2,48000) or w.getnframes()==0:
            raise ValueError('SOURCE_NOT_MONO_PCM16_48K')
    return b


def _write_once(target:Path,data:bytes):
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.parent.is_symlink() or target.is_symlink():raise ValueError('TARGET_SYMLINK_FORBIDDEN')
    if target.exists():
        if target.is_file() and sha(target.read_bytes())==sha(data):return 'REUSED_SHA_VERIFIED'
        raise ValueError('EXISTING_TARGET_MISMATCH_NO_OVERWRITE')
    fd, temp=tempfile.mkstemp(prefix='._BGVOICE_',suffix='.partial',dir=target.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
        if sha(Path(temp).read_bytes())!=sha(data):raise ValueError('COPY_SHA_MISMATCH')
        # Atomic create-if-absent on NTFS/POSIX. os.rename may replace destination
        # in a race on POSIX; hard-link creation NEVER overwrites a path.
        try:
            os.link(temp, target)
        except FileExistsError:
            raise ValueError('CONCURRENT_STAGE_TARGET_EXISTS_NO_OVERWRITE')
        return 'STAGED_NOT_APPROVED'
    finally:
        if os.path.exists(temp):os.unlink(temp)


def _report_atomic(target:Path,blob:bytes):
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.parent.is_symlink() or target.is_symlink():raise ValueError('REPORT_SYMLINK_FORBIDDEN')
    fd,temp=tempfile.mkstemp(prefix='.bgvoice_report_',suffix='.partial',dir=target.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(blob);f.flush();os.fsync(f.fileno())
        os.replace(temp,target)
    finally:
        if os.path.exists(temp):os.unlink(temp)


def _csv(blob:bytes):return list(csv.DictReader(io.StringIO(blob.decode('utf-8-sig'))))

def _as_csv(rows,fields):
    s=io.StringIO(newline='');w=csv.DictWriter(s,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)
    return s.getvalue().encode('utf-8-sig')


def _read_manifest(folder:Path):
    m=json.loads((folder/'MANIFEST.json').read_text(encoding='utf-8'))
    if m['schema']!='BGVOICE_ROLLING_SECOND_PASS_V1' or m['staging_count']!=613 or m['additional_ab']!=24:
        raise ValueError('UNEXPECTED_BATCH_MANIFEST')
    rows={}
    for name in (CSV_613,CSV_QA24):
        b=(folder/name).read_bytes();proof=m['files'][name]
        if sha(b)!=proof['sha256'] or len(b)!=proof['bytes']:raise ValueError('MANIFEST_FILE_HASH_FAIL:'+name)
        rows[name]=_csv(b)
    if len(rows[CSV_613])!=613 or len(rows[CSV_QA24])!=24:raise ValueError('COUNT_MISMATCH')
    one={r['sound_id'] for r in rows[CSV_613]};two={r['sound_id'] for r in rows[CSV_QA24]}
    if len(one)!=613 or len(two)!=24 or one&two:raise ValueError('DUPLICATE_OR_OVERLAPPING_IDS')
    if one&BLOCK:raise ValueError('PROTECTED_ID_IN_STAGE')
    return m,rows


def _name(char:str,sid:str,mode:str,source_root:Path):
    if not SID.fullmatch(sid) or not CHAR.fullmatch(char) or mode not in ('STABLE','PER_LINE'):
        raise ValueError('BAD_ID_CHARACTER_OR_MODE')
    return source_root/char/(sid+'__'+mode.lower()+'_RU.wav')


def _assert_safe_output(source_root:Path,output_root:Path, *,tests:bool=False):
    s=source_root.resolve();d=output_root.resolve()
    if d==s or s in d.parents or d in s.parents:raise ValueError('STAGE_SOURCE_OVERLAP')
    if not tests:
        ds=str(d).casefold().replace('/','\\')
        if '\\games\\' in ds or '\\russian_wav_two_versions' in ds:
            raise ValueError('STAGE_CANNOT_WRITE_TO_GAME_OR_SOURCE')
        if 'bg_voice_ru' not in ds or 'full_production' not in ds:
            raise ValueError('STAGE_OUTSIDE_FULL_PRODUCTION')
    if output_root.is_symlink(): raise ValueError('STAGE_ROOT_SYMLINK_FORBIDDEN')


def _sort_blind(sid:str):
    # deterministic A/B label, not dependent on ASR/voice scores
    stable_a=(hashlib.sha256(sid.encode('ascii')).digest()[0]&1)==0
    return {'A':'STABLE' if stable_a else 'PER_LINE','B':'PER_LINE' if stable_a else 'STABLE'}


def _run(folder:Path,source_root:Path,output_root:Path, *,max_items=None, tests=False):
    manifest, data=_read_manifest(folder)
    _assert_safe_output(source_root,output_root,tests=tests)
    folder_out=output_root/'VOICE_BACKED_SECOND_PASS'
    result=[]
    batch=data[CSV_613] if max_items is None else data[CSV_613][:max_items]
    for r in batch:
        sid=r['sound_id']; status='HOLD';reason='';path=''
        try:
            if r['stage_only']!='YES' or r['game_install_ready']!='NO' or r['source_provenance']!='V55_SHA_V5_VOICE_DELTA_V57_ASR':raise ValueError('UNSAFE_PROVENANCE_FLAGS')
            b=_safe_bytes(_name(r['character'],sid,r['mode'],source_root),r['expected_sha256'])
            p=folder_out/(sid+'__'+r['mode']+'__NOT_APPROVED.wav')
            status=_write_once(p,b);path=str(p)
        except (OSError,ValueError,KeyError,wave.Error) as e:reason=(type(e).__name__+': '+str(e))[:200]
        result.append(dict(sound_id=sid,status=status,reason=reason,staged_path=path,approved='NO'))
    # QA AB wave candidates are produced independently even if some stage files HOLD.
    reviews=[];mapping={}
    for r in data[CSV_QA24]:
        sid=r['sound_id']; state='HOLD';detail='';pairs={};tags=_sort_blind(sid)
        try:
            if r['human_approval']!='REQUIRED' or r['do_not_switch_automatically']!='YES' or r['ready_for_game']!='NO':raise ValueError('QA_UNSAFE_FLAGS')
            for label,mode in tags.items():
                proof=r['stable_sha256'] if mode=='STABLE' else r['per_line_sha256']
                b=_safe_bytes(_name(r['character'],sid,mode,source_root),proof)
                pairs[label]=b
            for label,b in pairs.items():_write_once(output_root/'VOICE_AB_NEXT24'/label/(sid+'.wav'),b)
            mapping[sid]=tags;state='READY_FOR_HUMAN_AB'
        except (OSError,ValueError,KeyError,wave.Error) as e:detail=(type(e).__name__+': '+str(e))[:200]
        reviews.append(dict(sound_id=sid,character=r['character'],priority=r['priority'],status=state,detail=detail))
    report_dir=output_root/'VOICE_AB_NEXT24'
    report_dir.mkdir(parents=True,exist_ok=True)
    html_out=['<!doctype html><html lang="ru"><meta charset="utf-8"><title>BG Voice RU — ещё 24 реплики</title>',
        '<style>body{font:16px/1.45 system-ui;max-width:920px;margin:auto;padding:18px}section{padding:15px 0;border-bottom:1px solid #bbb}audio{width:360px;max-width:100%}</style>',
        '<h1>24 реплики — проверка голоса, эмоции, затем ударений</h1>',
        '<p>Приоритет — узнаваемость персонажа и актёрская подача. Не утверждать по метрикам. KORGAN57 требует проверки исторической защиты Per_line. Не устанавливает ничего в игру.</p>']
    for r in reviews:
        sid=html.escape(r['sound_id']);html_out.append('<section><strong>'+sid+'</strong> — '+html.escape(r['character']))
        if r['status']=='READY_FOR_HUMAN_AB':
            for label in 'AB':html_out.append('<p>'+label+': <audio controls preload="none" src="'+label+'/'+sid+'.wav"></audio></p>')
            for label in ['A','B','HOLD']:
                html_out.append('<label><input type="radio" name="'+sid+'" value="'+label+'">'+label+'</label> ')
        else:html_out.append('<p>HOLD: '+html.escape(r['detail'])+'</p>')
        html_out.append('</section>')
    html_out.append('<button onclick="copyChoices()">Скопировать оценки</button><script>function copyChoices(){let t="sound_id,choice";for(let id of '+json.dumps([r['sound_id'] for r in reviews])+'){let e=document.querySelector(`input[name="${id}"]:checked`);if(e)t+="\\n"+id+","+e.value;}if(navigator.clipboard)navigator.clipboard.writeText(t).then(()=>alert("Скопировано"),()=>prompt("Скопируйте:",t));else prompt("Скопируйте:",t);}</script></html>')
    _report_atomic(report_dir/'OPEN_REVIEW.html',''.join(html_out).encode('utf-8'))
    _report_atomic(report_dir/'PRIVATE_AB_MAPPING.json',json.dumps(mapping,ensure_ascii=False,indent=2).encode('utf-8'))
    _report_atomic(report_dir/'QA_STATUS.csv',_as_csv(reviews,list(reviews[0])))
    _report_atomic(folder_out/'STAGING_STATUS.csv',_as_csv(result,list(result[0])))
    summary=dict(schema='BGVOICE_ROLLING_CONTINUATION_RESULTS_V1',source_manifest_sha256=sha((folder/'MANIFEST.json').read_bytes()),stage_total=len(batch),stage_status_counts={k:sum(i['status']==k for i in result) for k in sorted(set(i['status'] for i in result))},qa24_ready=sum(i['status']=='READY_FOR_HUMAN_AB' for i in reviews),qa24_hold=sum(i['status']=='HOLD' for i in reviews),game_install_ready=0,game_modified=False,original_wavs_modified=False,voice_and_emotion_human_approved=0,outputs_for_main_report=[str(report_dir/'QA_STATUS.csv'),str(folder_out/'STAGING_STATUS.csv')])
    _report_atomic(output_root/'VOICE_CONTINUATION_STATUS.json',json.dumps(summary,ensure_ascii=False,indent=2).encode('utf-8'))
    return summary


def run(package_dir, *,max_items=None):
    """Use ONLY from main updater; source and output locations are fixed.

    Owns no CMD, does no model installation, never writes game content.
    """
    if max_items is not None and (type(max_items)!=int or not 1<=max_items<=613):raise ValueError('INVALID_MAX_ITEMS')
    return _run(Path(package_dir),SOURCE_ROOT,OUTPUT_ROOT,max_items=max_items,tests=False)