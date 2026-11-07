# -*- coding: utf-8 -*-
"""BG Voice RU 3.2: actual emotion2vec inference, original English WAV only."""
import argparse
import base64
import csv
import html
import json
import os
import sys
import traceback
import wave
import zipfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
OUT=HERE/"REPORTS"
SRC=HERE/"SOURCE_EN"
NAMES=("IMOEN06_","IMOEN77A","IMOEN79A","IMOEN79B")
TRANSLATE={"angry":"злость","disgusted":"отвращение","fearful":"страх","happy":"радость","neutral":"нейтральная","other":"другое","sad":"грусть","surprised":"удивление","unknown":"неизвестно"}
MODEL_ID="iic/emotion2vec_plus_base"

def log(s):
    print(s,flush=True)
    OUT.mkdir(parents=True,exist_ok=True)
    with (OUT/"EMOTION_RUN.log").open("a",encoding="utf-8") as f:
        f.write(str(s)+"\n")

def candidate_files(names):
    found={}
    targets={n.upper()+".WAV":n for n in names}
    roots=[SRC,ROOT/"RVC_DATASETS"/"IMOEN",ROOT/"BG_RU_FULL_17",ROOT/"BG_RU_IMOEN_PROSODY_29"/"ORIGINAL_EN",ROOT/"ORIGINAL_EN",ROOT/"IMOEN"]
    for d in roots:
        if not d.exists():continue
        for path, dirs, files in os.walk(d):
            dirs[:]=[x for x in dirs if not x.startswith(".") and x.lower() not in ("output","reports","models",".venv_qwen")]
            for name in files:
                key=targets.get(name.upper())
                if key and key not in found:found[key]=Path(path)/name
    # Discover source archives in root or extracted dataset folder, without modifying originals.
    for archive in [ROOT/"IMOEN.zip",ROOT/"RVC_DATASETS"/"IMOEN.zip"]:
        if not archive.is_file():continue
        with zipfile.ZipFile(archive) as z:
            for entry in z.infolist():
                target=targets.get(Path(entry.filename).name.upper())
                if not target or target in found or entry.is_dir():continue
                if entry.file_size>15_000_000:raise ValueError("Unexpectedly large WAV in archive")
                SRC.mkdir(exist_ok=True)
                to=SRC/(target+".wav")
                if not to.exists():
                    with z.open(entry) as source,to.open("xb") as dest:
                        import shutil
                        shutil.copyfileobj(source,dest)
                found[target]=to
    return found

