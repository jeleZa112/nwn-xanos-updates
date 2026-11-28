local M=dofile("BGXAI/BUILD/WEAPON_INVENTORY_PRIORITY_V4_20261126/BGXAI_BACKPACK16_PRIORITY_RO_V4.lua")
local n=0
local function test(name,fn)
 local ok,e=pcall(fn);assert(ok,name..": "..tostring(e));n=n+1;print("PASS "..name)
end
local function item(s,name)
 return {slot=s,status="PRESENT_RAW",resref=name,flagsRaw=0,
  useCount1Raw=0,useCount2Raw=0,useCount3Raw=0}
end
local function data()
 local bag={status="BACKPACK16_RAW_NOT_INSTANCE_PROOF",actorId=123,slots={}}
 for s=18,33 do bag.slots[s]={slot=s,status="EMPTY"} end
 bag.slots[18]=item(18,"HAMM01")
 local quick={}
 for s=35,38 do quick[s]={slot=s,status="EMPTY"} end
 quick[35]=item(35,"BOW05")
 local other={}
 for s=0,17 do other[s]={slot=s,status="EMPTY"} end
 other[34]={slot=34,status="EMPTY"}
 local scene={actorId=123,tick=100,targetResref="GIBBER",
  snapshotId="EET-run-1",itemModelProvenance="V3_V4_V5",
  targetHostilityVerified=true,targetIdentityStable=true,
  sameAreaVerified=true,protectionEvidenceVerified=true,
  currentWeaponScoreVerified=true,currentWeaponScore=3,
  weaponSlotCapacity=4,selectedWeaponStillSame=true,
  currentEquipmentFingerprintStable=true,r37ActionContextStable=true}
 local candidates={{sourceSlot=18,resref="HAMM01",
  predictedUtility=9,snapshotId="EET-run-1",modelProvenance="V3_V4_V5",
  usabilityVerified=true,identifiedVerified=true,notCursedVerified=true,
  notQuestItemVerified=true,offhandCompatibilityVerified=true,
  ammoAndLauncherVerified=true,protectionsAccountedVerified=true}}
 return bag,quick,other,scene,candidates
end
local function run(b,q,o,s,c) return M.plan(b,q,o,s,c) end
local function contract(x)
 assert(x.readOnly and x.sourceOnly and x.executable==false and
  x.ordersSent==0 and x.localsWritten==0 and
  x.weaponSwitchAuthorized==false and x.dispatchAuthorized==false and
  x.inventoryMoveAuthorized==false and x.itemTransferSemanticsVerified==false and
  x.engineFinalAlternativeStatsVerified==false and
  x.manualEpsOriginVerified==false and x.safeActionBoundaryVerified==false and
  x.fullItemInstanceIdentityVerified==false and x.gameModified==false)
