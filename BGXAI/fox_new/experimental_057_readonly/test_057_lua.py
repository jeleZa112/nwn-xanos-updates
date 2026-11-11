#!/usr/bin/env python3
"""Run actual Lua 5.4 mock checks; does not load EEex, game, or Windows."""
import ctypes
from pathlib import Path
LIB=ctypes.CDLL('liblua5.4.so.0')
LIB.luaL_newstate.restype=ctypes.c_void_p
LIB.luaL_openlibs.argtypes=[ctypes.c_void_p]
LIB.luaL_loadfilex.argtypes=[ctypes.c_void_p,ctypes.c_char_p,ctypes.c_char_p]
LIB.luaL_loadfilex.restype=ctypes.c_int
LIB.luaL_loadstring.argtypes=[ctypes.c_void_p,ctypes.c_char_p]
LIB.luaL_loadstring.restype=ctypes.c_int
LIB.lua_pcallk.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_longlong,ctypes.c_void_p]
LIB.lua_pcallk.restype=ctypes.c_int
LIB.lua_tolstring.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p]
LIB.lua_tolstring.restype=ctypes.c_char_p
LIB.lua_close.argtypes=[ctypes.c_void_p]
source=Path(__file__).with_name('M_BX57.lua')
assert source.is_file()
code=source.read_text('utf-8')
assert 'ClearActions(' not in code and 'ProtectObject(' not in code and 'setLocalInt(' not in code
assert 'ActionOverride(' not in code and 'io.open(' not in code and 'os.execute(' not in code
assert source.stem=='M_BX57' and len(source.stem)<=8

def run(s, content, is_file=False):
    if is_file:
        rc=LIB.luaL_loadfilex(s, str(content).encode(), None)
    else:
        rc=LIB.luaL_loadstring(s,content.encode())
    assert rc==0, f'Lua syntax: {LIB.lua_tolstring(s,-1,None)}'
    rc=LIB.lua_pcallk(s,0,0,0,0,None)
    assert rc==0, f'Lua runtime: {LIB.lua_tolstring(s,-1,None)}'

L=LIB.luaL_newstate()
try:
    LIB.luaL_openlibs(L)
    run(L, '''
msgs={}; key_listener=nil
function Infinity_DisplayString(t) msgs[#msgs+1] = t end
function EEex_Key_AddPressedListener(f, consume) assert(consume==false); key_listener=f end
function EEex_Key_IsDown(k) return k==0x400000E0 or k==0x400000E2 end
local vars = {BGX38_GUARD=1,BGX52_REQ_SLOT=3,BGX52_EXPIRE=1000,BGX52_COOLDOWN=990}
local guardian = {m_nModalState=0}
function guardian:getLocalInt(k) return vars[k] or 0 end
function EEex_Sprite_GetInPortraitID(i) if i==1 then return 301 else return -1 end end
function EEex_GameObject_Get(id) if id==301 then return guardian end end
BGX43Probe={snapshot=function() return {
  version='0.3.22-056-ACTIVE-GUARD-OPTIN',weapon_hit_registered=true,
  weapon_hit_calls=3,weapon_hit_errors=0, bcs_bridge_enabled=true,
  bridge_prepared_count=1,bridge_attempts=2,guard_signal_errors=0,
  bridge_last={result='PREPARED_BCS_ONLY',victim_slot=3,chosen_guardian=301},
  bridge_rejections={no_guardian_with_f_mode=1},
} end}
''')
    run(L,source,True)
    run(L, '''
assert(BGX57Diag.registered==true and type(key_listener)=='function')
assert(key_listener(0)==false and #msgs==0) -- no interception of unrelated keys
assert(key_listener(0x40000043)==false and #msgs==5)
assert(string.find(msgs[1], 'H=3', 1, true))
assert(string.find(msgs[2], 'PREP=1 ATT=2', 1, true))
assert(string.find(msgs[3], 'PREPARED_BCS_ONLY', 1, true))
assert(string.find(msgs[4], 'no_guardian_with_f_mode', 1, true))
assert(string.find(msgs[5], 'P2 F=1 Q=3 MOD=0', 1, true))
assert(BGX57Diag.pressCount==1)
''')
    print('PASS: Lua5.4 syntax, hotkey, read-only 056 snapshot, guardian locals, nonconsuming')
    run(L, '''
BGX43Probe=nil
assert(BGX57Diag.report()==false)
assert(string.find(msgs[#msgs], 'not loaded', 1, true))
Infinity_DisplayString=nil
assert(BGX57Diag.report()==false)
assert(BGX57Diag.lastError=='DISPLAY_API_UNAVAILABLE')
''')
    print('PASS: unloaded 056 and unavailable display fail safely')
finally:
    LIB.lua_close(L)
print('PASS: source does not call combat, local-writing, filesystem, or external APIs')