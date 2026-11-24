-- BG_EET_RU / native same-Hit observer pilot / SOURCE ONLY / not an installable release
-- Based on pinned Baldur.exe SHA fc821a4806a0305b84fd85f1aad2bd472c8db642ed34b4494ae62351cae1c580
-- Native JIT code is deliberately *not armed*. Game UI, rolls, APR, ammo and damage unchanged.
-- Before activation, review Win64 ABI, EEex JIT, cross-thread Lua state, unwind and transactional rollback.
-- CRITICAL: old suggested capture site FirstCall-0x11 is RIP-relative LEA. DO NOT HOOK IT.
-- Replacement capture site FirstCall-0x1E is relocatable `sub rsp, 0x80`.

local P = {
  schema = 'BG_EET_RU_SAME_HIT_NATIVE_PILOT_SOURCE_ONLY_V1',
  authorized_install = false,              -- only guarded installer may set, after typed consent
  runtime_abi_verified = false,             -- remains false until independent live ABI verification
  atomic_three_hook_install_verified = false, -- EEex JIT hooks are not a rollback transaction
  installed = false,
  max_active = 128,
  max_samples = 64,
  next_epoch = 0,
  active = {},
  blocked = {},
  sample_count = 0,
  counters = {entries=0, invalid=0, conflicts=0, messages=0, unmatched=0, exits=0},
}
BG_EET_RU_HIT_PILOT = P

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
  if not P.installed then return end
  P.counters.entries = P.counters.entries+1
  if type(frame)~='number' or frame<=0 or frame%1~=0
    or type(attacker)~='number' or attacker<=0 or attacker%1~=0
    or type(target)~='number' or target<=0 or target%1~=0
    or type(ability)~='number' or ability%1~=0
    or ability<0 or ability>65535 or item==nil then
    P.counters.invalid=P.counters.invalid+1;return
  end
  if P.active[frame] or P.blocked[frame] then
    P.counters.conflicts=P.counters.conflicts+1
    P.active[frame]=nil;P.blocked[frame]=true
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
  if not P.installed then return end
  P.counters.messages=P.counters.messages+1
  local ev=P.active[frame]
  if not ev or P.blocked[frame] or ev.messages>=8 or type(message)~='number' or message<=0 then
    P.counters.unmatched=P.counters.unmatched+1;return
  end
  ev.messages=ev.messages+1
  logsample('SAME_FRAME_MESSAGE_UNTYPED',ev.weapon,ev.ability)
end

function BG_EET_RU_HIT_PILOT_Exit(frame)
  if not P.installed then return end
  P.counters.exits=P.counters.exits+1
  P.active[frame]=nil;P.blocked[frame]=nil
end

local function exact(address, hex)
  if type(address)~='number' or type(EEex_ReadU8)~='function' then return false end
  local index=0
  for byte in hex:gmatch('%x%x') do
    if EEex_ReadU8(address+index) ~= tonumber(byte,16) then return false end
    index=index+1
  end
  return true
end

function BG_EET_RU_HIT_PILOT_Preflight()
  if EEex_PtrSize~=8 or type(EEex_Label)~='function' then
    return false,'EEEX_X64_BINDINGS_REQUIRED'
  end
  local first=EEex_Label('Hook-CGameSprite::Hit()-FirstCall')
  if type(first)~='number' then return false,'FIRSTCALL_LABEL_MISSING' end
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
  -- Upstream EEex HookAfterCall owns this exact call after EEex_Sprite_Patch initializes.
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