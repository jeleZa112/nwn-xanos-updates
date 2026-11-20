-- Simulated EEex started-action event. Runs outside Baldur's Gate.
local fn=nil
EEex_Action_AddSpriteStartedActionListener=function(f) fn=f end
local p={101,102,103}
EEex_Sprite_GetInPortraitID=function(i) return p[i+1] or -1 end
assert(dofile("M_BXFR.lua")==nil)
assert(BGXFRTrace.initialized and BGXFRTrace.active)
assert(type(fn)=="function")
local s={m_id=102,m_curScriptNum=3}
local act={m_actionID=3,m_acteeID={m_Instance=103},m_acteeID2={m_Instance=-1}}
fn(s,act)
fn(s,{m_actionID=134,m_acteeID={m_Instance=-1},m_acteeID2={m_Instance=101}})
fn(s,{m_actionID=3,m_acteeID={m_Instance=9999}})
fn(s,{m_actionID=17,m_acteeID={m_Instance=101}})
fn({m_id=998},act)
assert(BGXFRTrace.recorded==3)
local f=assert(io.open("BGXAI_FRIENDLY_ACTION_TRACE.log","r"))
local x=f:read("*a");f:close()
assert(x:find("seq=1 actor=102 slot=2 action=3 a1=103 a2=-1 target=103 target_slot=3 script=3 status=PARTY_TARGET_OBSERVED origin=UNKNOWN",1,true))
assert(x:find("seq=2 actor=102 slot=2 action=134 a1=-1 a2=101 target=101 target_slot=1 script=3 status=PARTY_TARGET_OBSERVED origin=UNKNOWN",1,true))
assert(x:find("seq=3 actor=102 slot=2 action=3 a1=9999 a2=-1 target=9999 target_slot=-1 script=3 status=TARGET_NOT_CONFIRMED_PARTY origin=UNKNOWN",1,true))
assert(not x:find("action=17",1,true))
local oldfn=fn
dofile("M_BXFR.lua")
assert(fn==oldfn)
assert(BGXFRTrace.recorded==3)
print("BGXFTRACE MOCK EEex PASS")
