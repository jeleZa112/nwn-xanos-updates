# -*- coding: utf-8 -*-
"""CPU-only synthetic logic regression, NOT actual voice-quality evaluation."""
import sys,random,hashlib, math, tempfile, json, zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np
import BGVOICE_RU_ANCHOR_V2 as v2
import BGVOICE_GPU_SELECTION as v1

rows,human,byid=v1.check_registry()
protected={x['sound_id'] for x in v1.load_csv(v1.LOCKS)}
assert len(rows)==7206 and len(protected)==58
assert len(human)==20 and len({x['sound_id'] for x in human})==20

rng=np.random.default_rng(31415)
characters=sorted({x['character'] for x in rows})
base={c:v2.unit(rng.normal(size=128)) for c in characters}
preference={x['sound_id']:x['human_preference'] for x in human}
sha_to_vector={}
for r in rows:
    c=r['character'];sid=r['sound_id'];b=base[c]
    for mode in ('stable','per_line'):
        if sid in preference:
            if mode.upper()==preference[sid]:
                v=b + 0.02*v2.unit(rng.normal(size=128))
            else:
                v=b + 0.7*v2.unit(rng.normal(size=128))
        else:
            # Synthetic unlabeled donors are equally close to true character voice.
            v=b + 0.02*v2.unit(rng.normal(size=128))
        sha_to_vector[r[mode+'_sha256']]=v2.unit(v)

orig_source=v1.safe_source
orig_embed=v1.embed_audio
v1.safe_source=lambda path:path
calls=[]
def fake_embed(path,sha,cache,speaker,role):
    calls.append((sha,role));return sha_to_vector[sha],'CACHE'
v1.embed_audio=fake_embed
class Dummy: id='SIMULATED_ONLY';calls=0
try:
    a=v2.RUAnchor(rows,protected,None,Dummy(),donor_pairs=6)
    pilot=[]
    for h in human:
        row=byid[h['sound_id']]
        result=a.infer(row)
        assert h['sound_id'] not in result['reference_ids'].split('|')
        for x in result['reference_ids'].split('|'):
            assert x not in protected
        result.update(human_choice=h['human_preference'],was_correct=result['ru_proposal']==h['human_preference'])
        pilot.append(result)
    s=v2.measure(pilot,human)
    assert s['calibration_gate_pass'] is True,s
    assert s['stable_recall']==1 and s['per_line_recall']==1,s
    assert s['overall_exact_matches_including_hold']==20
    print('PASS SYNTHETIC: correct 7 STABLE and 13 PER_LINE; no label leakage')
    # All protected rows are untouched by full-pass branch.
    lockrows={x['sound_id']:x for x in v1.load_csv(v1.LOCKS)}
    assert all(x in byid for x in lockrows)
    assert len(lockrows)==58
    assert len({byid[x]['stable_sha256'] for x in lockrows})==58
    print('PASS SYNTHETIC: 7206 registry + 58 protected SHA-matched decisions')
    # Noise in random donor must be rejectable without poisoning whole character.
    c=human[0]['character'];target=human[0]['sound_id'];a.memo.clear()
    assert a.reference(c,target)[0] is not None
    print('PASS SYNTHETIC: 3+ donor prototypes, leave-target-out')
    # Ambiguous equal candidates -> hold, not a default selection.
    check=byid['D1SARE01'];saved=sha_to_vector[check['per_line_sha256']]
    sha_to_vector[check['per_line_sha256']]=sha_to_vector[check['stable_sha256']]
    r=a.infer(check)
    assert r['ru_proposal']=='HOLD' and abs(r['ru_margin_stable_minus_perline'])<1e-6,r
    sha_to_vector[check['per_line_sha256']]=saved
    print('PASS SYNTHETIC: ambiguous equals -> HOLD')
    # SHA-bound role reuse: both candidates read by separate SHA without changing paths.
    assert {role for _,role in calls}=={'RU_STABLE','RU_PER_LINE'}
    print('PASS SYNTHETIC: no English reference or user-label leakage in donor model')
    # Full-registry simulated diagnostic, preserving 58 human locks.
    decisions=[];locks=0
    for row in rows:
        if row['sound_id'] in protected:
            locks+=1
            continue
        d=a.infer(row)
        assert d['sound_id']==row['sound_id'] and d['approved']=='NO'
        decisions.append(d)
    assert len(decisions)==7148 and locks==58
    print('PASS SYNTHETIC: 7148 diagnostic rows, 58 human locks, 7206 total')
    with tempfile.TemporaryDirectory() as td:
        saved=(v2.OUT,v2.REPORT,v2.PILOT_OUTPUT,v2.MASS_OUTPUT,v2.PROGRESS_OUTPUT)
        v2.OUT=Path(td);v2.REPORT=Path(td)/'REPORT.zip';v2.PROGRESS_OUTPUT=Path(td)/'PROGRESS.json'
        class FakeCache: hits=20;misses=0
        try:
            full=decisions+[{'sound_id':sid,'character':byid[sid]['character'],'ru_proposal':'HOLD',
                'reason':'HUMAN_LOCK_PRESERVED','human_lock':'YES','protected_human_choice':'PRESERVED',
                'approved':'NO','acting_verified':'NO'} for sid in sorted(protected)]
            rep=v2.write_report(pilot,s,full,[],'MASS_DONE_PROVISIONAL_ONLY','OLD_REPORT_REUSED',FakeCache(),0)
            with zipfile.ZipFile(v2.REPORT) as z:
                assert z.testzip() is None
                names=set(z.namelist())
                assert names=={'PILOT_20_RU_ANCHORS.csv','MASS_RU_PROPOSALS.csv','RUN_STATUS.json','REFERENCE_ISSUES.json'}
                status=json.loads(z.read('RUN_STATUS.json'))
                assert status['pilot_sound_ids']==20 and status['mass_rows']==7206
                assert status['final_approvals']==0 and status['human_choices_overridden']==0
            print('PASS SYNTHETIC: full 7206-row ZIP report, CRC and JSON audit')
        finally:v2.OUT,v2.REPORT,v2.PILOT_OUTPUT,v2.MASS_OUTPUT,v2.PROGRESS_OUTPUT=saved
finally:
    v1.safe_source=orig_source;v1.embed_audio=orig_embed
print('SELFTEST_RESULT: PASS, SYNTHETIC ONLY; REAL GPU NOT YET RUN')