end
test("dryrun_valid_unique_hammer",function()
 local b,q,o,s,c=data();local x=run(b,q,o,s,c)
 assert(x.status=="ADVISE_BACKPACK16_TO_EMPTY_QUICKSLOT_DRYRUN_ONLY"
   and x.sourceSlot==18 and x.targetSlot==36
   and x.topLevelResrefOccurrences==1
   and x.entireInventoryUniquenessVerified==false)
 contract(x)
end)
test("fails_closed_nil",function()local x=run();assert(x.status=="HOLD_INPUT_SNAPSHOT_INCOMPLETE");contract(x)end)
test("rejects_wrong_v1_20_slot_map",function()
 local b,q,o,s,c=data();b.slots[15]={slot=15,status="EMPTY"}
 local x=run(b,q,o,s,c);assert(x.status=="HOLD_BACKPACK16_EXTRA_SLOT");contract(x)
end)
test("rejects_candidate_quickitem_slot",function()
 local b,q,o,s,c=data();c[1].sourceSlot=15
 local x=run(b,q,o,s,c);assert(x.status=="HOLD_CANDIDATE_LIST_AMBIGUOUS");contract(x)
end)
test("rejects_duplicate_in_shield_slot",function()
 local b,q,o,s,c=data();o[9]=item(9,"HAMM01")
 local x=run(b,q,o,s,c);assert(x.status=="HOLD_RESREF_DUPLICATED_IN_TOP_LEVEL_SLOTS");contract(x)
end)
test("rejects_duplicate_in_quick_item_slot",function()
 local b,q,o,s,c=data();o[15]=item(15,"HAMM01")
 local x=run(b,q,o,s,c);assert(x.status=="HOLD_RESREF_DUPLICATED_IN_TOP_LEVEL_SLOTS");contract(x)
end)
test("rejects_duplicate_in_magic_slot",function()
 local b,q,o,s,c=data();o[34]=item(34,"HAMM01")
 local x=run(b,q,o,s,c);assert(x.status=="HOLD_RESREF_DUPLICATED_IN_TOP_LEVEL_SLOTS");contract(x)
end)
test("rejects_duplicate_in_quickweapon",function()
 local b,q,o,s,c=data();q[37]=item(37,"HAMM01")
 local x=run(b,q,o,s,c);assert(x.status=="HOLD_RESREF_DUPLICATED_IN_TOP_LEVEL_SLOTS");contract(x)
end)
test("rejects_unknown_other_slot",function()
 local b,q,o,s,c=data();o[9]=nil
 local x=run(b,q,o,s,c);assert(x.status=="HOLD_REMAINING_EQUIPMENT_INCOMPLETE");contract(x)
end)
test("no_overwrite_quickslots",function()
 local b,q,o,s,c=data()
 for i=36,38 do q[i]=item(i,"SW1H01")end
 local x=run(b,q,o,s,c);assert(x.status=="HOLD_ALL_PERMITTED_QUICKSLOTS_OCCUPIED");contract(x)
end)
test("only_2_permitted_quickslots",function()
 local b,q,o,s,c=data();s.weaponSlotCapacity=2;q[36]=item(36,"SW1H04")
 local x=run(b,q,o,s,c);assert(x.status=="HOLD_ALL_PERMITTED_QUICKSLOTS_OCCUPIED");contract(x)
end)
test("rejects_stale_action_context",function()
 local b,q,o,s,c=data();s.r37ActionContextStable=false
 local x=run(b,q,o,s,c);assert(x.status=="HOLD_EQUIPMENT_OR_ACTION_CONTEXT_DRIFT");contract(x)
end)
test("rejects_unknown_enemy",function()
 local b,q,o,s,c=data();s.targetHostilityVerified=false
 local x=run(b,q,o,s,c);assert(x.status=="HOLD_SCENE_OR_MODEL_NOT_PROVEN");contract(x)
end)
test("rejects_unproven_poison_effects",function()
 local b,q,o,s,c=data();c[1].protectionsAccountedVerified=false
 local x=run(b,q,o,s,c);assert(x.status=="HOLD_CANDIDATE_NOT_VERIFIED");contract(x)
end)
test("rejects_cursed_weapon",function()
 local b,q,o,s,c=data();c[1].notCursedVerified=false
 local x=run(b,q,o,s,c);assert(x.status=="HOLD_CANDIDATE_NOT_VERIFIED");contract(x)
end)
test("rejects_ammo_pair",function()
 local b,q,o,s,c=data();c[1].ammoAndLauncherVerified=false
 local x=run(b,q,o,s,c);assert(x.status=="HOLD_CANDIDATE_NOT_VERIFIED");contract(x)
end)
test("no_meaningful_gain",function()
 local b,q,o,s,c=data();c[1].predictedUtility=4
 local x=run(b,q,o,s,c);assert(x.status=="KEEP_CURRENT_NO_MEANINGFUL_GAIN");contract(x)
end)
test("rejects_ambiguous_candidate_list",function()
 local b,q,o,s,c=data();c[2]=c[1]
 local x=run(b,q,o,s,c);assert(x.status=="HOLD_CANDIDATE_LIST_AMBIGUOUS");contract(x)
end)
test("rejects_bad_target_area",function()
 local b,q,o,s,c=data();s.sameAreaVerified=false
 local x=run(b,q,o,s,c);assert(x.status=="HOLD_SCENE_OR_MODEL_NOT_PROVEN");contract(x)
end)
test("never_executes_even_if_caller_claims_safe",function()
 local b,q,o,s,c=data();s.manualEpsOriginVerified=true
 s.safeActionBoundaryVerified=true;s.engineFinalAlternativeStatsVerified=true
 local x=run(b,q,o,s,c);assert(x.status=="ADVISE_BACKPACK16_TO_EMPTY_QUICKSLOT_DRYRUN_ONLY");contract(x)
end)
-- V3 already uses zero hysteresis for a provably useless current attack.
-- The backpack planner must match that rule, without granting dispatch.
test("verified_target_immune_allows_small_positive_backpack_alternative",function()
 local b,q,o,s,c=data()
 s.currentWeaponScore=0
 s.currentWeaponUnusableVerified=true
 s.currentWeaponUnusableReason="VERIFIED_TARGET_WEAPON_IMMUNITY"
 c[1].predictedUtility=0.25
 local x=run(b,q,o,s,c)
 assert(x.status=="ADVISE_BACKPACK16_TO_EMPTY_QUICKSLOT_DRYRUN_ONLY"
    and x.scoreMargin==0 and x.estimatedGain==0.25)
 contract(x)
end)
test("unproven_zero_does_not_bypass_hysteresis",function()
 local b,q,o,s,c=data()
 s.currentWeaponScore=0
 c[1].predictedUtility=0.25
 local x=run(b,q,o,s,c)
 assert(x.status=="KEEP_CURRENT_NO_MEANINGFUL_GAIN")
 contract(x)
end)
test("caller_claim_without_v3_reason_is_hold",function()
 local b,q,o,s,c=data()
 s.currentWeaponScore=0
 s.currentWeaponUnusableVerified=true
 c[1].predictedUtility=0.25
 local x=run(b,q,o,s,c)
 assert(x.status=="HOLD_CURRENT_WEAPON_UNUSABLE_EVIDENCE_INCOMPLETE")
 contract(x)
end)
test("unverified_reason_is_hold",function()
 local b,q,o,s,c=data()
 s.currentWeaponScore=0
 s.currentWeaponUnusableVerified=false
 s.currentWeaponUnusableReason="VERIFIED_TARGET_WEAPON_IMMUNITY"
 local x=run(b,q,o,s,c)
 assert(x.status=="HOLD_CURRENT_WEAPON_UNUSABLE_EVIDENCE_INCOMPLETE")
 contract(x)
end)
test("inconsistent_positive_current_score_is_hold",function()
 local b,q,o,s,c=data()
 s.currentWeaponScore=3
 s.currentWeaponUnusableVerified=true
 s.currentWeaponUnusableReason="VERIFIED_TARGET_WEAPON_IMMUNITY"
 local x=run(b,q,o,s,c)
 assert(x.status=="HOLD_CURRENT_WEAPON_STATUS_INCONSISTENT")
 contract(x)
end)
test("known_useless_but_negative_alternative_is_hold",function()
 local b,q,o,s,c=data()
 s.currentWeaponScore=-3
 s.currentWeaponUnusableVerified=true
 s.currentWeaponUnusableReason="VERIFIED_NO_EFFECTIVE_DAMAGE_OR_EFFECT"
 c[1].predictedUtility=-0.5
 local x=run(b,q,o,s,c)
 assert(x.status=="HOLD_NO_POSITIVE_BACKPACK_ALTERNATIVE")
 contract(x)
end)
test("unknown_unusable_reason_cannot_bypass_threshold",function()
 local b,q,o,s,c=data()
 s.currentWeaponScore=0
 s.currentWeaponUnusableVerified=true
 s.currentWeaponUnusableReason="POSSIBLY_RESISTANT"
 c[1].predictedUtility=0.25
 local x=run(b,q,o,s,c)
 assert(x.status=="HOLD_CURRENT_WEAPON_UNUSABLE_EVIDENCE_INCOMPLETE")
 contract(x)
end)
-- Compose the ALREADY EXISTING V3 target ranker with the V4 16-slot planner.
-- This is a modeled snapshot; all approvals remain forbidden.
local V3=dofile('BGXAI/patchsets/ranged_fighter_guarded_20261119/BGXAI_WEAPON_PRIORITY_LUA_V3.lua')
local function v3v4()
 local b,q,o,s,c=data()
 s.snapshotId='SNAP1';s.targetActorId=222
 c[1].snapshotId='SNAP1';c[1].predictedUtility=nil
 local vm={frame={tick=100,area='AR001',actorId='123',enemyId='222',
    snapshotId='SNAP1',equipmentFingerprint='EQ1',protectionFingerprint='PR1',
    combatFingerprint='C1',selectedWeaponId='BOW',
    captureContract='COMPLETE_EFFECTIVE_SNAPSHOT',
    completeEquipmentObserved=true,completeQuiverObserved=true,
    completeTargetObserved=true},
   actor={actorId='123',area='AR001',currentTargetId='222',
    selectedWeaponId='BOW',observationVerified=true,handsMode='SINGLE',
    nearRangedEnemy=false,canSustainMelee=true,pathSafeVerified=true,
    manualOrderActive=false,epsBusy=false,healingReserved=false,
    currentlyCasting=false,originVerified='AI',
    traitProfile={verified=true,snapshotId='SNAP1',modFingerprint='EET',
     activeClassesVerified=true,raceClassKitBonusesIncluded=true}},
   enemy={enemyId='222',area='AR001',observationVerified=true,
    hostileVerified=true,visibleVerified=true,armorClass=0,
    protections={snapshotId='SNAP1',observed=true,
     immuneDamageTypes={},minimumEnchantment=0,magicalWeaponsBlocked=false,
     normalWeaponsBlocked=false,missilesBlocked=false,
     resistance={SLASHING=0,PIERCING=0,CRUSHING=0,MISSILE=0}}},
   quickslotIds={'BOW',false,false,false},
   weapons={{id='BOW',slot='QUICKSLOT',quickslotIndex=0,resRef='BOW05',
    snapshotId='SNAP1',modFingerprint='EET',mode='RANGED',damageType='MISSILE',
    weaponGroup='LONG_BOW',usableVerified=true,equippedWeaponSlotVerified=true,
    ammoVerified=true,ammunitionModel='SELF',ammoCount=20,
    inRange=true,rangedClosePenaltyAccounted=true,
    finalTHAC0=20,avgDamageOnHit=2,apr=1,enchantment=0,magical=false,
    switchCost=0,resourceCost=0,retaliationRisk=0,movementCost=0,
    extraEffectValue=0,combatCostsVerified=true,statBasis='FINAL_EFFECTIVE',
    finalCombatStatsVerified=true,
    allRaceClassKitProficiencyBonusesIncluded=true}}}
 c[1].weaponModel={id='BAG_HAMM',slot='BACKPACK',sourceSlot=18,
   resRef='HAMM01',snapshotId='SNAP1',modFingerprint='EET',
   modelProvenance='V3_V4_V5',
   counterfactualBasis='MODEL_ONLY_NOT_NATIVE_EFFECTIVE',
   alternativeEffectiveStatsLiveVerified=false,
   usableVerified=true,identifiedVerified=true,notCursedVerified=true,
   notQuestItemVerified=true,offhandCompatibilityVerified=true,
   ammoAndLauncherVerified=true,protectionsAccountedVerified=true,
   mode='MELEE',weaponGroup='WAR_HAMMER',damageType='CRUSHING',
   inRange=true,finalTHAC0=10,apr=2,avgDamageOnHit=7,
   enchantment=0,magical=false,statBasis='FINAL_EFFECTIVE',
   finalCombatStatsVerified=true,
   allRaceClassKitProficiencyBonusesIncluded=true,
   combatCostsVerified=true,switchCost=0,resourceCost=0,
   retaliationRisk=0,movementCost=0,extraEffectValue=0}
 return b,q,o,s,c,vm
