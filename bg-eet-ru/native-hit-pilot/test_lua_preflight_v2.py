"""Genuine Lua 5.4 mock-memory and hostile callback tests.
No installed EEex, no JIT, no game IO. SOURCE/MODEL result only.
"""
from __future__ import annotations
import ctypes, ctypes.util
from pathlib import Path
ROOT=Path(__file__).resolve().parent
CHECKS=r'''
local n=0
local function check(c,m) n=n+1; assert(c,'V2 case '..n..' '..m) end
local P=BG_EET_RU_HIT_PILOT
local base=0x140000000
local first=base+0x39DA86
local mem={}
local function put(addr,hex)
  local offset=0
  for h in hex:gmatch('%x%x') do mem[addr+offset]=tonumber(h,16);offset=offset+1 end
end
local function reset()
  mem={}
  put(first-0x1E,'4881ec80000000')
  put(first+0xDC5,'e81064e6ff')
  put(first+0xF10,'e865e40500')
  put(first,'e9')
  put(first-0x11,'488d15a1c92400')
  EEex_PtrSize=8
  EEex_Label=function(name) if name=='Hook-CGameSprite::Hit()-FirstCall' then return first end end
  EEex_ReadU8=function(addr) return mem[addr] end
end
reset()
local ok, sites=BG_EET_RU_HIT_PILOT_Preflight()
check(ok==true,'mock exact original sites produce source preflight')
check(sites.capture==first-0x1E and sites.message==first+0xDC5 and sites.exit==first+0xF10,'all sites same function')
check(sites.forbidden==first-0x11 and sites.first==first,'old LEA forbidden and existing hook left intact')
local cases={
  {first-0x1E,'CAPTURE_BYTES_CHANGED_HOLD'},
  {first+0xDC5,'MESSAGE_BYTES_CHANGED_HOLD'},
  {first+0xF10,'EXIT_BYTES_CHANGED_HOLD'},
  {first,'EEEX_FIRSTCALL_NOT_ALREADY_PATCHED_HOLD'},
  {first-0x11,'OLD_RIP_RELATIVE_SITE_DRIFT_HOLD'},
}
for _,case in ipairs(cases) do
  reset();mem[case[1]]=bit32 and bit32.bxor(mem[case[1]],1) or ((mem[case[1]]+1)%256)
  local a,b=BG_EET_RU_HIT_PILOT_Preflight()
  check(a==false and b==case[2],'single-byte mutated source must HOLD '..case[2])
end
reset();EEex_PtrSize=4
local a,b=BG_EET_RU_HIT_PILOT_Preflight()
check(a==false and b=='EEEX_X64_BINDINGS_REQUIRED','reject non-x64 EEex')
reset();EEex_Label=nil
a,b=BG_EET_RU_HIT_PILOT_Preflight()
check(a==false and b=='EEEX_X64_BINDINGS_REQUIRED','reject no label resolver')
reset();EEex_Label=function() error('engine label panic') end
a,b=BG_EET_RU_HIT_PILOT_Preflight()
check(a==false and b=='FIRSTCALL_LABEL_MISSING','resolver error safely held')
for _,bad in ipairs({false,0,-1,0x10,2.5,math.huge}) do
  reset();EEex_Label=function() return bad end
  a,b=BG_EET_RU_HIT_PILOT_Preflight()
  check(a==false and b=='FIRSTCALL_LABEL_MISSING','invalid FirstCall label held')
end
reset();EEex_ReadU8=function() error('engine read panic') end
a,b=BG_EET_RU_HIT_PILOT_Preflight()
check(a==false and b=='CAPTURE_BYTES_CHANGED_HOLD','reader exception gracefully held')
reset();EEex_ReadU8=function() return 'string-not-byte' end
a,b=BG_EET_RU_HIT_PILOT_Preflight()
check(a==false and b=='CAPTURE_BYTES_CHANGED_HOLD','reader wrong return type held')
reset()
P.authorized_install=true; P.runtime_abi_verified=true; P.atomic_three_hook_install_verified=true
local start,why=BG_EET_RU_HIT_PILOT_Start()
check(start==false and why=='RUNTIME_HOOK_IMPLEMENTATION_NOT_VERIFIED' and not P.installed,'even all flags cannot install JIT')
P.authorized_install=false; P.runtime_abi_verified=false; P.atomic_three_hook_install_verified=false
P.installed=true -- ONLY mock Lua; no native code installed
local weapon=function(s)return {cResRef={get=function()return s end}} end
local before=P.counters.invalid
for _,bad in ipairs({'bogus',0,-1,1.2,math.huge}) do
  local okay=pcall(BG_EET_RU_HIT_PILOT_Exit,bad)
  check(okay and P.counters.invalid>before,'Exit invalid frame not a Lua panic')
  before=P.counters.invalid
end
local nan=0/0
check(pcall(BG_EET_RU_HIT_PILOT_Exit,nil),'Exit nil no table indexing failure')
check(pcall(BG_EET_RU_HIT_PILOT_Exit,nan),'Exit NaN no table indexing failure')
check(pcall(BG_EET_RU_HIT_PILOT_Message,nil,nil),'Message nil/nil no failure')
check(pcall(BG_EET_RU_HIT_PILOT_Message,nan,123),'Message NaN no failure')
check(pcall(BG_EET_RU_HIT_PILOT_Enter,nil,1,2,weapon('AX1H01'),0),'Enter nil no failure')
check(pcall(BG_EET_RU_HIT_PILOT_Enter,nan,1,2,weapon('AX1H01'),0),'Enter NaN no failure')
local ev={cResRef={get=function()return 'SW1H04' end}}
BG_EET_RU_HIT_PILOT_Enter(100,1,2,ev,0)
BG_EET_RU_HIT_PILOT_Enter(100,1,2,weapon('AX1H01'),1)
check(P.active[100]==nil and P.blocked[100]==2,'first collision poisoned with two exits required')
BG_EET_RU_HIT_PILOT_Enter(100,1,2,ev,0)
check(P.blocked[100]==3 and P.active[100]==nil,'third colliding nested enter counted')
BG_EET_RU_HIT_PILOT_Exit(100)
check(P.blocked[100]==2,'first exit does not revive poisoned frame')
BG_EET_RU_HIT_PILOT_Enter(200,3,4,ev,0)
check(P.active[200]~=nil,'unrelated frame still accepted while poisoned one blocked')
BG_EET_RU_HIT_PILOT_Exit(100)
check(P.blocked[100]==1,'second exit still blocked')
BG_EET_RU_HIT_PILOT_Exit(100)
check(P.blocked[100]==nil,'third exit clears all collision levels')
BG_EET_RU_HIT_PILOT_Enter(100,1,2,ev,0)
check(P.active[100]~=nil,'new clean native epoch can reuse frame address')
BG_EET_RU_HIT_PILOT_Exit(100)
BG_EET_RU_HIT_PILOT_Exit(200)
local before=P.counters.invalid
for _,bad in ipairs({{},false,math.huge,nan}) do
  check(pcall(BG_EET_RU_HIT_PILOT_Enter,bad,1,2,ev,0),'invalid type never throws')
end
check(P.counters.invalid>=before+4,'invalid counters raised')
local blimit=P.max_blocked
P.max_blocked=2
for i=1,3 do
  BG_EET_RU_HIT_PILOT_Enter(1000+i,1,2,ev,0)
  BG_EET_RU_HIT_PILOT_Enter(1000+i,1,2,ev,0)
end
check(P.hold_reason=='BLOCKED_FRAME_BUDGET_EXHAUSTED','many poisoned frames terminate logging')
check(next(P.active)==nil and next(P.blocked)==nil,'halt clears Lua-only context')
local seen=P.counters.entries
BG_EET_RU_HIT_PILOT_Enter(7777,1,2,ev,0)
check(P.counters.entries==seen and not P.active[7777],'after hold observer remains off')
P.max_blocked=blimit
-- This per-session hold is deliberately NOT reset by a public API.
-- Restarting game is the only way to create a fresh disabled-by-default source model.
print('LUA_PREFLIGHT_HARDENING_PASS',n)
'''

