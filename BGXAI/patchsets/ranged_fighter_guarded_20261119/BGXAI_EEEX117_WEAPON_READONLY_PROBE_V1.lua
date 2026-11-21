-- BGXAI Weapon EEex 1.1.7 passive evidence probe V1. SOURCE ONLY, NOT INSTALLED.
-- Only reads CGameSprite already supported by EEex_Sprite_GetInPortrait() and
-- m_equipment.m_selectedWeapon (both in public EEex 1.1.7 source).
-- m_items availability/index semantics, status of manual commands and EPS queue
-- MUST be verified live before any upgrade to COMPLETE_EFFECTIVE_SNAPSHOT.
-- NEVER writes LOCALS, registers hooks, uses memory writes, or issues an order.
local M={version='BGXAI_W_EEEX117_RO_V1',installed=false}
local function protected_get(obj,field)
 if obj==nil then return nil end
 local ok,val=pcall(function() return obj[field] end)
 if not ok then return nil end
 return val
end
local function safe_num(n)
 return type(n)=='number' and n==n and n~=-math.huge and n~=math.huge
end
local function bad(reason,partial)
 return {status=reason,partial=partial or {},capturedFromGame=false,
  completeEquipmentObserved=false,completeQuiverObserved=false,
  completeTargetObserved=false,finalCombatStatsVerified=false,
  originVerified=false,epsQueueEmptyVerified=false,manualQueueEmptyVerified=false,
  bcsRequestAllowed=false,engineDispatchAllowed=false,ordersSent=0,localsWritten=0,
  canRankWeapon=false}
end
function M.observe_portrait(index,read_portrait)
 if not safe_num(index) or index%1~=0 or index<0 or index>5 then
  return bad('HOLD_INVALID_PORTRAIT_INDEX') end
 -- Default uses the verified EEex 1.1.7 getter. Optional injected getter is
 -- intended exclusively for offline tests, not as an evidence attestation.
 local getter=read_portrait
 if getter==nil then getter=EEex_Sprite_GetInPortrait end
 if type(getter)~='function' then return bad('HOLD_EEEX117_API_MISSING') end
 local ok,sprite=pcall(getter,index)
 if not ok or sprite==nil then return bad('HOLD_NO_PORTRAIT_SPRITE') end
 local id=protected_get(sprite,'m_id')
 local equipment=protected_get(sprite,'m_equipment')
 local selected=protected_get(equipment,'m_selectedWeapon')
 local position=protected_get(sprite,'m_pos')
 local px,py=protected_get(position,'x'),protected_get(position,'y')
 local action=protected_get(sprite,'m_curAction')
 local actionId=protected_get(action,'m_actionID')
 local scriptNumber=protected_get(sprite,'m_curScriptNum')
 local observed={portraitIndex=index,actorIdObserved=safe_num(id) and id or nil,
  rawSelectedWeaponSlot=safe_num(selected) and selected or nil,
  position= safe_num(px) and safe_num(py) and {x=px,y=py} or nil,
  rawActionId=safe_num(actionId) and actionId or nil,
  rawCurrentScriptNumber=safe_num(scriptNumber) and scriptNumber or nil,
  quickslotsRead=false,quiverRead=false,selectedWeaponMappingVerified=false,
  observationsOnly=true}
 if not safe_num(id) or not safe_num(selected) then
  return bad('HOLD_EQUIPMENT_FIELDS_UNVERIFIED',observed) end
 -- Information is useful for later native EEex runtime capability validation,
 -- NOT sufficient for a valid ranking or a command. Even action 0 is not idle proof.
 local result=bad('OBSERVED_ID_AND_SELECTED_WEAPON_RAW_ONLY',observed)
 result.capturedFromGame=(read_portrait==nil)
 return result
end
return M
