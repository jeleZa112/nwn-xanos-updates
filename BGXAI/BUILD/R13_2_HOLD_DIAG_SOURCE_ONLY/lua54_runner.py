import ctypes,sys
lib=ctypes.CDLL('liblua5.4.so.0');c_void_p=ctypes.c_void_p;c_int=ctypes.c_int
lib.luaL_newstate.restype=c_void_p
lib.luaL_openlibs.argtypes=[c_void_p]
lib.luaL_loadfilex.argtypes=[c_void_p,ctypes.c_char_p,ctypes.c_char_p];lib.luaL_loadfilex.restype=c_int
lib.lua_pcallk.argtypes=[c_void_p,c_int,c_int,c_int,c_int,c_void_p];lib.lua_pcallk.restype=c_int
lib.lua_tolstring.argtypes=[c_void_p,c_int,ctypes.POINTER(ctypes.c_size_t)];lib.lua_tolstring.restype=ctypes.c_char_p
lib.lua_close.argtypes=[c_void_p]
L=lib.luaL_newstate();lib.luaL_openlibs(L)
r=lib.luaL_loadfilex(L,sys.argv[1].encode(),None)
if r==0:r=lib.lua_pcallk(L,0,-1,0,0,None)
if r!=0:
 size=ctypes.c_size_t();msg=lib.lua_tolstring(L,-1,ctypes.byref(size));print('LUA_FAILED',msg.decode(errors='replace') if msg else r)
lib.lua_close(L);sys.exit(0 if r==0 else 1)
