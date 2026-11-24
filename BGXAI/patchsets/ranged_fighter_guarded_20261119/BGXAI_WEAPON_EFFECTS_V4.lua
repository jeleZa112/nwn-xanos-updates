-- BGXAI Weapon Priority V4: strength/launcher/ammo/on-hit effects adapter.
-- SOURCE ONLY, NOT INSTALLED. REQUIRES separately verified COMPLETE game snapshots.
-- No EEex hooks, game actions, BCS or LOCALS writes. Always advisory-only.
-- V3 receives FINAL_EFFECTIVE stat fields; this layer does not guess stat bonuses.
local M={}
local function finite(x) return type(x)=='number' and x==x and x~=math.huge and x~=-math.huge end
local function bounded(x,low,high) return finite(x) and x>=low and x<=high end
local function id(x) return type(x)=='string' and #x>=1 and #x<=80 and not x:find('[^%w_.%+%-]') end
local function hold(why,other)
 local out={status='HOLD_EFFECT_MODEL_INCOMPLETE',reason=why,executable=false,dispatchAuthorized=false}
 if type(other)=='table' then for k,v in pairs(other) do out[k]=v end end
 return out
end
-- Keep this narrow verified exclusion in lockstep with V3.proven_ineligible.
-- A guessed empty quiver, an unknown path, or an unverified class is NOT evidence.
local function known_ineligible(w,a)
 if type(w)~='table' or type(a)~='table' then return false end
 if w.mode=='RANGED' then
  return w.ammoVerified==true and w.ammoCount==0 and
     (w.ammunitionModel=='QUIVER' or w.ammunitionModel=='SELF')
 end
 if w.mode=='MELEE' then
  return a.canSustainMelee==false or
    (w.inRange==false and (a.pathSafeVerified==false or w.canReachWithSafeMove==false))
 end
 return false
end
local STRENGTH_RANGED={SLING=true,THROWING_DAGGER=true,THROWING_AXE=true}
local KINDS={INSTANT_DAMAGE=true,POISON_DOT=true,CONTROL=true,DEBUFF=true,OTHER_DAMAGE_OVER_TIME=true}
local SOURCES={WEAPON=true,AMMO=true,LAUNCHER=true,ACTIVE_BUFF=true}
local CATEGORIES={WEAPON=true,AMMO=true,LAUNCHER=true,STRENGTH=true,OTHER_EFFECTIVE=true}
local function strength_applies(w)
 if w.mode=='MELEE' then return true end
 if w.mode~='RANGED' then return nil end
 return STRENGTH_RANGED[w.weaponGroup]==true
end
local function physical(w,actor,snapshot)
 if w.finalCombatStatsVerified~=true or w.statBasis~='FINAL_EFFECTIVE' then
  return nil,'FINAL_STATS_NOT_VERIFIED' end
 if not bounded(actor.strengthDamageBonus,-30,100) or actor.strengthDamageBonusVerified~=true then
  return nil,'STRENGTH_BONUS_UNVERIFIED' end
 if w.dexterityHitBonusIncluded~=true and w.mode=='RANGED' then
  return nil,'RANGED_DEX_TO_HIT_NOT_INCLUDED' end
 if w.mode=='RANGED' and w.strengthHitBonusExcluded~=true then
  return nil,'RANGED_STRENGTH_TO_HIT_UNVERIFIED' end
 if w.weaponGroup=='SLING' and (w.launcherAmmoPairVerified~=true or
    w.ammunitionModel~='QUIVER' and w.ammunitionModel~='SELF') then
  return nil,'SLING_LAUNCHER_AMMO_PAIR_UNVERIFIED' end
 if w.damageTypeSpecialRulesVerified~=true then return nil,'DAMAGE_TYPE_SPECIAL_RULES_UNKNOWN' end
 if w.strengthRuleFromInstalledEET~=true or w.strengthDamageApplies~=strength_applies(w) then
  return nil,'STRENGTH_APPLICABILITY_UNVERIFIED' end
 local b=w.damageBreakdown
 if type(b)~='table' or b.snapshotId~=snapshot or b.complete~=true or
    b.verifiedInInstalledEET~=true or b.launcherAmmoAndBuffsIncluded~=true or
    b.conditionalOnHitEffectsExcluded~=true or
    type(b.components)~='table' or #b.components<1 or #b.components>20 then
  return nil,'PHYSICAL_BREAKDOWN_INCOMPLETE' end
 local total=0;local seen={};local strengths=0;local base=0
 for _,c in ipairs(b.components) do
  if type(c)~='table' or not id(c.id) or seen[c.id] or
     not CATEGORIES[c.category] or c.snapshotId~=snapshot or
     c.observedInInstalledEET~=true or not bounded(c.avgDamage,-100,1000) then
   return nil,'PHYSICAL_COMPONENT_UNVERIFIED_OR_DUPLICATE' end
  seen[c.id]=true
  if c.category=='STRENGTH' then
   strengths=strengths+1
   if c.avgDamage~=actor.strengthDamageBonus then return nil,'STRENGTH_VALUE_MISMATCH' end
  end
  if c.category=='WEAPON' then base=base+1 end
  total=total+c.avgDamage
 end
 if base~=1 or strengths~=(strength_applies(w) and 1 or 0) then
  return nil,'STRENGTH_OR_BASE_COMPONENT_NOT_ACCOUNTED' end
 -- Do NOT add strength: effective final damage is already calculated by game.
 if not bounded(w.avgDamageOnHit,0,1000) or math.abs(w.avgDamageOnHit-total)>0.000001 then
  return nil,'DOUBLE_COUNT_OR_INCOMPLETE_PHYSICAL_DAMAGE' end
 return total,nil
