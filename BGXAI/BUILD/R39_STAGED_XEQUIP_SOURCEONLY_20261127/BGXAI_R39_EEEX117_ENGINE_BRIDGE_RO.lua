-- BGXAI R39 native EEex 1.1.7 partial physical/trigger adapter, SOURCE ONLY.
-- Reuses existing R37 inventory access semantics and 084 native trigger evaluator.
-- No registration, no local/global writes, no arming, no XEquipItem, no game orders.
-- Crucially: physical match and instant trigger truth do NOT authorize any action.
local M={schema='BGXAI_R39_EEEX117_ENGINE_BRIDGE_READONLY_V1',sourceOnly=true,
         registered=false,armAuthorized=false,dispatchAuthorized=false,ordersSent=0}
local TRIGGERS={
 'Name("*GCLERIC",Myself)',
 'Class(Myself,CLERIC)',
 'ActionListEmpty()',
 'CombatCounter(0)',
 '!See([EVILCUTOFF])',
 '!GlobalTimerNotExpired("MO_SpellCast","LOCALS")',
 'ModalState(NONE)',
 '!StateCheck(Myself,STATE_PANIC)',
 '!StateCheck(Myself,STATE_HELPLESS)',
 'CheckItemSlot(Myself,"STAF01",SLOT_MISC5)',
 '!HasItemSlot(Myself,SLOT_WEAPON0)',
 '!HasItemSlot(Myself,SLOT_SHIELD)',
}
local function int(x,lo,hi)
 return type(x)=='number' and x==x and x%1==0 and x>=lo and x<=hi
end
local function prop(obj,key)
 if obj==nil then return nil end
 local ok,v=pcall(function() return obj[key] end)
 return ok and v or nil
end
local function safe(f,...)
 if type(f)~='function' then return nil end
 local ok,x=pcall(f,...)
 return ok and x or nil
end
local function report(status,flags)
 local r={schema=M.schema,status=status,sourceOnly=true,readOnly=true,
  nativeR39Compiled=false,installed=false,ordersSent=0,localsWritten=0,
  armAuthorized=false,dispatchAuthorized=false,
  actualItemUsabilityVerified=false,activeEffectsFullyChecked=false,
  epsManualOriginVerified=false,currentActionContinuityVerified=false,
  nativeTriggerSideEffectsExcluded=false,canArm=false,gameModified=false}
 if flags then for k,v in pairs(flags) do r[k]=v end end
 return r
end
local function slot(items,n)
 local getter=prop(items,'get')
 if type(getter)~='function' then return nil end
 local ok,item=pcall(getter,items,n)
 if not ok then return nil end
 if item==nil then return {empty=true} end
 local ref=prop(item,'cResRef')
 local getref=prop(ref,'get')
 if type(getref)~='function' then return nil end
 local res=safe(getref,ref)
 local flags=prop(item,'m_flags')
 local a,b,c=prop(item,'m_useCount1'),prop(item,'m_useCount2'),prop(item,'m_useCount3')
 if type(res)~='string' or #res<1 or #res>8 or res:find('[^%w_]') or
  not int(flags,0,4294967295) or
  not int(a,0,65535) or not int(b,0,65535) or not int(c,0,65535) then
  return nil
 end
 return {empty=false,resref=res:upper(),flags=flags,charges={a,b,c}}
end
local function exactPhysical(sprite,selected,portraitId)
 local actor=prop(sprite,'m_id')
 if not int(actor,1,2147483647) or portraitId~=actor then
  return nil,'HOLD_PORTRAIT_ACTOR_ID'
 end
 -- One *selected* portrait only, not just EEex_Sprite_GetSelectedID() leader.
 if type(selected)~='table' or #selected~=1 or selected[1]~=actor then
  return nil,'HOLD_SELECTION_NOT_EXACTLY_THIS_ACTOR'
 end
 local ai=prop(sprite,'m_typeAI')
 if prop(ai,'m_Class')~=3 then return nil,'HOLD_ACTOR_NOT_CLERIC' end
 local active=safe(prop(sprite,'getActiveStats'),sprite)
 if active==nil then return nil,'HOLD_ACTIVE_STATS_UNAVAILABLE' end
 local kit,str=prop(active,'m_nKit'),prop(active,'m_nSTR')
 if kit~=16384 or not int(str,5,25) then
  return nil,'HOLD_KIT_OR_STRENGTH_NOT_MATCHED' end
 local eq=prop(sprite,'m_equipment')
 local items=prop(eq,'m_items')
 if items==nil then return nil,'HOLD_EQUIPMENT_UNAVAILABLE' end
 local copies,source,target,offhand=0,nil,nil,nil
 for i=0,38 do
  if i~=10 then -- implicit fist slot: R37 explicitly does not treat as empty
   local x=slot(items,i)
   if x==nil then return nil,'HOLD_SLOT_UNREADABLE' end
   if not x.empty and x.resref=='STAF01' then copies=copies+1 end
   if i==20 then source=x end
   if i==35 then target=x end
   if i==9 then offhand=x end
  end
 end
 if copies~=1 or source==nil or source.empty or
  source.resref~='STAF01' or source.flags~=1 or
  source.charges[1]~=0 or source.charges[2]~=0 or source.charges[3]~=0 or
  not target.empty or not offhand.empty then
  return nil,'HOLD_SOURCE_TARGET_OR_ITEM_UNIQUENESS_CHANGED'
 end
 return {actorId=actor,classRaw=3,kitRaw=kit,strength=str,sourceResref='STAF01',
  sourceSlot=20,targetSlot=35,sourceUnique=true,targetEmpty=true,
  offhandEmpty=true,partyPortraitSame=true,selectedActorSame=true},nil
