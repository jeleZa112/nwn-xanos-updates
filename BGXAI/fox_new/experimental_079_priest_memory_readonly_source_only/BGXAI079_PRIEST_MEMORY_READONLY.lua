-- BGXAI079 SOURCE ONLY: read priest memorization via injected EEex reader.
-- Based on Bubb EEex public modder example, WITHOUT claiming tested v1.1.7 runtime.
-- This module does not register hooks, set locals, cast, attack or modify EPS.
local M={version='0.3.46-079-PRIEST-MEMORY-READONLY',installed=false}
local function unknown(why)
 return {status='UNVERIFIED',reason=why,known_in_memory=false,
         unused_memorizations=nil,castable_now_verified=false,usable_now=nil,
         orders_sent=0,locals_written=0}
end
local function safe(fn) local ok,value=pcall(fn);if ok then return true,value end; return false,nil end
-- `api` functions are injected only for testing or a separately reviewed
-- adapter; NEVER assume all old engine-x86 functions exist on modern EEex.
function M.scan(sprite,wanted_resref,api)
 if type(wanted_resref)~='string' or not wanted_resref:match('^[A-Z0-9_]+$')
   or #wanted_resref>8 then return unknown('WANTED_RESREF_NOT_VERIFIED') end
 if sprite==nil or type(api)~='table'
   or type(api.iterate_list)~='function'
   or type(api.resref_of)~='function'
   or type(api.bit0_unset)~='function' then return unknown('EEEX_READER_UNAVAILABLE') end
 local okMem, mem=safe(function()return sprite.m_memorizedSpellsPriest end)
 if not okMem or mem==nil then return unknown('PRIEST_MEMORIZED_LIST_UNKNOWN') end
 local getReference
 local okRef=pcall(function() getReference=mem.getReference end)
 if not okRef or type(getReference)~='function' then return unknown('PRIEST_LIST_METHOD_UNAVAILABLE') end
 local matched=0
 local unused=0
 local visited=0
 local invalid=false
 for i=0,6 do
  local okLevel,level=safe(function()return mem:getReference(i) end)
  if not okLevel or level==nil then return unknown('SPELL_LEVEL_POINTER_MISSING') end
  local okIter=pcall(function()
   api.iterate_list(level,function(entry)
    visited=visited+1
    if visited>512 then error('PRIEST_SPELL_LIST_TOO_LONG') end
    if type(entry.m_flags)~='number' or entry.m_flags~=math.floor(entry.m_flags) or entry.m_flags<0 then
      invalid=true;return
    end
    local okRes,res=safe(function()return api.resref_of(entry) end)
    local okBit,spent=safe(function()return api.bit0_unset(entry.m_flags) end)
    if not okRes or not okBit or type(res)~='string'
      or type(spent)~='boolean' then invalid=true;return end
    if res:upper()==wanted_resref then
      matched=matched+1
      if not spent then unused=unused+1 end
    end
   end)
  end)
  if not okIter or invalid then return unknown('PRIEST_LIST_READ_INCOMPLETE') end
 end
 -- Even an *unused* memorized priest spell may not be castable because of
 -- dual-class lock, silence, aura, spell failure, EPS busy queue, etc.
 return {status='READ_ONLY_MEMORIZATION_OBSERVED',reason='CASTABILITY_NOT_PROVEN',
    known_in_memory=matched>0,unused_memorizations=unused,
    matched_memorizations=matched,visited=visited,
    castable_now_verified=false,usable_now=nil,orders_sent=0,locals_written=0}
end
return M
