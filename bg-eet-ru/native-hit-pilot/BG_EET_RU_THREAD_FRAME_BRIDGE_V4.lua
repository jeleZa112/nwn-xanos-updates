-- BG_EET_RU V4 / SOURCE-ONLY logical correlation core; NOT loaded by game.
-- No EEex hooks, no JIT, no memory reads/writes, no game text modification.
-- REQUIRE a native wrapper to supply verified thread ID, RBP frame, attacker,
-- target, synchronous CItem RESREF and the exact Hit CALLSITE provenance.
-- IMPORTANT: 0x597CD0 vtable is SHARED by damage and Hit messages.
-- A vtable-only match must always be rejected.

local M={
  schema='BG_EET_RU_THREAD_FRAME_CALLSITE_BRIDGE_V4',
  mode='SOURCE_ONLY',install_allowed=false,runtime_abi_verified=false,
  max_threads=24,max_active=128,max_blocked=128,max_poison_depth=128,
  max_messages=8,max_samples=64,
  active={},blocked={},thread_refs={},thread_count=0,active_count=0,blocked_count=0,
  epoch=0,sample_count=0,session_hold=nil,
  counters={enters=0,messages=0,matched_source=0,ambiguous=0,invalid=0,
    wrong_origin=0,wrong_class=0,exits=0,holds=0,unmatched=0}
}
BG_EET_RU_THREAD_FRAME_BRIDGE_V4=M

local function pointer(x)
  return type(x)=='number' and x==x and x%1==0
    and x>0 and x<=9007199254740991
end
local function smallint(x)
  return type(x)=='number' and x==x and x%1==0
    and x>=0 and x<=65535
end
local function resref(x)
  return type(x)=='string' and #x>0 and #x<=8
    and x:match('^[A-Za-z0-9_]+$')~=nil
end
local function key(thread,frame)
  if not pointer(thread) or not pointer(frame) then return nil end
  -- Lua 5.1-compatible numeric keys; combine with a string to avoid
  -- accidental concatenated decimal ambiguities and cross-thread collisions.
  return string.format('%.0f/%.0f',thread,frame),string.format('%.0f',thread)
end
local function hold(reason)
  if M.session_hold then return end
  M.session_hold=reason
  M.active={}; M.blocked={}; M.thread_refs={}
  M.active_count=0;M.blocked_count=0;M.thread_count=0
  M.counters.holds=M.counters.holds+1
end
local function block(k,n)
  local depth=M.blocked[k]
  if depth then
    if depth+n>M.max_poison_depth then hold('POISON_DEPTH_EXHAUSTED')
    else M.blocked[k]=depth+n end
  else
    if M.blocked_count>=M.max_blocked then hold('POISON_SLOTS_EXHAUSTED')
    else M.blocked[k]=n;M.blocked_count=M.blocked_count+1 end
  end
end
local function reserve_thread(t)
  if not M.thread_refs[t] then
    if M.thread_count>=M.max_threads then
      hold('THREAD_BUDGET_EXHAUSTED')
      return false
    end
    M.thread_count=M.thread_count+1
    M.thread_refs[t]=0
  end
  M.thread_refs[t]=M.thread_refs[t]+1
  return true
end
local function release_thread(t)
  local count=M.thread_refs[t]
  if count then
    if count<=1 then M.thread_refs[t]=nil;M.thread_count=M.thread_count-1
    else M.thread_refs[t]=count-1 end
  end
end
local function fail(reason)return false,reason end

