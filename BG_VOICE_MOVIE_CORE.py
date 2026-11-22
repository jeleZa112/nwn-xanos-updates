# BG Voice RU movie 1.1: recover SHA-matched extracted 37-group text into an actionable 22-group queue.
# One permanent CMD, one common report, no TTS and no game writes.
from __future__ import annotations
import csv
import hashlib
import io
import json
import os
import shutil
import tempfile
import zipfile
from collections import Counter
from pathlib import Path

MOVIE_CORE_VERSION = '1.1.0'
SCRIPT_JSON_SHA256 = '87d18d68ce2be6236e2bdb468dc0275c7f5f257714643b5cf9013c48f87a9ee4'
MOVIE_SEGMENTS = {'INTRO15F': 16, 'SODCIN01': 18, 'IWINTRO': 29}
PILOT_KNOWN = {'INTRO15F_G01','SODCIN01_G02','IWINTRO_G06'}
ROOT = 'VIDEO/SCRIPT_QA/'


def _json(obj):
    return (json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)+'\n').encode('utf-8')


def _csv(rows, keys):
    out=io.StringIO(newline='')
    wr=csv.DictWriter(out, fieldnames=keys, extrasaction='ignore',lineterminator='\r\n')
    wr.writeheader()
    wr.writerows(rows)
    return out.getvalue().encode('utf-8-sig')


def _verify_source(raw, selected):
    if not isinstance(raw, bytes) or hashlib.sha256(raw).hexdigest()!=SCRIPT_JSON_SHA256:
        raise ValueError('EXTRACTED_JSON_SHA_NOT_VERIFIED')
    source=json.loads(raw)
    groups=source.get('groups', [])
    if not isinstance(groups,list) or len(groups)!=37 or source.get('segments')!=63:
        raise ValueError('37_GROUP_63_SEGMENT_SOURCE_MISMATCH')
    if len(selected)!=37 or len({r['id'] for r in selected})!=37:
        raise ValueError('PARSED_GROUPS_NOT_37_UNIQUE')
    mapping={r['id']:r for r in selected}
    used={name:[] for name in MOVIE_SEGMENTS}
    ids=[]; pending=[]
    for g in groups:
        sid=g['id'];movie=g['movie'];ids.append(sid)
        if movie not in MOVIE_SEGMENTS or sid not in mapping or mapping[sid]['movie']!=movie:
            raise ValueError('UNRECOGNIZED_GROUP_MAPPING')
        segments=g['source_segments']
        if not isinstance(segments,list) or not segments or not all(type(x)==int for x in segments):
            raise ValueError('ASR_SEGMENTS_MALFORMED')
        used[movie].extend(segments)
        if g.get('source_asr_en','')=='' or g.get('ru_text','')=='':
            raise ValueError('MISSING_EN_ASR_OR_RU_DRAFT')
        if not mapping[sid].get('selected_audio'):
            state=g['status']
            priority='P1_FIND_APPROVED_PILOT_WAV' if sid in PILOT_KNOWN else ('P2_CHECK_EN_ASR_AND_NAMES' if 'SOURCE' in state or 'NAME' in state else ('P3_VERIFY_TIMING' if 'TIMING' in state else 'P4_REVIEW_DRAFT_THEN_SYNTHESIZE'))
            pending.append({'id':sid,'movie':movie,'priority':priority,
                 'source_status':state,'source_asr_en_NOT_AUDIO_VERIFIED':g['source_asr_en'],
                 'russian_draft_NOT_APPROVED':g['ru_text'],
                 'english_window_start_s':g['source_start_s'],
                 'english_window_end_s':g['source_end_s'],
                 'timing_status':g.get('timing_status',''),
                 'asr_corrections':g.get('asr_corrections',''),
                 'source_note':g.get('note',''),
                 'full_english_original_audio_verified':'NO',
                 'approved_russian_wav_available':'NO',
                 'game_install_allowed':'NO'})
    if len(set(ids))!=37 or len(pending)!=22:
        raise ValueError('QUEUE_COUNT_MISMATCH')
    for movie,n in MOVIE_SEGMENTS.items():
        if sorted(used[movie])!=list(range(1,n+1)):
            raise ValueError('EN_ASR_SEGMENT_COVERAGE_'+movie)
    if sum(bool(x.get('selected_audio')) for x in selected)!=15:
        raise ValueError('SELECTED_WAV_COUNT_NOT_15')
    return pending


