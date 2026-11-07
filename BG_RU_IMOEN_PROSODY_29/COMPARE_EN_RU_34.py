# -*- coding: utf-8 -*-
"""BG Voice RU 3.4: compare original English acting vs Russian WHOLE/PARTS.
Read-only for source audio, Qwen and game. Uses cached emotion2vec+ weights and
existing English inference; does not download models or invent emotion scores.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import html
import json
import os
from pathlib import Path
import shutil
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ANALYSIS = HERE / 'ANALYSIS'
OUT = ANALYSIS / 'COMPARE_EN_RU_34'
EN_RESULTS = ANALYSIS / 'RESULTS_EMOTION_32.json'
RU_CACHE = OUT / 'RU_EMOTION_CACHE_34.json'
TARGETS = ('IMOEN06_', 'IMOEN77A', 'IMOEN79A', 'IMOEN79B')
RU_EMOTIONS = {
    'angry':'злость/раздражение','disgusted':'отвращение','fearful':'страх',
    'happy':'радость','neutral':'нейтральная речь','other':'другая эмоция',
    'sad':'грусть','surprised':'удивление','unknown':'не определено',
}
DIRECTING = {
    'happy': 'Живее и звонче; если в оригинале слышен смех, передать отдельным звуком.',
    'angry': 'Больше дерзости или напряжения, точнее смысловые акценты; не обязательно крик.',
    'fearful': 'Настороженность, нервное дыхание и темп — сверять по оригиналу.',
    'sad': 'Более сдержанная, приглушённая подача без автоматического шёпота.',
    'surprised': 'Живой подъём тона и подчёркивание ключевого слова.',
    'neutral': 'Разговорная естественность; не делать каждую фразу одинаково нежной.',
    'disgusted': 'Проверить неприязнь или отстранение по оригиналу.',
    'other': 'Неясная эмоция: прослушать и решить вручную.',
    'unknown': 'Неопределённая эмоция: прослушать и решить вручную.',
}
NOTES = {
    'IMOEN06_':'«Ха!» в оригинале — смех, а не слово. Классификатор не распознаёт смех отдельно.',
    'IMOEN77A':'Приветствие, отдельный смешок, вопрос и просьба могут иметь разные эмоции.',
    'IMOEN79A':'Проверить ударение и вопросительный тон на «Ты уверен?».',
    'IMOEN79B':'Во второй половине вопроса не должен возникать другой, чужой тембр.',
}


def log(s: str) -> None:
    print(time.strftime('%H:%M:%S') + ' ' + str(s), flush=True)


def canonical(label: str) -> str:
    value = str(label).strip().lower()
    if value in RU_EMOTIONS:
        return value
    if '/' in value:
        for piece in reversed(value.split('/')):
            piece = piece.strip()
            if piece in RU_EMOTIONS:
                return piece
    return 'unknown'


def sorted_scores(ranking) -> list[tuple[str,float]]:
    out = []
    for name, value in ranking:
        score = float(value)
        if not 0 <= score <= 1.001:
            raise ValueError('Unusable model score')
        out.append((canonical(name), score))
    return sorted(out, key=lambda r:-r[1])


def file_sha(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()


def get_originals() -> dict:
    if not EN_RESULTS.is_file():
        raise FileNotFoundError('No original-English emotion analysis: '+str(EN_RESULTS))
    rows=json.loads(EN_RESULTS.read_text(encoding='utf-8'))
    if not isinstance(rows,dict):
        raise ValueError('Original-English JSON has wrong format')
    absent=[k for k in TARGETS if k not in rows or not rows[k].get('model_ranking')]
    if absent:
        raise ValueError('English emotion model has not analyzed: '+', '.join(absent))
    return rows


def find_ru_files() -> dict:
    # Prefer the local generated output from 2.9. Never overwrite this directory.
    dirs=(HERE/'OUTPUT', ROOT/'OUTPUT', ROOT/'BG_RU_IMOEN_PROSODY_29'/'OUTPUT')
    for directory in dirs:
        candidates={(key,mode): directory/(key+'_'+mode+'_29.wav')
                    for key in TARGETS for mode in ('WHOLE','PARTS')}
        if all(p.is_file() for p in candidates.values()):
            return candidates
    # User's earlier OUTPUT.zip can be used as a fallback. Extract only eight
    # exact names into our own analysis folder; never into source OUTPUT.
    archives=(HERE/'OUTPUT.zip',ROOT/'OUTPUT.zip', ROOT.parent/'OUTPUT.zip')
    for archive in archives:
        if not archive.is_file():
            continue
        import zipfile
        candidates={(key,mode):key+'_'+mode+'_29.wav'
                    for key in TARGETS for mode in ('WHOLE','PARTS')}
        with zipfile.ZipFile(archive) as z:
            all_names={Path(x).name:x for x in z.namelist() if not x.endswith('/')}
            if not all(n in all_names for n in candidates.values()):
                continue
            dest=OUT/'RU_SOURCES_FROM_ZIP'
            dest.mkdir(parents=True,exist_ok=True)
            files={}
            for pair,name in candidates.items():
                d=dest/name
                if not d.exists():
                    with z.open(all_names[name]) as src, d.open('xb') as dst:
                        shutil.copyfileobj(src,dst)
                files[pair]=d
            return files
    raise FileNotFoundError('No eight Russian WHOLE/PARTS WAV. Expected '+str(HERE/'OUTPUT')+' or OUTPUT.zip in project root')


def validate(files:dict) -> None:
    import wave
    for (key,mode),path in files.items():
        if path.stat().st_size < 4096:
            raise ValueError('Suspiciously small WAV '+path.name)
        with wave.open(str(path),'rb') as w:
            if w.getframerate()<16000 or w.getnframes()<8000:
                raise ValueError('Invalid WAV '+path.name)


def model_local_only():
    # A successful original English analysis means these weights are already
    # cached. Refuse to download a second time or modify anything.
    os.environ['HF_HUB_OFFLINE']='1'
    os.environ['HF_HUB_DISABLE_TELEMETRY']='1'
    from huggingface_hub import hf_hub_download
    revision='b318240bfe67db81a8c572ecb37ce9c3759b81c9'
    paths=[]
    for filename in ('config.yaml','configuration.json','tokens.txt','model.pt'):
        try:
            p=Path(hf_hub_download(repo_id='emotion2vec/emotion2vec_plus_base',
                                    filename=filename,revision=revision,local_files_only=True))
        except Exception as exc:
            raise RuntimeError('Model cache incomplete ('+filename+'). No downloads made; rerun the previous working RUN_EMOTION_32.cmd once.') from exc
        paths.append(p)
    if any(p.parent!=paths[0].parent for p in paths):
        raise RuntimeError('Model cache files are in different snapshot directories')
    from funasr import AutoModel
    import torch
    device='cuda' if torch.cuda.is_available() else 'cpu'
    log('LOADING existing emotion2vec+ weights locally, '+device+'; NO DOWNLOADS')
    return AutoModel(model=str(paths[0].parent),device=device,disable_update=True)


def load_ru_cache() -> dict:
    if not RU_CACHE.exists(): return {}
    data=json.loads(RU_CACHE.read_text(encoding='utf-8'))
    if not isinstance(data,dict):raise ValueError('Bad RU emotion cache; not replacing it')
    return data


def save_json_atomic(path:Path,obj) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.partial')
    tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
    os.replace(tmp,path)


def infer_one(model, audio_path:Path, key:str, mode:str, source_hash:str) -> dict:
    import numpy as np
    import soundfile as sf
    from scipy.signal import resample_poly
    from math import gcd
    a,sr=sf.read(str(audio_path),dtype='float32',always_2d=True)
    a=a.mean(axis=1)
    if sr!=16000:
        div=gcd(int(sr),16000)
        a=resample_poly(a,16000//div,int(sr)//div).astype('float32')
    processed=OUT/'WAV16'/(key+'_'+mode+'_'+source_hash[:12]+'.wav')
    processed.parent.mkdir(parents=True,exist_ok=True)
    if not processed.is_file():
        tmp=processed.with_suffix('.partial.wav')
        sf.write(str(tmp),a,16000,subtype='PCM_16')
        os.replace(tmp,processed)
    import EMOTION_ANALYSIS_32 as base
    ranked=sorted_scores(base.calc_emotion(model,processed))
    segs=[]
    if mode=='PARTS':
        for n,(start,end) in enumerate(base.boundaries(a)):
            if n>11:break
            if (end-start)/16000<1.0:continue
            p=OUT/'WAV16'/(key+'_'+mode+'_'+source_hash[:12]+'_seg%02d.wav'%n)
            if not p.is_file():
                tmp=p.with_suffix('.partial.wav')
                sf.write(str(tmp),a[start:end],16000,subtype='PCM_16')
                os.replace(tmp,p)
            segs.append({'start_s':round(start/16000,2),'end_s':round(end/16000,2),
                         'ranking':sorted_scores(base.calc_emotion(model,p))[:4]})
    rms=float(np.sqrt(np.mean(a*a)))
    return {'resource':key,'mode':mode,'sha256':source_hash,'duration_s':round(len(a)/16000,2),
            'rms':round(rms,6),'ranking':ranked,'segments':segs,
            'engine':'emotion2vec/emotion2vec_plus_base',
            'completed_at':time.strftime('%Y-%m-%d %H:%M:%S')}


def compare(en:dict,ru:dict) -> list[dict]:
    rows=[]
    for key in TARGETS:
        en_scores=sorted_scores(en[key]['model_ranking'])
        for mode in ('WHOLE','PARTS'):
            r=ru[key+'_'+mode]
            scores=sorted_scores(r['ranking'])
            e,er=en_scores[0];q,qr=scores[0]
            attention=(e!=q and er>=0.55 and qr>=0.55)
            rows.append({'resource':key,'mode':mode,'english_emotion':e,'english_score':round(er,3),
                         'russian_emotion':q,'russian_score':round(qr,3),
                         'different_main_labels':e!=q,'review_priority':('CHECK' if attention else 'LISTEN'),
                         'english_duration_s':en[key]['acoustic']['duration_s'],
                         'russian_duration_s':r['duration_s'],
                         'human_note':NOTES[key],
                         'directing_suggestion':DIRECTING[e]})
    return rows


def render(en:dict,ru:dict,paths:dict) -> None:
    OUT.mkdir(parents=True,exist_ok=True)
    rows=compare(en,ru)
    outcsv=OUT/'EN_RU_EMOTION_COMPARISON_34.csv'
    with outcsv.open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)
    # Create self-contained playable report references, never alter sources.
    audio=OUT/'AUDIO';audio.mkdir(exist_ok=True)
    original_dir=HERE/'ORIGINAL_EN'
    import EMOTION_ANALYSIS_32 as base
    originals=base.validate_source(base.find_sources())
    for key in TARGETS:
        src=originals[key]
        dst=audio/(key+'_EN.wav')
        if not dst.exists():shutil.copyfile(src,dst)
        for mode in ('WHOLE','PARTS'):
            src=paths[(key,mode)]
            dst=audio/(key+'_'+mode+'_RU.wav')
            if not dst.exists() or file_sha(dst)!=file_sha(src):
                # Previously exported comparators are output-only, never the original.
                shutil.copyfile(src,dst)
    h=html.escape
    lines=['<!doctype html><html lang="ru"><meta charset="utf-8"><title>Имоуэн — сравнение оригинала и русского 3.4</title>',
           '<style>body{font:15px system-ui;max-width:1050px;margin:20px auto;padding:0 15px;line-height:1.45}section{border:1px solid #aaa8;border-radius:10px;padding:14px;margin:18px 0}audio{width:100%;margin:8px 0}table{width:100%;border-collapse:collapse}td,th{padding:8px;text-align:left;border-bottom:1px solid #aaa7}small{color:#666}</style>',
           '<h1>Имоуэн — английский оригинал и русские WHOLE / PARTS</h1>',
           '<p>Результаты <strong>двух сторон</strong> вычислены emotion2vec+. Оценки условные; одинаковые или разные метки не доказывают совпадение актёрской игры. Смех, хрипота и дерзость не являются отдельными классами модели.</p>']
    for key in TARGETS:
        src_en=sorted_scores(en[key]['model_ranking']);en1=src_en[0]
        lines.extend(['<section><h2>'+h(key)+'</h2>',
                      '<p><b>Английский оригинал:</b> '+h(RU_EMOTIONS[en1[0]])+' — '+f'{en1[1]:.2f}'+'</p>',
                      '<audio controls preload="none" src="AUDIO/'+key+'_EN.wav"></audio>',
                      '<table><tr><th>Версия</th><th>Главная метка</th><th>Оценка</th><th>Отметка</th></tr>'])
        for mode in ('WHOLE','PARTS'):
            x=next(i for i in rows if i['resource']==key and i['mode']==mode)
            lines.append('<tr><td>'+mode+'</td><td>'+h(RU_EMOTIONS[x['russian_emotion']])+'</td><td>'+str(x['russian_score'])+'</td><td>'+h(x['review_priority'])+'</td></tr>')
        lines.append('</table>')
        for mode in ('WHOLE','PARTS'):
            lines.append('<p><b>Русский '+mode+'</b></p><audio controls preload="none" src="AUDIO/'+key+'_'+mode+'_RU.wav"></audio>')
        english_segments=en[key].get('segments',[])
        russian_segments=ru[key+'_PARTS'].get('segments',[])
        if english_segments or russian_segments:
            lines.append('<details><summary>Метки по временным отрезкам (без привязки к словам)</summary>')
            for lab,segs in (('EN',english_segments),('RU PARTS',russian_segments)):
                lines.append('<p><b>'+lab+':</b> '+h('; '.join(f'{s["start_s"]}–{s["end_s"]}с {RU_EMOTIONS[sorted_scores(s["ranking"])[0][0]]}' for s in segs) or 'Нет отдельных отрезков')+'</p>')
            lines.append('</details>')
        lines.append('<p><b>Режиссёрская цель:</b> '+h(DIRECTING[en1[0]])+'</p><p><b>Особенность:</b> '+h(NOTES[key])+'</p></section>')
    lines.append('<small>Файлы EN и RU в отчёте — только копии для прослушивания; исходные WAV неизменны. Сравнение эмоций не копирует интонацию автоматически.</small></html>')
    (OUT/'LISTEN_EN_RU_34.html').write_text('\n'.join(lines),encoding='utf-8')
    log('SAVED '+str(outcsv))
    log('OPEN '+str(OUT/'LISTEN_EN_RU_34.html'))


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument('--check',action='store_true',help='Verify input files without downloading or loading the emotion model')
    p.add_argument('--report-only',action='store_true',help='Rebuild comparison from existing saved EN and RU scores')
    args=p.parse_args()
    en=get_originals()
    paths=find_ru_files();validate(paths)
    log('CHECK OK: 4 cached English profiles, 8 Russian WAV, no Qwen/game modifications')
    if args.check:return
    cache=load_ru_cache()
    if not args.report_only:
        work=[]
        for (key,mode),path in paths.items():
            hash=file_sha(path)
            id=key+'_'+mode
            if id in cache and cache[id].get('sha256')==hash and cache[id].get('ranking'):
                log('KEEP '+id+' (cached Russian emotion scores)')
            else:work.append((id,key,mode,path,hash))
        if work:
            model=model_local_only()
            for index,(id,key,mode,path,hash) in enumerate(work,1):
                log('ANALYZE RU '+str(index)+'/'+str(len(work))+' '+id)
                cache[id]=infer_one(model,path,key,mode,hash)
                save_json_atomic(RU_CACHE,cache)
                log('DONE '+id+' -> '+RU_EMOTIONS[sorted_scores(cache[id]['ranking'])[0][0]])
            del model
    missed=[key+'_'+mode for key in TARGETS for mode in ('WHOLE','PARTS') if not cache.get(key+'_'+mode)]
    if missed:
        raise RuntimeError('Missing Russian emotion results: '+', '.join(missed))
    render(en,cache,paths)
    log('FINISH: 4 original English + 8 Russian recordings, report ready')

if __name__=='__main__':
    try:main()
    except Exception as e:
        log('STOP '+repr(e))
        raise SystemExit(1)
