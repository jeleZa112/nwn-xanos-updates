-- BGXAI WEAPON PARTY OBSERVER R1. READ-ONLY GAME STATE. Explicit opt-in install ONLY.
-- Listens to EEex sprite-started actions; never issues an action, equips an item,
-- touches LOCALS, replaces a script, or edits combat state. All combat stats RAW.
-- In particular, m_nNumberOfAttacks is NOT a verified per-slot final APR.
if type(BGXWeaponRuntimeR1)=='table' and BGXWeaponRuntimeR1.registered then return end
local M={version='BGXAI_WEAPON_RUNTIME_R1',registered=false,recorded=0,errors=0,
         skipped=0,limit=320,writer='UNINITIALIZED'}
BGXWeaponRuntimeR1=M
local function safely(fn)
 local ok, val=pcall(fn)
 if ok then return val end
 return nil
end
local function field(obj,name)
 if obj==nil then return nil end
 return safely(function() return obj[name] end)
end
local function integer(v,low,high)
 return type(v)=='number' and v==math.floor(v) and v>=low and v<=high
end
local function clean(v,low,high)
 return integer(v,low,high) and tostring(v) or 'null'
end
local function member_slot(id)
 if not integer(id,0,2147483647) then return nil end
 for i=0,5 do
  local p=safely(function() return EEex_Sprite_GetInPortraitID(i) end)
  if p==id then return i end
 end
 return nil
end
local function observe(sprite,action,slot)
 local stats=safely(function()
  if type(EEex_Sprite_GetActiveStats)=='function' then
   return EEex_Sprite_GetActiveStats(sprite)
  end
  local method=field(sprite,'getActiveStats')
  if type(method)=='function' then return method(sprite) end
 end)
 local eq=field(sprite,'m_equipment')
 local selected=field(eq,'m_selectedWeapon')
 local allow=field(sprite,'m_bAllowEffectListCall')
 local nAPR=field(stats,'m_nNumberOfAttacks')
 local strength=field(stats,'m_nSTR')
 local sextra=field(stats,'m_nSTRExtra')
 local dex=field(stats,'m_nDEX')
 local thac0=field(stats,'m_nTHAC0')
 local dmg=field(stats,'m_nDamageBonus')
 local melee=field(stats,'m_nMeleeDamageBonus')
 local missile=field(stats,'m_nMissileDamageBonus')
 local rangedhit=field(stats,'m_nMissileTHAC0Bonus')
 local improved=field(stats,'m_bImprovedHaste')
 local actionID=field(action,'m_actionID')
 -- JSONL with raw values only; a non-present field is null and is never guessed.
 return '{"type":"ACTION","partyIndex":'..clean(slot,0,5)..
 ',"actor":'..clean(field(sprite,'m_id'),0,2147483647)..
 ',"action":'..clean(actionID,0,65535)..
 ',"scriptRaw":'..clean(field(sprite,'m_curScriptNum'),0,65535)..
 ',"selectedWeaponRaw":'..clean(selected,0,65535)..
 ',"effectListAccessFlagRaw":'..clean(allow,-50,50)..
 ',"aprRaw":'..clean(nAPR,-500,500)..
 ',"thac0Raw":'..clean(thac0,-100,100)..
 ',"strengthRaw":'..clean(strength,0,100)..
 ',"strengthExtraRaw":'..clean(sextra,0,100)..
 ',"dexRaw":'..clean(dex,0,100)..
 ',"damageBonusRaw":'..clean(dmg,-500,500)..
 ',"meleeDamageBonusRaw":'..clean(melee,-500,500)..
 ',"missileDamageBonusRaw":'..clean(missile,-500,500)..
 ',"missileTHAC0BonusRaw":'..clean(rangedhit,-500,500)..
 ',"improvedHasteRaw":'..clean(improved,-50,50)..
 ',"weaponAbilityVerified":false,"actualPerSlotAPRVerified":false,'..
 '"buffsExhaustivelyObserved":false,"manualOrderOriginVerified":false,'..
 '"epsQueueVerified":false,"weaponSwitchAuthorized":false}'
end
local function write(data)
 if M.handle==nil then M.writer='FILE_UNAVAILABLE';return false end
 local ok=pcall(function()
  M.handle:write(data,'\n')
  if M.recorded%16==0 then M.handle:flush() end
 end)
 if not ok then
  M.errors=M.errors+1;M.writer='FILE_WRITE_STOP'
  safely(function() M.handle:close() end);M.handle=nil
 end
 return ok
end
function M.on_action(sprite,action)
 -- Unconditionally isolate observer faults from the EEex action dispatcher.
 local ok=pcall(function()
  if M.recorded>=M.limit then M.skipped=M.skipped+1;return end
  local id=field(sprite,'m_id')
  local slot=member_slot(id)
  if slot==nil then return end
  -- No heavy logging outside the party and no attempt to inspect inventory.
  M.recorded=M.recorded+1
  write(observe(sprite,action,slot))
 end)
 if not ok then M.errors=M.errors+1 end
end
local function init()
 if type(EEex_Action_AddSpriteStartedActionListener)~='function' or
    type(EEex_Sprite_GetInPortraitID)~='function' or
    type(EEex_Sprite_GetActiveStats)~='function' then
  M.writer='EEEX117_API_UNAVAILABLE';return false
 end
 if type(os)~='table' or type(os.getenv)~='function' or
    type(io)~='table' or type(io.open)~='function' then
  M.writer='REPORT_IO_UNAVAILABLE';return false
 end
 local home=safely(function() return os.getenv('USERPROFILE') end)
 if type(home)~='string' or #home<4 or #home>260 then
  M.writer='USERPROFILE_UNAVAILABLE';return false
 end
 -- The installer creates this folder before game launch. Never create folders
 -- from within the game process, and never fall back to the game directory.
 local path=home..'\\Documents\\BGXAI_LIVE_REPORTS\\BGXAI_WEAPON_RUNTIME_RAW_R1.jsonl'
 local f=safely(function() return io.open(path,'a') end)
 if not f then M.writer='REPORT_DIRECTORY_UNAVAILABLE';return false end
 M.handle=f;M.writer='APPEND_REPORT_ONLY'
 local stamp=safely(function() return os.date('!%Y-%m-%dT%H:%M:%SZ') end) or 'UNKNOWN'
 write('{"type":"SESSION","schema":"BGXAI_WEAPON_RUNTIME_RAW_R1","utc":"'..stamp..'",'..
  '"readOnly":true,"noActionsIssued":true,"rawOnly":true}')
 local good=safely(function()
  EEex_Action_AddSpriteStartedActionListener(M.on_action)
  return true
 end)
 if not good then
  M.writer='EEEX_HOOK_REGISTRATION_FAILED'
  safely(function() M.handle:close() end)
  M.handle=nil;return false
 end
 M.registered=true
 return true
end
M.initialized=init()