-- Only plain numbers/strings are retained. Never CItem or message userdata.
-- "weapon" comes from the synchronous native CItem ability at this callsite.
-- No guessing about launcher, ammunition, hands, or visible journal row.
function M.enter(thread,frame,attacker,target,weapon,ability)
  if M.session_hold then return fail('SESSION_HOLD') end
  local k,t=key(thread,frame)
  if not k then M.counters.invalid=M.counters.invalid+1;return fail('THREAD_FRAME_UNVERIFIED') end
  M.counters.enters=M.counters.enters+1
  local active=M.active[k]
  if active then
    M.active[k]=nil;M.active_count=M.active_count-1
    M.counters.ambiguous=M.counters.ambiguous+1
    block(k,2)
    return fail('DUPLICATE_FRAME_POISONED')
  end
  if M.blocked[k] then
    M.counters.ambiguous=M.counters.ambiguous+1
    block(k,1)
    return fail('POISONED_FRAME')
  end
  if not pointer(attacker) or not pointer(target) or not smallint(ability)
     or not resref(weapon) then
    M.counters.invalid=M.counters.invalid+1
    -- No context is created; bad CItem never becomes a predicted weapon.
    return fail('INVALID_ITEM_ATTACK_CONTEXT')
  end
  if M.active_count>=M.max_active then
    hold('ACTIVE_FRAME_EXHAUSTED');return fail('SESSION_HOLD')
  end
  if not reserve_thread(t) then return fail('SESSION_HOLD') end
  M.epoch=M.epoch+1
  M.active[k]={weapon=string.upper(weapon),ability=ability,
    attacker=attacker,target=target,epoch=M.epoch,messages=0,message_ids={}}
  M.active_count=M.active_count+1
  return true,'FRAME_CAPTURED_SOURCE_ONLY'
end

function M.message(thread,frame,msgptr,vtable,expected_vtable,origin_rva)
  M.counters.messages=M.counters.messages+1
  if M.session_hold then return fail('SESSION_HOLD') end
  local k=key(thread,frame)
  if not k then M.counters.invalid=M.counters.invalid+1;return fail('THREAD_FRAME_UNVERIFIED') end
  local ctx=M.active[k]
  if not ctx or M.blocked[k] then M.counters.unmatched=M.counters.unmatched+1;return fail('NO_EXACT_FRAME') end
  -- Never equate generic CMessage vtable with a roll. Damage uses this vtable!
  if origin_rva~=0x39E84B then M.counters.wrong_origin=M.counters.wrong_origin+1;return fail('WRONG_NATIVE_CALLSITE') end
  if not pointer(msgptr) or not pointer(vtable) or not pointer(expected_vtable)
     or vtable~=expected_vtable then
    M.counters.wrong_class=M.counters.wrong_class+1;return fail('MESSAGE_CLASS_UNVERIFIED')
  end
  if ctx.message_ids[msgptr] then
    M.counters.ambiguous=M.counters.ambiguous+1;return fail('DUPLICATE_MESSAGE_POINTER')
  end
  if ctx.messages>=M.max_messages then
    M.counters.ambiguous=M.counters.ambiguous+1
    return fail('MESSAGES_EXHAUSTED')
  end
  ctx.messages=ctx.messages+1
  ctx.message_ids[msgptr]=true
  M.counters.matched_source=M.counters.matched_source+1
  -- Critical: source-only proof isn't an identity for the UI combatLog row.
  -- We return a newly copied string, never edit a native message.
  return true,{status='MATCHED_SOURCE_ONLY_UI_UNVERIFIED',
    weapon=ctx.weapon,ability=ctx.ability,attacker=ctx.attacker,
    target=ctx.target,epoch=ctx.epoch,thread=thread,frame=frame,
    visible_row_verified=false,miss_verified=false,game_modified=false}
end

function M.exit(thread,frame)
  M.counters.exits=M.counters.exits+1
  if M.session_hold then return fail('SESSION_HOLD') end
  local k,t=key(thread,frame)
  if not k then M.counters.invalid=M.counters.invalid+1;return fail('THREAD_FRAME_UNVERIFIED') end
  if M.blocked[k] then
    M.blocked[k]=M.blocked[k]-1
    if M.blocked[k]<=0 then M.blocked[k]=nil; M.blocked_count=M.blocked_count-1; release_thread(t) end
    return true,'POISON_DEPTH_DECREMENTED'
  end
  if M.active[k] then M.active[k]=nil;M.active_count=M.active_count-1;release_thread(t);return true,'FRAME_RELEASED' end
  return fail('UNKNOWN_FRAME')
end

function M.start()
  return false,'NO_JIT_OR_GAME_INSTALL_IN_THIS_SOURCE_ONLY_MODULE'
end
function M.status()
  return {schema=M.schema,mode=M.mode,install_allowed=false,
    game_files_written=0,gameplay_verified=false,
    active=M.active_count,blocked=M.blocked_count,threads=M.thread_count,session_hold=M.session_hold,
    counters=M.counters}
end