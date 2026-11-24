-- BG_EET_RU: source-only, fail-closed live-memory site inventory.
-- No JIT, no memory write, no game mutation. This file is not loaded by the game.
-- Evidence from the installed process is required: bytes from Baldur.exe alone do
-- not establish who owns an existing patched branch.
local G = {schema='BG_EET_RU_HIT_RUNTIME_INVENTORY_RO_V1', write_allowed=false}
BG_EET_RU_HIT_RUNTIME_INVENTORY_RO = G

local function valid_addr(x)
  return type(x)=='number' and x==x and x>0x10000 and x%1==0
end
local function read_bytes(addr, size)
  if not valid_addr(addr) or type(EEex_ReadU8)~='function' then return nil end
  local t={}
  for i=0,size-1 do
    local ok,value=pcall(EEex_ReadU8,addr+i)
    if not ok or type(value)~='number' or value%1~=0 or value<0 or value>255 then return nil end
    t[i+1]=value
  end
  return t
end
local function same(a,b)
  if not a or not b or #a~=#b then return false end
  for i=1,#a do if a[i]~=b[i] then return false end end
  return true
end
local function expected_hex(bytes,hex)
  local expected={}
  for h in hex:gmatch('%x%x') do expected[#expected+1]=tonumber(h,16) end
  return same(bytes,expected)
end
local function rel32(data)
  if not data or #data~=5 then return nil end
  local v=data[2]+data[3]*256+data[4]*65536+data[5]*16777216
  if v>=2147483648 then v=v-4294967296 end
  return v
end
local function result(code)
  return {status=code,install_allowed=false,game_writes=0,owner_verified=false,
    visible_combat_log_verified=false,miss_weapon_verified=false}
end
function BG_EET_RU_HIT_RUNTIME_INVENTORY_RO_Check()
  if EEex_PtrSize~=8 or type(EEex_Label)~='function' then return result('EEEX_X64_HOLD') end
  local ok,first=pcall(EEex_Label,'Hook-CGameSprite::Hit()-FirstCall')
  if not ok or not valid_addr(first) then return result('FIRSTCALL_LABEL_HOLD') end
  local rva_first=0x39DA86
  local base=first-rva_first
  if not valid_addr(base) then return result('MODULE_BASE_HOLD') end
  local sites={
    capture={first-0x1E,7,'4881ec80000000'},
    message={first+0xDC5,5,'e81064e6ff'},
    exit={first+0xF10,5,'e865e40500'},
    first={first,5,nil},
    forbidden={first-0x11,7,'488d15a1c92400'},
  }
  local one={}
  for name,site in pairs(sites) do
    local bytes=read_bytes(site[1],site[2])
    if not bytes then return result('SITE_MEMORY_READ_HOLD_'..name) end
    if site[3] and not expected_hex(bytes,site[3]) then
      return result('SITE_BYTES_CHANGED_HOLD_'..name)
    end
    one[name]=bytes
  end
  if one.first[1]~=0xE9 then return result('FIRSTCALL_NOT_JMP_HOLD') end
  local target_message=sites.message[1]+5+rel32(one.message)
  local target_exit=sites.exit[1]+5+rel32(one.exit)
  if target_message~=base+0x204C60 then return result('MESSAGE_CALL_TARGET_HOLD') end
  if target_exit~=base+0x3FCE00 then return result('EXIT_CALL_TARGET_HOLD') end
  local first_jump=sites.first[1]+5+rel32(one.first)
  if not valid_addr(first_jump) or first_jump==first then return result('FIRSTCALL_JMP_TARGET_HOLD') end
  -- A second read catches snapshots changed while they were collected.
  for name,site in pairs(sites) do
    if not same(one[name],read_bytes(site[1],site[2])) then
      return result('NON_ATOMIC_MEMORY_SNAPSHOT_HOLD_'..name)
    end
  end
  local out=result('SOURCE_SITES_MATCH_OWNER_UNPROVEN_HOLD')
  out.site_count=5
  out.capture_rva=0x39DA68
  out.message_rva=0x39E84B
  out.exit_rva=0x39E996
  out.first_rva=rva_first
  out.firstcall_is_jmp=true
  out.firstcall_jump_target=first_jump
  out.owner_verified=false -- E9 target alone never authenticates EEex trampoline ownership
  return out
end