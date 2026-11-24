"""Run full correlation matrix in REAL Lua 5.4; not EEex and not GAMEPLAY."""
from pathlib import Path
import ctypes,ctypes.util,sys
P=Path(__file__).with_name('BG_EET_RU_THREAD_FRAME_BRIDGE_V4.lua')
TESTS=r'''
local n=0
local function ck(cond,msg)
  n=n+1
  assert(cond,'scenario '..n..': '..msg)
end
local B=BG_EET_RU_THREAD_FRAME_BRIDGE_V4
local VT=0x140597CD0
local function ent(th,fr,weapon,ab,atk,tgt)
  return B.enter(th,fr,atk or 100+th,tgt or 200+th,weapon or 'SW1H04',ab or 0)
end
local function msg(th,fr,p,origin,vtab)
  return B.message(th,fr,p,vtab or VT,VT,origin or 0x39E84B)
end
ck(B.install_allowed==false and B.mode=='SOURCE_ONLY','permanent no install')
ck(select(1,B.start())==false,'cannot activate JIT')
ck(B.active_count==0 and B.blocked_count==0,'clean state')
ck(select(1,ent(1,1024,'sw1h04',0)),'enter')
local ok,data=msg(1,1024,4000)
ck(ok and data.weapon=='SW1H04' and data.visible_row_verified==false,'copies item and source-only status')
ck(data.attacker==101 and data.target==201,'unique attacker/target kept')
ck(B.active_count==1,'one frame')
ck(select(1,msg(2,1024,4001))==false,'same stack address on other thread NOT matched')
ck(select(1,msg(1,1024,4002,0x390E00))==false,'damage origin rejected with same vtable')
ck(select(1,msg(1,1024,4003,nil,VT+8))==false,'wrong vtable rejected')
ck(select(1,msg(1,1024,4000))==false,'message pointer duplicate rejected')
ck(select(1,B.exit(1,1024)),'exit')
ck(select(1,msg(1,1024,4010))==false,'stale after exit rejected')
ck(select(1,ent(1,1024,'AX1H01',1)),'reuse frame after normal exit')
ok,data=msg(1,1024,4011)
ck(ok and data.weapon=='AX1H01' and data.ability==1,'fresh event after reuse')
ck(select(1,B.exit(1,1024)),'exit #2')
-- True concurrent threads can have equal numeric frame IDs: keys are separate.
for t=1,16 do ck(select(1,ent(t,8000,'BOW01',t)),'multi-thread enter') end
ck(B.active_count==16,'concurrent frame count')
for t=1,16 do
  ok,data=msg(t,8000,100000+t)
  ck(ok and data.thread==t and data.ability==t,'thread isolated')
end
for t=1,16 do ck(select(1,B.exit(t,8000)),'multi-thread exit') end
ck(B.active_count==0,'no leaked thread entries')
-- Poison ambiguous same (thread,frame) until ALL matching enters have exited.
ck(select(1,ent(55,9000,'SW1H04',1)),'poison first')
ck(select(1,ent(55,9000,'AX1H01',1))==false,'collision second')
ck(B.active_count==0 and B.blocked_count==1 and B.blocked['55/9000']==2,'poison depth=2')
ck(select(1,ent(55,9000,'BOW01',1))==false,'collision third')
ck(B.blocked['55/9000']==3,'poison depth=3')
ck(select(1,msg(55,9000,7777))==false,'poisoned frame cannot match')
for i=1,2 do ck(select(1,B.exit(55,9000)),'decrement poison') end
ck(B.blocked['55/9000']==1,'poison persists for final active call')
ck(select(1,B.exit(55,9000)),'last exit clears')
ck(B.blocked['55/9000']==nil and B.blocked_count==0,'poison cleared')
ck(select(1,ent(55,9000,'BOW01',1)),'clean reuse after exits')
ck(select(1,B.exit(55,9000)),'clean postpoison release')
-- Need no event if damaged RESREF, unconfirmed ability, pointer, cross-thread.
for _,r in ipairs({'','BAD*NAME','TOO_LONG_REF','A-B'}) do
  ck(select(1,ent(22,10000,r,1))==false,'resref invalid')
end
for _,i in ipairs({-1,65536,1.25}) do
  ck(select(1,B.enter(22,10000,1,2,'SW1H04',i))==false,'ability invalid')
end
for _,i in ipairs({0,-1,1.5,math.huge}) do
  ck(select(1,B.enter(i,1234,1,2,'SW1H04',0))==false,'thread invalid')
end
for _,i in ipairs({0,-1,1.5,math.huge}) do
  ck(select(1,B.enter(1,i,1,2,'SW1H04',0))==false,'frame invalid')
end
ck(select(1,B.enter(1,1,1,2,'SW1H04',0/0))==false,'NaN ability rejected')
ck(select(1,B.enter(1,1,1,2,'SW1H04',0)),'fresh for origin negatives')
ck(select(1,B.message(1,1,404,VT,VT,0x390E00))==false,'wrong origin regardless of class')
ck(select(1,B.message(1,1,404,VT,VT,nil))==false,'missing origin rejected')
ck(select(1,B.message(1,1,404,VT,nil,0x39E84B))==false,'missing verified vtable rejected')
ck(select(1,B.message(1,1,404,nil,VT,0x39E84B))==false,'unknown message vtable rejected')
ck(select(1,B.exit(1,1)),'cleanup origin negatives')
-- Large pairwise stress: each event must be either exact or unambiguously held.
for t=1,22 do
  for j=1,70 do
    local f=200000+t*1000+j
    local wp=(j%2==0) and 'BOW01' or 'SW1H04'
    ck(select(1,ent(t,f,wp,j%4)),'stress enter')
    local good,d=msg(t,f,20000000+t*1000+j)
    ck(good and d.weapon==wp and d.thread==t and d.frame==f,'stress matching')
    ck(select(1,msg(t+1,f,20000000+t*1000+j))==false,'stress cross-thread mismatch')
    ck(select(1,B.exit(t,f)),'stress release')
  end
end
ck(B.active_count==0 and B.blocked_count==0,'no growth after thousands')
-- Exactly 8 distinct messages per frame; no speculative 9th row.
ck(select(1,ent(9,333333,'SW1H04',0)),'message budget enter')
for i=1,8 do ck(select(1,msg(9,333333,100+i)),'bounded msg') end
ck(select(1,msg(9,333333,109))==false,'ninth rejected')
ck(select(1,B.exit(9,333333)),'exit msg budget')
-- Two representations of one pointer have identical canonical key.
ck(select(1,ent(11,888888,'AX1H01',2)),'numeric key enters')
local r,d=B.message(11.0,888888.0,9888888,VT,VT,0x39E84B)
ck(r and d.weapon=='AX1H01','integer/float representation cannot split frame key')
ck(select(1,B.exit(11.0,888888.0)),'float exit clears integer key')
ck(B.active_count==0 and B.thread_count==0,'no numerical type leak')
-- 129th simultaneous frame must fail closed for the SESSION, clearing cache.
for i=1,128 do ck(select(1,ent(9,1000000+i,'SW1H04',1)),'fill capacity') end
ck(select(1,ent(9,1000200,'SW1H04',1))==false,'capacity fail closed')
ck(B.session_hold=='ACTIVE_FRAME_EXHAUSTED' and B.active_count==0,'cache securely cleared')
ck(select(1,msg(9,1000001,100))==false,'no posthold use')
ck(select(1,ent(9,1000300,'SW1H04',1))==false,'posthold enters denied')
local st=B.status()
ck(st.game_files_written==0 and st.install_allowed==false and st.gameplay_verified==false,'no gameplay claims')
print('BG_EET_RU_V4_REAL_LUA_SOURCE_ONLY_PASS',n)
'''

