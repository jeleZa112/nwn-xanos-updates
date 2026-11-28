-- R47 corrected witness: 11 mocks with the very same EEex global port R44 used.
local script=assert(arg[1],"candidate Lua tempfile required")
local oldprint=print
local count=0
local function check(label,fn)
 count=count+1
 local ok,err=pcall(fn)
 if not ok then error(label..": "..tostring(err)) end
end
local function eq(a,b)assert(a==b,tostring(a).." != "..tostring(b))end
local NAME="BGXAI_R46_BDDEFAI_Witness"
local logs={}
local function reset()
 _G[NAME]=nil
 _G.EEex_LuaTrigger_Object=nil
 _G.EEex_Sprite_GetInPortrait=nil
 _G.EEex_Sprite_GetInPortraitID=nil
 _G.EEex_AIBase_GetScriptLevelResRef=nil
 logs={}
 _G.print=function(s)logs[#logs+1]=s end
end
local function fixture(o)
 o=o or {}
 reset()
 local actor={m_id=o.actor or 1234,m_typeAI={m_Class=o.class or 3},
              getActiveStats=function() return {m_nKit=o.kit or 16384} end}
 _G.EEex_LuaTrigger_Object=actor
 _G.EEex_Sprite_GetInPortrait=function(i)eq(i,1)
  return {m_id=o.wrapper or o.portrait or 1234} end
 _G.EEex_Sprite_GetInPortraitID=function(i)eq(i,1)
  return o.portrait or 1234 end
 local hit=0
 _G.EEex_AIBase_GetScriptLevelResRef=function(ai,level)
  eq(level,4)
  eq(ai,actor)
  hit=hit+1
  return o.resref or "BDDEFAI"
 end
 local M=assert(loadfile(script))()
 return M,function()return hit end
end
local function call()
 eq(assert(_G[NAME])(),false)
end
check("global-port success, same ID in different Lua wrappers, once",function()
 local m,hits=fixture()
 call();eq(#logs,1);eq(hits(),1);call();eq(#logs,1);eq(hits(),1)
 eq(m.inspect().witnessOnce,true)
end)
check("missing global script-port is HOLD, no log",function()
 fixture();_G.EEex_AIBase_GetScriptLevelResRef=nil
 call();eq(#logs,0)
end)
check("method on actor not used even when exists",function()
 local m=fixture()
 _G.EEex_LuaTrigger_Object.getScriptLevelResRef=function()error("MUST NEVER RUN")end
 call();eq(#logs,1)
end)
check("wrong CLASS4 script name rejected",function()
 fixture({resref="DPLAYER"});call();eq(#logs,0)
end)
check("changed portrait actor ID rejected",function()
 fixture({portrait=4321});call();eq(#logs,0)
end)
check("different wrapper actor ID rejected",function()
 fixture({wrapper=4321});call();eq(#logs,0)
end)
check("wrong kit rejected",function()
 fixture({kit=1});call();eq(#logs,0)
end)
check("wrong class rejected",function()
 fixture({class=1});call();eq(#logs,0)
end)
check("missing script-owner context rejected",function()
 fixture();_G.EEex_LuaTrigger_Object=nil;call();eq(#logs,0)
end)
check("error from script-level API swallowed, BAF always false",function()
 fixture();_G.EEex_AIBase_GetScriptLevelResRef=function()error("EEex unavailable")end
 call();eq(#logs,0)
end)
check("collision cannot override original global, BAF expression still false",function()
 reset()
 local sentinel=function()return true end
 _G[NAME]=sentinel
 local m=assert(loadfile(script))()
 eq(m.registered,false);eq(_G[NAME],sentinel)
 eq(assert(load("pcall(BGXAI_R46_BDDEFAI_Witness); return false"))(),false)
end)
reset()
_G.print=oldprint
print("R47 EEex GLOBAL CLASS PORT MOCK "..count.."/"..count.." PASS; GAME NOT TOUCHED")
