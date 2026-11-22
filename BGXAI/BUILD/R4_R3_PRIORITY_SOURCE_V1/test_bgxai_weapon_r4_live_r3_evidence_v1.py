#!/usr/bin/env python3
"""Offline safety tests with exact already-captured evidence; no game access."""
import copy
import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
MODULE=HERE/'BGXAI_WEAPON_R4_LIVE_R3_EVIDENCE_V1.py'
spec=importlib.util.spec_from_file_location('bgxai_live_evidence',MODULE)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
GAME=Path('/mnt/data/BGXAI_WEAPON_CONSOLE_20261122T131454167969Z.log')
NATIVE=Path('/mnt/data/BGXAI_WEAPON_NATIVE_ITM_R3.json')
R4=Path('/mnt/data/bgxai_weapon_r4_fix/BGXAI_WEAPON_ACTIVE_R4_READONLY.lua')
for p in (GAME,NATIVE,R4):
 if not p.exists(): raise RuntimeError('MISSING_TEST_INPUT:'+str(p))
parsed=m.read_console(GAME)
native=json.loads(NATIVE.read_text())
COUNT=0

def check(name, condition):
 global COUNT
 COUNT+=1
 if not condition: raise AssertionError('FAIL: '+name)
 print(f'PASS {COUNT:02d} {name}')

def failure(name, edit, expected):
 specimen=copy.deepcopy(parsed)
 obj=copy.deepcopy(native)
 edit(specimen,obj)
 answer=m.evaluate(specimen,obj,lua_source=R4)
 check(name, answer['status']=='HOLD_INCOMPLETE_LIVE_EVIDENCE' and answer['reason']==expected and answer['dispatchAuthorized']==False and answer['actionsIssued']==0)

answer=m.evaluate(parsed,native,lua_source=R4)
check('real same-game triplet 16/16',answer['correlation']=={'r1Events':16,'r2Events':16,'r4Events':16,'eventTriplesMatched':16})
check('only one actor slot 2',len(answer['actors'])==1 and answer['actors'][0]['partyIndex']==2 and answer['actors'][0]['actorId']==139266124)
check('all three selected slots found',set(s['selectedWeaponRaw'] for s in answer['actors'][0]['selections'])=={12,35,38})
selections={x['weaponResRef']:x for x in answer['actors'][0]['selections']}
check('staff native R3 APR 1',selections['STAF01']['aprDecodedIfStandard']==1 and selections['STAF01']['staticBaseDamageTimesSelectedAPR_NotDPS']==3.5)
check('short bow with arrow selected ammo APR 2',selections['BOW05']['aprDecodedIfStandard']==2 and selections['BOW05']['ammunitionResRef']=='AROW01' and selections['BOW05']['selectionResolution'].startswith('AMMO_SELECTED_UNIQUE'))
check('long sword APR 1.5, raw7',selections['SW1H04']['aprDecodedIfStandard']==1.5 and selections['SW1H04']['aprRaw']==7)
check('bow PROF 105=SHORT BOW rank 0',selections['BOW05']['proficiencyIdRaw']==105 and selections['BOW05']['proficiencyField']=='m_nProficiencyShortBow' and selections['BOW05']['proficiencyRaw']==0)
check('long sword PROF 90 rank 2',selections['SW1H04']['proficiencyIdRaw']==90 and selections['SW1H04']['proficiencyRaw']==2)
check('staff PROF 102 rank 0',selections['STAF01']['proficiencyIdRaw']==102 and selections['STAF01']['proficiencyRaw']==0)
check('raw THAC0 bonus per weapon maintained',[(s['weaponResRef'],s['rightHandTHAC0BonusRaw']) for s in answer['actors'][0]['selections']]==[('BOW05',-1),('SW1H04',1),('STAF01',-2)])
check('no fingerprint changed, not exhaustive',answer['actors'][0]['sampledRawFingerprintChanged']==False and answer['actors'][0]['sampledRawFingerprintIsExhaustiveBuffProof']==False)
check('cannot dispatch or rank',answer['priorityRecommendation'] is None and not answer['weaponSwitchAuthorized'] and not answer['dispatchAuthorized'] and answer['actionsIssued']==0)
check('full-fingerprint and target safety gates persist',len(answer['rankingGate']['missing'])>=7 and answer['rankingGate']['cannotInferFromHistoricalSelectedAPRs'])
check('R4 mapping matches source',m.standard_map_from_r4_lua(R4))
check('R3 source current game',native['sourceKind']=='CURRENT_GAME' and native['status']=='ITM_NATIVE_ALL_ITEMS_RAW_READ')
check('APR raw strict code map 7=1.5',m.RAW_APR[7]==1.5 and m.RAW_APR[6]==.5)
check('LUA/LPRINT deduplicated',len(parsed['records']['BGXW2'])==16)
check('native SW1H04 hit effect not silently valued',selections['SW1H04']['hasUnvaluedOnHitEffects']==True and 146 in selections['SW1H04']['nativeAbilityHitEffectOpcodesRaw'])
check('bow fixed APR equipped effect raw, not additive',1 in selections['BOW05']['nativeEquippedEffectOpcodesRaw'] and selections['BOW05']['aprDecodedIfStandard']==2)

