-- BGXAI weapon runtime observer R1.1: passive evidence only, opt-in install.
-- Never changes an action, inventory, game variable, EPS queue or weapon selection.
-- RAW combat stats are NOT verified per-slot values or a proof of idle/AI origin.
if type(BGXWeaponRuntimeR1)=='table' and BGXWeaponRuntimeR1.registered then return end
local M={version='BGXAI_WEAPON_RUNTIME_R1_1',registered=false,recorded=0,
 errors=0,skipped=0,limit=320,writer='UNINITIALIZED'}
BGXWeaponRuntimeR1=M
local function safe(fn)
 local ok,val=pcall(fn)
 if ok then return val end
 return nil
end
local function field(obj,name)
 if obj==nil then return nil end
 return safe(function() return obj[name] end)
end
local function integer(v,lo,hi)
 return type(v)=='number' and v==math.floor(v) and v>=lo and v<=hi
end
local function raw(v,lo,hi)
 return integer(v,lo,hi) and tostring(v) or 'null'
end
local function portrait_slot(id)
 if not integer(id,0,2147483647) then return nil end
 for i=0,5 do
  if safe(function() return EEex_Sprite_GetInPortraitID(i) end)==id then return i end
 end
 return nil
end
local function console_write(data)
 local line='[BGXWP] '..data
 local ok=false
 if type(Infinity_Log)=='function' then
  ok=safe(function() Infinity_Log(line);return true end) or ok
 end
 if type(print)=='function' then
  ok=safe(function() print(line);return true end) or ok
 end
 if ok then M.writer='CONSOLE_FALLBACK' else M.writer='NO_OUTPUT_SINK' end
 return ok
end
local function write(data)
 if M.handle==nil then return console_write(data) end
 local ok=pcall(function()
  M.handle:write(data,'\n')
  if M.recorded%16==0 then M.handle:flush() end
 end)
 if ok then return true end
 M.errors=M.errors+1
 safe(function() M.handle:close() end)
 M.handle=nil
 return console_write(data)
end
local function observation(sprite,action,slot)
 local stats=safe(function() return EEex_Sprite_GetActiveStats(sprite) end)
 local eq=field(sprite,'m_equipment')
 return '{"type":"ACTION","sequence":'..raw(M.recorded,1,320)..
  ',"partyIndex":'..raw(slot,0,5)..
  ',"actor":'..raw(field(sprite,'m_id'),0,2147483647)..
  ',"action":'..raw(field(action,'m_actionID'),0,65535)..
  ',"scriptRaw":'..raw(field(sprite,'m_curScriptNum'),0,65535)..
  ',"selectedWeaponRaw":'..raw(field(eq,'m_selectedWeapon'),0,65535)..
  ',"effectListAccessFlagRaw":'..raw(field(sprite,'m_bAllowEffectListCall'),-50,50)..
  ',"aprRaw":'..raw(field(stats,'m_nNumberOfAttacks'),-500,500)..
  ',"thac0Raw":'..raw(field(stats,'m_nTHAC0'),-100,100)..
  ',"strengthRaw":'..raw(field(stats,'m_nSTR'),0,100)..
  ',"strengthExtraRaw":'..raw(field(stats,'m_nSTRExtra'),0,100)..
  ',"dexRaw":'..raw(field(stats,'m_nDEX'),0,100)..
  ',"damageBonusRaw":'..raw(field(stats,'m_nDamageBonus'),-500,500)..
  ',"meleeDamageBonusRaw":'..raw(field(stats,'m_nMeleeDamageBonus'),-500,500)..
  ',"missileDamageBonusRaw":'..raw(field(stats,'m_nMissileDamageBonus'),-500,500)..
  ',"missileTHAC0BonusRaw":'..raw(field(stats,'m_nMissileTHAC0Bonus'),-500,500)..
  ',"improvedHasteRaw":'..raw(field(stats,'m_bImprovedHaste'),-50,50)..
  ',"weaponAbilityVerified":false,"actualPerSlotAPRVerified":false,'..
  '"buffsExhaustivelyObserved":false,"manualOrderOriginVerified":false,'..
  '"epsQueueVerified":false,"weaponSwitchAuthorized":false}'
end
function M.on_action(sprite,action)
 local ok=pcall(function()
  if M.recorded>=M.limit then M.skipped=M.skipped+1;return end
  local slot=portrait_slot(field(sprite,'m_id'))
  if slot==nil then return end
  M.recorded=M.recorded+1
  write(observation(sprite,action,slot))
 end)
 if not ok then M.errors=M.errors+1 end
end
local function init()
 if type(EEex_Action_AddSpriteStartedActionListener)~='function' or
    type(EEex_Sprite_GetInPortraitID)~='function' or
    type(EEex_Sprite_GetActiveStats)~='function' then
  M.writer='EEEX_API_UNAVAILABLE';return false
 end
 local handle=nil
 if type(io)=='table' and type(io.open)=='function' and
    type(os)=='table' and type(os.getenv)=='function' then
  local home=safe(function() return os.getenv('USERPROFILE') end)
  if type(home)=='string' and #home>=4 and #home<=260 then
   local filename=home..'\\Documents\\BGXAI_LIVE_REPORTS\\BGXAI_WEAPON_RUNTIME_RAW_R1.jsonl'
   handle=safe(function() return io.open(filename,'a') end)
  end
 end
 M.handle=handle
 if handle then M.writer='APPEND_REPORT_ONLY'
 elseif type(Infinity_Log)=='function' or type(print)=='function' then M.writer='CONSOLE_FALLBACK'
 else M.writer='NO_OUTPUT_SINK';return false end
 local stamp=safe(function() return os.date('!%Y-%m-%dT%H:%M:%SZ') end) or 'UNKNOWN'
 if not write('{"type":"SESSION","schema":"BGXAI_WEAPON_RUNTIME_RAW_R1",'..
   '"utc":"'..stamp..'","readOnly":true,"noActionsIssued":true,"rawOnly":true}') then
  return false
 end
 local ok=safe(function()
  EEex_Action_AddSpriteStartedActionListener(M.on_action)
  return true
 end)
 if not ok then
  M.writer='EEEX_HOOK_REGISTRATION_FAILED'
  safe(function() if M.handle then M.handle:close() end end)
  M.handle=nil
  return false
 end
 M.registered=true
 write('{"type":"READY","schema":"BGXAI_WEAPON_RUNTIME_RAW_R1","observerRegistered":true}')
 return true
end
M.initialized=init()
