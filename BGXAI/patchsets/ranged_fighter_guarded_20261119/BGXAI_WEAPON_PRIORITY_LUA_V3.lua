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
-- Immunity evidence MUST be a dense array of distinct known damage types.
-- A keyed table such as {SLASHING=true}, sparse list, or a hidden extra
-- field must HOLD, not silently read as an empty immunity list via ipairs().
local function immunities_complete(t)
 if type(t)~='table' then return false end
 local count,seen=0,{}
 for index,damageType in pairs(t) do
  if type(index)~='number' or index%1~=0 or index<1 or index>16 or
     damage_types[damageType]~=true or seen[damageType] then return false end
  seen[damageType]=true
  count=count+1
 end
 for i=1,count do if t[i]==nil then return false end end
 return true
end
-- Exclusions require direct, current, positive evidence that an attack is impossible
-- or unsafe. A confirmed unusable candidate needs a verified slot and evidence,
-- but its *hypothetical* APR / damage / combat costs must not block every other
-- weapon; no attack will ever be made through an excluded slot by this scorer.
local function proven_ineligible(w,a)
 if w.mode=='RANGED' and w.ammoVerified==true and w.ammoCount==0 then
  return 'VERIFIED_EMPTY_AMMUNITION'
 end
 if w.mode=='RANGED' and w.inRange==false then
  return 'VERIFIED_RANGED_OUT_OF_RANGE'
 end
 if w.mode=='MELEE' then
  if a.canSustainMelee==false then return 'VERIFIED_UNSAFE_TO_TANK' end
  if w.inRange==false and (a.pathSafeVerified==false or
       w.canReachWithSafeMove==false) then return 'VERIFIED_NO_SAFE_MELEE_PATH' end
 end
 return nil