failure('reject R2 different actor', lambda p,n:p['records']['BGXW2'][0][1].__setitem__('actor',123),'CROSS_OBSERVER_EVENT_IDENTITY_OR_ORDER_MISMATCH')
failure('reject R1 action mismatch',lambda p,n:p['records']['BGXWP'][1][1].__setitem__('action',19),'CROSS_OBSERVER_EVENT_IDENTITY_OR_ORDER_MISMATCH')
failure('reject R4 sequence mismatch',lambda p,n:p['records']['BGXW4'][3][1].__setitem__('seq',200),'CROSS_OBSERVER_EVENT_IDENTITY_OR_ORDER_MISMATCH')
failure('reject noncorrelated APR',lambda p,n:p['records']['BGXWP'][12][1].__setitem__('aprRaw',7),'R1_R4_RAW_COMBAT_STATS_MISMATCH')
failure('reject changed THAC0 R1/R4',lambda p,n:p['records']['BGXWP'][0][1].__setitem__('thac0Raw',123),'R1_R4_RAW_COMBAT_STATS_MISMATCH')
failure('reject missing R4 field',lambda p,n:p['records']['BGXW4'][0][1]['statsRaw'].pop('m_nDEX'),'R1_R4_RAW_COMBAT_STATS_MISMATCH')
failure('reject unrecorded slot',lambda p,n:p['records']['BGXW4'][3][1].__setitem__('selectedWeaponRaw',40),'CROSS_OBSERVER_EVENT_IDENTITY_OR_ORDER_MISMATCH')
failure('reject fake additional R4 event',lambda p,n:p['records']['BGXW4'].append(copy.deepcopy(p['records']['BGXW4'][-1])),'R1_R2_R4_ACTION_COUNTS_DISAGREE')

failure('reject missing native arrow',lambda p,n:n['items'].pop('AROW01'),'SELECTED_ITEM_OR_AMMO_UNRESOLVED')
failure('reject unknown bow launcher',lambda p,n:n['items']['BOW05']['item']['abilities'][0].__setitem__('attackTypeRaw',8),'SELECTED_ITEM_OR_AMMO_UNRESOLVED')
failure('reject changed bow native proficiency to unobserved mod slot',lambda p,n:n['items']['BOW05']['item'].__setitem__('proficiencyIdRaw',116),'MODDED_PROFICIENCY_MAPPING_UNVERIFIED')
failure('reject changed R3 sourcekind',lambda p,n:n.__setitem__('sourceKind','NOT_LIVE'),'SELECTED_ITEM_OR_AMMO_UNRESOLVED')
failure('reject item prof of untracked kind',lambda p,n:n['items']['SW1H04']['item'].__setitem__('proficiencyIdRaw',888),'NATIVE_PROFICIENCY_UNMAPPED_OR_UNREADABLE')
failure('reject half-empty arrow bag',lambda p,n:p['records']['BGXW2'][11][1]['quivers'][1].__setitem__('useCount1Raw',0),'SELECTED_ITEM_OR_AMMO_UNRESOLVED')
failure('reject class changes in same session from actor new snapshot',lambda p,n:p['records']['BGXW4'][4][1]['statsRaw'].__setitem__('m_nNumberOfAttacks',7),'R1_R4_RAW_COMBAT_STATS_MISMATCH')
failure('reject prof change mid-session',lambda p,n:p['records']['BGXW4'][3][1]['statsRaw'].__setitem__('m_nProficiencyQuarterStaff',1),'SAME_SELECTED_WEAPON_STATS_CHANGED_WITHIN_SESSION')
failure('reject new actor unsupported blank weapon',lambda p,n:p['records']['BGXW2'][0][1]['quickWeapons'][3].__setitem__('resrefRaw',None),'SELECTED_ITEM_OR_AMMO_UNRESOLVED')

with tempfile.TemporaryDirectory() as tmp:
 tmp=Path(tmp)
 bad=tmp/'R3_tampered.json'; v=copy.deepcopy(native);v['items']['BOW05']['item']['proficiencyIdRaw']=104
 bad.write_text(json.dumps(v),encoding='utf-8')
 x=m.make_report(GAME,bad,R4)
 check('reject substituted or tampered R3 report with pin',x['reason']=='NATIVE_R3_REPORT_CHANGED_REAUDIT_REQUIRED' and x['priorityRecommendation'] is None)
 wrongmap=tmp/'altered.lua';wrongmap.write_text(R4.read_text().replace("[105]='m_nProficiencyShortBow'","[105]='m_nProficiencyLongBow'"),encoding='utf-8')
 check('reject changed WPROF mapping in Lua',not m.standard_map_from_r4_lua(wrongmap) and m.evaluate(parsed,native,lua_source=wrongmap)['reason']=='R4_LUA_WPROF_MAPPING_CHANGED')
 check('reject changed R4 source contract pin',m.make_report(GAME,NATIVE,wrongmap)['reason']=='R4_SOURCE_CONTRACT_CHANGED_REAUDIT_REQUIRED')
 # Two sessions must not silently concatenate: this precisely prevents the old-save bug.
 doubled=tmp/'double.log'; doubled.write_text(GAME.read_text()+GAME.read_text(),encoding='utf-8')
 check('reject multiple sessions in one console',m.read_console(doubled)['reason']=='AMBIGUOUS_OR_MISSING_CONSOLE_SESSION')
 garbage=tmp/'garbage.log';garbage.write_text('INFO: LUA: [BGXW4] {no-json}\n'+GAME.read_text(),encoding='utf-8')
 check('reject malformed JSON source',m.read_console(garbage)['reason']=='MALFORMED_SOURCE_CONSOLE_JSON')
 # 64-record cap in R4 is not a full-party sampler, but all selected events parse.
 known=m.make_report(GAME,NATIVE,R4)
 check('real-input source pins and no ranking',known['status'].startswith('SELECTED_HISTORICAL') and known['inputSHA256']['nativeR3']==m.PINNED_R3_REPORT_SHA256 and known['priorityRecommendation'] is None)
 print('TOTAL',COUNT,'PASS')
