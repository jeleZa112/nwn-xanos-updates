# -*- coding: utf-8 -*-
"""Read-only Russian same-character WavLM prototype pilot, independent of EN identity matching.

This is EXPERIMENTAL diagnostic speaker consistency, not human acting approval.
An equal-weight mean of both candidates from other, non-human-locked IDs defines an
unlabelled character prototype. Pilot target, all 58 human-protected IDs and any
pilot labels are EXCLUDED from prototype construction; no label-aware tuning.
No mass inference unless an explicitly fixed engineering gate passes on 20 historic picks.
"""
from __future__ import annotations
import argparse, csv, io, json, math, os, sys, traceback, time, zipfile
from pathlib import Path
from collections import defaultdict, Counter
import BGVOICE_GPU_SELECTION as v1

VERSION='BGVOICE_RU_ANCHOR_V2_EXPLORATORY_20261123'
OUT=v1.OUT
REPORT=OUT/'BG_VOICE_RU_ANCHOR_V2_REPORT.zip'
PILOT_OUTPUT=OUT/'RU_ANCHOR_PILOT_20.csv'
MASS_OUTPUT=OUT/'RU_ANCHOR_PROPOSALS_7206.csv'
PROGRESS_OUTPUT=OUT/'RU_ANCHOR_PROGRESS.json'


def atomic_progress(state,done,errors,extra=None):
    v1.atomic(PROGRESS_OUTPUT,v1.json_bytes({'schema':VERSION,'status':state,'processed':done,'errors':errors,
        'at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'original_wavs_modified':False,
        'game_modified':False,'human_approvals':0,**(extra or {})}))


def load_old_pilot():
    p=OUT/'BG_VOICE_GPU_SELECTION_REPORT.zip'
    if not p.is_file():return {},'OLDER_PILOT_REPORT_MISSING'
    try:
        with zipfile.ZipFile(p) as z:
            status=json.loads(z.read('RUN_STATUS.json'))
            if status.get('model_revision')!=v1.MODEL_REVISION or status.get('pilot_sound_ids')!=20:
                return {},'OLD_PILOT_MODEL_MISMATCH'
            d=list(csv.DictReader(io.StringIO(z.read('PILOT_HUMAN_20_WAVLM.csv').decode('utf-8-sig'))))
            if len(d)!=20 or len({x['sound_id'] for x in d})!=20:return {},'OLD_PILOT_NOT_20'
            return {x['sound_id']:x for x in d},'PREVIOUS_REAL_WAVLM_REUSED'
    except (OSError,KeyError,ValueError,zipfile.BadZipFile) as e:
        return {},'OLD_PILOT_READ_ERROR_'+type(e).__name__


def unit(x):
    import numpy as np
    a=np.asarray(x,dtype='float32').reshape(-1)
    n=float(np.linalg.norm(a))
    if not np.isfinite(n) or n < 1e-8:raise ValueError('INVALID_VECTOR')
    return a/n


