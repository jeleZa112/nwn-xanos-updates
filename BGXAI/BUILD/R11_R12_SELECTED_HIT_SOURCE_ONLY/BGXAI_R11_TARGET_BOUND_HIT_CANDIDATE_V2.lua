-- BGXAI R11 target binding V2. SOURCE ONLY, PURE ORCHESTRATION.
-- Assemble target resolver + selected hit probe under one started-action snapshot.
-- No game hook registration, target scan, action orders, queue edits or I/O.
-- A successful candidate is NOT an authenticated live read or permission to switch.
local M = { version='BGXAI_R11_TARGET_BOUND_HIT_CANDIDATE_V2', installed=false }
local function int(x,lo,hi)
 return type(x)=='number' and x==x and x~=math.huge and x~=-math.huge and
  x%1==0 and x>=lo and x<=hi
end
local function identifier(x)
 return type(x)=='string' and #x>0 and #x<=128 and not x:find('[^%w_.:%-]')
end
local function hold(reason,extra)
 local o={schema=M.version,status='HOLD',reason=reason,installed=false,
  executable=false,dispatchAuthorized=false,weaponSwitchAuthorized=false,
  gameFilesModified=false,ordersSent=0,actionQueueCleared=false,
  currentActionPreserved=true,nativeEvidenceAuthenticated=false,
  liveReadVerified=false,hostileTargetProven=false,actionAttackProven=false,
  manualOrderProven=false,epsQueueProven=false,
  alternateSlotAPRVerified=false,rankingAuthorized=false}
 if extra then
  -- Only diagnostic primitive fields; no possibility to override control flags.
  if extra.sourceActor then o.sourceActor=extra.sourceActor end
  if extra.targetActor then o.targetActor=extra.targetActor end
  if extra.selectedSlot then o.selectedSlot=extra.selectedSlot end
 end
 return o
end
local function inspect_event(sprite,action)
 local ok,sid,aid,tid=pcall(function()
  return sprite.m_id,action.m_actionID,action.m_acteeID.m_Instance
 end)
 if not ok or not int(sid,1,2147483647) or
  not int(aid,0,65535) or not int(tid,1,2147483647) or sid==tid then return nil end
 return sid,aid,tid
end
local function inspect_selected(sprite)
 local ok,slot,ability,item=pcall(function()
  local eq=sprite.m_equipment
  local s,a=eq.m_selectedWeapon,eq.m_selectedWeaponAbility
  return s,a,eq.m_items:get(s)
 end)
 if not ok or (not int(slot,35,38) and not int(slot,11,14)) or
  not int(ability,0,255) or item==nil then return nil end
 return slot,ability,item
end
local function same_state(sprite,action,eeex,sourceId,actionId,targetId,target,slot,ability,item)
 local sid,aid,tid=inspect_event(sprite,action)
 if sid~=sourceId or aid~=actionId or tid~=targetId then return false end
 local s,a,i=inspect_selected(sprite)
 if s~=slot or a~=ability or not rawequal(i,item) then return false end
 local good,got=pcall(eeex.GameObject_Get,targetId)
 if not good or not rawequal(got,target) then return false end
 local ok,id,isSprite=pcall(function()return got.m_id,got:isSprite(true) end)
 return ok and id==targetId and isSprite==true
