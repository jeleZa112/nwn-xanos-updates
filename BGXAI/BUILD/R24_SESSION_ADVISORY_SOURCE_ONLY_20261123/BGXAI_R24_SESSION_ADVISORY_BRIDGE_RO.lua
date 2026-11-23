-- BGXAI R24: source-only session-isolated glue for EXISTING weapon advice.
-- NEVER install as a listener; no EEex, BCS/LOCALS, file I/O, or game actions.
-- Only the OFFLINE_SYNTHETIC test path may call the existing scorer/scheduler.
-- Every real/unverified input must HOLD and keep the current weapon.
local M={version='BGXAI_R24_SESSION_ADVISORY_RO_V1',installed=false}
local function valid_id(x)
 return type(x)=='string' and #x>0 and #x<=80 and not x:find('[^%w_%+%.%-]')
end
local function hold(reason, reset)
 return {schema=M.version,status='KEEP_CURRENT_WEAPON_NO_DISPATCH',
  reason=reason,previousSessionDiscarded=reset==true,
  readOnly=true,sourceOnly=true,installed=false,executable=false,
  dispatchAuthorized=false,weaponSwitchAuthorized=false,
  ordersSent=0,localsWritten=0,actionQueueCleared=false,
  currentActionPreserved=true,proposedWeaponId=nil,next=nil}
end
function M.step(input, prior, deps)
 if type(input)~='table' then return hold('NO_INPUT') end
 -- Explicitly disallow real data from being interpreted as a complete scene.
 -- A caller's optimistic verified/complete flags cannot override this rule.
 if input.mode~='OFFLINE_SYNTHETIC_FIXTURE' then
  return hold('REAL_SOURCE_ALT_APR_EFFECTS_EPS_AND_LAUNCHER_UNVERIFIED')
 end
 local s=input.scene
 if type(s)~='table' or type(s.frame)~='table' or
    type(s.actor)~='table' or not valid_id(input.sessionToken) or
    not valid_id(s.frame.snapshotId) or not valid_id(s.frame.actorId) or
    s.actor.actorId~=s.frame.actorId or
    (input.pipeline~='CURRENT_ACTIVE_STATS' and input.pipeline~='APR_PROVENANCE') then
  return hold('OFFLINE_SCENE_OR_SESSION_MISSING') end
 if type(deps)~='table' or type(deps.noninterrupt)~='table' or
    type(deps.noninterrupt.step)~='function' or type(deps.effects)~='table' or
    type(deps.effects.choose)~='function' or type(deps.priority)~='table' or
    type(deps.priority.preview)~='function' then
  return hold('EXISTING_PIPELINE_DEPENDENCIES_MISSING') end
 local bridge=input.pipeline=='CURRENT_ACTIVE_STATS' and deps.currentStats or deps.apr
 if type(bridge)~='table' or type(bridge.choose)~='function' then
  return hold('EXISTING_STATS_OR_APR_BRIDGE_MISSING') end
 local reset=type(prior)=='table' and (
   prior.sessionToken~=input.sessionToken or
   prior.actorId~=s.frame.actorId or
   prior.pipeline~=input.pipeline)
 local previous=nil
 if type(prior)=='table' and reset~=true then previous=prior.plan end
 local readonly=function(scene, previousToken)
  return bridge.choose(scene,previousToken,deps.effects.choose,deps.priority.preview)
 end
 local ok,res=pcall(deps.noninterrupt.step,s,previous,readonly)
 if not ok or type(res)~='table' then return hold('SCHEDULER_UNEXPECTED_FAILURE',reset) end
 if res.executable~=false or res.dispatchAuthorized~=false or
    res.ordersSent~=0 or res.localsWritten~=0 or
    res.actionQueueCleared~=false or res.currentActionPreserved~=true or
    res.installed~=false then
  return hold('SCHEDULER_READ_ONLY_INVARIANT_VIOLATED',reset) end
 local proposed=nil
 if res.status=='CONTINUE_CURRENT_ACTION_SWITCH_PENDING' or
    res.status=='ADVISORY_SAFE_BOUNDARY_OBSERVED_NO_DISPATCH' then
  proposed=res.proposedWeaponId
 end
 return {schema=M.version,status='OFFLINE_SYNTHETIC_ADVISORY_NO_DISPATCH',
   advisoryStatus=res.status,scoreStatus=res.scoreStatus,
   proposedWeaponId=proposed,proposedSlotIndex=proposed and res.proposedSlotIndex or nil,
   previousSessionDiscarded=reset==true,
   readOnly=true,sourceOnly=true,installed=false,executable=false,
   dispatchAuthorized=false,weaponSwitchAuthorized=false,
   ordersSent=0,localsWritten=0,actionQueueCleared=false,
   currentActionPreserved=true,
   next={sessionToken=input.sessionToken,actorId=s.frame.actorId,
     pipeline=input.pipeline,plan=res.next}}
end
return M
