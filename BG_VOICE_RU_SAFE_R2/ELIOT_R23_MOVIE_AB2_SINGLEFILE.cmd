@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
set "HF_HUB_OFFLINE=1"
set "TRANSFORMERS_OFFLINE=1"
set "HF_DATASETS_OFFLINE=1"
set "HF_HUB_DISABLE_TELEMETRY=1"
set "BGV_COMMAND=import sys; p=sys.argv.pop(1); t=open(p,encoding='utf-8-sig').read(); exec(compile(t.split(chr(10)+'#BGVOICE_PYTHON_START'+chr(10),1)[1],p,'exec'),{'__name__':'__main__','__file__':p})"
py -3.11 -c "import sys;assert sys.version_info >= (3,9)" >nul 2>nul
if not errorlevel 1 goto :py_launcher
python -c "import sys;assert sys.version_info >= (3,9)" >nul 2>nul
if not errorlevel 1 goto :python_launcher
echo ERROR: Python 3.9+ not found. Existing WAV files unchanged.
set "RC=1"
goto :done
:py_launcher
py -3.11 -c "%BGV_COMMAND%" "%~f0" %*
set "RC=%ERRORLEVEL%"
goto :done
:python_launcher
python -c "%BGV_COMMAND%" "%~f0" %*
set "RC=%ERRORLEVEL%"
:done
echo BG Voice RU offline updater exit code: %RC%
if /I "%~1"=="--eliot-r4-preflight" exit /b %RC%
if /I "%~1"=="--eliot-movie-ab2" exit /b %RC%
if /I "%~1"=="--eliot-movie-ab2-preflight" exit /b %RC%
if /I "%~1"=="--eliot-movie-ab2-selftest" exit /b %RC%
pause
exit /b %RC%
#BGVOICE_PYTHON_START
# -*- coding: utf-8 -*-
"""BG Voice RU: offline audio selection research engine, no network and no WAV changes.
Embedded in the existing BG_VOICE_UPDATE.cmd as a single executable source.
"""
from __future__ import annotations
import csv
import datetime as dt
import difflib
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import sys
import traceback
import unicodedata
import wave
import zipfile
from collections import Counter, defaultdict

VERSION = '4.7.1-offline'
REPORT = 'SEND_TO_CHATGPT_BG_VOICE_RU.zip'
DB_FILE = 'BG_VOICE_RU_PROGRESS.sqlite3'
PROTECTED = {'IMOEN75'}
ACTION_WORDS = {'chuckle','laugh','sigh','sob','gasp','cough','cry','смешок','смех','смеётся','смеется','вздох','кашель','плач','всхлип','стон','хохот','хихикает','вздыхает','кашляет','плачет','рыдает','чихает','апчхи'}
MODES = ('stable','per_line')
MODE_RE = re.compile(r'^([a-z0-9]{3,24})__(stable|per_line)_RU(?:\(\d+\))?\.wav$', re.I)
STAR = re.compile(r'\*([^*\r\n]{1,100})\*')
SID_RE = re.compile(r'^[A-Z0-9]{3,24}$')
AVOID_DIRS = {'.git','.venv','venv','.venv_voxcpm2','__pycache__','node_modules','site-packages','BG_VOICE_RU_ONECLICK_OUT','REPORTS'}
DECISIONS = {
    'AERIE63':'stable','AERIE74':'per_line','EDWIN28':'HOLD','EDWIN60':'per_line',
    'EDWIN81':'stable','GORCHR08':'per_line','GORCHR11':'per_line','JAHEIR06':'per_line',
    'JAHEIR48':'HOLD','KORGAN49':'stable','KORGAN54':'per_line','KORGAN57':'per_line',
    'KORGAN60':'per_line','MINSC66':'stable','NALIA15':'per_line','NALIA97':'stable',
    'OH81854':'per_line','OH87501':'per_line','SAREVO40':'per_line',
    'SAREVO74':'stable','SAREVO84':'stable','VICONI88':'per_line','VICONI90':'stable',
    'VICONIA5':'HOLD'
}
USER_NOTES = {
    'EDWIN28':'Check unusually short English original; prior HOLD.',
    'GORCHR11':'Per_line voice approved, spoken *chuckle* needs real laughter. Keep voice.',
    'JAHEIR48':'Both overly rushed; punctuation and ending need revision.',
    'SAREVO40':'Per_line voice approved, spoken stage cue needs actual laughter.',
    'SAREVO74':'Both have incorrect stress in «жилах»; keep preferred Stable voice.',
    'VICONIA5':'Both too aggressive; English is calm, insinuating; rework delivery.',
}
USER_NOTE_GUARDS = {'GORCHR11','SAREVO40','SAREVO74'}

# No network in this process; even an accidentally used Hugging Face name cannot download.
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
os.environ['WANDB_DISABLED'] = 'true'


def now(): return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
def safe_read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def all_rows(obj):
    if isinstance(obj, dict):
        if obj.get('sound_id') or obj.get('soundId'):
            yield obj
        else:
            for value in obj.values():
                if isinstance(value, (dict, list)):
                    yield from all_rows(value)
    elif isinstance(obj,list):
        for value in obj:
            if isinstance(value,(list,dict)):
                yield from all_rows(value)

def bounded_walk(path, max_depth=8):
    if not path.is_dir():return
    for base, dirs, files in os.walk(path):
        depth=len(Path(base).relative_to(path).parts)
        dirs[:] = sorted(x for x in dirs if x.lower() not in {d.lower() for d in AVOID_DIRS} and not x.startswith('.')) if depth<max_depth else []
        for f in sorted(files):
            yield Path(base)/f

def wav_info(p):
    if not p or not p.is_file():return {'error':'MISSING'}
    try:
        with wave.open(str(p),'rb') as w:
            if w.getnframes()<=0 or w.getframerate()<=0:
                raise ValueError('empty WAV')
            return {'seconds':round(w.getnframes()/w.getframerate(),3),'sample_rate':w.getframerate(),
                    'channels':w.getnchannels(),'sample_width':w.getsampwidth()}
    except Exception as exc:
        return {'error':type(exc).__name__+': '+str(exc)[:200]}

def normalize_words(t):
    t=unicodedata.normalize('NFC',str(t or '')).casefold().replace('ё','е')
    return re.findall(r'[а-яa-z0-9]+',t)

def spoken_and_actions(text):
    actions=[]; emphasis=[]
    def take(m):
        val=m.group(1).strip()
        v=re.sub(r'[!?,.]+$','',val.lower()).strip()
        if v in ACTION_WORDS or any(v.startswith(a+' ') for a in ACTION_WORDS):
            actions.append(val)
            return ' '
        emphasis.append(val)
        return val
    spoken=re.sub(r'\s+',' ',STAR.sub(take,str(text or ''))).strip()
    return spoken,actions,emphasis

def word_match(expected, heard):
    a,b=normalize_words(expected),normalize_words(heard)
    if not a or not b:return None
    return round(difflib.SequenceMatcher(a=a,b=b,autojunk=False).ratio(),4)

def char_from_row(row):
    return str(row.get('voice') or row.get('character') or row.get('speaker') or '').strip()


def wav_scan(preferred, root, errors):
    # Use only the original two-variants collection, never repaired or mixed copies.
    wavs=defaultdict(dict)
    for base in (preferred,root/'RUSSIAN_WAV_TWO_VERSIONS'):
        if not base.is_dir():continue
        for p in bounded_walk(base,max_depth=5):
            if p.suffix.lower()!='.wav':continue
            m=MODE_RE.fullmatch(p.name)
            if not m:continue
            sid,mode=m.group(1).upper(),m.group(2).lower()
            prior=wavs[sid].get(mode)
            if not prior or (len(p.name),str(p))<(len(prior.name),str(prior)):
                wavs[sid][mode]=p
        if len(wavs)>=1000:break
    # If paths are inaccessible, read prior report for fully-qualified paths.
    if len(wavs)<1000:
        errors.append({'sound_id':'','stage':'wav_scan','error':'Original RUSSIAN_WAV_TWO_VERSIONS directory not found or incomplete','path':str(preferred)})
    return wavs

def plan_scan(root, errors):
    p=root/'PLAN_VERIFIED.json'
    if not p.is_file():
        found=[]
        for f in bounded_walk(root,max_depth=5):
            if f.name.upper()=='PLAN_VERIFIED.JSON':found.append(f)
        if found:p=sorted(found,key=lambda x:(len(x.parts),str(x)))[0]
    if not p.is_file():
        errors.append({'sound_id':'','stage':'plan','error':'PLAN_VERIFIED.json not found','path':str(root)})
        return {},None
    try:
        rows={}
        for row in all_rows(safe_read_json(p)):
            sid=str(row.get('sound_id') or row.get('soundId') or '').strip().upper()
            if SID_RE.fullmatch(sid):rows[sid]=row
        return rows,p
    except Exception as exc:
        errors.append({'sound_id':'','stage':'plan','error':repr(exc),'path':str(p)})
        return {},p


def metadata_search(master,work,errors):
    home=Path.home()
    downloads=home/'Downloads'
    roots=[master,work]
    if downloads.is_dir():
        # Only relevant top-level files in Downloads; do not crawl unrelated folders.
        for f in downloads.iterdir():
            if f.is_file() and f.suffix.lower() in ('.csv','.json','.zip') and any(t in f.name.lower() for t in ('asr','decision','choice','review','triage','fast_voice','blind_ab')):
                try:
                    if f.stat().st_size<45_000_000:yield f
                except OSError:pass
        for p in downloads.iterdir():
            if p.is_dir() and (p.name.upper().startswith(('BG_VOICE','BLIND_AB','SEND_TO_CHATGPT'))):
                roots.append(p)
    dedup=set()
    for root in roots:
        for p in bounded_walk(root,max_depth=(6 if root==master else 5)):
            if p in dedup:continue
            dedup.add(p)
            n=p.name.lower()
            if p.suffix.lower() in ('.csv','.json','.zip') and any(t in n for t in ('asr','decision','choice','review','triage','fast_voice','blind_ab')):
                try:
                    if p.stat().st_size<45_000_000:yield p
                except OSError:pass

def csv_or_json_rows(p):
    if p.suffix.lower()=='.csv':
        with p.open('r',encoding='utf-8-sig',newline='') as f:yield from csv.DictReader(f)
    elif p.suffix.lower()=='.json':
        yield from all_rows(safe_read_json(p))
    elif p.suffix.lower()=='.zip':
        with zipfile.ZipFile(p) as z:
            for name in z.namelist():
                low=name.lower()
                if not low.endswith(('.csv','.json')) or not any(k in low for k in ('asr','decision','choice','review','triage')):continue
                f=z.getinfo(name)
                if f.file_size>24_000_000:continue
                data=z.read(name)
                if low.endswith('.csv'):
                    yield from csv.DictReader(io.StringIO(data.decode('utf-8-sig',errors='replace')))
                elif low.endswith('.json'):
                    yield from all_rows(json.loads(data.decode('utf-8-sig',errors='replace')))

def parse_mode(value):
    x=str(value or '').strip().lower().replace('-','_')
    if x in ('stable','per_line'):return x
    if x in ('hold','redo','tie_hold','voice_hold'):return 'HOLD'
    return None

def parse_meta(master,work,errors):
    # Baseline is a direct copy of 24 historical user decisions, not AI guesses.
    manual={sid:{'decision':choice,'source':'USER_VERIFIED_2026_11_15','note':USER_NOTES.get(sid,'')} for sid,choice in DECISIONS.items()}
    asr={}
    conflicts=[];scanned=0
    for p in metadata_search(master,work,errors):
        scanned+=1
        try:
            for row in csv_or_json_rows(p):
                sid=str(row.get('sound_id') or row.get('soundId') or row.get('id') or '').strip().upper()
                if not SID_RE.fullmatch(sid):continue
                choice=parse_mode(row.get('selection') or row.get('voice_choice') or row.get('choice') or row.get('selected_mode') or row.get('chosen_mode') or row.get('selected_variant') or row.get('winner_mode') or row.get('voice_selection'))
                # Never convert blinded A/B without an exact mode mapping.
                if choice:
                    # Prefer explicit, newer local decisions. Previously approved baseline remains a safeguard.
                    prev=manual.get(sid)
                    if prev and prev['decision']!=choice and prev['source']=='USER_VERIFIED_2026_11_15':
                        # A later explicit file choice is not reliably dated as newer; do not override silently.
                        conflicts.append({'sound_id':sid,'old':prev['decision'],'new':choice,'source':str(p)})
                    elif not prev:
                        manual[sid]={'decision':choice,'source':str(p),'note':str(row.get('user_note') or '')[:200]}
                mode=parse_mode(row.get('mode') or row.get('variant') or row.get('generation_mode') or row.get('variant_type'))
                transcript=str(row.get('asr_text') or row.get('recognized_text') or row.get('transcript') or row.get('hypothesis') or '').strip()
                if mode in MODES and transcript and (sid,mode) not in asr:
                    asr[sid,mode]={'transcript':transcript,'source':str(p)}
                # Existing 618-pair audits often store both transcripts in one CSV row.
                for target_mode in MODES:
                    aliases=(f'asr_{target_mode}',f'{target_mode}_asr',f'{target_mode}_transcript',
                             f'asr_text_{target_mode}',f'recognized_{target_mode}',
                             f'{target_mode}_recognized_text',f'transcript_{target_mode}')
                    text_value=next((str(row[k]).strip() for k in aliases if row.get(k)), '')
                    if text_value and (sid,target_mode) not in asr:
                        asr[sid,target_mode]={'transcript':text_value,'source':str(p)}
        except Exception as exc:
            errors.append({'sound_id':'','stage':'metadata','error':type(exc).__name__+': '+str(exc)[:200],'path':str(p)})
    return manual,asr,conflicts,scanned


def find_english(master,plan,errors):
    # Walk master, excluding RU variants; exact sound_id match only, not a guessed similar voice.
    en={}
    accepted=set(plan)
    for entry in plan.values():
        for k in ('stable_source_sound_id','english_sound_id'):
            v=str(entry.get(k) or '').upper()
            if SID_RE.fullmatch(v):accepted.add(v)
    for p in bounded_walk(master,max_depth=9):
        if p.suffix.lower()!='.wav':continue
        if MODE_RE.fullmatch(p.name):continue
        if any('RUSSIAN_WAV_TWO_VERSIONS'==q.upper() for q in p.parts):continue
        if any(q.upper() in ('RU','RUSSIAN','RUSSIAN_WAV','REDO','REPAIR') for q in p.parts):continue
        # Exact name is necessary but not sufficient: exclude unidentified Russian final WAVs.
        proof=any(('english' in part.lower() or part.lower() in ('en','en_wavs','original_en','originals_en','en_originals'))
                  for part in p.parts)
        if p.stem.upper() in accepted and p.stem.upper() not in en and proof:
            en[p.stem.upper()]=p
    return en

def get_ref(sid,entry,en,master):
    keys=('english_wav','en_wav','english_wav_path','original_wav','stable_reference_wav',
          'reference_wav_path','stable_reference_path','reference_wav','source_wav')
    for key in keys:
        v=entry.get(key)
        if not isinstance(v,str) or not v.lower().endswith('.wav'):continue
        p=Path(v)
        if not p.is_absolute():p=master/p
        # Explicit reference must not accidentally resolve to a generated Russian variant.
        if p.is_file() and not MODE_RE.fullmatch(p.name):return p
    ref=str(entry.get('stable_source_sound_id') or entry.get('english_sound_id') or sid).upper()
    return en.get(ref) or en.get(sid)


