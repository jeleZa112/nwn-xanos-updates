-- Offline EEex mock. Run with: lua5.3|lua5.4|luajit test_r31_runtime.lua <generated_source.lua>
local file=assert(arg and arg[1],"source-only generated Lua path required")
local logs={}
local listeners={}
local registrations=0
local commands=0
local function check(cond,why)
  assert(cond,why)
end
Infinity_Log=function(line) logs[#logs+1]=line end
EEex_ReadLString=function(ptr,maxLen)
  if ptr==65536 then return 'MOCore.bcs' end
  error('unexpected test pointer')
end
EEex_Sprite_GetInPortraitID=function(index)
  if index==2 then return 1001 end
  return nil
end
local stats=setmetatable({m_nNumberOfAttacks=7},{__index=function() return 1 end})
EEex_Sprite_GetActiveStats=function(sprite) return stats end
EEex_Action_AddSpriteStartedActionListener=function(listener)
  registrations=registrations+1
  listeners[#listeners+1]=listener
end
-- Detect any unexpected engine action from the composed observer.
SelectWeaponAbility=function() commands=commands+1;error('forbidden equip') end
ClearActions=function() commands=commands+1;error('forbidden clear') end
Attack=function() commands=commands+1;error('forbidden attack') end

dofile(file)
check(registrations==1 and #listeners==1,'one EEex listener registered')
check(type(BGXAI_R27_ObserverPilot)=='table' and
 BGXAI_R27_ObserverPilot.registered==true,'runtime registry is true')
check(BGXAI_R27_ObserverPilot.version=='BGXAI_R31_R27V3_PASSIVE_CANDIDATE',
 'exact V3 source wrapper identity')
check(#logs==1 and logs[1]:find('"type":"SESSION"',1,true)~=nil,
 'read-only SESSION is logged')

local action={m_actionID=3,m_source={m_pchData=65536}}
local sprite={m_id=1001,m_bAllowEffectListCall=1,m_curAction=action,
 m_queuedActions={m_nCount=2},m_bInActionExecution=0,m_bNoInterrupt=0,
 m_curScriptNum=4,m_actionCount=2,m_interrupt=0,
 m_lOrderedBy={m_Instance=0},m_lOrderedBySent={m_Instance=0},
 m_equipment={m_selectedWeapon=35,m_selectedWeaponAbility=0,
   m_items={get=function() return nil end}}}
listeners[1](sprite,action)
check(#logs==2,'one real mock callback emitted')
local line=logs[2]
local function has(fragment)
  return line:find(fragment,1,true)~=nil
end
check(has('"type":"R27_SINGLE_CALLBACK"'),'R27 event shape retained')
check(has('"queueSnapshotStable":true'),'raw queue count stable')
check(has('"queuedActionsRaw":2'),'nonempty queue observed, not invented')
check(has('"queueNonemptyObserved":true'),'busy queue status observed')
check(has('"selectedAprKeyRaw":7'),'selected APR observed')
check(has('"actionOriginVerified":false'),'origin remains unverified')
check(has('"manualEpsQueueVerified":false'),'EPS origin remains unverified')
check(has('"alternativeAPRVerified":false'),'alternatives still not verified')
check(has('"dispatchAuthorized":false'),'no dispatch')
check(has('"ordersSent":0'),'no engine orders emitted')
check(commands==0,'not even a mock action issued')
dofile(file)
check(registrations==1 and #logs==2,'duplicate dofile did not re-register')

-- A vanished EEex API is a safe HOLD, no extra listener or orders.
BGXAI_R27_ObserverPilot=nil
EEex_Action_AddSpriteStartedActionListener=nil
dofile(file)
check(registrations==1,'missing EEex API does not register')
check(BGXAI_R27_ObserverPilot.registered==false and
 BGXAI_R27_ObserverPilot.writer=='REQUIRED_EEEX_API_MISSING',
 'missing native API is explicit passive HOLD')
check(commands==0,'failed startup also sent no actions')
io.write('R31 SOURCE ONLY OFFLINE MOCK PASS; 1 listener, queue=2, 0 orders\n')
