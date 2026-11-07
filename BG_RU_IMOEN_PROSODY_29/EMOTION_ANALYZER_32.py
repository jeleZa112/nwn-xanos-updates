# -*- coding: utf-8 -*-
"""BG Voice RU 3.2: verified local emotion2vec+ annotation, no speech generation."""
import argparse, csv, html, json, math, os, sys, wave, zipfile
from pathlib import Path
from datetime import datetime

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = HERE/'EMOTION_32_RESULTS'
TARGETS = ('IMOEN06_', 'IMOEN77A', 'IMOEN79A', 'IMOEN79B')
MODEL_NAME = 'iic/emotion2vec_plus_base'
LABEL_RU = {'angry':'злость','disgusted':'отвращение','fearful':'страх',
            'happy':'радость','neutral':'нейтрально','other':'другое',
            'sad':'грусть','surprised':'удивление','unknown':'неопределённо'}
KNOWN_LABELS = set(LABEL_RU)

def log(message):
    print(str(message),flush=True)

def find_source():
    # Local WAVs preferred; do not move or alter any originals.
    roots=[ROOT/'RVC_DATASETS'/'IMOEN', ROOT/'BG_RU_FULL_17'/'IMOEN',
           ROOT/'BG_VOICE_RU_VOICE_TRAIN_2_0'/'IMOEN',ROOT/'IMOEN',
           HERE/'ORIGINAL_EN',ROOT/'BG_RU_IMOEN_PROSODY_29'/'ORIGINAL_EN']
    for d in roots:
        if d.is_dir() and sum(p.is_file() for p in d.glob('IMOEN*.wav'))>=4:
            return ('dir',d)
    archives=[ROOT/'IMOEN.zip', HERE/'IMOEN.zip', ROOT/'RVC_DATASETS'/'IMOEN.zip']
    for p in archives:
        if p.is_file():
            with zipfile.ZipFile(p) as z:
                if sum(Path(n).suffix.lower()=='.wav' and Path(n).stem.upper().startswith('IMOEN') for n in z.namelist())>=4:
                    return ('zip',p)
    # Read-only limited directory scan rather than requiring user to locate files.
    for d in [ROOT/'RVC_DATASETS',ROOT/'BG_RU_FULL_17',ROOT/'BG_VOICE_RU_VOICE_TRAIN_2_0']:
        if d.is_dir():
            for sub in d.rglob('*'):
                if sub.is_dir() and sum(1 for _ in sub.glob('IMOEN*.wav'))>=4:
                    return ('dir',sub)
    raise FileNotFoundError('Cannot find English IMOEN WAVs. Copy your existing IMOEN.zip next to EMOTION_ANALYZER_32.py, then rerun.')

