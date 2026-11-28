-- BGXAI R13: passive target defensive-stats candidate from EEex derived stats.
-- SOURCE ONLY; no hook, no game commands, no writing, no action queue changes.
-- Target AC/resistance fields are raw readings, NOT effective hit probabilities.
-- All output from injected EEex adapter is NOT authenticated to installed runtime.
local M={version='BGXAI_R13_TARGET_DEFENSE_OBSERVER_V1',installed=false}
local DEF={
 'm_nArmorClass','m_nACCrushingMod','m_nACMissileMod',
 'm_nACPiercingMod','m_nACSlashingMod',
 'm_nResistCrushing','m_nResistPiercing','m_nResistSlashing',
 'm_nResistMissile'
}
M.fields=DEF
local function int(x,lo,hi)
 return type(x)=='number' and x==x and x~=math.huge and x~=-math.huge and
  x%1==0 and x>=lo and x<=hi
end
local function ident(x)
 return type(x)=='string' and #x>=1 and #x<=128 and not x:find('[^%w_.:%-]')
end
local function output(status,reason,extra)
 local o={schema=M.version,status=status,reason=reason,
  installed=false,executable=false,readOnly=true,
  dispatchAuthorized=false,weaponSwitchAuthorized=false,rankingAuthorized=false,
  ordersSent=0,actionQueueCleared=false,currentActionPreserved=true,
  gameFilesModified=false,nativeEvidenceAuthenticated=false,liveReadVerified=false,
  runtimeApiAuthenticated=false,hostileTargetProven=false,attackActionProven=false,
  targetProtectionFullyObserved=false,exactHitChanceProven=false,
  selectedItemRefVerified=false,alternateSlotAPRVerified=false,
  epsQueueProven=false,manualOrderProven=false,
  eligibleForR10Model=false,eligibleForR12HitChance=false}
 if type(extra)=='table' then for k,v in pairs(extra) do o[k]=v end end
 return o
end
local function event(sprite,action)
 local ok,sourceId,actionId,targetId=pcall(function()
  return sprite.m_id,action.m_actionID,action.m_acteeID.m_Instance
 end)
 if not ok or not int(sourceId,1,2147483647) or
  not int(targetId,1,2147483647) or sourceId==targetId or
  not int(actionId,0,65535) then return nil end
 return sourceId,actionId,targetId
end
local function selection(sprite)
 local ok,slot,ability,item=pcall(function()
  local e=sprite.m_equipment
  local s=e.m_selectedWeapon
  return s,e.m_selectedWeaponAbility,e.m_items:get(s)
 end)
 if not ok or (not int(slot,35,38) and not int(slot,11,14)) or
  not int(ability,0,255) or item==nil then return nil end
 return slot,ability,item
end
local function is_sprite(target,id)
 local ok,a,b=pcall(function()return target.m_id,target:isSprite(true) end)
 return ok and a==id and b==true
end
local function stable(source,action,api,sourceId,actionId,targetId,target,slot,ability,item)
 local s,a,t=event(source,action)
 if s~=sourceId or a~=actionId or t~=targetId then return false end
 local x,y,z=selection(source)
 if x~=slot or y~=ability or not rawequal(z,item) then return false end
 local ok,got=pcall(api.GameObject_Get,targetId)
 return ok and rawequal(got,target) and is_sprite(got,targetId)