def _merge_main_report(replacements,root=None):
    work=Path(root) if root else Path(os.environ.get('BG_VOICE_FULL_PRODUCTION_ROOT') or Path.home()/'Documents'/'BG_VOICE_RU'/'FULL_PRODUCTION')
    main=work/'SEND_TO_CHATGPT_BG_VOICE_RU.zip'
    if not main.is_file():
        return 'COMMON_REPORT_NOT_FOUND_HOLD'
    fd,tmp=tempfile.mkstemp(prefix='BGVOICE_VIDEO_QA_',suffix='.pending',dir=str(work));os.close(fd)
    try:
        with zipfile.ZipFile(main) as old, zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED,compresslevel=4,allowZip64=True) as out:
            if old.testzip() is not None:raise ValueError('COMMON_REPORT_CRC_HOLD')
            names=old.namelist()
            if len(set(names))!=len(names):raise ValueError('COMMON_REPORT_DUPLICATE_NAMES_HOLD')
            for meta in old.infolist():
                if meta.filename in replacements:continue
                if meta.filename.endswith('/'):
                    out.writestr(meta,b'')
                else:
                    with old.open(meta) as src,out.open(meta,'w',force_zip64=True) as dst:
                        shutil.copyfileobj(src,dst,1024*1024)
            for name,data in sorted(replacements.items()):out.writestr(name,data)
        with zipfile.ZipFile(tmp) as test:
            if test.testzip() is not None or len(set(test.namelist()))!=len(test.namelist()):
                raise ValueError('NEW_COMMON_REPORT_CORRUPTED')
        os.replace(tmp,main)
        return 'MAIN_REPORT_UPDATED_ATOMIC'
    finally:
        if os.path.exists(tmp):os.unlink(tmp)


def selftest():
    assert MOVIE_CORE_VERSION=='1.1.0' and sum(MOVIE_SEGMENTS.values())==63
    assert len(PILOT_KNOWN)==3 and _csv([{'id':'A'}],['id']).endswith(b'A\r\n')
    print('MOVIE_CHANNEL_SELFTEST_PASS')
    return 0


def run(host):
    if set(host)!={'audit','write'} or not all(callable(v) for v in host.values()):
        raise RuntimeError('MOVIE_CHANNEL_UNEXPECTED_HOST')
    status,rows,raw,extras=host['audit']()
    status=dict(status);extras=dict(extras)
    status.update({'video_code_version':MOVIE_CORE_VERSION,
                   'video_update_mode':'ONE_PERMANENT_CMD_GITHUB_SHA_PINNED_CACHED',
                   'game_write':False,'voice_synthesis':False})
    pending=None
    try:
        pending=_verify_source(raw,rows)
        fields=list(pending[0]);by_priority=Counter(r['priority'] for r in pending)
        summary={'schema':'BG_VOICE_RU_MOVIE_22_PENDING_QA_1_1',
          'source_extracted_json_sha256':SCRIPT_JSON_SHA256,
          'extracted_json_bytes_SHA_VERIFIED':True,
          'original_2026_11_21_zip_sha_verified':status.get('full_script_provenance')=='PINNED_SHA_VERIFIED',
          'english_asr_and_text_verified_by_human':False,
          'source_group_total':37,'english_asr_segment_count':63,'selected_wav_count':15,
          'pending_group_count':22,'pilot_audio_must_be_recovered':sorted(PILOT_KNOWN),
          'priority_counts':dict(by_priority),
          'game_write':False,'voice_synthesis':False,
          'next':'Recover 3 approved pilot WAV; source-audit & name-check holds; verify 22 EN timings; prepare missing audio without touching 15 selections'}
        status['video_extracted_json_sha_verified']=True
        status['video_full_script_verified']=status.get('full_script_provenance')=='PINNED_SHA_VERIFIED'
        status['video_pending_group_count']=22
        status['video_accepted_wav_count']=15
        status['next']=summary['next']
        extras['VIDEO_22_PENDING_QA.csv']=_csv(pending,fields)
        extras['VIDEO_22_PENDING_QA_SUMMARY.json']=_json(summary)
        main_files={ROOT+'22_PENDING_EN_RU_QA.csv':extras['VIDEO_22_PENDING_QA.csv'],
                    ROOT+'STATUS.json':extras['VIDEO_22_PENDING_QA_SUMMARY.json']}
        print('MOVIE_CHANNEL: 37/37 SHA-matched text groups; 22 pending; 3 approved voice pilots to recover; no incomplete mix',flush=True)
    except (ValueError,KeyError,TypeError,json.JSONDecodeError) as error:
        status['video_extracted_json_sha_verified']=False
        status['next']='Recover exact 37-group script; no guessed text or incomplete mix'
        extras['VIDEO_SOURCE_HOLD.json']=_json({'reason':str(error),'no_game_write':True})
        main_files=None
        print('MOVIE_CHANNEL_SOURCE_HOLD:',str(error)[:150],flush=True)
    report=host['write'](status,rows,raw,extras)
    if main_files:
        try:print('MOVIE_CHANNEL_COMMON_REPORT:',_merge_main_report(main_files),flush=True)
        except Exception as exc:print('MOVIE_CHANNEL_COMMON_REPORT_HOLD:',type(exc).__name__,str(exc)[:150],flush=True)
    print('MOVIE_CHANNEL_REPORT:',report,flush=True)
    return 0


if __name__=='__main__':raise SystemExit(selftest())