"""Execute dormant same-Hit callbacks inside REAL Lua 5.4, without EEex or game.

Requires liblua5.4.so.0 locally; this library is not distributed to users.
This tests model logic, NOT the native JIT / EEex Lua bindings or gameplay.
"""
from __future__ import annotations
import ctypes, ctypes.util
from pathlib import Path

ROOT=Path(__file__).resolve().parent
CHECKS_LUA=r'''
local n=0
local function check(c,name) n=n+1;assert(c,'Lua test '..tostring(n)..': '..name) end
local P=BG_EET_RU_HIT_PILOT
local logs={}
Infinity_Log=function(s)table.insert(logs,s) end
check(P~=nil,'globals available')
check(P.installed==false,'inactive by default')
check(P.authorized_install==false,'no install consent')
check(P.runtime_abi_verified==false,'no native proof')
check(P.atomic_three_hook_install_verified==false,'no JIT rollback proof')
local ok,reason=BG_EET_RU_HIT_PILOT_Start()
check(ok==false and reason=='NATIVE_JIT_INSTALL_BLOCKED_SOURCE_ONLY','Start fail closed')
P.installed=true -- mock only; native patches are never installed in this test
local weapon=function(s) return {cResRef={get=function(self) return s end}} end
BG_EET_RU_HIT_PILOT_Enter(1000,11,12,weapon('sw1h04'),0)
check(P.active[1000] and P.active[1000].weapon=='SW1H04','copies uppercase resref')
check(P.active[1000].ability==0 and P.active[1000].attacker==11 and P.active[1000].target==12,'copies scalar context')
check(P.active[1000].messages==0,'no stale message')
check(P.active[1000].item==nil and P.active[1000].cResRef==nil,'native item not retained')
BG_EET_RU_HIT_PILOT_Message(1000,4242)
check(P.active[1000].messages==1,'same frame message')
check(#logs==1 and logs[1]:find('journal_row=UNVERIFIED',1,true)~=nil,'no invented visible row')
BG_EET_RU_HIT_PILOT_Message(1001,4444)
check(P.counters.unmatched==1,'reject missing frame')
BG_EET_RU_HIT_PILOT_Message(1000,0)
check(P.counters.unmatched==2,'reject null message')
for i=2,8 do BG_EET_RU_HIT_PILOT_Message(1000,4242+i) end
check(P.active[1000].messages==8,'bounded message count')
BG_EET_RU_HIT_PILOT_Message(1000,4000)
check(P.counters.unmatched==3,'reject ninth message')
BG_EET_RU_HIT_PILOT_Exit(1000)
check(P.active[1000]==nil and P.blocked[1000]==nil,'normal exit clears')
BG_EET_RU_HIT_PILOT_Enter(1000,11,12,weapon('SW1H04'),1)
check(P.active[1000] and P.active[1000].ability==1,'frame reuse after exit')
BG_EET_RU_HIT_PILOT_Exit(1000)
BG_EET_RU_HIT_PILOT_Enter(2000,21,22,weapon('AX1H01'),1)
BG_EET_RU_HIT_PILOT_Enter(3000,31,32,weapon('BOW05'),2)
check(P.active[2000] and P.active[3000],'nested distinct frames')
BG_EET_RU_HIT_PILOT_Exit(3000)
check(P.active[2000] and P.active[3000]==nil,'nested child exit keeps parent')
BG_EET_RU_HIT_PILOT_Exit(2000)
BG_EET_RU_HIT_PILOT_Enter(4000,1,2,weapon('SW1H04'),0)
BG_EET_RU_HIT_PILOT_Enter(4000,1,2,weapon('AX1H01'),0)
check(P.active[4000]==nil and P.blocked[4000] and P.counters.conflicts==1,'ambiguous duplicate frame dropped')
BG_EET_RU_HIT_PILOT_Enter(4000,1,2,weapon('SW1H04'),0)
check(P.active[4000]==nil,'blocked frame cannot revive')
BG_EET_RU_HIT_PILOT_Exit(4000)
check(P.blocked[4000]==2,'collision still blocked after first exit')
BG_EET_RU_HIT_PILOT_Exit(4000)
check(P.blocked[4000]==1,'collision still blocked after second exit')
BG_EET_RU_HIT_PILOT_Exit(4000)
check(not P.blocked[4000],'clear collision only after all exits')
BG_EET_RU_HIT_PILOT_Enter(4000,1,2,weapon('SW1H04'),0)
check(P.active[4000]~=nil,'clean new frame')
BG_EET_RU_HIT_PILOT_Exit(4000)
for _,bad in ipairs({-1,65536,1.5}) do
  BG_EET_RU_HIT_PILOT_Enter(5011,1,2,weapon('SW1H04'),bad)
  check(P.active[5011]==nil,'invalid ability rejected')
  P.active[5011]=nil
end
BG_EET_RU_HIT_PILOT_Enter(5000,1,2,weapon('BAD*RES'),0)
check(P.active[5000]==nil,'invalid resref chars')
BG_EET_RU_HIT_PILOT_Enter(5001,1,2,weapon('TOO_LONG_REF'),0)
check(P.active[5001]==nil,'invalid resref length')
BG_EET_RU_HIT_PILOT_Enter(5002,1,2,weapon(''),0)
check(P.active[5002]==nil,'empty resref')
BG_EET_RU_HIT_PILOT_Enter(5003,1,2,{cResRef={get=function(self) error('dummy CItem fault') end}},0)
check(P.active[5003]==nil,'Lua item accessor error rejected')
BG_EET_RU_HIT_PILOT_Enter(5004,1,2,nil,0)
check(P.active[5004]==nil,'null item rejected')
BG_EET_RU_HIT_PILOT_Enter(-1,1,2,weapon('SW1H04'),0)
check(P.active[-1]==nil,'invalid frame rejected')
BG_EET_RU_HIT_PILOT_Enter(5005,'attacker',2,weapon('SW1H04'),0)
check(P.active[5005]==nil,'invalid attacker rejected')
BG_EET_RU_HIT_PILOT_Enter(5006,1,'target',weapon('SW1H04'),0)
check(P.active[5006]==nil,'invalid target rejected')
BG_EET_RU_HIT_PILOT_Enter(5007,0,2,weapon('SW1H04'),0)
check(P.active[5007]==nil,'null attacker rejected')
BG_EET_RU_HIT_PILOT_Enter(5008,1,0,weapon('SW1H04'),0)
check(P.active[5008]==nil,'null target rejected')
BG_EET_RU_HIT_PILOT_Enter(5009.1,1,2,weapon('SW1H04'),0)
check(P.active[5009.1]==nil,'fractional frame rejected')
for i=1,128 do BG_EET_RU_HIT_PILOT_Enter(100000+i,i,i+1,weapon('SW1H04'),0) end
check(P.active[100128]~=nil,'last permitted frame exists')
BG_EET_RU_HIT_PILOT_Enter(110000,9,10,weapon('SW1H04'),0)
check(P.active[110000]==nil,'129th frame blocked')
for i=1,128 do BG_EET_RU_HIT_PILOT_Exit(100000+i) end
check(next(P.active)==nil,'all frames cleared')
P.installed=false
BG_EET_RU_HIT_PILOT_Enter(6000,1,2,weapon('SW1H04'),0)
check(P.active[6000]==nil,'disabled callback does nothing')
check(P.sample_count<=P.max_samples,'telemetry bounded')
print('LUA_SOURCE_RUNTIME_PASS',n)
'''