end
local function linked(b,q,o,s,c,vm,p)
 return M.planWithV3(b,q,o,s,c,vm,p,V3)
end
local function stable(b,q,o,s,c,vm)
 local first=linked(b,q,o,s,c,vm,nil)
 assert(first.status=='HOLD_V3_V4_TARGET_RANKING_UNSTABLE' and
        type(first.v3Next)=='table')
 contract(first)
 s.tick=101;vm.frame.tick=101
 return linked(b,q,o,s,c,vm,first.v3Next)
end
test('v3_v4_same_target_backpack_advice_only',function()
 local b,q,o,s,c,vm=v3v4()
 local x=stable(b,q,o,s,c,vm)
 assert(x.status=='ADVISE_BACKPACK16_TO_EMPTY_QUICKSLOT_DRYRUN_ONLY')
 assert(x.sourceSlot==18 and x.targetSlot==36 and x.candidateResref=='HAMM01')
 assert(x.v3V4Link=='SAME_ACTOR_TARGET_BACKPACK_MODEL_ONLY')
 assert(x.estimatedGain>7 and x.scoreMargin==2)
 assert(c[1].predictedUtility==nil)
 contract(x)
end)
test('v3_v4_target_id_changed_hold',function()
 local b,q,o,s,c,vm=v3v4()
 s.targetActorId=333
 local x=linked(b,q,o,s,c,vm,nil)
 assert(x.status=='HOLD_V3_V4_ACTOR_TARGET_FRAME_MISMATCH')
 contract(x)
end)
test('v3_v4_external_score_cannot_overwrite_v3',function()
 local b,q,o,s,c,vm=v3v4()
 c[1].predictedUtility=999
 local x=stable(b,q,o,s,c,vm)
 assert(x.status=='HOLD_V3_V4_EXTERNAL_OR_MISMATCHED_SCORE')
 contract(x)
end)
test('v3_v4_unknown_counterfactual_apr_hold',function()
 local b,q,o,s,c,vm=v3v4()
 c[1].weaponModel.apr=nil
 local x=stable(b,q,o,s,c,vm)
 assert(x.status=='HOLD_V3_V4_BACKPACK_TARGET_MODEL_UNVERIFIED')
 contract(x)
end)
test('v3_v4_quickslot_identity_mismatch_hold',function()
 local b,q,o,s,c,vm=v3v4()
 vm.weapons[1].resRef='WRONG'
 local x=linked(b,q,o,s,c,vm,nil)
 assert(x.status=='HOLD_V3_V4_QUICKSLOT_IDENTITY_DRIFT')
 contract(x)
end)
test('v3_v4_verified_current_missile_immunity_allows_positive_hammer',function()
 local b,q,o,s,c,vm=v3v4()
 vm.enemy.protections.missilesBlocked=true
 local x=stable(b,q,o,s,c,vm)
 assert(x.status=='ADVISE_BACKPACK16_TO_EMPTY_QUICKSLOT_DRYRUN_ONLY')
 assert(x.scoreMargin==0 and x.estimatedGain>0)
 contract(x)
end)
test('v3_v4_caller_current_score_cannot_launder_gain',function()
 local b,q,o,s,c,vm=v3v4()
 s.currentWeaponScore=99999;s.currentWeaponScoreVerified=true
 local x=stable(b,q,o,s,c,vm)
 assert(x.status=='ADVISE_BACKPACK16_TO_EMPTY_QUICKSLOT_DRYRUN_ONLY')
 assert(x.estimatedGain>7)
 contract(x)
end)
-- Regression: evaluate the backpack against the BEST available quickslot,
-- not just the currently selected (possibly depleted or immune) weapon.
local function equipped_sword(b,q,o,s,c,vm,apr,thac0,dmg)
 q[36]=item(36,'SW1H04')
 vm.quickslotIds[2]='SWORD'
 local w={}
 for k,v in pairs(vm.weapons[1]) do w[k]=v end
 w.id='SWORD';w.quickslotIndex=1;w.resRef='SW1H04'
 w.mode='MELEE';w.damageType='SLASHING';w.weaponGroup='LONG_SWORD'
 w.finalTHAC0=thac0;w.apr=apr;w.avgDamageOnHit=dmg
 w.enchantment=1;w.magical=true
 vm.weapons[2]=w
