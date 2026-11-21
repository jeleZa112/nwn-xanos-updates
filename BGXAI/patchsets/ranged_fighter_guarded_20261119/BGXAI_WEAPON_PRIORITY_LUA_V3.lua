-- BGXAI priority weapon selection V3, pure native Lua 5.3-compatible advice.
-- SOURCE ONLY. NOT INSTALLED. NO engine action, filesystem or EEex hook.
-- Expects COMPLETE_EFFECTIVE_SNAPSHOT from separately proven EEex adapter;
-- never interprets a caller's boolean 'verified' as a runtime proof.
-- Empty quickslot is the explicit boolean false (not nil).
-- Output is ALWAYS executable=false, dispatchAuthorized=false.
local M = {}
local function finite(x) return type(x)=='number' and x==x and x~=math.huge and x~=-math.huge end
local function between(x,low,high) return finite(x) and x>=low and x<=high end
local function ident(x) return type(x)=='string' and #x>0 and #x<=80 and not x:find('[^%w_.%+%-]') end
local function clamp(x,lo,hi) return math.max(lo,math.min(hi,x)) end
local function issue(s,extra)
 local out={status=s,executable=false,dispatchAuthorized=false}
 if type(extra)=='table' then for k,v in pairs(extra) do out[k]=v end end
 return out
