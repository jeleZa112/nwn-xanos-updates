# BG Voice RU movie 1.5: offline IEEE FLOAT32 source-cue fallback for 19 voice-missing groups.
# One permanent CMD, one common report, no TTS and no game writes.
from __future__ import annotations
import csv
import hashlib
import io
import json
import os
import shutil
import subprocess
import struct
import sys
import math
from array import array
import wave
import tempfile
import zipfile
from collections import Counter
from pathlib import Path

MOVIE_CORE_VERSION = '1.5.0'
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


def _recover_pilots(roots=None, accepted=None, common_report=None):
    expected=dict(PILOT_SHA256 if accepted is None else accepted)
    found={}; attempted=0; zip_errors=0; file_errors=0
    # Read back previously SHA-verified voice clips from the one existing report.
    # A moved/deleted historical ZIP must NEVER make an approved clip disappear.
    existing = Path(common_report) if common_report is not None else (
        Path(os.environ.get('BG_VOICE_FULL_PRODUCTION_ROOT') or
             Path.home()/'Documents'/'BG_VOICE_RU'/'FULL_PRODUCTION')/'SEND_TO_CHATGPT_BG_VOICE_RU.zip')
    if existing.is_file():
        try:
            with zipfile.ZipFile(existing) as archive:
                names=set(archive.namelist())
                for sid,sha in expected.items():
                    name=PILOT_ROOT+sid+'__LOCKED_APPROVED.wav'
                    if name not in names or archive.getinfo(name).file_size>16*1024*1024:
                        continue
                    data=archive.read(name)
                    if data[:4]==b'RIFF' and data[8:12]==b'WAVE' and hashlib.sha256(data).hexdigest()==sha:
                        found[sid]=(data,'VERIFIED_EXISTING_REPORT_SHA','COMMON_REPORT')
        except (OSError,zipfile.BadZipFile,RuntimeError,ValueError,EOFError,KeyError):
            zip_errors+=1
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
    status={'schema':'BGVOICE_MOVIE_APPROVED_PILOT_RECOVERY_1_3',
            'verified_sha_wav_count':len(found),'total_approved_pilots':len(expected),
            'searched_candidate_files_or_members':attempted,
            'zip_read_errors_held':zip_errors,'wav_read_errors_held':file_errors,
            'original_wavs_modified':False,'game_write':False,'voice_synthesis':False,
            'human_decisions_preserved':True,'items':results}
    additions[PILOT_ROOT+'RECOVERY_STATUS.json']=_json(status)
    return additions,status



