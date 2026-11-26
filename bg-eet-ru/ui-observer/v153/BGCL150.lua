-- BG EET RU V152: isolated SOURCE-ONLY candidate for future typed install.
-- Never executed by the updater; does not modify game state or game files.
-- Existing V126 RowRecord would call BG_EET_RU_V150_Poll using guarded pcall.
-- This is diagnostic, partial UI-render-tick observation, NOT lossless attack tracing.
local BG_EET_RU_CL150_Model = (function()
-- BG_EET_RU V150: source-only, NO installation, NO UI.MENU modification.
-- Pure Lua 5.2-compatible passive snapshot observer. Caller must explicitly
-- pass the actual combatLog table; this file does NOT attach any callbacks.
-- A local observation sequence is NOT an engine attack id or native UI row id.
local M = {}

function M.new(options)
    options = options or {}
    local max_rows = options.max_rows or 2048
    local max_bytes = options.max_bytes or 4096
    local max_events = options.max_events or 256
    assert(type(max_rows) == 'number' and max_rows % 1 == 0 and max_rows > 0)
    assert(type(max_bytes) == 'number' and max_bytes % 1 == 0 and max_bytes > 0)
    assert(type(max_events) == 'number' and max_events % 1 == 0 and max_events > 0)

    local state = {
        source_only = true, installed = false, game_files_written = 0,
        native_hooks_installed = false, gameplay_verified = false,
        native_attack_to_row_verified = false,
        table_ref = nil, previous = nil, last_tick = nil,
        epoch = 0, seq = 0, lost = 0, buffer = {},
    }

    local function result(status, count, reason)
        return {
            status = status, observed_new_text_rows = count or 0,
            reason = reason or '', epoch = state.epoch,
            local_observation_seq = state.seq,
            buffered_rows = #state.buffer, lost_rows = state.lost,
            source_only = true, installed = false, game_files_written = 0,
            native_hooks_installed = false, gameplay_verified = false,
            native_attack_to_row_verified = false,
            weapon_to_hit_miss_verified = false,
        }
    end

    local function copy_rows(source)
        if type(source) ~= 'table' then return nil end
        local count = #source
        if count > max_rows then return nil end
        -- Detect integer keys that would make #source ambiguous.
        for k in next, source do
            if type(k) ~= 'number' or k % 1 ~= 0 or k < 1 or k > count then
                return nil
            end
        end
        local rows = {}
        for i = 1, count do
            local text = rawget(source, i)
            if type(text) ~= 'string' or #text > max_bytes then return nil end
            rows[i] = text
        end
        return rows
    end

    function state:poll(source, tick)
        if type(tick) ~= 'number' or tick < 0 or tick % 1 ~= 0 then
            return result('HOLD_INVALID_TICK')
        end
        local now = copy_rows(source)
        if not now then
            self.table_ref = nil; self.previous = nil; self.last_tick = nil
            self.epoch = self.epoch + 1
            return result('HOLD_INVALID_OR_OVERSIZED_SNAPSHOT')
        end
        if self.previous == nil or self.table_ref == nil then
            self.table_ref, self.previous, self.last_tick = source, now, tick
            self.epoch = self.epoch + 1
            return result('BASELINE_NO_HISTORY', 0, 'INITIAL_ROWS_NOT_MARKED_NEW')
        end
        if self.table_ref ~= source then
            self.table_ref, self.previous, self.last_tick = source, now, tick
            self.epoch = self.epoch + 1
            return result('TABLE_REPLACED_RESYNC', 0, 'NO_BRIDGE_ACROSS_TABLE_IDENTITY')
        end
        if tick < self.last_tick then
            self.previous, self.last_tick = now, tick
            self.epoch = self.epoch + 1
            return result('HOLD_TICK_REGRESSION_RESYNC')
        end
        local before = self.previous
        self.previous, self.last_tick = now, tick
        if #now < #before then
            self.epoch = self.epoch + 1
            return result('HOLD_TRIM_CLEAR_OR_REWRITE', 0, 'NO_UNIQUE_APPEND_ONLY_PROOF')
        end
        for i = 1, #before do
            if before[i] ~= now[i] then
                self.epoch = self.epoch + 1
                return result('HOLD_TRIM_CLEAR_OR_REWRITE', 0, 'NO_UNIQUE_APPEND_ONLY_PROOF')
            end
        end
        local added = #now - #before
        if added == 0 then return result('NO_CHANGE') end
        if #self.buffer + added > max_events then
            self.lost = self.lost + added
            self.epoch = self.epoch + 1
            return result('HOLD_BUFFER_OVERFLOW', 0, 'NO_SILENT_DROP_OR_PARTIAL_EMISSION')
        end
        for i = #before + 1, #now do
            self.seq = self.seq + 1
            self.buffer[#self.buffer + 1] = {
                local_observation_seq = self.seq, epoch = self.epoch,
                tick = tick, text = now[i], provenance = 'APPEND_ONLY_SNAPSHOT_TEXT',
                native_attack_id = nil, native_weapon_resref = nil,
                native_result_verified = false,
                exact_ui_row_identity_verified = false,
            }
        end
        return result('APPEND_ONLY_TEXT_OBSERVED', added)
    end

    function state:drain()
        local events = self.buffer
        self.buffer = {}
        return events
    end

    return state
end
return M
end)()