def run():
    name=ctypes.util.find_library('lua5.4') or 'liblua5.4.so.0'
    lib=ctypes.CDLL(name)
    lib.luaL_newstate.restype=ctypes.c_void_p
    lib.luaL_openlibs.argtypes=[ctypes.c_void_p]
    lib.luaL_loadstring.argtypes=[ctypes.c_void_p,ctypes.c_char_p]
    lib.luaL_loadstring.restype=ctypes.c_int
    lib.lua_pcallk.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_ssize_t,ctypes.c_void_p]
    lib.lua_pcallk.restype=ctypes.c_int
    lib.lua_tolstring.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.POINTER(ctypes.c_size_t)]
    lib.lua_tolstring.restype=ctypes.c_char_p
    lib.lua_close.argtypes=[ctypes.c_void_p]
    state=lib.luaL_newstate()
    if not state:raise RuntimeError('LUA_STATE_ALLOCATION_FAILED')
    try:
        lib.luaL_openlibs(state)
        b=(ROOT/'BG_EET_RU_HIT_PILOT_DRAFT.lua').read_bytes()+b'\n'+CHECKS_LUA.encode('utf8')
        if lib.luaL_loadstring(state,b)!=0:
            raise RuntimeError('LUA_SYNTAX:'+str(lib.lua_tolstring(state,-1,None)))
        if lib.lua_pcallk(state,0,0,0,0,None)!=0:
            raise RuntimeError('LUA_RUNTIME:'+str(lib.lua_tolstring(state,-1,None)))
    finally:
        lib.lua_close(state)
    return {'status':'PASS','engine':'liblua5.4','gameplay_verified':False}

if __name__=='__main__':
    print(run())
