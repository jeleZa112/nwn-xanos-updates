# -*- coding: utf-8 -*-
"""BG Voice RU 2.9 -- safe 4-line prosody pilot. No installation or overwrite."""
from pathlib import Path
import argparse, csv, html, sys, time, wave
BASE=Path(__file__).resolve().parent
ROOT=BASE.parent
MODEL=ROOT/'.tools/models/qwen3-ru-stress-cf'
MANIFEST=ROOT/'VOICE_MANIFEST.csv'
OUT=BASE/'OUTPUT'
EN=BASE/'ORIGINAL_EN'
LOG=BASE/'PROSODY_29_RUN.log'
SCENES={
 'IMOEN06_':('Ха, в тебе есть что-то странное.','Ха! В тебе есть что-то странное.',['Ха!','В тебе есть что-то странное.'],[130]),
 'IMOEN77A':('Приятно снова встретить тебя, маленький братец. Ха! Мне нравится так тебя называть. Ну, ты готов идти? Мне бы хотелось путешествовать с тобой, если можно.','Приятно снова встретить тебя, маленький братец. Ха! Мне нравится так тебя называть. Ну, ты готов идти? Мне бы хотелось путешествовать с тобой, если можно.',['Приятно снова встретить тебя, маленький братец.','Ха!','Мне нравится так тебя называть.','Ну, ты готов идти?','Мне бы хотелось путешествовать с тобой, если можно.'],[150,100,180,210]),
 'IMOEN79A':('Хорошо, нет проблем, маленький братец. Ты уверен, что хочешь со мной расстаться?','Хорошо, нет проблем, маленький братец. Ты уверен, что хочешь со мной расстаться?',['Хорошо, нет проблем, маленький братец.','Ты уверен, что хочешь со мной расстаться?'],[210]),
 'IMOEN79B':('Хорошо, нет проблем, сестричка. Ты точно хочешь от меня избавиться?','Хорошо, нет проблем, сестричка. Ты точно хочешь от меня избавиться?',['Хорошо, нет проблем, сестричка.','Ты точно хочешь от меня избавиться?'],[210]),
}
def log(s):
 line=time.strftime('%H:%M:%S')+' '+str(s)
 print(line,flush=True)
 with LOG.open('a',encoding='utf-8') as f:f.write(line+'\n')
def duration(p):
 try:
  with wave.open(str(p),'rb') as w:return w.getnframes()/w.getframerate()
 except (OSError,ValueError,wave.Error,ZeroDivisionError):return 0
def find_audio(name):
 for p in (BASE/name,ROOT/'BG_RU_IMOEN_BATCH_26'/name,ROOT/'BG_RU_RASK75_CLONE_24'/name):
  if duration(p)>1:return p
 return None
def check():
 if not MANIFEST.is_file():raise RuntimeError('Missing VOICE_MANIFEST.csv in root '+str(ROOT))
 with MANIFEST.open(encoding='utf-8-sig',newline='') as f:
  r=csv.DictReader(f)
  if not {'Resource','Character','Russian_existing'}<=set(r.fieldnames or []):raise RuntimeError('Manifest columns differ')
  got={}
  for row in r:
   k=(row.get('Resource') or '').strip()
   if k in SCENES:
    if k in got:raise RuntimeError('Duplicate manifest resource '+k)
    if (row.get('Character') or '').upper().strip()!='IMOEN':raise RuntimeError('Wrong character '+k)
    got[k]=(row.get('Russian_existing') or '').split(' | ')[0].strip()
 for k,v in SCENES.items():
  if got.get(k)!=v[0]:raise RuntimeError('Russian text mismatch for '+k)
 for f in ('config.json','model.safetensors','speech_tokenizer/model.safetensors'):
  if not (MODEL/f).is_file():raise RuntimeError('Cached Qwen missing '+f)
 ref=find_audio('RASK75_LONG.wav')
 approved=find_audio('B_LONG_XVECTOR_APPROVED.wav')
 if not ref or not 15<duration(ref)<35:raise RuntimeError('RASK75_LONG.wav missing: keep your BG_RU_IMOEN_BATCH_26 folder')
 if not approved or not 5<duration(approved)<15:raise RuntimeError('Approved B_LONG_XVECTOR_APPROVED.wav missing: keep your BG_RU_IMOEN_BATCH_26 folder')
 OUT.mkdir(exist_ok=True);EN.mkdir(exist_ok=True)
 return ref,approved
