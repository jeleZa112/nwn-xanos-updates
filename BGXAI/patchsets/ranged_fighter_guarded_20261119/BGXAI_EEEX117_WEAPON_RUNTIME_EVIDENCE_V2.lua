-- BGXAI EEex 1.1.7 live-capability observer V2. PASSIVE / SOURCE ONLY.
-- Uses fields/getter present in EEex tag v1.1.7:
-- EEex_Sprite_GetInPortrait, m_equipment.m_selectedWeapon,
-- sprite:getActiveStats(), m_bAllowEffectListCall, m_curAction.m_actionID.
-- NEVER enumerates unknown CItem arrays or calls GetAtOffset on guessed IDs.
-- This is an ON-DEMAND snapshot, not a hook or automatic background service.
-- It cannot prove any combat stats, buff completeness, manual/EPS queue state,
-- or whether a new slot can be safely equipped. No calls write game state.
local M={version='BGXAI_EEEX117_WEAPON_RUNTIME_EVIDENCE_V2',installed=false}
local function safe(obj,key)
 if obj==nil then return nil end
 local ok,val=pcall(function() return obj[key] end)
 return ok and val or nil
end
local function integer(x,lo,hi)
 return type(x)=='number' and x==x and x%1==0 and x>=lo and x<=hi
end
local function num(x)
 return type(x)=='number' and x==x and x~=math.huge and x~=-math.huge
end
local function state(status,raw)
 return {status=status,raw=raw or {},readOnly=true,executable=false,
  dispatchAuthorized=false,ordersSent=0,localsWritten=0,
  actionQueueCleared=false,currentActionPreserved=true,
  capturedFromRealGame=false,completeEquipmentObserved=false,
  completeQuiverObserved=false,completeBuffEffectsObserved=false,
  effectivePerWeaponAPRVerified=false,manualOrderOriginVerified=false,
  epsQueueVerifiedEmpty=false,canSwitchWeapon=false}
end
function M.observe_portrait(index,getter)
 if not integer(index,0,5) then return state('HOLD_INVALID_PORTRAIT') end
 local liveGetter=(getter==nil)
 local retrieve=getter
 if liveGetter then retrieve=EEex_Sprite_GetInPortrait end
 if type(retrieve)~='function' then return state('HOLD_EEEX_PORTRAIT_API_UNAVAILABLE') end
 local ok,sprite=pcall(retrieve,index)
 if not ok or sprite==nil then return state('HOLD_NO_SPRITE') end
 local id=safe(sprite,'m_id')
 local selection=safe(safe(sprite,'m_equipment'),'m_selectedWeapon')
 local flag=safe(sprite,'m_bAllowEffectListCall')
 local actionId=safe(safe(sprite,'m_curAction'),'m_actionID')
 local script=safe(sprite,'m_curScriptNum')
 local raw={portraitIndex=index,
  actorId=integer(id,0,65535) and id or nil,
  selectedWeaponRaw=integer(selection,0,65535) and selection or nil,
  actionIdRaw=integer(actionId,0,65535) and actionId or nil,
  scriptNumberRaw=integer(script,0,65535) and script or nil,
  effectListAccessFlagRaw=num(flag) and flag or nil,
  statsObjectSeen=false,
  -- These are only branch labels from the 1.1.7 getActiveStats implementation.
  -- They are not evidence of a finished cast, usable weapon, buff completion.
  activeStatsBranch=(flag==0 and 'TEMP_STATS_PATH' or
                   (num(flag) and 'DERIVED_STATS_PATH' or 'UNKNOWN')),
  observedOnly=true}
 local fn=safe(sprite,'getActiveStats')
 local activeOk,activeStats=false,nil
 if type(fn)=='function' then
  activeOk,activeStats=pcall(fn,sprite)
 elseif type(EEex_Sprite_GetActiveStats)=='function' then
  activeOk,activeStats=pcall(EEex_Sprite_GetActiveStats,sprite)
 end
 raw.statsObjectSeen=activeOk and activeStats~=nil
 if not integer(id,0,65535) or not integer(selection,0,65535) then
  return state('HOLD_SELECTED_WEAPON_OR_ID_UNAVAILABLE',raw) end
 if not num(flag) or not raw.statsObjectSeen then
  return state('HOLD_ACTIVE_STATS_CONTEXT_UNAVAILABLE',raw) end
 local r=state('OBSERVED_RAW_SELECTED_AND_ACTIVE_STATS_CONTEXT_ONLY',raw)
 r.capturedFromRealGame=liveGetter
 return r
end
function M.compare(before,after)
 if type(before)~='table' or type(after)~='table' or
    type(before.raw)~='table' or type(after.raw)~='table' then
  return state('HOLD_MISSING_OBSERVATIONS') end
 local a,b=before.raw,after.raw
 if not integer(a.actorId,0,65535) or a.actorId~=b.actorId or
    not integer(a.selectedWeaponRaw,0,65535) or
    not integer(b.selectedWeaponRaw,0,65535) or
    not num(a.effectListAccessFlagRaw) or
    not num(b.effectListAccessFlagRaw) then
  return state('HOLD_INCOMPARABLE_RAW_OBSERVATIONS') end
 local selectionChanged=a.selectedWeaponRaw~=b.selectedWeaponRaw
 local statsBranchChanged=a.effectListAccessFlagRaw~=b.effectListAccessFlagRaw
 -- A change invalidates existing weapon advice. A *lack* of change says
 -- NOTHING about buffs: effect magnitude can change within either branch.
 local r=state((selectionChanged or statsBranchChanged) and
   'INVALIDATE_WEAPON_ADVICE_KEEP_CURRENT_ACTION' or
   'RAW_CONTEXT_UNCHANGED_BUFFS_STILL_UNKNOWN')
 r.selectedWeaponChanged=selectionChanged
 r.activeStatsBranchChanged=statsBranchChanged
 return r
end
return M