end

-- A momentary read-only physical + native trigger probe, never used to ARM.
-- Recheck same actor and raw physical state after evaluating triggers.
function M.probe(ports)
 if type(ports)~='table' or type(ports.getPortraitSprite)~='function' or
  type(ports.getPortraitID)~='function' or type(ports.getSelectedIDs)~='function' or
  type(ports.evalNativeTrigger)~='function' then
  return report('HOLD_REQUIRED_EEEX_PORTS_UNAVAILABLE') end
 local sprite=safe(ports.getPortraitSprite,1)
 local id=safe(ports.getPortraitID,1)
 local ids=safe(ports.getSelectedIDs)
 if sprite==nil then return report('HOLD_NO_PORTRAIT_ACTOR') end
 local first,err=exactPhysical(sprite,ids,id)
 if not first then return report(err) end
 local nativeCount=0
 for _,trigger in ipairs(TRIGGERS) do
  local v=safe(ports.evalNativeTrigger,trigger,sprite)
  if v~=true then return report('HOLD_NATIVE_TRIGGER_FALSE_OR_UNKNOWN',{
      trigger=trigger,nativeTriggerSamples=nativeCount}) end
  nativeCount=nativeCount+1
 end
 local sprite2=safe(ports.getPortraitSprite,1)
 local id2=safe(ports.getPortraitID,1)
 local ids2=safe(ports.getSelectedIDs)
 if sprite2~=sprite or id2~=id then return report('HOLD_ACTOR_CHANGED_IN_PROBE') end
 local second,err2=exactPhysical(sprite2,ids2,id2)
 if not second then return report(err2) end
 for k,v in pairs(first) do if second[k]~=v then
  return report('HOLD_DOUBLE_PHYSICAL_PROBE_CHANGED') end end
 -- Never manufacture proof that EEex has not supplied: item race/kit/effects,
 -- manual/EPS origin, stable idle interval, and trigger's no-side-effects.
 return report('PARTIAL_ENGINE_PHYSICAL_AND_TRIGGER_MATCH_NO_ARM',{
   physicalSnapshotMatched=true,nativeTriggerSamples=nativeCount,
   actorIdentityDoubleRead=true,
   currentSessionItemSHAProven=false,
   engineUsabilityProven=false,
   noInterruptionVerified=false})
end

function M.probeInstalledEEex()
 local g=_G
 local gp=rawget(g,'EEex_Sprite_GetInPortrait')
 local gi=rawget(g,'EEex_Sprite_GetInPortraitID')
 local gs=rawget(g,'EEex_Sprite_GetAllSelectedIDs')
 local ge=rawget(g,'EEex_Trigger_EvalConditionalStringAsAIBase')
 if type(gp)~='function' or type(gi)~='function' or
  type(gs)~='function' or type(ge)~='function' then
  return report('HOLD_INSTALLED_EEEX117_REQUIRED_APIS_MISSING')
 end
 return M.probe({getPortraitSprite=gp,getPortraitID=gi,
  getSelectedIDs=gs,evalNativeTrigger=ge})
end

-- An adapter to M_BGXW3_EXPLICIT_USER_ARM_SOURCE_ONLY.lua is intentionally
-- NOT exported. This module cannot assert itemEngineUsable or all effects;
-- substituting partial observations for these fields would be unsafe.
-- Read the actor's current script *assignments* without any listener or action.
-- EEex v1.1.7 provides EEex_AIBase_GetScriptLevelResRef() for SCRLEV.IDS.
-- A script being assigned is not proof that the engine is evaluating it.
local SCRIPT_LEVELS={0,1,2,4,5,6,7}
local function validResref(s)
 return type(s)=='string' and #s<=8 and (s=='' or not s:find('[^%w_]'))
