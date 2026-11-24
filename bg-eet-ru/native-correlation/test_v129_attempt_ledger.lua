-- Run with lua5.4 in source-only CI. No game / EEex required.
local source='BG_EET_RU_V129_ATTEMPT_LEDGER.lua'
local M=dofile(source)
local function eq(a,b)assert(a==b,tostring(a)..' != '..tostring(b))end
local ok,why=M.install()
eq(ok,false);eq(why,'NO_NATIVE_HOOK_OR_GAME_INSTALL_IN_SOURCE_ONLY_MODEL')
local s=M.status()
eq(s.installed,false);eq(s.game_files_written,0)

-- A real attempt may have NO native CMessage at the chosen Hit() callsite.
local success,one=M.enter(11,101,1001,2001,'SW1H04',0)
eq(success,true);eq(one,1)
local done,ev=M.finish(11,101,one)
eq(done,true);eq(ev.message_seen,false)
eq(ev.attack_result,'UNVERIFIED');eq(ev.combat_row_join_verified,false)
eq(M.completed[1].message_emission,'NOT_SEEN')
eq(M.completed[1].weapon_resref,'SW1H04')
eq(M.statistics.without_message,1)

local a,two=M.enter(11,102,1001,2002,'arow01',1)
eq(a,true);eq(two,2)
local reject,why=M.message(11,102,two,333,0x390DF9)
eq(reject,false);eq(why,'WRONG_CALLSITE')
local yes,tag=M.message(11,102,two,333,0x39E84B)
eq(yes,true);eq(tag,'OPTIONAL_MESSAGE_CAPTURED_SOURCE_ONLY')
local f,res=M.finish(11,102,two)
eq(f,true);eq(res.message_seen,true);eq(res.ui_row_id,nil)
eq(res.attack_result,'UNVERIFIED')
eq(M.completed[2].message_emission,'SEEN')
eq(M.statistics.with_message,1)

-- Wrong actor/frame or invented token MUST NOT attach to another attempt.
local ok3,three=M.enter(22,103,2000,3000,'BOW05',0)
eq(ok3,true)
local bad,reason=M.message(23,103,three,400,0x39E84B)
eq(bad,false);eq(reason,'NOT_SAME_OPEN_ATTEMPT')
bad,reason=M.message(22,103,three+1,400,0x39E84B)
eq(bad,false);eq(reason,'NOT_SAME_OPEN_ATTEMPT')
bad,reason=M.finish(22,103,three+1)
eq(bad,false);eq(reason,'EXIT_NOT_SAME_ATTEMPT')
local good=M.finish(22,103,three)
eq(good,true)
eq(M.statistics.without_message,2)

-- Invalid CItem/attacker/target/ability -> no invented event.
for _,ref in ipairs({'bad.item','TOOLONGRESREF',''}) do
 local passed=M.enter(25,110,1,2,ref,0)
 eq(passed,false)
end
eq(M.statistics.invalid,3)

-- Nested frame reuse without a verified exit poisons the whole session.
local hold=dofile(source)
local go,oid=hold.enter(1,55,10,20,'SW1H04',0)
eq(go,true)
local second,stop=hold.enter(1,55,10,20,'SW1H04',0)
eq(second,false);eq(stop,'SESSION_HOLD')
eq(hold.status().session_hold,'DUPLICATE_THREAD_FRAME')
eq(hold.status().active,0)
eq(hold.status().game_files_written,0)
eq(hold.install(),false)

-- Future storage exhaustion can't silently drop a truncated event chain.
local bounded=dofile(source)
bounded.max_completed=1
local b1,id1=bounded.enter(1,5,1,2,'BOW05',0)
eq(b1,true);eq(bounded.finish(1,5,id1),true)
local b2,id2=bounded.enter(1,6,1,2,'BOW05',0)
eq(b2,true)
local stopped,status=bounded.finish(1,6,id2)
eq(stopped,false);eq(status,'SESSION_HOLD')
eq(bounded.status().session_hold,'COMPLETED_BUDGET_EXCEEDED')
eq(bounded.status().gameplay_verified,false)

print('V129_LUA_ATTEMPT_LEDGER_SOURCE_ONLY_PASS')