class RUAnchor:
    """Unlabelled, candidate-mode-blind RU prototyping; avoid data leakage."""
    def __init__(self,rows,protected,cache,speaker,donor_pairs=6,minimum_good=3):
        self.groups=defaultdict(list)
        for r in rows:
            if r['sound_id'] not in protected:self.groups[r['character']].append(r)
        self.protected=set(protected)
        self.cache=cache;self.speaker=speaker
        self.donor_pairs=donor_pairs;self.minimum_good=minimum_good
        self.memo={};self.errors=[];self.hits=0;self.misses=0
        self.stats=Counter()

    def pair(self,row):
        sid=row['sound_id']
        xs=[]
        for mode in ('stable','per_line'):
            p=v1.safe_source(row[mode+'_readonly_path'])
            x,method=v1.embed_audio(p,row[mode+'_sha256'],self.cache,self.speaker,'RU_'+mode.upper())
            xs.append(unit(x))
            if method=='CACHE':self.hits+=1
            else:self.misses+=1
        return unit(xs[0]+xs[1])

    def _donors(self,ch):
        # Select a diverse, deterministic subset without using labels or model scores.
        # The target and all historic human IDs are excluded.
        pool=self.groups.get(ch,[])
        import hashlib
        return sorted(pool,key=lambda r:hashlib.sha256((ch+'|'+r['sound_id']).encode()).digest())

    def reference(self,ch,sid):
        import numpy as np
        key=(ch,sid)  # strict leave-one-sound-ID-out per pilot; donors never include historic locks
        if key in self.memo:return self.memo[key]
        vectors=[];ids=[];issues=[]
        for row in self._donors(ch):
            if len(vectors)>=self.donor_pairs:break
            if row['sound_id']==sid:continue
            try:vec=self.pair(row)
            except Exception as e:
                issues.append({'character':ch,'donor':row['sound_id'],'exception':type(e).__name__,
                               'note':str(e)[:160]})
                continue
            vectors.append(vec);ids.append(row['sound_id'])
        if len(vectors)<self.minimum_good:
            result=(None,len(vectors),'HOLD_FEWER_THAN_3_RU_PAIRS',ids,issues)
        else:
            array=np.stack(vectors)
            m=array@array.T
            medoid=int(np.argmax(np.median(m,axis=1)))
            keep=np.flatnonzero(m[medoid]>=.55)
            kept_ids=[ids[int(i)] for i in keep]
            if len(keep)<self.minimum_good:
                result=(None,len(keep),'HOLD_RU_REFERENCE_INCOHERENT',kept_ids,issues)
            else:
                center=unit(array[keep].mean(axis=0))
                result=(center,len(keep),'UNLABELLED_RU_PAIR_PROTOTYPE_NO_HUMAN_ATTESTATION',kept_ids,issues)
        self.memo[key]=result
        self.errors.extend(issues)
        return result

    def infer(self,row,threshold=.035):
        sid,ch=row['sound_id'],row['character']
        center,n,note,ids,issues=self.reference(ch,sid)
        base={'sound_id':sid,'character':ch,'reference_count':n,
              'reference_provenance':note,'reference_ids':'|'.join(ids),
              'approved':'NO','acting_verified':'NO','reference_source':'RUSSIAN_BOTH_MODES_MODE_BLIND'}
        if center is None:return dict(base,ru_proposal='HOLD',reason=note)
        scores={};methods={}
        for mode in ('stable','per_line'):
            try:
                p=v1.safe_source(row[mode+'_readonly_path'])
                emb,method=v1.embed_audio(p,row[mode+'_sha256'],self.cache,self.speaker,'RU_'+mode.upper())
                scores[mode]=v1.cos(unit(emb),center);methods[mode]=method
                if method=='CACHE':self.hits+=1
                else:self.misses+=1
            except Exception as e:
                return dict(base,ru_proposal='HOLD',reason='RU_'+mode.upper()+'_'+type(e).__name__,
                            details=str(e)[:160])
        margin=scores['stable']-scores['per_line']
        choice='STABLE' if margin>threshold else 'PER_LINE' if margin<-threshold else 'HOLD'
        return dict(base,ru_proposal=choice,ru_stable=round(scores['stable'],6),
                    ru_per_line=round(scores['per_line'],6),ru_margin_stable_minus_perline=round(margin,6),
                    reason=('RU_DIAGNOSTIC_ONLY_NOT_ACTING_QUALITY' if choice!='HOLD' else 'RU_TIE'),
                    cache_sources=str(methods))