class State:
    def __init__(self,p):
        self.conn=sqlite3.connect(str(p),timeout=30)
        self.conn.execute('pragma journal_mode=DELETE')
        self.conn.execute('pragma synchronous=NORMAL')
        self.conn.execute('create table if not exists embeds (key text primary key, model text not null, dim integer not null, vector blob not null, at text not null)')
        self.conn.execute('create table if not exists transcripts (key text primary key, model text not null, transcript text not null, at text not null)')
        self.conn.commit()
    def get_embed(self,key,model,dim=None):
        r=self.conn.execute('select dim,vector from embeds where key=? and model=?',(key,model)).fetchone()
        if r is None:return None
        import numpy as np
        a=np.frombuffer(r[1],dtype=np.float32)
        if len(a)!=r[0] or (dim and len(a)!=dim):return None
        return a
    def put_embed(self,key,model,arr):
        import numpy as np
        a=np.asarray(arr,dtype=np.float32).ravel()
        self.conn.execute('insert or replace into embeds values(?,?,?,?,?)',(key,model,len(a),a.tobytes(),now()))
    def get_asr(self,key,model):
        r=self.conn.execute('select transcript from transcripts where key=? and model=?',(key,model)).fetchone()
        return r[0] if r else None
    def put_asr(self,key,model,value):
        self.conn.execute('insert or replace into transcripts values(?,?,?,?)',(key,model,value,now()))
    def commit(self):self.conn.commit()
    def close(self):self.conn.commit();self.conn.close()


def path_sig(p):
    s=p.stat()
    return hashlib.sha256((str(p.resolve()).casefold()+'|'+str(s.st_size)+'|'+str(s.st_mtime_ns)).encode('utf-8')).hexdigest()


def load_audio(path):
    import numpy as np
    try:
        with wave.open(str(path),'rb') as f:
            sr=f.getframerate();nch=f.getnchannels();width=f.getsampwidth();raw=f.readframes(f.getnframes())
        if width==2:
            x=np.frombuffer(raw,dtype='<i2').astype(np.float32)/32768.0
        elif width==4:
            x=np.frombuffer(raw,dtype='<i4').astype(np.float32)/2147483648.0
        elif width==1:
            x=(np.frombuffer(raw,dtype='u1').astype(np.float32)-128.)/128.
        else:raise ValueError('Unsupported PCM sample width '+str(width))
        if nch>1:x=x.reshape(-1,nch).mean(axis=1)
    except (wave.Error,ValueError):
        import soundfile as sf
        x,sr=sf.read(str(path),dtype='float32',always_2d=True);x=x.mean(axis=1)
    if not len(x) or sr<=0:raise ValueError('empty audio')
    if sr!=16000:
        try:
            from scipy.signal import resample_poly
            import math
            d=math.gcd(sr,16000);x=resample_poly(x,16000//d,sr//d).astype('float32')
        except ImportError:
            # Last resort: linear resampling is acceptable for a diagnostic embedding,
            # but we mark this backend as approximate; no final acceptance.
            pos=np.linspace(0,len(x)-1,round(len(x)*16000/sr))
            x=np.interp(pos,np.arange(len(x)),x).astype('float32')
    if x.size<16000*.4:raise ValueError('too short for speaker comparison')
    if x.size>16000*24:
        x=np.concatenate((x[:16000*12],x[-16000*12:]))
    if not np.isfinite(x).all():raise ValueError('nonfinite audio')
    return x.astype('float32')


class Speaker:
    def __init__(self,master):
        self.name='UNAVAILABLE';self.error='No locally installed speaker model';self.impl=None;self.device='cpu'
        try:
            import torch
            self.device='cuda' if torch.cuda.is_available() else 'cpu'
        except Exception as exc:
            self.error='torch not available: '+type(exc).__name__
            return
        try:
            import resemblyzer
            from resemblyzer import VoiceEncoder, preprocess_wav
            weights=Path(resemblyzer.__file__).parent/'pretrained.pt'
            if weights.is_file():
                self.model=VoiceEncoder(device=self.device,verbose=False)
                self.preprocess=preprocess_wav
                self.name='resemblyzer-packaged-pretrained'
                self.impl='resemblyzer'
                self.error=''
                return
        except Exception as exc:
            self.error='resemblyzer: '+type(exc).__name__+': '+str(exc)[:130]
        try:
            from speechbrain.inference.classifiers import EncoderClassifier
            hf=Path.home()/'.cache'/'huggingface'/'hub'/'models--speechbrain--spkrec-ecapa-voxceleb'/'snapshots'
            candidates=[]
            for root in (hf,master/'MODELS'/'ECAPA',master/'MODELS'/'speechbrain-ecapa'):
                if not root.is_dir():continue
                if (root/'hyperparams.yaml').is_file():candidates.append(root)
                else:candidates.extend(p for p in root.iterdir() if p.is_dir() and (p/'hyperparams.yaml').exists())
            for folder in candidates:
                try:
                    self.model=EncoderClassifier.from_hparams(source=str(folder),savedir=str(folder),run_opts={'device':self.device})
                    self.name='speechbrain-ecapa-local'
                    self.impl='speechbrain'
                    self.error=''
                    return
                except Exception as exc:self.error='Local ECAPA load: '+type(exc).__name__+': '+str(exc)[:130]
        except Exception as exc:
            self.error+='; SpeechBrain: '+type(exc).__name__
    def embed(self,p):
        import numpy as np
        x=load_audio(p)
        if self.impl=='resemblyzer':
            x=self.preprocess(x,source_sr=16000)
            v=self.model.embed_utterance(x)
        elif self.impl=='speechbrain':
            import torch
            with torch.no_grad():
                ten=torch.from_numpy(x).float().unsqueeze(0).to(self.device)
                v=self.model.encode_batch(ten).detach().cpu().numpy().ravel()
        else:raise RuntimeError('Speaker model unavailable')
        v=np.asarray(v,dtype='float32').ravel()
        if not np.isfinite(v).all() or np.linalg.norm(v)<1e-6:raise RuntimeError('invalid speaker embedding')
        return v/np.linalg.norm(v)


class ASR:
    def __init__(self,master):
        self.impl=None;self.name='UNAVAILABLE';self.error='No local ASR weights';self.model=None
        self.device='cpu'
        try:
            import torch
            self.device='cuda' if torch.cuda.is_available() else 'cpu'
        except ImportError:pass
        # First, use an explicitly local faster-whisper model directory if present.
        try:
            from faster_whisper import WhisperModel
            roots=[]
            if os.getenv('BG_VOICE_LOCAL_WHISPER'):roots.append(Path(os.environ['BG_VOICE_LOCAL_WHISPER']))
            cache=Path.home()/'.cache'/'huggingface'/'hub'
            if cache.is_dir():
                for p in cache.glob('models--*--faster-whisper*'):
                    snap=p/'snapshots'
                    if snap.is_dir():roots.extend(q for q in snap.iterdir() if q.is_dir())
            for d in roots:
                if not (d/'model.bin').is_file():continue
                try:
                    self.model=WhisperModel(str(d),device=self.device,compute_type=('int8_float16' if self.device=='cuda' else 'int8'),local_files_only=True)
                    self.impl='faster-whisper';self.name='faster-whisper-local';self.error='';return
                except Exception as exc:self.error='faster-whisper: '+str(exc)[:180]
        except ImportError:pass
        try:
            import whisper
            cache=Path.home()/'.cache'/'whisper'
            candidates=[*cache.glob('*.pt')] if cache.is_dir() else []
            if os.getenv('BG_VOICE_LOCAL_WHISPER') and Path(os.environ['BG_VOICE_LOCAL_WHISPER']).suffix.lower()=='.pt':
                candidates.insert(0,Path(os.environ['BG_VOICE_LOCAL_WHISPER']))
            if candidates:
                # Use already available checkpoint by path: whisper.load_model(name) would download.
                p=sorted(candidates,key=lambda x:x.stat().st_size)[0]
                self.model=whisper.load_model(str(p),device=self.device)
                self.impl='openai-whisper';self.name='whisper-local:'+p.name;self.error='';return
        except Exception as exc:self.error='openai-whisper: '+str(exc)[:180]
    def transcribe(self,p):
        if self.impl=='faster-whisper':
            seg,_=self.model.transcribe(load_audio(p),language='ru',beam_size=2,vad_filter=True,condition_on_previous_text=False)
            return ' '.join(s.text.strip() for s in seg).strip()
        if self.impl=='openai-whisper':
            return str(self.model.transcribe(load_audio(p),language='ru',fp16=(self.device=='cuda'),verbose=False,condition_on_previous_text=False)['text']).strip()
        raise RuntimeError('No offline ASR model')


def cosine(a,b):
    import numpy as np
    return round(float(np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b))),5)

def csv_bytes(rows,fields):
    t=io.StringIO(newline='')
    w=csv.DictWriter(t,fieldnames=fields,extrasaction='ignore')
    w.writeheader();w.writerows(rows)
    return ('\ufeff'+t.getvalue()).encode('utf-8')


def check_self_test():
    assert parse_mode('Per-Line')=='per_line'
    assert parse_mode('A') is None
    assert spoken_and_actions('Мы *смеётся* и *мы* победим')[0]=='Мы и мы победим'
    assert spoken_and_actions('Мы *смеётся* и *мы* победим')[1]==['смеётся']
    assert word_match('Привет, мир!','привет мир')==1.0
    assert MODE_RE.fullmatch('GORCHR11__per_line_RU.wav')
    assert MODE_RE.fullmatch('BMRCH102__per_line_RU(1).wav')
    assert not MODE_RE.fullmatch('GORCHR11__per_line_RU_REPAIR.wav')
    assert not MODE_RE.fullmatch('GORCHR11_REPAIR.wav')
    assert DECISIONS['GORCHR11']=='per_line' and DECISIONS['VICONIA5']=='HOLD'
    print('SELF_TEST_OK');return 0


