-- BG_EET_RU V129 SOURCE-ONLY attempt ledger. NEVER loaded by game.
-- 0x39E84B AddMessage is CONDITIONAL in the user's exact CGameSprite::Hit().
-- Therefore an attempt must be counted by a separate validated Hit-entry source,
-- regardless of whether a CMessage is emitted. Missing CMessage != MISS.
-- No JIT, no native hook registration, no menu, message or file modification.
local M={
 schema='BG_EET_RU_V129_HIT_ATTEMPT_LEDGER_SOURCE_ONLY',
 mode='SOURCE_ONLY', install_allowed=false, installed=false,
 active={}, count=0, next_ordinal=0, completed={},
 max_active=128,max_completed=128, session_hold=nil,
 statistics={entered=0,closed=0,with_message=0,without_message=0,invalid=0}
}
BG_EET_RU_V129_ATTEMPT_LEDGER=M

local function id(v)
 return type(v)=='number' and v==v and v%1==0
  and v>0 and v<=9007199254740991
end
local function ability(v)
 return type(v)=='number' and v==v and v%1==0 and v>=0 and v<=65535
end
local function item(v)
 return type(v)=='string' and #v>0 and #v<=8
  and v:match('^[a-zA-Z0-9_]+$')~=nil
end
local function key(thread,frame)
 if not id(thread) or not id(frame) then return nil end
 return string.format('%.0f/%.0f',thread,frame)
end
local function stop(reason)
 if M.session_hold==nil then M.session_hold=reason end
 M.active={}; M.count=0
 return false,'SESSION_HOLD'
end

function M.enter(thread,frame,attacker,target,weapon,ability_index)
 if M.session_hold then return false,'SESSION_HOLD' end
 local k=key(thread,frame)
 if not k or not id(attacker) or not id(target) or not item(weapon)
  or not ability(ability_index) then
   M.statistics.invalid=M.statistics.invalid+1
   return false,'UNVERIFIED_NATIVE_CONTEXT'
 end
 if M.active[k] then return stop('DUPLICATE_THREAD_FRAME') end
 if M.count>=M.max_active then return stop('ACTIVE_BUDGET_EXCEEDED') end
 M.next_ordinal=M.next_ordinal+1
 local attempt={local_ordinal=M.next_ordinal,thread=thread,frame=frame,
   attacker=attacker,target=target,weapon_resref=string.upper(weapon),
   ability_index=ability_index,
   native_message_ptr=nil,message_seen=false,ui_row_id=nil,
   attack_result='UNVERIFIED',source_scope='ENTRY_MODEL_ONLY',
   native_abi_verified=false,gameplay_verified=false}
 M.active[k]=attempt;M.count=M.count+1
 M.statistics.entered=M.statistics.entered+1
 -- This ordinal is LOCAL ONLY. It is NOT an engine attack sequence or UI id.
 return true,attempt.local_ordinal
end

function M.message(thread,frame,ordinal,msgptr,origin_rva)
 if M.session_hold then return false,'SESSION_HOLD' end
 local k=key(thread,frame)
 if not k or not id(ordinal) or not id(msgptr) then return false,'INVALID_MESSAGE_ID' end
 local a=M.active[k]
 if not a or a.local_ordinal~=ordinal then return false,'NOT_SAME_OPEN_ATTEMPT' end
 if origin_rva~=0x39E84B then return false,'WRONG_CALLSITE' end
 if a.message_seen then return stop('DUPLICATE_MESSAGE_FOR_ATTEMPT') end
 a.native_message_ptr=msgptr
 a.message_seen=true
 return true,'OPTIONAL_MESSAGE_CAPTURED_SOURCE_ONLY'
end

function M.finish(thread,frame,ordinal)
 if M.session_hold then return false,'SESSION_HOLD' end
 local k=key(thread,frame)
 if not k or not id(ordinal) then return false,'INVALID_EXIT' end
 local a=M.active[k]
 if not a or a.local_ordinal~=ordinal then return false,'EXIT_NOT_SAME_ATTEMPT' end
 if #M.completed>=M.max_completed then return stop('COMPLETED_BUDGET_EXCEEDED') end
 M.active[k]=nil;M.count=M.count-1
 -- Never infer a miss from a missing message; the native CALL is conditional.
 if a.message_seen then a.message_emission='SEEN'
 else a.message_emission='NOT_SEEN' end
 a.source_scope='SOURCE_ONLY_NOT_GAMEPLAY_VERIFIED'
 a.attack_result='UNVERIFIED'
 a.ui_row_id=nil
 a.combat_row_join_verified=false
 a.gameplay_verified=false
 M.completed[#M.completed+1]=a
 M.statistics.closed=M.statistics.closed+1
 if a.message_seen then M.statistics.with_message=M.statistics.with_message+1
 else M.statistics.without_message=M.statistics.without_message+1 end
 return true,{local_ordinal=a.local_ordinal,message_seen=a.message_seen,
   attack_result='UNVERIFIED',ui_row_id=nil,
   weapon_resref=a.weapon_resref,combat_row_join_verified=false}
end

function M.status()
 return {schema=M.schema,mode=M.mode,installed=false,install_allowed=false,
   active=M.count,completed=#M.completed,session_hold=M.session_hold,
   game_files_written=0,gameplay_verified=false,
   attack_outcomes_verified=false,ui_row_join_verified=false,
   statistics=M.statistics}
end
function M.install()
 return false,'NO_NATIVE_HOOK_OR_GAME_INSTALL_IN_SOURCE_ONLY_MODEL'
end
return M
