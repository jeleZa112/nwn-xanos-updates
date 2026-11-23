-- BGXAI R27 read-only single-callback candidate.
-- This file is *source only*. It does not register a hook by itself.
-- It composes unchanged R2 and R4 observation cores directly in one call.
-- No item:getAbility, getLauncher, Demand, BCS/LOCALS, inventory or actions.
local R27 = {schema='BGXAI_R27_SINGLE_CALLBACK_SELECTED_RO_V1',
  sourceOnly=true, registered=false, recorded=0, limit=64, errors=0,
  gameModified=false, ordersSent=0}

local function int(v,lo,hi)
 return type(v)=='number' and v==v and v~=math.huge and v~=-math.huge
  and v%1==0 and v>=lo and v<=hi
end
local function scalar(obj,key,lo,hi)
 if obj==nil then return nil end
 local ok,val=pcall(function() return obj[key] end)
 if ok and int(val,lo,hi) then return val end
 return nil
end
local function before_after(sprite,action)
 local actor=scalar(sprite,'m_id',1,2147483647)
 local aid=scalar(action,'m_actionID',0,65535)
 local ok,eq=pcall(function() return sprite.m_equipment end)
 if not ok then eq=nil end
 local weapon=scalar(eq,'m_selectedWeapon',0,65535)
 local ability=scalar(eq,'m_selectedWeaponAbility',0,65535)
 return {actor=actor,action=aid,weapon=weapon,ability=ability}
end
local function same(a,b)
 return a.actor~=nil and a.action~=nil and a.weapon~=nil and
   a.ability~=nil and a.actor==b.actor and a.action==b.action and
   a.weapon==b.weapon and a.ability==b.ability
end
local function hold(reason,ord)
 return {schema=R27.schema,status='HOLD_SINGLE_CALLBACK_NO_DISPATCH',
  reason=reason,collectorOrdinal=ord,readOnly=true,sourceOnly=true,
  gameModified=false,ordersSent=0,localsWritten=0,
  dispatchAuthorized=false,weaponSwitchAuthorized=false,
  currentActionPreserved=true,actionQueueCleared=false,
  nativeEventTokenAuthenticated=false,alternativeAPRVerified=false,
  launcherAmmoPairVerified=false,completeActiveEffectsVerified=false,
  epsManualQueueVerified=false,engineSessionVerified=false}
end
R27.hold=hold
-- Safe to use in a controlled unit test; callable from a future separately
-- approved EEex action-start listener. The read-only cores do all raw reads.
function R27.observe(sprite,action,partyIndex,getActiveStats)
 if sprite==nil or action==nil or not int(partyIndex,0,5) then
  return hold('ACTOR_ACTION_OR_PARTY_UNAVAILABLE') end
 local b=before_after(sprite,action)
 if not same(b,b) then return hold('START_EVENT_KEYS_UNREADABLE') end
 local ok2,r2=pcall(R2_CORE.observe_sprite,sprite)
 if not ok2 or type(r2)~='table' then return hold('R2_CORE_EXCEPTION') end
 local ok4,r4=pcall(R4_CORE.observe,sprite,action,partyIndex,getActiveStats)
 if not ok4 or type(r4)~='table' then return hold('R4_CORE_EXCEPTION') end
 local a=before_after(sprite,action)
 if not same(b,a) then return hold('SELECTION_OR_ACTION_CHANGED_DURING_CAPTURE') end
 if r2.actorId~=b.actor or r4.actorId~=b.actor or
  r2.selectedWeaponRaw~=b.weapon or r4.selectedWeaponRaw~=b.weapon or
  r2.selectedAbilityRaw~=b.ability or r4.selectedAbilityRaw~=b.ability or
  r4.actionRaw~=b.action or r4.partyIndex~=partyIndex then
  return hold('R2_R4_SCALARS_DISAGREE') end
 local f=r4.fields
 local rawApr=type(f)=='table' and f.m_nNumberOfAttacks or nil
 if not int(rawApr,0,10) then return hold('CURRENT_SELECTED_APR_UNAVAILABLE') end
 -- Observe but never turn a selected-only APR into alternative-slot evidence.
 -- The R2 slot data are still only raw candidates, not validated items.
 return {schema=R27.schema,status='CURRENT_SELECTED_SAME_CALLBACK_SOURCE_CANDIDATE',
  actor=b.actor,partyIndex=partyIndex,actionRaw=b.action,
  selectedWeaponRaw=b.weapon,selectedAbilityRaw=b.ability,
  selectedAprKeyRaw=rawApr,r2Status=r2.status,r4Status=r4.status,
  sameLuaListenerInvocation=true,nativeEventTokenAuthenticated=false,
  engineSessionVerified=false,alternativeAPRVerified=false,
  launcherAmmoPairVerified=false,completeActiveEffectsVerified=false,
  epsManualQueueVerified=false,readOnly=true,sourceOnly=true,
  gameModified=false,ordersSent=0,localsWritten=0,
  dispatchAuthorized=false,weaponSwitchAuthorized=false,
  currentActionPreserved=true,actionQueueCleared=false}
end

-- This candidate is deliberately NOT auto-registered. A separate typed
-- authorization, preflight, external backup and single-updater install design
-- are required before any game integration.
function R27.makeListener(deps)
 if type(deps)~='table' or type(deps.portraitIndex)~='function' or
    type(deps.getActiveStats)~='function' or type(deps.emit)~='function' then
  return nil,'DEPENDENCIES_UNPROVEN' end
 return function(sprite,action)
  if R27.recorded>=R27.limit then return end
  local id=scalar(sprite,'m_id',1,2147483647)
  if not id then return end
  local ok,p=pcall(deps.portraitIndex,id)
  if not ok or not int(p,0,5) then return end
  local result=R27.observe(sprite,action,p,deps.getActiveStats)
  R27.recorded=R27.recorded+1
  result.collectorOrdinal=R27.recorded
  -- Results intentionally remain read-only regardless of observer failure.
  local emitted=pcall(deps.emit,result)
  if not emitted then R27.errors=R27.errors+1 end
 end
end
return R27
