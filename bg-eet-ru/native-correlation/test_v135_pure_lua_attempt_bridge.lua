-- Native Lua 5.4 test of V135 source-only pairing; no game, no EEex.
local base=arg and arg[1] or '.'
local Bridge=dofile(base..'/BG_EET_RU_V135_PURE_LUA_ATTEMPT_BRIDGE.lua')
local count=0
local function eq(a,b) count=count+1;assert(a==b, tostring(a)..' != '..tostring(b)) end
local function entry(thread,frame,weapon,attacker,target)
 return {entry_site_rva=0x39DA6F,thread_id=thread,frame_id=frame,
   attacker_id=attacker or 10,target_id=target or 20,ability_index=0,
   weapon_resref=weapon or 'SW1H04'}
end
local function exit(thread,frame,value)
 return {exit_site_rva=0x39E99B,thread_id=thread,frame_id=frame,raw_return=value}
end
local b=Bridge.new('SESSION_20261125')
local id=b:begin(entry(1,1000,'AROW01'))
eq(id,1)
local rec=b:finish(exit(1,1000,0))
eq(rec.weapon_resref,'AROW01')
eq(rec.raw_return,0)
eq(rec.outcome,'UNVERIFIED')
eq(rec.return_semantics,'RAW_BYTE_UNCLASSIFIED')
eq(rec.native_abi_verified,false)
eq(b:status().pending_count,0)
local id2=b:begin(entry(1,1000,'SW1H04'))
eq(id2,2)  -- reused stack frame is valid after prior return
local rec2=b:finish(exit(1,1000,1))
eq(rec2.weapon_resref,'SW1H04')
eq(rec2.attack_seq,2)
eq(rec2.outcome,'UNVERIFIED')
eq(rec2.row_join_verified,false)
-- Nested per-thread and concurrent interleaving; no cross-thread state.
local n=Bridge.new('S')
n:begin(entry(4,41,'SW1H04')); n:begin(entry(4,42,'BOW05')); n:begin(entry(9,91,'AROW01'))
eq(n:status().pending_count,3)
eq(n:finish(exit(9,91,1)).weapon_resref,'AROW01')
eq(n:finish(exit(4,42,0)).weapon_resref,'BOW05')
eq(n:finish(exit(4,41,1)).weapon_resref,'SW1H04')
eq(n:status().pending_count,0)
-- Out-of-order return abandons an entire thread; it never pairs by adjacent events.
local bad=Bridge.new('S')
bad:begin(entry(1,51,'AROW01'));bad:begin(entry(1,52,'SW1H04'))
local missing,reason=bad:finish(exit(1,51,0))
eq(missing,nil)
eq(reason,'OUT_OF_ORDER_EXIT_STACK_INVALIDATED')
eq(bad:status().pending_count,0)
eq(bad:status().completed_count,0)
eq(bad:status().dropped_or_invalid_count,3)
-- Missing RESREF and invalid input are rejected before creating an attempt.
local missing_resref=entry(1,1);missing_resref.weapon_resref='unknown'
local x,r=bad:begin(missing_resref)
eq(x,nil);eq(r,'INVALID_ENTRY_OR_UNCOPIED_RESREF')
local fake=entry(1,1);fake.entry_site_rva=0x39DA68
x,r=bad:begin(fake);eq(x,nil);eq(r,'INVALID_ENTRY_OR_UNCOPIED_RESREF')
x,r=bad:finish(exit(1,999,0));eq(x,nil);eq(r,'ORPHAN_EXIT_NO_GUESSING')
-- Duplicate active stack-frame identity invalidates the thread (not another thread).
local d=Bridge.new('S')
d:begin(entry(1,555));d:begin(entry(2,666));x,r=d:begin(entry(1,555))
eq(x,nil);eq(r,'DUPLICATE_ACTIVE_FRAME')
eq(d:status().pending_count,1)
eq(d:finish(exit(2,666,1)).frame_id,666)
-- Capacity must stop new capture, never silently evict old events.
local cap=Bridge.new('S',{max_threads=1,max_frames_per_thread=1,max_completed=1})
cap:begin(entry(1,1))
x,r=cap:begin(entry(2,2));eq(x,nil);eq(r,'MAX_THREADS_OVERFLOW')
eq(cap:status().paused_due_to_overflow,true)
local c=Bridge.new('S',{max_completed=1})
c:begin(entry(1,1));c:finish(exit(1,1,1));c:begin(entry(1,2))
x,r=c:finish(exit(1,2,0));eq(x,nil);eq(r,'COMPLETED_CAPACITY_OVERFLOW')
eq(c:status().completed_count,1)
eq(c:status().pending_count,0)
-- 2500 independent sequential attempts with same frame address. No stale weapon.
local batch=Bridge.new('S',{max_completed=4096})
for i=1,2500 do
 local w=(i%2==0) and 'BOW05' or 'SW1H04'
 local seq=batch:begin(entry(1,55,w))
 eq(seq,i)
 local event=batch:finish(exit(1,55,i%2))
 eq(event.weapon_resref,w)
 eq(event.raw_return,i%2)
 eq(event.outcome,'UNVERIFIED')
end
eq(batch:status().completed_count,2500)
eq(batch:status().dropped_or_invalid_count,0)
eq(batch:status().native_runtime_proven,false)
print('V135_LUA_PAIRING_PASS assertions='..count)
