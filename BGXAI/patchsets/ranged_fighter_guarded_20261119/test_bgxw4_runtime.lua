-- BGXW4 offline EEex hook mocks. No game actions, no runtime install.
local folder=(arg and arg[0] or ''):match('^(.*[/\\])') or './'
local orig={print=print,Infinity_Log=Infinity_Log,EEex_Action_AddSpriteStartedActionListener=EEex_Action_AddSpriteStartedActionListener,
 EEex_Sprite_GetInPortraitID=EEex_Sprite_GetInPortraitID,EEex_Sprite_GetActiveStats=EEex_Sprite_GetActiveStats,
 io=io,os=os}
local core=dofile(folder..'BGXAI_WEAPON_ACTIVE_R4_READONLY.lua')
local results={} ;local hooks={}
local function set()
 BGXWeaponActiveR4=nil
 hooks={};results={}
 Infinity_Log=function(s)results[#results+1]=s end
 print=function(s)results[#results+1]=s end
 io={open=function()return nil end}
 os={getenv=function()return nil end,date=function() return '2026-11-22T00:00:00Z' end}
 EEex_Action_AddSpriteStartedActionListener=function(fn)hooks[#hooks+1]=fn end
 EEex_Sprite_GetInPortraitID=function(index)if index==2 then return 139135050 end end
 EEex_Sprite_GetActiveStats=function(sprite)return sprite.stats end
end
local count=0
local function test(name,fn) set();fn();count=count+1;orig.print('PASS '..name) end
local function example()
 local stats={};for _,n in ipairs(core.fields) do stats[n]=0 end
 stats.m_nNumberOfAttacks=2;stats.m_nProficiencyShortBow=1
 return {m_id=139135050,m_equipment={m_selectedWeapon=12,m_selectedWeaponAbility=0},stats=stats}
end
local function active_lines()
 local l={}
 for _,s in ipairs(results) do if s:find('"type":"ACTIVE"',1,true) then l[#l+1]=s end end
 return l
end
test('registers one hook, SESSION and READY emitted',function()
 dofile(folder..'M_BGXW4.lua'); assert(#hooks==1);assert(#results>=2)
 assert(results[1]:find('"type":"SESSION"',1,true))
 assert(results[2]:find('"type":"READY"',1,true))
end)
test('one party action logs selected ammo APR2 and pips',function()
 dofile(folder..'M_BGXW4.lua')
 hooks[1](example(),{m_actionID=30})
 local l=active_lines();assert(#l>=1)
 assert(l[1]:find('"actor":139135050',1,true))
 assert(l[1]:find('"selectedWeaponRaw":12',1,true))
 assert(l[1]:find('"m_nNumberOfAttacks":2',1,true))
 assert(l[1]:find('"m_nProficiencyShortBow":1',1,true))
end)
test('no raw stats claims to authorize switch',function()
 dofile(folder..'M_BGXW4.lua');hooks[1](example(),{m_actionID=30})
 local l=active_lines(); assert(#l>=1)
 assert(l[1]:find('"dispatchAuthorized":false',1,true))
 assert(l[1]:find('"allBuffsObserved":false',1,true))
 assert(l[1]:find('"alternateSlotAPRVerified":false',1,true))
end)
test('irrelevant NPC not logged',function()
 dofile(folder..'M_BGXW4.lua');local e=example();e.m_id=456
 hooks[1](e,{m_actionID=30});assert(#active_lines()==0)
end)
test('missing m_nSTR serialized as null not zero',function()
 dofile(folder..'M_BGXW4.lua');local e=example();e.stats.m_nSTR=nil
 hooks[1](e,{m_actionID=30});assert(active_lines()[1]:find('"m_nSTR":null',1,true))
end)
test('bad engine fields held within error hook without crashing',function()
 dofile(folder..'M_BGXW4.lua');local e=example();e.stats=setmetatable({m_nNumberOfAttacks=7},{__index=function()error('bad pointer')end})
 hooks[1](e,{m_actionID=30});assert(active_lines()[1]:find('"m_nNumberOfAttacks":7',1,true))
 assert(active_lines()[1]:find('"m_nTHAC0":null',1,true))
end)
test('max64 events, never exceeds',function()
 dofile(folder..'M_BGXW4.lua');for i=1,75 do hooks[1](example(),{m_actionID=30}) end
 assert(#active_lines()==64);assert(BGXWeaponActiveR4.recorded==64);assert(BGXWeaponActiveR4.skipped==11)
end)
test('duplicate dofile does not register twice',function()
 dofile(folder..'M_BGXW4.lua');dofile(folder..'M_BGXW4.lua');assert(#hooks==1)
end)
test('hook unavailable does not install',function()
 EEex_Action_AddSpriteStartedActionListener=nil
 dofile(folder..'M_BGXW4.lua');assert(BGXWeaponActiveR4.registered==false);assert(#hooks==0)
end)
test('failed hook does not throw and has no orders',function()
 EEex_Action_AddSpriteStartedActionListener=function()error('mock hook error')end
 dofile(folder..'M_BGXW4.lua');assert(BGXWeaponActiveR4.registered==false)
 assert(BGXWeaponActiveR4.ordersSent==0)
end)
for k,v in pairs(orig) do _G[k]=v end
print('BGXAI_R4_WRAPPER_OFFLINE_PASS '..count..'/'..count)