end
test('already_equipped_stronger_than_backpack_no_inventory_move',function()
 local b,q,o,s,c,vm=v3v4()
 equipped_sword(b,q,o,s,c,vm,4,3,10)
 local x=stable(b,q,o,s,c,vm)
 assert(x.status=='PREFER_ALREADY_EQUIPPED_QUICKSLOT_NO_INVENTORY_MOVE')
 assert(x.bestEquippedWeaponId=='SWORD' and x.suggestedQuickslotIndex==1)
 assert(x.bestEquippedScoreModel>x.selectedScoreModel)
 contract(x)
end)
test('backpack_stronger_than_all_already_equipped',function()
 local b,q,o,s,c,vm=v3v4()
 equipped_sword(b,q,o,s,c,vm,2,12,4)
 local x=stable(b,q,o,s,c,vm)
 assert(x.status=='ADVISE_BACKPACK16_TO_EMPTY_QUICKSLOT_DRYRUN_ONLY')
 assert(x.bestEquippedWeaponId=='SWORD' and x.sourceSlot==18)
 assert(x.estimatedGain>x.scoreMargin)
 contract(x)
end)
test('immune_selected_still_prefers_effective_equipped_over_weak_backpack',function()
 local b,q,o,s,c,vm=v3v4()
 vm.enemy.protections.missilesBlocked=true
 equipped_sword(b,q,o,s,c,vm,2,7,7)
 local x=stable(b,q,o,s,c,vm)
 assert(x.status=='PREFER_ALREADY_EQUIPPED_QUICKSLOT_NO_INVENTORY_MOVE')
 assert(x.bestEquippedScoreModel>6)
 contract(x)
end)
-- R37's EXISTING single-callback raw schema is index/itemResrefRaw,
-- not slot/resrefRaw; its offhand is a singleton, never an array.
local R37Bag=dofile('BGXAI/BUILD/WEAPON_INVENTORY_CORRECTED_V3_20261126/BGXAI_BACKPACK16_R37_RO_V3.lua')
local function r37_fixture()
 local bag,quick,other,scene,candidates,v3Scene=v3v4()
 local slots={}
 for slot=0,38 do
  local x=slot>=18 and slot<=33 and bag.slots[slot] or
          slot>=35 and quick[slot] or other[slot]
  slots[slot]=x
 end
 local items={get=function(self,slot)
  local x=slots[slot]
  if x==nil or x.status=='EMPTY' then return nil end
  return {cResRef={get=function()return x.resref end},m_flags=0,
   m_useCount1=0,m_useCount2=0,m_useCount3=0}
 end}
 local actor={m_id=123,m_equipment={m_items=items}}
 local function raw(slot,kind,ordinal)
  local x=slots[slot]
  local t={index=slot,kind=kind,ordinal=ordinal,
    access=x.status=='EMPTY' and 'NULL' or 'OBJECT_RETURNED_UNVERIFIED'}
  if x.status~='EMPTY' then
   t.itemResrefRaw=x.resref
   t.resrefAccess='RAW_RESREF_RETURNED_UNVERIFIED'
   t.useCount1Raw=0;t.useCount2Raw=0;t.useCount3Raw=0;t.flagsRaw=0
  end
  return t
 end
 local obs={schema='BGXAI_R27_SINGLE_CALLBACK_SELECTED_RO_V1',
  status='CURRENT_SELECTED_SAME_CALLBACK_SOURCE_CANDIDATE',
  readOnly=true,ordersSent=0,dispatchAuthorized=false,
  weaponSwitchAuthorized=false,sameLuaListenerInvocation=true,
  rawInventoryDoubleReadConsistent=true,
  selectedDerivedStatsDoubleReadConsistent=true,
  queueSnapshotStable=true,actionContextSnapshotStable=true,
  actionOriginVerified=false,manualEpsQueueVerified=false,
  actor=123,partyIndex=1,actionRaw=105,selectedWeaponRaw=35,
  selectedAbilityRaw=0,queuedActionsRaw=0,currentScriptNumberRaw=4,
  quickWeaponsRaw={},quiversRaw={}}
 for i=1,4 do
  obs.quickWeaponsRaw[i]=raw(34+i,'QUICKWEAPON',i-1)
  obs.quiversRaw[i]=raw(10+i,'QUIVER',i-1)
 end
 obs.offhandRaw=raw(9,'OFFHAND_OR_SHIELD',0)
 local ctx=function()
  return {actorId=123,actionRaw=105,selectedWeaponRaw=35,
   selectedAbilityRaw=0,queuedActionsRaw=0,currentScriptNumberRaw=4}
 end
 return actor,obs,ctx,bag,quick,other,scene,candidates,v3Scene,slots
