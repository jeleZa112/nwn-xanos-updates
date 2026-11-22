# BG Voice RU V70 1.2.0 -- project continuity, known rework quarantine.
# Never presents old blind A/B as fresh review, never changes game/master WAV.
from __future__ import annotations
import csv
import hashlib
import io
import json
import os
import shutil
import tempfile
import zipfile
from pathlib import Path

VERSION = '1.2.0'
ROOT = 'V70/'
RESULT_PREFIX = ROOT + 'PRODUCTION_GATE/'
OLD_AB = ROOT + 'QA_NEXT12/'
KNOWN_PILOT20_REWORK = {
    'CERND46': 'PILOT20_STRESS_REWORK: Russian белка/белке stress on first syllable',
    'HAERDA36': 'PILOT20_PRONUNCIATION_OR_STRESS_REWORK',
    'KAGAN05': 'PILOT20_PRONUNCIATION_OR_STRESS_REWORK',
    'OH80910': 'PILOT20_PRONUNCIATION_OR_STRESS_REWORK',
    'OH86758': 'PILOT20_PRONUNCIATION_OR_STRESS_REWORK',
    'VICONI58': 'PILOT20_PRONUNCIATION_OR_STRESS_REWORK',
}
KNOWN_ACTING_HOLD = {'CEFALD18': 'SUSPICIOUS_SCREAM_DURATION_1.76S_VS_12S_HUMAN_REVIEW_NOT_APPROVAL'}
# These 12 were already shown to the user in Nov 22 QA; not accepted.
OLD_AB_IDS = {'AERIE01','ALORA14','CERND46','CORAN37','OH91797','CEFALD18',
              'HAER2501','OH87140','IMOEN09','JAHEIR59','JANJAN08','KAGAN20'}


def _csv(data, fields):
    b = io.StringIO(newline='')
    writer=csv.DictWriter(b,fieldnames=fields,extrasaction='ignore',lineterminator='\r\n')
    writer.writeheader()
    writer.writerows(data)
    return b.getvalue().encode('utf-8-sig')


