-- BG_EET_RU / native same-Hit observer pilot / SOURCE ONLY / not an installable release
-- Based on pinned Baldur.exe SHA fc821a4806a0305b84fd85f1aad2bd472c8db642ed34b4494ae62351cae1c580
-- Native JIT code is deliberately *not armed*. Game UI, rolls, APR, ammo and damage unchanged.
-- Before activation, review Win64 ABI, EEex JIT, cross-thread Lua state, unwind and transactional rollback.
-- CRITICAL: old suggested capture site FirstCall-0x11 is RIP-relative LEA. DO NOT HOOK IT.
-- Replacement capture site FirstCall-0x1E is relocatable `sub rsp, 0x80`.

local P = {
  schema = 'BG_EET_RU_SAME_HIT_NATIVE_PILOT_SOURCE_ONLY_V2',
  authorized_install = false,              -- only guarded installer may set, after typed consent
  runtime_abi_verified = false,             -- remains false until independent live ABI verification
  atomic_three_hook_install_verified = false, -- EEex JIT hooks are not a rollback transaction
  installed = false,
  -- Source-only strategy contract, NOT executable hooks. A relocated REL32 CALL
  -- must use EEex_HookBeforeCallWithLabels, never raw-copy BeforeRestore.
  hook_plan = {
    capture = 'EEex_HookBeforeRestoreWithLabels',
    message = 'EEex_HookBeforeCallWithLabels',
    exit = 'EEex_HookBeforeCallWithLabels',
  },
  max_active = 128,
  max_blocked = 128,
  max_same_frame_depth = 128,
  hold_reason = nil,
  max_samples = 64,
  next_epoch = 0,
  active = {},
  blocked = {},
  sample_count = 0,
  counters = {entries=0, invalid=0, conflicts=0, messages=0, unmatched=0, exits=0, session_holds=0},
}
BG_EET_RU_HIT_PILOT = P

-- Native pointer IDs must be positive integral Lua values. No arithmetic is
-- performed on pointers, and no native userdata is retained across callbacks.
local function valid_id(v)
  return type(v)=='number' and v>0 and v%1==0
end

local function session_hold(reason)
  P.hold_reason = reason
  P.counters.session_holds = P.counters.session_holds + 1
  -- This is only Lua-model state. No native JIT can be installed by this file.
  P.active = {}
  P.blocked = {}
end

local function bounded_block(frame)
  local current=P.blocked[frame]
  if current then
    if current>=P.max_same_frame_depth then
      session_hold('SAME_FRAME_COLLISION_OVERFLOW')
    else
      P.blocked[frame]=current+1
    end
    return
  end
  local n=0
  for _ in pairs(P.blocked) do n=n+1 end
  if n>=P.max_blocked then
    session_hold('BLOCKED_FRAME_BUDGET_EXHAUSTED')
    return
  end
  -- Two unpaired enters need TWO exits before frame ID can be trusted again.
  P.blocked[frame]=2
end

local function valid_resref(ref)
  return type(ref)=='string' and #ref>=1 and #ref<=8
    and ref:match('^[A-Za-z0-9_]+$') ~= nil
end

local function logsample(tag, ref, ability)
  if P.sample_count >= P.max_samples then return end
  P.sample_count = P.sample_count+1
  if type(Infinity_Log)=='function' then
    pcall(Infinity_Log, '[BG_EET_RU_HIT_PILOT] '..tag..' #'
      ..tostring(P.sample_count)..' weapon='..tostring(ref or 'UNVERIFIED')
      ..' ability='..tostring(ability or 'UNVERIFIED')
      ..' journal_row=UNVERIFIED miss=UNVERIFIED')
  end
end

-- Callback runs at the relocated, native frame-established, pre-local-stack instruction.
-- Never retain the CItem userdata or an engine pointer beyond this synchronous call.
function BG_EET_RU_HIT_PILOT_Enter(frame, attacker, target, item, ability)
  if not P.installed or P.hold_reason then return end
  P.counters.entries = P.counters.entries+1
  if not valid_id(frame) or not valid_id(attacker) or not valid_id(target)
    or type(ability)~='number' or ability%1~=0
    or ability<0 or ability>65535 or item==nil then
    P.counters.invalid=P.counters.invalid+1;return
  end
  if P.blocked[frame] then
    P.counters.conflicts=P.counters.conflicts+1
    bounded_block(frame)
    return
  end
  if P.active[frame] then
    P.counters.conflicts=P.counters.conflicts+1
    P.active[frame]=nil
    bounded_block(frame)
    return
  end
  local n=0
  for _ in pairs(P.active) do n=n+1; if n>=P.max_active then
    P.counters.invalid=P.counters.invalid+1;return
  end end
  local ok,ref=pcall(function() return item.cResRef:get() end)
  if not ok or not valid_resref(ref) then
    P.counters.invalid=P.counters.invalid+1;return
  end
  -- ONLY plain strings/numbers are retained: never native CItem, projectile or message pointers.
  P.next_epoch=P.next_epoch+1
  P.active[frame]={weapon=ref:upper(),ability=ability,attacker=attacker,
                   target=target,epoch=P.next_epoch,messages=0}