end
local modes={MELEE=true,RANGED=true}
local hands={SINGLE=true,DUAL=true,TWO_HANDED=true}
local damage_types={SLASHING=true,PIERCING=true,CRUSHING=true,MISSILE=true}
local function signature(s)
 local f=s.frame
 local t={f.area,f.actorId,f.enemyId,f.equipmentFingerprint,f.protectionFingerprint,
          f.combatFingerprint,s.actor.selectedWeaponId,s.actor.traitProfile.modFingerprint}
 for i=1,4 do t[#t+1]=s.quickslotIds[i]==false and '-' or s.quickslotIds[i] end
 return table.concat(t,'|')
end
local function verified_scene(s,passivePreview)
 if type(s)~='table' or type(s.frame)~='table' or type(s.actor)~='table' or
    type(s.enemy)~='table' or type(s.weapons)~='table' or type(s.quickslotIds)~='table' then
  return 'HOLD_INCOMPLETE_LOADOUT'
 end
 local f,a,e=s.frame,s.actor,s.enemy
 if not between(f.tick,0,1e12) or f.tick~=math.floor(f.tick) or
    not ident(f.snapshotId) or not ident(f.area) or not ident(f.actorId) or
    not ident(f.enemyId) or f.actorId==f.enemyId or
    not ident(f.equipmentFingerprint) or not ident(f.protectionFingerprint) or
    not ident(f.combatFingerprint) or f.captureContract~='COMPLETE_EFFECTIVE_SNAPSHOT' or
    f.completeEquipmentObserved~=true or f.completeQuiverObserved~=true or
    f.completeTargetObserved~=true then return 'HOLD_CAPTURE_CONTRACT_UNVERIFIED' end
 if a.actorId~=f.actorId or a.area~=f.area or a.currentTargetId~=f.enemyId or
    e.enemyId~=f.enemyId or e.area~=f.area or a.selectedWeaponId~=f.selectedWeaponId or
    not ident(a.selectedWeaponId) or e.observationVerified~=true or
    e.visibleVerified~=true or e.hostileVerified~=true or
    a.observationVerified~=true then return 'HOLD_TARGET_OR_SELECTION_CHANGED' end
 if type(a.traitProfile)~='table' or a.traitProfile.verified~=true or
    a.traitProfile.snapshotId~=f.snapshotId or not ident(a.traitProfile.modFingerprint) or
    a.traitProfile.activeClassesVerified~=true or
    a.traitProfile.raceClassKitBonusesIncluded~=true then return 'HOLD_TRAIT_PROFILE_UNVERIFIED' end
 if type(e.protections)~='table' or e.protections.snapshotId~=f.snapshotId or
    e.protections.observed~=true then return 'HOLD_STALE_ENEMY_PROTECTIONS' end
 if not hands[a.handsMode] then return 'HOLD_HANDS_CONFIGURATION_UNKNOWN' end
 if type(a.nearRangedEnemy)~='boolean' then return 'HOLD_DISTANCE_OR_PENALTY_CONTEXT_UNKNOWN' end
 -- Read-only background ranking must not pretend that actions are free.
 -- The old foreground choose() continues enforcing manual/EPS protections.
 if not passivePreview and (a.manualOrderActive~=false or a.epsBusy~=false or
    a.healingReserved~=false or a.currentlyCasting~=false or a.originVerified~='AI') then
  return 'HOLD_PRESERVE_MANUAL_OR_EPS' end
 if #s.weapons>4 then return 'HOLD_INCOMPLETE_LOADOUT' end
 local seen,occupied={},0
 for i=1,4 do
  local id=s.quickslotIds[i]
  if id==nil then return 'HOLD_INCOMPLETE_LOADOUT' end
  if id~=false then
   if not ident(id) or seen[id] then return 'HOLD_AMBIGUOUS_QUICKSLOT' end
   seen[id]=true;occupied=occupied+1
   local count=0;local weapon=nil
   for _,w in ipairs(s.weapons) do
    if type(w)=='table' and w.id==id then count=count+1;weapon=w end
   end
   if count~=1 or weapon.quickslotIndex~=i-1 or weapon.slot~='QUICKSLOT' or
      weapon.snapshotId~=f.snapshotId or weapon.modFingerprint~=a.traitProfile.modFingerprint or
      weapon.usableVerified~=true or weapon.equippedWeaponSlotVerified~=true or
      weapon.combatCostsVerified~=true or weapon.statBasis~='FINAL_EFFECTIVE' or
      weapon.finalCombatStatsVerified~=true or weapon.allRaceClassKitProficiencyBonusesIncluded~=true or
      not modes[weapon.mode] then return 'HOLD_QUICKSLOT_EVIDENCE_INCOMPLETE' end
   if a.handsMode=='DUAL' and weapon.mode=='MELEE' and weapon.dualWieldStatsVerified~=true then
    return 'HOLD_DUAL_WIELD_COMBAT_STATS_UNKNOWN' end
   if weapon.mode=='RANGED' then
    if weapon.ammoVerified~=true or (weapon.ammunitionModel~='QUIVER' and
        weapon.ammunitionModel~='SELF') or not between(weapon.ammoCount,1,1000000) or
       weapon.ammoCount~=math.floor(weapon.ammoCount) or
       (weapon.ammunitionModel=='QUIVER' and not ident(weapon.ammoResRef)) then
     return 'HOLD_AMMO_OR_THROWABLE_UNVERIFIED' end
   end
  end
 end
 if occupied==0 or occupied~=#s.weapons or not seen[a.selectedWeaponId] then
  return 'HOLD_INCOMPLETE_LOADOUT' end
 return nil
end
local function scored_weapon(w,a,e)
 if not between(w.apr,0.5,10) or not between(w.avgDamageOnHit,0,1000) or
    not between(w.finalTHAC0,-50,100) or not damage_types[w.damageType] or
    not between(w.enchantment,-5,15) or type(w.magical)~='boolean' then
  return nil,'ATTACK_STATS_UNVERIFIED' end
 for _,key in ipairs({'switchCost','resourceCost','retaliationRisk','movementCost','extraEffectValue'}) do
  if not between(w[key],0,1000) then return nil,'COSTS_UNVERIFIED' end
 end
 if type(w.inRange)~='boolean' then return nil,'IN_RANGE_EVIDENCE_UNKNOWN' end
 if w.inRange~=true then
  if w.mode~='MELEE' or a.pathSafeVerified~=true or w.canReachWithSafeMove~=true then
   return nil,'OUT_OF_RANGE_OR_UNSAFE_PATH'
  end
 end
 if w.mode=='MELEE' and a.canSustainMelee~=true then return nil,'MELEE_SURVIVABILITY_UNVERIFIED' end
 if w.mode=='RANGED' and a.nearRangedEnemy==true and w.rangedClosePenaltyAccounted~=true then
  return nil,'CLOSE_RANGE_THAC0_PENALTY_UNVERIFIED' end
 local p=e.protections
 if type(p.immuneDamageTypes)~='table' or type(p.resistance)~='table' or
    not between(p.minimumEnchantment,-5,15) or
    type(p.magicalWeaponsBlocked)~='boolean' or
    type(p.normalWeaponsBlocked)~='boolean' or type(p.missilesBlocked)~='boolean' or
    not between(p.resistance[w.damageType],0,1) or not between(e.armorClass,-50,100) then
  return nil,'ENEMY_PROTECTIONS_UNVERIFIED' end
 if #p.immuneDamageTypes>16 then return nil,'IMMUNITY_SET_INCOMPLETE' end
 for _,x in ipairs(p.immuneDamageTypes) do if not damage_types[x] then return nil,'IMMUNITY_SET_INCOMPLETE' end end
 local immune=(w.enchantment<p.minimumEnchantment or
    (w.magical and p.magicalWeaponsBlocked) or
    (not w.magical and p.normalWeaponsBlocked) or
    (w.mode=='RANGED' and p.missilesBlocked))
 for _,x in ipairs(p.immuneDamageTypes) do if x==w.damageType then immune=true end end
 local hit=clamp((21-w.finalTHAC0+e.armorClass)/20,0.05,0.95)
 local dpr=immune and 0 or hit*w.avgDamageOnHit*w.apr*(1-p.resistance[w.damageType])
 local extra=immune and 0 or w.extraEffectValue
 local value=dpr+extra-w.switchCost-w.resourceCost-w.retaliationRisk-w.movementCost
 return {id=w.id,slotIndex=w.quickslotIndex,value=value,dpr=dpr,penetrates=not immune,
         hitChance=hit,mode=w.mode},nil
end
local function choose_impl(scene,previous,passivePreview)
 local problem=verified_scene(scene,passivePreview)
 if problem then return issue(problem) end
 local f,a,e=scene.frame,scene.actor,scene.enemy
 local sig=signature(scene)
 local next={signature=sig,lastTick=f.tick,
             lastAdviceTick=type(previous)=='table' and previous.lastAdviceTick or nil}
 if type(previous)~='table' or previous.signature~=sig or
    not between(previous.lastTick,0,1e12) or f.tick<=previous.lastTick or
    f.tick-previous.lastTick>30 then
  return issue('HOLD_STABILIZE_TARGET_AND_EQUIPMENT',{next=next}) end
 if between(next.lastAdviceTick,0,1e12) and f.tick-next.lastAdviceTick<45 then
  return issue('HOLD_ADVISORY_SWITCH_COOLDOWN',{next=next}) end
 local candidates={};local current=nil;local best=nil
 for _,w in ipairs(scene.weapons) do
  local score,err=scored_weapon(w,a,e)
  if not score then return issue('HOLD_UNRANKABLE_OCCUPIED_WEAPON',{next=next,reason=err}) end
  candidates[#candidates+1]=score
  if score.id==a.selectedWeaponId then current=score end
  if not best or score.value>best.value or (score.value==best.value and score.id==a.selectedWeaponId) then
   best=score end
 end
 if not current or not best then return issue('HOLD_CURRENT_WEAPON_UNVERIFIED',{next=next}) end
 local anyEffective=false
 for _,x in ipairs(candidates) do if x.penetrates and x.dpr>0 then anyEffective=true end end
 if not anyEffective then return issue('HOLD_NO_EFFECTIVE_ATTACK',{next=next,candidates=candidates}) end
 local diff=best.value-current.value
 local threshold=math.max(2,math.abs(current.value)*0.15)
 if best.id==current.id or diff<=threshold then
  return issue('KEEP_CURRENT',{next=next,candidates=candidates}) end
 next.lastAdviceTick=f.tick
 return issue('ADVISE_PRIORITY_QUICKSLOT_ONLY',{
  fromWeaponId=current.id,toWeaponId=best.id,slotIndex=best.slotIndex,
  targetId=e.enemyId,improvement=diff,threshold=threshold,next=next,candidates=candidates,
  reason='COMPLETE_EFFECTIVE_STATS_BETTER_AFTER_STABILITY'})
end
-- Existing foreground scorer remains strict: no recommendation under manual/EPS/cast.
function M.choose(scene,previous)
 return choose_impl(scene,previous,false)
end
-- Pure background scoring only: this bypasses activity gates solely for a
-- NON-EXECUTABLE comparison. It does NOT bypass inventory/target/trait/effect
-- evidence checks, and grants NO order/LOCALS/BCS authority to a caller.
function M.preview(scene,previous)
 local out=choose_impl(scene,previous,true)
 if out.status=='ADVISE_PRIORITY_QUICKSLOT_ONLY' then
  out.status='PASSIVE_RANKING_SUGGESTS_SLOT'
 end
 out.passivePreview=true
 out.executable=false
 out.dispatchAuthorized=false
 return out
end
return M
