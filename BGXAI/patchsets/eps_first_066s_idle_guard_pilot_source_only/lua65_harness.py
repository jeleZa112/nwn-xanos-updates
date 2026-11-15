"""Execute Lua source in a fresh native Lua 5.4 VM via ctypes; no game or filesystem writes.

The Lua module is a source-only mock-EEex unit; this does NOT prove EEex x64 runtime.
"""
import ctypes
import ctypes.util
from pathlib import Path

LIB = ctypes.util.find_library('lua5.4')
if not LIB:
    raise RuntimeError('Lua 5.4 shared library unavailable; no fabricated PASS')
lua = ctypes.CDLL(LIB)
lua.luaL_newstate.restype = ctypes.c_void_p
lua.luaL_openlibs.argtypes = (ctypes.c_void_p,)
lua.luaL_loadstring.argtypes = (ctypes.c_void_p, ctypes.c_char_p)
lua.luaL_loadstring.restype = ctypes.c_int
lua.lua_pcallk.argtypes = (ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_longlong, ctypes.c_void_p)
lua.lua_pcallk.restype = ctypes.c_int
lua.lua_tolstring.argtypes = (ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p)
lua.lua_tolstring.restype = ctypes.c_char_p
lua.lua_close.argtypes = (ctypes.c_void_p,)

SOURCE = Path(__file__).with_name('BGX62E_CLASS_ACTION_PROBE.lua')

def run_case(preamble: str, assertions: str, source_file: Path = SOURCE) -> None:
    """Isolate each test in a fresh VM and assert actual execution, not regex checks."""
    L = lua.luaL_newstate()
    if not L:
        raise MemoryError('luaL_newstate')
    try:
        lua.luaL_openlibs(L)
        source = source_file.read_text(encoding='utf-8')
        script = preamble + '\nlocal BGXMODULE = (function()\n' + source + '\nend)()\n' + assertions
        err = lua.luaL_loadstring(L, script.encode('utf-8'))
        if err:
            msg = lua.lua_tolstring(L, -1, None)
            raise AssertionError('LUA_COMPILE_ERROR: ' + repr(msg))
        err = lua.lua_pcallk(L, 0, 0, 0, 0, None)
        if err:
            msg = lua.lua_tolstring(L, -1, None)
            raise AssertionError('LUA_EXECUTION_ERROR: ' + repr(msg))
    finally:
        lua.lua_close(L)
