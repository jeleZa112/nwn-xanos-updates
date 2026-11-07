# -*- coding: utf-8 -*-
"""BG Voice RU 3.2 -- real emotion2vec inference on original EN Imoen WAV.
Never writes to originals, game, Qwen environment or approved Russian WAV.
Run --check with built-in Python; --pilot/--all requires separate FunASR env.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import html
import json
import os
import shutil
import sys
import time
import wave
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCES = HERE / 'INPUT_EN'
OUT = HERE / 'ANALYSIS'
MODEL_ID = 'emotion2vec/emotion2vec_plus_base'
# Same official weights via Hugging Face: bypass modelscope.cn repeated 10s timeouts.
os.environ.setdefault('HF_HUB_ETAG_TIMEOUT', '120')
os.environ.setdefault('HF_HUB_DOWNLOAD_TIMEOUT', '300')
os.environ.setdefault('HF_HUB_DISABLE_SYMLINKS_WARNING', '1')
TARGETS = ('IMOEN06_', 'IMOEN77A', 'IMOEN79A', 'IMOEN79B')
EN_LABELS = ['angry','disgusted','fearful','happy','neutral','other','sad','surprised','unknown']
RU_LABELS = {'angry':'злость/раздражение','disgusted':'отвращение','fearful':'страх','happy':'радость','neutral':'нейтральная речь','other':'другая эмоция','sad':'грусть','surprised':'удивление','unknown':'не определено'}
ACTING_STYLE = {
    'angry': 'Напряжённее и резче, точные смысловые акценты; не превращать в крик автоматически.',
    'disgusted': 'Сдержанное неприятие или отвращение; сверить интонацию по оригиналу.',
    'fearful': 'Настороженность и нервное напряжение; проверить дыхание и ускорения.',
    'happy': 'Более звонкий, живой голос, улыбка; смех переносить как отдельное событие.',
    'neutral': 'Естественная разговорная речь без постоянной нежности и монотонности.',
    'other': 'Эмоция не классифицирована: режиссёрская проверка обязательна.',
    'sad': 'Приглушённее, спокойнее, смысловые паузы; не обязательно шёпотом.',
    'surprised': 'Выраженное удивление, яркие изменения мелодики и акценты.',
    'unknown': 'Невозможно назначить эмоциональный окрас автоматически.',
}

REVIEW = {
    'IMOEN06_': 'В оригинале «Ha!» — смех, а не буквальное произнесение «Ха». Сравнить настоящий смех перед русской репликой.',
    'IMOEN77A': 'Выделить радостное приветствие, настоящий смешок, шутливый вопрос и более мягкую просьбу.',
    'IMOEN79A': 'Проверить эмоциональный акцент на «Ты уверен» и вопросительную интонацию, не делать всю реплику нежной.',
    'IMOEN79B': 'Проверить вопрос «Ты точно хочешь от меня избавиться?»; добиваться живой, не монотонной подачи.',
}

def log(msg):
    message = time.strftime('%H:%M:%S') + ' ' + str(msg)
    print(message, flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / 'RUN_EMOTION_32.log').open('a', encoding='utf-8') as f:
        f.write(message + '\n')

def ident(name):
    base = Path(name).stem.upper()
    return base if base.startswith('IMOEN') and all(c.isalnum() or c == '_' for c in base) else None

def wav_len(path):
    try:
        with wave.open(str(path), 'rb') as f:
            return f.getnframes() / f.getframerate()
    except (OSError, EOFError, ValueError, ZeroDivisionError, wave.Error):
        # Genuine game WAVs usually open with stdlib wave. Non-PCM: validate by soundfile only after install.
        try:
            import soundfile as sf
            return sf.info(str(path)).duration
        except (ImportError, RuntimeError, OSError):
            return 0

def find_sources():
    """Find an existing English collection; do not confuse it with our Russian OUTPUT."""
    if SOURCES.is_dir() and len(list(SOURCES.glob('IMOEN*.wav'))) >= 4:
        return SOURCES
    direct = [ROOT / 'RVC_DATASETS' / 'IMOEN', ROOT / 'BG_RU_FULL_17' / 'IMOEN', ROOT / 'IMOEN', ROOT.parent / 'IMOEN', Path.home() / 'Downloads' / 'IMOEN']
    for d in direct:
        if d.is_dir() and all((d / (x + '.wav')).exists() for x in TARGETS):
            return d
    for z in [ROOT / 'IMOEN.zip', ROOT.parent / 'IMOEN.zip', Path.home() / 'Downloads' / 'IMOEN.zip']:
        if not z.is_file():
            continue
        try:
            with zipfile.ZipFile(z) as archive:
                members = [n for n in archive.namelist() if ident(n) and n.lower().endswith('.wav')]
                names = {Path(n).stem.upper() for n in members}
                if not all(t in names for t in TARGETS):
                    continue
                SOURCES.mkdir(exist_ok=True)
                for member in members:
                    name = Path(member).name
                    dest = SOURCES / name
                    # Basename-only extraction blocks ZIP traversal. Don't overwrite any local source.
                    if not dest.exists():
                        with archive.open(member) as r, dest.open('xb') as w:
                            shutil.copyfileobj(r,w)
                return SOURCES
        except (OSError, ValueError, zipfile.BadZipFile) as e:
            log('ZIP discovery: ' + repr(e))
    # Limited walk, excludes massive model/venv and existing generated audio.
    excluded = {'.tools','.git','.venv_qwen','.venv_seed','.venv_emotion32','OUTPUT','ANALYSIS','REFERENCE_AUDIO','BG_VOICE_BACKUPS'}
    for base in [ROOT, ROOT.parent]:
        if not base.exists():
            continue
        for dirpath, dirs, files in os.walk(base):
            d = Path(dirpath)
            if len(d.relative_to(base).parts) > 5:
                dirs[:] = []
                continue
            dirs[:] = [x for x in dirs if x not in excluded and not x.startswith('.venv') and not x.startswith('BG_VOICE_BACKUP_')]
            fs = {f.upper() for f in files}
            if all(t + '.WAV' in fs for t in TARGETS) and len([x for x in fs if x.startswith('IMOEN') and x.endswith('.WAV')]) >= 20:
                return d
    raise FileNotFoundError('English IMOEN originals not found. Copy the existing IMOEN folder or IMOEN.zip into bg_voice_release_v2 (do not use Russian OUTPUT).')

def read_manifest():
    manifest = ROOT / 'VOICE_MANIFEST.csv'
    rows = {}
    if not manifest.is_file():
        return rows
    with manifest.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        if not {'Resource', 'Russian_existing'} <= set(reader.fieldnames or []):
            return rows
        for r in reader:
            key = (r.get('Resource') or '').strip().upper()
            if key.startswith('IMOEN'):
                rows[key] = (r.get('Russian_existing') or '').split(' | ')[0].strip()
    return rows

def checksum(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def validate_source(d):
    mapping = {ident(p.name):p for p in d.glob('*.wav') if ident(p.name)}
    missing = [t for t in TARGETS if t not in mapping]
    if missing:
        raise RuntimeError('Missing originals: ' + ', '.join(missing))
    if len(mapping)<4:
        raise RuntimeError('Originals folder incomplete')
    return mapping

def make_resample_16k(src, key):
    """Return 16kHz mono PCM WAV in analysis cache, preserving input."""
    import numpy as np
    import soundfile as sf
    from scipy.signal import resample_poly
    data,sr=sf.read(str(src), dtype='float32', always_2d=True)
    if sr<=0 or not data.size:
        raise RuntimeError('Invalid source audio')
    mono=data.mean(axis=1)
    from math import gcd
    g=gcd(int(sr),16000)
    if sr!=16000:
        mono=resample_poly(mono,16000//g,int(sr)//g).astype('float32')
    if len(mono) < int(0.35*16000):
        raise RuntimeError('Source too short for emotion recognition')
    dest=OUT/'WAV16'/f'{key}_{checksum(src)[:12]}.wav'
    dest.parent.mkdir(parents=True,exist_ok=True)
    if not dest.exists():
        tmp=dest.with_suffix('.temp.wav')
        sf.write(str(tmp),mono,16000,subtype='PCM_16')
        tmp.replace(dest)
    return dest,mono

def boundaries(audio, sr=16000):
    """Segment long lines at energy valleys, ~2.5-4.5s. Not word alignment."""
    import numpy as np
    dur=len(audio)/sr
    if dur<=4.0:return [(0,len(audio))]
    hop=int(sr*0.025)
    frames=[]
    for j in range(0,len(audio),hop):
        x=audio[j:j+hop]
        if x.size:frames.append(float(np.sqrt(np.mean(x*x))))
    splits=[0]
    while (dur-splits[-1]/sr)>4.7:
        lo=splits[-1]+int(2.2*sr)
        target=splits[-1]+int(3.3*sr)
        hi=min(len(audio)-int(1.6*sr),splits[-1]+int(4.35*sr))
        if lo>=hi:break
        candidates=list(range(lo//hop, max(lo//hop+1,hi//hop)))
        ix=min(candidates,key=lambda i: frames[min(i,len(frames)-1)]+(abs(i*hop-target)/sr)*.001)
        sp=ix*hop
        if sp-splits[-1]<int(1.4*sr):break
        splits.append(sp)
    splits.append(len(audio))
    if len(splits)>2 and (splits[-1]-splits[-2])<int(1.45*sr):splits.pop(-2)
    return list(zip(splits[:-1],splits[1:]))

def parse_model_result(res):
    """Honor model-provided labels and scores; no fabricated emotion estimates."""
    import numpy as np
    if isinstance(res,list):
        if len(res)!=1:raise ValueError('Unexpected emotion output length')
        res=res[0]
    if not isinstance(res,dict):raise ValueError('Unexpected emotion output format: '+str(type(res)))
    labels=res.get('labels')
    scores=res.get('scores')
    if labels is None or scores is None:
        raise ValueError('Emotion model returned no labels/scores: '+str(list(res.keys())))
    labels=list(labels)
    scores=np.asarray(scores,dtype=float).squeeze().tolist()
    if not isinstance(scores,list):scores=[scores]
    if len(labels)!=len(scores) or not labels or any(not np.isfinite(v) for v in scores):
        raise ValueError('Invalid model emotion scores')
    ranked=sorted([(str(k).strip().lower(),float(v)) for k,v in zip(labels,scores)],key=lambda x:x[1],reverse=True)
    return ranked

def stats(audio, sr):
    import numpy as np
    hop=int(sr*0.04)
    rms=[]
    for i in range(0,len(audio),hop):
        x=audio[i:i+hop]
        if len(x)>0:rms.append(float(np.sqrt(np.mean(x*x))))
    arr=np.array(rms,dtype=float)
    return {'duration_s':round(len(audio)/sr,3),'rms':round(float(np.sqrt(np.mean(audio*audio))),5),'rms_max':round(float(np.max(arr)),5),'intensity_dynamic_db':round(float(20*np.log10((np.percentile(arr,95)+1e-5)/(np.percentile(arr,25)+1e-5))),1)}

def calc_emotion(model,wav):
    res=model.generate(str(wav),granularity='utterance',extract_embedding=False)
    return parse_model_result(res)

def infer_one(model,path,key,text,full):
    import numpy as np
    import soundfile as sf
    wav,a=make_resample_16k(path,key)
    emotions=calc_emotion(model,wav)
    segments=[]
    if full:
        for j,(start,end) in enumerate(boundaries(a)):
            piece=a[start:end]
            if len(piece)/16000<1.0:continue
            segment_file=OUT/'WAV16'/f'{key}_seg{j:02}.wav'
            if not segment_file.exists():sf.write(str(segment_file),piece,16000,subtype='PCM_16')
            ranking=calc_emotion(model,segment_file)
            segments.append({'start_s':round(start/16000,2),'end_s':round(end/16000,2),'ranking':ranking[:4]})
    return {'resource':key,'source_name':path.name,'source_sha256':checksum(path),'model':MODEL_ID,'model_ranking':emotions,'acoustic':stats(a,16000),'segments':segments,'russian_text':text,'human_notes':REVIEW.get(key,''),'generated_at':time.strftime('%Y-%m-%d %H:%M:%S')}

def load_cache():
    dest=OUT/'RESULTS_EMOTION_32.json'
    if not dest.exists():return {}
    try:
        return json.loads(dest.read_text(encoding='utf-8'))
    except (OSError,ValueError):
        log('Existing results invalid; not overwriting. Rename RESULTS_EMOTION_32.json manually to recover.')
        raise

def persist(results):
    dest=OUT/'RESULTS_EMOTION_32.json'
    temp=dest.with_suffix('.tmp')
    temp.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    os.replace(temp,dest)

def report(results,source_dir):
    with (OUT/'ACTING_PROFILES_32.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f)
        w.writerow(['resource','emotion_top','model_score','emotion_second','model_score_2','duration_s','rms','intensity_dynamic_db','acting_direction_hypothesis','english_sha256','russian_text','human_notes'])
        for key,r in sorted(results.items()):
            choices=r['model_ranking']
            a=choices[0];b=choices[1] if len(choices)>1 else ('unknown',0)
            st=r['acoustic']
            w.writerow([key,a[0],round(a[1],4),b[0],round(b[1],4),st['duration_s'],st['rms'],st['intensity_dynamic_db'],ACTING_STYLE.get(a[0],ACTING_STYLE['unknown']),r['source_sha256'],r['russian_text'],r['human_notes']])
    en = html.escape
    table=[]
    for key,r in sorted(results.items()):
        choices=r['model_ranking'][:3]
        labels=' / '.join(f'{RU_LABELS.get(k,k)} {v:.2f}' for k,v in choices)
        seg='; '.join(f'{s["start_s"]}-{s["end_s"]}с: {RU_LABELS.get(s["ranking"][0][0],s["ranking"][0][0])}' for s in r['segments'])
        table.append('<tr><td>'+en(key)+'</td><td>'+en(labels)+'</td><td>'+en(str(r['acoustic']['duration_s']))+'</td><td>'+en(r['russian_text'])+'</td><td>'+en(seg)+'</td><td>'+en(ACTING_STYLE.get(choices[0][0],ACTING_STYLE['unknown']))+'</td><td>'+en(r['human_notes'])+'</td></tr>')
    doc='''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Имоуэн — эмоции оригинала 3.2</title><style>
body{font:15px system-ui,Segoe UI,sans-serif;max-width:1300px;margin:24px auto;padding:0 14px;line-height:1.45}table{width:100%;border-collapse:collapse}td,th{border:1px solid #ddd;padding:9px;text-align:left;vertical-align:top}th{position:sticky;top:0;background:#eee;color:#111}tr:nth-child(2n){background:rgba(120,120,120,.06)}.warn{border-left:3px solid #b58c44;padding:8px 16px;background:rgba(128,128,128,.07)}
</style></head><body><h1>BG Voice RU — Emotion2vec+ 3.2</h1><p class="warn">Оценки модели — гипотезы, не достоверное определение эмоций, и не вероятность того, что актриса действительно испытывала эти чувства. Оригинальная актёрская подача, включая смех и хрипоту, проверяется на слух. «Хрипота», «дерзость», «смех» не входят в категории emotion2vec+.</p><p>Анализ выполнен <b>на оригинальных английских WAV</b>. Модель: iic/emotion2vec_plus_base, 16 kHz mono. Паузы и оттенки голоса требуют ручной режиссёрской проверки.</p><table><tr><th>Ресурс</th><th>Эмоции / оценки</th><th>Секунд</th><th>Русский перевод</th><th>Эмоции по фрагментам</th><th>Режиссёрская гипотеза</th><th>Пометки для проверки</th></tr>'''+''.join(table)+'</table></body></html>'
    (OUT/'REPORT_EMOTION_32.html').write_text(doc,encoding='utf-8')

def self_test():
    assert ident('IMOEN77A.wav')=='IMOEN77A'
    assert ident('../../hack.wav') is None
    # No model load; validates result normalization and absence of fake values.
    import numpy as np
    r=parse_model_result([{'labels':['neutral','happy'],'scores':[0.4,0.6]}])
    assert r[0][0]=='happy' and r[0][1]==0.6
    assert boundaries(np.zeros(16000*3,dtype=np.float32))==[(0,48000)]
    log('SELFTEST passed')

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--check',action='store_true')
    p.add_argument('--pilot',action='store_true')
    p.add_argument('--all',action='store_true')
    p.add_argument('--self-test',action='store_true')
    args=p.parse_args()
    if args.self_test:self_test();return
    source=find_sources()
    files=validate_source(source)
    texts=read_manifest()
    log('SOURCE '+str(source)+'; files='+str(len(files)))
    for key in TARGETS:
        log('CHECK '+key+' '+str(round(wav_len(files[key]),2))+'s')
    if args.check:
        log('CHECK OK. Existing Qwen models and voices untouched.')
        return
    if not args.pilot and not args.all:
        raise RuntimeError('Use --pilot or --all to run the actual model.')
    try:
        import torch
        from funasr import AutoModel
    except ImportError as e:
        raise RuntimeError('Install FunASR into the separate .venv_emotion32 using RUN_EMOTION_32.cmd') from e
    device='cuda' if torch.cuda.is_available() else 'cpu'
    # Isolate downloads from model construction. The checkpoint is ~1.12 GB;
    # total "4/9 files" is NOT a useful indicator of checkpoint progress.
    # Sequential downloads avoid multiple concurrent stalled requests. The HF
    # cache is reused, and no prior voices, models or generated WAVs are changed.
    from huggingface_hub import hf_hub_download
    revision='b318240bfe67db81a8c572ecb37ce9c3759b81c9'
    required=('config.yaml','configuration.json','tokens.txt','model.pt')
    resolved=[]
    for filename in required:
        log('MODEL FILE '+filename+' — checking cache / downloading if needed')
        if filename=='model.pt':
            log('MODEL WEIGHTS ~1.12 GB. This file can take much longer than the 3 small files.')
        try:
            local=Path(hf_hub_download(repo_id=MODEL_ID,filename=filename,revision=revision))
        except Exception as exc:
            log('DOWNLOAD ERROR on '+filename+': '+repr(exc))
            log('Already cached files are kept. Run again to retry; do not reinstall dependencies.')
            raise
        size=local.stat().st_size
        if size<1 or (filename=='model.pt' and size<500_000_000):
            raise RuntimeError('Unexpected model file size: '+filename+' '+str(size))
        log('MODEL FILE READY '+filename+' '+str(round(size/1048576,1))+' MiB')
        resolved.append(local)
    model_dir=resolved[0].parent
    if any(p.parent!=model_dir for p in resolved):
        raise RuntimeError('Model files resolved from different snapshots')
    log('LOADING local complete emotion2vec+ model on '+device+' (no new hub download)')
    try:
        model=AutoModel(model=str(model_dir),device=device,disable_update=True)
    except Exception as exc:
        log('MODEL LOAD ERROR (weights already downloaded): '+repr(exc))
        log('Do not reinstall Python, Torch, Qwen, or redownload the files.')
        raise
    results=load_cache()
    keys=list(TARGETS) if args.pilot else sorted(files)
    errors=[]
    for i,key in enumerate(keys,1):
        path=files[key]
        if wav_len(path)<.35:
            log('SKIP short or unsupported WAV: '+key);continue
        previous=results.get(key)
        if previous and previous.get('source_sha256')==checksum(path) and previous.get('model')==MODEL_ID:
            log(f'KEEP {i}/{len(keys)} {key}');continue
        try:
            log(f'ANALYZE {i}/{len(keys)} {key}')
            results[key]=infer_one(model,path,key,texts.get(key,''),key in TARGETS)
            persist(results)
            report(results,source)
            log('DONE '+key+' '+RU_LABELS.get(results[key]['model_ranking'][0][0],'unknown'))
        except Exception as e:
            errors.append(key)
            log('ERROR '+key+' '+repr(e))
    report(results,source)
    log(f'FINISH {len(results)} profiles, errors={len(errors)}; see ANALYSIS/REPORT_EMOTION_32.html')
    if errors:sys.exit(2)

if __name__=='__main__':
    try:main()
    except Exception as exc:
        log('STOP '+repr(exc))
        sys.exit(1)