# The 22-row file is a source/timing QA queue, not a count of missing WAV after
# approved pilot recovery. Reconciliation works entirely on the ONE ZIP.
def _reconcile_common_report(root=None):
    work=Path(root) if root else Path(os.environ.get('BG_VOICE_FULL_PRODUCTION_ROOT') or
                              Path.home()/'Documents'/'BG_VOICE_RU'/'FULL_PRODUCTION')
    main=work/'SEND_TO_CHATGPT_BG_VOICE_RU.zip'
    if not main.is_file():return 'COMMON_REPORT_NOT_FOUND_HOLD'
    with zipfile.ZipFile(main) as archive:
        if archive.testzip() is not None:raise ValueError('COMMON_REPORT_CRC_HOLD')
        movie=json.loads(archive.read(ROOT+'STATUS.json'))
        if (movie.get('source_extracted_json_sha256')!=SCRIPT_JSON_SHA256 or
            movie.get('source_group_total')!=37 or movie.get('pending_group_count')!=22):
            raise ValueError('MOVIE_SOURCE_GATE_NOT_SATISFIED')
        entries=list(csv.DictReader(io.StringIO(archive.read(ROOT+'22_PENDING_EN_RU_QA.csv').decode('utf-8-sig'))))
        if len(entries)!=22 or len({r['id'] for r in entries})!=22 or not PILOT_KNOWN.issubset({r['id'] for r in entries}):
            raise ValueError('PENDING_QUEUE_INVALID')
        recovered=[]; pilot_items={}
        for sid,sha in PILOT_SHA256.items():
            name=PILOT_ROOT+sid+'__LOCKED_APPROVED.wav'
            if name in archive.namelist():
                if archive.getinfo(name).file_size>16*1024*1024:raise ValueError('PILOT_ENTRY_OVERSIZE')
                data=archive.read(name)
                if data[:4]==b'RIFF' and data[8:12]==b'WAVE' and hashlib.sha256(data).hexdigest()==sha:
                    recovered.append(sid)
                    pilot_items[sid]={'status':'SHA_VERIFIED_LOCKED', 'sha256':sha, 'source':name}
                else:
                    pilot_items[sid]={'status':'HOLD_HASH_MISMATCH','sha256':sha}
            else:
                pilot_items[sid]={'status':'HOLD_MISSING','sha256':sha}
        selected=movie.get('selected_wav_count')
        if selected!=15:raise ValueError('SELECTED_BASELINE_NOT_15')
        recovered_set=set(recovered)
        remaining=[r for r in entries if r['id'] not in recovered_set]
        if len(remaining)!=22-len(recovered_set):raise ValueError('RECONCILIATION_COUNT_MISMATCH')
        expected_groups={'INTRO15F':7,'SODCIN01':11,'IWINTRO':19}
        remaining_counts=Counter(r['movie'] for r in remaining)
        status={
            'schema':'BGVOICE_MOVIE_RECONCILED_COVERAGE_1_3',
            'movie_module_version':MOVIE_CORE_VERSION,
            'source_extracted_json_sha256':SCRIPT_JSON_SHA256,
            'full_original_archive_SHA_verified':movie.get('original_2026_11_21_zip_sha_verified',False),
            'movie_group_counts':expected_groups,
            'total_script_groups':37,
            'selected_previously':15,
            'selected_prior_wavs_all_physically_in_report':False,
            'approved_pilot_wavs_SHA_verified_in_report':len(recovered),
            'russian_wav_identified_total':15+len(recovered),
            'russian_wav_not_yet_identified':len(remaining),
            'english_asr_segments_draft':63,
            'english_original_speech_audio_verified':False,
            'russian_translation_human_approved_for_all_groups':False,
            'speech_timing_verified':False,
            'pending_source_or_timing_QA_groups':22,
            'new_audio_generation_allowed_without_source_QA':False,
            'game_write':False,
            'voice_synthesis':False,
            'protected_pilots':pilot_items,
            'remaining_by_movie':dict(remaining_counts),
            'next':'Verify English source and Russian draft for remaining 19 groups; do not regenerate 3 recovered approved clips.'}
    keys=list(entries[0].keys())
    # Source statuses of recovered pilots are preserved in the 22-row QA list,
    # because exact English source, timing and text still require independent QA.
    new={ROOT+'19_MISSING_RUSSIAN_WAV.csv':_csv(remaining,keys),
         ROOT+'RECONCILED_STATUS.json':_json(status)}
    with zipfile.ZipFile(main) as check:
        if all(k in check.namelist() and check.read(k)==v for k,v in new.items()):
            return 'RECONCILIATION_CURRENT: '+str(len(recovered))+' SHA-verified pilots, '+str(len(remaining))+' voice-missing'
    outcome=_merge_main_report(new,work)
    return outcome+': '+str(len(recovered))+' SHA-verified pilots, '+str(len(remaining))+' voice-missing'


MOVIE_FULL_AUDIO_SEC={'INTRO15F':171.636,'SODCIN01':97.822,'IWINTRO':186.183}
EN_CUES_ROOT='VIDEO/EN_REFERENCE_19/'


def _source_stem_candidates(movie, base=None):
    if movie not in MOVIE_FULL_AUDIO_SEC:raise ValueError('UNEXPECTED_MOVIE')
    home=Path.home(); downloads=home/'Downloads'
    roots=[]
    if base is not None: roots.append(Path(base))
    if os.environ.get('BG_VOICE_EN_DNR_ROOT'):
        roots.insert(0, Path(os.environ['BG_VOICE_EN_DNR_ROOT']))
    roots.extend([
        downloads/'BG_VOICE_RU_MOVIES_BATCH_V1',
        downloads/'BG_VOICE_RU_MOVIES_BATCH_V1'/'BG_VOICE_RU_MOVIES_BATCH_V1',
        home/'Documents'/'BG_VOICE_RU'/'FULL_PRODUCTION'/'BG_VOICE_RU_MOVIES_BATCH_V1',
        Path('C:/BG_VOICE_RU_MASTER')/'BG_VOICE_RU_MOVIES_BATCH_V1',
    ])
    try:
        roots.extend(p for p in sorted(downloads.iterdir()) if p.is_dir() and
                     p.name.upper().startswith('BG_VOICE_RU_MOVIES_BATCH') and len(roots)<18)
    except OSError:pass
    seen=set()
    for root in roots:
        for candidate in (root/'RESULTS'/movie/'FULL'/'SPEECH_EN.wav',
                          root/'BG_VOICE_RU_MOVIES_BATCH_V1'/'RESULTS'/movie/'FULL'/'SPEECH_EN.wav'):
            key=str(candidate).casefold()
            if key not in seen:
                seen.add(key)
                if candidate.is_file():yield candidate


