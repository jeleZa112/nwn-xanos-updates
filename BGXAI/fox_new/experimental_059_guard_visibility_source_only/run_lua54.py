"""Execute an untrusted-free local Lua test with liblua5.4.so; no game file access."""
import ctypes, ctypes.util, pathlib, sys
lib=ctypes.CDLL(ctypes.util.find_library('lua5.4') or 'liblua5.4.so.0')
lib.luaL_newstate.restype=ctypes.c_void_p
lib.luaL_openlibs.argtypes=[ctypes.c_void_p]
lib.luaL_loadstring.argtypes=[ctypes.c_void_p,ctypes.c_char_p]
lib.luaL_loadstring.restype=ctypes.c_int
lib.lua_pcallk.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_longlong,ctypes.c_void_p]
lib.lua_pcallk.restype=ctypes.c_int
lib.lua_tolstring.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p]
lib.lua_tolstring.restype=ctypes.c_char_p
lib.lua_close.argtypes=[ctypes.c_void_p]
source=pathlib.Path(__file__).resolve().parent
p=source/'BGX59_ELIGIBILITY.lua'
h=source/'test_059.lua'
script='arg={[1]='+repr(str(p)).replace('\\','\\\\')+'}\n'+h.read_text(encoding='utf8')
L=lib.luaL_newstate();lib.luaL_openlibs(L)
try:
    code=lib.luaL_loadstring(L,script.encode('utf-8'))
    if code==0: code=lib.lua_pcallk(L,0,-1,0,0,None)
    if code!=0:
        print('FAIL: ',lib.lua_tolstring(L,-1,None).decode('utf-8',errors='replace'),file=sys.stderr)
        sys.exit(1)
finally:lib.lua_close(L)