def run(work,root, limit=0):
    errors=[]
    primary=root/'RUSSIAN_WAV_TWO_VERSIONS'
    wavs=wav_scan(primary,root,errors)
    plan,plan_path=plan_scan(root,errors)
    # Search all existing master project areas for exact EN reference WAVs.
    master=root.parent if root.name.upper()=='08_VOXCPM2_ALL_CHARACTERS' else root
    en=find_english(master,plan,errors)
    manual, prior_asr, conflicts, scanned=parse_meta(master,work,errors)
    state=State(work/DB_FILE)
    print('BG Voice RU OFFLINE 4.7.1 | pairs:',len(wavs),'| previous manual:',len(manual),
          '| prior ASR:',len(prior_asr),'| EN WAV:',len(en),flush=True)
    speaker=Speaker(master)
    print('SPEAKER MODEL:',speaker.name,'|',speaker.error,flush=True)
    # Keep ASR separate; two simultaneous GPU models exceed laptop VRAM often.
    selected=[];counter=Counter();review=[];scores=[];asrqueue=[]
    total=len(set(plan)|set(wavs))
    all_ids=sorted(set(plan)|set(wavs))
    if limit>0:all_ids=all_ids[:limit]
    for idx,sid in enumerate(all_ids,1):
        try:
            row=plan.get(sid,{})
            voice=char_from_row(row)
            text,actions,emphasis=spoken_and_actions(row.get('russian_text'))
            enpath=get_ref(sid,row,en,master)
            ens=wav_info(enpath)
            paths=wavs.get(sid,{})
            a,b=(paths.get('stable'),paths.get('per_line'))
            wa,wb=wav_info(a),wav_info(b)
            flags=[]
            for mode,p,info in (('stable',a,wa),('per_line',b,wb)):
                if info.get('error'):flags.append(mode.upper()+'_INVALID')
            if actions:flags.append('ACTION_CHECK')
            if sid in USER_NOTE_GUARDS:flags.append('USER_CONFIRMED_REPAIR')
            sa,sb=wa.get('seconds'),wb.get('seconds')
            if sa and sb and max(sa,sb)>min(sa,sb)*1.75 and abs(sa-sb)>3:flags.append('LENGTH_DISAGREEMENT')
            if ens.get('seconds') and sa and sb:
                for mode,d in (('stable',sa),('per_line',sb)):
                    if d>ens['seconds']*1.75 and d-ens['seconds']>3:flags.append(mode.upper()+'_LONG_EN')
            old=manual.get(sid)
            manual_choice=old['decision'] if old else ''
            sim_a=sim_b=margin=None
            if speaker.impl and enpath and enpath.is_file() and a and b and not wa.get('error') and not wb.get('error'):
                vec=[]
                for p in (enpath,a,b):
                    key=path_sig(p)
                    cached=state.get_embed(key,speaker.name)
                    if cached is None:
                        cached=speaker.embed(p)
                        state.put_embed(key,speaker.name,cached)
                    vec.append(cached)
                sim_a=cosine(vec[0],vec[1]);sim_b=cosine(vec[0],vec[2]);margin=round(abs(sim_a-sim_b),5)
            candidate=''
            if sim_a is not None and sim_b is not None and margin is not None and margin>=.12:
                candidate='stable' if sim_a>sim_b else 'per_line'
                # Audio similarity is not a final guarantee of identity or acting.
            if manual_choice:
                selection=manual_choice
                status='USER_CHOICE_PENDING_FULL_QA' if manual_choice in MODES else 'USER_HOLD'
                counter['manual_preserved']+=1
            elif candidate and not flags:
                selection=candidate
                status='AI_VOICE_CANDIDATE_NOT_FINAL'
                counter['ai_candidates']+=1
            else:
                selection='HOLD'
                if not enpath:status='MISSING_EN_REFERENCE'
                elif not speaker.impl:status='MISSING_OFFLINE_SPEAKER_MODEL'
                elif flags:status='NEEDS_REVIEW'
                elif candidate:status='NEEDS_QA'
                else:status='AI_UNCERTAIN'
                counter['hold']+=1
            if sid in PROTECTED:status='PROTECTED_REFERENCE';selection=manual_choice or 'HOLD'
            if not enpath:counter['missing_en']+=1
            if flags:counter['flagged']+=1
            if sim_a is not None:counter['voice_scored']+=1
            # Cache ASR from historical reports and leave utterance re-transcription to a separate pass.
            heard={}
            for mode,p in (('stable',a),('per_line',b)):
                prev=prior_asr.get((sid,mode))
                if prev:heard[mode]=prev['transcript']
                elif p and not wav_info(p).get('error'):asrqueue.append({'sound_id':sid,'mode':mode,'reason':'NOT_CACHED','path':str(p)})
            quality_a=word_match(text,heard.get('stable'))
            quality_b=word_match(text,heard.get('per_line'))
            if text and (quality_a is not None and quality_a<.72 or quality_b is not None and quality_b<.72):
                flags.append('ASR_LEXICAL_REVIEW')
                if status=='AI_VOICE_CANDIDATE_NOT_FINAL':
                    selection='HOLD';status='ASR_LEXICAL_CONFLICT'
            item={'sound_id':sid,'character':voice,'manual_selection':manual_choice,'selected':selection,
                  'status':status,'EN_WAV':str(enpath or ''),'stable_WAV':str(a or ''),'per_line_WAV':str(b or ''),
                  'EN_seconds':ens.get('seconds',''),'stable_seconds':sa or '','per_line_seconds':sb or '',
                  'speaker_model':speaker.name if speaker.impl else '',
                  'voice_sim_stable':sim_a if sim_a is not None else '',
                  'voice_sim_per_line':sim_b if sim_b is not None else '',
                  'voice_score_margin':margin if margin is not None else '',
                  'asr_word_stable':quality_a if quality_a is not None else '',
                  'asr_word_per_line':quality_b if quality_b is not None else '',
                  'flags':';'.join(flags),'notes':(old or {}).get('note','')}
            selected.append(item)
            if status in ('USER_HOLD','MISSING_EN_REFERENCE','MISSING_OFFLINE_SPEAKER_MODEL','NEEDS_REVIEW','NEEDS_QA','AI_UNCERTAIN') or flags:
                review.append(item)
            if sim_a is not None:scores.append({'sound_id':sid,'stable':sim_a,'per_line':sim_b,'margin':margin,'candidate':candidate,'manual_selection':manual_choice})
            counter['rows']+=1
        except KeyboardInterrupt:
            state.commit();raise
        except Exception as exc:
            errors.append({'sound_id':sid,'stage':'voice','error':type(exc).__name__+': '+str(exc)[:250],'path':''})
            counter['errors']+=1
        if idx%25==0:
            state.commit()
            print('PROGRESS',idx,'/',len(all_ids),'VOICE_SCORED',counter['voice_scored'],flush=True)
    state.commit()
    # Only run ASR with local weights when they are already available.
    asr=ASR(master)
    counter['asr_cached']=len(prior_asr)
    if asr.impl:
        for i,row in enumerate(asrqueue,1):
            try:
                p=Path(row['path'])
                key=path_sig(p)
                recognized=state.get_asr(key,asr.name)
                if recognized is None:
                    recognized=asr.transcribe(p)
                    state.put_asr(key,asr.name,recognized)
                    counter['asr_new']+=1
                if recognized and recognized.strip():counter['asr_scored']+=1
            except KeyboardInterrupt:state.commit();raise
            except Exception as exc:
                errors.append({'sound_id':row['sound_id'],'stage':'asr','error':type(exc).__name__+': '+str(exc)[:220],'path':row['path']})
            if i%25==0:
                state.commit()
                print('ASR PROGRESS',i,'/',len(asrqueue),flush=True)
        state.commit()
        # Include newly calculated ASR lexical diagnostics in this same report.
        by_id={item['sound_id']:item for item in selected}
        for todo in asrqueue:
            item=by_id.get(todo['sound_id'])
            if not item:continue
            try:
                transcript=state.get_asr(path_sig(Path(todo['path'])),asr.name)
                if transcript:
                    t=plan.get(todo['sound_id'],{}).get('russian_text','')
                    expected,_,_=spoken_and_actions(t)
                    val=word_match(expected,transcript)
                    item['asr_word_'+todo['mode']]=val if val is not None else ''
                    if val is not None and val<.72:
                        item['flags']=(item['flags']+';ASR_LEXICAL_REVIEW').strip(';')
                        if item['status']=='AI_VOICE_CANDIDATE_NOT_FINAL':
                            item['selected']='HOLD';item['status']='ASR_LEXICAL_CONFLICT'
                        if item not in review:review.append(item)
            except Exception as exc:
                errors.append({'sound_id':todo['sound_id'],'stage':'asr_score','error':repr(exc),'path':todo['path']})
    summary={'version':VERSION,'timestamp_utc':now(),'offline':True,'network_calls':0,
             'original_wavs_changed':False,'game_modified':False,'root':str(root),
             'original_pairs':len(wavs),'plan_rows':len(plan),'rows_processed':counter['rows'],
             'speaker_model':speaker.name,'speaker_error':speaker.error,
             'asr_model':asr.name,'asr_error':asr.error,'english_wavs_found':len(en),
             'prior_manual_decisions':len(manual),'prior_asr_transcripts':len(prior_asr),
             'decision_conflicts':len(conflicts),'metadata_files_scanned':scanned,
             'counts':dict(counter),'error_count':len(errors),'note':'Candidates are not final approvals; preserve user-approved WAVs and all original files.'}
    fields=['sound_id','character','manual_selection','selected','status','EN_WAV','stable_WAV','per_line_WAV',
            'EN_seconds','stable_seconds','per_line_seconds','speaker_model','voice_sim_stable','voice_sim_per_line',
            'voice_score_margin','asr_word_stable','asr_word_per_line','flags','notes']
    entries={
      'SUMMARY.json':json.dumps(summary,indent=2,ensure_ascii=False).encode('utf-8'),
      'ALL_7206_CHOICES.csv':csv_bytes(selected,fields),
      'REVIEW_QUEUE.csv':csv_bytes(review,fields),
      'VOICE_MODEL_SCORES.csv':csv_bytes(scores,['sound_id','stable','per_line','margin','candidate','manual_selection']),
      'ASR_MISSING_QUEUE.csv':csv_bytes(asrqueue,['sound_id','mode','reason','path']),
      'ERROR_RETRY_QUEUE.csv':csv_bytes(errors,['sound_id','stage','error','path']),
      'PRIOR_USER_DECISIONS.csv':csv_bytes([{'sound_id':sid,'selection':entry['decision'],'source':entry['source'],'note':entry['note']} for sid,entry in sorted(manual.items())],['sound_id','selection','source','note']),
      'DECISION_CONFLICTS.csv':csv_bytes(conflicts,['sound_id','old','new','source']),
      'README.txt':('BG Voice RU offline 4.7.1\nOne launcher. One ZIP. One persistent progress database in the same directory.\n'
                    'AI speaker scores are provisional, never final voice approvals.\n'
                    'Missing local model/English originals leads to HOLD, not invented scores.\n'
                    'No Internet access required and no WAV files are modified.\n').encode('utf-8')}
    tmp=work/(REPORT+'.pending')
    with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED,compresslevel=7) as f:
        for filename,data in entries.items():f.writestr(filename,data)
    with zipfile.ZipFile(tmp) as f:
        bad=f.testzip()
        if bad:raise RuntimeError('bad ZIP member '+bad)
    os.replace(tmp,work/REPORT)
    state.close()
    print('SUCCESS: BG Voice RU '+VERSION,flush=True)
    print('ONE REPORT:',work/REPORT,flush=True)
    return 0



def maybe_switch_to_installed_model_env(work,root):
    """Prefer an existing offline Python with speaker/ASR packages; never install or download."""
    if os.name!='nt' or os.environ.get('BG_VOICE_RU_ENV_SELECTED')=='1':return None
    import importlib.util, subprocess
    def score(flags):
        return (10 if flags.get('torch') and flags.get('resemblyzer') else 0) + (8 if flags.get('torch') and flags.get('speechbrain') else 0) + (3 if flags.get('faster_whisper') or flags.get('whisper') else 0)
    names=('.venv','.venv_voxcpm2','.venv_emotion','venv','venv311','vox_env','voice_env','env','VENV')
    current={k:importlib.util.find_spec(k) is not None for k in ('torch','resemblyzer','speechbrain','faster_whisper','whisper')}
    best_score=score(current)
    best=None
    roots=[work,root,root.parent]
    checked=set()
    for base in roots:
        if not base.is_dir():continue
        dirs=[base]
        try:
            dirs.extend(d for d in base.iterdir() if d.is_dir() and d.name.lower() not in ('russian_wav_two_versions','english_wav','reports'))
        except OSError:pass
        for d in dirs:
            for name in names:
                candidate=d/name/'Scripts'/'python.exe'
                if not candidate.is_file() or str(candidate).lower() in checked:continue
                checked.add(str(candidate).lower())
                probe=("import importlib.util,json,sys; n=('torch','resemblyzer','speechbrain','faster_whisper','whisper');"
                       "print(json.dumps({k:importlib.util.find_spec(k) is not None for k in n}))")
                try:
                    r=subprocess.run([str(candidate),'-c',probe],capture_output=True,text=True,timeout=15)
                    if r.returncode or not r.stdout.strip():continue
                    flags=json.loads(r.stdout.strip().splitlines()[-1])
                    rscore=score(flags)
                    if rscore>best_score:
                        best_score=rscore;best=candidate
                except Exception:continue
    if best is None:return None
    print('USING EXISTING OFFLINE MODEL ENV:',best,flush=True)
    launcher=("import sys; p=sys.argv.pop(1); t=open(p,encoding='utf-8-sig').read(); "
              "exec(compile(t.split(chr(10)+'#BGVOICE_PYTHON_START'+chr(10),1)[1],p,'exec'),"
              "{'__name__':'__main__','__file__':p})")
    env=os.environ.copy();env['BG_VOICE_RU_ENV_SELECTED']='1'
    # Same single CMD source, another already-installed interpreter, no auxiliary files.
    return subprocess.call([str(best),'-c',launcher,str(Path(__file__).resolve()),*sys.argv[1:]],env=env)

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument('--self-test',action='store_true')
    p.add_argument('--root',default=os.environ.get('BG_VOICE_RU_ROOT',r'C:\BG_VOICE_RU_MASTER\08_VOXCPM2_ALL_CHARACTERS'))
    p.add_argument('--limit',type=int,default=0)
    a=p.parse_args()
    if a.self_test:return check_self_test()
    # Work folder is always the actual directory containing this updater.
    # Do not use a trailing-backslash argument: cmd.exe quotes may become part of it.
    work=Path(__file__).resolve().parent
    if not work.is_dir():raise RuntimeError('WORK FOLDER MISSING '+str(work))
    root=Path(a.root)
    if not root.is_dir():
        # One error report, in the same folder; do not make any new directory.
        with zipfile.ZipFile(work/REPORT,'w',zipfile.ZIP_DEFLATED) as f:
            f.writestr('ERROR.txt','WAV source directory not found: '+str(root))
        print('SOURCE_ROOT_MISSING:',root)
        return 2
    switched=maybe_switch_to_installed_model_env(work,root)
    if switched is not None:return switched
    return run(work,root,a.limit)



# The only permanent launcher is BG_VOICE_UPDATE.cmd. New engine versions live
# solely as integrity-checked BLOBs in BG_VOICE_RU_PROGRESS.sqlite3.
# No model, audio, text or user decision is ever uploaded by the updater.
BOOTSTRAP_VERSION='4.9.0'
_UPDATE_MANIFEST='https://raw.githubusercontent.com/jeleZa112/nwn-xanos-updates/bg-voice-ru/BG_VOICE_RUNTIME_MANIFEST.json'
_UPDATE_CORE_PREFIX='https://raw.githubusercontent.com/jeleZa112/nwn-xanos-updates/'
_UPDATE_REPOSITORY='jeleZa112/nwn-xanos-updates'
_UPDATE_MAX_BYTES=300000
_UPDATE_PAYLOAD_NAME='BG_VOICE_CORE.py'


def _version_tuple(version):
    m=re.fullmatch(r'(\d+)\.(\d+)\.(\d+)(?:-offline)?',str(version))
    return tuple(map(int,m.groups())) if m else (0,0,0)


def _verified_core(row):
    version,digest,raw=row
    if not isinstance(raw,bytes) or len(raw)>_UPDATE_MAX_BYTES:return None
    if not isinstance(digest,str) or hashlib.sha256(raw).hexdigest()!=digest:return None
    if _version_tuple(version)<(4,9,0):return None
    try:
        source=raw.decode('utf-8-sig')
        compile(source,'<bg_voice_cached_core>','exec')
    except (SyntaxError,UnicodeError,ValueError):return None
    return source


def _download_checked(url, limit, timeout=4):
    import urllib.request
    req=urllib.request.Request(url,headers={'User-Agent':'BG-Voice-RU-Local-Updater/4.9'})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        if resp.geturl()!=url:raise RuntimeError('Update redirects are not accepted')
        raw=resp.read(limit+1)
    if len(raw)>limit:raise RuntimeError('Update exceeds size limit')
    return raw


def _check_core_self_test(raw):
    import subprocess
    child='import sys;path=sys.argv.pop(1);code=sys.stdin.buffer.read();exec(compile(code,"<verified_voice_engine>","exec"),{"__name__":"__main__","__file__":path})'
    env=os.environ.copy()
    env['BG_VOICE_RU_ENV_SELECTED']='1'
    env['BG_VOICE_RU_OFFLINE']='1'
    result=subprocess.run([sys.executable,'-c',child,str(Path(__file__).resolve()),'--self-test'],input=raw,
                          capture_output=True,timeout=30,env=env)
    return result.returncode==0 and b'SELF_TEST_OK' in result.stdout


def _boot_cached_or_fallback():
    # --offline explicitly forbids network, but still uses the latest cached engine.
    offline=(os.environ.get('BG_VOICE_RU_OFFLINE','').lower() in ('1','true','yes')
             or '--offline' in sys.argv or '--no-update' in sys.argv)
    force='--check-update' in sys.argv
    sys.argv[:]=[x for x in sys.argv if x not in ('--offline','--no-update','--check-update')]
    if '--self-test' in sys.argv:return False
    work=Path(__file__).resolve().parent
    if not work.is_dir():return False
    database=work/DB_FILE
    try:
        conn=sqlite3.connect(str(database),timeout=20)
        conn.execute('pragma busy_timeout=20000')
        conn.execute("""create table if not exists bgvoice_cached_engines (
            version text primary key, sha256 text not null, source blob not null, at_utc text not null)""")
        conn.execute("""create table if not exists bgvoice_update_status (
            slot integer primary key, last_checked text not null, last_result text not null)""")
        conn.commit()
    except (sqlite3.Error,OSError) as exc:
        print('AUTO UPDATE: database not writable; using embedded offline engine:',repr(exc),flush=True)
        try:conn.close()
        except Exception:pass
        return False
    try:
        existing=conn.execute('select version,sha256,source from bgvoice_cached_engines').fetchall()
        valid=sorted(((row[0],_verified_core(row)) for row in existing),key=lambda x:_version_tuple(x[0]),reverse=True)
        valid=[x for x in valid if x[1] is not None]
        cached_version,cached_source=valid[0] if valid else ('4.8.0',None)
        status=conn.execute('select last_checked from bgvoice_update_status where slot=1').fetchone()
        due=True
        if status and not force:
            try:
                age=(dt.datetime.now(dt.timezone.utc)-dt.datetime.fromisoformat(status[0])).total_seconds()
                due=age>=6*3600 or age<0
            except (ValueError,TypeError):pass
        if not offline and due:
            result='not_checked'
            try:
                manifest_raw=_download_checked(_UPDATE_MANIFEST,8192)
                release=json.loads(manifest_raw.decode('utf-8'))
                version=str(release.get('version',''))
                commit=str(release.get('commit',''))
                digest=str(release.get('sha256','')).lower()
                if release.get('project')!='BG_VOICE_RU' or release.get('path')!=_UPDATE_PAYLOAD_NAME:
                    raise RuntimeError('Unrecognized update manifest')
                if not re.fullmatch('[0-9a-f]{40}',commit) or not re.fullmatch('[0-9a-f]{64}',digest):
                    raise RuntimeError('Invalid update pin')
                if _version_tuple(version)<(4,9,0):raise RuntimeError('Unrecognized update version')
                if _version_tuple(version)>_version_tuple(cached_version):
                    target=_UPDATE_CORE_PREFIX+_UPDATE_REPOSITORY+'/'+commit+'/'+_UPDATE_PAYLOAD_NAME
                    raw=_download_checked(target,_UPDATE_MAX_BYTES,timeout=8)
                    if hashlib.sha256(raw).hexdigest()!=digest:raise RuntimeError('SHA256 mismatch')
                    if not _check_core_self_test(raw):raise RuntimeError('Update self-test failed')
                    with conn:
                        conn.execute('insert or replace into bgvoice_cached_engines values(?,?,?,?)',
                                     (version,digest,raw,now()))
                        # Keep current and prior versions for safe rollback.
                        old=conn.execute('select version from bgvoice_cached_engines').fetchall()
                        for (v,) in sorted(old,key=lambda x:_version_tuple(x[0]),reverse=True)[2:]:
                            conn.execute('delete from bgvoice_cached_engines where version=?',(v,))
                    cached_version,cached_source=version,raw.decode('utf-8-sig')
                    result='updated_to_'+version
                else:result='up_to_date_'+cached_version
            except Exception as exc:
                result='offline_fallback_'+type(exc).__name__+': '+str(exc)[:180]
            with conn:
                conn.execute('insert or replace into bgvoice_update_status values(1,?,?)',(now(),result))
            print('AUTO UPDATE:',result,flush=True)
        elif offline:
            print('AUTO UPDATE: offline mode, no network requests',flush=True)
        else:print('AUTO UPDATE: recent check already completed',flush=True)
    finally:conn.close()
    if cached_source is None:
        print('AUTO UPDATE: embedded engine 4.8.0 (no cached update)',flush=True)
        return False
    print('AUTO UPDATE: using verified local engine '+cached_version,flush=True)
    # The core runs entirely locally. The same launcher remains the one entrypoint.
    # __file__ deliberately refers to the cmd file so progress/report paths stay put.
    namespace={'__name__':'__main__','__file__':str(Path(__file__).resolve()),'__package__':None}
    exec(compile(cached_source,str(Path(__file__).resolve()),'exec'),namespace)
    return True

