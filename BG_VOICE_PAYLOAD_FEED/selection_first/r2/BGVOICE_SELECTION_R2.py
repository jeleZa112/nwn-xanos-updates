"""BG Voice RU: selection FIRST, historical evidence arbitration, read-only.

No generation, no stress QA, no installation, no audio writes. Scores describe
uncertainty, not validated acting quality. Designed to be imported by the
single main updater, which provides the real WAV SHA check/audio listener.
"""
from __future__ import annotations
import csv, hashlib, io, json, math, statistics, zipfile
from collections import defaultdict, Counter
from pathlib import Path

R2_SCHEMA='BGVOICE_SELECTION_R2_BIAS_AWARE'
EXPECTED_INPUT_SHA256={
 'fusion':'c00169c4c5e3196865445e9f1ca3b42b80f675e5aeda812cd88df73c8d5f9b2c',
 'v58':'4a735ad88e85e5598fad31ea3d86f49708b882fb43157b581ad515dc07b04692'
}

def checked_input(path, expected):
    p=Path(path)
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    if h.hexdigest()!=expected:raise ValueError('INPUT_SHA_MISMATCH_'+p.name)

CHOICES={'STABLE','PER_LINE'}
HUMAN_STATUSES={'USER_LOCK','USER_PREFERENCE_NEEDS_QA','HUMAN_PREFERENCE_FINAL_QA_PENDING','USER_APPROVED_SPECIAL_WAV'}
ACTING_HOLDS={'HOLD_EXPRESSIVE','HOLD_KNOWN_HISTORY','HOLD_USER_GUARD','HOLD_SELECTED_AUDIO_FLAG',
              'HUMAN_BOTH_BAD_HOLD','HUMAN_NO_EN_HOLD'}
MAIN_BRANCH_HISTORY={'CERND46','HAERDA36','KAGAN05','OH80910','OH86758','VICONI58','CEFALD18'}
HISTORICAL_MODE_CONFLICT={'KORGAN57'}
OLD_AB12={'AERIE01','ALORA14','CERND46','CORAN37','OH91797','CEFALD18',
          'HAER2501','OH87140','IMOEN09','JAHEIR59','JANJAN08','KAGAN20'}

def csv_from_zip(data, name):
    with zipfile.ZipFile(data) as z:
        if z.testzip():raise ValueError('SOURCE_ZIP_CRC_FAILED')
        return list(csv.DictReader(io.StringIO(z.read(name).decode('utf-8-sig'))))

def nfloat(s):
    try:
        v=float(s)
        return v if math.isfinite(v) else None
    except (ValueError,TypeError):return None

def ind(x):
    return ('STABLE' if x>0 else 'PER_LINE') if x!=0 else None

