-- Simulate loading the exact staged EEex module ONLY in a mock environment.
local folder=(arg and arg[0] or ''):match('^(.*[/\\])') or './'
local callback=nil
local nregister=0
local logged={}
local n=0
local function check(x,s)n=n+1;assert(x,'R27 pilot '..n..': '..s)end
EEex_Action_AddSpriteStartedActionListener=function(fn)
 nregister=nregister+1;callback=fn
end
EEex_Sprite_GetInPortraitID=function(i)if i==2 then return 9876 end end
local stats=setmetatable({m_nNumberOfAttacks=7},{__index=function()return 1 end})
EEex_Sprite_GetActiveStats=function()return stats end
Infinity_Log=function(s)logged[#logged+1]=s end
local s={m_id=9876,m_equipment={m_selectedWeapon=35,m_selectedWeaponAbility=0,
 m_items={get=function()return nil end}}}
local a={m_actionID=3}
check(BGXAI_R27_ObserverPilot==nil,'no registration before load')
dofile(folder..'M_BGXR27.lua')
check(nregister==1 and type(callback)=='function','registered once after explicit load')
check(BGXAI_R27_ObserverPilot.registered==true,'passive pilot registered')
check(logged[1]:find('"type":"SESSION"',1,true)~=nil,'session is bounded and honest')
callback(s,a)
check(#logged==2,'only one combined output per event')
check(logged[2]:find('"selectedAprKeyRaw":7',1,true)~=nil,'APR from selected only')
check(logged[2]:find('"quickWeaponsRaw":',1,true)~=nil,'R2 inventory raw evidence')
check(logged[2]:find('"dispatchAuthorized":false',1,true)~=nil,'no dispatch')
check(logged[2]:find('"engineSessionVerified":false',1,true)~=nil,'no session authenticity claim')
check(BGXAI_R27_ObserverPilot.ordersSent==0,'zero actions')
dofile(folder..'M_BGXR27.lua')
check(nregister==1,'no double registration')
print('R27 staged authorized-pilot mock '..n..' tests PASS')