def copy_sources(source, wanted):
    dest=OUT/'INPUT_16K'
    dest.mkdir(parents=True,exist_ok=True)
    import numpy as np
    import soundfile as sf
    from scipy.signal import resample_poly
    files={}
    if source[0]=='dir':
        found={p.stem.upper():p for p in source[1].glob('*.wav')}
        entries=[(key,found[key]) for key in wanted if key in found]
    else:
        z=zipfile.ZipFile(source[1]);found={Path(n).stem.upper():n for n in z.namelist() if n.lower().endswith('.wav')}
        entries=[(key,found[key]) for key in wanted if key in found]
    for key,item in entries:
        dst=dest/(key+'.wav')
        if dst.exists():
            # Refuse to silently replace existing extracted sources.
            with sf.SoundFile(dst) as s:
                if s.samplerate==16000 and s.frames>1000:
                    files[key]=dst;continue
            raise ValueError('Invalid existing 16k source: '+str(dst))
        if source[0]=='dir':
            audio,sr=sf.read(str(item),always_2d=True,dtype='float32')
        else:
            import io
            audio,sr=sf.read(io.BytesIO(z.read(item)),always_2d=True,dtype='float32')
        audio=audio.mean(axis=1)
        if sr!=16000:
            g=math.gcd(sr,16000)
            audio=resample_poly(audio,16000//g,sr//g).astype(np.float32)
        if not 0.15<=len(audio)/16000<=120:continue
        sf.write(str(dst),audio,16000,subtype='PCM_16')
        files[key]=dst
    if source[0]=='zip':z.close()
    return files

def segments(audio,sr=16000):
    import numpy as np
    # Non-speech pauses only: no emotion/laughter fabricated from acoustic cues.
    hop=160; win=320
    if len(audio)<win:return [(0,len(audio)/sr)]
    rms=np.array([np.sqrt(np.mean(audio[i:i+win]**2)) for i in range(0,len(audio)-win,hop)])
    threshold=max(0.006,float(np.percentile(rms,80))*.14)
    silent=rms<threshold
    cut=[0]
    start=None
    for i,quiet in enumerate(silent):
        if quiet and start is None:start=i
        if not quiet and start is not None:
            if (i-start)*hop/sr>=.28:
                mid=(start+i)*hop/(2*sr)
                if mid-cut[-1]>=.65 and len(audio)/sr-mid>=.65:cut.append(mid)
            start=None
    cut.append(len(audio)/sr)
    ranges=[]
    for a,b in zip(cut,cut[1:]):
        if b-a>=.6:ranges.append((round(a,3),round(b,3)))
    # Limit model calls on very segmented recordings.
    if len(ranges)>8:return [(0,len(audio)/sr)]
    return ranges or [(0,len(audio)/sr)]

def parse_result(raw):
    """Accept only real model scores; fail closed on unknown formats."""
    if isinstance(raw,list):
        if len(raw)!=1:raise ValueError('Unexpected model batch size: '+str(len(raw)))
        raw=raw[0]
    if not isinstance(raw,dict):raise ValueError('Unexpected model output type')
    labs=raw.get('labels')
    vals=raw.get('scores')
    if labs is None or vals is None:
        raise ValueError('Model returned no labels/scores; keys='+repr(list(raw)))
    if hasattr(vals,'tolist'):vals=vals.tolist()
    if hasattr(labs,'tolist'):labs=labs.tolist()
    if len(vals)!=len(labs) or not labs:raise ValueError('Model score length mismatch')
    result=[]
    for label,val in zip(labs,vals):
        label=str(label).lower().strip()
        v=float(val)
        if not math.isfinite(v):raise ValueError('Nonfinite emotion score')
        result.append((label,v))
    # Scores are model relative scores, do not call them calibrated probabilities.
    return sorted(result,key=lambda x:-x[1])

def analyze(model,files,per_segment=True):
    import numpy as np
    import soundfile as sf
    rows=[]
    for i,(key,p) in enumerate(sorted(files.items()),1):
        log(f'[{i}/{len(files)}] {key}')
        audio,sr=sf.read(str(p),dtype='float32')
        spans=[(0,round(len(audio)/sr,3),'whole')]
        if per_segment:
            chunks=segments(audio,sr)
            # Avoid redundant segments where the whole audio is effectively one chunk.
            if len(chunks)>1:spans.extend((a,b,'part') for a,b in chunks)
        for a,b,kind in spans:
            chunk=audio[int(a*sr):int(b*sr)]
            if len(chunk)<sr*.5:continue
            tmp=OUT/'INPUT_16K'/'_segment_processing.wav'
            sf.write(str(tmp),chunk,sr,subtype='PCM_16')
            try:
                raw=model.generate(input=str(tmp),granularity='utterance',extract_embedding=False)
                scored=parse_result(raw)
            finally:
                if tmp.exists():tmp.unlink()
            # Note uncertainty. Nine labels is not sarcasm, laughter or rasp detector.
            best=scored[0]
            rows.append({'resource':key,'kind':kind,'start_s':a,'end_s':b,
                         'emotion_en':best[0],'emotion_ru':LABEL_RU.get(best[0],best[0]),
                         'score':round(best[1],4),'all_scores':json.dumps(dict(scored),ensure_ascii=False),
                         'needs_human_review':'YES' if best[0] in ('neutral','other','unknown') or best[1]<.5 else 'CHECK',
                         'laughter':'NOT_CLASSIFIED','rasp':'NOT_CLASSIFIED'})
    return rows

def generate_report(rows,all_count):
    OUT.mkdir(parents=True,exist_ok=True)
    csvfile=OUT/'EMOTION_SCORES.csv'
    fields=['resource','kind','start_s','end_s','emotion_en','emotion_ru','score','all_scores','needs_human_review','laughter','rasp']
    with csvfile.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    by={}
    for r in rows:by.setdefault(r['resource'],[]).append(r)
    lines=['<!doctype html><html lang="ru"><meta charset="utf-8"><title>Имоуэн — эмоции 3.2</title>',
           '<style>body{font:16px system-ui;max-width:1020px;margin:20px auto;padding:12px}article{border:1px solid #ccc;border-radius:10px;padding:14px;margin:15px 0}audio{display:block;width:100%;margin:8px 0}table{border-collapse:collapse;width:100%}td,th{padding:6px;border-bottom:1px solid #ddd;text-align:left}</style>',
           '<h1>Имоуэн — emotion2vec+ base, фактические оценки</h1>',
           '<p>Оценки модели не являются достоверной режиссурой. Смех, сарказм и хрипотца автоматически НЕ классифицируются. Отмечайте их при прослушивании оригинала.</p>',
           '<p>Обработано оригиналов: '+str(len(by))+' из '+str(all_count)+'</p>']
    for key,group in sorted(by.items()):
        lines.append('<article><h2>'+html.escape(key)+'</h2><audio controls src="INPUT_16K/'+html.escape(key)+'.wav"></audio><table><tr><th>Фрагмент</th><th>Время</th><th>Категория модели</th><th>Оценка</th></tr>')
        for r in group:
            lines.append(f'<tr><td>{r["kind"]}</td><td>{r["start_s"]:.2f}–{r["end_s"]:.2f}</td><td>{html.escape(r["emotion_ru"])}</td><td>{r["score"]:.3f}</td></tr>')
        lines.append('</table><p>Режиссёрская проверка: смех/вздох/хрипотца, характер вопроса, изменение тембра, место эмоционального акцента.</p></article>')
    lines.append('</html>')
    (OUT/'LISTEN_EMOTIONS.html').write_text('\n'.join(lines),encoding='utf-8')
    log('SAVED '+str(csvfile))
    log('OPEN '+str(OUT/'LISTEN_EMOTIONS.html'))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--all',action='store_true',help='All available English originals')
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    source=find_source()
    log('SOURCE '+str(source[1]))
    if source[0]=='dir':
        keys=sorted({p.stem.upper() for p in source[1].glob('IMOEN*.wav')})
    else:
        with zipfile.ZipFile(source[1]) as z:
            keys=sorted({Path(p).stem.upper() for p in z.namelist() if p.lower().endswith('.wav')})
    wanted=keys if args.all else TARGETS
    if not args.all and any(k not in keys for k in TARGETS):
        raise ValueError('Missing pilot originals: '+str(set(TARGETS)-set(keys)))
    log(f'FOUND {len(keys)} sources; SELECTED {len(wanted)}')
    if args.check:return
    files=copy_sources(source,wanted)
    from funasr import AutoModel
    log('Loading emotion2vec+ base; model files may download on first use (separate environment).')
    model=AutoModel(model=MODEL_NAME,device='cpu',disable_update=True)
    rows=analyze(model,files)
    generate_report(rows,len(keys))
    log('DONE. No Rask/Qwen/game/WAV originals changed.')
if __name__=='__main__':
    try:main()
    except Exception as exc:
        log('ERROR '+repr(exc))
        sys.exit(1)