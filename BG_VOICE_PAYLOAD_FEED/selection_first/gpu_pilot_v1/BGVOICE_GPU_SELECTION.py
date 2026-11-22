# -*- coding: utf-8 -*-
"""BG Voice RU: independent WavLM pilot gated by historic Stable/Per_line human picks.

READ-ONLY: All English, Russian and EET source files. This standalone script only
writes its own separate user Documents report directory. No synthesis or game install.
The sound-ID/character registry and 20 earlier human choices are bundled, not inferred.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import math
import os
import sqlite3
import sys
import tempfile
import time
import traceback
import wave
from collections import Counter, defaultdict
from pathlib import Path, PureWindowsPath

PROJECT = 'BGVOICE_WAVLM_SELECTION_FIRST_PILOT_V1'
MODEL_ID = 'microsoft/wavlm-base-plus-sv'
MODEL_REVISION = 'feb593a6c23c1cc3d9510425c29b0a14d2b07b1e'
MASTER_WIN = PureWindowsPath(r'C:\BG_VOICE_RU_MASTER\08_VOXCPM2_ALL_CHARACTERS\RUSSIAN_WAV_TWO_VERSIONS')
MASTER_DIR = Path(str(MASTER_WIN))
ROOT = Path(__file__).resolve().parent
DATA = ROOT/'DATA'/'SOURCE_7206.csv'
HUMAN = ROOT/'DATA'/'RETROSPECTIVE_HUMAN_COMPARISON.csv'
LOCKS = ROOT/'DATA'/'HUMAN_LOCKS_58_WINDOWS.csv'
OUT = Path.home()/'Documents'/'BG_VOICE_RU'/'VOICE_SELECTION_GPU'
OUT.mkdir(parents=True, exist_ok=True)


def sha256(raw): return hashlib.sha256(raw).hexdigest()

def file_sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for x in iter(lambda:f.read(1024*1024),b''): h.update(x)
    return h.hexdigest()

def atomic(p,data):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=p.parent,prefix='._bgvoice_',suffix='.tmp')
    try:
        with os.fdopen(fd,'wb') as f:
            f.write(data); f.flush();os.fsync(f.fileno())
        os.replace(tmp,p)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def json_bytes(obj):return (json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode('utf-8')

def load_csv(p):
    with p.open('r',encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def csv_bytes(rows,fields):
    buf=io.StringIO(newline='')
    w=csv.DictWriter(buf,fieldnames=fields,lineterminator='\r\n',extrasaction='ignore');w.writeheader();w.writerows(rows)
    return ('\ufeff'+buf.getvalue()).encode('utf-8')


def check_registry():
    r=load_csv(DATA);h=load_csv(HUMAN)
    if len(r)!=7206 or len(set(x['sound_id'] for x in r))!=7206:raise ValueError('REGISTRY_NOT_7206_UNIQUE')
    if len(h)!=20 or Counter(x['human_preference'] for x in h)!={'PER_LINE':13,'STABLE':7}:
        raise ValueError('RETROSPECTIVE_HUMAN_20_INCONSISTENT')
    byid={x['sound_id']:x for x in r}
    locked=load_csv(LOCKS)
    if len(locked)!=58 or len({x['sound_id'] for x in locked})!=58:raise ValueError('HISTORIC_LOCKS_NOT_58_UNIQUE')
    for x in locked:
        row=byid.get(x['sound_id'])
        if not row or x['human_lock']!='YES' or row['character']!=x['character']:
            raise ValueError('MISSING_HISTORIC_LOCK_'+x['sound_id'])
        if x['stable_sha256']!=row['stable_sha256'] or x['per_line_sha256']!=row['per_line_sha256']:
            raise ValueError('HISTORIC_LOCK_SOURCE_SHA_CHANGED_'+x['sound_id'])
    for x in r:
        for mode in ('stable','per_line'):
            v=x[mode+'_sha256']
            if len(v)!=64 or not all(z in '0123456789abcdef' for z in v):raise ValueError('MISSING_OR_BAD_EXPECTED_SHA_'+x['sound_id'])
    for x in h:
        y=byid.get(x['sound_id'])
        if not y or y['character']!=x['character']:raise ValueError('HUMAN_MISMATCH_'+x['sound_id'])
    return r,h,byid


def safe_source(raw):
    source=PureWindowsPath(raw)
    if '..' in source.parts or tuple(s.lower() for s in source.parts[:len(MASTER_WIN.parts)])!=tuple(s.lower() for s in MASTER_WIN.parts):
        raise ValueError('NOT_MASTER_RU_SOURCE')
    sub=source.parts[len(MASTER_WIN.parts):]
    if not sub:raise ValueError('NO_RU_RELATIVE_PATH')
    p=MASTER_DIR.joinpath(*sub)
    realroot=MASTER_DIR.resolve(strict=False)
    realp=p.resolve(strict=False)
    if os.path.commonpath((str(realroot),str(realp)))!=str(realroot):raise ValueError('PATH_ESCAPES_MASTER')
    return p


def read_pcm_bytes(raw,max_frames=48000*120):
    import numpy as np
    from scipy.signal import resample_poly
    with wave.open(io.BytesIO(raw),'rb') as w:
        ch=w.getnchannels(); fs=w.getframerate(); sw=w.getsampwidth(); n=w.getnframes()
        if ch<1 or ch>2 or sw!=2 or fs<8000 or fs>96000 or n<1600 or n>max_frames*2:
            raise ValueError('INVALID_PCM16_OR_AUDIO_DURATION')
        samples=np.frombuffer(w.readframes(n),dtype='<i2').astype(np.float32)/32768.
    if ch>1:samples=samples.reshape(-1,ch).mean(axis=1)
    if fs!=16000:
        g=math.gcd(fs,16000)
        samples=resample_poly(samples,16000//g,fs//g).astype(np.float32,copy=False)
    if len(samples)<int(.7*16000):raise ValueError('TOO_SHORT_FOR_SPEAKER_MODEL')
    if not np.isfinite(samples).all() or float(np.sqrt(np.mean(samples*samples)))<0.0004:
        raise ValueError('SILENCE_OR_INVALID_AUDIO')
    # Silence trimming is conservative; relative threshold avoids over-trimming whispers.
    win=1600
    frame_count=len(samples)//win
    energy=np.sqrt(np.mean(samples[:frame_count*win].reshape(-1,win)**2,axis=1)+1e-12)
    threshold=max(0.0009, min(float(np.quantile(energy,.80))*.10,.007))
    active=np.flatnonzero(energy>threshold)
    if len(active)>1:
        start=max(0,(int(active[0])-1)*win);end=min(len(samples),(int(active[-1])+2)*win)
        samples=samples[start:end]
    # Multiple source spans are pooled later for long utterances; limit model VRAM.
    maxsamples=16000*9
    if len(samples)>maxsamples:
        # Clip centered speech; long dialogue variants also receive RISK_LONG_LINE.
        start=(len(samples)-maxsamples)//2
        samples=samples[start:start+maxsamples]
    return samples


class Cache:
    def __init__(self,path):
        self.db=sqlite3.connect(path)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('CREATE TABLE IF NOT EXISTS embeddings (key TEXT PRIMARY KEY, sha TEXT, size INT, mtime_ns INT, dims INT, vector BLOB)')
        self.db.execute('CREATE TABLE IF NOT EXISTS errors (key TEXT PRIMARY KEY, reason TEXT, date INT)')
        self.db.commit()

    def get(self,key,path,expected=None):
        import numpy as np
        try:
            st=path.stat()
            r=self.db.execute('SELECT sha,size,mtime_ns,dims,vector FROM embeddings WHERE key=?',(key,)).fetchone()
            if r and (not expected or r[0]==expected) and r[1]==st.st_size and r[2]==st.st_mtime_ns:
                v=np.frombuffer(r[4],dtype=np.float32)
                if v.size==r[3] and 0<v.size<10000 and np.isfinite(v).all():return v.copy()
        except OSError:pass
        return None

    def put(self,key,path,sha,vector):
        import numpy as np
        v=np.asarray(vector,dtype=np.float32).reshape(-1)
        if not np.isfinite(v).all():raise ValueError('NONFINITE_MODEL_EMBEDDING')
        st=path.stat()
        self.db.execute('INSERT OR REPLACE INTO embeddings VALUES (?,?,?,?,?,?)',(key,sha,st.st_size,st.st_mtime_ns,len(v),v.tobytes()))
        self.db.commit()

    def close(self):self.db.commit();self.db.close()


class Speaker:
    def __init__(self,device='cuda'):
        import torch
        from transformers import Wav2Vec2FeatureExtractor, WavLMForXVector
        if device=='cuda' and not torch.cuda.is_available():
            raise RuntimeError('CUDA_NOT_AVAILABLE_SAFE_STOP_NO_SILENT_CPU_HOURS')
        self.torch=torch
        self.device=torch.device(device)
        self.processor=Wav2Vec2FeatureExtractor.from_pretrained(MODEL_ID,revision=MODEL_REVISION,trust_remote_code=False)
        self.model=WavLMForXVector.from_pretrained(MODEL_ID,revision=MODEL_REVISION,trust_remote_code=False).to(self.device).eval()
        self.id=f'{MODEL_ID}@{MODEL_REVISION}:xvector:{self.device.type}'
        self.calls=0

    def __call__(self,pcm16):
        import numpy as np
        t=self.torch
        values=self.processor(pcm16,sampling_rate=16000,return_tensors='pt',padding=False)
        inputs={k:v.to(self.device) for k,v in values.items()}
        try:
            with t.inference_mode():
                x=self.model(**inputs).embeddings.detach().float().cpu().numpy()[0]
        except t.cuda.OutOfMemoryError:
            if self.device.type=='cuda':t.cuda.empty_cache()
            raise RuntimeError('MODEL_GPU_OOM_HOLD')
        denom=np.linalg.norm(x)
        if not np.isfinite(denom) or denom<1e-7:raise ValueError('INVALID_EMBEDDED_VECTOR')
        self.calls+=1
        return (x/denom).astype(np.float32)


def embed_audio(p,expected,cache,speaker,role):
    key=f'{speaker.id}|{role}|{str(p).casefold()}|{expected or "NO_EXPECTED"}'
    old=cache.get(key,p,expected)
    if old is not None:return old,'CACHE'
    if not p.is_file():raise FileNotFoundError(str(p))
    if p.stat().st_size>40*1024*1024:raise ValueError('FILE_TOO_LARGE_HOLD')
    raw=p.read_bytes()
    measured=sha256(raw)
    if expected and measured!=expected:raise ValueError('SHA_MISMATCH_SOURCE_HOLD')
    pcm=read_pcm_bytes(raw)
    v=speaker(pcm)
    cache.put(key,p,measured,v)
    return v,'GPU' if speaker.device.type=='cuda' else 'CPU'


def cos(a,b):
    import numpy as np
    if len(a)!=len(b):raise ValueError('DIMENSION_MISMATCH')
    return float(np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b)+1e-12))


def robust_mean(vectors):
    import numpy as np
    if not vectors:raise ValueError('NO_ENGLISH_REFERENCES')
    v=np.stack(vectors).astype('float32')
    if len(v)>=3:
        # Medoid reduces damage from one wrong EN source/actor.
        sim=v@v.T
        medoid=int(np.argmax(np.median(sim,axis=1)))
        if sum(float(z)>=.38 for z in sim[medoid])<3:raise ValueError('INCOHERENT_ENGLISH_REFERENCES_HOLD')
        keep=v[sim[medoid]>=.38]
    else:keep=v
    s=keep.mean(axis=0);norm=np.linalg.norm(s)
    if norm<1e-7:raise ValueError('DEGENERATE_ENGLISH_SPEAKER_REFERENCE')
    return s/norm, len(keep)


class ReferenceManager:
    def __init__(self,rows,out,cache,speaker,strict_game_extract=False):
        from V58_EN_RECOVERY import ENResolver
        self.resolver=ENResolver(out/'EN_CACHE',game_root=Path(r'C:\Games\BG_EET_FOXX_NEW'))
        self.groups=defaultdict(list)
        for r in rows:self.groups[r['character']].append(r)
        self.cache=cache;self.speaker=speaker;self.refs={};self.errors=[]
        self.allow_extract=strict_game_extract

    def source(self,sid):
        # Existing EN or exact-ID game extraction. NEVER use a Russian file as fallback.
        p=self.resolver.quick(sid)
        if not p and self.allow_extract and len(sid)<=8:
            x=self.resolver.resolve(sid)
            if x.get('ok'):
                p=Path(self.resolver._record[sid]['path'])
        return p

    def reference(self,character):
        if character in self.refs:return self.refs[character]
        es=[];paths=[];notes=[]
        misses=0;attempts=0
        # Diversity by sound ID; exact EN speaker identity is not independently attested.
        self.resolver._scan_loose()
        for r in sorted(self.groups[character],key=lambda x:(x['sound_id'] not in self.resolver._found,len(x['sound_id'])>8,x['sound_id'])):
            if len(es)>=5:break
            if attempts>=18 or misses>=13:break
            attempts+=1
            sid=r['sound_id']
            try:
                p=self.source(sid)
                if not p:
                    misses+=1
                    continue
                if 'RUSSIAN_WAV_TWO_VERSIONS' in str(p).upper():continue
                if p.stat().st_size<44 or p.stat().st_size>40*1024*1024:continue
                key=str(p.resolve()).casefold()
                if key in paths:continue
                paths.append(key)
                v,_=embed_audio(p,None,self.cache,self.speaker,'EN_REF')
                es.append(v)
            except Exception as e:
                misses+=1
                notes.append(f'{sid}:{type(e).__name__}')
        if len(es)<3:
            ans=(None,len(es),'NEED_3_TO_5_EN_SAME_CHARACTER_REFERENCES')
        else:
            try:
                centroid,n=robust_mean(es)
                ans=(centroid,n,'EN_LANGUAGE_AND_ACTOR_NOT_HUMAN_ATTESTED') if n>=3 else (None,n,'INCOHERENT_EN_REFERENCE_HOLD')
            except Exception as e:ans=(None,len(es),type(e).__name__)
        self.refs[character]=ans
        if notes:self.errors.append({'character':character,'issues':notes[:8]})
        return ans


def preference(row,cache,speaker,refmgr,threshold=.035):
    sid=row['sound_id'];ch=row['character']
    ref,refs,ref_note=refmgr.reference(ch)
    if ref is None:return {'sound_id':sid,'character':ch,'speaker_proposal':'HOLD','reason':ref_note,'en_reference_count':refs}
    scores={};methods={}
    for mode in ('stable','per_line'):
        try:
            p=safe_source(row[mode+'_readonly_path'])
            v,method=embed_audio(p,row[mode+'_sha256'],cache,speaker,'RU_'+mode.upper())
            scores[mode]=cos(v,ref);methods[mode]=method
        except Exception as e:
            note=str(e).replace('\n',' ')[:100]
            return {'sound_id':sid,'character':ch,'speaker_proposal':'HOLD','reason':'RU_AUDIO_'+mode.upper()+'_'+type(e).__name__+'_'+note, 'en_reference_count':refs}
    d=scores['stable']-scores['per_line']
    if not math.isfinite(d):return {'sound_id':sid,'character':ch,'speaker_proposal':'HOLD','reason':'NONFINITE_SPEAKER_SCORE','en_reference_count':refs}
    proposal='STABLE' if d>threshold else 'PER_LINE' if d < -threshold else 'HOLD'
    # ASR is evidence for completeness, NEVER a speaker-label override.
    try:
        ar=float(row['asr_stable'])-float(row['asr_per_line'])
    except (ValueError,TypeError): ar=0
    content_conflict=(proposal=='STABLE' and ar < -.12) or (proposal=='PER_LINE' and ar>.12)
    return {'sound_id':sid,'character':ch,'speaker_proposal':proposal,
            'speaker_stable':round(scores['stable'],6),'speaker_per_line':round(scores['per_line'],6),
            'independent_wavlm_margin_stable_minus_perline':round(d,6),'old_ecapa_margin':row['voice_margin_stable_minus_per_line'],
            'asr_margin_stable_minus_perline':round(ar,5),'content_conflict':content_conflict,
            'reason':'WAVLM_PROPOSAL_NEEDS_ACTING_AND_EN_VERIFICATION' if proposal!='HOLD' else 'WAVLM_TIE_UNCALIBRATED',
            'en_reference_count':refs,'en_reference_provenance':ref_note,
            'cache_modes':str(methods),'game_approved':'NO','acting_verified':'NO'}


def retrospective(rows,human,cache,speaker,refmgr):
    import numpy as np
    byid={r['sound_id']:r for r in rows}
    output=[]
    for i,item in enumerate(human,1):
        sid=item['sound_id']
        try:r=preference(byid[sid],cache,speaker,refmgr)
        except Exception as e:r={'sound_id':sid,'speaker_proposal':'HOLD','reason':type(e).__name__}
        r.update(human_choice=item['human_preference'],was_correct=(r.get('speaker_proposal')==item['human_preference']))
        output.append(r)
        print(f'PILOT {i}/{len(human)} {sid} human={item["human_preference"]} model={r["speaker_proposal"]} refs={r.get("en_reference_count",0)}',flush=True)
        if i%5==0:write_progress('PILOT_IN_PROGRESS',output,[])
    valid=[x for x in output if x.get('speaker_proposal') in ('STABLE','PER_LINE')]
    st=[x for x in valid if x['human_choice']=='STABLE'];pl=[x for x in valid if x['human_choice']=='PER_LINE']
    recall_st=sum(x['was_correct'] for x in st)/len(st) if st else None
    recall_pl=sum(x['was_correct'] for x in pl)/len(pl) if pl else None
    acc=sum(x['was_correct'] for x in valid)/len(valid) if valid else None
    balanced=(recall_st+recall_pl)/2 if recall_st is not None and recall_pl is not None else None
    # Explicitly compare against trivial always-PER_LINE baseline (13/20).
    passed=(len(valid)>=12 and len(st)>=4 and len(pl)>=6 and
            recall_st is not None and recall_st>=.60 and recall_pl is not None and recall_pl>=.70 and
            balanced is not None and balanced>=.70 and acc is not None and acc>.65)
    stats={'total':len(human),'evaluable':len(valid),'stable_evaluable':len(st),'per_line_evaluable':len(pl),
           'stable_recall':recall_st,'per_line_recall':recall_pl,'accuracy':acc,'balanced_accuracy':balanced,
           'always_per_line_baseline_accuracy':.65,'calibration_gate_pass':bool(passed),
           'rule':'FULL_RUN_ONLY_IF_12+_3_EN_REF_AND_RECALL_STABLE>=.60_PERLINE>=.70_BALANCED>=.70'}
    return output,stats


def write_progress(state,details,errors):
    atomic(OUT/'RUN_STATUS.json',json_bytes({'schema':PROJECT,'state':state,'updated_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
                                          'reviewed':len(details),'errors':len(errors),
                                          'master_originals_changed':False,'final_game_approvals':0}))

def write_outputs(pilot,stats,full,errors,state,device,reason=''):
    pilot_fields=['sound_id','human_choice','speaker_proposal','was_correct','character','en_reference_count','speaker_stable','speaker_per_line','independent_wavlm_margin_stable_minus_perline','reason','en_reference_provenance']
    full_fields=['sound_id','character','speaker_proposal','speaker_stable','speaker_per_line','independent_wavlm_margin_stable_minus_perline','old_ecapa_margin','asr_margin_stable_minus_perline','content_conflict','reason','en_reference_count','en_reference_provenance','human_lock','protected_human_choice','game_approved','acting_verified']
    status={'schema':PROJECT,'state':state,'reason':reason,'device':device,'model':MODEL_ID,'model_revision':MODEL_REVISION,'pilot':stats,'tested_sound_ids':len(full),
            'pilot_sound_ids':len(pilot),'master_wav_modified':False,'game_modified':False,
            'stress_checked':False,'emotion_model_run':False,'human_approvals_generated':0,'final_game_approvals':0,
            'note':'WavLM speaker signal only; not a validated actor/emotion metric; no release approvals.'}
    import zipfile
    paths={
        'PILOT_HUMAN_20_WAVLM.csv':csv_bytes(pilot,pilot_fields),
        'WAVLM_PROPOSALS_READONLY.csv':csv_bytes(full,full_fields),
        'RUN_STATUS.json':json_bytes(status),
        'EN_REFERENCE_ISSUES.json':json_bytes(errors)}
    for name,data in paths.items():atomic(OUT/name,data)
    fd,tmp=tempfile.mkstemp(dir=OUT,prefix='._bgvoice_report_',suffix='.zip.tmp')
    os.close(fd)
    try:
        with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for name,data in paths.items():z.writestr(name,data)
        with zipfile.ZipFile(tmp) as z:
            if z.testzip() or len(set(z.namelist()))!=len(z.namelist()):raise ValueError('OUTPUT_ZIP_BAD_CRC_OR_DUPLICATE')
        os.replace(tmp,OUT/'BG_VOICE_GPU_SELECTION_REPORT.zip')
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
    return status


def run(args,model_factory=Speaker):
    rows,human,byid=check_registry()
    print('BG Voice RU independent speaker comparison (WavLM).',flush=True)
    print('7206 Sound IDs | 20 historic picks | NO SOURCE/ GAME CHANGES',flush=True)
    print('Existing SHA-verified Windows report reused; new model rehashes only audio actually read.',flush=True)
    write_progress('INITIALIZING',[],[])
    import torch
    print('Torch:',torch.__version__,'CUDA:',torch.cuda.is_available(),'GPU:',torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NONE',flush=True)
    if args.device=='cuda' and not torch.cuda.is_available():
        status=write_outputs([],{},[],[],'HOLD_NO_CUDA','cpu','Existing GPU Python/Torch environment not detected')
        print('GATED_HOLD_NO_CUDA: no CPU full-library run launched',flush=True)
        return 0
    try:speaker=model_factory(device=args.device)
    except Exception as e:
        write_outputs([],{},[],[{'error':type(e).__name__,'detail':str(e)}],'HOLD_MODEL_SETUP',args.device,str(e))
        print('HOLD_MODEL_SETUP:',type(e).__name__,str(e)[:220],flush=True)
        return 0
    cache=Cache(OUT/'SHA_BOUND_WAVLM_CACHE.sqlite')
    references=ReferenceManager(rows,OUT,cache,speaker,strict_game_extract=not args.no_extract_en)
    try:
        pilot,stats=retrospective(rows,human,cache,speaker,references)
        if not stats['calibration_gate_pass']:
            write_outputs(pilot,stats,[],references.errors,'HOLD_CALIBRATION',args.device,'Independent WavLM failed human Stable/Per_line pilot or lacked EN references')
            print('HOLD_CALIBRATION:',json.dumps(stats,ensure_ascii=False),flush=True)
            print('No mass inference. No TTS, no stress, no game changes.',flush=True)
            return 0
        print('PILOT PASS: independent speaker model beat stable/per_line gate; mass inference begins.',flush=True)
        full=[];errors=[]
        locked_rows={x['sound_id']:x for x in load_csv(LOCKS)}
        protected=set(locked_rows)
        # Preserve all historical locks and non-human conflict labels in registry.
        for i,row in enumerate(rows,1):
            sid=row['sound_id']
            if (row.get('r2_human_guard')=='YES' or row.get('human_guard_present')=='YES' or sid in protected):
                full.append({'sound_id':sid,'character':row['character'],'speaker_proposal':'HOLD',
                             'reason':'HISTORIC_USER_SELECTION_PROTECTED_DO_NOT_REPLACE',
                             'protected_human_choice':locked_rows.get(sid,{}).get('voice_choice',row.get('r2_human_choice_preserved','')),
                             'human_lock':'YES','game_approved':'NO','acting_verified':'NO'})
            else:
                try:
                    selection=preference(row,cache,speaker,references)
                    selection['human_lock']='NO'
                    full.append(selection)
                except Exception as e:
                    full.append({'sound_id':sid,'character':row['character'],'speaker_proposal':'HOLD','reason':'INFERENCE_ERROR_'+type(e).__name__,'human_lock':'NO','game_approved':'NO','acting_verified':'NO'})
                    errors.append({'sound_id':sid,'reason':type(e).__name__,'details':str(e)[:300]})
            if i%25==0:
                write_progress('MASS_IN_PROGRESS',full,errors)
                print(f'MASS {i}/7206 WavLM calls={speaker.calls} HOLD={sum(x.get("speaker_proposal")=="HOLD" for x in full)}',flush=True)
            if args.max_lines and i>=args.max_lines:break
        state='MASS_DONE_PROVISIONAL_ONLY' if len(full)==7206 else 'PARTIAL_PROVISIONAL_ONLY'
        status=write_outputs(pilot,stats,full,errors+references.errors,state,args.device)
        print('RESULT:',state,'Rows:',len(full),'Report:',OUT/'BG_VOICE_GPU_SELECTION_REPORT.zip',flush=True)
        return 0
    finally:
        cache.close()


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--device',choices=['cuda','cpu'],default='cuda')
    ap.add_argument('--no-extract-en',action='store_true',help='Do not attempt exact read-only WeiDU extraction for missing EN WAV')
    ap.add_argument('--max-lines',type=int,default=0,help='Only for internal tests; 0 means all 7206')
    a=ap.parse_args()
    try:return run(a)
    except KeyboardInterrupt:
        print('INTERRUPTED: source WAV unchanged; retry can reuse cached embeddings',flush=True);return 130
    except Exception as e:
        write_outputs([],{},[],[{'error':type(e).__name__,'message':str(e),'trace':traceback.format_exc()[-2500:]}],
                      'FATAL_SAFE_STOP',a.device,str(e))
        print('FATAL_SAFE_STOP:',type(e).__name__,str(e),flush=True)
        return 2

if __name__=='__main__':raise SystemExit(main())