def measure(pilot,human):
    recognized=[x for x in pilot if x['ru_proposal'] in ('STABLE','PER_LINE')]
    st=[x for x in recognized if x['human_choice']=='STABLE']
    pl=[x for x in recognized if x['human_choice']=='PER_LINE']
    recall_st=sum(x['was_correct'] for x in st)/len(st) if st else None
    recall_pl=sum(x['was_correct'] for x in pl)/len(pl) if pl else None
    acc=sum(x['was_correct'] for x in recognized)/len(recognized) if recognized else None
    ba=(recall_st+recall_pl)/2 if recall_st is not None and recall_pl is not None else None
    correct_all=sum(x['was_correct'] for x in pilot)
    passed=(len(recognized)>=12 and len(st)>=4 and len(pl)>=6 and
         recall_st is not None and recall_st>=.60 and recall_pl is not None and recall_pl>=.70 and
         ba is not None and ba>=.70 and acc is not None and acc>.65)
    return {'rows':len(pilot),'ru_decided':len(recognized),'ru_held':len(pilot)-len(recognized),
        'stable_covered':len(st),'per_line_covered':len(pl),
        'stable_recall':recall_st,'per_line_recall':recall_pl,'coverage':len(recognized)/20,
        'accuracy_on_decided':acc,'overall_exact_matches_including_hold':correct_all,
        'balanced_accuracy':ba,'original_wavlm_baseline_balanced_accuracy':.6285714285714286,
        'original_wavlm_baseline_overall_accepted':8,
        'original_wavlm_baseline_accepted_accuracy':.6666666666666666,
        'always_per_line_baseline_full20':.65,'calibration_gate_pass':bool(passed),
        'predeclared_gate':'12+ selected, Stable >=4 recall>=.6; Per_line>=6 recall>=.7; balanced>=.7; accuracy>.65',
        'warning':'EXPLORATORY_REUSE_OF_20_OLD_HUMAN_CHOICES_NOT_INDEPENDENT_HOLDOUT'}