end
test('r37_full_real_top_level_raw_map_for_v4',function()
 local sprite,obs,ctx=r37_fixture()
 local x=R37Bag.captureTopLevel(sprite,obs,ctx)
 assert(x.status=='TOPLEVEL0_38_AND_R37_STABLE_ADVICE_ONLY')
 assert(x.topLevelSlotsCount==39 and x.backpack.slots[18].resref=='HAMM01')
 assert(x.quick[35].resref=='BOW05' and x.other[9].status=='EMPTY')
 assert(x.alternativeAPRVerified==false and x.sameTickProven==false)
 assert(x.dispatchAuthorized==false and x.inventoryMoveAuthorized==false)
end)
test('r37_full_map_rejects_raw_selected_weapon_mismatch',function()
 local sprite,obs,ctx=r37_fixture()
 obs.quickWeaponsRaw[1].itemResrefRaw='SW1H04'
 local x=R37Bag.captureTopLevel(sprite,obs,ctx)
 assert(x.status=='HOLD_TOPLEVEL_R37_GEAR_CHANGED')
 assert(x.dispatchAuthorized==false)
end)
test('r37_full_map_rejects_mutating_item_reads',function()
 local sprite,obs,ctx=r37_fixture()
 local get=sprite.m_equipment.m_items.get
 local seen=0
 sprite.m_equipment.m_items.get=function(self,slot)
  if slot==35 then
   seen=seen+1
   if seen==2 then
    return {cResRef={get=function()return 'SW1H04' end},
      m_flags=0,m_useCount1=0,m_useCount2=0,m_useCount3=0}
   end
  end
  return get(self,slot)
 end
 local x=R37Bag.captureTopLevel(sprite,obs,ctx)
 assert(x.status=='HOLD_TOPLEVEL_ITEM_CHANGED')
 assert(x.dispatchAuthorized==false)
end)
test('r37_to_v3_v4_target_aware_no_new_listener',function()
 local sprite,obs,ctx,b,q,o,s,c,vm=r37_fixture()
 local one=M.planWithR37(sprite,obs,ctx,R37Bag,s,c,vm,nil,V3)
 assert(one.status=='HOLD_V3_V4_TARGET_RANKING_UNSTABLE'
        and type(one.v3Next)=='table')
 contract(one)
 s.tick=101;vm.frame.tick=101
 local x=M.planWithR37(sprite,obs,ctx,R37Bag,s,c,vm,one.v3Next,V3)
 assert(x.status=='ADVISE_BACKPACK16_TO_EMPTY_QUICKSLOT_DRYRUN_ONLY')
 assert(x.r37InventoryMap=='ON_DEMAND_TOPLEVEL0_38_SOURCE_ONLY')
 assert(x.sourceSlot==18 and x.targetSlot==36 and x.candidateResref=='HAMM01')
 assert(x.nativeInventoryInstanceAuthenticated==false)
 contract(x)
end)
test('r37_v4_rejects_laundered_native_or_dispatch_claim',function()
 local sprite,obs,ctx,b,q,o,s,c,vm=r37_fixture()
 local forged={captureTopLevel=function()
  return {status='TOPLEVEL0_38_AND_R37_STABLE_ADVICE_ONLY',
   readOnly=true,sourceOnly=true,dispatchAuthorized=true,
   inventoryMoveAuthorized=false}
 end}
 local x=M.planWithR37(sprite,obs,ctx,forged,s,c,vm,nil,V3)
 assert(x.status=='HOLD_R37_TOPLEVEL_RAW_MAP_UNVERIFIED')
 contract(x)
end)
-- Actual batch delta: enumerate R3 ITM for ALL 16 observed backpack slots;
-- choose a stronger ready weapon even without a backpack candidate; produce
-- one queued, noninterrupting source-only decision for either weapon route.
local function r3_snapshot(raw,weaponName,attackType)
 local map={}
 for slot=0,38 do
  local x=slot>=18 and slot<=33 and raw.backpack.slots[slot] or
          slot>=35 and raw.quick[slot] or raw.other[slot]
  map[tostring(slot)]={slot=slot,status=x.status,resref=x.resref}
 end
 local items={}
 for slot=18,33 do
  local x=raw.backpack.slots[slot]
  if x.status=='PRESENT_RAW' then
   items[x.resref]={item={schema='BGXAI_ITM_RAW_V1',
      abilities={{attackTypeRaw=attackType or 1}}},
      provenance={origin='CURRENT_GAME_BIFF'}}
  end
 end
 return {inventoryLinkSchema='BGXAI_R3_R37_TOPLEVEL_ITM_JOIN_SOURCE_ONLY_V1',
   sourceKind='CURRENT_GAME',status='ITM_NATIVE_ALL_ITEMS_RAW_READ',
   nativeRuntimeInventorySnapshotAuthenticated=false,
   nativeCurrentAlternativeAPRVerified=false,
   dispatchAuthorized=false,inventoryTransferAuthorized=false,
   inventoryRawMap=map,items=items}
end
local function modeled_from(fixture,force)
 local base=fixture[8][1].weaponModel
 return function(slot,observed,itm)
  local w={}
  for k,v in pairs(base) do w[k]=v end
  w.sourceSlot=slot;w.resRef=observed.resref;w.id='BAG_'..tostring(slot)
  if force then force(w) end
  return {status='MODELED_WEAPON_CANDIDATE',abilityIndex=0,weaponModel=w,
   usabilityVerified=true,identifiedVerified=true,notCursedVerified=true,
   notQuestItemVerified=true,offhandCompatibilityVerified=true,
   ammoAndLauncherVerified=true,protectionsAccountedVerified=true}
 end