local CL150 = BG_EET_RU_CL150_Model.new({max_rows=2048,max_bytes=4096,max_events=256})
local CL150_stats = {calls=0,polls=0,emitted=0,holds=0,errors=0,limit=512,
                    last_status="UNTESTED", game_files_written=0, native_hooks_installed=false,
                    native_attack_to_row_verified=false, observed_table_text_only=true}
local last_table, last_count, last_first, last_tail = nil,nil,nil,nil
local last_epoch = nil

function BG_EET_RU_V150_Status()
 return CL150_stats
end

local function emit(line)
 if type(print)=='function' then pcall(print,line) end
end

function BG_EET_RU_V150_Poll(source)
 CL150_stats.calls=CL150_stats.calls+1
 if type(source)~='table' then
  CL150_stats.last_status='HOLD_INVALID_TABLE'
  return
 end
 local n=#source
 local first=source[1]
 local last=source[n]
 if source==last_table and n==last_count and first==last_first
    and last==last_tail and CL150_stats.calls%32~=0 then
  return
 end
 last_table,last_count,last_first,last_tail=source,n,first,last
 local tick=nil
 if type(Infinity_GetGameTicks)=='function' then
  local ok,value=pcall(Infinity_GetGameTicks)
  if ok then tick=value end
 end
 CL150_stats.polls=CL150_stats.polls+1
 local ok,r=pcall(function() return CL150:poll(source,tick) end)
 if not ok then
  CL150_stats.errors=CL150_stats.errors+1
  CL150_stats.last_status='HOLD_POLL_LUA_EXCEPTION'
  return
 end
 CL150_stats.last_status=r.status
 if r.status=='APPEND_ONLY_TEXT_OBSERVED' then
  local events=CL150:drain()
  for _,event in ipairs(events) do
   if CL150_stats.emitted>=CL150_stats.limit then
    CL150_stats.holds=CL150_stats.holds+1
    if CL150_stats.emitted==CL150_stats.limit then
     emit('BG_EET_RU_V150_HOLD\tOUTPUT_LIMIT_REACHED')
     CL150_stats.emitted=CL150_stats.emitted+1
    end
    break
   end
   local raw=event.text or ''
   if #raw>1000 then
    CL150_stats.holds=CL150_stats.holds+1
    emit('BG_EET_RU_V150_HOLD\tTEXT_TOO_LONG\t'..tostring(event.local_observation_seq))
   else
    -- Only line-safe text is emitted. This sequence is not a native attack id.
    local line=raw:gsub('[\t\r\n]',' ')
    emit('BG_EET_RU_V150_RAW\t'..tostring(event.epoch)..'\t'..
         tostring(event.local_observation_seq)..'\t'..tostring(event.tick)..'\t'..line)
    CL150_stats.emitted=CL150_stats.emitted+1
   end
  end
 elseif r.status:sub(1,4)=='HOLD' or r.status=='TABLE_REPLACED_RESYNC' then
  CL150_stats.holds=CL150_stats.holds+1
  if last_epoch~=r.epoch then
   last_epoch=r.epoch
   emit('BG_EET_RU_V150_HOLD\t'..r.status..'\t'..tostring(r.epoch))
  end
 end
end