def build(input_fusion_zip, v58_review_zip, outdir):
    checked_input(input_fusion_zip,EXPECTED_INPUT_SHA256['fusion'])
    checked_input(v58_review_zip,EXPECTED_INPUT_SHA256['v58'])
    rows=csv_from_zip(input_fusion_zip,'VOICE_SELECTION_MASTER_7206_MODEL_FUSION.csv')
    v58=csv_from_zip(v58_review_zip,'01_USER_RATINGS.csv')
    if len(rows)!=7206 or len({x['sound_id'] for x in rows})!=7206:raise ValueError('INPUT_REGISTRY_NOT_7206_UNIQUE')
    if len(v58)!=24 or len({x['sound_id'] for x in v58})!=24:raise ValueError('INPUT_V58_NOT_24_UNIQUE')
    lookup={x['sound_id']:x for x in rows}
    for a in v58:
        if a['sound_id'] not in lookup:raise ValueError('V58_UNKNOWN_ID')
        if a['verified_stable']!='SOURCE_SHA_VERIFIED' or a['verified_per_line']!='SOURCE_SHA_VERIFIED':
            raise ValueError('V58_AUDIO_NOT_VERIFIED')
    user_old={x['sound_id']:(x['voice_choice_or_proposal'],x['selection_status'])
              for x in rows if x['selection_status'] in HUMAN_STATUSES}
    hist={x['sound_id']:x for x in v58}
    # Do NOT count cross-model evidence as equivalent labels.
    for sid,x in hist.items():
        if x['choice'] in CHOICES and sid in user_old and user_old[sid][0] in CHOICES and x['choice']!=user_old[sid][0]:
            raise ValueError('HISTORICAL_HUMAN_CONFLICT:'+sid)
    # Old ECAPA V5 values favor Per_line in ~81% of scored pairs. Estimate
    # character-specific distribution shifts (not a validated correction).
    speaker_raw=defaultdict(list)
    raw_all=[]
    for x in rows:
        a,b=nfloat(x['voice_stable']),nfloat(x['voice_per_line'])
        if (a is not None and b is not None and x['sound_id'] not in hist and x['selection_status'] not in ACTING_HOLDS
                and x['selection_status'] not in HUMAN_STATUSES and not x['v17_human_preference']
                and 'ACTING_QUEUE' not in x['risk_flags']):
            raw=a-b;raw_all.append(raw)
            if int(x['v55_speaker_anchors'] or 0)>=3:
                speaker_raw[x['character']].append(raw)
    if len(raw_all)<5000:raise ValueError('ECAPA_BASELINE_INCOMPLETE')
    gmed=statistics.median(raw_all)
    character_stats={}
    for ch in set(x['character'] for x in rows):
        sample=speaker_raw.get(ch,[])
        n=len(sample)
        own_med=statistics.median(sample) if n>=10 else gmed
        # Small groups borrow the GLOBAL group rather than falsely asserting
        # their 2-3 line medians as speaker signatures.
        shrink=n/(n+25) if n>=10 else 0
        baseline=gmed*(1-shrink)+own_med*shrink
        character_stats[ch]={'n_clean_scored':n,'global_ecapa_gap_median':gmed,
                             'speaker_ecapa_gap_median':own_med if n>=10 else None,
                             'expected_gap':baseline,
                             'bias_estimate_is_voice_quality':False}
    candidates=[];review=[];human_audit=[];out=[]
    flags_counter=Counter();class_counter=Counter();calibration=Counter()
    for x in rows:
        sid=x['sound_id'];a,b=nfloat(x['voice_stable']),nfloat(x['voice_per_line'])
        as_,ap=nfloat(x['asr_stable']),nfloat(x['asr_per_line'])
        raw=(a-b) if a is not None and b is not None else None
        de_bias=(raw-character_stats[x['character']]['expected_gap']) if raw is not None else None
        raw_winner=ind(raw) if raw is not None else None
        deb_winner=ind(de_bias) if de_bias is not None else None
        anchors=int(x['v55_speaker_anchors'] or 0)
        h=hist.get(sid)
        prior=x['selection_status']; prior_choice=x['voice_choice_or_proposal']
        gate=[];sel='';truth='NO';status='';recommend='';label='';voice_strength=''
        # Human original pair preference ALWAYS outranks numeric signals;
        # never reinterpret BOTH_BAD, NO_EN, special V65/V60 WAV as original pair.
        if sid in user_old or x['v17_human_preference'] or h:
            val=(x['v17_human_preference'] if x['v17_human_preference'] else '')
            if prior=='USER_APPROVED_SPECIAL_WAV':
                # A separately approved V60/V65 WAV is NOT an approved original pair.
                status='PRESERVE_APPROVED_SPECIAL_WAV';truth='YES';sel=prior_choice
                if h and h['choice']=='BOTH_BAD':gate.append('ORIGINAL_STABLE_PER_LINE_BOTH_BAD')
            elif val in ('BOTH_BAD','NO_EN'):
                status='HUMAN_HOLD_'+val;truth='YES'
            elif h and h['choice'] in ('BOTH_BAD','UNSURE'):
                status='HUMAN_ORIGINAL_PAIR_'+h['choice'];truth='YES'
            elif val in CHOICES:
                status='HUMAN_PREFERENCE_NO_GAME_APPROVAL';truth='YES';sel=val
            elif h and h['choice'] in CHOICES:
                status='HUMAN_PREFERENCE_NO_GAME_APPROVAL';truth='YES';sel=h['choice']
            elif prior_choice in CHOICES or prior_choice=='PREVIOUS_LONG_XVECTOR':
                status='PRESERVE_HUMAN_BASELINE_OR_SPECIAL';truth='YES';sel=prior_choice
            else:status='HUMAN_HOLD_SOURCE';truth='YES'
            gate.append('HUMAN_BEATS_ALL_MODELS')
        elif sid in HISTORICAL_MODE_CONFLICT:
            status='HOLD_PREVIOUS_MODE_CONFLICT';gate.append('HISTORICAL_MODE_CONFLICT')
        else:
            critical=x['risk_flags'] or ''
            if anchors<3:gate.append('NO_THREE_ANCHORS')
            if prior in ACTING_HOLDS or 'ACTING_QUEUE' in critical:gate.append('ACTING_HOLD_NO_VALIDATED_EMOTION')
            if sid in MAIN_BRANCH_HISTORY:gate.append('KNOWN_HISTORY_NO_AUTOMATIC_REWORK')
            if 'V70_SELECTED_WEAKER_VOICE' in critical:gate.append('V70_VOICE_DISAGREEMENT')
            if prior in ('HOLD_CONTENT','HOLD_VOICE_CONTENT_CONFLICT'):gate.append('SOURCE_CONTENT_HOLD')
            if a is None or b is None:gate.append('MISSING_PAIRWISE_VOICE_SCORES')
            if as_ is None or ap is None:gate.append('MISSING_ASR')
            if as_ is not None and ap is not None and max(as_,ap)<0.82:gate.append('BOTH_ASR_LOW')
            if x['v14_ecapa_vs_asr']=='ASR_OPPOSES_ECAPA':gate.append('ASR_ECAPA_CONFLICT')
            if x['v14_v13_whisper_zipformer_disagree']=='YES':gate.append('ZIPFORMER_WHISPER_DISAGREE')
            if x['v14_v7_pacing_if_measured'] not in ('','VAD_NO_LARGE_DIFFERENCE'):gate.append('VAD_PACING_RISK')
            if raw_winner is not None and deb_winner is not None and raw_winner!=deb_winner:
                gate.append('GLOBAL_OR_CHARACTER_ECAPA_BIAS_MAY_CHANGE_DIRECTION')
            if x['v14_v13_content_hint_NOT_APPROVED'] in CHOICES and raw_winner and x['v14_v13_content_hint_NOT_APPROVED']!=raw_winner:
                gate.append('TWO_ASR_CONTENT_HINT_VOICE_CONFLICT')
            # A conservative, non-approved *review hypothesis*.
            # All other cases remain a ranked human/automated review; avoiding
            # false confidence is better than marking every PER_LINE good.
            if anchors>=3 and raw is not None and de_bias is not None and as_ is not None and ap is not None and raw_winner==deb_winner and abs(raw)>=0.10 and abs(de_bias)>=0.06:
                w=raw_winner
                chosen_asr=as_ if w=='STABLE' else ap
                alt_asr=ap if w=='STABLE' else as_
                if chosen_asr>=0.82 and chosen_asr+0.035>=alt_asr and not gate:
                    status='VOICE_REVIEW_HYPOTHESIS_PREVIOUSLY_HELD';recommend=w
                    voice_strength='SAME_ECAPA_MODEL_RAW_AND_RELATIVE_SCORES_AGREE_ASR_NOT_WORSE_NOT_ARTISTIC_PROOF';
                else:status='HOLD_SELECTION_RISK'
            else:status='HOLD_INCONCLUSIVE_VOICE_EVIDENCE' if not gate else 'HOLD_SELECTION_RISK'
        # Machine 'recommendation' never equals user-approved choice.
        if recommend and truth=='YES':raise AssertionError('machine overruled human')
        if status.startswith('HUMAN') or status.startswith('PRESERVE'):
            class_counter['HUMAN_GUARDED']+=1
        class_counter[status]+=1
        for k in gate:flags_counter[k]+=1
        safe_asr_selected=as_ if (recommend=='STABLE' or sel=='STABLE') else ap if (recommend=='PER_LINE' or sel=='PER_LINE') else None
        # prioritize character and uncertainty rather than emotion label alone
        # rating is purely review urgency, not probability of good acting
        urgency=(100 if sid in HISTORICAL_MODE_CONFLICT else 0) + (95 if 'ASR_ECAPA_CONFLICT' in gate else 0) + (85 if 'TWO_ASR_CONTENT_HINT_VOICE_CONFLICT' in gate else 0) + (80 if 'VAD_PACING_RISK' in gate else 0) + (78 if 'ACTING_HOLD_NO_VALIDATED_EMOTION' in gate else 0) + (70 if 'SOURCE_CONTENT_HOLD' in gate else 0) + (20 if 'GLOBAL_OR_CHARACTER_ECAPA_BIAS_MAY_CHANGE_DIRECTION' in gate else 0)
        if x['v14_v9_emotion_stable_UNCALIBRATED']!=x['v14_v9_emotion_per_line_UNCALIBRATED']:
            urgency+=5 # Never select via V9 uncalibrated label.
        if raw is not None and de_bias is not None:
            urgency+=min(10,int(abs(raw-de_bias)*15))
        out.append({
            **x,
            'r2_status':status,'r2_human_guard':truth,'r2_human_choice_preserved':sel,
            'r2_human_evidence_level':('V17_HUMAN_SHA_PAIR_MATCHED' if x['v17_human_sha_verified']=='YES' else 'V58_HISTORIC_VERIFIED_AUDIO_NOW_NEEDS_LIVE_SHA' if h else 'LEGACY_USER_DECISION_PROVENANCE_IN_MASTER') if truth=='YES' else '',
            'r2_unapproved_voice_hypothesis':recommend,
            'r2_v5_original_no_auto_promotion':x['v5_previous_status'],
            'r2_old_ECAPA_margin':f'{raw:.6f}' if raw is not None else '',
            'r2_bias_estimate':f'{character_stats[x["character"]]["expected_gap"]:.6f}',
            'r2_residual_ECAPA_margin_DIAGNOSTIC':f'{de_bias:.6f}' if de_bias is not None else '',
            'r2_review_priority':str(urgency),
            'r2_gates':';'.join(gate),
            'r2_best_hypothesis_reason':voice_strength,
            'r2_actor_quality_verified':'NO',
            'r2_EN_expected_sound_id':sid,
            'r2_EN_same_character_and_SHA_VERIFIED':'NOT_YET_VERIFIED',
            'r2_stress_checked':'NO',
            'r2_final_game_approved':'NO',
        })
        if truth=='YES':human_audit.append(out[-1])
        if recommend:candidates.append(out[-1])
        if truth=='NO' and not recommend:review.append(out[-1])
    if len(out)!=7206 or len({x['sound_id'] for x in out})!=7206:raise AssertionError('coverage error')
    if sum(x['r2_human_guard']=='YES' for x in out)!=len(human_audit):raise AssertionError('guard count error')
    for sid in ['OH85856','OH80404','IMOEN75','KORGAN57','DYNAH32','OH83564','VICON36']:
        if sid not in set(x['sound_id'] for x in out):raise AssertionError('missing protected case')
    protected={r['sound_id']:r for r in out}
    assert protected['IMOEN75']['r2_human_choice_preserved']=='PREVIOUS_LONG_XVECTOR'
    assert protected['OH85856']['r2_status']=='PRESERVE_APPROVED_SPECIAL_WAV'
    assert protected['OH80404']['r2_status']=='PRESERVE_APPROVED_SPECIAL_WAV'
    assert protected['KORGAN57']['r2_status']=='HOLD_PREVIOUS_MODE_CONFLICT'
    assert protected['DYNAH32']['r2_human_choice_preserved']=='STABLE'
    assert protected['OH83564']['r2_human_choice_preserved']=='PER_LINE'
    assert protected['VICON36']['r2_human_choice_preserved']=='STABLE'
    assert not any(x['r2_final_game_approved']!='NO' or x['r2_stress_checked']!='NO' for x in out)
    # Selection-first reference audit: prefer unapproved *candidates*, never call them human approved anchors.
    grouped=defaultdict(list)
    for x in out:grouped[x['character']].append(x)
    reference_rows=[]
    for ch,rs in sorted(grouped.items()):
        eligible=[x for x in rs if x['r2_unapproved_voice_hypothesis']]
        eligible.sort(key=lambda x:(-abs(float(x['r2_residual_ECAPA_margin_DIAGNOSTIC'])),x['sound_id']))
        reference_rows.append({'character':ch,'lines':len(rs),'old_anchors_available':max(int(x['v55_speaker_anchors'] or 0) for x in rs),
        'safe_voice_only_hypotheses':len(eligible),'example_ids_FOR_HUMAN_CALIBRATION_NOT_APPROVED':'|'.join(x['sound_id'] for x in eligible[:5]),
        'human_prefs_or_locks':sum(x['r2_human_guard']=='YES' for x in rs),
        'note':'EN+RU character voice anchors require real acoustic QA; 3 old cached anchors != 3 human approved references'})
    # Distinguish A/B *model calibration* from defect triage: don't ask the
    # user to judge voice identity on samples already marked with speech/acting
    # defects, without anchors, or previously shown in the old AB12. Balanced
    # strata stop Per_line class imbalance from dominating validation.
    exclude={x['sound_id'] for x in human_audit}|OLD_AB12
    clean_candidates=[x for x in candidates if x['sound_id'] not in exclude]
    conflicts=[x for x in review if x['sound_id'] not in exclude
        and 'GLOBAL_OR_CHARACTER_ECAPA_BIAS_MAY_CHANGE_DIRECTION' in x['r2_gates']
        and not any(f in x['r2_gates'] for f in ('ACTING_HOLD_NO_VALIDATED_EMOTION','SOURCE_CONTENT_HOLD',
            'ASR_ECAPA_CONFLICT','BOTH_ASR_LOW','MISSING_PAIRWISE_VOICE_SCORES','NO_THREE_ANCHORS',
            'ZIPFORMER_WHISPER_DISAGREE','KNOWN_HISTORY_NO_AUTOMATIC_REWORK'))
        and nfloat(x['asr_stable']) is not None and nfloat(x['asr_per_line']) is not None
        and min(float(x['asr_stable']),float(x['asr_per_line']))>=0.82]
    # representative strongest/probe ties from DIFFERENT characters
    stable=[x for x in clean_candidates if x['r2_unapproved_voice_hypothesis']=='STABLE']
    per=[x for x in clean_candidates if x['r2_unapproved_voice_hypothesis']=='PER_LINE']
    stable.sort(key=lambda x:(-abs(float(x['r2_residual_ECAPA_margin_DIAGNOSTIC'])),x['sound_id']))
    per.sort(key=lambda x:(-abs(float(x['r2_residual_ECAPA_margin_DIAGNOSTIC'])),x['sound_id']))
    conflicts.sort(key=lambda x:(-abs(float(x['r2_old_ECAPA_margin'])),x['sound_id']))
    sampled=[];char_counts=Counter();in_sample=set();strata=Counter()
    for label,items in [('STABLE_RECOMMENDED_UNAPPROVED',stable),('PER_LINE_RECOMMENDED_UNAPPROVED',per),
                        ('ECAPA_MODE_BIAS_CONFLICT',conflicts)]:
        for x in items:
            if x['sound_id'] in in_sample or char_counts[x['character']]>=2:continue
            y=x.copy();y['calibration_stratum']=label
            sampled.append(y);char_counts[x['character']]+=1;in_sample.add(x['sound_id']);strata[label]+=1
            if strata[label]>=20:break
    # Separate high-risk diagnostics for the engine; not an A/B prompt.
    review.sort(key=lambda x:(-int(x['r2_review_priority']),x['character'],x['sound_id']))
    risk_sample=review[:60]
    outpath=Path(outdir);outpath.mkdir(parents=True,exist_ok=True)
    for name,data in [('SELECTION_R2_MASTER_7206.csv',out),('CHARACTER_REFERENCE_AUDIT_365.csv',reference_rows),('HUMAN_GUARDS_PRESERVED.csv',human_audit),('MODEL_HYPOTHESES_UNAPPROVED.csv',candidates),('VOICE_REVIEW_PRIORITY_60.csv',risk_sample),('CALIBRATION_BALANCED_UP_TO_60.csv',sampled)]:
        p=outpath/name
        with p.open('w',encoding='utf-8-sig',newline='') as f:
            cols=list(out[0]) if data and name.endswith('7206.csv') else list(data[0]) if data else ['sound_id']
            w=csv.DictWriter(f,fieldnames=cols,extrasaction='raise',lineterminator='\n')
            w.writeheader();w.writerows(data)
    # Retrospective check only: these small, strongly selected examples are
    # NOT evidence of population accuracy. Critically, debiasing alone *loses*
    # agreement with the actual past human preferences on this sample.
    previously_human_scored=[x for x in human_audit if x['r2_human_choice_preserved'] in CHOICES
        and x['r2_old_ECAPA_margin'] and x['r2_residual_ECAPA_margin_DIAGNOSTIC']]
    raw_agree=sum(ind(float(x['r2_old_ECAPA_margin']))==x['r2_human_choice_preserved']
                  for x in previously_human_scored)
    adjusted_agree=sum(ind(float(x['r2_residual_ECAPA_margin_DIAGNOSTIC']))==x['r2_human_choice_preserved']
                       for x in previously_human_scored)
    v5_hold_status=Counter(x['v5_previous_status'] for x in candidates)
    s={
       'schema':R2_SCHEMA,'sound_ids':len(out),'human_guards':len(human_audit),
       'voice_only_dual_check_hypotheses':len(candidates),'unresolved_nonhuman':len(review),
       'calibration_balanced_sample_size':len(sampled),'calibration_strata':dict(strata),'high_risk_triage_size':len(risk_sample),'characters':len(reference_rows),
       'old_ecapa_pairs':len(raw_all),'old_ecapa_per_line_higher':sum(d<0 for d in raw_all),
       'retrospective_manual_with_both_scores':len(previously_human_scored),
       'old_raw_ecapa_direction_matches_human':raw_agree,
       'speaker_centered_ecapa_direction_matches_human':adjusted_agree,
       'prior_v5_status_for_voice_hypotheses':dict(v5_hold_status),
       'global_ecapa_gap_median':round(gmed,6),'bias_correction_is_acting_metric':False,
       'source_v58_human_decisions':len(v58),'v58_modes':sum(x['choice'] in CHOICES for x in v58),
       'v58_rejected_or_unsure':sum(x['choice'] not in CHOICES for x in v58),
       'r2_gates':dict(sorted(flags_counter.items())),
       'r2_status_counts':dict(sorted(class_counter.items())),
       'new_audio':0,'game_modified':False,'source_wavs_modified':False,'selection_complete':False,
       'real_world_validation':'NOT_CALIBRATED: no direct WAV listening; agreement on old preferences is limited and not generalization proof',
       'notes':'R2 is uncertainty triage; raw and speaker-centered scores are TWO VIEWS OF THE SAME ECAPA model, not independent validators. Centering did NOT improve retrospective human agreement. All preferences remain unapproved until real acoustic EN/voice/acting QA.'}
    (outpath/'SUMMARY.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    return s

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--fusion',required=True);p.add_argument('--v58',required=True);p.add_argument('--outdir',required=True)
 a=p.parse_args();print(json.dumps(build(a.fusion,a.v58,a.outdir),ensure_ascii=False,indent=2))