def _ffmpeg_bin():
    exe=shutil.which('ffmpeg')
    if exe:return exe
    try:
        from imageio_ffmpeg import get_ffmpeg_exe
        candidate=get_ffmpeg_exe()
        if candidate and Path(candidate).is_file():return candidate
    except (ImportError, OSError, RuntimeError):pass
    for path in (Path.home()/'Downloads'/'ffmpeg'/'bin'/'ffmpeg.exe',
                 Path('C:/ffmpeg/bin/ffmpeg.exe')):
        if path.is_file():return str(path)
    return None


def _source_duration(source):
    try:
        with wave.open(str(source),'rb') as w:
            return w.getnframes()/w.getframerate()
    except (wave.Error, EOFError, OSError):
        pass
    # RIFF chunk size can establish the duration even when Python's wave
    # decoder refuses IEEE_FLOAT32 or WAVE_FORMAT_EXTENSIBLE. No audio decoded.
    try:
        with open(source,'rb') as f:
            size=f.seek(0,2); f.seek(0)
            if size>=44 and f.read(4)==b'RIFF' and f.read(4) and f.read(4)==b'WAVE':
                rate=None;align=None;data_bytes=None
                while f.tell()+8<=size and f.tell()<1024*1024:
                    hdr=f.read(8)
                    if len(hdr)!=8:break
                    key,n=struct.unpack('<4sI',hdr)
                    if n>size-f.tell():break
                    if key==b'fmt ' and n>=16:
                        fields=f.read(16)
                        _,_,rate,_,align,_=struct.unpack('<HHIIHH',fields)
                        f.seek(n-16,1)
                    elif key==b'data':
                        data_bytes=n
                        f.seek(n,1)
                    else:f.seek(n,1)
                    if n%2:f.seek(1,1)
                    if rate and align and data_bytes is not None:
                        duration=data_bytes/(rate*align)
                        if 0<duration<300:return duration
    except (OSError,ValueError,struct.error):pass
    ffprobe=shutil.which('ffprobe')
    if not ffprobe:return None
    try:
        out=subprocess.run([ffprobe,'-v','error','-show_entries','format=duration',
                            '-of','default=noprint_wrappers=1:nokey=1',str(source)],
                           capture_output=True,text=True,timeout=12,check=True)
        val=float(out.stdout.strip())
        return val if 0<val<300 else None
    except (OSError,ValueError,subprocess.CalledProcessError,subprocess.TimeoutExpired):return None


