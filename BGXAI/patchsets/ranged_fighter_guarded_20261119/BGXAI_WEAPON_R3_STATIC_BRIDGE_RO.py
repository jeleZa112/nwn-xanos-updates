#!/usr/bin/env python3
"""BGXAI R3 -> weapon priority V3/V4/V5: passive *source-only* evidence bridge.

Input: user's actual R3 native ITM/2DA report and matched R1/R2 console report.
Output: bounded static weapon candidates, sampled APR, explicit unknowns.
NEVER chooses a weapon, issues an action, changes a file in the game or asserts
manual/EPS safety. All numerical attack comparisons are illustrative only.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path

SLOTS={35:'QUICKWEAPON1',36:'QUICKWEAPON2',37:'QUICKWEAPON3',38:'QUICKWEAPON4'}
RESREF=re.compile(r'^[A-Z0-9_#-]{1,8}$')
SHA=re.compile(r'^[0-9a-f]{64}$')
APR_DEC={0:0.0,1:1.0,2:2.0,3:3.0,4:4.0,5:5.0,6:0.5,7:1.5,8:2.5,9:3.5,10:4.5}
MANDATORY_FLAGS=('targetImmuneOrResistantVerified','launcherAmmoPairVerified',
 'currentCharacterBuffsVerified','proficiencyAlreadyAppliedVerified',
 'aprPerSlotVerified','fullWeaponEffectsVerified','manualAndEPSQueueVerified')

class EvidenceHold(ValueError): pass

def _req(condition, message):
    if not condition:raise EvidenceHold(message)

def _ref(x):return isinstance(x,str) and bool(RESREF.fullmatch(x))

def _finite_int(x,lo,hi):return type(x) is int and lo<=x<=hi

def _sha(source):return hashlib.sha256(source).hexdigest()

def _ability(a):
    _req(isinstance(a,dict),'ABILITY_NOT_OBJECT')
    for key in ('attackTypeRaw','rangeRaw','speedRaw','launcherRequiredRaw','diceCountRaw','diceSidesRaw','damageBonusRaw','thac0BonusRaw'):
        _req(_finite_int(a.get(key),-50000,50000),'ABILITY_FIELD_UNSAFE:'+key)
    _req(0<=a['diceCountRaw']<=100 and 0<=a['diceSidesRaw']<=1000,'ABILITY_DICE_UNSAFE')
    return a

def _base(a):
    n,s,b=a['diceCountRaw'],a['diceSidesRaw'],a['damageBonusRaw']
    return n*(s+1)/2+b if n>0 and s>0 else b

def _effects(item):
    e=item.get('equippedEffects') or []
    _req(isinstance(e,list) and len(e)<=2048,'EFFECTS_UNSAFE')
    for v in e:
        _req(isinstance(v,dict) and _finite_int(v.get('opcodeRaw'),0,65535),'EFFECT_OPCODE_INVALID')
    return e

def _item(r3,name):
    _req(_ref(name) and name in r3['items'],'ITEM_NOT_IN_NATIVE_REPORT:'+str(name))
    ent=r3['items'][name]; prov=ent.get('provenance',{})
    _req(prov.get('origin') in ('CURRENT_GAME_BIFF','CURRENT_GAME_OVERRIDE') and
         isinstance(prov.get('sha256'),str) and SHA.fullmatch(prov['sha256']),'ITEM_PROVENANCE_UNVERIFIED:'+name)
    val=ent.get('item')
    _req(isinstance(val,dict) and val.get('schema')=='BGXAI_ITM_RAW_V1','ITEM_SCHEMA_UNVERIFIED:'+name)
    _req(isinstance(val.get('abilities'),list) and len(val['abilities'])<=64,'ABILITY_COUNT_UNSAFE:'+name)
    for a in val['abilities']:_ability(a)
    _effects(val)
    return val,prov

def _item_loss_risks(r3, name, abilities):
    """Detect resource-based replacement chains; describes *potential* loss only.

    The effect activation (including iron-crisis story state, weapon ownership,
    opcode target semantics) is unproven. Do not invent damage or probability.
    """
    found=[]
    for a in abilities:
        for e in a.get('effects',[]):
            if e.get('opcodeRaw')!=146 or not _ref(e.get('resourceRaw')):
                continue
            spname=e['resourceRaw']
            sp=r3.get('linkedSpells',{}).get(spname)
            if not isinstance(sp,dict):
                raise EvidenceHold('LINKED_SPELL_MISSING_IN_R3:'+spname)
            spr=sp.get('provenance',{})
            _req(spr.get('origin') in ('CURRENT_GAME_BIFF','CURRENT_GAME_OVERRIDE') and
                 isinstance(spr.get('sha256'),str) and SHA.fullmatch(spr['sha256']),
                 'LINKED_SPELL_PROVENANCE_INVALID:'+spname)
            ability_fx=[x for ab in sp.get('spell',{}).get('abilities',[]) for x in ab.get('effects',[])]
            removes=[x.get('resourceRaw') for x in ability_fx if x.get('opcodeRaw')==112]
            creates=[x.get('resourceRaw') for x in ability_fx if x.get('opcodeRaw')==122]
            replacement=name in removes and 'MISC56_' in creates
            if replacement:
                found.append({'type':'POTENTIAL_WEAPON_BREAKAGE_REPLACEMENT',
                    'triggerOpcodeRaw':146,'triggerSpellRaw':spname,
                    'triggerProbability1Raw':e.get('probability1Raw'),
                    'triggerProbability2Raw':e.get('probability2Raw'),
                    'removeItemRaw':name,'createItemRaw':'MISC56_',
                    'narrativeContext':'IRON_CRISIS_POSSIBLE_NOT_LIVE_PROVEN',
                    'observedTriggerCount':0,'numericalDamageContributionCounted':0,
                    'activationAndTargetConditionsVerified':False})
    return found

def _read(path):
    p=Path(path)
    _req(p.is_file() and not p.is_symlink() and 0<p.stat().st_size<=12_000_000,'INPUT_FILE_INVALID')
    return json.loads(p.read_bytes()),_sha(p.read_bytes())

def analyze(r3,paired,r3sha=None,pairedsha=None):
    _req(isinstance(r3,dict) and r3.get('schema')=='BGXAI_WEAPON_NATIVE_ITM_R3_READONLY'
         and r3.get('status')=='ITM_NATIVE_ALL_ITEMS_RAW_READ' and r3.get('sourceKind')=='CURRENT_GAME'
         and r3.get('gameModified') is False,'R3_NOT_VERIFIED_READONLY')
    _req(r3.get('executable') is False and r3.get('dispatchAuthorized') is False
         and r3.get('weaponSwitchAuthorized') is False,'R3_HAS_UNEXPECTED_DISPATCH')
    _req(all(r3.get(k) is False for k in MANDATORY_FLAGS),'R3_CAPABILITY_FLAGS_UNEXPECTED')
    _req(r3.get('missingItemsOrLinkedSpells')==[],'R3_HAS_MISSING_RESOURCES')
    _req(isinstance(paired,dict) and paired.get('status')=='R1_R2_LIVE_PAIRED_READONLY'
         and paired.get('pairedActions')==10 and paired.get('loadoutResrefsConstantAcrossSnapshots') is True,
         'R1_R2_PAIR_UNTRUSTED')
    actor=paired.get('actor')
    _req(_finite_int(actor,0,2147483647) and
         r3.get('r2SnapshotSummary',{}).get('lastActor')==actor and
         r3['r2SnapshotSummary'].get('lastSeq')==10,'ACTOR_OR_SESSION_MISMATCH')
    gear=paired.get('gearSnapshotRaw')
    _req(isinstance(gear,dict) and len(gear.get('quickWeapons',[]))==4
         and len(gear.get('quivers',[]))==4,'GEAR_INCOMPLETE')
    weapons={w['index']:w.get('resrefRaw') for w in gear['quickWeapons']}
    ammo={w['index']:w.get('resrefRaw') for w in gear['quivers']}
    _req(set(weapons)==set(SLOTS) and set(ammo)=={11,12,13,14},'GEAR_SLOT_INDEX_MISMATCH')
    for slot,name in {**weapons,**ammo}.items():
        _req(name is None or _ref(name),'GEAR_RESREF_INVALID:'+str(slot))
        if name is not None: _item(r3,name)
    hand=gear.get('offhand',{})
    _req(hand.get('index')==9 and (hand.get('resrefRaw') is None or _ref(hand['resrefRaw'])),'OFFHAND_INVALID')
    if hand.get('resrefRaw'):_item(r3,hand['resrefRaw'])
    aps=paired.get('selectedSnapshotsBySlotRaw',{})
    _req(isinstance(aps,dict),'APR_SNAPSHOTS_MISSING')
    sampled={}
    for s,entries in aps.items():
        sn=int(s)
        _req(sn in {*SLOTS,11,12,13,14} and isinstance(entries,list) and entries,'APR_SLOT_BAD')
        codes={x.get('aprRaw') for x in entries}
        _req(len(codes)==1 and next(iter(codes)) in APR_DEC,'APR_RAW_CODES_INCONSISTENT')
        _req(all(x.get('resrefRaw')==(weapons.get(sn) if sn in SLOTS else ammo.get(sn)) for x in entries),
             'APR_SNAPSHOT_ITEM_MISMATCH')
        sampled[sn]={'raw':next(iter(codes)),'decodedIfStandard':APR_DEC[next(iter(codes))],
                     'samplingStatus':'CURRENT_SELECTED_ONLY_NOT_OTHER_SLOT_PROJECTION'}
    _req(r3.get('requestedItems') and set(r3['requestedItems'])==set(r3['items']), 'R3_REQUESTED_RESREF_MISMATCH')
    for key in ('WSPATCK','CLSWPBON'):
        tbl=r3.get('aprtables',{}).get(key, {})
        _req(tbl.get('contentsParsed') is True and tbl.get('provenance',{}).get('origin') in
             ('CURRENT_GAME_BIFF','CURRENT_GAME_OVERRIDE'),'APR_TABLE_NOT_FROM_CURRENT_GAME:'+key)
    bow_ammo=[]
    for slot,rr in ammo.items():
        if rr is None:continue
        it,_=_item(r3,rr)
        for a in it['abilities']:
            if a['attackTypeRaw']==2 and a['launcherRequiredRaw']==1:
                bow_ammo.append({'slot':slot,'resref':rr,'abilityIndex':a['abilityIndex'],'ability':a})
    candidates=[]
    for slot in sorted(weapons):
        name=weapons[slot]
        if name is None:
            candidates.append({'slot':slot,'item':None,'status':'EMPTY','executable':False})
            continue
        item,prov=_item(r3,name)
        abilities=item['abilities']; _req(abilities,'NO_USABLE_WEAPON_ABILITY:'+name)
        ab=abilities[0]
        mode={1:'MELEE',4:'RANGED_LAUNCHER',2:'PROJECTILE'}.get(ab['attackTypeRaw'],'UNKNOWN')
        if mode=='RANGED_LAUNCHER':
            reference=[{'ammoSlot':a['slot'],'ammo':a['resref'],'baseDamageMean':_base(a['ability']),
                        'pairProof':'TYPE_MATCH_ONLY_NOT_ENGINE_VERIFIED'} for a in bow_ammo]
            rawbase=reference[0]['baseDamageMean'] if len(reference)==1 else None
            possibleAPR=next(((s,p) for s,p in sampled.items() if s in ammo and ammo[s] in [a['resref'] for a in bow_ammo]),None)
        else:
            reference=[];rawbase=_base(ab);possibleAPR=(slot,sampled[slot]) if slot in sampled else None
        fx=_effects(item)
        flat=[{'keyModifierRaw':e.get('parameter1Raw'),'typeRaw':e.get('parameter2Raw'),
               'timingRaw':e.get('timingRaw')} for e in fx if e.get('opcodeRaw')==1 and e.get('parameter2Raw')==1]
        special=[]
        for a in abilities:
            special.extend({'opcodeRaw':e['opcodeRaw'],'resourceRaw':e.get('resourceRaw'),
                            'probability1Raw':e.get('probability1Raw')} for e in a.get('effects',[]))
        sampledcode=possibleAPR[1] if possibleAPR else None
        sampledDpr=round(rawbase*sampledcode['decodedIfStandard'],4) if (rawbase is not None and sampledcode is not None) else None
        candidates.append({'slot':slot,'item':name,'mode':mode,'source':prov['origin'],
         'twoHandedFlagRaw':item.get('twoHandedFlagRaw'),
         'proficiencyIdRaw':item.get('proficiencyIdRaw'),
         'minStrengthRaw':item.get('minStrengthRaw'),
         'baseWeaponAbility':{'attackTypeRaw':ab['attackTypeRaw'],'speedRaw':ab['speedRaw'],
            'rangeRaw':ab['rangeRaw'],'thac0BonusRaw':ab['thac0BonusRaw'],
            'diceCountRaw':ab['diceCountRaw'],'diceSidesRaw':ab['diceSidesRaw'],
            'damageBonusRaw':ab['damageBonusRaw']},
         'conditionalAmmoCandidates':reference,'staticBaseDamageMeanWithoutStatsOrEffects':rawbase,
         'fixedAPRByEquippedEffectRaw':flat,'sampledAPRAfterSelection':sampledcode,
         'staticBaseDamageTimesSampledAPR_NotDPS':sampledDpr,
         'specialHitEffectsUnvalued':special,'potentialItemLossRisks':_item_loss_risks(r3,name,abilities),
         'equippedEffectOpcodesRaw':[e['opcodeRaw'] for e in fx],
         'offhandShieldMayBeSuppressed':bool(item.get('twoHandedFlagRaw') and hand.get('resrefRaw')),
         'status':'STATIC_ONLY_ABILITY_AND_AMMO_NOT_VALIDATED_FOR_SWITCH',
         'executable':False,'dispatchAuthorized':False})
    spellEvidence={key:[{'opcodeRaw':e.get('opcodeRaw'),'resourceRaw':e.get('resourceRaw')}
                      for ab in ent.get('spell',{}).get('abilities',[]) for e in ab.get('effects',[])]
                   for key,ent in r3.get('linkedSpells',{}).items()}
    return {'schema':'BGXAI_R3_V3V4V5_STATIC_EVIDENCE_V1','status':'STATIC_CANDIDATES_READY_PRIORITY_AND_DISPATCH_HOLD',
     'sourceHashes':{'R3JSON':r3sha,'R1R2PairedJSON':pairedsha},'actorId':actor,'pairedActions':10,
     'gameFilesModified':False,'itemHashes':{name:v['provenance']['sha256'] for name,v in r3['items'].items()},
     'candidates':candidates,'offhandRaw':hand,'linkedSpellEffectsRaw':spellEvidence,
     'aprTables':{n:{'origin':r3['aprtables'][n]['provenance']['origin'],
                     'sha256':r3['aprtables'][n]['provenance']['sha256'],
                     'rows':r3['aprtables'][n]['table']['rowCount']} for n in ('WSPATCK','CLSWPBON')},
     'unverified':['CURRENT_SELECTED_ONLY_APR_OTHER_SLOTS_NOT_RECALCULATED',
         'WSPATCK_ACTOR_KIT_LEVEL_PROFICIENCY_ROW_NOT_BOUND',
         'CLASS_KIT_ACTIVE_BUFFS_FINGERPRINT_NOT_READ',
         'BONUS_DAMAGE_AND_HIT_CHANCE_NOT_EFFECTIVE',
         'LAUNCHER_AMMO_EQUIVALENCE_AND_ABILITY_NOT_ENGINE_PROVEN',
         'ITEM_RESTRICTIONS_OPCODE_319_AND_PROFICIENCY_NOT_PROVEN',
         'ON_HIT_SPELL_EFFECTS_AND_IMMUNITIES_NOT_MODELED',
         'CURRENT_TARGET_ENEMY_RESISTANCES_NOT_KNOWN',
         'OFFHAND_SHIELD_WHILE_TWO_HANDED_NOT_APPLIED_VERIFIED',
         'MANUAL_EPS_ACTION_ORIGIN_AND_SAFE_QUEUE_BOUNDARY_NOT_PROVEN'],
     'priorityAvailable':False,'weaponSwitchAuthorized':False,'dispatchAuthorized':False,
     'executable':False,'ordersSent':0,'currentActionPreserved':True,
     'note':'staticBaseDamageTimesSampledAPR_NotDPS ignores enemy defenses, damage bonuses, strength, effects and queue; NOT an order/ranking'}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--r3',required=True)
    ap.add_argument('--paired',required=True)
    ap.add_argument('--out')
    args=ap.parse_args()
    r3,s1=_read(args.r3);paired,s2=_read(args.paired)
    payload=analyze(r3,paired,s1,s2)
    data=json.dumps(payload,ensure_ascii=False,indent=2)+'\n'
    if args.out:
        dest=Path(args.out); _req(not dest.is_symlink(),'OUTPUT_SYMLINK')
        dest.write_text(data,encoding='utf-8')
    else:print(data,end='')
if __name__=='__main__':main()
