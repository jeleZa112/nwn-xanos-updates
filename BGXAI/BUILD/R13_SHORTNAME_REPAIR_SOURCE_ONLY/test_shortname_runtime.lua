-- Runtime smoke fixture: validates Lua chunk, SESSION/READY and no duplicate registration.
-- No EEex game access; never proof of native runtime.
local logs={}
local listeners={}
Infinity_Log=function(line) logs[#logs+1]=line end
EEex_Action_AddSpriteStartedActionListener=function(fn) listeners[#listeners+1]=fn end
EEex_Sprite_GetInPortraitID=function() return -1 end
EEex_Sprite_GetActiveStats=function() return {} end
EEex_GameObject_Get=function() return nil end
local realOsGetenv=os.getenv
os.getenv=function() return nil end
local source='M_BGXD13.lua'
dofile(source)
assert(type(BGXTargetDefenseR13)=='table')
assert(BGXTargetDefenseR13.registered==true)
assert(BGXTargetDefenseR13.active==true)
assert(BGXTargetDefenseR13.ordersSent==0)
assert(#listeners==1)
assert(#logs==2)
assert(logs[1]:find('"type":"SESSION"',1,true))
assert(logs[2]:find('"type":"READY"',1,true))
local reference=BGXTargetDefenseR13
dofile(source)
assert(BGXTargetDefenseR13==reference and #listeners==1 and #logs==2)
os.getenv=realOsGetenv
print('PASS R13_SHORTNAME_LUA54_INIT_SESSION_READY_SINGLETON_NO_GAME')