end
local function signature(s)
 local f=s.frame
 local t={f.area,f.actorId,f.enemyId,f.equipmentFingerprint,f.protectionFingerprint,
          f.combatFingerprint,s.actor.selectedWeaponId,s.actor.traitProfile.modFingerprint}
 for i=1,4 do t[#t+1]=s.quickslotIds[i]==false and '-' or s.quickslotIds[i] end
 -- Do not trust an external protection fingerprint alone for the new R13
 -- attack-type AC model. Any AC drift forces fresh scene stabilization.
 local enemy=s.enemy
 t[#t+1]='BASE_AC:'..tostring(enemy.armorClass)
 t[#t+1]='TYPE_AC_STATE:'..tostring(enemy.targetTypeACModelStatus)
 local typed=enemy.targetArmorClassByAttackTypeCandidate
 if type(typed)=='table' then
  for _,kind in ipairs({'CRUSHING','PIERCING','SLASHING','MISSILE'}) do
   t[#t+1]='AC_'..kind..':'..tostring(rawget(typed,kind))
  end
 end
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
      not modes[weapon.mode] then return 'HOLD_QUICKSLOT_EVIDENCE_INCOMPLETE' end
   if weapon.mode=='RANGED' then
    if weapon.ammoVerified~=true or (weapon.ammunitionModel~='QUIVER' and
        weapon.ammunitionModel~='SELF') or not between(weapon.ammoCount,0,1000000) or
       weapon.ammoCount~=math.floor(weapon.ammoCount) or
       (weapon.ammunitionModel=='QUIVER' and not ident(weapon.ammoResRef)) then
     return 'HOLD_AMMO_OR_THROWABLE_UNVERIFIED' end
   end
   -- A *verified* non-attacking weapon cannot need speculative final combat
   -- stats. Unknown ammo, route or survivability still use the strict path.
   if not proven_ineligible(weapon,a) then
    if weapon.combatCostsVerified~=true or weapon.statBasis~='FINAL_EFFECTIVE' or
       weapon.finalCombatStatsVerified~=true or
       weapon.allRaceClassKitProficiencyBonusesIncluded~=true then
      return 'HOLD_QUICKSLOT_EVIDENCE_INCOMPLETE' end
    if a.handsMode=='DUAL' and weapon.mode=='MELEE' and weapon.dualWieldStatsVerified~=true then
     return 'HOLD_DUAL_WIELD_COMBAT_STATS_UNKNOWN' end
   end
  end
 end
 if occupied==0 or occupied~=#s.weapons or not seen[a.selectedWeaponId] then
  return 'HOLD_INCOMPLETE_LOADOUT' end
 return nil
end
-- R13 already reads distinct physical AC modifiers. When that complete
-- source-only candidate is supplied, use the AC for ATTACK KIND, not damage
-- resistance kind: all ranged weapon attacks test vs MISSILE AC even when
-- their damage payload is PIERCING. The model is NOT an EEex live attestation.
local AC_KINDS={SLASHING=true,PIERCING=true,CRUSHING=true,MISSILE=true}
local function attack_ac(w,e)
 local kind=w.mode=='RANGED' and 'MISSILE' or w.damageType
 local v=e.targetArmorClassByAttackTypeCandidate
 if v==nil then
  if e.targetTypeACModelStatus~=nil or
     e.targetTypeACModelSnapshotId~=nil or
     e.targetArmorClassBaseCandidate~=nil or
     e.targetTypeACNativeAuthenticated~=nil then
   return nil,'TARGET_TYPE_AC_MODEL_INCOMPLETE'
  end
  return e.armorClass,nil,kind,'BASE_AC_ONLY_APPROXIMATE'
 end
 if type(v)~='table' or
    e.targetTypeACModelStatus~='R13_DERIVED_ATTACK_TYPE_AC_MODEL_ONLY' or
    e.targetTypeACModelSnapshotId~=e.protections.snapshotId or
    e.targetTypeACNativeAuthenticated~=false or
    e.targetArmorClassBaseCandidate~=e.armorClass then
  return nil,'TARGET_TYPE_AC_EVIDENCE_INCONSISTENT'
 end
 local n=0
 for k,x in pairs(v) do
  if AC_KINDS[k]~=true or not between(x,-50,100) or x%1~=0 then
   return nil,'TARGET_TYPE_AC_EVIDENCE_INVALID' end
  n=n+1
 end
 if n~=4 or not between(v[kind],-50,100) then
  return nil,'TARGET_TYPE_AC_EVIDENCE_INCOMPLETE'
 end
 return v[kind],nil,kind,'R13_TYPE_AC_MODEL_ONLY'
end
local function scored_weapon(w,a,e)
 local excludedReason=proven_ineligible(w,a)
 if excludedReason then
  return {id=w.id,slotIndex=w.quickslotIndex,available=false,
          reason=excludedReason,mode=w.mode,penetrates=false,dpr=0},nil
 end
 if not between(w.apr,0.5,10) or not between(w.avgDamageOnHit,0,1000) or
    not between(w.finalTHAC0,-50,100) or not damage_types[w.damageType] or
    not between(w.enchantment,-5,15) or type(w.magical)~='boolean' then
  return nil,'ATTACK_STATS_UNVERIFIED' end
 for _,key in ipairs({'switchCost','resourceCost','retaliationRisk','movementCost','extraEffectValue'}) do
  if not between(w[key],0,1000) then return nil,'COSTS_UNVERIFIED' end
 end
 if type(w.inRange)~='boolean' then return nil,'IN_RANGE_EVIDENCE_UNKNOWN' end
 -- A confirmed lack of ammo, a verified unreachable position, or an unsafe
 -- melee engagement excludes ONLY that candidate; it must not disable a
 -- different, complete and safe quickslot. Unknown provenance still HOLDs.
 local function excluded(reason)
  return {id=w.id,slotIndex=w.quickslotIndex,available=false,
          reason=reason,mode=w.mode,penetrates=false,dpr=0},nil
 end
 if w.mode=='RANGED' and w.ammoCount==0 then
  return excluded('VERIFIED_EMPTY_AMMUNITION')
 end
 if w.inRange~=true then
  if w.mode=='RANGED' then return excluded('VERIFIED_RANGED_OUT_OF_RANGE') end
  if a.pathSafeVerified==false or w.canReachWithSafeMove==false then
   return excluded('VERIFIED_NO_SAFE_MELEE_PATH')
  end
  if a.pathSafeVerified~=true or w.canReachWithSafeMove~=true then
   return nil,'MELEE_PATH_EVIDENCE_UNKNOWN'
  end
 end
 if w.mode=='MELEE' then
  if a.canSustainMelee==false then return excluded('VERIFIED_UNSAFE_TO_TANK') end
  if a.canSustainMelee~=true then return nil,'MELEE_SURVIVABILITY_UNVERIFIED' end
 end
 if w.mode=='RANGED' and a.nearRangedEnemy==true and w.rangedClosePenaltyAccounted~=true then
  return nil,'CLOSE_RANGE_THAC0_PENALTY_UNVERIFIED' end
 local p=e.protections
 if type(p.immuneDamageTypes)~='table' or type(p.resistance)~='table' or
    not between(p.minimumEnchantment,-5,15) or
    type(p.magicalWeaponsBlocked)~='boolean' or
    type(p.normalWeaponsBlocked)~='boolean' or type(p.missilesBlocked)~='boolean' or
    not between(p.resistance[w.damageType],0,1) or not between(e.armorClass,-50,100) then
  return nil,'ENEMY_PROTECTIONS_UNVERIFIED' end
 if not immunities_complete(p.immuneDamageTypes) then
  return nil,'IMMUNITY_SET_INCOMPLETE'
 end
 local immune=(w.enchantment<p.minimumEnchantment or
    (w.magical and p.magicalWeaponsBlocked) or
    (not w.magical and p.normalWeaponsBlocked) or
    (w.mode=='RANGED' and p.missilesBlocked))
 for _,x in ipairs(p.immuneDamageTypes) do if x==w.damageType then immune=true end end
 local actualAC,acError,attackKind,acTier=attack_ac(w,e)
 if actualAC==nil then return nil,acError end
 local hit=clamp((21-w.finalTHAC0+actualAC)/20,0.05,0.95)
 local dpr=immune and 0 or hit*w.avgDamageOnHit*w.apr*(1-p.resistance[w.damageType])
 local extra=immune and 0 or w.extraEffectValue
 local value=dpr+extra-w.switchCost-w.resourceCost-w.retaliationRisk-w.movementCost
 -- A witnessed, fully blocked or entirely zero-value current attack must not
 -- retain a generic 2-DPR / 15% switching threshold. This is target-specific
 -- evidence, never an instruction to switch or evidence of a free EPS queue.
 -- Keep status utility alive: a weapon that applies a verified nonphysical
 -- effect still has a reason to remain equipped even when physical DPR is 0.
 local ineffectiveReason=nil
 if immune then
  ineffectiveReason='VERIFIED_TARGET_WEAPON_IMMUNITY'
 elseif dpr==0 and extra==0 then
  ineffectiveReason='VERIFIED_NO_EFFECTIVE_DAMAGE_OR_EFFECT'
 end
 return {id=w.id,slotIndex=w.quickslotIndex,available=true,value=value,dpr=dpr,penetrates=not immune,
         hitChance=hit,mode=w.mode,ineffectiveReason=ineffectiveReason,
         targetACUsed=actualAC,attackACType=attackKind,attackACModel=acTier},nil
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
  if score.available~=false and (not best or score.value>best.value or
      (score.value==best.value and score.id==a.selectedWeaponId)) then
   best=score end
 end
 if not current then return issue('HOLD_CURRENT_WEAPON_UNVERIFIED',{next=next}) end
 if not best then return issue('HOLD_NO_EFFECTIVE_ATTACK',{next=next,candidates=candidates}) end
 local anyEffective=false
 for _,x in ipairs(candidates) do if x.penetrates and x.dpr>0 then anyEffective=true end end
 if not anyEffective then return issue('HOLD_NO_EFFECTIVE_ATTACK',{next=next,candidates=candidates}) end
 -- A shielded / fully resistant target makes the current weapon as
 -- ineffective as confirmed empty ammo. Even a small *positive verified*
 -- alternative can be better than zero; the normal hysteresis is for two
 -- functioning weapons, not for continuing a futile attack indefinitely.
 local currentUnusable=current.available==false or current.ineffectiveReason~=nil
 local diff=nil
 local threshold=0
 if not currentUnusable then
  diff=best.value-current.value
  threshold=math.max(2,math.abs(current.value)*0.15)
 end
 if currentUnusable then
  -- Switching from a known unusable weapon is allowed as ADVICE only when
  -- the alternative has positive actual combat utility, not merely an attack.
  if not best.penetrates or best.dpr<=0 or best.value<=0 then
   return issue('HOLD_NO_EFFECTIVE_ATTACK',{next=next,candidates=candidates})
  end
 elseif best.id==current.id or diff<=threshold then
  return issue('KEEP_CURRENT',{next=next,candidates=candidates})
 end
 next.lastAdviceTick=f.tick
 return issue('ADVISE_PRIORITY_QUICKSLOT_ONLY',{
  fromWeaponId=current.id,toWeaponId=best.id,slotIndex=best.slotIndex,
  targetId=e.enemyId,improvement=diff,threshold=threshold,next=next,candidates=candidates,
  currentUnusableReason=currentUnusable and (current.reason or current.ineffectiveReason) or nil,
  reason=currentUnusable and 'VERIFIED_CURRENT_WEAPON_UNUSABLE_SAFE_FALLBACK' or
                          'COMPLETE_EFFECTIVE_STATS_BETTER_AFTER_STABILITY'})
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
-- Score ONE actual backpack location against the SAME actor and enemy model.
-- This reuses scored_weapon; it does not smuggle an unequipped item into a
-- quickslot or declare its counterfactual APR native-authenticated. The caller
-- must independently prove real engine stats before any future dispatch.
function M.scoreBackpackCandidate(scene,weapon)
 local problem=verified_scene(scene,true)
 if problem then return issue(problem,{sourceOnly=true}) end
 local f,a=scene.frame,scene.actor
 if type(weapon)~='table' or weapon.slot~='BACKPACK' or
    not between(weapon.sourceSlot,18,33) or weapon.sourceSlot%1~=0 or
    not ident(weapon.id) or not ident(weapon.resRef) or #weapon.resRef>8 or
    weapon.resRef:find('[^%w_]') or
    weapon.snapshotId~=f.snapshotId or
    weapon.modFingerprint~=a.traitProfile.modFingerprint or
    weapon.modelProvenance~='V3_V4_V5' or
    weapon.counterfactualBasis~='MODEL_ONLY_NOT_NATIVE_EFFECTIVE' or
    weapon.alternativeEffectiveStatsLiveVerified~=false or
    weapon.usableVerified~=true or weapon.identifiedVerified~=true or
    weapon.notCursedVerified~=true or weapon.notQuestItemVerified~=true or
    weapon.offhandCompatibilityVerified~=true or
    weapon.ammoAndLauncherVerified~=true or
    weapon.protectionsAccountedVerified~=true or
    weapon.finalCombatStatsVerified~=true or
    weapon.allRaceClassKitProficiencyBonusesIncluded~=true or
    weapon.statBasis~='FINAL_EFFECTIVE' or
    weapon.combatCostsVerified~=true then
  return issue('HOLD_BACKPACK_COUNTERFACTUAL_MODEL_INCOMPLETE',
               {sourceOnly=true})
 end
 for _,w in ipairs(scene.weapons) do
  if w.id==weapon.id then return issue('HOLD_BACKPACK_DUPLICATE_QUICKSLOT_ID',
                                     {sourceOnly=true}) end
 end
 if weapon.mode=='RANGED' then
  if weapon.ammoVerified~=true or
     (weapon.ammunitionModel~='QUIVER' and weapon.ammunitionModel~='SELF') or
     not between(weapon.ammoCount,0,1000000) or
     weapon.ammoCount%1~=0 or
     (weapon.ammunitionModel=='QUIVER' and not ident(weapon.ammoResRef)) then
   return issue('HOLD_BACKPACK_LAUNCHER_AMMO_UNVERIFIED',
                {sourceOnly=true})
  end
 end
 if a.handsMode=='DUAL' and weapon.mode=='MELEE' and
    weapon.dualWieldStatsVerified~=true then
  return issue('HOLD_BACKPACK_OFFHAND_RATE_UNKNOWN',{sourceOnly=true})
 end
 local score,err=scored_weapon(weapon,a,scene.enemy)
 if not score then
  return issue('HOLD_BACKPACK_TARGET_SCORE_INCOMPLETE',
               {reason=err,sourceOnly=true})
 end
 if score.available~=true then
  return issue('HOLD_BACKPACK_CANDIDATE_INELIGIBLE',
               {reason=score.reason,sourceOnly=true})
 end
 return issue('BACKPACK_TARGET_UTILITY_MODEL_ONLY',{
  sourceOnly=true,readOnly=true,weaponSwitchAuthorized=false,
  inventoryMoveAuthorized=false,ordersSent=0,
  engineFinalAlternativeStatsVerified=false,liveReadVerified=false,
  sourceSlot=weapon.sourceSlot,candidateResref=weapon.resRef,
  snapshotId=f.snapshotId,actorId=f.actorId,targetId=f.enemyId,
  estimatedUtility=score.value,estimatedDpr=score.dpr,
  hitChanceModel=score.hitChance,attackACType=score.attackACType,
  attackACModel=score.attackACModel,
  candidateIneffectiveReason=score.ineffectiveReason,
  targetTypeSpecific=true})
end
return M