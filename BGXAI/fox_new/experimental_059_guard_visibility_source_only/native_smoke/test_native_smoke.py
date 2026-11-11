"""Run the exact BGXAI 059 read-only console command against Lua 5.4 mocks.
No connection to Baldur's Gate, no game writes.
"""
from __future__ import annotations
import ctypes
import ctypes.util
from pathlib import Path

BASE=Path(__file__).resolve().parent
CODE=(BASE/'BGX59_NATIVE_SMOKE_READONLY.lua').read_text(encoding='utf8')
lib=ctypes.CDLL(ctypes.util.find_library('lua5.4'))
lib.luaL_newstate.restype=ctypes.c_void_p
lib.luaL_openlibs.argtypes=[ctypes.c_void_p]
lib.luaL_loadstring.argtypes=[ctypes.c_void_p,ctypes.c_char_p]
lib.luaL_loadstring.restype=ctypes.c_int
lib.lua_pcallk.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_longlong,ctypes.c_void_p]
lib.lua_pcallk.restype=ctypes.c_int
lib.lua_tolstring.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p]
lib.lua_tolstring.restype=ctypes.c_char_p
lib.lua_close.argtypes=[ctypes.c_void_p]

def exec_lua(src):
    s=lib.luaL_newstate()
    if not s:raise RuntimeError('Lua state unavailable')
    try:
        lib.luaL_openlibs(s)
        for part in (src,):
            assert lib.luaL_loadstring(s,part.encode('utf8'))==0,lib.lua_tolstring(s,-1,None)
            assert lib.lua_pcallk(s,0,0,0,0,None)==0,lib.lua_tolstring(s,-1,None)
    finally:lib.lua_close(s)

MOCK='''
ARE_A,ARE_B={},{}
portraits={[1]=102,[2]=103,[3]=104}
objects={}
function obj(id,area) return {m_id=id,m_pArea=area} end
objects[102]=obj(102,ARE_A);objects[103]=obj(103,ARE_A);objects[104]=obj(104,ARE_A)
EEex_Sprite_GetInPortraitID=function(i) return portraits[i] end
EEex_GameObject_Get=function(i) return objects[i] end
EEex_UDEqual=function(a,b) return rawequal(a,b) end
sight={[102]=true,[104]=true}
calls=0;messages={};writes=0
EEex_Sprite_ForAllOfTypeStringInRange=function(g,typ,r,cb,los,nonSprites)
 assert(typ=='[ANYONE]' and r==128 and los==true and nonSprites==false)
 calls=calls+1
 if throw_sight then error('synthetic EEex LOS error') end
 if sight[g.m_id] then cb(objects[103]) end
end
C={DisplayText=function(self,s) messages[#messages+1]=s end}
'''

def run(case, extra, expected):
    tests = MOCK+'\n'+extra+'\n'+CODE+'\n'
    checks=[f"assert({e}, 'check {i}')" for i,e in enumerate(expected)]
    checks+=['assert(writes==0)','assert(#messages==2)']
    # execute complete command and assertions in the same Lua state
    exec_lua(MOCK+'\n'+extra+'\n'+CODE+'\n'+'\n'.join(checks))
    print('PASS',case)

run('both guardians same area, LOS yes','',[
 'calls==2','messages[1]:find("G=P2 V=P3 ARE=true LOS=true OK=true",1,true)~=nil',
 'messages[2]:find("G=P4 V=P3 ARE=true LOS=true OK=true",1,true)~=nil'])
run('P4 in a different ARE','objects[104].m_pArea=ARE_B',[
 'calls==1','messages[2]:find("ARE=false LOS=false OK=false",1,true)~=nil'])
run('P2 behind LOS obstruction','sight[102]=false',[
 'calls==2','messages[1]:find("ARE=true LOS=false OK=true",1,true)~=nil'])
run('no sight listener function','EEex_Sprite_ForAllOfTypeStringInRange=nil',[
 'calls==0','messages[1]:find("ARE=true LOS=false OK=false",1,true)~=nil'])
run('LOS query throws but is contained','throw_sight=true',[
 'calls==2','messages[1]:find("ARE=true LOS=false OK=false",1,true)~=nil'])
run('guardian object missing','objects[104]=nil',[
 'calls==1','messages[2]:find("ARE=false LOS=false OK=false",1,true)~=nil'])
run('victim missing','objects[103]=nil',[
 'calls==0','messages[1]:find("ARE=false LOS=false OK=false",1,true)~=nil'])
run('false area compare','EEex_UDEqual=function(a,b)return false end',[
 'calls==0','messages[1]:find("ARE=false LOS=false OK=false",1,true)~=nil'])
run('area compare error is contained','EEex_UDEqual=function(a,b)error("synthetic pointer error")end',[
 'calls==0','messages[1]:find("ARE=false LOS=false OK=false",1,true)~=nil'])
assert not any(s in CODE for s in ('setLocalInt(', 'SetGlobal(', 'ProtectObject(', 'Attack(', 'ClearActions(', 'ActionOverride(', 'io.open(', 'os.execute('))
print('PASS','no writes / combat commands')
print('SUCCESS: 10 smoke probe mock checks')