end
function M.probeScriptAssignments(ports)
 if type(ports)~='table' or type(ports.getPortraitSprite)~='function' or
    type(ports.getPortraitID)~='function' or
    type(ports.getSelectedIDs)~='function' or
    type(ports.getScriptLevelResRef)~='function' then
  return report('HOLD_SCRIPT_ASSIGNMENT_APIS_UNAVAILABLE') end
 local sprite=safe(ports.getPortraitSprite,1)
 local portraitId=safe(ports.getPortraitID,1)
 if sprite==nil or not int(prop(sprite,'m_id'),1,2147483647) or
    prop(sprite,'m_id')~=portraitId then
  return report('HOLD_SCRIPT_ASSIGNMENT_ACTOR_ID') end
 local ai=prop(sprite,'m_typeAI')
 local stats=safe(prop(sprite,'getActiveStats'),sprite)
 if prop(ai,'m_Class')~=3 or prop(stats,'m_nKit')~=16384 then
  return report('HOLD_SCRIPT_ASSIGNMENT_CLASS_OR_KIT') end
 -- Reuse the already-defined, strictly read-only pilot physical gate.
 -- Other clerics in portrait1 MUST NOT be mistaken for this STAF01 pilot.
 -- This is a physical candidate match, not a proof of script name/ownership.
 local initialPhysical,initialReason=exactPhysical(sprite,
   safe(ports.getSelectedIDs),portraitId)
 if not initialPhysical then
  return report('HOLD_SCRIPT_PILOT_PHYSICAL_CONTEXT',{reason=initialReason}) end
 local function once()
  local out={}
  for _,level in ipairs(SCRIPT_LEVELS) do
   local value=safe(ports.getScriptLevelResRef,sprite,level)
   if not validResref(value) then return nil end
   out[level]=value:upper()
  end
  return out
 end
 local first=once()
 if not first then return report('HOLD_SCRIPT_RESREF_UNREADABLE') end
 local sameActor=safe(ports.getPortraitSprite,1)
 local sameId=safe(ports.getPortraitID,1)
 if sameActor~=sprite or sameId~=portraitId then
  return report('HOLD_SCRIPT_ACTOR_CHANGED') end
 local second=once()
 if not second then return report('HOLD_SCRIPT_RESREF_UNREADABLE') end
 local finalPhysical,finalReason=exactPhysical(sameActor,
   safe(ports.getSelectedIDs),sameId)
 if not finalPhysical then
  return report('HOLD_SCRIPT_PILOT_PHYSICAL_CHANGED',{reason=finalReason}) end
 for k,v in pairs(initialPhysical) do
  if finalPhysical[k]~=v then
   return report('HOLD_SCRIPT_PILOT_PHYSICAL_CHANGED') end
 end
 for _,level in ipairs(SCRIPT_LEVELS) do
  if first[level]~=second[level] then return report('HOLD_SCRIPT_RESREF_CHANGED') end
 end
 local found={}
 for _,level in ipairs(SCRIPT_LEVELS) do
  if first[level]=='BDDEFAI' then found[#found+1]=level end
 end
 -- Even when BDDEFAI appears, no conclusion about running AI, evaluation
 -- order, script ownership, action provenance or eligibility to install.
 return report('R39_SCRIPT_RESREFS_OBSERVED_NO_DEPLOY',{
    scriptLevelResrefs=first,portraitActorId=portraitId,
    bddefaiAssigned=(#found>0),bddefaiAssignedLevels=found,
    pilotPhysicalSnapshotDoubleMatched=true,
    nativeScriptNameVerified=false,
    actualBcsExecutionVerified=false,scriptSlotOwnershipVerified=false,
    actionOriginVerified=false,canArm=false})
end
function M.probeInstalledScriptAssignments()
 local g=_G
 local gp=rawget(g,'EEex_Sprite_GetInPortrait')
 local gi=rawget(g,'EEex_Sprite_GetInPortraitID')
 local selected=rawget(g,'EEex_Sprite_GetAllSelectedIDs')
 local gs=rawget(g,'EEex_AIBase_GetScriptLevelResRef')
 if type(gp)~='function' or type(gi)~='function' or
    type(selected)~='function' or type(gs)~='function' then
  return report('HOLD_SCRIPT_ASSIGNMENT_APIS_UNAVAILABLE') end
 return M.probeScriptAssignments({getPortraitSprite=gp,getPortraitID=gi,
    getSelectedIDs=selected,getScriptLevelResRef=gs})
end

function M.getStatus()return report('SOURCE_ONLY_NOT_REGISTERED_OR_CONNECTED') end
return M