# BGVOICE_STRESS_SINGLEFILE_BEGIN
# Additional guarded route for the existing one-file updater.
# It never alters BG files, old RU WAVs, model files, or cached engine versions.
def _singlefile_shtorm_v60(mode):
    import csv as _csv
    import io as _io
    import subprocess as _subprocess
    import tempfile as _tempfile
    import wave as _wave
    from datetime import timezone as _timezone

    schema='BGVOICE_SHTORM_STRESS_SINGLEFILE_V1'
    home=Path.home()
    base=Path(os.environ.get('BG_VOICE_FULL_PRODUCTION_ROOT') or
              (home/'Documents'/'BG_VOICE_RU'/'FULL_PRODUCTION'))
    prior=Path(os.environ.get('BG_VOICE_V60_ZIP') or
               (base/'V60_SHTORM_RETAKES'/'SEND_TO_CHATGPT_BGVOICE_V60_SHTORM_RETAKES.zip'))
    target=base/'STRESS_V60_CANDIDATES'
    report=base/'SEND_TO_CHATGPT_BG_VOICE_RU.zip'
    allowed={
      'OH85856':{'text':'Ты отл+ично спр+авилась, Хексат.',
                 'risk':'Proper name Хексат has no verified accent; review name and clipped opening Ты'},
      'OH80404':{'text':'Последователи +Истины Двуединой! Возр+адуйтесь! Коллус Даратон здесь! Ваш господ+ин верн+улся!',
                 'risk':'Words Последователи, Двуединой and names Коллус Даратон not stress-marked until verified; check ceremonial acting'},
      'OH89888':{'text':'Уб+ийца! Богох+ульник и оскверн+итель всев+о свят+ого!',
                 'risk':'Phonetic-only всего -> всево; original game text stays unchanged; verify enraged delivery'}
    }
    def _sha(blob):return hashlib.sha256(blob).hexdigest()
    def _timestamp():return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
    def _json(z,name,max_bytes=150000):
        if name not in z.namelist() or z.getinfo(name).file_size>max_bytes:
            raise RuntimeError('SOURCE_REPORT_MISSING_OR_TOO_LARGE '+name)
        return json.loads(z.read(name).decode('utf-8-sig'))
    def _validate_annotation(k,clean):
        marked=allowed[k]['text']
        if re.search(r'\+(?![аеёиоуыэюяАЕЁИОУЫЭЮЯ])',marked):
            raise RuntimeError('INVALID_STRESS_VOWEL '+k)
        if marked.count('+')<2:raise RuntimeError('MISSING_STRESS_MARKS '+k)
        plain=marked.replace('+','')
        plain=plain.replace('всево','всего') if k=='OH89888' else plain
        if plain!=clean:raise RuntimeError('ANNOTATION_CHANGED_GAME_WORDS '+k+': '+plain)
    if mode=='selftest':
        for sid,t in {'OH85856':'Ты отлично справилась, Хексат.',
                       'OH80404':'Последователи Истины Двуединой! Возрадуйтесь! Коллус Даратон здесь! Ваш господин вернулся!',
                       'OH89888':'Убийца! Богохульник и осквернитель всего святого!'}.items():
            _validate_annotation(sid,t)
        assert all('+' not in x['risk'] for x in allowed.values())
        print('STRESS_SINGLEFILE_SELFTEST_OK: 3 verified annotation transforms; no files written')
        return 0
    if not prior.is_file():
        print('HOLD: V60 SOURCE REPORT MISSING:',prior,flush=True)
        print('Original updater and game unchanged.',flush=True)
        return 2
    os.environ.update({'HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1',
                       'HF_DATASETS_OFFLINE':'1','HF_HUB_DISABLE_TELEMETRY':'1'})
    statuses=[]
    refs={}
    old={}
    try:
        with zipfile.ZipFile(prior,'r') as z:
            if z.testzip() is not None:raise RuntimeError('V60_ZIP_CRC_FAIL')
            members=z.infolist()
            if len(members)>200 or sum(f.file_size for f in members)>100*1024*1024:
                raise RuntimeError('V60_ARCHIVE_EXCEEDS_SAFE_BOUNDS')
            if len({x.filename for x in members})!=len(members):
                raise RuntimeError('DUPLICATE_V60_ARCHIVE_ENTRIES')
            v60=_json(z,'V60_REPORT_SUMMARY.json')
            spec=_json(z,'04_PILOT_6_ALLCAPS_SHTORM_JOBS.json')
            if v60.get('schema')!='BGVOICE_V60_RUNTIME_REPORT_V1' or spec.get('schema')!='BG_VOICE_RU_V59_PILOT_V1':
                raise RuntimeError('WRONG_V60_REPORT_SCHEMA')
            if v60.get('errors',0)!=0 or v60.get('game_files_modified') is not False:
                raise RuntimeError('V60_REPORT_NOT_SAFE')
            if spec.get('model_commit')!='481ce519010efd9a110277400132429763fbdab1':
                raise RuntimeError('WRONG_SHTORM_REVISION')
            src_jobs={j['sound_id']:j for j in spec['jobs']}
            completed={r['sound_id']:r for r in v60['items'] if r.get('generated')}
            if not set(allowed)<=set(src_jobs)&set(completed):
                raise RuntimeError('V60_MISSING_APPROVED_SOURCE_SET')
            for sid in allowed:
                j=src_jobs[sid];oldsha=completed[sid]['candidate_sha256']
                _validate_annotation(sid,j['tts_speech_text'])
                en_name='SOURCE_EN/'+sid+'_EN.wav'
                old_name='CANDIDATES/'+sid+'__V60_SHTORM_FULL_LINE_CANDIDATE.wav'
                if en_name not in z.namelist() or old_name not in z.namelist():
                    raise RuntimeError('MISSING_EXACT_EN_OR_OLD_RU '+sid)
                ref=z.read(en_name);previous=z.read(old_name)
                expected=j['en_reference_sha256']
                if _sha(ref)!=expected or _sha(ref)!=completed[sid]['reference_sha_expected']:
                    raise RuntimeError('EN_SOURCE_SHA_MISMATCH '+sid)
                if _sha(previous)!=oldsha:raise RuntimeError('OLD_V60_SHA_MISMATCH '+sid)
                if 'source_en_sha256' in v60 and v60['source_en_sha256']!=expected:
                    raise RuntimeError('SOURCE_IDENTITY_CONFLICT '+sid)
                refs[sid]=ref;old[sid]=previous
                statuses.append({'sound_id':sid,'source_en_sha256':expected,
                    'previous_v60_sha256':oldsha,'tts_original':j['tts_speech_text'],
                    'tts_stress_marked':allowed[sid]['text'],'risk':allowed[sid]['risk'],
                    'voice_id_source':j.get('voice_id_source',''),
                    'model_revision_expected':spec['model_commit'],
                    'style_metadata_not_a_model_control':j.get('style_metadata',''),
                    'status':'PREFLIGHT_OK_NOT_GENERATED',
                    'install_allowed':False})
    except Exception as exc:
        print('SHTORM SOURCE HOLD:',str(exc),flush=True)
        return 2
    if mode=='generate':
        # No independent updater; re-enter this same CMD through its own embedded Python.
        try:
            import importlib.util as _ilu
            missing=any(_ilu.find_spec(x) is None for x in ('torch','voxcpm','soundfile','numpy'))
        except (ImportError,ValueError):missing=True
        if missing:
            if os.environ.get('BGVOICE_SINGLEFILE_SHTORM_ENV')=='1':
                print('HOLD: VOXCPM_VENV_DEPENDENCIES_MISSING',flush=True);return 2
            venv=(home/'Downloads'/'BG_VOICE_RU_KELDORN_EMOTION_CLONING_PILOT_V1'/
                  'BG_VOICE_RU_KELDORN_CLONE_PILOT'/'.venv'/'Scripts'/'python.exe')
            if not venv.is_file():
                print('HOLD: KNOWN_EXISTING_VOXCPM_VENV_NOT_FOUND',flush=True);return 2
            env=os.environ.copy();env['BGVOICE_SINGLEFILE_SHTORM_ENV']='1'
            cmd=env.get('BGV_COMMAND')
            if not cmd:
                cmd=("import sys;p=sys.argv.pop(1);t=open(p,encoding='utf-8-sig').read();"
                     "exec(compile(t.split(chr(10)+'#BGVOICE_PYTHON_START'+chr(10),1)[1],p,'exec'),"
                     "{'__name__':'__main__','__file__':p})")
            print('USING_PREEXISTING_SHTORM_ENV:',venv,flush=True)
            return _subprocess.call([str(venv),'-u','-c',cmd,str(Path(__file__).resolve()),
                                      '--shtorm-stress-v60'],env=env)
        model_path=Path(r'C:\BG_VOICE_RU_MASTER\08_VOXCPM2_ALL_CHARACTERS\EXPERIMENTAL_MODELS\Shtorm-VoxCPM2-RU_481ce51')
        model_identity=v60.get('model',{}).get('sha256_identity',{})
        modelfile=model_path/'model.safetensors'
        if not modelfile.is_file():
            print('HOLD: EXISTING_MODEL_NOT_FOUND',flush=True);return 2
        mstat=modelfile.stat()
        if (mstat.st_size!=model_identity.get('size') or
            mstat.st_mtime_ns!=model_identity.get('mtime_ns') or
            model_identity.get('sha256')!='5c61cb1e9090a852c0f282a6bdd1be31f0c79ad94849f6376f8e6ea312f8d3b1'):
            print('HOLD: MODEL_IDENTITY_CHANGED_SINCE_REAL_V60',flush=True);return 2
        import torch as _torch
        import numpy as _np
        import soundfile as _sf
        from voxcpm import VoxCPM as _VoxCPM
        if not _torch.cuda.is_available():
            print('HOLD: CUDA_NOT_AVAILABLE',flush=True);return 2
        free,_=_torch.cuda.mem_get_info(0)
        if free<3*1024**3:
            print('HOLD: CLOSE_GAME_NEEDS_AT_LEAST_3_GIB_FREE_VRAM',flush=True);return 2
        target.mkdir(parents=True,exist_ok=True)
        todo=[]
        for row in statuses:
            sid=row['sound_id']
            fp=_sha(json.dumps({'schema':schema,'id':sid,'text':row['tts_stress_marked'],
                       'reference_sha':row['source_en_sha256'],'model_sha':model_identity['sha256'],
                       'steps':12,'cfg_value':2.0},sort_keys=True,ensure_ascii=False).encode())
            row['fingerprint']=fp
            dest=target/(sid+'__SHTORM_STRESS_SINGLEFILE.wav')
            side=target/(sid+'__SHTORM_STRESS_SINGLEFILE.json')
            if dest.exists() and side.exists():
                meta=json.loads(side.read_text(encoding='utf-8'))
                if (meta.get('fingerprint')==fp and _sha(dest.read_bytes())==meta.get('sha256')):
                    row['status']='REUSED_VERIFIED_CANDIDATE';row['candidate_sha256']=meta['sha256'];continue
                row['status']='HOLD_EXISTING_FILE_CONFLICT';continue
            if dest.exists() or side.exists():
                row['status']='HOLD_PARTIAL_EXISTING_FILES';continue
            todo.append((row,dest,side))
        if todo:
            print('LOAD_EXISTING_SHTORM_ONCE: ',model_path,flush=True)
            model=_VoxCPM.from_pretrained(str(model_path),device='cuda:0',optimize=False,load_denoiser=False)
            for row,dest,side in todo:
                sid=row['sound_id'];tmppath=None
                try:
                    # The English reference remains immutable in the V60 ZIP; only a temporary copy is made.
                    with _tempfile.TemporaryDirectory(prefix='bgvoice_stress_') as td:
                        refpath=Path(td)/(sid+'_EN.wav')
                        refpath.write_bytes(refs[sid])
                        seed=int(hashlib.sha256((sid+schema).encode()).hexdigest()[:8],16)
                        _torch.manual_seed(seed)
                        with _torch.inference_mode():
                            generated=model.generate(text=row['tts_stress_marked'],
                                reference_wav_path=str(refpath),cfg_value=2.0,
                                inference_timesteps=12,normalize=False,denoise=False)
                    rate=int(model.tts_model.sample_rate)
                    a=_np.asarray(generated,dtype='float32').reshape(-1)
                    if (rate<8000 or rate>96000 or not _np.isfinite(a).all() or
                        len(a)<rate//3 or len(a)>90*rate or
                        float(_np.sqrt(_np.mean(a.astype('float64')**2)))<0.001):
                        raise RuntimeError('INVALID_AUDIO_EMPTY_OR_NAN')
                    peak=float(_np.max(_np.abs(a)))
                    if peak>0.98:a=a*(0.98/peak)
                    tmppath=dest.with_suffix('.tmp.wav')
                    if tmppath.exists():raise RuntimeError('EXISTING_TEMP_WAV_CONFLICT')
                    _sf.write(str(tmppath),a,rate,subtype='PCM_16')
                    os.replace(tmppath,dest)
                    sha=_sha(dest.read_bytes())
                    metadata={'schema':schema,'fingerprint':row['fingerprint'],'sha256':sha,
                        'generated_utc':_timestamp(),'seconds':round(len(a)/rate,3),
                        'game_install_ready':False,'stress_model_guaranteed_correct':False}
                    tmp=side.with_suffix('.tmp.json')
                    tmp.write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
                    os.replace(tmp,side)
                    row['status']='CREATED_STRESS_CANDIDATE_NEEDS_HUMAN_QA'
                    row['candidate_sha256']=sha
                    print('CREATED_STRESS_CANDIDATE',sid,'seconds',metadata['seconds'],flush=True)
                except Exception as exc:
                    row['status']='GENERATION_ERROR_HOLD'
                    row['error']=type(exc).__name__+': '+str(exc)[:200]
                    print('CONTINUE_AFTER_ERROR',sid,row['error'],flush=True)
                finally:
                    if tmppath is not None and tmppath.is_file():
                        tmppath.unlink()
                    try:_torch.cuda.empty_cache()
                    except Exception:pass
    # The one report is in the permanent FULL_PRODUCTION folder; no new CMD/PY launcher.
    base.mkdir(parents=True,exist_ok=True)
    entries={}
    summary={'schema':schema,'utc':_timestamp(),'mode':mode,'report_source':str(prior),
        'single_launcher':str(Path(__file__).resolve()),
        'manual_review_required':True,'game_writes':False,'reused_existing_model':True,
        'model_commit_not_cryptographically_proved':True,
        'model_file_sha_from_V60':'5c61cb1e9090a852c0f282a6bdd1be31f0c79ad94849f6376f8e6ea312f8d3b1',
        'approved_to_install':0,'items':statuses,
        'notes':['This is NOT a final release or proof of correctness of audible stress.',
                 'Only verified vowel accents are marked; unverified fantasy names stay unmarked.',
                 'Full uppercase game text is unchanged; phonetic hints apply to TTS only.',
                 'Shtorm V60 style metadata is not independent emotion control.']}
    entries['STRESS_V60/SUMMARY.json']=json.dumps(summary,ensure_ascii=False,indent=2).encode('utf-8')
    # Copy only known, SHA-checked assets. No extraction to the game directory.
    for row in statuses:
        sid=row['sound_id']
        entries['STRESS_V60/SOURCE_EN/'+sid+'_EN.wav']=refs[sid]
        entries['STRESS_V60/OLD_V60/'+sid+'_V60.wav']=old[sid]
        dest=target/(sid+'__SHTORM_STRESS_SINGLEFILE.wav')
        if (row['status'] in ('REUSED_VERIFIED_CANDIDATE','CREATED_STRESS_CANDIDATE_NEEDS_HUMAN_QA')
            and dest.is_file() and _sha(dest.read_bytes())==row.get('candidate_sha256')):
            entries['STRESS_V60/NEW_CANDIDATES/'+dest.name]=dest.read_bytes()
    cards=[]
    for row in statuses:
        sid=row['sound_id']
        def aud(label,path):
            return '<p>'+label+'<audio controls preload="none" style="width:100%" src="'+path+'"></audio></p>'
        cards.append('<section><h2>'+sid+'</h2><p>Игра: '+row['tts_original']+
          '</p><p>Для Shtorm: <b>'+row['tts_stress_marked']+'</b></p><p>'+row['risk']+'</p>'+
          aud('EN по точному Sound ID','SOURCE_EN/'+sid+'_EN.wav')+
          aud('V60 без ударений','OLD_V60/'+sid+'_V60.wav')+
          (aud('Новый вариант с ударениями','NEW_CANDIDATES/'+sid+'__SHTORM_STRESS_SINGLEFILE.wav')
           if 'candidate_sha256' in row else '<p>Новый WAV ещё не создан.</p>')+'</section>')
    html='<html lang="ru"><meta charset="utf-8"><title>BG Voice RU — Shtorm stress</title><style>body{max-width:850px;margin:auto;padding:16px;background:#101a27;color:white;font:16px system-ui}section{background:#233344;padding:16px;margin:12px 0;border-radius:10px}</style><h1>V60: ударения Shtorm — только кандидатные WAV</h1><p>Это прослушивание, не подтверждение и не установка. Из архива извлеки папку STRESS_V60 целиком и открой этот HTML.</p>'+''.join(cards)+'</html>'
    entries['STRESS_V60/OPEN_REVIEW.html']=html.encode('utf-8')
    # Preserve a report created by this same route, refuse to replace a foreign report.
    if report.exists():
        try:
            with zipfile.ZipFile(report) as z:
                prev=_json(z,'STRESS_V60/SUMMARY.json')
                if prev.get('schema')!=schema:raise RuntimeError('FOREIGN_REPORT_EXISTS')
        except Exception:
            print('HOLD: REPORT_FILENAME_ALREADY_USED_BY_OTHER_PROCESS',report,flush=True)
            return 2
    tmp=report.with_suffix('.zip.pending')
    if tmp.exists():raise RuntimeError('PENDING_REPORT_EXISTS_REFUSE_OVERWRITE')
    try:
        with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for name,data in entries.items():z.writestr(name,data)
        with zipfile.ZipFile(tmp) as z:
            if z.testzip() is not None:raise RuntimeError('GENERATED_REPORT_ZIP_CRC_FAILED')
        os.replace(tmp,report)
    finally:
        if tmp.exists():tmp.unlink()
    print('REPORT:',report,flush=True)
    print('SOURCE_WAV_UNCHANGED, NEW_CANDIDATES:',sum('candidate_sha256' in r for r in statuses),flush=True)
    return 0 if all('ERROR' not in r['status'] and 'CONFLICT' not in r['status'] for r in statuses) else 2