end
local function status_value(w,enemy,frame)
 if w.extraEffectValue~=0 then return nil,'OLD_SPECIAL_VALUE_ALREADY_APPLIED' end
 if w.specialEffectsComplete~=true or w.specialEffectsSnapshotId~=frame.snapshotId or
    type(w.onHitEffects)~='table' or #w.onHitEffects>32 or
    type(w.effectSourcesComplete)~='table' then
  return nil,'WEAPON_ON_HIT_EFFECTS_NOT_EXHAUSTIVE' end
 for source,_ in pairs(SOURCES) do
  if w.effectSourcesComplete[source]~=true then return nil,'EFFECT_SOURCE_UNOBSERVED_'..source end
 end
 if enemy.effectStatusFingerprint~=frame.effectStatusFingerprint or
    enemy.effectStatusVerified~=true then return nil,'TARGET_EFFECT_STATUS_STALE' end
 if not bounded(enemy.armorClass,-50,100) or not bounded(w.finalTHAC0,-50,100) or
    not bounded(w.apr,0.5,10) then return nil,'HIT_CHANCE_UNVERIFIED' end
 local hit=math.max(0.05,math.min(0.95,(21-w.finalTHAC0+enemy.armorClass)/20))
 local sum=0;local seen={}
 for _,ef in ipairs(w.onHitEffects) do
  if type(ef)~='table' or not id(ef.id) or seen[ef.id] or not SOURCES[ef.source] or
     not KINDS[ef.kind] or ef.trigger~='ON_HIT' or
     ef.snapshotId~=frame.snapshotId or ef.targetStatusFingerprint~=frame.effectStatusFingerprint or
     ef.evidenceVerifiedInInstalledEET~=true or ef.abilityAndAmmoMatched~=true or
     ef.targetImmunityVerified~=true or type(ef.targetImmune)~='boolean' or
     ef.targetAlreadyAffectedVerified~=true or type(ef.targetAlreadyAffected)~='boolean' or
     not bounded(ef.procChance,0,1) or not bounded(ef.saveFailChance,0,1) or
     not bounded(ef.magicResistanceBlockChance,0,1) or
     not bounded(ef.resistanceFraction,0,1) or
     not bounded(ef.valueOnApplication,0,500) or
     not bounded(ef.valueOnSuccessfulSave,0,500) or
     type(ef.successfulSaveApplies)~='boolean' or
     ef.saveOutcomesVerified~=true or
     (ef.successfulSaveApplies==false and ef.valueOnSuccessfulSave~=0) or
     ef.valueBasis~='HP_EQUIVALENT_VERIFIED' or
     (ef.stackPolicy~='STACK_PER_HIT' and ef.stackPolicy~='REFRESH_NONSTACK') then
   return nil,'EFFECT_UNVERIFIED_OR_UNSUPPORTED' end
  seen[ef.id]=true
  -- Control/debuff utility must be target-specific, not a free guessed bonus.
  if (ef.kind=='CONTROL' or ef.kind=='DEBUFF') and ef.utilityCalibrationVerified~=true then
   return nil,'CONTROL_UTILITY_VALUE_UNKNOWN' end
  -- Delayed effects must already discount remaining lifetime, target survival,
  -- prior poison, possible cures, and damage type into verified valueOnApplication.
  if (ef.kind=='POISON_DOT' or ef.kind=='OTHER_DAMAGE_OVER_TIME') and
       ef.durationAndSurvivalAdjustedVerified~=true then
   return nil,'DAMAGE_OVER_TIME_HORIZON_UNKNOWN' end
  if ef.source=='AMMO' and (w.mode~='RANGED' or w.ammoVerified~=true or
       ef.sourceResRef~=w.ammoResRef) then return nil,'AMMO_EFFECT_MISMATCH' end
  if ef.source=='LAUNCHER' and (w.mode~='RANGED' or
       ef.launcherResRef~=w.launcherResRef or not id(w.launcherResRef)) then
   return nil,'LAUNCHER_EFFECT_MISMATCH' end
  if ef.source=='WEAPON' and ef.sourceResRef~=w.resRef then
   return nil,'WEAPON_EFFECT_MISMATCH' end
  if ef.source=='ACTIVE_BUFF' and ef.buffActiveNowVerified~=true then
   return nil,'BUFF_EXPIRED_OR_UNVERIFIED' end
  if ef.stackPolicy=='STACK_PER_HIT' and ef.targetAlreadyAffected and
     ef.canStackWithExistingVerified~=true then
   return nil,'DOT_STACKING_WITH_EXISTING_UNKNOWN' end
  if not ef.targetImmune then
   local save=ef.saveFailChance
   local surviveSave=ef.successfulSaveApplies and (1-save) or 0
   local applicationProbability=save+surviveSave
   local weightedValue=save*ef.valueOnApplication+(1-save)*ef.valueOnSuccessfulSave
   local onHitProc=hit*ef.procChance*(1-ef.magicResistanceBlockChance)
   local afterResistance=1-ef.resistanceFraction
   if ef.stackPolicy=='STACK_PER_HIT' then
    sum=sum+w.apr*onHitProc*weightedValue*afterResistance
   elseif not ef.targetAlreadyAffected and applicationProbability>0 then
    -- Treat refresh-only poison as ONE application maximum per round.
    local chance=onHitProc*applicationProbability
    local conditionalValue=weightedValue/applicationProbability
    sum=sum+(1-(1-chance)^w.apr)*conditionalValue*afterResistance
   end
  end
 end
 if not bounded(sum,0,1000) then return nil,'EFFECT_VALUE_OUT_OF_BOUNDS' end
 return sum,nil