def save(path,data,sr):
 import numpy as np, soundfile as sf
 a=np.asarray(data,dtype=np.float32).squeeze()
 if a.ndim!=1 or not np.isfinite(a).all() or not 16000<=int(sr)<=96000:raise RuntimeError('Invalid audio')
 if not .35<len(a)/sr<120 or float(np.max(np.abs(a)))<.01:raise RuntimeError('Silent/invalid output')
 if path.exists():raise FileExistsError('Existing WAV preserved: '+str(path))
 peak=float(np.max(np.abs(a)))
 if peak>.97:a=a*(.96/peak)
 tmp=path.with_name(path.name+'.partial.wav')
 if tmp.exists():raise RuntimeError('Partial output present: '+str(tmp))
 try:
  sf.write(str(tmp),a,int(sr),subtype='PCM_16')
  if duration(tmp)<.35:raise RuntimeError('Written WAV invalid')
  tmp.rename(path)
 except Exception:
  if tmp.exists():tmp.unlink()
  raise
def generate(model,torch,ref,text,seed):
 torch.manual_seed(seed)
 with torch.inference_mode():
  wav,sr=model.generate_voice_clone(text=text,language='Russian',ref_audio=str(ref),ref_text=None,x_vector_only_mode=True,max_new_tokens=2600)
 if len(wav)!=1:raise RuntimeError('Unexpected Qwen output')
 return wav[0],int(sr)
def generate_parts(model,torch,ref,parts,pauses,seed):
 import numpy as np
 joined=[];rate=None
 for i,t in enumerate(parts):
  a,sr=generate(model,torch,ref,t,seed+i)
  if rate is not None and sr!=rate:raise RuntimeError('Sample rate mismatch')
  rate=sr;a=np.asarray(a,dtype=np.float32).squeeze()
  if a.ndim!=1:raise RuntimeError('Invalid part waveform')
  # Gain cannot create an expressive shout; audition it against original EN.
  if t=='Ха!' and len(a)/sr<3.5:a=a*1.13
  joined.append(a)
  if i<len(pauses):joined.append(np.zeros(int(sr*pauses[i]/1000),dtype=np.float32))
 return np.concatenate(joined),rate
def draw(approved):
 s=['<!doctype html><html lang="ru"><meta charset="utf-8"><title>BG Voice RU 2.9</title><style>body{font:16px system-ui;max-width:880px;margin:auto;padding:22px}section{border:1px solid #ddd;padding:16px;margin:12px 0;border-radius:10px}audio{display:block;width:100%;margin:10px 0}</style><h1>Имоуэн — пилот 2.9</h1><p>Эмоции здесь задаются смысловыми фрагментами, а не автоматически копируются из английского.</p>']
 for k,v in SCENES.items():
  s+=['<section><h2>'+k+'</h2><p>'+html.escape(v[0])+'</p>']
  original=EN/(k+'.wav')
  if duration(original)>.5:s+=['<b>Английский оригинал</b><audio controls src="ORIGINAL_EN/'+k+'.wav"></audio>']
  else:s+=['<p>Для сравнения добавь ORIGINAL_EN/'+k+'.wav</p>']
  for suffix in ('WHOLE','PARTS'):
   f=OUT/(k+'_'+suffix+'_29.wav')
   if duration(f)>.3:s+=['<p>'+suffix+'</p><audio controls src="OUTPUT/'+f.name+'"></audio>']
  s+=['</section>']
 s+=['<p>Approved voice: '+html.escape(str(approved))+'. Оцени Ха!, вопросы, нежность, изменения тембра и русское С.</p></html>']
 (BASE/'LISTEN_PROSODY_29.html').write_text(''.join(s),encoding='utf-8')
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args()
 ref,approved=check();draw(approved)
 log('CHECK OK: manifest, local Qwen, Rask75, approved B. No downloads.')
 if args.check:return 0
 import torch
 if not torch.cuda.is_available():raise RuntimeError('CUDA not available')
 from qwen_tts import Qwen3TTSModel
 log('Loading existing Qwen. Long xvector, no Applio/SeedVC.')
 model=Qwen3TTSModel.from_pretrained(str(MODEL),device_map='cuda:0',dtype=torch.bfloat16,attn_implementation='sdpa')
 failed=[]
 for i,(k,(expected,whole,parts,pauses)) in enumerate(SCENES.items()):
  for variant in ('WHOLE','PARTS'):
   target=OUT/(k+'_'+variant+'_29.wav')
   if target.exists():log('KEEP '+target.name);continue
   try:
    log('GENERATE '+target.name)
    if variant=='WHOLE':a,sr=generate(model,torch,ref,whole,29000+i*100)
    else:a,sr=generate_parts(model,torch,ref,parts,pauses,29010+i*100)
    save(target,a,sr);log('DONE '+target.name+' '+str(round(duration(target),2))+'s')
   except Exception as e:failed.append(target.name);log('FAIL '+target.name+' '+repr(e))
   draw(approved)
 log('FINISH: '+('failed '+','.join(failed) if failed else 'all 8 done'))
 return 2 if failed else 0
if __name__=='__main__':
 try:sys.exit(main())
 except Exception as e:log('STOP '+repr(e));sys.exit(1)
