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
  quickWeaponsRaw=r2.quickWeapons,quiversRaw=r2.quivers,
  sampledStatsRaw={m_nNumberOfAttacks=rawApr,
   m_nTHAC0=f.m_nTHAC0,m_nSTR=f.m_nSTR,
   m_nSTRExtra=f.m_nSTRExtra,m_bImprovedHaste=f.m_bImprovedHaste,
   m_nHitBonus=f.m_nHitBonus},
  sameLuaListenerInvocation=true,nativeEventTokenAuthenticated=false,
  engineSessionVerified=false,alternativeAPRVerified=false,
  launcherAmmoPairVerified=false,completeActiveEffectsVerified=false,
  epsManualQueueVerified=false,readOnly=true,sourceOnly=true,
  gameModified=false,ordersSent=0,localsWritten=0,
  dispatchAuthorized=false,weaponSwitchAuthorized=false,
  currentActionPreserved=true,actionQueueCleared=false}
end

-- Strict bounded JSON for the future single existing-updater diagnostic writer.
-- No resource pointer, arbitrary object or user-supplied string is serialized.
local function jnum(v,lo,hi)
 if int(v,lo,hi) then return tostring(v) end
 return 'null'
end
local function jstr(v)
 if type(v)~='string' or #v<1 or #v>8 or v:find('[^%w_]') then
  return 'null' end
 return '"'..v:upper()..'"'
end
local function jrawstr(v)
 if type(v)~='string' or #v<1 or #v>48 then return 'null' end
 for i=1,#v do local b=v:byte(i);if b<32 or b>126 then return 'null' end end
 return '"'..v:gsub('\\','\\\\'):gsub('"','\\"')..'"'
end
local function jstatus(v)
 local allowed={SOURCE_RAW_OBSERVED=true,ACTION_SOURCE_ACTION_UNAVAILABLE=true,
  ACTION_SOURCE_FIELD_UNAVAILABLE=true,ACTION_SOURCE_POINTER_UNAVAILABLE=true,
  EEEX_READLSTRING_UNAVAILABLE=true,ACTION_SOURCE_READ_FAILED=true,
  ACTION_SOURCE_TRUNCATED=true,ACTION_SOURCE_EMPTY=true,
  ACTION_SOURCE_NONPRINTABLE=true,ACTION_SOURCE_STRING_INVALID=true,
  ACTION_SOURCE_STATUS_CHANGED_DURING_READ=true,
  ACTION_SOURCE_CHANGED_DURING_READ=true,
  ACTION_SOURCE_STATUS_CHANGED_DURING_CAPTURE=true,
  ACTION_CHANGED_DURING_CONTEXT_SNAPSHOT=true}
 return allowed[v] and ('"'..v..'"') or 'null'
end
local function jslots(arr,n)
 if type(arr)~='table' or #arr~=n then return '[]' end
 local out={}
 for i=1,n do
  local v=arr[i]
  if type(v)~='table' then return '[]' end
  out[i]='{"slot":'..jnum(v.index,0,38)..
    ',"resrefRaw":'..jstr(v.itemResrefRaw)..
    ',"useCount1Raw":'..jnum(v.useCount1Raw,0,65535)..
    ',"useCount2Raw":'..jnum(v.useCount2Raw,0,65535)..
    ',"useCount3Raw":'..jnum(v.useCount3Raw,0,65535)..'}'
 end
 return '['..table.concat(out,',')..']'
end
local function jstats(stats)
 local keys={'m_nNumberOfAttacks','m_nTHAC0','m_nSTR',
  'm_nSTRExtra','m_bImprovedHaste','m_nHitBonus'}
 local out={}
 for _,key in ipairs(keys) do
  local v=type(stats)=='table' and stats[key] or nil
  out[#out+1]='"'..key..'":'..jnum(v,-2147483648,2147483647)
 end
 return '{'..table.concat(out,',')..'}'
end
function R27.toConsoleJson(sample)
 if type(sample)~='table' or sample.schema~=R27.schema or
   sample.readOnly~=true or sample.ordersSent~=0 or
   sample.dispatchAuthorized~=false or sample.weaponSwitchAuthorized~=false then
  return nil end
 local allowed={CURRENT_SELECTED_SAME_CALLBACK_SOURCE_CANDIDATE=true,
  HOLD_SINGLE_CALLBACK_NO_DISPATCH=true}
 if not allowed[sample.status] then return nil end
 local status=sample.status
 return '{"schema":"'..R27.schema..'","type":"R27_SINGLE_CALLBACK",'..
  '"status":"'..status..'","seq":'..jnum(sample.collectorOrdinal,1,64)..
  ',"actor":'..jnum(sample.actor,1,2147483647)..
  ',"partyIndex":'..jnum(sample.partyIndex,0,5)..
  ',"actionRaw":'..jnum(sample.actionRaw,0,65535)..
  ',"selectedWeaponRaw":'..jnum(sample.selectedWeaponRaw,0,65535)..
  ',"selectedAbilityRaw":'..jnum(sample.selectedAbilityRaw,0,65535)..
  ',"selectedAprKeyRaw":'..jnum(sample.selectedAprKeyRaw,0,10)..
  ',"quickWeaponsRaw":'..jslots(sample.quickWeaponsRaw,4)..
  ',"quiversRaw":'..jslots(sample.quiversRaw,4)..
  ',"selectedStatsRaw":'..jstats(sample.sampledStatsRaw)..
  ',"sameLuaListenerInvocation":'..tostring(sample.sameLuaListenerInvocation==true)..
  ',"nativeEventTokenAuthenticated":false,"engineSessionVerified":false,'..
  '"alternativeAPRVerified":false,"launcherAmmoPairVerified":false,'..
  '"completeActiveEffectsVerified":false,"epsManualQueueVerified":false,'..
  '"ordersSent":0,"localsWritten":0,"dispatchAuthorized":false,'..
  '"weaponSwitchAuthorized":false,"readOnly":true}'
end
-- Makes a passive console sink but NEVER calls EEex to register it.
function R27.prepareConsolePilot(ports)
 if type(ports)~='table' or type(ports.portraitIndex)~='function' or
  type(ports.getActiveStats)~='function' or
  type(ports.emitString)~='function' then
  return nil,'CONSOLE_PORTS_MISSING' end
 local listener,err=R27.makeListener({
  portraitIndex=ports.portraitIndex,getActiveStats=ports.getActiveStats,
  emit=function(sample)
   local line=R27.toConsoleJson(sample)
   if line then ports.emitString('[BGXR27] '..line) end
  end})
 if not listener then return nil,err end
 return {status='SOURCE_ONLY_LISTENER_READY_NOT_REGISTERED',
   registered=false,installAuthorized=false,dispatchAuthorized=false,
   listener=listener}
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
