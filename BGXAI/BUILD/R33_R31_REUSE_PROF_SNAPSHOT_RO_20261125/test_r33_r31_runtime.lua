-- R33 candidate: only previously read R4 data are serialized, no second listener.
local file=assert(arg and arg[1],"Pass generated SOURCE ONLY Lua path")
local listeners,logs,orders={}, {},0
Infinity_Log=function(line)logs[#logs+1]=line end
EEex_ReadLString=function()return 'MOCORE.BCS'end
EEex_Sprite_GetInPortraitID=function(i)return i==2 and 1001 or nil end
EEex_Action_AddSpriteStartedActionListener=function(fn)listeners[#listeners+1]=fn end
SelectWeaponAbility=function()orders=orders+1;error("engine dispatch forbidden")end
ClearActions=function()orders=orders+1;error("queue mutation forbidden")end
Attack=function()orders=orders+1;error("attack forbidden")end
local stats=setmetatable({
 m_nNumberOfAttacks=7, m_nLevel1=8,m_nLevel2=0,m_nLevel3=0,
 m_nKit=256,m_nProficiencyLongSword=3,m_nProficiencyLongBow=1,
 m_nProficiencyShortBow=0,m_nExtraProficiency2=16,
},{__index=function()return 1 end})
local getStats=function()return stats end
EEex_Sprite_GetActiveStats=function()return getStats() end
local function check(ok,message)assert(ok,message)end
local function has(s,fragment)return s:find(fragment,1,true)~=nil end
dofile(file)
check(#listeners==1,"one listener registered")
check(#logs==1 and has(logs[1],'"observerCandidate":"R33_R27V3_PASSIVE_PROF_RO"'),"R33 session provenance")
check(BGXAI_R27_ObserverPilot.registered==true,"registered flag")
check(BGXAI_R27_ObserverPilot.version=='BGXAI_R33_R27V3_PASSIVE_PROF_CANDIDATE',"R33 version")

local action={m_actionID=3,m_source={m_pchData=65536}}
local sprite={m_id=1001,m_typeAI={m_Class=2},m_bAllowEffectListCall=1,m_curAction=action,
 m_queuedActions={m_nCount=0},m_bInActionExecution=0,m_bNoInterrupt=0,
 m_curScriptNum=4,m_actionCount=0,m_interrupt=0,
 m_lOrderedBy={m_Instance=0},m_lOrderedBySent={m_Instance=0},
 m_equipment={m_selectedWeapon=35,m_selectedWeaponAbility=0,
  m_items={get=function()return nil end}}}
listeners[1](sprite,action)
check(#logs==2,"one event")
local event=logs[2]
check(has(event,'"actionRaw":3'),"real R31 attack fixture")
check(has(event,'"queuedActionsRaw":0'),"real R31 queue zero")
check(has(event,'"aiObjectClassRawCandidate":2'),"raw class candidate")
check(has(event,'"levelsAndKitRaw":{"level1":8,"level2":0,"level3":0,"kitRaw":256}'),"R4 levels kit")
local arr=event:match('"proficiencyStat89to134Raw":%[(.-)%]')
check(arr~=nil,"raw fields serialized")
local prof={}
for v in arr:gmatch('[^,]+')do prof[#prof+1]=tonumber(v)end
check(#prof==46,"46 existing prof fields")
-- WPROF IDs 90=longsword, 104=longbow, 105=shortbow, 116=extra slot 2
check(prof[90-89+1]==3,"longsword raw")
check(prof[104-89+1]==1,"longbow raw")
check(prof[105-89+1]==0,"shortbow raw")
check(prof[116-89+1]==16,"modded stat raw")
check(has(event,'"classRowVerified":false'),"no class-rights claim")
check(has(event,'"actorPipsVerified":false'),"no pips claim")
check(has(event,'"weaponToProficiencyVerified":false'),"no item mapping claim")
check(has(event,'"activeDualMultiClassVerified":false'),"no dual class claim")
check(has(event,'"alternativeAPRVerified":false'),"alt APR not claimed")
check(has(event,'"dispatchAuthorized":false') and has(event,'"ordersSent":0'),"no game action")
check(orders==0,"no commands issued")

-- Unstable R4 double-read: no fabricated stable proficiency vector.
local counter=0
getStats=function()
 counter=counter+1
 local value=counter%2==1 and 3 or 4
 return setmetatable({m_nNumberOfAttacks=7,m_nProficiencyLongSword=value},
  {__index=function()return 1 end})
end
listeners[1](sprite,action)
check(#logs==3 and has(logs[3],'"status":"HOLD_SINGLE_CALLBACK_NO_DISPATCH"'),"unstable derived HOLD")
check(has(logs[3],'"proficiencyStat89to134Raw":null'),"unstable profs not exported as if stable")
check(not has(logs[3],'"actorPipsVerified":true'),"HOLD no authority")
check(orders==0,"unstable actor no commands")

-- AI class raw changes mid-capture: hold, never certify stable.
local reads=0
sprite.m_typeAI=setmetatable({}, {__index=function(_,key)
 if key=="m_Class" then reads=reads+1;return reads==1 and 2 or 3 end
 end})
getStats=function()return stats end
listeners[1](sprite,action)
check(#logs==4 and has(logs[4],'"status":"HOLD_SINGLE_CALLBACK_NO_DISPATCH"'),"class instability HOLD")
check(orders==0,"class instability no actions")

dofile(file)
check(#listeners==1,"no duplicate listener after reload")
io.write('PASS R33 R31 REUSE PROF MOCK 46 fields, class/kit/levels, no dispatch, fail-closed\n')