end
function M.choose(scene,previous,prioritizer)
 local v3=prioritizer
 if not v3 then return hold('V3_PRIORITIZER_NOT_WIRED') end
 if type(v3)~='function' or type(scene)~='table' or type(scene.frame)~='table' or
    type(scene.actor)~='table' or type(scene.enemy)~='table' or
    type(scene.weapons)~='table' then return hold('SCENE_INCOMPLETE') end
 local f=scene.frame
 if not id(f.snapshotId) or not id(f.effectStatusFingerprint) or
    f.completeOnHitEffectsObserved~=true or f.completePhysicalDamageObserved~=true or
    f.effectStatusSourceVerified~=true then return hold('SNAPSHOT_EFFECT_EVIDENCE_INCOMPLETE') end
 if not id(f.combatFingerprint) or #f.combatFingerprint+#f.effectStatusFingerprint+4>80 then
  return hold('FINGERPRINT_OVERFLOW') end
 local updated={}
 for _,w in ipairs(scene.weapons) do
  if type(w)~='table' then return hold('WEAPON_UNKNOWN') end
  -- No speculative APR/damage/effects are necessary for a verified
  -- excluded candidate. V3 must still confirm all inventory/ammo identifiers.
  local clone={};for k,v in pairs(w) do clone[k]=v end
  if not known_ineligible(w,scene.actor) then
   local total,why=physical(w,scene.actor,f.snapshotId)
   if not total then return hold(why,{weaponId=w.id}) end
   local ext,err=status_value(w,scene.enemy,f)
   if not ext then return hold(err,{weaponId=w.id}) end
   clone.avgDamageOnHit=total
   clone.extraEffectValue=ext
  end
  updated[#updated+1]=clone
 end
 local frm={};for k,v in pairs(f) do frm[k]=v end
 -- Effect-state changes cause V3 hysteresis to restart rather than reuse old advice.
 frm.combatFingerprint=frm.combatFingerprint..'.EF.'..frm.effectStatusFingerprint
 local candidate={};for k,v in pairs(scene) do candidate[k]=v end
 candidate.frame=frm
 candidate.weapons=updated
 local answer=v3(candidate,previous)
 answer.specialEffectsAccounting='ITEM_AMMO_LAUNCHER_BUFF_STR_EFFECTS_V4'
 answer.executable=false; answer.dispatchAuthorized=false
 return answer
end
M.strength_applies=strength_applies
return M