-- BGXAI weapon choice continuity: READ-ONLY scheduling, NOT INSTALLED.
-- Buff/stat changes invalidate only the ranking token, NEVER the game action.
-- No Stop, ClearActions, Attack, SelectWeaponAbility, LOCALS, EEex orders, hooks,
-- timers, files, runtime promises or mutations to the supplied scene/state.
-- Calculation is synchronous pure Lua when called; it is NOT a separate thread.
-- The caller must provide an audited, non-dispatching rank function (V3.preview
-- behind the current-stats/V4 bridge). It must never use foreground V3.choose
-- with fabricated 'manualOrderActive=false' to force scoring during a cast.
local M={version='BGXAI_WEAPON_NONINTERRUPT_PLAN_V1',installed=false}
-- At identical evidence, keep pending advice for a few ticks instead of
-- re-scoring every frame. Never skip evidence validation or issue actions.
local PENDING_REFRESH_TICKS=5
local function id(x)
 return type(x)=='string' and #x>0 and #x<=80 and not x:find('[^%w_%+%.%-]')
end
local function tick(x) return type(x)=='number' and x==x and x>=0 and x<=1e12 and x%1==0 end
local function output(status,next,extra)
 local r={status=status,next=next,executable=false,dispatchAuthorized=false,
  ordersSent=0,localsWritten=0,actionQueueCleared=false,
  currentActionPreserved=true,installed=false}
 if type(extra)=='table' then for k,v in pairs(extra) do r[k]=v end end
 return r
