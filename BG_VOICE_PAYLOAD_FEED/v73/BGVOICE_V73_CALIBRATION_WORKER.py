"""BG Voice RU V73: safe calibration-audition worker, imported by ONE main updater.

No GPU, inference, downloads, game writes, TLK edits, or automatic approvals.
Produces a local HTML review and SHA-gated audition WAV copies inside report root.
The main updater owns the canonical consolidated report ZIP and all scheduling.
"""
from __future__ import annotations
import csv
import hashlib
import html
import json
import os
from pathlib import Path, PureWindowsPath
import shutil
import tempfile
import wave

SCHEMA = 'BGVOICE_V73_CALIBRATION_V1'
CALIBRATION_SHA256 = '1b172b3905638da78cad4e0d69da8277deeb4086109adeb12fc1a01c32ab0519'
LANES = ('PROVISIONAL_BULK_STAGE_SHA_GATED','ACTING_REVIEW_298',
         'SPEECH_CONTENT_REVIEW_171','ACOUSTIC_OR_DURATION_REVIEW')
HUMAN_LOCKS = {'OH85856':'V65','OH80404':'V60','OH89888':'BOTH_BAD'}


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()


def valid_root(p):
    p=Path(p).resolve()
    ps={s.casefold() for s in p.parts}
    if {'russian_wav_two_versions','en_reference_wav','bg_eet_foxx_new'} & ps:
        raise ValueError('REFUSE_ORIGINAL_AUDIO_OR_GAME_OUTPUT_ROOT')
    if p==Path(p.anchor):
        raise ValueError('REFUSE_FILESYSTEM_ROOT')
    return p


def read_calibration(payload_dir, *, test_mode=False):
    p=Path(payload_dir)/'06_CALIBRATION_REVIEW_96.csv'
    if not test_mode and sha(p)!=CALIBRATION_SHA256:
        raise ValueError('V70_CALIBRATION_SOURCE_SHA_MISMATCH')
    with p.open(encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f))
    if len(rows)!=96 or len({r.get('sound_id') for r in rows})!=96:
        raise ValueError('EXPECTED_96_UNIQUE_CALIBRATION_ROWS')
    counts={k:sum(r.get('priority_lane')==k for r in rows) for k in LANES}
    if not test_mode and counts != dict(zip(LANES,(32,24,24,16))):
        raise ValueError('CALIBRATION_STRATA_CHANGED')
    for r in rows:
        if r['priority_lane'] not in LANES:
            raise ValueError('UNKNOWN_CALIBRATION_LANE')
        if r.get('ready_for_game') not in ('NO','False','FALSE','0',''):
            raise ValueError('UNEXPECTED_RELEASE_APPROVAL')
    return rows,counts


def balanced_batch(rows, batch_index=0, count=16):
    if not isinstance(batch_index,int) or batch_index<0:
        raise ValueError('INVALID_BATCH_INDEX')
    if count!=16:
        raise ValueError('ONLY_VERIFIED_CALIBRATION_BATCH_16')
    by={lane:[r for r in rows if r['priority_lane']==lane] for lane in LANES}
    # 6 equal batches, each includes 4 bulk/acting/content and 4 acoustic for first four;
    # last two use 8 bulk, 4 acting, 4 content, as acoustic runs out.
    quotas=[(4,4,4,4)]*4+[(8,4,4,0)]*2
    if batch_index>=len(quotas):
        raise ValueError('BATCH_INDEX_OUT_OF_RANGE')
    start={k:0 for k in LANES}
    for q in quotas[:batch_index]:
        for lane,n in zip(LANES,q):start[lane]+=n
    batch=[]
    for lane,n in zip(LANES,quotas[batch_index]):
        batch.extend(by[lane][start[lane]:start[lane]+n])
    if len(batch)!=16 or len({r['sound_id'] for r in batch})!=16:
        raise RuntimeError('BATCH_COVERAGE_INVALID')
    return batch