end
test('ready_slot_better_even_if_backpack_candidates_empty',function()
 local b,q,o,s,c,vm=v3v4()
 equipped_sword(b,q,o,s,c,vm,4,3,10)
 local first=linked(b,q,o,s,{},vm,nil)
 assert(first.status=='HOLD_V3_V4_TARGET_RANKING_UNSTABLE')
 s.tick=101;vm.frame.tick=101
 local x=linked(b,q,o,s,{},vm,first.v3Next)
 assert(x.status=='PREFER_ALREADY_EQUIPPED_QUICKSLOT_NO_INVENTORY_MOVE')
 assert(x.suggestedQuickslotIndex==1 and x.backpackCandidateCount==0)
 contract(x)
end)
test('no_backpack_no_better_ready_keeps_current_without_hold',function()
 local b,q,o,s,c,vm=v3v4()
 local first=linked(b,q,o,s,{},vm,nil)
 assert(first.status=='HOLD_V3_V4_TARGET_RANKING_UNSTABLE')
 s.tick=101;vm.frame.tick=101
 local x=linked(b,q,o,s,{},vm,first.v3Next)
 assert(x.status=='KEEP_CURRENT_NO_BACKPACK_CANDIDATE')
 contract(x)
end)
test('r3_auto_discovers_item_and_scores_without_external_score',function()
 local sprite,obs,ctx,b,q,o,s,c,vm=r37_fixture()
 local raw=R37Bag.captureTopLevel(sprite,obs,ctx)
 local r3=r3_snapshot(raw)
 local fixture={sprite,obs,ctx,b,q,o,s,c,vm}
 local candidates,err=M.prepare16FromR3(raw,r3,modeled_from(fixture))
 assert(err==nil and #candidates==1)
 assert(candidates[1].resref=='HAMM01' and candidates[1].sourceSlot==18)
 assert(candidates[1].predictedUtility==nil)
 local first=M.planWithV3(raw.backpack,raw.quick,raw.other,s,candidates,vm,nil,V3)
 assert(first.status=='HOLD_V3_V4_TARGET_RANKING_UNSTABLE')
 s.tick=101;vm.frame.tick=101
 local final=M.planWithV3(raw.backpack,raw.quick,raw.other,s,candidates,vm,first.v3Next,V3)
 assert(final.status=='ADVISE_BACKPACK16_TO_EMPTY_QUICKSLOT_DRYRUN_ONLY')
 contract(final)
end)
test('r3_enumerates_every_one_of_16_backpack_slots_in_one_batch',function()
 local sprite,obs,ctx,b,q,o,s,c,vm,slots=r37_fixture()
 for i=18,33 do slots[i]=item(i,string.format('H%05d',i)) end
 local raw=R37Bag.captureTopLevel(sprite,obs,ctx)
 assert(raw.status=='TOPLEVEL0_38_AND_R37_STABLE_ADVICE_ONLY')
 local fixture={sprite,obs,ctx,b,q,o,s,c,vm}
 local names,err=M.prepare16FromR3(raw,r3_snapshot(raw),modeled_from(fixture))
 assert(err==nil and #names==16)
 for i=1,16 do assert(names[i].sourceSlot==i+17) end
end)
test('r3_projector_can_skip_nonweapon_without_fake_candidate',function()
 local sprite,obs,ctx=r37_fixture()
 local raw=R37Bag.captureTopLevel(sprite,obs,ctx)
 local names,err=M.prepare16FromR3(raw,r3_snapshot(raw),function()
  return {status='CANNOT_USE_OR_NOT_WEAPON'}
 end)
 assert(err==nil and #names==0)
end)
test('r3_refuses_stale_weapon_map_with_correct_actor_but_wrong_weapon',function()
 local sprite,obs,ctx,b,q,o,s,c,vm=r37_fixture()
 local raw=R37Bag.captureTopLevel(sprite,obs,ctx)
 local r3=r3_snapshot(raw);r3.inventoryRawMap['35'].resref='SW1H04'
 local fixture={sprite,obs,ctx,b,q,o,s,c,vm}
 local x,err=M.prepare16FromR3(raw,r3,modeled_from(fixture))
 assert(x==nil and err=='HOLD_R3_TOPLEVEL_ITEM_CHANGED_OR_UNMAPPED')
end)
test('r3_rejects_forged_native_alternative_stats',function()
 local sprite,obs,ctx,b,q,o,s,c,vm=r37_fixture()
 local raw=R37Bag.captureTopLevel(sprite,obs,ctx)
 local fixture={sprite,obs,ctx,b,q,o,s,c,vm}
 local x,err=M.prepare16FromR3(raw,r3_snapshot(raw),modeled_from(fixture,function(w)
  w.alternativeEffectiveStatsLiveVerified=true end))
 assert(x==nil and err=='HOLD_R3_PROJECTED_WEAPON_NOT_SOURCE_BOUND')
end)
test('r3_actual_itm_attack_type_must_match_mode',function()
 local sprite,obs,ctx,b,q,o,s,c,vm=r37_fixture()
 local raw=R37Bag.captureTopLevel(sprite,obs,ctx)
 local fixture={sprite,obs,ctx,b,q,o,s,c,vm}
 local x,err=M.prepare16FromR3(raw,r3_snapshot(raw,nil,2),modeled_from(fixture))
 assert(x==nil and err=='HOLD_R3_ITEM_ABILITY_MODE_MISMATCH')
end)
test('r3_refuses_unattested_or_partial_resource_audit',function()
 local sprite,obs,ctx,b,q,o,s,c,vm=r37_fixture()
 local raw=R37Bag.captureTopLevel(sprite,obs,ctx)
 local r3=r3_snapshot(raw);r3.status='ITM_NATIVE_PARTIAL_HOLD'
 local fixture={sprite,obs,ctx,b,q,o,s,c,vm}
 local x,err=M.prepare16FromR3(raw,r3,modeled_from(fixture))
 assert(x==nil and err=='HOLD_R3_16_SLOT_INPUT_OR_PROVENANCE_INCOMPLETE')
end)
test('battle_decision_ready_quickslot_never_dispatches',function()
 local sprite,obs,ctx,b,q,o,s,c,vm=r37_fixture()
 local x=M.planBattleDecision({status='PREFER_ALREADY_EQUIPPED_QUICKSLOT_NO_INVENTORY_MOVE',
  readOnly=true,sourceOnly=true,executable=false,dispatchAuthorized=false,
  inventoryMoveAuthorized=false,suggestedQuickslotIndex=1,
  bestEquippedWeaponId='SWORD'},obs,s)
 assert(x.status=='STAGE_DECISION_AWAIT_INDEPENDENT_MANUAL_EPS_ROUND_PROOF')
 assert(x.pendingWeaponChange.kind=='SELECT_ALREADY_EQUIPPED_QUICKSLOT')
 assert(x.pendingWeaponChange.targetSlot==1)
 contract(x)
end)
test('battle_decision_backpack_deferred_when_engine_queue_nonempty',function()
 local sprite,obs,ctx,b,q,o,s,c,vm=r37_fixture()
 obs.queuedActionsRaw=2
 local x=M.planBattleDecision({status='ADVISE_BACKPACK16_TO_EMPTY_QUICKSLOT_DRYRUN_ONLY',
  readOnly=true,sourceOnly=true,executable=false,dispatchAuthorized=false,
  inventoryMoveAuthorized=false,sourceSlot=18,targetSlot=36,
  candidateResref='HAMM01',topLevelResrefOccurrences=1,
  topLevelItemMappingComplete=true},obs,s)
 assert(x.status=='DEFER_KNOWN_NONEMPTY_ACTION_QUEUE')
 assert(x.pendingWeaponChange.kind=='EQUIP_BACKPACK_TO_EMPTY_QUICKSLOT')
 assert(x.pendingWeaponChange.sourceSlot==18 and x.queuedActionsRaw==2)
 assert(x.engineActionCalls==0 and x.actionQueueCleared==false)
 contract(x)
end)
test('battle_decision_forged_authority_or_origin_fails_closed',function()
 local sprite,obs,ctx,b,q,o,s,c,vm=r37_fixture()
 local bad={status='ADVISE_BACKPACK16_TO_EMPTY_QUICKSLOT_DRYRUN_ONLY',
  readOnly=true,sourceOnly=true,executable=false,dispatchAuthorized=true,
  inventoryMoveAuthorized=false,sourceSlot=18,targetSlot=36,
  candidateResref='HAMM01',topLevelResrefOccurrences=1,
  topLevelItemMappingComplete=true}
 local x=M.planBattleDecision(bad,obs,s)
 assert(x.status=='HOLD_BATTLE_EVIDENCE_OR_ACTION_CONTEXT_INCOMPLETE')
 contract(x)
 bad.dispatchAuthorized=false;obs.actionOriginVerified=true
 local y=M.planBattleDecision(bad,obs,s)
 assert(y.status=='HOLD_BATTLE_EVIDENCE_OR_ACTION_CONTEXT_INCOMPLETE')
 contract(y)
end)
test('autobatch_known_busy_skips_39_slot_scan_and_rank_completely',function()
 local sprite,obs,ctx,b,q,o,s,c,vm=r37_fixture()
 obs.queuedActionsRaw=3
 local called=0
 local reader={captureTopLevel=function()called=called+1;error('scan forbidden')end}
 local x=M.planAutoBatch(sprite,obs,ctx,reader,{},function()error('projection')end,
                        s,vm,nil,V3)
 assert(x.status=='PRESERVE_KNOWN_ACTION_QUEUE_NO_SCAN')
 assert(x.knownQueuedActions==3 and x.inventoryCaptureCalls==0)
 assert(x.scorerCalls==0 and called==0)
 contract(x)
end)
test('autobatch_automatically_discovers_and_stages_backpack_weapon',function()
 local sprite,obs,ctx,b,q,o,s,c,vm=r37_fixture()
 local raw=R37Bag.captureTopLevel(sprite,obs,ctx)
 local r3=r3_snapshot(raw)
 local fixture={sprite,obs,ctx,b,q,o,s,c,vm}
 local project=modeled_from(fixture)
 local initial=M.planAutoBatch(sprite,obs,ctx,R37Bag,r3,project,s,vm,nil,V3)
 assert(initial.status=='HOLD_AUTOBATCH_TARGET_RANKING_UNSTABLE')
 assert(initial.candidateCount==1 and type(initial.v3Next)=='table')
 s.tick=101;vm.frame.tick=101
 local final=M.planAutoBatch(sprite,obs,ctx,R37Bag,r3,project,s,vm,initial.v3Next,V3)
 assert(final.status=='STAGE_DECISION_AWAIT_INDEPENDENT_MANUAL_EPS_ROUND_PROOF')
 assert(final.pendingWeaponChange.kind=='EQUIP_BACKPACK_TO_EMPTY_QUICKSLOT')
 assert(final.pendingWeaponChange.sourceSlot==18)
 assert(final.pendingWeaponChange.targetSlot==36)
 assert(final.candidateCount==1 and final.inventoryCaptureCalls==1)
 assert(final.r3ItemSourcesCrosschecked and final.nativeEffectiveAlternateAprVerified==false)
 contract(final)
end)
test('autobatch_empty_eligible_candidates_keeps_weapon',function()
 local sprite,obs,ctx,b,q,o,s,c,vm=r37_fixture()
 local r3=r3_snapshot(R37Bag.captureTopLevel(sprite,obs,ctx))
 local skip=function()return {status='CANNOT_USE_OR_NOT_WEAPON'}end
 local initial=M.planAutoBatch(sprite,obs,ctx,R37Bag,r3,skip,s,vm,nil,V3)
 assert(initial.status=='HOLD_AUTOBATCH_TARGET_RANKING_UNSTABLE')
 s.tick=101;vm.frame.tick=101
 local x=M.planAutoBatch(sprite,obs,ctx,R37Bag,r3,skip,s,vm,initial.v3Next,V3)
 assert(x.status=='KEEP_CURRENT_ACTION_OR_UNPROVEN_GAIN')
 assert(x.candidateCount==0)
 contract(x)
end)
test('autobatch_forged_r3_item_map_blocks_all_scoring',function()
 local sprite,obs,ctx,b,q,o,s,c,vm=r37_fixture()
 local r3=r3_snapshot(R37Bag.captureTopLevel(sprite,obs,ctx))
 r3.inventoryRawMap['18'].resref='CHEAT01'
 local projectCalls=0
 local x=M.planAutoBatch(sprite,obs,ctx,R37Bag,r3,function()
   projectCalls=projectCalls+1;return {} end,s,vm,nil,V3)
 assert(x.status=='HOLD_AUTOBATCH_R3_ITEM_JOIN')
 assert(x.reason=='HOLD_R3_TOPLEVEL_ITEM_CHANGED_OR_UNMAPPED')
 assert(projectCalls==0)
 contract(x)
end)
test('autobatch_rejects_other_actor_and_forged_manual_origin',function()
 local sprite,obs,ctx,b,q,o,s,c,vm=r37_fixture()
 local r3=r3_snapshot(R37Bag.captureTopLevel(sprite,obs,ctx))
 local fixture={sprite,obs,ctx,b,q,o,s,c,vm}
 s.actorId=999
 local x=M.planAutoBatch(sprite,obs,ctx,R37Bag,r3,modeled_from(fixture),s,vm,nil,V3)
 assert(x.status=='HOLD_AUTOBATCH_EVENT_CONTRACT_INCOMPLETE')
 contract(x)
 s.actorId=123;obs.actionOriginVerified=true
 local y=M.planAutoBatch(sprite,obs,ctx,R37Bag,r3,modeled_from(fixture),s,vm,nil,V3)
 assert(y.status=='HOLD_AUTOBATCH_EVENT_CONTRACT_INCOMPLETE')
 contract(y)
end)
test('autobatch_refuses_changed_r37_snapshot_mid_scan',function()
 local sprite,obs,ctx,b,q,o,s,c,vm=r37_fixture()
 local r3=r3_snapshot(R37Bag.captureTopLevel(sprite,obs,ctx))
 local fixture={sprite,obs,ctx,b,q,o,s,c,vm}
 local bad={captureTopLevel=function()
   return {status='HOLD_TOPLEVEL_ITEM_CHANGED',readOnly=true,
           sourceOnly=true,dispatchAuthorized=false}
 end}
 local x=M.planAutoBatch(sprite,obs,ctx,bad,r3,modeled_from(fixture),s,vm,nil,V3)
 assert(x.status=='HOLD_AUTOBATCH_R37_RAW_SNAPSHOT')
 assert(x.r37CaptureStatus=='HOLD_TOPLEVEL_ITEM_CHANGED')
 contract(x)
end)

-- R13 is the OLD, read-only target defense reader. This bridge uses its
-- double-read on native-action candidate 105/134; R3 still owns item ITM.
local R13=dofile('BGXAI/BUILD/R13_1_TARGET_DEFENSE_SOURCE_ONLY/BGXAI_R13_TARGET_DEFENSE_OBSERVER.lua')
local function with_r13()
 local sprite,obs,context,bag,quick,other,scene,candidates,v3Scene=r37_fixture()
 sprite.m_equipment.m_selectedWeapon=35
 sprite.m_equipment.m_selectedWeaponAbility=0
 local getter=sprite.m_equipment.m_items.get
 local stableItems={}
 sprite.m_equipment.m_items.get=function(self,slot)
  if stableItems[slot]==nil then stableItems[slot]=getter(self,slot) end
  return stableItems[slot]
 end
 local action={m_actionID=105,m_acteeID={m_Instance=222}}
 local target={m_id=222,m_bAllowEffectListCall=1,isSprite=function()return true end}
 local stats={m_nArmorClass=0,m_nACCrushingMod=0,m_nACPiercingMod=-1,
  m_nACSlashingMod=-3,m_nACMissileMod=4,
  m_nResistCrushing=0,m_nResistPiercing=0,
  m_nResistSlashing=0,m_nResistMissile=40}
 local api={GameObject_Get=function(id)return id==222 and target or nil end,
  GetActiveStats=function()return stats end}
 local contextR13={sessionId='S1',snapshotId='SNAP1',sequence=1,
  actor=123,targetActor=222,actionRaw=105,
  selectedSlot=35,selectedAbility=0,
  readOnlyContextOnly=true,switchAttempted=false,manualEPSBoundaryProven=false}
 local raw=R37Bag.captureTopLevel(sprite,obs,context)
 assert(raw.status=='TOPLEVEL0_38_AND_R37_STABLE_ADVICE_ONLY')
 local f={sprite,obs,context,bag,quick,other,scene,candidates,v3Scene}
 local calls=0
 local proxy={inspect=function(...)
  calls=calls+1
  return R13.inspect(...)
 end}
 local p={sprite=sprite,action=action,api=api,context=contextR13,
  r13=proxy,r37=obs,contextReader=context,reader=R37Bag,
  r3=r3_snapshot(raw),projection=modeled_from(f),
  scene=scene,v3Scene=v3Scene,previousV3=nil,v3=V3}
 return p,stats,target,function()return calls end
end
test('r13_real_action105_to_full_16_slot_weapon_choice_same_target',function()
 local p,stats,target,calls=with_r13()
 local beforeAC=p.v3Scene.enemy.armorClass
 local beforeRes=p.v3Scene.enemy.protections.resistance.MISSILE
 local initial=M.planAutoBatchWithR13(p)
 assert(initial.status=='HOLD_AUTOBATCH_TARGET_RANKING_UNSTABLE')
 assert(type(initial.v3Next)=='table')
 assert(initial.r13DefensesReadFromSameAttack and initial.r13ActionId==105)
 assert(initial.r13AttackTypeACModel.MISSILE==4)
 assert(initial.r13AttackTypeACModel.SLASHING==-3)
 assert(initial.r13PhysicalResistancesModel.MISSILE==0.4)
 -- Caller is NOT mutated; only cloned V3 scene receives raw R13 armor.
 assert(p.v3Scene.enemy.armorClass==beforeAC)
 assert(p.v3Scene.enemy.protections.resistance.MISSILE==beforeRes)
 p.scene.tick=101;p.v3Scene.frame.tick=101;p.previousV3=initial.v3Next
 local out=M.planAutoBatchWithR13(p)
 assert(out.status=='STAGE_DECISION_AWAIT_INDEPENDENT_MANUAL_EPS_ROUND_PROOF')
 assert(out.pendingWeaponChange.kind=='EQUIP_BACKPACK_TO_EMPTY_QUICKSLOT')
 assert(out.pendingWeaponChange.sourceSlot==18 and out.r13TargetId==222)
 assert(out.r13NativeRuntimeAuthenticated==false and out.r13AllImmunitiesKnown==false)
 assert(calls()==2)
 contract(out)
end)
test('r13_action134_context_remains_observed_only',function()
 local p=with_r13()
 p.action.m_actionID=134;p.context.actionRaw=134;p.r37.actionRaw=134
 local initial=M.planAutoBatchWithR13(p)
 assert(initial.status=='HOLD_AUTOBATCH_TARGET_RANKING_UNSTABLE')
 assert(initial.r13ActionId==134)
 contract(initial)
end)
test('r13_nonattack_weapon_selection_92_does_not_bypass_target_guard',function()
 local p=with_r13()
 p.action.m_actionID=92;p.context.actionRaw=92;p.r37.actionRaw=92
 local x=M.planAutoBatchWithR13(p)
 assert(x.status=='HOLD_AUTOBATCH_R13_TARGET_DEFENSE_UNSTABLE')
 assert(x.r13Reason=='NOT_AN_ATTACK_CANDIDATE_ACTION')
 contract(x)
end)
test('r13_target_temporarily_recalculating_stats_blocks_full_batch',function()
 local p,stats,target=with_r13()
 target.m_bAllowEffectListCall=0
 local calls=0
 p.reader={captureTopLevel=function()calls=calls+1;error('no scan')end}
 local x=M.planAutoBatchWithR13(p)
 assert(x.status=='HOLD_AUTOBATCH_R13_TARGET_DEFENSE_UNSTABLE')
 assert(x.r13Reason=='TARGET_ACTIVE_STATS_TEMP_OR_EFFECTS_IN_PROGRESS')
 assert(calls==0)
 contract(x)
end)
test('r13_target_or_action_mismatch_cannot_make_weapon_decision',function()
 local p=with_r13()
 p.context.targetActor=333
 local x=M.planAutoBatchWithR13(p)
 assert(x.status=='HOLD_AUTOBATCH_R13_R27_ACTOR_TARGET_ACTION_MISMATCH')
 contract(x)
 p.context.targetActor=222
 p.action.m_acteeID.m_Instance=333
 local y=M.planAutoBatchWithR13(p)
 assert(y.status=='HOLD_AUTOBATCH_R13_TARGET_DEFENSE_UNSTABLE')
 contract(y)
end)
test('r13_negative_resistance_not_clamped_into_normal_damage',function()
 local p,stats=with_r13()
 stats.m_nResistMissile=-15
 local x=M.planAutoBatchWithR13(p)
 assert(x.status=='HOLD_AUTOBATCH_R13_RESISTANCE_OUTSIDE_MODEL')
 contract(x)
end)
test('r13_outside_supported_attack_type_AC_is_HOLD',function()
 local p,stats=with_r13()
 stats.m_nACMissileMod=-99
 local x=M.planAutoBatchWithR13(p)
 assert(x.status=='HOLD_AUTOBATCH_R13_TYPE_AC_UNSUPPORTED')
 contract(x)
end)
test('r13_busy_action_queue_disables_even_target_probe',function()
 local p,stats,target,calls=with_r13()
 p.r37.queuedActionsRaw=2
 local scans=0
 p.reader={captureTopLevel=function()scans=scans+1;error('not allowed')end}
 local x=M.planAutoBatchWithR13(p)
 assert(x.status=='PRESERVE_KNOWN_ACTION_QUEUE_NO_SCAN')
 assert(x.knownQueuedActions==2 and x.r13ObserveCalls==0)
 assert(scans==0 and calls()==0)
 contract(x)
end)
print("BGXAI BACKPACK16 PRIORITY V4 "..n.." synthetic tests PASS")