def run():
    lib=ctypes.CDLL(ctypes.util.find_library('lua5.4') or 'liblua5.4.so.0')
    lib.luaL_newstate.restype=ctypes.c_void_p
    lib.luaL_openlibs.argtypes=[ctypes.c_void_p]
    lib.luaL_loadstring.argtypes=[ctypes.c_void_p,ctypes.c_char_p]
    lib.luaL_loadstring.restype=ctypes.c_int
    lib.lua_pcallk.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_ssize_t,ctypes.c_void_p]
    lib.lua_pcallk.restype=ctypes.c_int
    lib.lua_tolstring.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p]
    lib.lua_tolstring.restype=ctypes.c_char_p
    lib.lua_close.argtypes=[ctypes.c_void_p]
    state=lib.luaL_newstate()
    if not state:raise RuntimeError('LUA_ALLOC_FAILED')
    try:
        lib.luaL_openlibs(state)
        raw=(ROOT/'BG_EET_RU_HIT_PILOT_DRAFT.lua').read_bytes()+b'\n'+CHECKS.encode('utf8')
        rc=lib.luaL_loadstring(state,raw)
        if rc:raise RuntimeError('LUA_LOAD: '+str(lib.lua_tolstring(state,-1,None)))
        rc=lib.lua_pcallk(state,0,0,0,0,None)
        if rc:raise RuntimeError('LUA_EXEC: '+str(lib.lua_tolstring(state,-1,None)))
    finally:
        lib.lua_close(state)

if __name__=='__main__':run()