THREAD_BUDGET_LUA=r'''
local B=BG_EET_RU_THREAD_FRAME_BRIDGE_V4
local n=0
for th=1,24 do
  local ok=B.enter(th,100000+th,th,th+1,'SW1H04',0)
  assert(ok,'thread '..th)
  n=n+1
end
assert(B.thread_count==24 and B.active_count==24)
local ok=B.enter(25,100025,25,26,'SW1H04',0)
assert(not ok and B.session_hold=='THREAD_BUDGET_EXHAUSTED')
assert(B.active_count==0 and B.thread_count==0)
print('BG_EET_RU_V4_THREAD_LIMIT_PASS',n)
'''

POISON_DEPTH_LUA=r'''
local B=BG_EET_RU_THREAD_FRAME_BRIDGE_V4
assert(B.enter(1,12,100,101,'SW1H04',0))
for i=1,128 do B.enter(1,12,100,101,'SW1H04',0) end
assert(B.session_hold=='POISON_DEPTH_EXHAUSTED')
assert(B.active_count==0 and B.blocked_count==0 and B.thread_count==0)
print('BG_EET_RU_V4_POISON_LIMIT_PASS')
'''

def main():
    path=ctypes.util.find_library('lua5.4') or 'liblua5.4.so.0'
    lib=ctypes.CDLL(path)
    lib.luaL_newstate.restype=ctypes.c_void_p
    lib.luaL_openlibs.argtypes=[ctypes.c_void_p]
    lib.luaL_loadstring.argtypes=[ctypes.c_void_p,ctypes.c_char_p]
    lib.luaL_loadstring.restype=ctypes.c_int
    lib.lua_pcallk.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_ssize_t,ctypes.c_void_p]
    lib.lua_pcallk.restype=ctypes.c_int
    lib.lua_tolstring.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.POINTER(ctypes.c_size_t)]
    lib.lua_tolstring.restype=ctypes.c_char_p
    lib.lua_close.argtypes=[ctypes.c_void_p]
    for test in (TESTS, THREAD_BUDGET_LUA, POISON_DEPTH_LUA):
        state=lib.luaL_newstate();assert state
        try:
            lib.luaL_openlibs(state)
            body=P.read_bytes()+b'\n'+test.encode('utf8')
            rc=lib.luaL_loadstring(state,body)
            if rc==0:rc=lib.lua_pcallk(state,0,0,0,0,None)
            if rc:
                error=lib.lua_tolstring(state,-1,None)
                raise RuntimeError('LUA_V4_FAILED: '+str(error))
        finally:lib.lua_close(state)
    return 0
if __name__=='__main__':raise SystemExit(main())