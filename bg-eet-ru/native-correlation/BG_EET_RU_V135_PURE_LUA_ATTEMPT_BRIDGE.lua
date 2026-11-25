-- BG_EET_RU V135. PURE LUA MODEL. NOT LOADED IN GAME; NO EEex hooks or game writes.
-- An eventual synchronous native callback must copy the CItem RESREF before exit.
-- Do not infer HIT/MISS from raw_return, message adjacency, callsite target, or UI order.
local Bridge = {}
Bridge.__index = Bridge
local ENTRY = 0x39DA6F
local EXIT = 0x39E99B
local MAX_SAFE_SEQ = 9007199254740991

local function posnum(n)
  return type(n) == 'number' and n % 1 == 0 and n > 0 and n <= MAX_SAFE_SEQ
end
local function resref(s)
  return type(s) == 'string' and #s > 0 and #s <= 8 and s:match('^[A-Z0-9_]+$') ~= nil
end
local function strtoken(s)
  return type(s) == 'string' and #s > 0 and #s <= 128
end
local function u16(n)
  return type(n) == 'number' and n % 1 == 0 and n >= 0 and n <= 65535
end
local function u8(n)
  return type(n) == 'number' and n % 1 == 0 and n >= 0 and n <= 255
end

function Bridge.new(session, options)
  assert(strtoken(session), 'INVALID_SESSION')
  options = options or {}
  local mt = options.max_threads or 24
  local mf = options.max_frames_per_thread or 128
  local mc = options.max_completed or 512
  assert(posnum(mt) and mt <= 24 and posnum(mf) and mf <= 128 and posnum(mc) and mc <= 4096,
    'INVALID_LIMITS')
  return setmetatable({
    session = session,
    max_threads = mt,
    max_frames_per_thread = mf,
    max_completed = mc,
    threads = {}, thread_count = 0,
    seq = 0, completed = {}, errors = {}, lost = 0,
    paused_due_to_overflow = false,
    native_runtime_proven = false, game_writes = 0,
  }, Bridge)
end

function Bridge:_error(reason, thread_id)
  self.lost = self.lost + 1
  if #self.errors < 128 then
    self.errors[#self.errors+1] = {reason = reason, thread_id = thread_id}
  end
  return nil, reason
end

function Bridge:_drop_thread(thread_id, reason)
  local t = self.threads[thread_id]
  if t then
    -- Every unmatched frame is invalid after an out-of-order return.
    self.lost = self.lost + #t.stack
    self.threads[thread_id] = nil
    self.thread_count = self.thread_count - 1
  end
  return self:_error(reason, thread_id)
end

function Bridge:begin(e)
  if self.paused_due_to_overflow then return self:_error('CAPTURE_PAUSED_OVERFLOW', nil) end
  if type(e) ~= 'table' or e.entry_site_rva ~= ENTRY or
     not posnum(e.thread_id) or not posnum(e.frame_id) or
     not posnum(e.attacker_id) or not posnum(e.target_id) or
     not u16(e.ability_index) or not resref(e.weapon_resref) then
    return self:_error('INVALID_ENTRY_OR_UNCOPIED_RESREF', type(e)=='table' and e.thread_id or nil)
  end
  if (e.launcher_resref ~= nil and not resref(e.launcher_resref)) or
     (e.ammo_resref ~= nil and not resref(e.ammo_resref)) then
    return self:_error('INVALID_OPTIONAL_RESREF', e.thread_id)
  end
  if self.seq >= MAX_SAFE_SEQ then
    self.paused_due_to_overflow = true
    return self:_error('SEQUENCE_OVERFLOW', e.thread_id)
  end
  local t = self.threads[e.thread_id]
  if not t then
    if self.thread_count >= self.max_threads then
      self.paused_due_to_overflow = true
      return self:_error('MAX_THREADS_OVERFLOW', e.thread_id)
    end
    t = {stack = {}}
    self.threads[e.thread_id] = t
    self.thread_count = self.thread_count + 1
  end
  if #t.stack >= self.max_frames_per_thread then
    return self:_drop_thread(e.thread_id, 'MAX_FRAMES_PER_THREAD')
  end
  for _, frame in ipairs(t.stack) do
    if frame.frame_id == e.frame_id then
      return self:_drop_thread(e.thread_id, 'DUPLICATE_ACTIVE_FRAME')
    end
  end
  self.seq = self.seq + 1
  -- Only store primitive copies, never live CItem/ability pointers or Lua userdata.
  local record = {
    session = self.session, thread_id = e.thread_id,
    frame_id = e.frame_id, attack_seq = self.seq,
    attacker_id = e.attacker_id, target_id = e.target_id,
    weapon_resref = e.weapon_resref:sub(1,8),
    launcher_resref = e.launcher_resref and e.launcher_resref:sub(1,8) or nil,
    ammo_resref = e.ammo_resref and e.ammo_resref:sub(1,8) or nil,
    ability_index = e.ability_index,
    entry_site_rva = ENTRY,
    outcome = 'UNVERIFIED',
    raw_return = nil,
    native_abi_verified = false,
    weapon_at_actual_swing_verified = false,
    row_join_verified = false,
    source_only = true,
  }
  t.stack[#t.stack+1] = record
  return self.seq, nil
end

function Bridge:finish(e)
  if type(e) ~= 'table' or e.exit_site_rva ~= EXIT or
     not posnum(e.thread_id) or not posnum(e.frame_id) or not u8(e.raw_return) then
    return self:_error('INVALID_EXIT_OR_RAW_RETURN', type(e)=='table' and e.thread_id or nil)
  end
  local t = self.threads[e.thread_id]
  if not t or #t.stack == 0 then
    return self:_error('ORPHAN_EXIT_NO_GUESSING', e.thread_id)
  end
  local top = t.stack[#t.stack]
  if top.frame_id ~= e.frame_id then
    return self:_drop_thread(e.thread_id, 'OUT_OF_ORDER_EXIT_STACK_INVALIDATED')
  end
  if #self.completed >= self.max_completed then
    self.paused_due_to_overflow = true
    return self:_drop_thread(e.thread_id, 'COMPLETED_CAPACITY_OVERFLOW')
  end
  t.stack[#t.stack] = nil
  if #t.stack == 0 then
    self.threads[e.thread_id] = nil
    self.thread_count = self.thread_count - 1
  end
  top.raw_return = e.raw_return
  top.exit_site_rva = EXIT
  top.return_semantics = 'RAW_BYTE_UNCLASSIFIED'
  -- Even 0 or 1 is not mapped to HIT/MISS without independent live calibration.
  top.outcome = 'UNVERIFIED'
  self.completed[#self.completed+1] = top
  return top, nil
end

function Bridge:abort_thread(thread_id, reason)
  if not posnum(thread_id) then return self:_error('INVALID_THREAD_ABORT', thread_id) end
  return self:_drop_thread(thread_id, reason or 'NATIVE_EXCEPTION_OR_UNWIND')
end

function Bridge:status()
  local pending=0
  for _, t in pairs(self.threads) do pending = pending + #t.stack end
  return {
    schema='BG_EET_RU_V135_PURE_LUA_ATTEMPT_PAIR_MODEL',
    completed_count = #self.completed, pending_count = pending,
    dropped_or_invalid_count = self.lost, error_count = #self.errors,
    paused_due_to_overflow = self.paused_due_to_overflow,
    native_runtime_proven = false,
    return_zero_is_miss_verified = false,
    return_one_is_hit_verified = false,
    actual_weapon_to_ui_row_verified = false,
    game_writes = 0,
  }
end

return Bridge