def _file_sha256(path):
    obj=hashlib.sha256()
    with open(path,'rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):
            obj.update(chunk)
    return obj.hexdigest()


def _native_float32_to_pcm16_window(source, start, end):
    """Read a bounded RIFF WAVE_FLOAT32 section without ffmpeg or numpy.

    Preserve the exact input rate and channel count: no resampling, spectral
    denoising, time-stretch, pitch shift, or writes to the original source.
    Supports fmt 3 and WAVE_FORMAT_EXTENSIBLE IEEE-FLOAT GUID, excluding
    compressed audio, truncated blocks and malformed or oversized chunks.
    """
    source=Path(source)
    duration=end-start
    if not 0<duration<=42:raise ValueError('INVALID_TIME_RANGE_HOLD')
    # Standard IEEE FLOAT32 in WAVE_FORMAT_EXTENSIBLE uses this exact GUID.
    ieee_guid=bytes.fromhex('0300000000001000800000aa00389b71')
    with source.open('rb') as f:
        file_size=f.seek(0,2)
        f.seek(0)
        if file_size<44 or f.read(4)!=b'RIFF':raise ValueError('NO_RIFF_HOLD')
        declared=struct.unpack('<I',f.read(4))[0]
        if f.read(4)!=b'WAVE' or declared+8>file_size:
            raise ValueError('BAD_WAVE_SIZE_HOLD')
        info=None; data=None
        # Real wav stems have fmt near the header; impose bounded header scan.
        while f.tell()+8<=file_size and f.tell()<1024*1024:
            head=f.read(8)
            if len(head)<8:break
            chunk,n=struct.unpack('<4sI',head)
            offset=f.tell()
            if n>file_size-offset:raise ValueError('TRUNCATED_RIFF_CHUNK_HOLD')
            if chunk==b'fmt ':
                if not 16<=n<=512:raise ValueError('BAD_WAVE_FMT_SIZE_HOLD')
                fmt=f.read(n)
                tag,channels,rate,avg,align,bits=struct.unpack_from('<HHIIHH',fmt)
                if tag==0xfffe:
                    if len(fmt)<40 or struct.unpack_from('<H',fmt,16)[0]<22 or fmt[24:40]!=ieee_guid:
                        raise ValueError('NOT_IEEE_FLOAT_EXTENSIBLE_HOLD')
                elif tag!=3:
                    raise ValueError('NOT_IEEE_FLOAT32_HOLD')
                if bits!=32 or channels not in (1,2) or not 8000<=rate<=192000 or align!=channels*4 or avg!=rate*align:
                    raise ValueError('INVALID_FLOAT_FMT_HOLD')
                info={'channels':channels,'rate':rate,'align':align}
            elif chunk==b'data':
                data=(offset,n)
            f.seek(offset+n+(n&1))
            if info is not None and data is not None:break
        if info is None or data is None:raise ValueError('MISSING_WAVE_FMT_OR_DATA_HOLD')
        channels=info['channels'];rate=info['rate'];align=info['align']
        if data[1]%align:raise ValueError('TRUNCATED_FRAME_HOLD')
        total_frames=data[1]//align
        first=round(start*rate);frames=round(duration*rate)
        if first<0 or frames<1 or first+frames>total_frames+2:
            raise ValueError('FLOAT_WINDOW_OUT_OF_RANGE_HOLD')
        first=min(first,total_frames);frames=min(frames,total_frames-first)
        if frames<rate*duration*.98:raise ValueError('FLOAT_WINDOW_TRUNCATED_HOLD')
        if frames*channels*2>9*1024*1024:raise ValueError('FLOAT_WINDOW_OVERSIZE_HOLD')
        f.seek(data[0]+first*align)
        # First pass: find an amplitude-safe, globally uniform gain for this
        # cue.  No local per-block gain pumping or dynamic compression.
        peak=0.0;read_frames=0
        while read_frames<frames:
            take=min(32768,frames-read_frames)
            raw=f.read(take*align)
            if len(raw)!=take*align:raise ValueError('FLOAT_WINDOW_TRUNCATED_HOLD')
            values=array('f');values.frombytes(raw)
            if sys.byteorder!='little':values.byteswap()
            for val in values:
                if not math.isfinite(val):raise ValueError('FLOAT_NAN_INF_HOLD')
                if abs(val)>peak:peak=abs(val)
            read_frames+=take
        gain=min(1.0,0.98/peak) if peak else 1.0
        f.seek(data[0]+first*align)
        buffer=io.BytesIO()
        with wave.open(buffer,'wb') as output:
            output.setnchannels(channels);output.setframerate(rate);output.setsampwidth(2)
            written=0
            while written<frames:
                take=min(32768,frames-written)
                raw=f.read(take*align)
                if len(raw)!=take*align:raise ValueError('FLOAT_WINDOW_TRUNCATED_HOLD')
                values=array('f');values.frombytes(raw)
                if sys.byteorder!='little':values.byteswap()
                pcm=array('h')
                pcm.extend(max(-32768,min(32767,round(v*gain*32767))) for v in values)
                if sys.byteorder!='little':pcm.byteswap()
                output.writeframesraw(pcm.tobytes())
                written+=take
        method=('NATIVE_FLOAT32_PCM16_PRESERVE_RATE_CHANNELS'
                if gain==1.0 else f'NATIVE_FLOAT32_PCM16_UNIFORM_GAIN_{gain:.6f}')
        return buffer.getvalue(),method


def _extract_english_window(source,start,end,ffmpeg=None):
    duration=end-start
    if not 0<duration<=42:raise ValueError('INVALID_TIME_RANGE_HOLD')
    if ffmpeg:
        try:
            result=subprocess.run([ffmpeg,'-hide_banner','-nostdin','-loglevel','error',
                   '-i',str(source),'-ss',f'{start:.3f}','-t',f'{duration:.3f}',
                   '-map','0:a:0','-vn','-ac','1','-ar','16000',
                   '-c:a','pcm_s16le','-f','s16le','pipe:1'],
                   capture_output=True,timeout=35,check=True)
            raw=result.stdout
            if len(raw)>2*1024*1024:raise ValueError('CLIP_OVERSIZE_HOLD')
            if abs((len(raw)//2)/16000-duration)>0.3:raise ValueError('CLIP_DURATION_HOLD')
            buf=io.BytesIO()
            with wave.open(buf,'wb') as output:
                output.setnchannels(1);output.setsampwidth(2);output.setframerate(16000)
                output.writeframes(raw)
            return buf.getvalue(),'FFMPEG_PCM16_16KHZ_MONO'
        except (OSError,subprocess.CalledProcessError,subprocess.TimeoutExpired,EOFError,wave.Error):
            pass
    # Standard-library PCM16 and FLOAT32 fallbacks: no dependency on ffmpeg.
    try:
        return _native_float32_to_pcm16_window(source,start,end)
    except ValueError as err:
        # Non-FLOAT32 PCM16 is an expected second candidate. Any invalid float
        # audio remains on HOLD instead of masking source corruption.
        if str(err) not in ('NOT_IEEE_FLOAT32_HOLD','NOT_IEEE_FLOAT_EXTENSIBLE_HOLD'):
            raise
    with wave.open(str(source),'rb') as w:
        if w.getcomptype()!='NONE' or w.getsampwidth()!=2 or w.getnchannels() not in (1,2):
            raise ValueError('NO_DECODER_FOR_SOURCE_FORMAT_HOLD')
        hz=w.getframerate();channels=w.getnchannels()
        frames=round(duration*hz)
        if frames*channels*2>9*1024*1024:raise ValueError('FALLBACK_CLIP_TOO_LARGE_HOLD')
        w.setpos(round(start*hz)); raw=w.readframes(frames)
        if len(raw)<int(frames*channels*2*.98):raise ValueError('CLIP_TRUNCATED_HOLD')
        buf=io.BytesIO()
        with wave.open(buf,'wb') as out:
            out.setnchannels(channels);out.setsampwidth(2);out.setframerate(hz);out.writeframes(raw)
        return buf.getvalue(),'NATIVE_PCM16_NO_RESAMPLE'


def _prepare_english_reference_cues(root=None,source_root=None):
    work=Path(root) if root else Path(os.environ.get('BG_VOICE_FULL_PRODUCTION_ROOT') or
                        Path.home()/'Documents'/'BG_VOICE_RU'/'FULL_PRODUCTION')
    main=work/'SEND_TO_CHATGPT_BG_VOICE_RU.zip'
    if not main.is_file():return 'COMMON_REPORT_MISSING_HOLD'
    with zipfile.ZipFile(main) as z:
        if z.testzip() is not None:raise ValueError('BAD_COMMON_REPORT_CRC')
        summary=json.loads(z.read(ROOT+'RECONCILED_STATUS.json'))
        if summary.get('source_extracted_json_sha256')!=SCRIPT_JSON_SHA256 or summary.get('russian_wav_not_yet_identified') not in range(19,23):
            raise ValueError('SOURCE_OR_COVERAGE_GATE_HOLD')
        rows=list(csv.DictReader(io.StringIO(z.read(ROOT+'19_MISSING_RUSSIAN_WAV.csv').decode('utf-8-sig'))))
        if len(rows)!=summary['russian_wav_not_yet_identified'] or len({r['id'] for r in rows})!=len(rows):
            raise ValueError('INVALID_MISSING_QUEUE')
    # This source is derived from the game's old English audio by CDX23: it
    # is useful for review, NOT definitive proof of transcription or acting.
    ffmpeg=_ffmpeg_bin(); sources={};source_status={};clips={};results=[]
    for movie in MOVIE_FULL_AUDIO_SEC:
        selected=None;seen=[]
        for p in _source_stem_candidates(movie,source_root):
            try:
                if p.stat().st_size>500*1024*1024:continue
                duration=_source_duration(p)
                if duration is None or abs(duration-MOVIE_FULL_AUDIO_SEC[movie])>2.0:
                    seen.append('SOURCE_DURATION_MISMATCH_HOLD');continue
                selected=p; sources[movie]=p;source_status[movie]={
                    'state':'DNR_STEM_FOUND_LENGTH_MATCH','duration_s':round(duration,3),
                    'source_sha256':_file_sha256(p),
                    'path_local_not_exported':str(p),
                    'source_kind':'CDX23_DERIVED_SPEECH_EN_NOT_ORIGINAL_TRANSCRIPTION_PROOF'}
                break
            except (OSError,ValueError,wave.Error):continue
        if selected is None:
            source_status[movie]={'state':seen[0] if seen else 'FULL_DNR_SPEECH_EN_NOT_FOUND_HOLD',
                                  'original_english_audio_not_verified':True}
    for row in rows:
        sid=row['id'];movie=row['movie'];start=float(row['english_window_start_s']);end=float(row['english_window_end_s'])
        entry={'id':sid,'movie':movie,'source_window_start_s':start,'source_window_end_s':end,
               'russian_draft_status':'NOT_APPROVED','english_ASR_status':'UNVERIFIED',
               'exact_speech_onset_verified':False,'game_install_allowed':False}
        source=sources.get(movie)
        if source is None:
            entry['status']='HOLD_NO_FULL_DNR_EN_SOURCE'
        elif start<0 or end>source_status[movie]['duration_s']+0.05 or end<=start:
            entry['status']='HOLD_ASR_TIME_OUTSIDE_SOURCE'
        else:
            try:
                data,method=_extract_english_window(source,start,end,ffmpeg)
                name=EN_CUES_ROOT+sid+'_EN_DNR_ASR_WINDOW.wav'
                clips[name]=data
                entry.update({'status':'TECHNICAL_EN_CUE_READY_NOT_LINGUISTICALLY_VERIFIED',
                              'cue_member':name,'cue_sha256':hashlib.sha256(data).hexdigest(),
                              'export_format':method})
            except (OSError,ValueError,wave.Error,EOFError) as exc:
                entry['status']='HOLD_'+type(exc).__name__
                entry['hold_detail']=str(exc)[:100]
        results.append(entry)
    count=sum(row['status']=='TECHNICAL_EN_CUE_READY_NOT_LINGUISTICALLY_VERIFIED' for row in results)
    status={'schema':'BGVOICE_MOVIE_19_EN_DNR_SOURCE_PREVIEW_1_4',
            'source_script_sha256':SCRIPT_JSON_SHA256,
            'groups_with_ru_wav_absent':len(rows),'english_cues_prepared':count,
            'english_cues_hold':len(rows)-count,
            'source_stems':source_status,
            'correct_source_English_words_verified':False,
            'speaker_identity_verified_by_human':False,
            'original_EN_dnr_bleed_or_artifacts_possible':True,
            'asr_windows_not_speech_precise':True,
            'existing_approved_ru_wav_modified':False,
            'voice_synthesis':False,'game_write':False,
            'next':'Compare EN cues with ASR and Russian drafts; repair confirmed text before synthesizing missing Russian voices'}
    keys=list(results[0].keys())
    for row in results:
        for k in row:
            if k not in keys:keys.append(k)
    additions={EN_CUES_ROOT+'STATUS.json':_json(status),
               EN_CUES_ROOT+'CUE_INDEX.csv':_csv(results,keys),**clips}
    with zipfile.ZipFile(main) as z:
        if len(z.namelist())==len(set(z.namelist())) and all(
                k in z.namelist() and z.read(k)==v for k,v in additions.items()):
            return 'EN_CUES_CURRENT: '+str(count)+' of '+str(len(rows))
    return _merge_main_report(additions,work)+': '+str(count)+' of '+str(len(rows))

def selftest():
    assert MOVIE_CORE_VERSION=='1.5.0' and sum(MOVIE_SEGMENTS.values())==63
    assert len(PILOT_KNOWN)==3 and _csv([{'id':'A'}],['id']).endswith(b'A\r\n')
    assert set(PILOT_SHA256)==PILOT_KNOWN and all(len(sha)==64 for sha in PILOT_SHA256.values())
    assert len(PILOT_SHA256)==3
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
    try:
        print('MOVIE_COVERAGE_RECONCILED:',_reconcile_common_report(),flush=True)
    except Exception as exc:
        print('MOVIE_RECONCILIATION_HOLD:',type(exc).__name__,str(exc)[:160],flush=True)
    try:
        print('MOVIE_EN_REFERENCE_CUES:',_prepare_english_reference_cues(),flush=True)
    except Exception as exc:
        print('MOVIE_EN_REFERENCE_HOLD:',type(exc).__name__,str(exc)[:160],flush=True)
    print('MOVIE_CHANNEL_REPORT:',report,flush=True)
    return 0


if __name__=='__main__':raise SystemExit(selftest())