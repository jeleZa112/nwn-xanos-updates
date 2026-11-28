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
print("BGXAI BACKPACK16 PRIORITY V4 "..n.." synthetic tests PASS")
