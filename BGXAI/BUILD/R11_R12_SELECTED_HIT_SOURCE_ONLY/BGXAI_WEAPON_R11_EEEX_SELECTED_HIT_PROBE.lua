-- BGXAI R11. SOURCE ONLY: candidate read-only EEex hit-chance / immunity probe.
-- Follows the *selected weapon* sequence in B3AttackInfo.lua; never selects an item.
-- Does not create a hook, send engine orders, set variables, write files or load automatically.
-- A successful callback is UNAUTHENTICATED until checked against a real, pinned EEex runtime.
local M={version='BGXAI_WEAPON_R11_EEEX_SELECTED_HIT_PROBE_V1',installed=false}
local function int(v,lo,hi)
 return type(v)=='number' and v==v and v~=math.huge and v~=-math.huge and
   v%1==0 and v>=lo and v<=hi
end
local function label(v)
 return type(v)=='string' and #v>=1 and #v<=128 and not v:find('[^%w_.:%-]')
end
local function result(status,reason,fields)
 local out={schema=M.version,status=status,reason=reason,
   installed=false,readOnly=true,executable=false,dispatchAuthorized=false,
   weaponSwitchAuthorized=false,ordersSent=0,actionQueueCleared=false,
   currentActionPreserved=true,manualOrderProven=false,epsQueueProven=false,
   nativeEvidenceAuthenticated=false,liveReadVerified=false,
   alternateSlotAPRVerified=false,alternateSlotHitChanceVerified=false,
   selectionMutated=false,gameFilesModified=false}
 if type(fields)=='table' then for k,v in pairs(fields) do out[k]=v end end
 return out
end
local function safe_read_sprite(source)
 local ok,eq=pcall(function() return source.m_equipment end)
 if not ok or eq==nil then return nil,'SOURCE_EQUIPMENT_UNAVAILABLE' end
 local ok2,slot,ability,items=pcall(function()
   return eq.m_selectedWeapon,eq.m_selectedWeaponAbility,eq.m_items
 end)
 if not ok2 or (not int(slot,11,14) and not int(slot,35,38)) or
    not int(ability,0,255) or items==nil then
   return nil,'SELECTED_WEAPON_OR_ABILITY_UNSUPPORTED'
 end
 local ok3,item=pcall(function() return items:get(slot) end)
 if not ok3 or item==nil then return nil,'SELECTED_ITEM_UNAVAILABLE' end
 return {slot=slot,ability=ability,item=item,eq=eq}
end
function M.inspect(source,target,eeex,context)
 -- Only a caller which explicitly supplies source + target is used: no target search.
 if source==nil or target==nil or source==target then
   return result('HOLD','SOURCE_OR_TARGET_INVALID') end
 if type(context)~='table' or not label(context.sessionId) or
    not label(context.snapshotId) or not int(context.actor,1,2147483647) or
    not int(context.targetActor,1,2147483647) or context.actor==context.targetActor or
    not int(context.sequence,1,1000000) or
    context.usesAlreadySelectedWeapon~=true or context.readOnlyProbeConsent~=true or
    context.manualEPSBoundaryProven~=false or context.switchAttempted~=false then
   return result('HOLD','CONTEXT_OR_PROBE_INTENT_INVALID') end
 if type(eeex)~='table' or type(rawget(eeex,'GetWeaponHitChance'))~='function' or
    type(rawget(eeex,'IsImmuneToWeapon'))~='function' then
   return result('HOLD','EEEX_ATTACK_INFO_FUNCTIONS_UNAVAILABLE') end
 local selected,err=safe_read_sprite(source)
 if not selected then return result('HOLD',err) end
 -- The current selection must not be mutated before / after calls (runtime protection).
 local beforeSlot,beforeAbility=selected.slot,selected.ability
 local hitOk,chance,reasoning=pcall(eeex.GetWeaponHitChance,
   source,target,selected.item,selected.ability,false)
 local immOk,immune=pcall(eeex.IsImmuneToWeapon,
   source,target,selected.slot,selected.item,selected.ability)
 local after,afterErr=safe_read_sprite(source)
 if not after or after.slot~=beforeSlot or after.ability~=beforeAbility or
    not rawequal(after.item,selected.item) then
   return result('HOLD','SELECTED_WEAPON_CHANGED_DURING_PROBE') end
 if not hitOk or not immOk then
   return result('HOLD','EEEX_READ_CALL_FAILED') end
 if not int(chance,0,100) then
   return result('HOLD','EEEX_HIT_CHANCE_UNRECOGNIZED') end
 if type(immune)~='boolean' then
   return result('HOLD','EEEX_IMMUNITY_RESULT_UNRECOGNIZED') end
 if reasoning~=nil and type(reasoning)~='string' and type(reasoning)~='table' then
   return result('HOLD','EEEX_REASONING_UNRECOGNIZED') end
 return result('SELECTED_HIT_CHANCE_CANDIDATE_ONLY','CALLER_SUPPLIED_UNAUTHENTICATED_READ',{
   sessionId=context.sessionId,snapshotId=context.snapshotId,
   actor=context.actor,targetActor=context.targetActor,sequence=context.sequence,
   selectedSlot=beforeSlot,selectedAbility=beforeAbility,hitChancePercent=chance,
   isImmuneToSelectedWeapon=immune,
   launcherIdentityProven=false, -- item resref and launcher mechanics not independently checked
   -- A successful function call does NOT grant the provenance or readiness gates.
   callerSuppliedEEexApi=true,engineMethodProvenInstalled=false,
   targetActorBindingProven=false,activeEffectCompletenessProven=false,
   exactSelectedItemResRefProven=false,
   nextNeeded={'PINNED_INSTALLED_EEEX_API_PROOF','ENGINE_GAME_THREAD_SAFE_HOOK',
    'TARGET_ACTOR_BINDING','SELECTED_AMMO_LAUNCHER_IDENTITY','EPS_MANUAL_ACTION_BOUNDARY'}})
end
return M