end
local function key(scene)
 if type(scene)~='table' or type(scene.frame)~='table' or
    type(scene.actor)~='table' or type(scene.actor.activeStatsEvidence)~='table' or
    type(scene.quickslotIds)~='table' then return nil end
 local f,a,d=scene.frame,scene.actor,scene.actor.activeStatsEvidence
 if not tick(f.tick) or not id(f.snapshotId) or not id(f.area) or
    not id(f.actorId) or not id(f.enemyId) or not id(f.equipmentFingerprint) or
    not id(f.protectionFingerprint) or not id(f.combatFingerprint) or
    not id(d.buffFingerprint) or not id(d.activeFingerprint) or
    a.actorId~=f.actorId or a.selectedWeaponId~=f.selectedWeaponId or
    not id(a.selectedWeaponId) or d.snapshotId~=f.snapshotId or
    d.actorId~=f.actorId or d.tick~=f.tick or #scene.quickslotIds~=4 then return nil end
 local parts={f.area,f.actorId,f.enemyId,f.equipmentFingerprint,
  f.protectionFingerprint,f.combatFingerprint,
  id(f.effectStatusFingerprint) and f.effectStatusFingerprint or 'NO_EFFECT_FINGERPRINT',
  d.activeFingerprint,d.buffFingerprint,a.selectedWeaponId}
 for i=1,4 do
  local v=scene.quickslotIds[i]
  if v~=false and not id(v) then return nil end
  parts[#parts+1]=v==false and '-' or v
 end
 return table.concat(parts,'|')
end
M.signature=key
local function valid_proposal(scene,score)
 if score.status~='PASSIVE_RANKING_SUGGESTS_SLOT' or
    not id(score.fromWeaponId) or not id(score.toWeaponId) or
    score.fromWeaponId==score.toWeaponId or
    score.fromWeaponId~=scene.actor.selectedWeaponId or
    not tick(score.slotIndex) or score.slotIndex>3 or
    scene.quickslotIds[score.slotIndex+1]~=score.toWeaponId or
    score.targetId~=scene.frame.enemyId then return false end
 return true
end
local function model_safe_window(scene)
 -- These are hypothetical scene evidence flags, not permission to issue orders.
 -- Observing m_actionID=0 or m_curScriptNum NEVER proves these flags.
 local a=scene.actor
 local e=scene.activity
 if type(e)~='table' or e.snapshotId~=scene.frame.snapshotId or
    e.actorId~=scene.frame.actorId or e.tick~=scene.frame.tick or
    e.source~='INDEPENDENTLY_AUDITED_EEEX_EPS_ACTIVITY' then return false end
 return e.provenNoManualOrder==true and e.provenEpsFree==true and
    e.provenActionBoundary==true and e.provenAttackRecoveryComplete==true and
    e.provenNoCasting==true and e.provenNoHealing==true and
    e.provenNoQueuedAction==true and
    a.manualOrderActive==false and a.epsBusy==false and
    a.healingReserved==false and a.currentlyCasting==false and
    a.originVerified=='AI'
end
-- Raw x64 engine queue count is enough to DEFER work when >0. It never
-- proves an empty EPS/manual queue or authorizes a switch, even if forged.
local function queued_actions_known_busy(scene)
 if type(scene)~='table' or type(scene.actor)~='table' then return nil end
 local q=scene.observedR27Queue
 local actor=scene.actor
 if type(q)~='table' or q.schema~='BGXAI_R27_SINGLE_CALLBACK_SELECTED_RO_V1' or
    q.status~='CURRENT_SELECTED_SAME_CALLBACK_SOURCE_CANDIDATE' or
    q.queueSnapshotStable~=true or q.readOnly~=true or
    q.sameLuaListenerInvocation~=true or q.ordersSent~=0 or
    q.dispatchAuthorized~=false or q.actionOriginVerified~=false or
    q.manualEpsQueueVerified~=false or
    q.actor~=actor.engineActorRaw or q.actionRaw~=actor.currentActionRaw or
    type(q.queuedActionsRaw)~='number' or q.queuedActionsRaw%1~=0 or
    q.queuedActionsRaw<1 or q.queuedActionsRaw>512 then return nil end
 return q.queuedActionsRaw
end
function M.step(scene,previous,scoreReadOnly)
 local busyCount=queued_actions_known_busy(scene)
 if busyCount then
  -- This is a one-way NOOP safety signal. Drop pending advice and never call
  -- a scorer; no requirement to prove the origin of the queued actions.
  return output('PRESERVE_KNOWN_NONEMPTY_ACTION_QUEUE',nil,
   {queuedActionsRaw=busyCount,scorerCalls=0})
 end
 local k=key(scene)
 if k==nil then return output('HOLD_SCENE_AND_BUFF_EVIDENCE_INCOMPLETE',nil) end
 if type(scoreReadOnly)~='function' then
  return output('HOLD_READONLY_SCORER_NOT_CONNECTED',nil) end
 local f=scene.frame
 local stillCurrent=type(previous)=='table' and previous.key==k and
   tick(previous.tick) and f.tick>previous.tick and f.tick-previous.tick<=30
 local scorerToken=stillCurrent and previous.scorerToken or nil
 local pending=stillCurrent and previous.pending or nil
 local lastRanked=stillCurrent and previous.lastRankedTick or nil
 local ce=scene.cacheEvidence
 local cacheProven=type(ce)=='table' and
  ce.source=='INDEPENDENTLY_AUDITED_FULL_WEAPON_CACHE_SNAPSHOT' and
  ce.snapshotId==f.snapshotId and ce.actorId==f.actorId and
  ce.tick==f.tick and ce.allRelevantStateFingerprintComplete==true and
  ce.ammoAndItemEffectsCovered==true and ce.activeBuffsCovered==true and
  ce.targetProtectionsCovered==true
 if cacheProven and pending and tick(pending.createdTick) and tick(lastRanked) and
     f.tick-lastRanked<PENDING_REFRESH_TICKS and
     f.tick-pending.createdTick<=45 and
     pending.fromWeaponId==scene.actor.selectedWeaponId and
     pending.targetId==f.enemyId and
     scene.quickslotIds[pending.slotIndex+1]==pending.toWeaponId then
  -- No scorer call at all while a verified, unchanged plan is still fresh.
  -- Continuity / engine safety is STILL checked on every observation.
  local next={key=k,tick=f.tick,scorerToken=scorerToken,
   lastRankedTick=lastRanked,pending=pending}
  if model_safe_window(scene) then
   return output('ADVISORY_SAFE_BOUNDARY_OBSERVED_NO_DISPATCH',next,{
    proposedWeaponId=pending.toWeaponId,proposedSlotIndex=pending.slotIndex,
    scorerCalls=0})
  end
  return output('CONTINUE_CURRENT_ACTION_SWITCH_PENDING',next,{
   proposedWeaponId=pending.toWeaponId,proposedSlotIndex=pending.slotIndex,
   scorerCalls=0})
 end
 local good,score=pcall(scoreReadOnly,scene,scorerToken)
 if not good or type(score)~='table' or score.passivePreview~=true or
    score.executable~=false or score.dispatchAuthorized~=false then
  return output('HOLD_SCORER_RESULT_UNTRUSTED',nil) end
 local next={key=k,tick=f.tick,scorerToken=score.next,pending=nil,lastRankedTick=f.tick}
 if score.status=='PASSIVE_RANKING_SUGGESTS_SLOT' then
  if not valid_proposal(scene,score) then
   return output('HOLD_RANKING_SLOT_OR_TARGET_MISMATCH',next) end
  pending={fromWeaponId=score.fromWeaponId,toWeaponId=score.toWeaponId,
    slotIndex=score.slotIndex,targetId=score.targetId,
    createdTick=f.tick}
 elseif score.status=='HOLD_ADVISORY_SWITCH_COOLDOWN' and pending and
     tick(pending.createdTick) and f.tick-pending.createdTick<=45 and
     pending.fromWeaponId==scene.actor.selectedWeaponId and
     pending.targetId==f.enemyId and
     scene.quickslotIds[pending.slotIndex+1]==pending.toWeaponId then
  -- Keep pending switch while current attack completes; no forced idle.
 elseif score.status=='KEEP_CURRENT' or score.status=='HOLD_NO_EFFECTIVE_ATTACK' then
  return output('CONTINUE_CURRENT_ACTION_KEEP_WEAPON',next,{scoreStatus=score.status})
 else
  -- Includes fresh buff/state changes and incomplete evidence: no stale plan.
  return output('CONTINUE_CURRENT_ACTION_RECALCULATING',next,{scoreStatus=score.status})
 end
 next.pending=pending
 if model_safe_window(scene) then
  -- Strictly advisory, not a license for BCS/LOCALS; real adapter pending.
  return output('ADVISORY_SAFE_BOUNDARY_OBSERVED_NO_DISPATCH',next,{
   proposedWeaponId=pending.toWeaponId,proposedSlotIndex=pending.slotIndex})
 end
 return output('CONTINUE_CURRENT_ACTION_SWITCH_PENDING',next,{
  proposedWeaponId=pending.toWeaponId,proposedSlotIndex=pending.slotIndex,
  scoreStatus=score.status})
end
return M