def check_source(row, mode, root):
    sid=row['sound_id'];char=row['character'];x=mode.upper()
    if not sid.isalnum() or not char.replace('_','').isalnum() or x not in ('STABLE','PER_LINE'):
        raise ValueError('BAD_SOURCE_ID')
    key='stable_source' if x=='STABLE' else 'per_line_source'
    keysha='stable_sha256_v55' if x=='STABLE' else 'per_line_sha256_v55'
    target=Path(row[key])
    # Exact expected location: no arbitrary paths from CSV.
    expected=Path(root)/char/(sid+'__'+x.lower()+'_RU.wav')
    if target.resolve()!=expected.resolve():
        raise ValueError('SOURCE_NOT_IN_EXACT_CHARACTER_PATH')
    if target.is_symlink() or not target.is_file():
        raise FileNotFoundError('MISSING_OR_SYMLINK_WAV')
    original_sha=row[keysha].lower()
    if not (len(original_sha)==64 and all(c in '0123456789abcdef' for c in original_sha)):
        raise ValueError('BAD_SOURCE_SHA256')
    if sha(target)!=original_sha:
        raise ValueError('SOURCE_SHA256_MISMATCH')
    with wave.open(str(target),'rb') as w:
        if (w.getframerate(),w.getnchannels(),w.getsampwidth())!=(48000,1,2) or w.getnframes()==0:
            raise ValueError('SOURCE_WAV_FORMAT_MISMATCH')
    return target,original_sha


def safe_copy(src,dst,expected_sha):
    if dst.exists():
        if not dst.is_file() or dst.is_symlink() or sha(dst)!=expected_sha:
            raise ValueError('EXISTING_OUTPUT_DIFFERS_REFUSE_OVERWRITE')
        return 'REUSED_VERIFIED'
    with tempfile.NamedTemporaryFile(prefix='.bgvoice_v73_',suffix='.partial',
             dir=dst.parent,delete=False) as f:
        temp=Path(f.name)
    try:
        shutil.copyfile(src,temp)
        if sha(temp)!=expected_sha:
            raise ValueError('COPIED_WAV_SHA_MISMATCH')
        os.replace(temp,dst)
    finally:
        temp.unlink(missing_ok=True)
    return 'COPIED_SHA_VERIFIED'


def html_document(records, batch):
    rows=[]
    for r in records:
        sid=html.escape(r['sound_id']);line=html.escape(r['text_ru'][:1200]);
        fields=[]
        for mode in ('STABLE','PER_LINE','EN'):
            item=r['audio'].get(mode)
            if item:
                fields.append('<div><strong>'+mode+'</strong><audio controls preload="none" src="'+html.escape(item['relative'],quote=True)+'"></audio></div>')
            else:
                fields.append('<div><strong>'+mode+'</strong> <em>HOLD / нет проверенного WAV</em></div>')
        rows.append('<section data-id="'+sid+'"><h3>'+sid+' — '+html.escape(r['lane'])+'</h3><p>'+line+'</p>'+
                    ''.join(fields)+'<label>Мой выбор <select class="pick"><option value="UNDECIDED">Не выбрано</option>'+
                    ''.join('<option value="'+v+'">'+v+'</option>' for v in ('STABLE','PER_LINE','BOTH_BAD','REGEN','SKIP'))+
                    '</select></label> <label>Причина <select class="reason"><option value="">—</option>'+
                    ''.join('<option value="'+v+'">'+v+'</option>' for v in ('STRESS','VOICE','EMOTION','CONTENT','SFX','GOOD'))+
                    '</select></label><textarea placeholder="Ударения, имена, эмоции, замечания" rows="2"></textarea></section>')
    script="""<script>document.getElementById('save').onclick=()=>{let d=[];document.querySelectorAll('section[data-id]').forEach(s=>d.push({sound_id:s.dataset.id,preferred:s.querySelector('.pick').value,reason:s.querySelector('.reason').value,notes:s.querySelector('textarea').value}));let blob=new Blob([JSON.stringify({schema:'BGVOICE_V73_HUMAN_REVIEW_V1',batch:__BATCH__,decisions:d},null,2)],{type:'application/json'});let a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='BGVOICE_V73_USER_REVIEW_BATCH___BATCH__.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)};</script>""".replace('__BATCH__',str(batch))
    return ('<!doctype html><html lang="ru"><meta charset="utf-8"><title>BG Voice RU V73 calibration</title><style>body{max-width:1000px;margin:24px auto;font:16px system-ui;padding:0 12px;background:#f7f8fa;color:#17212b}section{margin:16px 0;padding:18px;background:white;border-radius:14px;border:1px solid #ddd}audio{width:90%;vertical-align:middle;margin:6px 14px}label{display:inline-block;margin:8px}textarea{display:block;width:95%;margin:10px 0}button{padding:12px;border-radius:8px;font-size:16px}</style><h1>BG Voice RU — калибровка</h1><p>Только прослушивание. Никакого автоматического утверждения и установки. Выбирай по голосу, эмоции и полноте; затем отмечай ударения.</p><button id="save">Сохранить оценки JSON</button>'+''.join(rows)+script+'</html>').encode('utf-8')


