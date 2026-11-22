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

MOVIE_CORE_VERSION = '1.2.0'
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


# These three clips were approved by the user on 2026-11-21.
# A filename, transcript, approximate timetag or speaker similarity is NEVER proof.
PILOT_SHA256 = {
    'INTRO15F_G01': '502f0ed76e0b46c884416768fff0da13cdb31a05bc150b6e760132525a13ed52',
    'SODCIN01_G02': '7c5b747e0ae3a2c778b5d6890d14a46bb493960d0e2398a2fc59170c9b4756ff',
    'IWINTRO_G06': 'd240ed50fa1a2ba7b0138e570b786d12347c909c7ea7fa9ef17d825051dc813b',
}
PILOT_ROOT = 'VIDEO/PILOTS/'


def _pilot_roots(base=None):
    if base is not None:
        return [Path(base)]
    home = Path.home()
    roots = [home/'Documents'/'BG_VOICE_RU'/'FULL_PRODUCTION',
             home/'Downloads', Path('C:/BG_VOICE_RU_MASTER')]
    env = os.environ.get('BG_VOICE_MOVIE_PILOT_SCAN_ROOT')
    if env:
        roots.insert(0, Path(env))
    # Dedup, never broaden to all of C:\ or user home.
    result=[]; seen=set()
    for p in roots:
        norm=str(p).casefold()
        if norm not in seen and p.is_dir():
            seen.add(norm); result.append(p)
    return result


def _pilot_candidates(roots):
    skip={'russian_wav_two_versions','.git','.venv','venv','site-packages',
          'node_modules','__pycache__','backups','game','games'}
    visited=0; wavs=0; archives=0
    for root in roots:
        for current, folders, files in os.walk(root, followlinks=False):
            visited+=1
            depth=len(Path(current).relative_to(root).parts)
            if visited>8000:break
            folders[:]=sorted(d for d in folders if d.casefold() not in skip and
                              not d.startswith('.') and depth < 5)
            for name in sorted(files):
                p=Path(current)/name
                upper=name.upper()
                if upper.endswith('.ZIP') and archives < 100 and any(
                        keyword in upper for keyword in ('NEXT3','NARRATOR','MOVIE','INTRO','FULL_SCRIPT')):
                    archives+=1; yield p,'ZIP'
                elif upper.endswith('.WAV') and wavs < 6000 and (
                        any(keyword in upper for keyword in ('INTRO15F','SODCIN01','IWINTRO','NARRATOR'))
                        or 'APPROVED' in str(p.parent).upper()):
                    wavs+=1; yield p,'WAV'


def _recover_pilots(roots=None, accepted=None):
    expected=dict(PILOT_SHA256 if accepted is None else accepted)
    found={}; attempted=0; zip_errors=0; file_errors=0
    for p,kind in _pilot_candidates(_pilot_roots(roots)):
        if len(found)==len(expected):break
        try:
            if kind=='WAV':
                if p.stat().st_size>16*1024*1024:continue
                attempted+=1
                data=p.read_bytes()
                if not (data[:4]==b'RIFF' and data[8:12]==b'WAVE'):continue
                digest=hashlib.sha256(data).hexdigest()
                for sid,sha in expected.items():
                    if sid not in found and digest==sha:
                        found[sid]=(data,'VERIFIED_WAV_SHA','WAV_FILE')
            else:
                if p.stat().st_size>120*1024*1024:continue
                with zipfile.ZipFile(p) as archive:
                    # Avoid extracting archive paths; in-memory exact SHA checks only.
                    entries=archive.infolist()
                    if len(entries)>2000:continue
                    for info in entries:
                        if len(found)==len(expected):break
                        if not (info.filename.lower().endswith('.wav') and 100<=info.file_size<=16*1024*1024):continue
                        attempted+=1
                        data=archive.read(info)
                        if not (data[:4]==b'RIFF' and data[8:12]==b'WAVE'):continue
                        digest=hashlib.sha256(data).hexdigest()
                        for sid,sha in expected.items():
                            if sid not in found and digest==sha:
                                found[sid]=(data,'VERIFIED_ZIP_MEMBER_SHA','ARCHIVE_MEMBER')
        except (OSError,zipfile.BadZipFile,RuntimeError,ValueError,EOFError) as exc:
            if kind=='ZIP':zip_errors+=1
            else:file_errors+=1
            continue
    additions={}
    results={}
    for sid,sha in expected.items():
        if sid in found:
            content,signal,provenance=found[sid]
            assert hashlib.sha256(content).hexdigest()==sha
            additions[PILOT_ROOT+sid+'__LOCKED_APPROVED.wav']=content
            results[sid]={'status':signal,'sha256':sha,'source_provenance':provenance,
                          'report_entry':PILOT_ROOT+sid+'__LOCKED_APPROVED.wav',
                          'approved_user_choice_preserved':True,'game_install_allowed':False}
        else:
            results[sid]={'status':'HOLD_APPROVED_PILOT_NOT_FOUND','sha256':sha,
                          'do_not_regenerate_approved_audio':True,'game_install_allowed':False}
    status={'schema':'BGVOICE_MOVIE_APPROVED_PILOT_RECOVERY_1_2',
            'verified_sha_wav_count':len(found),'total_approved_pilots':len(expected),
            'searched_candidate_files_or_members':attempted,
            'zip_read_errors_held':zip_errors,'wav_read_errors_held':file_errors,
            'original_wavs_modified':False,'game_write':False,'voice_synthesis':False,
            'human_decisions_preserved':True,'items':results}
    additions[PILOT_ROOT+'RECOVERY_STATUS.json']=_json(status)
    return additions,status


def selftest():
    assert MOVIE_CORE_VERSION=='1.2.0' and sum(MOVIE_SEGMENTS.values())==63
    assert len(PILOT_KNOWN)==3 and _csv([{'id':'A'}],['id']).endswith(b'A\r\n')
    assert set(PILOT_SHA256)==PILOT_KNOWN and all(len(sha)==64 for sha in PILOT_SHA256.values())
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
    # SHA-exact recovery is independent of text ASR accuracy and can proceed while
    # translations remain on HOLD. No audio is synthesized or installed.
    try:
        additions, pilot_status = _recover_pilots()
        print('MOVIE_PILOTS:', pilot_status['verified_sha_wav_count'],'of 3 SHA-verified; no resynthesis',flush=True)
        print('MOVIE_PILOTS_COMMON_REPORT:',_merge_main_report(additions),flush=True)
    except Exception as exc:
        print('MOVIE_PILOTS_RECOVERY_HOLD:',type(exc).__name__,str(exc)[:150],flush=True)
    print('MOVIE_CHANNEL_REPORT:',report,flush=True)
    return 0


if __name__=='__main__':raise SystemExit(selftest())