def write_report(pilot,stats,full,issues,state,oldpilot_provenance,cache,model_calls=0):
    pkeys=['sound_id','human_choice','ru_proposal','was_correct','ru_stable','ru_per_line','ru_margin_stable_minus_perline',
           'previous_en_wavlm_choice','previous_en_wavlm_margin','character','reference_count',
           'reference_provenance','reference_ids','reason','approved','acting_verified']
    mkeys=['sound_id','character','ru_proposal','ru_stable','ru_per_line','ru_margin_stable_minus_perline',
           'reference_count','reference_provenance','reference_ids','reason','human_lock','protected_human_choice',
           'approved','acting_verified']
    status={'schema':VERSION,'state':state,'model':v1.MODEL_ID,'model_revision':v1.MODEL_REVISION,
            'pilot':stats,'pilot_sound_ids':len(pilot),'mass_rows':len(full),
            'original_wavlm_pilot_status':oldpilot_provenance,
            'speaker_gpu_inference_calls_new':model_calls,'cache_hits':cache.hits,'cache_misses':cache.misses,
            'game_modified':False,'original_master_modified':False,'human_choices_overridden':0,
            'stress_checks':0,'tts_regenerations':0,'final_approvals':0,
            'prototype_warning':'RU prototypes are computed from BOTH UNAPPROVED modes; speaker-consistency diagnostic only'}
    contents={'PILOT_20_RU_ANCHORS.csv':v1.csv_bytes(pilot,pkeys),
              'MASS_RU_PROPOSALS.csv':v1.csv_bytes(full,mkeys),
              'RUN_STATUS.json':v1.json_bytes(status),
              'REFERENCE_ISSUES.json':v1.json_bytes(issues[:1000])}
    import tempfile
    fd,temp=tempfile.mkstemp(dir=OUT,prefix='._ru_anchor_v2_',suffix='.zip')
    os.close(fd)
    try:
        with zipfile.ZipFile(temp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for name,b in contents.items():z.writestr(name,b)
        os.replace(temp,REPORT)
    finally:
        if os.path.exists(temp):os.unlink(temp)
    atomic_progress(state,len(full),len(issues),{'pilot':stats})
    return status


def run():
    rows,human,byid=v1.check_registry()
    protected={r['sound_id'] for r in v1.load_csv(v1.LOCKS)}
    if len(protected)!=58:raise ValueError('PROTECTED_NOT_58')
    old,provenance=load_old_pilot()
    import torch
    if not torch.cuda.is_available():
        v1.atomic(PROGRESS_OUTPUT,v1.json_bytes({'schema':VERSION,'status':'HOLD_NO_CUDA','source_modified':False}))
        print('HOLD_NO_CUDA; no mass speaker inference',flush=True)
        return 0
    model=v1.Speaker(device='cuda')
    cache=v1.Cache(OUT/'SHA_BOUND_WAVLM_CACHE.sqlite')
    anchors=RUAnchor(rows,protected,cache,model)
    try:
        pilot=[]
        for i,h in enumerate(human,1):
            sid=h['sound_id'];result=anchors.infer(byid[sid])
            result.update(human_choice=h['human_preference'],was_correct=(result['ru_proposal']==h['human_preference']))
            if sid in old:
                result['previous_en_wavlm_choice']=old[sid]['speaker_proposal']
                result['previous_en_wavlm_margin']=old[sid].get('independent_wavlm_margin_stable_minus_perline','')
            else:
                result['previous_en_wavlm_choice']='UNAVAILABLE'
            pilot.append(result)
            print(f'RU PILOT {i}/20 {sid} human={h["human_preference"]} ru={result["ru_proposal"]} refs={result["reference_count"]} newGPU={model.calls}',flush=True)
            if i%5==0:atomic_progress('PILOT_IN_PROGRESS',i,len(anchors.errors))
        stats=measure(pilot,human)
        if not stats['calibration_gate_pass']:
            write_report(pilot,stats,[],anchors.errors,'HOLD_RU_PILOT',provenance,anchors,model.calls)
            print('HOLD_RU_PILOT:',json.dumps(stats,ensure_ascii=False),flush=True)
            print('No mass run. Previous picks preserved. No voice/stress/TTS changes.',flush=True)
            return 0
        # The pilot pass is an engineering gate, not proof of acting quality.
        print('RU PILOT PASS (EXPLORATORY): begin provisional diagnostic for 7206; no release approvals.',flush=True)
        locked={r['sound_id']:r for r in v1.load_csv(v1.LOCKS)}
        full=[]
        for i,row in enumerate(rows,1):
            sid=row['sound_id']
            if sid in protected:
                result={'sound_id':sid,'character':row['character'],'ru_proposal':'HOLD',
                       'reason':'HUMAN_LOCK_PRESERVED','human_lock':'YES','protected_human_choice':locked[sid]['voice_choice'],
                       'approved':'NO','acting_verified':'NO'}
            else:
                result=anchors.infer(row)
                result['human_lock']='NO'
            full.append(result)
            if i%25==0:
                atomic_progress('MASS_IN_PROGRESS',i,len(anchors.errors))
                print(f'RU MASS {i}/7206 newGPU={model.calls} HOLD={sum(x["ru_proposal"]=="HOLD" for x in full)}',flush=True)
        write_report(pilot,stats,full,anchors.errors,'MASS_DONE_PROVISIONAL_ONLY',provenance,anchors,model.calls)
        print('MASS_DONE_PROVISIONAL_ONLY rows=',len(full),'report=',REPORT,flush=True)
    finally:cache.close()
    return 0


def main():
    try:return run()
    except KeyboardInterrupt:
        atomic_progress('INTERRUPTED_CACHED_RESULTS_RESUMABLE',0,0)
        print('INTERRUPTED. Re-run to reuse WavLM SHA-bound cache. No originals modified.',flush=True)
        return 130
    except Exception as e:
        atomic_progress('FATAL_SAFE_STOP',0,1,{'exception':type(e).__name__,'details':str(e),'trace':traceback.format_exc()[-1500:]})
        print('FATAL_SAFE_STOP:',type(e).__name__,str(e),flush=True)
        return 2

if __name__=='__main__':raise SystemExit(main())
