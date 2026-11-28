-- R46 witness Lua 5.4 tests: NEVER run an actual game or BCS action.
-- arg1: tempfile containing composed candidate M_BGXR46_WITNESS.lua
local path=assert(arg[1],"missing candidate Lua")
local tests=0
local function check(name,fn)
 tests=tests+1
 local ok,err=pcall(fn)
 if not ok then error(name..": "..tostring(err)) end
end
local function eq(a,b)assert(a==b,tostring(a).." != "..tostring(b))end
local NAME='BGXAI_R46_BDDEFAI_Witness'
local logs={}
local savedPrint=print
local function reset()
 _G[NAME]=nil
 _G.EEex_LuaTrigger_Object=nil
 _G.EEex_Sprite_GetInPortrait=nil
 _G.EEex_Sprite_GetInPortraitID=nil
 logs={}
 _G.print=function(s)logs[#logs+1]=s end
end
local function fixture(opt)
 opt=opt or {}
 reset()
 local sourceID=opt.actorID or 1234
 local portraitID=opt.portraitID or 1234
 local m=assert(loadfile(path))()
 local actor={
  m_id=sourceID,m_typeAI={m_Class=opt.class or 3},
  getActiveStats=function()return {m_nKit=opt.kit or 16384} end,
  getScriptLevelResRef=function(_self,level)
   eq(level,4)
   return opt.assigned or 'BDDEFAI'
  end}
 _G.EEex_LuaTrigger_Object=actor
 _G.EEex_Sprite_GetInPortrait=function(i)eq(i,1)
  return {m_id=opt.wrapperID or portraitID} -- distinct TABLE wrapper
 end
 _G.EEex_Sprite_GetInPortraitID=function(i)eq(i,1);return portraitID end
 return m
end
local function call()
 local f=assert(_G[NAME])
 local outcome=f()
 eq(outcome,false) -- no BAF RESPONSE, even after successful witness
end
check('inert import registers witness but no action or log',function()
 local m=fixture()
 eq(m.registered,true)
 eq(m.ordersSent,0)
 eq(m.inspect().witnessOnce,false)
 eq(#logs,0)
end)

check('same actor distinct portrait wrapper emits ONE event and always false',function()
 local m=fixture()
 call()
 eq(#logs,1)
 assert(logs[1]:find('R46_BDDEFAI_CLASS_TRIGGER_EVALUATED_JAGAN_READONLY',1,true))
 eq(m.inspect().witnessOnce,true)
 call();eq(#logs,1)
end)
check('different portrait numeric ID suppresses event',function()
 fixture({actorID=1234,portraitID=5678})
 call();eq(#logs,0)
end)
check('different fresh wrapper m_id suppresses event',function()
 fixture({actorID=1234,portraitID=1234,wrapperID=5678})
 call();eq(#logs,0)
end)
check('wrong CLASS assigned resref suppresses event',function()
 fixture({assigned='DPLAYER3'})
 call();eq(#logs,0)
end)
check('wrong class suppresses event',function()
 fixture({class=1})
 call();eq(#logs,0)
end)
check('wrong kit suppresses event',function()
 fixture({kit=1})
 call();eq(#logs,0)
end)
check('missing EEex_LuaTrigger_Object suppresses event',function()
 fixture();_G.EEex_LuaTrigger_Object=nil
 call();eq(#logs,0)
end)
check('missing EEex portrait APIs suppresses event',function()
 fixture();_G.EEex_Sprite_GetInPortrait=nil
 call();eq(#logs,0)
end)
check('malformed script assignment suppresses event',function()
 fixture({assigned='BDDEF A'})
 call();eq(#logs,0)
end)
check('global namespace collision is NOT overridden',function()
 reset()
 local sentinel=function()return true end
 _G[NAME]=sentinel
 local m=assert(loadfile(path))()
 eq(m.registered,false)
 eq(_G[NAME],sentinel)
 -- independent BAF pcall(our_name);return false remains false even if collided
 local script=assert(load('pcall(BGXAI_R46_BDDEFAI_Witness); return false'))
 eq(script(),false)
end)
check('pcall wrapper always returns false on throwing global',function()
 reset()
 _G[NAME]=function()error('broken global')end
 local script=assert(load('pcall(BGXAI_R46_BDDEFAI_Witness); return false'))
 eq(script(),false)
end)
check('pcall wrapper always returns false on missing global',function()
 reset()
 local script=assert(load('pcall(BGXAI_R46_BDDEFAI_Witness); return false'))
 eq(script(),false)
end)
check('Lua witness pcall never crashes BAF if print raises',function()
 fixture()
 _G.print=function(_)error('no console')end
 call()
 -- Value was withheld; still no engine action, fail closed on proof.
end)
reset()
_G.print=savedPrint
print('BGXAI R46 INERT BCS SOURCE ONLY '..tests..'/'..tests..
      ' PASS; GAME NOT TOUCHED; RESPONSE ALWAYS FALSE')
