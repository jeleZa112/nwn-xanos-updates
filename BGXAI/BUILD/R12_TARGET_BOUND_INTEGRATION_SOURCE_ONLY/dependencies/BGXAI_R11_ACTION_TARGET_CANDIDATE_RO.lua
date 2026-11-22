-- BGXAI: source-only, non-registering target candidate resolver for an EEex
-- sprite-started-action callback. Observing m_acteeID is NOT proof that an
-- arbitrary action is a hostile attack. No hook, calls to spells, orders or files.
local M={version='BGXAI_R11_ACTION_TARGET_CANDIDATE_RO_V1',installed=false}
local function int(x,lo,hi)
 return type(x)=='number' and x==x and x~=math.huge and x~=-math.huge and
 x%1==0 and x>=lo and x<=hi
end
local function output(reason,extras)
 local r={schema=M.version,status='TARGET_CANDIDATE_HOLD',reason=reason,
  installed=false,executable=false,dispatchAuthorized=false,weaponSwitchAuthorized=false,
  ordersSent=0,currentActionPreserved=true,actionQueueCleared=false,
  hostileTargetProven=false,actionTypeAttackProven=false,
  nativeEvidenceAuthenticated=false,manualOrderProven=false,epsQueueProven=false,
  hitChanceCallAllowed=false,gameFilesModified=false}
 if type(extras)=='table' then for k,v in pairs(extras) do r[k]=v end end
 return r
end
function M.resolve(sourceSprite,action,eeexApi)
 if sourceSprite==nil or action==nil then return output('MISSING_EVENT_OBJECTS') end
 if type(eeexApi)~='table' or type(rawget(eeexApi,'GameObject_Get'))~='function' then
  return output('TARGET_RESOLVER_UNAVAILABLE') end
 local ok,sourceId,actionId,acteeId=pcall(function()
   return sourceSprite.m_id,action.m_actionID,action.m_acteeID.m_Instance
 end)
 if not ok or not int(sourceId,1,2147483647) or
  not int(actionId,0,65535) or not int(acteeId,1,2147483647) or
  sourceId==acteeId then return output('ACTEE_POINTER_NOT_SAFE') end
 local got,target=pcall(eeexApi.GameObject_Get,acteeId)
 if not got or target==nil or rawequal(target,sourceSprite) then
  return output('ACTEE_NOT_RESOLVED') end
 local good,id,isSprite=pcall(function() return target.m_id,target:isSprite(true) end)
 if not good or not int(id,1,2147483647) or id~=acteeId or isSprite~=true then
  return output('ACTEE_ID_OR_TYPE_UNVERIFIED') end
 local originalOk,currentSourceId,currentActionId,currentActeeId=pcall(function()
  return sourceSprite.m_id,action.m_actionID,action.m_acteeID.m_Instance
 end)
 if not originalOk or currentSourceId~=sourceId or currentActionId~=actionId or
   currentActeeId~=acteeId then return output('ACTION_CHANGED_DURING_READ') end
 return output('ACTEE_SPRITE_CANDIDATE_NOT_CONFIRMED_ENEMY',{
   sourceActor=sourceId,candidateTargetActor=id,rawActionId=actionId,
   targetResolvedBySuppliedEEexApi=true,
   -- Keep the target usertype strictly out of serialized output.
   targetObjectCanBeUsedOnlyWithinSameCallback=true})
end
return M