# BGVOICE_STRESS_SINGLEFILE_END

# BGVOICE_V68_OH89888_ACTING_AND_FX_BEGIN
# One-updater-only, non-destructive experimental retake. Not a game install.
def _v68_oh89888(mode):
    import array as _array
    import base64 as _b64
    import html as _html
    import io as _io
    import shutil as _shutil
    import subprocess as _sp
    import tempfile as _tmp
    import wave as _wave
    from time import time as _time

    schema='BGVOICE_OH89888_ACTING_FX_V68_20261122'
    sid='OH89888'
    home=Path.home()
    root=Path(os.environ.get('BG_VOICE_FULL_PRODUCTION_ROOT') or
              (home/'Documents'/'BG_VOICE_RU'/'FULL_PRODUCTION'))
    report=root/'SEND_TO_CHATGPT_BG_VOICE_RU.zip'
    target=root/'V68_OH89888_CANDIDATES'
    enname='STRESS_V60/SOURCE_EN/OH89888_EN.wav'
    v60name='STRESS_V60/OLD_V60/OH89888_V60.wav'
    v65name='STRESS_V60/NEW_CANDIDATES/OH89888__SHTORM_STRESS_SINGLEFILE.wav'
    expected={
       enname:'42d64858903c23ae66906f9b4e5488966fdc2f0cc9de26efac00ee2eaf46064d',
       v60name:'d81f89aacf8d8fbb0123f094a521c1d4b4bc16cec04023ee0c98e0e1c4d0582e',
       v65name:'15d14800e139317edfb23022a4c9d5d9382a4bd443b556771de8ffada383e998',
       'STRESS_V60/NEW_CANDIDATES/OH85856__SHTORM_STRESS_SINGLEFILE.wav':'32d3a454fb164fd92e1673307fc8aeba1eae1daf58fb5c24baa726795ce937fa',
       'STRESS_V60/OLD_V60/OH80404_V60.wav':'9ea03060b20c4cdd2bb7adb937bea479bd42fe3b17b7b0086dd5e9d4d493ce9f',
    }
    manual={'schema':'BGVOICE_V65_HUMAN_DECISIONS_LOCK_V1','OH85856':{'preferred':'V65','stress':'PASS','speech':'PASS','voice_emotion':'PASS','protected_sha256':expected['STRESS_V60/NEW_CANDIDATES/OH85856__SHTORM_STRESS_SINGLEFILE.wav']},'OH80404':{'preferred':'V60','stress':'PASS','speech':'PASS','voice_emotion':'PASS','protected_sha256':expected['STRESS_V60/OLD_V60/OH80404_V60.wav']},'OH89888':{'preferred':'BOTH_BAD','stress':'PASS','speech':'PASS','voice_emotion':'FAIL','user_note':'Вялый/медленный русский голос, не передаёт эмоцию и эффект оригинала; возможно эхо. ВОСПРОИЗВЕСТИ АКТЁРСКУЮ ПОДАЧУ И АКУСТИКУ ОТДЕЛЬНО.'}}
    text_original='Убийца! Богохульник и осквернитель всего святого!'
    stress_original='Уб+ийца! Богох+ульник и оскверн+итель всев+о свят+ого!'
    tasks={
       'DRY_A':{'text':'Уб+ийца!! Богох+ульник!!! И оскверн+итель всев+о свят+ого!!!', 'cfg':1.7, 'seed':680101, 'intent':'Резкие короткие эмоциональные выкрики, не слова «крик/злость»'},
       'DRY_B':{'text':'Уб+ийца! Богох+ульник! И оскверн+итель всев+о свят+ого!', 'cfg':2.3, 'seed':680102, 'intent':'Настойчивая энергичная фразировка без лишних пауз'},
    }
    def sha(b):return hashlib.sha256(b).hexdigest()
    def stamp():return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
    def cleanwords(t):
        t=t.replace('+','').replace('всево','всего')
        return re.findall(r'[а-яё]+',t.lower())
    def validate_text():
        baseline=cleanwords(text_original)
        assert baseline==cleanwords(stress_original)
        for key,t in tasks.items():
            if cleanwords(t['text'])!=baseline:raise RuntimeError('RETAKE_CHANGED_ORIGINAL_WORDS: '+key)
            if re.search(r'\+(?![аеёиоуыэюяАЕЁИОУЫЭЮЯ])',t['text']):raise RuntimeError('INVALID_STRESS_MARKER: '+key)
            if t['text'].count('+')<4:raise RuntimeError('STRESS_MARKERS_LOST: '+key)
    def open_wav(data):
        with _wave.open(_io.BytesIO(data),'rb') as w:
            rate=w.getframerate();channels=w.getnchannels();width=w.getsampwidth();frames=w.getnframes();samples=w.readframes(frames)
        if channels!=1 or width!=2 or not(8000<=rate<=96000) or frames<=0 or frames>rate*30:
            raise RuntimeError('WAV_EXPECT_PCM16_MONO_SHORT')
        a=_array.array('h');a.frombytes(samples)
        if sys.byteorder!='little':a.byteswap()
        if len(a)!=frames:raise RuntimeError('BAD_PCM_LENGTH')
        return rate,a
    def pack_wav(rate,a):
        b=_array.array('h',a)
        if sys.byteorder!='little':b.byteswap()
        bio=_io.BytesIO()
        with _wave.open(bio,'wb') as w:
            w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(b.tobytes())
        return bio.getvalue()
    def make_fx(raw,profile):
        # Explicit hypotheses, not claimed reverse engineering of the EN effect.
        rate,arr=open_wav(raw)
        if profile=='FX_A':taps=[(0.074,.19),(0.141,.095),(0.215,.047)];tail=.29
        elif profile=='FX_B':taps=[(.047,.14),(.096,.12),(.158,.095),(.243,.055),(.312,.028)];tail=.38
        else:raise RuntimeError('INVALID_FX_PROFILE')
        n=len(arr); length=n+int(rate*tail)
        result=[float(x) for x in arr]+[0.]*max(0,length-n)
        # Damped repeated reflections; direct dry speech remains intelligible.
        for d,g in taps:
            delay=int(round(d*rate))
            for i,x in enumerate(arr):
                j=i+delay
                if j<length:
                    result[j]+=g*(float(x)+float(arr[i-1] if i>0 else 0.0))*0.5
        mx=max(abs(x) for x in result) or 1.
        scale=min(1.,30500./mx)
        out=_array.array('h',(int(max(-32768.,min(32767.,round(x*scale)))) for x in result))
        return pack_wav(rate,out)
    def archive_load():
        if not report.is_file():raise RuntimeError('SINGLE_REPORT_MISSING: '+str(report))
        with zipfile.ZipFile(report) as z:
            if z.testzip() is not None:raise RuntimeError('EXISTING_REPORT_BAD_CRC')
            info=z.infolist()
            if len(info)>4000 or sum(x.file_size for x in info)>512*1024*1024:
                raise RuntimeError('EXISTING_REPORT_TOO_LARGE')
            names=[x.filename for x in info]
            if len(set(names))!=len(names):raise RuntimeError('DUPLICATE_EXISTING_REPORT_ENTRY')
            for name in names:
                if name.startswith('/') or '..' in Path(name).parts or '\\' in name:
                    raise RuntimeError('UNSAFE_REPORT_ENTRY_NAME')
            for name,hash_ in expected.items():
                if name not in names or sha(z.read(name))!=hash_:
                    raise RuntimeError('USER_APPROVED_OR_SOURCE_WAV_SHA_MISMATCH: '+name)
            prev=json.loads(z.read('STRESS_V60/SUMMARY.json').decode('utf-8'))
            if prev.get('schema')!='BGVOICE_SHTORM_STRESS_SINGLEFILE_V1':
                raise RuntimeError('V65_REPORT_SCHEMA_MISMATCH')
            return {name:z.read(name) for name in names}
    def store_one(filename,b):
        if not target.is_dir():target.mkdir(parents=True,exist_ok=True)
        p=target/filename
        if p.exists():
            if sha(p.read_bytes())==sha(b):return
            raise RuntimeError('DO_NOT_OVERWRITE_DIFFERENT_EXISTING_WAV: '+filename)
        tmp=p.with_suffix('.wav.pending')
        if tmp.exists():raise RuntimeError('LEFTOVER_PENDING_FILE: '+str(tmp))
        try:
            tmp.write_bytes(b)
            if sha(tmp.read_bytes())!=sha(b):raise RuntimeError('TEMP_FILE_HASH_MISMATCH')
            os.replace(tmp,p)
        finally:
            if tmp.exists():tmp.unlink()
    def load_cached(key,fp):
        p=target/(sid+'__'+key+'.wav');j=target/(sid+'__'+key+'.json')
        if p.exists() and j.exists():
            meta=json.loads(j.read_text(encoding='utf-8-sig'))
            data=p.read_bytes()
            if meta.get('fingerprint')==fp and meta.get('sha256')==sha(data):return data
            raise RuntimeError('CACHED_CANDIDATE_FINGERPRINT_CONFLICT: '+key)
        if p.exists() or j.exists():raise RuntimeError('INCOMPLETE_CACHE_REFUSE_OVERWRITE: '+key)
        return None
    def store_cached(key,fp,data,details):
        p=target/(sid+'__'+key+'.wav');j=target/(sid+'__'+key+'.json')
        store_one(p.name,data)
        details=dict(details,fingerprint=fp,sha256=sha(data),generated_utc=stamp(),game_install_ready=False)
        tmp=j.with_suffix('.json.pending')
        if j.exists():raise RuntimeError('EXISTING_JSON_CACHE_REFUSE_OVERWRITE')
        try:
            tmp.write_text(json.dumps(details,ensure_ascii=False,indent=2),encoding='utf-8')
            os.replace(tmp,j)
        finally:
            if tmp.exists():tmp.unlink()
    def embed_page(items,summary):
        audio=[]
        for label,raw in items:
            fmt='audio/wav'
            audio.append('<div class="sound"><strong>'+_html.escape(label)+'</strong><audio controls preload="none" src="data:'+fmt+';base64,'+_b64.b64encode(raw).decode('ascii')+'"></audio></div>')
        head='''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>BG Voice RU — OH89888 V68</title><style>body{font:16px system-ui;background:#0e1620;color:#f6f6f6;max-width:860px;margin:auto;padding:24px}h1{font-size:23px}.sound{padding:12px;background:#1d2b3a;border-radius:10px;margin:10px 0}audio{display:block;width:100%;margin-top:8px}label{display:block;margin:12px 0}button,textarea,select{font:inherit;padding:8px;border-radius:6px}textarea{width:95%}small{color:#bac4cc}</style><h1>BG Voice RU — OH89888</h1><p>Текст: Убийца! Богохульник и осквернитель всего святого!</p><p>Ручной вердикт V65: V60 и V65 отклонены, слова/ударения верны, эмоция и эффект не переданы. Ничего не устанавливается в игру.</p>'''
        tail='''<h2>Твоя оценка</h2><label>Лучший дубль <select id="best"><option value="BOTH_BAD">Пока все плохие</option>'''+''.join('<option value="'+_html.escape(k)+'">'+_html.escape(k)+'</option>' for k in summary['candidate_names'])+'''</select></label><label>Текст и ударения <select id="speech"><option value="PASS">Правильно</option><option value="FAIL">Ошибка</option><option value="UNKNOWN">Не уверен</option></select></label><label>Эмоция/голос <select id="acting"><option value="FAIL">Ещё не подходит</option><option value="PASS">Подходит</option><option value="UNKNOWN">Не уверен</option></select></label><label>Замечания <textarea id="note" rows="3" placeholder="Эффект эха, голос, скорость, крик..."></textarea></label><button onclick="download()">Сохранить оценку JSON</button><script>function download(){const d={schema:'BGVOICE_V68_OH89888_HUMAN_QA',sound_id:'OH89888',preferred:document.getElementById('best').value,speech_and_stress:document.getElementById('speech').value,voice_and_emotion:document.getElementById('acting').value,notes:document.getElementById('note').value};const a=document.createElement('a');a.download='BGVOICE_OH89888_V68_REVIEW.json';a.href=URL.createObjectURL(new Blob([JSON.stringify(d,null,2)],{type:'application/json'}));a.click();setTimeout(()=>URL.revokeObjectURL(a.href),2000)}</script><p><small>Два утверждённых ранее дубля OH85856 и OH80404 не меняются.</small></p></html>'''
        return (head+''.join(audio)+tail).encode('utf-8')
    try:
        validate_text()
        if mode=='selftest':
            rate=16000
            a=_array.array('h',[int(15000*math.sin(2*math.pi*440*i/rate)) for i in range(rate//4)])
            raw=pack_wav(rate,a)
            for fx in ('FX_A','FX_B'):
                r,ary=open_wav(make_fx(raw,fx))
                if r!=rate or len(ary)<=len(a):raise RuntimeError('FX_SELFTEST_FAILED')
            print('V68_SELFTEST_PASS: stress+text guards; PCM FX A/B; no original WAV writes',flush=True)
            return 0
        original=archive_load()
        ref=original[enname];old60=original[v60name];old65=original[v65name]
        if mode=='preflight':
            print('V68_PREFLIGHT_PASS: original EN, V60, V65 and two human-lock SHA256 proven',flush=True)
            print('V68_REQUESTED_TASK: OH89888 only; old approvals immutable; no game writes',flush=True)
            return 0
        # Offline effects can proceed even when ML cannot load.
        collection={}
        entries={}
        notes=[]
        jobs=[]
        for typ in ('FX_A','FX_B'):
            key='V65_'+typ
            fpr=sha(json.dumps({'schema':schema,'id':sid,'base':expected[v65name],'type':typ},sort_keys=True).encode())
            try:
                content=load_cached(key,fpr)
                status='REUSED_VERIFIED' if content is not None else 'GENERATED'
                if content is None:
                    content=make_fx(old65,typ)
                    store_cached(key,fpr,content,{'source_sha256':expected[v65name],'effect':typ})
                collection[key]=content
                jobs.append({'candidate':key,'status':status,'sha256':sha(content),'input':'V65','type':'ACOUSTIC_EFFECT_EXPERIMENT','stress_unchanged':True})
                print('CREATED_OR_REUSED_FX',key,flush=True)
            except Exception as exc:
                jobs.append({'candidate':key,'status':'HOLD','error':str(exc)[:300]})
                print('HOLD_FX',key,type(exc).__name__,str(exc)[:200],flush=True)
        model_file=Path(r'C:\BG_VOICE_RU_MASTER\08_VOXCPM2_ALL_CHARACTERS\EXPERIMENTAL_MODELS\Shtorm-VoxCPM2-RU_481ce51')/'model.safetensors'
        # Attempt the same previously used environment, not pip and not another launcher.
        missing=False
        try:
            import importlib.util as ilu
            missing=any(ilu.find_spec(x) is None for x in ('torch','voxcpm','soundfile','numpy'))
        except Exception:missing=True
        generated=False
        if mode=='generate' and missing and os.environ.get('BGVOICE_SINGLEFILE_V68_ENV')!='1':
            venv=(home/'Downloads'/'BG_VOICE_RU_KELDORN_EMOTION_CLONING_PILOT_V1'/'BG_VOICE_RU_KELDORN_CLONE_PILOT'/'.venv'/'Scripts'/'python.exe')
            if venv.is_file():
                env=os.environ.copy();env['BGVOICE_SINGLEFILE_V68_ENV']='1'
                cmd=env.get('BGV_COMMAND') or ("import sys;p=sys.argv.pop(1);t=open(p,encoding='utf-8-sig').read();exec(compile(t.split(chr(10)+'#BGVOICE_PYTHON_START'+chr(10),1)[1],p,'exec'),{'__name__':'__main__','__file__':p})")
                print('USING_PREEXISTING_SHTORM_ENV:',venv,flush=True)
                return _sp.call([str(venv),'-u','-c',cmd,str(Path(__file__).resolve()),'--oh89888-retake'],env=env)
            else:
                notes.append('HOLD_EXISTING_VOXCMP2_ENV_NOT_FOUND; effects-only candidates preserved')
        elif mode=='generate' and missing:
            notes.append('HOLD_VOXCMP2_DEPENDENCIES_MISSING_IN_PREEXISTING_ENV')
        elif mode=='generate':
            try:
                import torch as torch
                import numpy as np
                import soundfile as sf
                from voxcpm import VoxCPM as VoxCPM
                with zipfile.ZipFile(report) as z:
                    model_tag=json.loads(z.read('STRESS_V60/SUMMARY.json').decode()).get('model_file_sha_from_V60')
                if model_tag!='5c61cb1e9090a852c0f282a6bdd1be31f0c79ad94849f6376f8e6ea312f8d3b1':
                    raise RuntimeError('MODEL_SOURCE_HASH_NOT_PINNED')
                if not model_file.is_file():raise RuntimeError('PINNED_SHTORM_MODEL_MISSING')
                # The V60 production report previously hashed this exact local file once.
                # Reject any changed file without pointlessly rehashing 4.58 GB on every run.
                ms=model_file.stat()
                if ms.st_size!=4580080624 or ms.st_mtime_ns!=1794637435152839100:
                    raise RuntimeError('LOCAL_SHTORM_MODEL_SIZE_OR_MTIME_CHANGED_SINCE_VERIFIED_V60')
                if not torch.cuda.is_available():raise RuntimeError('CUDA_NOT_AVAILABLE')
                free,total=torch.cuda.mem_get_info(0)
                if free<3*1024**3:raise RuntimeError('INSUFFICIENT_FREE_VRAM_CLOSE_GAME')
                targets=[]
                for key,job in tasks.items():
                    fp=sha(json.dumps({'schema':schema,'id':sid,'key':key,'text':job['text'],'cfg':job['cfg'],'seed':job['seed'],'reference_sha256':expected[enname],'model_sha256':model_tag,'steps':12},sort_keys=True,ensure_ascii=False).encode())
                    cached=load_cached(key,fp)
                    if cached is not None:
                        collection[key]=cached
                        jobs.append({'candidate':key,'status':'REUSED_VERIFIED','sha256':sha(cached),'type':'NEW_SHTORM_ACTING_EXPERIMENT','text':job['text']})
                    else:targets.append((key,job,fp))
                if targets:
                    print('LOAD_EXISTING_SHTORM_ONCE:',model_file.parent,flush=True)
                    model=VoxCPM.from_pretrained(str(model_file.parent),device='cuda:0',optimize=False,load_denoiser=False)
                    with _tmp.TemporaryDirectory(prefix='bgvoice_v68_ref_') as td:
                        refpath=Path(td)/'OH89888_EN.wav';refpath.write_bytes(ref)
                        if sha(refpath.read_bytes())!=expected[enname]:raise RuntimeError('TEMPERATURE_REFERENCE_HASH_CHANGED')
                        for key,job,fp in targets:
                            try:
                                torch.manual_seed(job['seed'])
                                with torch.inference_mode():
                                    generated_audio=model.generate(text=job['text'],reference_wav_path=str(refpath),cfg_value=job['cfg'],inference_timesteps=12,normalize=False,denoise=False)
                                rate=int(model.tts_model.sample_rate)
                                arr=np.asarray(generated_audio,dtype=np.float32).reshape(-1)
                                if rate!=48000 or len(arr)<rate//3 or len(arr)>rate*20 or not np.isfinite(arr).all() or float(np.sqrt(np.mean(arr.astype(np.float64)**2)))<0.001:
                                    raise RuntimeError('GENERATED_AUDIO_FAILED_QUALITY_FLOOR')
                                peak=float(np.max(np.abs(arr)))
                                if peak>.96:arr=arr*(.96/peak)
                                with _io.BytesIO() as b:
                                    sf.write(b,arr,rate,format='WAV',subtype='PCM_16');wav=b.getvalue()
                                open_wav(wav)
                                store_cached(key,fp,wav,{'source_sha256':expected[enname],'cfg':job['cfg'],'seed':job['seed'],'text':job['text']})
                                collection[key]=wav
                                jobs.append({'candidate':key,'status':'GENERATED','sha256':sha(wav),'type':'NEW_SHTORM_ACTING_EXPERIMENT','text':job['text']})
                                print('CREATED_ACTING_CANDIDATE',key,round(len(arr)/rate,3),'seconds',flush=True)
                            except Exception as exc:
                                jobs.append({'candidate':key,'status':'HOLD','error':type(exc).__name__+': '+str(exc)[:250]})
                                print('CONTINUE_AFTER_ACTING_ERROR',key,str(exc)[:200],flush=True)
                            finally:
                                try:torch.cuda.empty_cache()
                                except Exception:pass
                generated=True
            except Exception as exc:
                notes.append('HOLD_ACTING_SYNTH:'+type(exc).__name__+': '+str(exc)[:300])
                print(notes[-1],flush=True)
        # FX derivatives depend only on verified new dry WAVs, not on unavailable model.
        for name,typ in [('DRY_A','FX_A'),('DRY_B','FX_B')]:
            if name not in collection:continue
            key=name+'_'+typ
            fp=sha(json.dumps({'schema':schema,'base_sha':sha(collection[name]),'fx':typ},sort_keys=True).encode())
            try:
                wav=load_cached(key,fp)
                reused=wav is not None
                if wav is None:
                    wav=make_fx(collection[name],typ)
                    store_cached(key,fp,wav,{'source_sha256':sha(collection[name]),'fx':typ})
                collection[key]=wav
                jobs.append({'candidate':key,'status':'REUSED_VERIFIED' if reused else 'GENERATED','sha256':sha(wav),'type':'NEW_SHTORM_WITH_FX_EXPERIMENT'})
            except Exception as exc:
                jobs.append({'candidate':key,'status':'HOLD','error':str(exc)[:300]})
                print('CONTINUE_AFTER_EFFECT_ERROR',key,str(exc)[:200],flush=True)
        summary={'schema':schema,'utc':stamp(),'source_report_sha256':sha(report.read_bytes()),'approved_manual_locks':manual,'text_immutable':text_original,'original_en_sha256':expected[enname],'original_v65_sha256':expected[v65name],'output_install_ready':False,'style_control_guaranteed':False,'echo_type_proven':False,'model_generation_available':generated,'jobs':jobs,'notes':notes,'candidate_names':list(collection)}
        audio=[('EN — оригинальный актёр и эффекты',ref),('V60 — отклонён пользователем',old60),('V65 — отклонён пользователем',old65)]
        audio.extend((name+' — эксперимент',b) for name,b in collection.items())
        docs={'V68_OH89888/MANIFEST.json':json.dumps(summary,ensure_ascii=False,indent=2).encode('utf-8'),'V68_OH89888/HUMAN_LOCKS.json':json.dumps(manual,ensure_ascii=False,indent=2).encode('utf-8'),'V68_OH89888/OPEN_REVIEW.html':embed_page(audio,summary),'V68_OH89888/READ_ME_FIRST.txt':('EXPERIMENTAL OH89888. Use OPEN_REVIEW.html offline for English vs V60 vs V65 vs new Shtorm retakes, FX_A and FX_B. Effects are hypotheses, not verified reconstruction. No game installation. No change to approved OH85856 or OH80404.').encode('utf-8')}
        for k,data in collection.items():docs['V68_OH89888/CANDIDATES/OH89888__'+k+'.wav']=data
        # Re-runs must never discard an earlier, richer V68 report or create endless backups.
        if 'V68_OH89888/MANIFEST.json' in original:
            oldmeta=json.loads(original['V68_OH89888/MANIFEST.json'].decode('utf-8'))
            if oldmeta.get('schema')!=schema:
                raise RuntimeError('FOREIGN_EXISTING_V68_REPORT_SCHEMA')
            prior_names=set(oldmeta.get('candidate_names',[]))
            if set(collection).issubset(prior_names):
                intact=True
                for key,data in collection.items():
                    filename='V68_OH89888/CANDIDATES/OH89888__'+key+'.wav'
                    if filename not in original or sha(original[filename])!=sha(data):
                        intact=False;break
                if intact:
                    print('V68_IDEMPOTENT_REUSE: all current candidates present in verified original report',flush=True)
                    print('REPORT:',report,flush=True)
                    return 0
        # Always retain other lanes of the one existing production ZIP, atomically.
        root.mkdir(parents=True,exist_ok=True)
        backup=root/'BACKUPS'/('BEFORE_V68_'+sha(report.read_bytes())[:16]+'.zip')
        if not backup.is_file():
            backup.parent.mkdir(parents=True,exist_ok=True)
            backup_tmp=backup.with_suffix('.zip.pending')
            try:
                with report.open('rb') as src, backup_tmp.open('xb') as dst:_shutil.copyfileobj(src,dst)
                if sha(backup_tmp.read_bytes())!=sha(report.read_bytes()):raise RuntimeError('BACKUP_HASH_MISMATCH')
                os.replace(backup_tmp,backup)
            finally:
                if backup_tmp.exists():backup_tmp.unlink()
        destination=report.with_suffix('.zip.v68.pending')
        if destination.exists():raise RuntimeError('LEFTOVER_TEMP_REPORT_REFUSE_OVERWRITE')
        try:
            with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
                for name,data in original.items():
                    if not name.startswith('V68_OH89888/'):z.writestr(name,data)
                for name,data in docs.items():z.writestr(name,data)
            with zipfile.ZipFile(destination) as z:
                if z.testzip() is not None:raise RuntimeError('NEW_REPORT_ZIP_CRC_FAILED')
                if sha(z.read('STRESS_V60/NEW_CANDIDATES/OH85856__SHTORM_STRESS_SINGLEFILE.wav'))!=expected['STRESS_V60/NEW_CANDIDATES/OH85856__SHTORM_STRESS_SINGLEFILE.wav']:
                    raise RuntimeError('PREVIOUS_USER_APPROVED_V65_CHANGED')
                if sha(z.read('STRESS_V60/OLD_V60/OH80404_V60.wav'))!=expected['STRESS_V60/OLD_V60/OH80404_V60.wav']:
                    raise RuntimeError('PREVIOUS_USER_APPROVED_V60_CHANGED')
            os.replace(destination,report)
        finally:
            if destination.exists():destination.unlink()
        print('V68_COMPLETE: report and backup verified, approved user WAV untouched',flush=True)
        print('NEW_CANDIDATES:',len(collection),'GENERATED_SHTORM:',generated,'NOTES:',notes,flush=True)
        print('REPORT:',report,flush=True)
        return 0 if collection else 2
    except Exception as exc:
        print('V68_SAFE_HOLD:',type(exc).__name__,str(exc)[:500],flush=True)
        print('NO_GAME_WAV_CHANGES; existing report preserved unless verified atomic rewrite completed',flush=True)
        return 2
# BGVOICE_V68_OH89888_ACTING_AND_FX_END

# BGVOICE ELIOT R4 READONLY WINDOWS MODEL/STRESS PROBE - source from tested V68 only.
# Invoked only by --eliot-r4-preflight; does not start cached remote cores, TTS, GPU, or game.
def _eliot_r4_preflight(*, updater_path=None, report_path=None, model_root=None, python_exe=None,
                        full_model_hash=False):
    import ast
    import hashlib
    import io
    import json
    import os
    import shutil
    import sys
    import tempfile
    import time
    import zipfile
    from pathlib import Path

    updater = Path(updater_path) if updater_path is not None else Path(__file__).resolve()
    home = Path.home()
    report = Path(report_path) if report_path is not None else home / 'Documents' / 'BG_VOICE_RU' / 'FULL_PRODUCTION' / 'SEND_TO_CHATGPT_BG_VOICE_RU.zip'
    model = Path(model_root) if model_root is not None else Path('C:/BG_VOICE_RU_MASTER/08_VOXCPM2_ALL_CHARACTERS/EXPERIMENTAL_MODELS/Shtorm-VoxCPM2-RU_481ce51')
    python = Path(python_exe) if python_exe is not None else home / 'Downloads' / 'BG_VOICE_RU_KELDORN_EMOTION_CLONING_PILOT_V1' / 'BG_VOICE_RU_KELDORN_CLONE_PILOT' / '.venv' / 'Scripts' / 'python.exe'
    outname = 'DIAGNOSTICS/ELIOT_R4_WINDOWS_PREFLIGHT.json'

    def sha(path):
        h = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda:f.read(1024*1024), b''):
                h.update(chunk)
        return h.hexdigest()
    def file_entry(p, *, hash_limit=2_000_000):
        if not p.is_file() or p.is_symlink():
            return {'status':'HOLD_MISSING_OR_SYMLINK'}
        try:
            st=p.stat()
            d={'status':'FILE_PRESENT', 'bytes':st.st_size}
            if st.st_size <= hash_limit: d['sha256']=sha(p)
            else: d['sha256']='NOT_HASHED_SIZE_LIMIT'
            return d
        except OSError as e:
            return {'status':'HOLD_READ_ERROR','reason':type(e).__name__}
    def safe_name(n):
        if not isinstance(n,str) or not n or n.startswith(('/', '\\')) or '\\' in n or ':' in n or n.startswith('//'):
            raise ValueError('INVALID_ZIP_ENTRY_NAME')
        if any(v in ('','.','..') for v in n.rstrip('/').split('/')):
            raise ValueError('INVALID_ZIP_ENTRY_PART')
        return n
    result={
        'schema':'BGVOICE_ELIOT_R4_WINDOWS_PREFLIGHT_1',
        'windows_host':os.name=='nt',
        'read_only_game_wavs_models':True,
        'game_write':False,'tts_generated':False,'gpu_inference':False,
        'movie_core_literary_gate':'MUST_REMAIN_HOLD',
        'style_control_runtime_verified':False,
        'stress_plus_mark_runtime_verified':False,
        'updater':file_entry(updater,hash_limit=150_000),
        'local_python_exe':file_entry(python,hash_limit=0),
        'model_root_status':'HOLD_NOT_CHECKED','model_files':[],
        'voxcpm_source_status':'HOLD_NOT_CHECKED','voxcpm_modules':[],
        'generate_signatures_static':[],'report_preflight':{},
    }
    # Enumerate only the intended Shtorm bundle. Never import model/torch or touch CUDA.
    if model.is_dir() and not model.is_symlink():
        try:
            found=[]
            for p in sorted(model.rglob('*')):
                if p.is_symlink(): raise ValueError('MODEL_SYMLINK_HOLD')
                if p.is_file():
                    if len(found)>=150: raise ValueError('MODEL_TOO_MANY_FILES_HOLD')
                    rel=p.relative_to(model).as_posix();safe_name(rel)
                    entry={'name':rel,'bytes':p.stat().st_size}
                    if p.stat().st_size<=20_000_000 or (full_model_hash and p.stat().st_size<=6_000_000_000):
                        entry['sha256']=sha(p)
                    else: entry['sha256']='NOT_HASHED_BUNDLE_INVENTORY_ONLY'
                    found.append(entry)
            result['model_files']=found
            result['model_root_status']='INVENTORY_ONLY_FULL_HASHES' if full_model_hash else 'INVENTORY_ONLY_NO_LARGE_WEIGHT_HASH'
        except (ValueError,OSError) as e:
            result['model_root_status']='HOLD_MODEL_INVENTORY_'+type(e).__name__
            result['model_inventory_error']=str(e)[:180]
    else:
        result['model_root_status']='HOLD_MODEL_ROOT_MISSING_OR_LINK'
    # Parse Python sources only; do not import VoxCPM, transformers, torch, or user models.
    site = python.parent.parent/'Lib'/'site-packages'/'voxcpm'
    if site.is_dir() and not site.is_symlink():
        try:
            modules=[];signatures=[]
            for p in sorted(site.rglob('*.py')):
                if p.is_symlink():raise ValueError('VOXCPM_SYMLINK_HOLD')
                if len(modules)>=100:raise ValueError('VOXCPM_MODULE_LIMIT_HOLD')
                raw=p.read_bytes()
                if len(raw)>2_000_000:raise ValueError('VOXCPM_LARGE_PY_HOLD')
                rel=p.relative_to(site).as_posix();safe_name(rel)
                modules.append({'relative_name':rel,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
                tree=ast.parse(raw.decode('utf-8-sig'),filename=rel)
                for node in ast.walk(tree):
                    if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name in ('generate','generate_stream'):
                        args=[a.arg for a in node.args.posonlyargs+node.args.args+node.args.kwonlyargs]
                        signatures.append({'module':rel,'name':node.name,'arguments':args,'has_kwargs':node.args.kwarg is not None})
            result['voxcpm_modules']=modules
            result['generate_signatures_static']=signatures[:30]
            result['voxcpm_source_status']='STATIC_AST_SCANNED_NOT_RUNTIME_VERIFIED'
        except (OSError,UnicodeError,SyntaxError,ValueError) as e:
            result['voxcpm_source_status']='HOLD_VOXCPM_SOURCE_'+type(e).__name__
            result['voxcpm_source_error']=str(e)[:180]
    else:
        result['voxcpm_source_status']='HOLD_VOXCPM_NOT_FOUND_IN_EXPECTED_VENV'
    # Never invent a model PASS from file lists or a Python AST signature.
    if not report.is_file() or report.is_symlink() or report.name!='SEND_TO_CHATGPT_BG_VOICE_RU.zip':
        print('ELIOT_R4_HOLD: standard one-report ZIP missing/symlink. No changes.',flush=True)
        return 2
    lock=report.with_name(report.name+'.eliot_r4_lock')
    fd=None;temp=None
    try:
        fd=os.open(str(lock),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        os.write(fd,(str(os.getpid())+'\n').encode('ascii'))
        os.close(fd);fd=None
    except FileExistsError:
        print('ELIOT_R4_HOLD: another preflight owns report lock. No changes.',flush=True)
        return 3
    try:
        before=sha(report)
        with zipfile.ZipFile(report,'r') as source:
            metas=source.infolist()
            if len(metas)>25000 or len(metas)!=len({m.filename for m in metas}):
                raise ValueError('REPORT_DUPLICATE_OR_TOO_MANY_ENTRIES')
            if sum(m.file_size for m in metas)>600*1024*1024:
                raise ValueError('REPORT_TOO_LARGE_UNCOMPRESSED_HOLD')
            for m in metas: safe_name(m.filename)
            if source.testzip() is not None:raise ValueError('REPORT_BAD_CRC_HOLD')
            # Stable semantic fingerprint excludes our own diagnostic entry, making reruns idempotent.
            others=[(m.filename,m.file_size,m.CRC) for m in metas if m.filename!=outname]
            semantic_sha=hashlib.sha256(json.dumps(sorted(others),ensure_ascii=False,separators=(',',':')).encode('utf-8')).hexdigest()
            result['report_preflight']={'status':'CRC_PASS','original_members':len(others),'semantic_sha256':semantic_sha}
            result['status']=('READONLY_INVENTORY_COLLECTED_TTS_STILL_HOLD' if
                              result['model_root_status'].startswith('INVENTORY') and
                              result['voxcpm_source_status'].startswith('STATIC_AST') else
                              'READONLY_INVENTORY_INCOMPLETE_TTS_HOLD')
            blob=json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2).encode('utf-8')
            if outname in source.namelist() and source.read(outname)==blob:
                print('ELIOT_R4_PREFLIGHT_CURRENT: same report already present, no rewrite.',flush=True)
                return 0
            tempfile_handle,temp=tempfile.mkstemp(prefix='.eliot_r4_',suffix='.pending',dir=str(report.parent))
            os.close(tempfile_handle)
            with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED,compresslevel=4,allowZip64=True) as target:
                for meta in metas:
                    if meta.filename==outname:continue
                    if meta.is_dir():target.writestr(meta,b'')
                    else:
                        with source.open(meta,'r') as inp,target.open(meta,'w',force_zip64=True) as dst:
                            shutil.copyfileobj(inp,dst,1024*1024)
                target.writestr(outname,blob)
        with zipfile.ZipFile(temp,'r') as updated:
            new_metas=updated.infolist()
            if len(new_metas)!=len({m.filename for m in new_metas}) or updated.testzip() is not None:
                raise ValueError('NEW_ZIP_VALIDATION_FAILED_HOLD')
        if sha(report)!=before:
            raise ValueError('REPORT_CONCURRENT_MODIFICATION_HOLD')
        with open(temp,'rb') as tmp_r:os.fsync(tmp_r.fileno())
        os.replace(temp,report);temp=None
        print('ELIOT_R4_PREFLIGHT_SAVED: '+str(report),flush=True)
        print('ELIOT_R4_RESULT: '+result['status'],flush=True)
        print('ELIOT_R4_NOTE: NO GPU, NO TTS, NO GAME, NO APPROVED WAV CHANGES.',flush=True)
        return 0
    except Exception as e:
        print('ELIOT_R4_HOLD: '+type(e).__name__+' '+str(e)[:180],flush=True)
        return 4
    finally:
        if fd is not None:os.close(fd)
        if temp is not None:
            try:os.unlink(temp)
            except OSError:pass
        try:os.unlink(lock)
        except OSError:pass

# END BGVOICE ELIOT R4 READONLY WINDOWS MODEL/STRESS PROBE

# ELIOT_R23_AB2_SOURCE_BEGIN
# A guarded preview-only route for the existing single BG_VOICE_UPDATE.cmd.
# Does not alter any original WAV, game file, approved voice, or movie master.
def _eliot_movie_ab2(mode):
    import hashlib as _h, io as _io, json as _json, math as _math
    import os as _os, shutil as _sh, subprocess as _sp, sys as _sys
    import tempfile as _tmp, zipfile as _zf, re as _re, wave as _wave
    from pathlib import Path as _P
    SCHEMA='ELIOT_R23_MOVIE_AB2_SOURCE_PINNED_V1'
    cases=[
      {'id':'SODCIN01_G10','text':'Другие шепчутся, будто она — ещё одно дитя Баала, решившее пойти по стопам Саревока.',
       'tts':'Другие шепчутся, будто она — ещё одно дитя Баала, решившее пойти по стопам Сарев+ока.',
       'en':'VIDEO/EN_REFERENCE_19/SODCIN01_G10_EN_DNR_ASR_WINDOW.wav','en_sha':'4a64b3faa2b87c6648b368f8ec98058e8c3cd96f29be19fea6295094965a10e8',
       'ref':'VIDEO/PILOTS/SODCIN01_G02__LOCKED_APPROVED.wav','ref_sha':'7c5b747e0ae3a2c778b5d6890d14a46bb493960d0e2398a2fc59170c9b4756ff',
       'old':'VIDEO/RU_CANDIDATES_10/WAV/SODCIN01_G10.wav','old_sha':'926806e8da3473ca26235584b82db09f1e15f3cdebe1d20cdecf643693e003c9',
       'retake':'VIDEO/RU_STRESS_RETAKES_7/WAV/SODCIN01_G10.wav','retake_sha':'b0993abb8c190bbdff9e39a46b6ac5a5e163a0b8225a1455006aa113599719ef'},
      {'id':'IWINTRO_G08','text':'Не прошло и нескольких недель, как из Хребта Мира хлынули полчища гоблинов. Над этим смертоносным потоком реяло знамя с чудовищными головами химеры.',
       'tts':'Не прошло и нескольких недель, как из Хребта Мира хлынули полчища гоблинов. Над этим смертоносным потоком реяло знамя с чудовищными голов+ами химеры.',
       'en':'VIDEO/EN_REFERENCE_19/IWINTRO_G08_EN_DNR_ASR_WINDOW.wav','en_sha':'1a982712abc4450b90343ba1dabe906f52291f58fd8b36e35f9453637f864143',
       'ref':'VIDEO/PILOTS/IWINTRO_G06__LOCKED_APPROVED.wav','ref_sha':'d240ed50fa1a2ba7b0138e570b786d12347c909c7ea7fa9ef17d825051dc813b',
       'old':'VIDEO/RU_CANDIDATES_10/WAV/IWINTRO_G08.wav','old_sha':'391623e82023c250596d5abd5ccca5575df832bddf9b88a1da5a49976ebeb74d',
       'retake':'VIDEO/RU_STRESS_RETAKES_7/WAV/IWINTRO_G08.wav','retake_sha':'e488bf7500147d6330c0bbcf75ae9adddb635676cd5932e6685c8ff65dbe6cea'}]
    settings=[('A','BASELINE',2.0,12),('B','REFINED_SAMPLING_NOT_STYLE_CONTROL',2.3,20)]
    def digest(b):return _h.sha256(b).hexdigest()
    def fmt(o):return _json.dumps(o,ensure_ascii=False,sort_keys=True,indent=2).encode('utf-8')
    for x in cases:
        if x['tts'].replace('+','')!=x['text'] or _re.search(r'\+(?![аеёиоуыэюя])',x['tts'],_re.I):
            raise RuntimeError('INVALID_STRESS_ANNOTATION_'+x['id'])
    if mode=='selftest':
        assert len(cases)==2 and len(settings)==2
        assert all(len(x[k])==64 for x in cases for k in ('en_sha','ref_sha','old_sha','retake_sha'))
        assert all(x['tts'].count('+')==1 for x in cases)
        print('ELIOT_R23_AB2_SELFTEST_PASS: 2 scenes, 8 immutable source SHA, 4 candidate slots; no files written',flush=True)
        return 0
    root=_P(_os.environ.get('BG_VOICE_FULL_PRODUCTION_ROOT') or (_P.home()/'Documents'/'BG_VOICE_RU'/'FULL_PRODUCTION'))
    report=root/'SEND_TO_CHATGPT_BG_VOICE_RU.zip'
    if not report.is_file():
        print('R23_HOLD: EXISTING_ONE_REPORT_MISSING',report,flush=True);return 2
    input_data={}
    try:
        with _zf.ZipFile(report) as z:
            infos=z.infolist();names=[m.filename for m in infos]
            if len(names)!=len(set(names)) or len(names)>5000:
                raise RuntimeError('REPORT_DUPLICATE_OR_TOO_MANY_MEMBERS')
            if any(n.startswith('/') or '\\' in n or '..' in n.split('/') for n in names):
                raise RuntimeError('REPORT_UNSAFE_MEMBER_NAME')
            if z.testzip() is not None:raise RuntimeError('REPORT_CRC_ERROR')
            for case in cases:
                for kind in ('en','ref','old','retake'):
                    n=case[kind]
                    blob=z.read(n)
                    if digest(blob)!=case[kind+'_sha']:raise RuntimeError('SHA_MISMATCH_'+case['id']+'_'+kind)
                    input_data[(case['id'],kind)]=blob
            if any(n.startswith('ELIOT_R23/') for n in names):
                print('R23_ALREADY_IN_ONE_REPORT: preserving existing result; no generation or overwrite',flush=True);return 0
    except Exception as exc:
        print('R23_SOURCE_HOLD:',type(exc).__name__,str(exc)[:210],flush=True);return 2
    print('R23_SOURCE_SHA_PASS: all 8 EN/OLD/RETAKE/VOICE_REF WAVs verified',flush=True)
    if mode=='preflight':
        print('R23_PREFLIGHT_PASS: source assets correct; model loading and acoustic stress NOT tested',flush=True)
        return 0
    if mode!='generate':raise ValueError('INVALID_AB2_MODE')
    # Re-enter the SAME existing one-file updater under the pre-existing Shtorm Python.
    try:
        import importlib.util as _ilu
        needs=any(_ilu.find_spec(k) is None for k in ('torch','numpy','soundfile','voxcpm'))
    except (ImportError,ValueError):needs=True
    if needs:
        if _os.environ.get('BGVOICE_ELIOT_R23_VENV')=='1':
            print('R23_HOLD: DEPENDENCIES_MISSING_IN_PREEXISTING_ENV',flush=True);return 2
        venv=(_P.home()/'Downloads'/'BG_VOICE_RU_KELDORN_EMOTION_CLONING_PILOT_V1'/
            'BG_VOICE_RU_KELDORN_CLONE_PILOT'/'.venv'/'Scripts'/'python.exe')
        if not venv.is_file():
            print('R23_HOLD: VERIFIED_PREEXISTING_SHTORM_ENV_NOT_FOUND',flush=True);return 2
        env=_os.environ.copy();env['BGVOICE_ELIOT_R23_VENV']='1'
        cmd=env.get('BGV_COMMAND') or ("import sys;p=sys.argv.pop(1);t=open(p,encoding='utf-8-sig').read();"
            "exec(compile(t.split(chr(10)+'#BGVOICE_PYTHON_START'+chr(10),1)[1],p,'exec'),"
            "{'__name__':'__main__','__file__':p})")
        print('R23_REENTER_SAME_CMD_EXISTING_ENV',flush=True)
        return _sp.call([str(venv),'-u','-c',cmd,str(_P(__file__).resolve()),'--eliot-movie-ab2'],env=env)
    model_root=_P(r'C:\BG_VOICE_RU_MASTER\08_VOXCPM2_ALL_CHARACTERS\EXPERIMENTAL_MODELS\Shtorm-VoxCPM2-RU_481ce51')
    model_file=model_root/'model.safetensors'
    if not model_file.is_file() or model_file.stat().st_size!=4580080624:
        print('R23_HOLD: EXACT_MODEL_FILE_NOT_FOUND_OR_WRONG_SIZE',flush=True);return 2
    expected_model='5c61cb1e9090a852c0f282a6bdd1be31f0c79ad94849f6376f8e6ea312f8d3b1'
    # Full model hash before execution. Never trust size/mtime alone.
    try:
        h=_h.sha256()
        with model_file.open('rb') as f:
            for blk in iter(lambda:f.read(4*1024*1024),b''):h.update(blk)
        if h.hexdigest()!=expected_model:raise RuntimeError('MODEL_FULL_SHA_MISMATCH')
        import torch as _torch,numpy as _np,soundfile as _sf
        from voxcpm import VoxCPM as _VoxCPM
        if not _torch.cuda.is_available():raise RuntimeError('CUDA_MISSING')
        free,_=_torch.cuda.mem_get_info(0)
        if free<3*1024**3:raise RuntimeError('LESS_THAN_3_GIB_FREE_CUDA_VRAM')
    except Exception as exc:
        print('R23_MODEL_HOLD:',type(exc).__name__,str(exc)[:180],flush=True);return 2
    cache=root/'ELIOT_R23_CANDIDATE_CACHE'
    cache.mkdir(parents=True,exist_ok=True)
    summary={'schema':SCHEMA,'status':'PREVIEW_ONLY_NOT_APPROVED','model_weight_sha256':expected_model,
        'model_provenance_signature_verified':False,
        'same_RU_voice_reference_for_A_and_B':True,
        'tts_text_editorial_status':'EXPERIMENTAL_NOT_FINAL_APPROVED',
        'english_asr_verification':'SODCIN01_G10_NOT_MANUALLY_VERIFIED',
        'style_control_verified':False,'generation_params_are_NOT_acting_style_control':True,
        'game_install_allowed':False,'old_WAV_overwritten':False,'results':[]}
    entries={}
    try:
        print('R23_LOADING_SHTORM_ONCE',flush=True)
        model=_VoxCPM.from_pretrained(str(model_root),device='cuda:0',optimize=False,load_denoiser=False)
    except Exception as exc:
        print('R23_MODEL_LOAD_HOLD:',type(exc).__name__,str(exc)[:180],flush=True);return 2
    for case in cases:
        sid=case['id']
        for label,description,cfg,steps in settings:
            item={'sound_id':sid,'variant':label,'description':description,'cfg_value':cfg,'steps':steps,
                  'tts_text':case['tts'],'voice_reference_sha256':case['ref_sha'],'state':'HOLD'}
            cachewav=cache/(sid+'_'+label+'.wav')
            cacheside=cache/(sid+'_'+label+'.json')
            fp=digest(fmt({'schema':SCHEMA,'id':sid,'variant':label,'text':case['tts'],
                'voice_sha':case['ref_sha'],'model_sha':expected_model,'cfg':cfg,'steps':steps}))
            try:
                if cachewav.exists() or cacheside.exists():
                    if not (cachewav.is_file() and cacheside.is_file()):
                        raise RuntimeError('PARTIAL_CACHE_CONFLICT_HOLD')
                    metadata=_json.loads(cacheside.read_text(encoding='utf-8'))
                    payload=cachewav.read_bytes()
                    if metadata.get('fingerprint')!=fp or digest(payload)!=metadata.get('sha256'):
                        raise RuntimeError('EXISTING_CACHE_NOT_MATCHING_SHA_HOLD')
                    member=f'ELIOT_R23/NEW/{sid}_{label}.wav'
                    entries[member]=payload
                    item.update({'state':'REUSED_SHA_VERIFIED_PREVIEW','member':member,
                                 'sha256':digest(payload),'seconds':metadata['seconds'],
                                 'sample_rate':metadata['sample_rate'],'seed':metadata['seed']})
                    print('R23_REUSED_CANDIDATE',sid,label,flush=True)
                    summary['results'].append(item)
                    continue
                with _tmp.TemporaryDirectory(prefix='eliot_r23_voice_') as td:
                    refp=_P(td)/(sid+'_RU_ANCHOR.wav');refp.write_bytes(input_data[(sid,'ref')])
                    seed=int(_h.sha256((SCHEMA+sid+label).encode()).hexdigest()[:8],16)
                    _torch.manual_seed(seed)
                    with _torch.inference_mode():
                        samples=model.generate(text=case['tts'],reference_wav_path=str(refp),
                            cfg_value=cfg,inference_timesteps=steps,normalize=False,denoise=False)
                rate=int(model.tts_model.sample_rate)
                audio=_np.asarray(samples,dtype='float32').reshape(-1)
                if (rate<8000 or rate>96000 or not _np.isfinite(audio).all() or
                    len(audio)<rate//3 or len(audio)>60*rate or
                    float(_np.sqrt(_np.mean(audio.astype('float64')**2)))<0.001):
                    raise RuntimeError('INVALID_PCM')
                peak=float(_np.max(_np.abs(audio)))
                if peak>0.98:audio=audio*(.98/peak)
                bio=_io.BytesIO();_sf.write(bio,audio,rate,format='WAV',subtype='PCM_16')
                payload=bio.getvalue();member=f'ELIOT_R23/NEW/{sid}_{label}.wav'
                metadata={'fingerprint':fp,'sha256':digest(payload),'seconds':round(len(audio)/rate,3),
                    'sample_rate':rate,'seed':seed,'preview_only':True}
                # Exclusive-create: never replace a previous candidate/sidecar.
                with cachewav.open('xb') as fout:
                    fout.write(payload);fout.flush();_os.fsync(fout.fileno())
                with cacheside.open('x',encoding='utf-8') as fout:
                    _json.dump(metadata,fout,ensure_ascii=False,indent=2)
                entries[member]=payload
                item.update({'state':'CREATED_NEEDS_HUMAN_QA','member':member,'sha256':digest(payload),
                             'seconds':round(len(audio)/rate,3),'sample_rate':rate,'seed':seed})
                print('R23_CREATED',sid,label,item['seconds'],'s',flush=True)
            except Exception as exc:
                item['error']=type(exc).__name__+': '+str(exc)[:150]
                print('R23_ITEM_HOLD_CONTINUING',sid,label,item['error'],flush=True)
            finally:
                try:_torch.cuda.empty_cache()
                except Exception:pass
            summary['results'].append(item)
    finished=sum(x['state'] in ('CREATED_NEEDS_HUMAN_QA','REUSED_SHA_VERIFIED_PREVIEW')
                 for x in summary['results'])
    if finished!=4:
        print('R23_PARTIAL_HOLD:',finished,'of 4 candidates cached; rerun SAME CMD to resume. Main ZIP untouched.',flush=True)
        return 2
    entries['ELIOT_R23/SUMMARY.json']=fmt(summary)
    entries['ELIOT_R23/README_RU.txt']=('ПРОБНЫЕ 2x2: SODCIN01_G10, IWINTRO_G08.\n'
        'Сравни с прежними RU_CANDIDATES_10 и RU_STRESS_RETAKES_7.\n'
        'A: cfg 2.0/12; B: cfg 2.3/20. B НЕ означает доказанный Style Control.\n'
        'Все файлы -- только кандидаты; не устанавливать в игру.\n').encode('utf-8')
    # Preserve every original report member byte-for-byte, refusing any existing R23 names.
    # Re-check source report hash immediately before atomic replacement. Other historical
    # writers may not share our mutex: user must not run a concurrent updater.
    source_hash=_h.sha256()
    with report.open('rb') as f:
        for blk in iter(lambda:f.read(2*1024*1024),b''):source_hash.update(blk)
    with _tmp.NamedTemporaryFile(prefix='ELIOT_R23_',suffix='.pending',dir=str(root),delete=False) as nf:
        tmpname=_P(nf.name)
    try:
        with _zf.ZipFile(report) as existing,_zf.ZipFile(tmpname,'w',_zf.ZIP_DEFLATED,compresslevel=5,allowZip64=True) as new:
            if existing.testzip() is not None:raise RuntimeError('REPORT_CHANGED_OR_CRC_FAIL')
            for meta in existing.infolist():
                if meta.filename.startswith('ELIOT_R23/'):
                    raise RuntimeError('R23_ALREADY_EXISTS_NO_OVERWRITE')
                with existing.open(meta) as src,new.open(meta,'w',force_zip64=True) as dst:
                    _sh.copyfileobj(src,dst,1024*1024)
            for name,data in sorted(entries.items()):new.writestr(name,data)
        with _zf.ZipFile(tmpname) as done:
            if done.testzip() is not None:raise RuntimeError('RESULT_CRC_FAILED')
            names=done.namelist()
            if len(names)!=len(set(names)):raise RuntimeError('RESULT_DUPLICATE_MEMBER')
        compare=_h.sha256()
        with report.open('rb') as f:
            for blk in iter(lambda:f.read(2*1024*1024),b''):compare.update(blk)
        if compare.digest()!=source_hash.digest():raise RuntimeError('CONCURRENT_REPORT_CHANGED_HOLD')
        _os.replace(tmpname,report)
        print('R23_ONE_REPORT_UPDATED',report,flush=True)
    except Exception as exc:
        print('R23_REPORT_HOLD:',type(exc).__name__,str(exc)[:180],flush=True)
        return 2
    finally:
        if tmpname.exists():tmpname.unlink()
    made=sum(x['state'] in ('CREATED_NEEDS_HUMAN_QA','REUSED_SHA_VERIFIED_PREVIEW') for x in summary['results'])
    print('R23_AB2_COMPLETED',made,'of 4 WAVs, original report assets preserved',flush=True)
    return 0 if made==4 else 2
# ELIOT_R23_AB2_SOURCE_END

if __name__=='__main__':
    try:
        if '--eliot-movie-ab2-selftest' in sys.argv:
            sys.exit(_eliot_movie_ab2('selftest'))
        if '--eliot-movie-ab2-preflight' in sys.argv:
            sys.exit(_eliot_movie_ab2('preflight'))
        if '--eliot-movie-ab2' in sys.argv:
            sys.exit(_eliot_movie_ab2('generate'))
        if '--eliot-r4-preflight' in sys.argv:
            sys.exit(_eliot_r4_preflight(full_model_hash='--eliot-r4-full-model-hash' in sys.argv))
        if '--oh89888-retake-selftest' in sys.argv:
            sys.exit(_v68_oh89888('selftest'))
        if '--oh89888-retake-preflight' in sys.argv:
            sys.exit(_v68_oh89888('preflight'))
        if '--oh89888-retake' in sys.argv:
            sys.exit(_v68_oh89888('generate'))
        if '--oh89888-fx-only' in sys.argv:
            sys.exit(_v68_oh89888('fx-only'))
        if '--shtorm-stress-selftest' in sys.argv:
            sys.exit(_singlefile_shtorm_v60('selftest'))
        if '--shtorm-stress-v60-preflight' in sys.argv:
            sys.exit(_singlefile_shtorm_v60('preflight'))
        if '--shtorm-stress-v60' in sys.argv:
            sys.exit(_singlefile_shtorm_v60('generate'))
        if not _boot_cached_or_fallback():sys.exit(main())
    except KeyboardInterrupt:
        print('INTERRUPTED: progress saved. Rerun same file to resume.',file=sys.stderr)
        sys.exit(130)
    except Exception:
        msg=traceback.format_exc()
        print(msg,file=sys.stderr)
        try:
            import argparse as _argparse
            # Always report failures next to the actual existing launcher.
            work=Path(__file__).resolve().parent
            if work.is_dir():
                pending=work/(REPORT+'.pending')
                with zipfile.ZipFile(pending,'w',zipfile.ZIP_DEFLATED) as z:
                    z.writestr('ERROR.txt',msg)
                os.replace(pending,work/REPORT)
        except Exception as exc:
            print('Could not save error ZIP:',repr(exc),file=sys.stderr)
        sys.exit(1)