end

-- Event belongs to the same native Hit stack frame; message type and visible row UNKNOWN.
-- Never edit the message or attach the weapon to a UI row without separate type verification.
function BG_EET_RU_HIT_PILOT_Message(frame, message)
  if not P.installed or P.hold_reason then return end
  P.counters.messages=P.counters.messages+1
  if not valid_id(frame) or not valid_id(message) then
    P.counters.unmatched=P.counters.unmatched+1;return
  end
  local ev=P.active[frame]
  if not ev or P.blocked[frame] or ev.messages>=8 then
    P.counters.unmatched=P.counters.unmatched+1;return
  end
  ev.messages=ev.messages+1
  -- The native message class and visible combatLog row are still unverified.
  logsample('SAME_FRAME_MESSAGE_UNTYPED',ev.weapon,ev.ability)
end

function BG_EET_RU_HIT_PILOT_Exit(frame)
  if not P.installed or P.hold_reason then return end
  P.counters.exits=P.counters.exits+1
  if not valid_id(frame) then
    P.counters.invalid=P.counters.invalid+1;return
  end
  if P.blocked[frame] then
    if P.blocked[frame]>1 then
      P.blocked[frame]=P.blocked[frame]-1
    else
      P.blocked[frame]=nil
    end
    return
  end
  P.active[frame]=nil;P.blocked[frame]=nil
end

local function exact(address, hex)
  if type(address)~='number' or type(EEex_ReadU8)~='function' then return false end
  local index=0
  for byte in hex:gmatch('%x%x') do
    local ok,got=pcall(EEex_ReadU8,address+index)
    if not ok or got ~= tonumber(byte,16) then return false end
    index=index+1
  end
  return true
end

function BG_EET_RU_HIT_PILOT_Preflight()
  if EEex_PtrSize~=8 or type(EEex_Label)~='function' then
    return false,'EEEX_X64_BINDINGS_REQUIRED'
  end
  local resolved,first=pcall(EEex_Label,'Hook-CGameSprite::Hit()-FirstCall')
  if not resolved or not valid_id(first) or first<0x10000 then return false,'FIRSTCALL_LABEL_MISSING' end
  local sites={
    capture=first-0x1E,           -- 0x39DA68, sub rsp,0x80, relocatable, before r8/r9 clobber
    message=first+0xDC5,         -- 0x39E84B, call AddMessage
    exit=first+0xF10,            -- 0x39E996, call C-string destructor before normal return
    first=first,                 -- 0x39DA86, owned by upstream EEex, NEVER patch
    forbidden=first-0x11,       -- 0x39DA75, RIP-relative LEA, relocation corruption hazard
  }
  if not exact(sites.capture,'4881ec80000000') then return false,'CAPTURE_BYTES_CHANGED_HOLD' end
  if not exact(sites.message,'e81064e6ff') then return false,'MESSAGE_BYTES_CHANGED_HOLD' end
  if not exact(sites.exit,'e865e40500') then return false,'EXIT_BYTES_CHANGED_HOLD' end
  -- E9 suggests a hook, but alone cannot authenticate the owner of the trampoline.
  -- Installed EEex source SHA and exact JIT owner must be proven separately.
  if not exact(sites.first,'e9') then return false,'EEEX_FIRSTCALL_NOT_ALREADY_PATCHED_HOLD' end
  if not exact(sites.forbidden,'488d15a1c92400') then return false,'OLD_RIP_RELATIVE_SITE_DRIFT_HOLD' end
  return true,sites
end

-- Future-only assembly prototype. This function MUST remain unreachable in released files
-- until independent native run-time, ABI, unwind, and partial-JIT-rollback proof exists.
function BG_EET_RU_HIT_PILOT_Start()
  if P.installed then return false,'ALREADY_INSTALLED' end
  if not (P.authorized_install and P.runtime_abi_verified
      and P.atomic_three_hook_install_verified) then
    return false,'NATIVE_JIT_INSTALL_BLOCKED_SOURCE_ONLY'
  end
  local ok,sites=BG_EET_RU_HIT_PILOT_Preflight()
  if not ok then return false,sites end
  -- Intentional HOLD: do not mutate executable memory from an unverified Lua source.
  -- A guarded future implementation must JIT all three hooks atomically, restore
  -- RCX/RDX/R8/R9/XMM0-5 and original call targets, and keep all text unchanged.
  return false,'RUNTIME_HOOK_IMPLEMENTATION_NOT_VERIFIED'
end