end
function M.inspect(sprite,action,eeex,context,resolver,probe)
 if sprite==nil or action==nil then return hold('MISSING_STARTED_ACTION') end
 if type(context)~='table' or not identifier(context.sessionId) or
  not identifier(context.snapshotId) or not int(context.sequence,1,1000000) or
  context.observeSelectedOnly~=true or context.switchAttempted~=false or
  context.manualEPSBoundaryProven~=false or context.readOnlyProbeConsent~=true then
  return hold('CONTEXT_UNTRUSTED') end
 if type(eeex)~='table' or type(rawget(eeex,'GameObject_Get'))~='function' or
  type(rawget(eeex,'GetWeaponHitChance'))~='function' or
  type(rawget(eeex,'IsImmuneToWeapon'))~='function' then
  return hold('EEEX_API_MISSING') end
 if type(resolver)~='table' or type(rawget(resolver,'resolve'))~='function' or
  type(probe)~='table' or type(rawget(probe,'inspect'))~='function' then
  return hold('REQUIRED_READONLY_BRIDGE_MISSING') end
 local sid,aid,tid=inspect_event(sprite,action)
 if not sid then return hold('STARTED_ACTION_IDS_UNTRUSTED') end
 if context.actor~=sid or context.targetActor~=tid or context.actionRaw~=aid then
  return hold('CONTEXT_ACTOR_TARGET_ACTION_MISMATCH') end
 -- Caller-provided action IDs do not prove hostile attack. Conservative
 -- allowlist for reading a candidate only, never for ranking or dispatch.
 if aid~=3 and aid~=30 then return hold('NON_ATTACK_CANDIDATE_ACTION') end
 local slot,ability,item=inspect_selected(sprite)
 if not slot then return hold('SELECTED_EQUIPMENT_UNAVAILABLE') end
 -- We need independently verified launcher mapping before ranged selected
 -- hit chance can be attributed to a weapon. An ammo-only slot is HOLD.
 if slot>=11 and slot<=14 then return hold('AMMO_LAUNCHER_NOT_PROVEN') end
 local ok,candidate=pcall(resolver.resolve,sprite,action,eeex)
 if not ok or type(candidate)~='table' or
  candidate.reason~='ACTEE_SPRITE_CANDIDATE_NOT_CONFIRMED_ENEMY' or
  candidate.sourceActor~=sid or candidate.candidateTargetActor~=tid or
  candidate.hitChanceCallAllowed~=false or candidate.hostileTargetProven~=false or
  candidate.dispatchAuthorized~=false or candidate.weaponSwitchAuthorized~=false then
  return hold('ACTEE_RESOLUTION_NOT_TRUSTED') end
 local got,target=pcall(eeex.GameObject_Get,tid)
 if not got or target==nil then return hold('ACTEE_UNAVAILABLE') end
 local ok2,id,isSprite=pcall(function()return target.m_id,target:isSprite(true) end)
 if not ok2 or id~=tid or isSprite~=true then return hold('ACTEE_ID_OR_TYPE_CHANGED') end
 if not same_state(sprite,action,eeex,sid,aid,tid,target,slot,ability,item) then
  return hold('STATE_CHANGED_BEFORE_READ') end
 local params={sessionId=context.sessionId,snapshotId=context.snapshotId,
  actor=sid,targetActor=tid,sequence=context.sequence,
  usesAlreadySelectedWeapon=true,readOnlyProbeConsent=true,
  manualEPSBoundaryProven=false,switchAttempted=false}
 local performed,c=pcall(probe.inspect,sprite,target,eeex,params)
 if not performed or type(c)~='table' or
  c.schema~='BGXAI_WEAPON_R11_EEEX_SELECTED_HIT_PROBE_V1' or
  c.status~='SELECTED_HIT_CHANCE_CANDIDATE_ONLY' or
  c.executable~=false or c.dispatchAuthorized~=false or
  c.weaponSwitchAuthorized~=false or c.nativeEvidenceAuthenticated~=false or
  c.targetActorBindingProven~=false or c.liveReadVerified~=false or
  c.selectedSlot~=slot or c.selectedAbility~=ability or
  c.actor~=sid or c.targetActor~=tid or c.sequence~=context.sequence or
  c.sessionId~=context.sessionId or c.snapshotId~=context.snapshotId or
  not int(c.hitChancePercent,0,100) or type(c.isImmuneToSelectedWeapon)~='boolean' then
  return hold('SELECTED_HIT_PROBE_UNTRUSTED_OR_UNAVAILABLE') end
 if not same_state(sprite,action,eeex,sid,aid,tid,target,slot,ability,item) then
  return hold('STATE_CHANGED_AFTER_READ') end
 return {
  schema=M.version,status='TARGET_BOUND_SELECTED_HIT_CANDIDATE_NOT_NATIVE_PROOF',
  sourceActor=sid,targetActor=tid,rawActionId=aid,selectedSlot=slot,
  selectedAbility=ability,sessionId=context.sessionId,snapshotId=context.snapshotId,
  sequence=context.sequence,hitChancePercentCandidate=c.hitChancePercent,
  isImmuneCandidate=c.isImmuneToSelectedWeapon,
  candidateDerivedFromCallerSuppliedApi=true,
  hostileTargetProven=false,actionAttackProven=false,
  nativeEvidenceAuthenticated=false,liveReadVerified=false,
  alternativeWeaponProven=false,alternateSlotAPRVerified=false,
  installed=false,executable=false,dispatchAuthorized=false,
  weaponSwitchAuthorized=false,rankingAuthorized=false,ordersSent=0,
  manualOrderProven=false,epsQueueProven=false,
  currentActionPreserved=true,actionQueueCleared=false,gameFilesModified=false
 }
end
return M
