-- Deterministic state-space regression, SOURCE ONLY, not an EEex runtime test.
-- Exercises the complete V3 public advisory boundary with orthogonal bad facts.
local path=(arg and arg[0] or ''):match('^(.*[/\\])') or './'
local api=dofile(path..'BGXAI_WEAPON_PRIORITY_LUA_V3.lua')
local function copy(x)
 if type(x)~='table' then return x end
 local out={}; for k,v in pairs(x) do out[k]=copy(v) end
 return out
end
local function canon(v)
 if type(v)~='table' then return tostring(v) end
 local keys={};for k in pairs(v) do keys[#keys+1]=k end
 table.sort(keys,function(a,b) return tostring(a)<tostring(b) end)
 local parts={};for _,k in ipairs(keys) do parts[#parts+1]=tostring(k)..'='..canon(v[k]) end
 return '{'..table.concat(parts,',')..'}'
end
local function new_scene()
 local base={usableVerified=true,equippedWeaponSlotVerified=true,slot='QUICKSLOT',
  inRange=true,finalTHAC0=10,apr=2,avgDamageOnHit=7,damageType='SLASHING',
  enchantment=1,magical=true,switchCost=0,resourceCost=0,retaliationRisk=0,
  movementCost=0,extraEffectValue=0,combatCostsVerified=true,statBasis='FINAL_EFFECTIVE',
  allRaceClassKitProficiencyBonusesIncluded=true,finalCombatStatsVerified=true,
  modFingerprint='EET',snapshotId='NATIVE_FUZZ',weaponGroup='LONG_SWORD'}
 local sword=copy(base);sword.id='SWORD';sword.quickslotIndex=0;sword.mode='MELEE'
 local dart=copy(base);dart.id='DART';dart.quickslotIndex=1;dart.mode='RANGED'
 dart.weaponGroup='DART';dart.damageType='MISSILE';dart.apr=3;dart.avgDamageOnHit=5
 dart.ammoVerified=true;dart.ammunitionModel='SELF';dart.ammoCount=20
 dart.rangedClosePenaltyAccounted=true
 return {frame={tick=300,area='ARX',actorId='KHALID',enemyId='HOSTILE',
  snapshotId='NATIVE_FUZZ',equipmentFingerprint='E1',protectionFingerprint='P1',
  combatFingerprint='C1',selectedWeaponId='DART',captureContract='COMPLETE_EFFECTIVE_SNAPSHOT',
  completeEquipmentObserved=true,completeQuiverObserved=true,completeTargetObserved=true},
  actor={actorId='KHALID',area='ARX',currentTargetId='HOSTILE',handsMode='SINGLE',
  observationVerified=true,manualOrderActive=false,currentlyCasting=false,
  healingReserved=false,epsBusy=false,originVerified='AI',selectedWeaponId='DART',
  pathSafeVerified=true,canSustainMelee=true,nearRangedEnemy=true,
  traitProfile={verified=true,activeClassesVerified=true,raceClassKitBonusesIncluded=true,
  modFingerprint='EET',snapshotId='NATIVE_FUZZ'}},
  enemy={enemyId='HOSTILE',area='ARX',observationVerified=true,visibleVerified=true,
  hostileVerified=true,armorClass=0,protections={snapshotId='NATIVE_FUZZ',observed=true,
  immuneDamageTypes={},minimumEnchantment=0,magicalWeaponsBlocked=false,
  normalWeaponsBlocked=false,missilesBlocked=false,
  resistance={SLASHING=0,MISSILE=0,CRUSHING=0,PIERCING=0}}},
  weapons={sword,dart},quickslotIds={'SWORD','DART',false,false}}
end
local function assert_readonly(res)
 assert(type(res)=='table' and res.executable==false and res.dispatchAuthorized==false)
 assert(res.ordersSent==nil or res.ordersSent==0)
 assert(res.actionQueueCleared==nil or res.actionQueueCleared==false)
 assert(res.weaponSwitchAuthorized==nil or res.weaponSwitchAuthorized==false)
 if res.toWeaponId then
  assert(res.toWeaponId=='SWORD' or res.toWeaponId=='DART')
  assert(res.slotIndex==(res.toWeaponId=='SWORD' and 0 or 1))
  assert(res.targetId=='HOSTILE')
 end
end
local states={true,false,'UNKNOWN'}
local ammo={0,20,'UNKNOWN'}
local immunities={'NONE','KNOWN','MAP','SPARSE'}
local tested=0
for _,range in ipairs(states) do
 for _,bullets in ipairs(ammo) do
  for stats=1,2 do
   for _,immunity in ipairs(immunities) do
    for activity=1,2 do
     for target=1,2 do
      local scene=new_scene();local d=scene.weapons[2]
      if range=='UNKNOWN' then d.inRange=nil else d.inRange=range end
      if bullets=='UNKNOWN' then d.ammoCount=nil else d.ammoCount=bullets end
      if stats==2 then
       d.apr=nil;d.finalTHAC0=nil;d.avgDamageOnHit=nil
       d.finalCombatStatsVerified=false;d.combatCostsVerified=false
      end
      if immunity=='KNOWN' then scene.enemy.protections.immuneDamageTypes={'SLASHING'}
      elseif immunity=='MAP' then scene.enemy.protections.immuneDamageTypes={SLASHING=true}
      elseif immunity=='SPARSE' then scene.enemy.protections.immuneDamageTypes={[2]='SLASHING'} end
      if activity==2 then
       scene.actor.manualOrderActive=true;scene.actor.epsBusy=true
       scene.actor.currentlyCasting=true;scene.actor.originVerified='UNKNOWN'
      end
      if target==2 then scene.enemy.enemyId='ALLY' end
      local before=canon(scene)
      local first=api.choose(scene)
      local passive=api.preview(scene)
      assert_readonly(first);assert_readonly(passive)
      assert(canon(scene)==before,'pure first call changed input')
      local future=copy(scene);future.frame.tick=future.frame.tick+1
      local futureBefore=canon(future)
      local second=api.choose(future,first.next)
      local passiveSecond=api.preview(future,passive.next)
      assert_readonly(second);assert_readonly(passiveSecond)
      assert(canon(future)==futureBefore,'pure second call changed input')
      if activity==2 then assert(second.status=='HOLD_PRESERVE_MANUAL_OR_EPS' or
          second.status=='HOLD_TARGET_OR_SELECTION_CHANGED' or
          second.status=='HOLD_AMMO_OR_THROWABLE_UNVERIFIED' or
          second.status=='HOLD_QUICKSLOT_EVIDENCE_INCOMPLETE',second.status) end
      if target==2 then assert(second.status=='HOLD_TARGET_OR_SELECTION_CHANGED') end
      if immunity=='MAP' or immunity=='SPARSE' then
       assert(second.status~='ADVISE_PRIORITY_QUICKSLOT_ONLY')
       assert(passiveSecond.status~='PASSIVE_RANKING_SUGGESTS_SLOT')
      end
      if d.inRange==false then
       assert(second.toWeaponId~='DART')
       assert(passiveSecond.toWeaponId~='DART')
      end
      tested=tested+1
     end
    end
   end
  end
 end
end
assert(tested==288,tostring(tested))
print('PASS WEAPON MATRIX '..tested..'/'..tested..' READONLY CASES SOURCE ONLY')