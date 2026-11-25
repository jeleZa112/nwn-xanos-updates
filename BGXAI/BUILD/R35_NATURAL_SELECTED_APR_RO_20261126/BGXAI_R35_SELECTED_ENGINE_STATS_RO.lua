-- BGXAI R35: EEex selected APR/THAC0 passive observation ONLY.
-- SOURCE ONLY. No new EEex listener, game writes, action orders or slot switch.
-- Designed to be called by the already-existing R33 callback, not installed.
-- The EEex API EEex_Sprite_GetActiveStats() returns m_tempStats while effect
-- processing is ongoing (m_bAllowEffectListCall==0); reject that state.
-- It cannot calculate an unselected slot's final effective APR or THAC0.
local M={version='BGXAI_R35_SELECTED_ENGINE_STATS_RO_V1',installed=false}
local APR={[0]=0,[1]=1,[2]=2,[3]=3,[4]=4,[5]=5,
           [6]=0.5,[7]=1.5,[8]=2.5,[9]=3.5,[10]=4.5}
local function raw(fn)
 local ok,result=pcall(fn)
 if ok then return result end
 return nil
end
local function integer(x,lo,hi)
 return type(x)=='number' and x==math.floor(x) and x>=lo and x<=hi
end
local function result(status,reason)
 return {schema='BGXAI_R35_SELECTED_ENGINE_STATS_RO_V1',
         status=status,reason=reason,installed=false,readOnly=true,
         ordersSent=0,localsWritten=0,gameModified=false,
         actionQueueCleared=false,currentActionPreserved=true,
         dispatchAuthorized=false,weaponSwitchAuthorized=false,
         selectedOnly=true,otherSlotEffectiveAPRVerified=false,
         matchedBuffContextVerified=false,fullActiveEffectsVerified=false,
         manualAndEPSOriginVerified=false,launcherAmmoBindingVerified=false,
         sameSessionTemporalAlignmentVerified=false}
end
function M.observe(sprite,statsReader)
 local out=result('HOLD_SELECTED_STATS_UNVERIFIED','NO_SPRITE')
 if sprite==nil then return out end
 local actor=raw(function()return sprite.m_id end)
 if not integer(actor,1,2147483647) then
  out.reason='ACTOR_ID_UNREADABLE';return out
 end
 local guard1=raw(function()return sprite.m_bAllowEffectListCall end)
 if not integer(guard1,1,65535) then
  out.reason='ACTIVE_STATS_EFFECT_LIST_IN_PROGRESS_OR_UNVERIFIED';return out
 end
 local eq=raw(function()return sprite.m_equipment end)
 if eq==nil then out.reason='EQUIPMENT_UNREADABLE';return out end
 local slot1=raw(function()return eq.m_selectedWeapon end)
 local ability1=raw(function()return eq.m_selectedWeaponAbility end)
 if not integer(slot1,0,65535) or not integer(ability1,0,65535) then
  out.reason='SELECTED_SLOT_OR_ABILITY_UNREADABLE';return out
 end
 if statsReader==nil then statsReader=EEex_Sprite_GetActiveStats end
 if type(statsReader)~='function' then
  out.reason='EEEX_ACTIVE_STATS_API_UNAVAILABLE';return out
 end
 local stats1=raw(function()return statsReader(sprite)end)
 if stats1==nil then out.reason='ACTIVE_STATS_MISSING';return out end
 local apr1=raw(function()return stats1.m_nNumberOfAttacks end)
 local thac1=raw(function()return stats1.m_nTHAC0 end)
 if not integer(apr1,0,10) or not integer(thac1,-100,100) then
  out.reason='APR_OR_THAC0_UNREADABLE';return out
 end
 -- Second read in the same synchronous callback catches obvious drift.
 -- It is NOT proof of a complete effect list or snapshot ownership.
 local stats2=raw(function()return statsReader(sprite)end)
 local apr2=raw(function()return stats2.m_nNumberOfAttacks end)
 local thac2=raw(function()return stats2.m_nTHAC0 end)
 local slot2=raw(function()return eq.m_selectedWeapon end)
 local ability2=raw(function()return eq.m_selectedWeaponAbility end)
 local guard2=raw(function()return sprite.m_bAllowEffectListCall end)
 local actor2=raw(function()return sprite.m_id end)
 if guard2~=guard1 or actor2~=actor or
    slot1~=slot2 or ability1~=ability2 or apr1~=apr2 or thac1~=thac2 then
  out.reason='SAME_CALLBACK_STATS_OR_EQUIPMENT_DRIFT';return out
 end
 out.status='SELECTED_APR_THAC0_DOUBLE_READ_STABLE_PASSIVE'
 out.reason=nil
 out.actorRaw=actor
 out.selectedSlotRaw=slot1
 out.selectedAbilityRaw=ability1
 out.selectedAPRKeyRaw=apr1
 out.selectedAPRIfStandardDecoder=APR[apr1]
 out.selectedTHAC0Raw=thac1
 out.source='EEEX_ACTIVE_DERIVED_STATS_CURRENT_SELECTED'
 out.liveSameCallbackDoubleRead=true
 out.activeStatsNotTempObserved=true
 return out
end
function M.compare(first,second)
 local out=result('HOLD_NATURAL_SELECTED_COMPARISON','BAD_INPUT')
 if type(first)~='table' or type(second)~='table' or
    first.schema~=out.schema or second.schema~=out.schema or
    first.status~='SELECTED_APR_THAC0_DOUBLE_READ_STABLE_PASSIVE' or
    second.status~='SELECTED_APR_THAC0_DOUBLE_READ_STABLE_PASSIVE' then
  return out
 end
 if first.actorRaw~=second.actorRaw then
  out.reason='CROSS_ACTOR';return out
 end
 if first.selectedSlotRaw==second.selectedSlotRaw then
  out.reason='SAME_SELECTED_SLOT';return out
 end
 out.status='DIFFERENT_NATURALLY_SELECTED_SLOTS_RAW_WITNESSED'
 out.reason=nil
 out.firstSelectedSlotRaw=first.selectedSlotRaw
 out.secondSelectedSlotRaw=second.selectedSlotRaw
 out.firstSelectedAPRKeyRaw=first.selectedAPRKeyRaw
 out.secondSelectedAPRKeyRaw=second.selectedAPRKeyRaw
 out.firstSelectedTHAC0Raw=first.selectedTHAC0Raw
 out.secondSelectedTHAC0Raw=second.selectedTHAC0Raw
 -- No assumption that selected ammo implies a specific launcher; no active
 -- effects fingerprint, action ownership or same-context counterfactual.
 return out
end
return M
