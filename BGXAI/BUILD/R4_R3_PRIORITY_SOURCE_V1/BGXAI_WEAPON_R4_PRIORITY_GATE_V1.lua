-- BGXAI R4→V5 APR provenance→CURRENT→V4 effects→V3 preview→NONINTERRUPT.
-- Offline SOURCE ONLY. No require(), engine functions, IO, globals, or game edits.
-- The JSON evidence matrix is historical raw observations; it cannot establish
-- present target protections, effects, projected per-slot APR, EPS or manual queue.
-- Even a COMPLETE independently audited scene may only produce passive advice.
local M={version='BGXAI_WEAPON_R4_PRIORITY_GATE_V1',installed=false}
local function hold(reason)
 return {status='HOLD_EVIDENCE_BEFORE_PRIORITY',reason=reason,
  executable=false,dispatchAuthorized=false,weaponSwitchAuthorized=false,
  priorityRecommendation=nil,ordersSent=0,localsWritten=0,
  actionQueueCleared=false,currentActionPreserved=true,installed=false}
end
local function deps_ok(d)
 return type(d)=='table' and type(d.current)=='table' and
  type(d.apr)=='table' and type(d.effects)=='table' and
  type(d.priority)=='table' and type(d.noninterrupt)=='table' and
  type(d.current.audit)=='function' and
  type(d.current.choose)=='function' and
  type(d.apr.audit)=='function' and
  type(d.apr.choose)=='function' and
  type(d.effects.choose)=='function' and
  type(d.priority.preview)=='function' and
  type(d.noninterrupt.step)=='function'
end
local function matrix_ok(evidence,actorId)
 if type(evidence)~='table' or
  evidence.schema~='BGXAI_WEAPON_R4_R3_LIVE_EVIDENCE_V1' or
  evidence.status~='SELECTED_HISTORICAL_APR_AND_ITEM_IDENTITY_OBSERVED_PRIORITY_HOLD' or
  evidence.executable~=false or evidence.dispatchAuthorized~=false or
  evidence.weaponSwitchAuthorized~=false or
  type(evidence.rankingGate)~='table' or
  evidence.rankingGate.status~='HOLD_COMPLETE_EFFECTIVE_SCENE_REQUIRED' or
  evidence.rankingGate.cannotInferFromHistoricalSelectedAPRs~=true or
  type(evidence.actors)~='table' then return false end
 for _,v in ipairs(evidence.actors) do
  if type(v)=='table' and tostring(v.actorId)==actorId and
    type(v.events)=='number' and v.events>=1 then return true end
 end
 return false
end
local function raw_preview(scene,previous,modules)
 -- Real per-slot effective evidence must be separately audited *now*. Cached
 -- historical selected APR isn't accepted by either independent audit.
 local cur,curitem=modules.current.audit(scene)
 if cur then return hold('CURRENT_STATS:'..tostring(cur)..':'..tostring(curitem or '-')) end
 local apr,apritem=modules.apr.audit(scene)
 if apr then return hold('APR_PROVENANCE:'..tostring(apr)..':'..tostring(apritem or '-')) end
 -- Read-only priority is the existing V3.preview, not V3.choose. V4 and V5
 -- add item/ammo/on-hit/strength and APR provenance once only.
 local ok,result=pcall(function()
  return modules.current.choose(scene,previous,function(s,p,v3)
    return modules.apr.choose(s,p,function(s2,p2,v3fn)
      return modules.effects.choose(s2,p2,v3fn)
    end,v3)
  end,modules.priority.preview)
 end)
 if not ok or type(result)~='table' then return hold('SCORER_ERROR') end
 result.passivePreview=true
 result.executable=false
 result.dispatchAuthorized=false
 result.weaponSwitchAuthorized=false
 result.currentActionPreserved=true
 return result
end
function M.preview(scene,previous,rawHistory,modules)
 if not deps_ok(modules) then return hold('AUDITED_SOURCE_ONLY_MODULES_MISSING') end
 if type(scene)~='table' or type(scene.frame)~='table' or
     type(scene.actor)~='table' or type(scene.frame.actorId)~='string' then
  return hold('CURRENT_EFFECTIVE_SCENE_NOT_PROVIDED') end
 if not matrix_ok(rawHistory,scene.frame.actorId) then
  return hold('HISTORICAL_R4_R3_ACTOR_OR_SOURCE_MISMATCH') end
 return raw_preview(scene,previous,modules)
end
function M.step(scene,previous,rawHistory,modules)
 -- Check proofs WITHOUT running a full scorer first. A complete scorer may be
 -- expensive; only the noninterrupt scheduler decides if re-ranking is due.
 if not deps_ok(modules) then return hold('AUDITED_SOURCE_ONLY_MODULES_MISSING') end
 if type(scene)~='table' or type(scene.frame)~='table' or
    type(scene.actor)~='table' or type(scene.frame.actorId)~='string' then
  return hold('CURRENT_EFFECTIVE_SCENE_NOT_PROVIDED') end
 if not matrix_ok(rawHistory,scene.frame.actorId) then
  return hold('HISTORICAL_R4_R3_ACTOR_OR_SOURCE_MISMATCH') end
 local cur,curitem=modules.current.audit(scene)
 if cur then return hold('CURRENT_STATS:'..tostring(cur)..':'..tostring(curitem or '-')) end
 local apr,apritem=modules.apr.audit(scene)
 if apr then return hold('APR_PROVENANCE:'..tostring(apr)..':'..tostring(apritem or '-')) end
 -- Re-evaluate with current tick/token via the established noninterrupt path.
 local ok,output=pcall(function()
  return modules.noninterrupt.step(scene,previous,function(sc,token)
   return M.preview(sc,token,rawHistory,modules)
  end)
 end)
 if not ok or type(output)~='table' then return hold('NONINTERRUPT_ERROR') end
 output.executable=false
 output.dispatchAuthorized=false
 output.weaponSwitchAuthorized=false
 output.ordersSent=0
 output.localsWritten=0
 output.actionQueueCleared=false
 output.currentActionPreserved=true
 output.installed=false
 return output
end
return M