end
local function read_fields(api,target)
 -- EEex 1.1.7 getActiveStats() uses m_tempStats when the effect list is
 -- being processed. Reuse R35's existing read guard, not a new stat API.
 local guardOk,guard=pcall(function()return target.m_bAllowEffectListCall end)
 if not guardOk or not int(guard,1,65535) then
  return nil,'TARGET_ACTIVE_STATS_TEMP_OR_EFFECTS_IN_PROGRESS' end
 local ok,stats=pcall(api.GetActiveStats,target)
 if not ok or stats==nil then return nil,'TARGET_ACTIVE_STATS_UNAVAILABLE' end
 local fields,missing={},{}
 for _,name in ipairs(DEF) do
  local good,value=pcall(function()return stats[name] end)
  local lo,hi= name=='m_nArmorClass' and -60 or -200,
               name=='m_nArmorClass' and 100 or 200
  if good and int(value,lo,hi) then fields[name]=value
  else fields[name]=false;missing[#missing+1]=name end
 end
 local afterOk,after=pcall(function()return target.m_bAllowEffectListCall end)
 if not afterOk or after~=guard then
  return nil,'TARGET_ACTIVE_STATS_GUARD_CHANGED' end
 return {fields=fields,missing=missing},nil
end
local function same_reading(a,b)
 if not a or not b then return false end
 for _,name in ipairs(DEF) do
  if a.fields[name]~=b.fields[name] then return false end
 end
 return true
end
function M.inspect(source,action,api,ctx)
 if source==nil or action==nil then return output('HOLD','SOURCE_OR_ACTION_MISSING') end
 if type(ctx)~='table' or not ident(ctx.sessionId) or
  not ident(ctx.snapshotId) or not int(ctx.sequence,1,1000000) or
  not int(ctx.actor,1,2147483647) or not int(ctx.targetActor,1,2147483647) or
  not int(ctx.actionRaw,0,65535) or
  not int(ctx.selectedSlot,11,38) or not int(ctx.selectedAbility,0,255) or
  ctx.readOnlyContextOnly~=true or ctx.switchAttempted~=false or
  ctx.manualEPSBoundaryProven~=false then return output('HOLD','CONTEXT_INCOMPLETE') end
 if type(api)~='table' or type(rawget(api,'GameObject_Get'))~='function' or
  type(rawget(api,'GetActiveStats'))~='function' then
  return output('HOLD','REQUIRED_BASE_EEEX_ADAPTER_MISSING') end
 local sid,aid,tid=event(source,action)
 if not sid then return output('HOLD','ACTION_IDENTITY_UNREADABLE') end
 if sid~=ctx.actor or aid~=ctx.actionRaw or tid~=ctx.targetActor then
  return output('HOLD','ACTION_CONTEXT_MISMATCH') end
 -- Started action IDs are only candidate values; hostility/priority not proven.
 -- ACTION.IDS in BGEE / actual BGXAI R27 logs: AttackOneRound=105,
 -- AttackReevaluate=134. These bind a candidate target, NOT a free round.
 if aid~=3 and aid~=30 and aid~=105 and aid~=134 then
  return output('HOLD','NOT_AN_ATTACK_CANDIDATE_ACTION') end
 local slot,ability,item=selection(source)
 if not slot then return output('HOLD','SELECTION_UNREADABLE') end
 if slot~=ctx.selectedSlot or ability~=ctx.selectedAbility then
  return output('HOLD','SELECTION_CONTEXT_MISMATCH') end
 local ok,target=pcall(api.GameObject_Get,tid)
 if not ok or target==nil or not is_sprite(target,tid) then
  return output('HOLD','TARGET_NOT_A_SPRITE') end
 if not stable(source,action,api,sid,aid,tid,target,slot,ability,item) then
  return output('HOLD','SOURCE_TARGET_CHANGED_BEFORE_READ') end
 local first,err=read_fields(api,target)
 if not first then return output('HOLD',err) end
 if not stable(source,action,api,sid,aid,tid,target,slot,ability,item) then
  return output('HOLD','SOURCE_TARGET_CHANGED_DURING_READ') end
 local second,err2=read_fields(api,target)
 if not second then return output('HOLD',err2) end
 if not stable(source,action,api,sid,aid,tid,target,slot,ability,item) then
  return output('HOLD','SOURCE_TARGET_CHANGED_AFTER_READ') end
 if not same_reading(first,second) then
  return output('HOLD','DEFENSE_STATS_CHANGED_DURING_READ') end
 local full=#second.missing==0
 return output(full and 'TARGET_RAW_DEFENSE_FIELDS_CANDIDATE_ONLY' or
  'TARGET_PARTIAL_DEFENSE_FIELDS_CANDIDATE_ONLY',
  full and 'UNVERIFIED_IN_NATIVE_EEEX_AND_EFFECTS_UNKNOWN' or
  'SOME_RAW_DEFENSE_FIELDS_UNREADABLE',{
   sessionId=ctx.sessionId,snapshotId=ctx.snapshotId,sequence=ctx.sequence,
   sourceActor=sid,targetActor=tid,rawActionId=aid,
   selectedSlot=slot,selectedAbility=ability,
   selectedSlotIsAmmo=(slot>=11 and slot<=14),
   rawFields=second.fields,missingFields=second.missing,
   rawDefenseFieldsComplete=full,allDamageTypesModeled=false,
   nativeItemDamageTypeUnknown=true,
   damageTypeACResolutionUnverified=true,
   protectionsAndItemImmunitiesUnknown=true,
   actualTargetHitProbability=nil,
   actualTargetPhysicalDamageThrough=nil,
   targetDefensesReadFromInjectedAdapterOnly=true,
   activeStatsNotTempDoubleRead=true,
  })
end
local CORE=M

-- BGXAI R13 bounded runtime wrapper. SOURCE ONLY, NOT INSTALLED.
-- Adds ONE passive started-action listener; EPS/R4 listeners are not modified.
-- Does not issue orders, touch queues, or replace existing mods.
local R={version='BGXAI_R13_TARGET_DEFENSE_RUNTIME_RO',registered=false,
 limit=64,recorded=0,skipped=0,errors=0,writer='UNINITIALIZED',ordersSent=0,
 active=false,sessionId='BGXTD13_UNAUTHENTICATED'}
BGXTargetDefenseR13=R
local function safe(f)
 local ok,v=pcall(f)
 if ok then return v end
 return nil
end
local function numeric(n,lo,hi)
 if type(n)=='number' and n==n and n~=math.huge and n~=-math.huge and
    n%1==0 and n>=lo and n<=hi then return tostring(n) end
 return 'null'
end
local function party(id)
 if type(id)~='number' or id%1~=0 or id<1 or id>2147483647 then return nil end
 for p=0,5 do
  if safe(function() return EEex_Sprite_GetInPortraitID(p) end)==id then return p end
 end
 return nil
end
local function report(s)
 if R.handle then
  local ok=pcall(function()
   R.handle:write(s,'\n')
   if R.recorded%8==0 then R.handle:flush() end
  end)
  if ok then return true end
  R.errors=R.errors+1
  safe(function() R.handle:close() end)
  R.handle=nil
 end
 if type(Infinity_Log)=='function' then
  local ok=pcall(Infinity_Log,'[BGXTD13] '..s)
  if ok then R.writer='CONSOLE_FALLBACK';return true end
 end
 if type(print)=='function' then
  local ok=pcall(print,'[BGXTD13] '..s)
  if ok then R.writer='CONSOLE_FALLBACK';return true end
 end
 R.writer='NO_OUTPUT_SINK';return false
end
local function allowedStatus(s)
 return ({TARGET_RAW_DEFENSE_FIELDS_CANDIDATE_ONLY=true,
 TARGET_PARTIAL_DEFENSE_FIELDS_CANDIDATE_ONLY=true,HOLD=true})[s]
end
local function encode_fields(v)
 local x={}
 for _,name in ipairs(CORE.fields) do
  local raw=type(v)=='table' and v[name] or nil
  x[#x+1]='"'..name..'":'..numeric(raw,-200,200)
 end
 return '{'..table.concat(x,',')..'}'
end
local function event_json(q,partyIndex)
 local st=allowedStatus(q.status) and q.status or 'HOLD'
 return '{"schema":"BGXAI_R13_TARGET_DEFENSE_RUNTIME_RO",'..
  '"type":"DEFENSE","seq":'..numeric(R.recorded,1,64)..
  ',"partyIndex":'..numeric(partyIndex,0,5)..
  ',"sourceActor":'..numeric(q.sourceActor,1,2147483647)..
  ',"targetActor":'..numeric(q.targetActor,1,2147483647)..
  ',"selectedSlot":'..numeric(q.selectedSlot,11,38)..
  ',"selectedAbility":'..numeric(q.selectedAbility,0,255)..
  ',"rawActionId":'..numeric(q.rawActionId,0,65535)..
  ',"status":"'..st..'","fields":'..encode_fields(q.rawFields)..
  ',"runtimeApiAuthenticated":false,"exactHitChanceProven":false,'..
  '"sourceTargetPairAuthenticated":false,'..
  '"allProtectionsObserved":false,"alternateSlotAPRVerified":false,'..
  '"manualOrderProven":false,"epsQueueProven":false,'..
  '"weaponSwitchAuthorized":false,"dispatchAuthorized":false}'
end
function R.on_started(sprite,action)
 local ok=pcall(function()
  if not R.active or R.recorded>=R.limit then R.skipped=R.skipped+1;return end
  local id=safe(function()return sprite.m_id end)
  local p=party(id)
  if p==nil then return end
  local actionRaw=safe(function()return action.m_actionID end)
  if actionRaw~=3 and actionRaw~=30 and
    actionRaw~=105 and actionRaw~=134 then return end
  R.recorded=R.recorded+1
  local context={
   sessionId=R.sessionId,snapshotId='BGXTD13_'..tostring(R.recorded),
   sequence=R.recorded,actor=id,
   targetActor=safe(function() return action.m_acteeID.m_Instance end),
   actionRaw=actionRaw,
   selectedSlot=safe(function()return sprite.m_equipment.m_selectedWeapon end),
   selectedAbility=safe(function()return sprite.m_equipment.m_selectedWeaponAbility end),
   readOnlyContextOnly=true,switchAttempted=false,manualEPSBoundaryProven=false,
  }
  local api={GameObject_Get=EEex_GameObject_Get,GetActiveStats=EEex_Sprite_GetActiveStats}
  local value=CORE.inspect(sprite,action,api,context)
  report(event_json(value,p))
 end)
 if not ok then R.errors=R.errors+1 end
end
local function init()
 if type(EEex_Action_AddSpriteStartedActionListener)~='function' or
  type(EEex_Sprite_GetInPortraitID)~='function' or
  type(EEex_Sprite_GetActiveStats)~='function' or
  type(EEex_GameObject_Get)~='function' then
  R.writer='REQUIRED_EEEX_FUNCTION_MISSING';return false end
 if type(io)=='table' and type(io.open)=='function' and
    type(os)=='table' and type(os.getenv)=='function' then
  local home=safe(function()return os.getenv('USERPROFILE')end)
  if type(home)=='string' and #home>=4 and #home<=260 then
   -- Output is outside the game folder; if unavailable fall back to console.
   R.handle=safe(function()
    return io.open(home..'\\Documents\\BGXAI_LIVE_REPORTS\\BGXAI_R13_TARGET_DEFENSE_RAW.jsonl','a')
   end)
  end
 end
 if R.handle then R.writer='FILE'
 elseif type(Infinity_Log)=='function' or type(print)=='function' then
  R.writer='CONSOLE_FALLBACK'
 else R.writer='NO_OUTPUT_SINK';return false end
 if not report('{"schema":"BGXAI_R13_TARGET_DEFENSE_RUNTIME_RO",'..
    '"type":"SESSION","readOnly":true,"liveReadVerified":false,'..
    '"weaponSwitchAuthorized":false}') then return false end
 local ok=pcall(function()EEex_Action_AddSpriteStartedActionListener(R.on_started)end)
 if not ok then R.writer='LISTENER_REGISTRATION_FAILED';return false end
 R.registered=true;R.active=true
 report('{"schema":"BGXAI_R13_TARGET_DEFENSE_RUNTIME_RO",'..
  '"type":"READY","hookRegistered":true,'..
  '"runtimeApiAuthenticated":false,"weaponSwitchAuthorized":false}')
 return true
end
R.initialized=init()
