"""Checks the generated selection-only evidence, no game or WAV writes."""
import csv, hashlib, io, json, pathlib, shutil, subprocess, sys, tempfile, zipfile
from collections import Counter
from BGVOICE_SELECTION_R2 import build,EXPECTED_INPUT_SHA256

ROOT=pathlib.Path('/mnt/data')
F=ROOT/'BG_VOICE_RU_SELECTION_MODEL_EVIDENCE_FUSED.zip'
V=ROOT/'SEND_TO_CHATGPT_BGVOICE_V58_TARGETED_REVIEW.zip'
Z=ROOT/'BG_VOICE_RU_V70_BULK_SELECTION_PAYLOAD_20261122.zip'

def csvfile(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def run():
    assert sha(F)==EXPECTED_INPUT_SHA256['fusion'] and sha(V)==EXPECTED_INPUT_SHA256['v58']
    with tempfile.TemporaryDirectory() as d:
        a,b=pathlib.Path(d)/'run1',pathlib.Path(d)/'run2'
        info=build(F,V,a)
        info2=build(F,V,b)
        assert info==info2
        files={x.name:sha(x) for x in a.iterdir()}
        assert files=={x.name:sha(x) for x in b.iterdir()}
        full=csvfile(a/'SELECTION_R2_MASTER_7206.csv')
        cand=csvfile(a/'MODEL_HYPOTHESES_UNAPPROVED.csv')
        human=csvfile(a/'HUMAN_GUARDS_PRESERVED.csv')
        cal=csvfile(a/'CALIBRATION_BALANCED_UP_TO_60.csv')
        char=csvfile(a/'CHARACTER_REFERENCE_AUDIT_365.csv')
        assert len(full)==7206 and len({x['sound_id'] for x in full})==7206
        assert len(human)==info['human_guards']==41
        assert len(cand)==info['voice_only_dual_check_hypotheses']
        assert len(full)==len(human)+len(cand)+info['unresolved_nonhuman']
        assert len(char)==365 and len(cal)==60
        assert Counter(x['calibration_stratum'] for x in cal)=={
            'STABLE_RECOMMENDED_UNAPPROVED':20,'PER_LINE_RECOMMENDED_UNAPPROVED':20,'ECAPA_MODE_BIAS_CONFLICT':20}
        assert max(Counter(x['character'] for x in cal).values())<=2
        oldab={'AERIE01','ALORA14','CERND46','CORAN37','OH91797','CEFALD18',
            'HAER2501','OH87140','IMOEN09','JAHEIR59','JANJAN08','KAGAN20'}
        assert not oldab & {x['sound_id'] for x in cal}
        assert not {x['sound_id'] for x in human} & {x['sound_id'] for x in cand}
        assert all(x['r2_final_game_approved']=='NO' and x['r2_stress_checked']=='NO' and
           x['r2_actor_quality_verified']=='NO' for x in full)
        for x in cand:
            assert int(x['v55_speaker_anchors'])>=3
            assert x['r2_unapproved_voice_hypothesis'] in ('STABLE','PER_LINE')
            assert not x['r2_gates'] and float(x['r2_residual_ECAPA_margin_DIAGNOSTIC'])*float(x['r2_old_ECAPA_margin'])>0
        byid={x['sound_id']:x for x in full}
        assert byid['DYNAH32']['r2_human_choice_preserved']=='STABLE'
        assert byid['OH88513']['r2_human_choice_preserved']=='PER_LINE'
        assert byid['OH83564']['r2_human_choice_preserved']=='PER_LINE'
        assert byid['OH92184']['r2_human_choice_preserved']=='STABLE'
        assert byid['KORGAN57']['r2_status']=='HOLD_PREVIOUS_MODE_CONFLICT'
        assert byid['IMOEN75']['r2_human_choice_preserved']=='PREVIOUS_LONG_XVECTOR'
        assert byid['OH85856']['r2_status']=='PRESERVE_APPROVED_SPECIAL_WAV'
        assert byid['OH80404']['r2_status']=='PRESERVE_APPROVED_SPECIAL_WAV'
        assert byid['OH89888']['r2_status']=='HUMAN_ORIGINAL_PAIR_BOTH_BAD'
        assert byid['OH85713']['r2_status']=='HUMAN_ORIGINAL_PAIR_BOTH_BAD'
        assert byid['EDWIN74']['r2_status']=='HUMAN_HOLD_BOTH_BAD'
        assert byid['VICONI58']['r2_status'] in ('HOLD_SELECTION_RISK','HOLD_INCONCLUSIVE_VOICE_EVIDENCE')
        # SHA fail must fail before any output changes.
        bad=pathlib.Path(d)/'tampered.zip';shutil.copyfile(F,bad)
        with bad.open('ab') as f:f.write(b'corrupted')
        try:build(bad,V,pathlib.Path(d)/'should_not_exist')
        except ValueError as e:assert 'INPUT_SHA_MISMATCH' in str(e)
        else:raise AssertionError('accepted tampered source archive')
        assert not (pathlib.Path(d)/'should_not_exist').exists()
        return {'status':'PASS','registry':len(full),'machine_hypotheses':len(cand),
        'human_guarded':len(human),'unresolved':info['unresolved_nonhuman'],
        'balanced_calibration':len(cal),'distinct_calibration_characters':len(set(x['character'] for x in cal)),
        'old_ecapa_per_line_higher':info['old_ecapa_per_line_higher'],
        'old_ecapa_pairs':info['old_ecapa_pairs'],
        'identical_deterministic_rerun':True,'tampered_input_fail_closed':True,
        'no_old_ab12_in_calibration':True,'no_game_install':True}

if __name__=='__main__':print(json.dumps(run(),ensure_ascii=False,indent=2))