def run_from_main_updater(payload_dir, output_root, russian_root, english_root,
                          *, batch_index=0, mode='stage'):
    if mode not in ('preflight','stage'):
        raise ValueError('INVALID_MODE')
    out=valid_root(output_root)
    rows,counts=read_calibration(payload_dir)
    chosen=balanced_batch(rows,batch_index)
    prepared=[]
    if mode=='stage':
        (out/f'V73_CALIBRATION_BATCH_{batch_index+1:02d}'/'audio').mkdir(parents=True,exist_ok=True)
    for row in chosen:
        sid=row['sound_id']; lane=row['priority_lane']
        item={'sound_id':sid,'lane':lane,'text_ru':row['russian_game_text_UNCHANGED'],
              'suggested':row.get('proposed_or_human_choice','NONE'),
              'audio':{},'holds':{},'human_approved':False,'game_install_ready':False}
        if sid in HUMAN_LOCKS or row.get('hard_guard') or row.get('user_choice'):
            item['holds']['ALL']='HUMAN_PROTECTED';prepared.append(item);continue
        for label in ('STABLE','PER_LINE'):
            try:
                src,expected=check_source(row,label,russian_root)
                rel='audio/'+sid+'__'+label+'.wav'
                if mode=='stage':
                    safe_copy(src,out/f'V73_CALIBRATION_BATCH_{batch_index+1:02d}'/rel,expected)
                item['audio'][label]={'relative':rel,'sha256':expected,
                                     'source':'V55_SHA_VERIFIED','staged':mode=='stage'}
            except (OSError,ValueError,wave.Error) as exc:
                item['holds'][label]=type(exc).__name__+': '+str(exc)[:120]
        try:
            char=row['character'];original=Path(english_root)/char/(sid+'_EN.wav')
            if original.is_file() and not original.is_symlink() and original.resolve().is_relative_to(Path(english_root).resolve()):
                with wave.open(str(original),'rb') as w:
                    if w.getnframes()>0 and w.getsampwidth()==2:
                        en_sha=sha(original)
                        rel='audio/'+sid+'__EN.wav'
                        if mode=='stage':safe_copy(original,out/f'V73_CALIBRATION_BATCH_{batch_index+1:02d}'/rel,en_sha)
                        item['audio']['EN']={'relative':rel,'sha256':en_sha,'source':'EXACT_SOUND_ID_FILE_NOT_SPEAKER_PROOF','staged':mode=='stage'}
            if 'EN' not in item['audio']:
                item['holds']['EN']='EXACT_EN_NOT_FOUND_OR_UNSUITABLE'
        except (OSError,ValueError,wave.Error) as exc:
            item['holds']['EN']=type(exc).__name__+': '+str(exc)[:120]
        prepared.append(item)
    result={'schema':SCHEMA,'mode':mode,'batch_index':batch_index,'total_rows':len(rows),'batch_size':len(chosen),
            'strata':counts,'audio_verified':sum(len(r['audio']) for r in prepared),
            'hold_items':sum(bool(r['holds']) for r in prepared),
            'user_approvals_created':0,'game_modified':False,'source_modified':False,
            'report_owner':'MAIN_UPDATER','entries':prepared}
    if mode=='stage':
        path=out/f'V73_CALIBRATION_BATCH_{batch_index+1:02d}'
        data=html_document(prepared,batch_index+1)
        # Regenerated HTML contains no personal decisions and is safe to replace atomically.
        with tempfile.NamedTemporaryFile(prefix='.calib_',suffix='.tmp',dir=path,delete=False) as f:
            tmp=Path(f.name);f.write(data)
        os.replace(tmp,path/'OPEN_REVIEW.html')
        (path/'QA_RESULT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        result['report_files_for_main_updater']=[str(path/'OPEN_REVIEW.html'),str(path/'QA_RESULT.json')]
    return result