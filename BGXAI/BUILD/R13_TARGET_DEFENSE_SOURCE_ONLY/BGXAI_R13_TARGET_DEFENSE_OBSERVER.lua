-- BGXAI R13: passive target defensive-stats candidate from EEex derived stats.
-- SOURCE ONLY; no hook, no game commands, no writing, no action queue changes.
-- Target AC/resistance fields are raw readings, NOT effective hit probabilities.
-- All output from injected EEex adapter is NOT authenticated to installed runtime.
local M={version='BGXAI_R13_TARGET_DEFENSE_OBSERVER_V1',installed=false}
local DEF={
 'm_nArmorClass','m_nACCrushingMod','m_nACMissileMod',
 'm_nACPiercingMod','m_nACSlashingMod',
 'm_nResistCrushing','m_nResistPiercing','m_nResistSlashing'
}
M.fields=DEF
-- BG(2)EE: effective AC against each attack kind is the general AC
-- plus the corresponding derived AC modifier. This is MODEL-ONLY until a
-- version-pinned installed EEex source validates fields and snapshot identity.
local AC_FIELDS={
 CRUSHING='m_nACCrushingMod',
 PIERCING='m_nACPiercingMod',
 SLASHING='m_nACSlashingMod',
 MISSILE='m_nACMissileMod'
}
local function effective_ac_candidate(fields)
 if type(fields)~='table' then return nil end
 local base=fields.m_nArmorClass
 if type(base)~='number' or base~=base or base%1~=0 or
    base< -60 or base>100 then return nil end
 local out={}
 for typ,key in pairs(AC_FIELDS) do
  local mod=fields[key]
  if type(mod)~='number' or mod~=mod or mod%1~=0 or
     mod< -200 or mod>200 then return nil end
  local total=base+mod
  if total< -50 or total>100 then return nil end
  out[typ]=total
 end
 return out
end
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
 if aid~=3 and aid~=30 then return output('HOLD','NOT_AN_ATTACK_CANDIDATE_ACTION') end
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
 local byAttack=full and effective_ac_candidate(second.fields) or nil
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
   targetArmorClassByAttackTypeCandidate=byAttack,
   targetArmorClassBaseCandidate=byAttack and second.fields.m_nArmorClass or nil,
   targetTypeACModelStatus=byAttack and
     'R13_DERIVED_ATTACK_TYPE_AC_MODEL_ONLY' or 'HOLD_TYPE_AC_NOT_MODELABLE',
   targetTypeACModelSnapshotId=byAttack and ctx.snapshotId or nil,
   targetTypeACNativeAuthenticated=false,
   nativeItemDamageTypeUnknown=true,
   damageTypeACResolutionUnverified=true,
   protectionsAndItemImmunitiesUnknown=true,
   actualTargetHitProbability=nil,
   actualTargetPhysicalDamageThrough=nil,
   targetDefensesReadFromInjectedAdapterOnly=true,
  })
end
return M
