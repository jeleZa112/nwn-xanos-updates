"""Isolated Lua 5.4 semantics tests for BGXAI 058 same-area selection gate.
Not an EEex runtime test, not a whole-file Lua compile, never touches game.
"""
import ctypes
from ctypes.util import find_library
libname = find_library('lua5.4') or 'liblua5.4.so.0'
lua = ctypes.CDLL(libname)
lua.luaL_newstate.restype = ctypes.c_void_p
lua.luaL_openlibs.argtypes = [ctypes.c_void_p]
lua.luaL_loadstring.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
lua.luaL_loadstring.restype = ctypes.c_int
lua.lua_pcallk.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_longlong, ctypes.c_void_p]
lua.lua_pcallk.restype = ctypes.c_int
lua.lua_tolstring.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
lua.lua_tolstring.restype = ctypes.c_char_p
lua.lua_close.argtypes = [ctypes.c_void_p]
code = r'''
local function safe(fn) local ok,val=pcall(fn); if ok then return val end; return nil end
local function selected(victim, guards)
    local victimArea=safe(function()return victim.m_pArea end)
    if not victimArea or type(EEex_UDEqual)~="function" then return nil,"area_compare_unavailable" end
    local options={}
    for _,obj in ipairs(guards) do
        local guard=safe(function()return obj:getLocalInt("BGX38_GUARD")end)
        local modal=safe(function()return obj.m_nModalState end)
        local xx=safe(function()return obj.m_pos.x end)
        local yy=safe(function()return obj.m_pos.y end)
        local guardArea=safe(function()return obj.m_pArea end)
        local sameArea=guardArea and safe(function()return EEex_UDEqual(guardArea,victimArea)end)==true
        if guard==1 and modal==0 and sameArea and type(xx)=="number" and type(yy)=="number" then
           local dx,dy=xx-victim.m_pos.x,yy-victim.m_pos.y
           options[#options+1]={id=obj.m_id, dist=dx*dx+dy*dy}
        end
    end
    if #options==0 then return nil,"no_guardian_with_f_mode_in_same_area" end
    table.sort(options,function(a,b)return a.dist<b.dist end)
    return options[1].id,nil
end
local function sp(id,area,x,y,f,modal)
   local o={m_id=id,m_pArea=area,m_pos={x=x,y=y},m_nModalState=modal or 0}
   function o:getLocalInt(n) if n=="BGX38_GUARD" then return f end return 0 end
   return o
end
EEex_UDEqual=function(a,b)return a==b end
local v=sp(103,'INSIDE',10,10,0)
local far=sp(104,'OUTSIDE',10,10,1)
local near=sp(102,'INSIDE',16,14,1)
assert(selected(v,{far,near})==102)
local id,why=selected(v,{far});assert(id==nil and why=='no_guardian_with_f_mode_in_same_area')
local nearOff=sp(102,'INSIDE',16,14,0);id,why=selected(v,{far,nearOff});assert(id==nil)
local nearSong=sp(102,'INSIDE',16,14,1,1);id,why=selected(v,{far,nearSong});assert(id==nil)
EEex_UDEqual=nil;id,why=selected(v,{near});assert(id==nil and why=='area_compare_unavailable')
EEex_UDEqual=function(a,b)return a==b end
v.m_pArea=nil;id,why=selected(v,{near});assert(id==nil and why=='area_compare_unavailable')
print('PASS: 6 isolated Lua area-gate cases')
'''
L = lua.luaL_newstate()
if not L: raise RuntimeError('luaL_newstate failed')
try:
    lua.luaL_openlibs(L)
    ret = lua.luaL_loadstring(L, code.encode('utf-8'))
    if ret: raise RuntimeError('Lua compile failed: '+str(lua.lua_tolstring(L,-1,None)))
    ret = lua.lua_pcallk(L,0,0,0,0,None)
    if ret: raise RuntimeError('Lua test failed: '+str(lua.lua_tolstring(L,-1,None)))
finally:
    lua.lua_close(L)