def sample_audio(path):
    import numpy as np
    import soundfile as sf
    from scipy.signal import resample_poly
    import math
    data,sr=sf.read(str(path),dtype="float32",always_2d=True)
    if data.shape[0]==0:raise ValueError("Empty WAV")
    mono=data.mean(axis=1)
    if sr!=16000:
        g=math.gcd(sr,16000)
        mono=resample_poly(mono,16000//g,sr//g).astype("float32")
    if not np.isfinite(mono).all():raise ValueError("Invalid samples")
    return mono,16000

def extract_scores(obj):
    # FunASR emotion2vec returns list of dicts {labels:[...],scores:[...]}.
    if isinstance(obj,list):
        if not obj:raise ValueError("Empty emotion result")
        obj=obj[0]
    if not isinstance(obj,dict):raise ValueError("Unexpected emotion result type")
    labels=obj.get("labels",[])
    scores=obj.get("scores",[])
    if hasattr(labels,"tolist"):labels=labels.tolist()
    if hasattr(scores,"tolist"):scores=scores.tolist()
    if len(labels)!=len(scores) or not labels:raise ValueError("Emotion model returned no labels/scores")
    items={}
    for name,value in zip(labels,scores):
        label=str(name).strip().lower()
        if label.startswith("emotion/"):label=label.split("/")[-1]
        items[label]=round(float(value),5)
    return dict(sorted(items.items(),key=lambda p:-p[1]))

def safe_name(name):
    if not name.startswith("IMOEN") or not all(c.isalnum() or c=="_" for c in name):
        raise ValueError("Invalid resource name")
    return name

def save_wav(path,data,sr):
    import soundfile as sf
    sf.write(str(path),data,sr,subtype="PCM_16")

def run_model(model,path,name,window_seconds):
    import numpy as np
    mono,sr=sample_audio(path)
    dur=round(len(mono)/sr,3)
    # ModelScope/FunASR expects 16k speech input.
    cache=OUT/"CACHE_16K"
    cache.mkdir(exist_ok=True)
    input_file=cache/(safe_name(name)+".wav")
    if not input_file.exists():save_wav(input_file,mono,sr)
    global_res=model.generate(input=str(input_file),granularity="utterance",extract_embedding=False)
    overall=extract_scores(global_res)
    windows=[]
    # Short overlapping windows can miss context and laughter; mark as tentative.
    if dur>=4.5:
        length=int(window_seconds*sr)
        stride=int(max(window_seconds-0.7,1.0)*sr)
        for start in range(0,len(mono)-int(sr),stride):
            stop=min(start+length,len(mono))
            if (stop-start)/sr<1.4:break
            temp=cache/(safe_name(name)+f"_part_{start:08d}.wav")
            if not temp.exists():save_wav(temp,mono[start:stop],sr)
            res=model.generate(input=str(temp),granularity="utterance",extract_embedding=False)
            scores=extract_scores(res)
            windows.append({"start":round(start/sr,2),"end":round(stop/sr,2),"top":next(iter(scores)),"scores":scores})
            if stop==len(mono):break
    return {"resource":name,"original_wav":str(path),"duration_s":dur,"overall":overall,"windows":windows,"status":"model_inference"}

def export(results,scope):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/("EMOTIONS_"+scope+".json")).write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding="utf-8")
    csvpath=OUT/("EMOTIONS_"+scope+".csv")
    with csvpath.open("w",newline="",encoding="utf-8-sig") as f:
        writer=csv.writer(f)
        writer.writerow(["resource","duration_s","segment_start","segment_end","emotion","score","source","human_verification","remarks"])
        for r in results:
            if r.get("status")!="model_inference":
                writer.writerow([r["resource"],"","","","","","ERROR","REQUIRES_REVIEW",r.get("error","")]);continue
            for label,score in r["overall"].items():
                writer.writerow([r["resource"],r["duration_s"],0,r["duration_s"],label,score,"emotion2vec+ whole","REQUIRES_REVIEW","not calibrated probability"])
            for seg in r["windows"]:
                for label,score in seg["scores"].items():
                    writer.writerow([r["resource"],r["duration_s"],seg["start"],seg["end"],label,score,"emotion2vec+ segment","REQUIRES_REVIEW","short window; verify laughter and delivery"])
    page=['<!doctype html><html lang="ru"><meta charset="utf-8"><title>BG Voice RU — эмоции</title><style>body{font:16px system-ui;max-width:980px;margin:auto;padding:20px}section{padding:12px;border:1px solid #ddd;border-radius:12px;margin:12px 0}table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid #ddd;padding:5px;text-align:left}</style><h1>Имоуэн — нейросетевой анализ оригиналов</h1><p>Это оценки emotion2vec+, а не доказанные эмоции. Модель не определяет отдельно хрипотцу, дерзость и смех. Проверка актёрской подачи на слух обязательна.</p>']
    for r in results:
        page+=['<section><h2>'+html.escape(r["resource"])+'</h2>']
        if r.get("status")!="model_inference":
            page+=['<p>Ошибка: '+html.escape(r.get("error",""))+'</p></section>'];continue
        scores=r["overall"]
        page+=['<p>Длительность: '+str(r["duration_s"])+' с. Общий характер (по модели): <b>'+html.escape(TRANSLATE.get(next(iter(scores)),next(iter(scores))))+'</b></p>']
        page+=['<table><tr><th>Отрезок</th><th>Первая эмоция</th><th>Оценка</th><th>Вторая эмоция</th></tr>']
        seq=[{"start":0,"end":r["duration_s"],"scores":scores}]+r["windows"]
        for t in seq:
            pairs=list(t["scores"].items())
            first=pairs[0]
            second=pairs[1][0] if len(pairs)>1 else "—"
            page+=['<tr><td>'+str(t["start"])+'–'+str(t["end"])+' с</td><td>'+html.escape(TRANSLATE.get(first[0],first[0]))+'</td><td>'+str(round(first[1],3))+'</td><td>'+html.escape(TRANSLATE.get(second,second))+'</td></tr>']
        page+=['</table><p>Режиссёр: проверь смех, голосовую звонкость, хрипотцу, вопросительные акценты и сопоставление с русским PARTS.</p></section>']
    page+=['</html>']
    (OUT/("LISTEN_EMOTIONS_"+scope+".html")).write_text("".join(page),encoding="utf-8")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--all",action="store_true",help="all 102 source WAV")
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--window",type=float,default=3.5)
    a=p.parse_args()
    if not 2.5<=a.window<=8:raise ValueError("Window range: 2.5–8 sec")
    if a.self_test:
        assert extract_scores([{"labels":["happy","sad"],"scores":[0.7,0.3]}])["happy"]==0.7
        assert len(NAMES)==4
        print("SELFTEST OK (parser only; no model inference)")
        return 0
    if a.all:
        wanted=set()
        for parent in [ROOT/"RVC_DATASETS"/"IMOEN",ROOT/"IMOEN",SRC]:
            if parent.is_dir():
                for entry in parent.rglob("IMOEN*.wav"):
                    if entry.stem.upper().startswith("IMOEN"):wanted.add(entry.stem.upper())
        for arc in [ROOT/"IMOEN.zip",ROOT/"RVC_DATASETS"/"IMOEN.zip"]:
            if arc.exists():
                with zipfile.ZipFile(arc) as z:
                    wanted|={Path(p).stem.upper() for p in z.namelist() if Path(p).name.upper().startswith("IMOEN") and p.lower().endswith(".wav")}
        if not wanted:raise RuntimeError("No source WAV/IMOEN.zip found. Put IMOEN.zip next to VOICE_MANIFEST.csv.")
    else:wanted=set(NAMES)
    files=candidate_files(sorted(wanted))
    missing=sorted(wanted-set(files))
    if missing:raise RuntimeError("Missing original EN WAV: "+", ".join(missing[:20])+". Put IMOEN.zip in root or use RVC_DATASETS/IMOEN.")
    from funasr import AutoModel
    log("LOADING official model "+MODEL_ID+" (first run downloads model weights)")
    model=AutoModel(model=MODEL_ID,device="cpu",disable_update=True)
    results=[];scope="ALL" if a.all else "PILOT4"
    for idx,name in enumerate(sorted(wanted),1):
        log(f"[{idx}/{len(wanted)}] {name}")
        try:r=run_model(model,files[name],name,a.window)
        except Exception as ex:
            r={"resource":name,"status":"error","error":str(ex)}
            log("ERROR "+name+" "+repr(ex))
        results.append(r)
        export(results,scope)
    good=sum(x.get("status")=="model_inference" for x in results)
    log("DONE "+str(good)+"/"+str(len(results))+" reports: "+str(OUT))
    return 0 if good==len(results) else 2

if __name__=="__main__":
    try:sys.exit(main())
    except Exception as exc:
        log("FATAL "+repr(exc));traceback.print_exc();sys.exit(1)