def _json(data):
    return (json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode('utf-8')


def _load_verified(report):
    with zipfile.ZipFile(report) as src:
        if src.testzip() is not None:
            raise ValueError('COMMON_REPORT_CRC_HOLD')
        embedded=src.read('V70/V70_ORIGINAL_PAYLOAD_SHA256_VERIFIED.zip')
        status=json.loads(src.read('V70/STATUS.json'))
        if hashlib.sha256(embedded).hexdigest()!=status['payload_sha256']:
            raise ValueError('V70_ORIGINAL_PAYLOAD_SHA_HOLD')
        old_status=json.loads(src.read(OLD_AB+'STATUS.json')) if OLD_AB+'STATUS.json' in src.namelist() else {}
        old_files=set(src.namelist())
    with zipfile.ZipFile(io.BytesIO(embedded)) as payload:
        if payload.testzip() is not None:
            raise ValueError('V70_EMBEDDED_PAYLOAD_CRC_HOLD')
        allrows=list(csv.DictReader(io.StringIO(payload.read('01_ALL_7206_PRIORITY_AND_PROTECTION.csv').decode('utf-8-sig'))))
        stage=list(csv.DictReader(io.StringIO(payload.read('02_SHA_GATED_BULK_STAGE.csv').decode('utf-8-sig'))))
        locks=list(csv.DictReader(io.StringIO(payload.read('05_USER_LOCKS_AND_CHOICES.csv').decode('utf-8-sig'))))
        cal=list(csv.DictReader(io.StringIO(payload.read('06_CALIBRATION_REVIEW_96.csv').decode('utf-8-sig'))))
    ids=[r['sound_id'] for r in allrows]
    if len(ids)!=7206 or len(set(ids))!=7206 or len(stage)!=420 or len(cal)!=96 or len(locks)!=52:
        raise ValueError('V70_REGISTRY_OR_PRIORITY_COUNT_HOLD')
    if not set(r['sound_id'] for r in stage).issubset(set(ids)):
        raise ValueError('V70_STAGE_IDS_NOT_IN_REGISTRY_HOLD')
    if len({r['sound_id'] for r in stage})!=420:
        raise ValueError('V70_STAGE_ID_DUPLICATION_HOLD')
    return allrows,stage,locks,old_status,old_files,status['payload_sha256']


def _produce(report):
    rows,stage,locks,old_status,old_files,payload_sha = _load_verified(report)
    locked={r['sound_id'] for r in locks}
    staged={r['sound_id'] for r in stage}
    if locked & staged:
        raise ValueError('PROTECTED_V70_STAGE_OVERLAP_HOLD')
    counters={}
    production=[]
    for r in rows:
        sid=r['sound_id']
        if sid in KNOWN_PILOT20_REWORK:
            state='KNOWN_PILOT20_DEFECT_REWORK'
            detail=KNOWN_PILOT20_REWORK[sid]
        elif sid in KNOWN_ACTING_HOLD:
            state='ACTING_DURATION_HOLD'
            detail=KNOWN_ACTING_HOLD[sid]
        elif sid in locked:
            state='PRESERVE_PRIOR_USER_DECISION'
            detail='MANUAL_LOCK_DO_NOT_REPLACE'
        elif sid in OLD_AB_IDS:
            state='PREVIOUS_AB_PRESENTED_NOT_APPROVED'
            detail='NO_REPEAT_AB_WITHOUT_EN_AND_PRIOR_FEEDBACK'
        elif sid in staged:
            state='STAGED_TECHNICALLY_NOT_APPROVED'
            detail='VERIFY_VOICE_ACTING_STRESS_WITH_EN_BEFORE_RELEASE'
        else:
            state='UNVERIFIED_NEEDS_PRODUCTION_QA'
            detail='NO_AUTO_APPROVAL'
        counters[state]=counters.get(state,0)+1
        production.append({'sound_id':sid,
                           'character':r.get('character',''),
                           'priority_lane':r.get('priority_lane',''),
                           'state':state,
                           'reason':detail,
                           'english_text':r.get('english_text',''),
                           'russian_game_text_UNCHANGED':r.get('russian_game_text_UNCHANGED','')})
    if len(production)!=7206:
        raise ValueError('PRODUCTION_COVERAGE_INCOMPLETE')
    status={
        'schema':'BGVOICE_V70_PRODUCTION_GATE_V1',
        'version':VERSION,
        'source_payload_sha256':payload_sha,
        'source_total_sound_ids':7206,
        'source_total_russian_wavs':14412,
        'technical_staged':420,
        'calibration_technical_only':96,
        'calibration_with_human_gold_labels':0,
        'preserved_user_lock_rows':len(locks),
        'prior_ab12': 'SUPERSEDED_NO_NEW_HUMAN_REVIEW_REQUEST',
        'prior_ab12_ids':sorted(OLD_AB_IDS),
        'known_pilot20_stress_rework':sorted(KNOWN_PILOT20_REWORK),
        'known_critical_acting_hold':sorted(KNOWN_ACTING_HOLD),
        'production_counts':counters,
        'auto_game_approvals':0,
        'game_write':False,
        'original_english_wav_in_previous_ab12':False,
        'next_action':'STOP_REPEATED_AB; RECOVER_EXISTING_HUMAN_DECISIONS_AND_ORIGINAL_EN_BEFORE_TARGETED_REPAIR; NEVER_INSTALL_UNVERIFIED_WAV',
    }
    old_status.update({'version':VERSION, 'superseded':True,
                       'human_review_requested':False,
                       'status':'HOLD_KNOWN_PRIOR_FEEDBACK_AND_MISSING_ORIGINAL_EN',
                       'note':'Do not use the old 12-pair HTML. CERND46 already failed stress in Pilot20, CEFALD18 has extreme scream duration. No new choices requested.'})
    new={RESULT_PREFIX+'STATUS.json':_json(status),
         RESULT_PREFIX+'FULL_7206_PROGRESS.csv':_csv(production,list(production[0].keys())),
         RESULT_PREFIX+'KNOWN_PILOT20_HOLDS.json':_json({
             'confirmed_history':KNOWN_PILOT20_REWORK,
             'newly_flagged_duration':KNOWN_ACTING_HOLD,
             'prior_manual_decisions':'protect all 52 rows; do not conflate earlier EN acting comparison choices with RU Stable/Per_line approvals'}),
         OLD_AB+'STATUS.json':_json(old_status)}
    return new,status


def _replace_atomic(report,replacements):
    fd,tmp=tempfile.mkstemp(prefix='BGVOICE_V70_GUARD_',suffix='.pending',dir=str(report.parent))
    os.close(fd)
    try:
        with zipfile.ZipFile(report) as old,zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED,compresslevel=4,allowZip64=True) as out:
            if old.testzip() is not None:
                raise ValueError('EXISTING_REPORT_BAD_CRC')
            for meta in old.infolist():
                if meta.filename in replacements or meta.filename.startswith(RESULT_PREFIX):
                    continue
                if meta.filename.endswith('/'):
                    out.writestr(meta,b'')
                else:
                    with old.open(meta) as src,out.open(meta,'w',force_zip64=True) as dest:
                        shutil.copyfileobj(src,dest,1024*1024)
            for name,data in sorted(replacements.items()):
                out.writestr(name,data)
        with zipfile.ZipFile(tmp) as done:
            if done.testzip() is not None or len(done.namelist())!=len(set(done.namelist())):
                raise ValueError('NEW_REPORT_NOT_UNIQUE_OR_CRC')
        os.replace(tmp,report)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)


def selftest():
    assert VERSION=='1.2.0'
    assert 'CERND46' in KNOWN_PILOT20_REWORK
    assert 'CEFALD18' in KNOWN_ACTING_HOLD
    assert len(OLD_AB_IDS)==12 and len(KNOWN_PILOT20_REWORK)==6
    assert _csv([{'sound_id':'CERND46'}],['sound_id']).endswith(b'CERND46\r\n')
    print('BG_VOICE_V70_CORE_SELFTEST_PASS')
    return 0


def run(host, *, mode='stage', limit=None):
    if set(host)!={'run_local'} or not callable(host['run_local']):
        raise RuntimeError('V70_UNEXPECTED_HOST')
    if mode not in ('stage','calibration') or (limit is not None and (type(limit) is not int or not 1<=limit<=420)):
        raise RuntimeError('V70_INVALID_MODE_OR_LIMIT')
    result=host['run_local'](mode=mode,limit=limit)
    try:
        path=Path.home()/'Documents'/'BG_VOICE_RU'/'FULL_PRODUCTION'/'SEND_TO_CHATGPT_BG_VOICE_RU.zip'
        if not path.is_file():raise FileNotFoundError('ONE_REPORT_NOT_FOUND')
        replacements,status=_produce(path)
        with zipfile.ZipFile(path) as z:
            existing=z.read(RESULT_PREFIX+'STATUS.json') if RESULT_PREFIX+'STATUS.json' in z.namelist() else b''
        if existing != replacements[RESULT_PREFIX+'STATUS.json']:
            _replace_atomic(path,replacements)
        print('V70_PRODUCTION_GATE:',VERSION,'7206 audited; 420 staged; old AB superseded; known stress HOLD; game unchanged',flush=True)
    except Exception as error:
        print('V70_PRODUCTION_GATE_HOLD:',type(error).__name__,str(error)[:160],flush=True)
    return result

if __name__=='__main__':
    raise SystemExit(selftest())