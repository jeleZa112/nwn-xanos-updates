-- BGXAI R6: passive evidence classification for real R1/R2/R4 selected weapon changes.
-- SOURCE ONLY, not installed; read-only, no hooks / orders / EEex / globals / IO.
-- Observing selected APR under one loadout is NOT projected APR under another.
-- Even a matching actor, levels, raw buff fields and selected stats on two
-- snapshots cannot prove that all temporary / equip effects are the same.
local M = {version='BGXAI_WEAPON_SELECTED_VS_ALTERNATE_V1',installed=false}
local function integer(x,low,high)
 return type(x)=='number' and x==x and x%1==0 and x>=low and x<=high
end
local function resref(x)
 return type(x)=='string' and #x>=1 and #x<=8 and not x:find('[^%w_]')
end
local function hold(reason)
 return {schema=M.version,status='HOLD_UNVERIFIED_OBSERVATION',reason=reason,
  executable=false,weaponSwitchAuthorized=false,dispatchAuthorized=false,
  ordersSent=0,actionQueueCleared=false,currentActionPreserved=true}
end
local standardAPR={ [1]=1,[2]=2,[7]=1.5 }
M.decodeOnlyVerifiedRawAPR=function(n) return standardAPR[n] end
local function same(r4,r2,r1)
 if type(r4)~='table' or type(r2)~='table' or type(r1)~='table' then return false end
 if r4.schema~='BGXAI_WEAPON_ACTIVE_R4' or r4.type~='ACTIVE' or
    r2.schema~='BGXAI_WEAPON_SLOTS_RAW_R2' or r2.type~='SLOTS' or
    r1.type~='ACTION' or
    r4.status~='RAW_CURRENT_SELECTED_STATS_OBSERVED_NOT_COMPLETE_EFFECTS' then return false end
 if not integer(r4.seq,1,64) or r4.seq~=r2.seq or r4.seq~=r1.sequence or
    not integer(r4.actor,0,2147483647) or r4.actor~=r2.actor or r4.actor~=r1.actor or
    not integer(r4.partyIndex,0,5) or r4.partyIndex~=r2.partyIndex or
    r4.partyIndex~=r1.partyIndex or
    not integer(r4.selectedWeaponRaw,0,38) or
    r4.selectedWeaponRaw~=r2.selectedWeaponRaw or
    r4.selectedWeaponRaw~=r1.selectedWeaponRaw or
    not integer(r4.actionRaw,0,65535) or
    r4.actionRaw~=r2.actionRaw or r4.actionRaw~=r1.action then return false end
 if r4.presentCount~=68 or r4.missingCount~=0 or
    type(r4.statsRaw)~='table' or
    not integer(r4.statsRaw.m_nTHAC0,-50,100) or
    r4.statsRaw.m_nTHAC0~=r1.thac0Raw or
    r4.statsRaw.m_nNumberOfAttacks~=r1.aprRaw or
    not standardAPR[r1.aprRaw] then return false end
 for _,flag in ipairs({'allBuffsObserved','allEffectsObserved','alternateSlotAPRVerified',
  'manualOrderProven','epsQueueProven','weaponSwitchAuthorized','dispatchAuthorized'}) do
  if r4[flag]~=false then return false end
 end
 return true
end
local function slot_list(slots,name,base)
 if type(slots)~='table' or #slots~=4 then return false end
 for i=1,4 do
  local x=slots[i]
  if type(x)~='table' or x.index~=base+i-1 then return false end
  if x.resrefRaw~=nil and not resref(x.resrefRaw) then return false end
 end
 return true
end
local function resolve(r4,r2)
 local quick,ammo=r2.quickWeapons,r2.quivers
 if not slot_list(quick,'quick',35) or not slot_list(ammo,'ammo',11) then
  return nil,'SLOT_SHAPE_MISMATCH'
 end
 local idx=r4.selectedWeaponRaw
 if idx>=35 and idx<=38 then
  local e=quick[idx-34]
  if not resref(e.resrefRaw) then return nil,'SELECTED_QUICK_EMPTY' end
  return {selectedRef=e.resrefRaw,selection='CURRENT_SELECTED_QUICK_ITEM_RAW',
   selectedSlot=idx,launcherCandidate=nil,ammoRef=nil},nil
 end
 if idx>=11 and idx<=14 then
  local e=ammo[idx-10]
  if not resref(e.resrefRaw) or not integer(e.useCount1Raw,1,1000000) then
   return nil,'SELECTED_AMMO_EMPTY_OR_DEPLETED'
  end
  -- R2 does not identify the active launcher. Store ammo, never guess bow type.
  return {selectedRef=e.resrefRaw,selection='CURRENT_SELECTED_AMMO_LAUNCHER_UNPROVEN',
   selectedSlot=idx,launcherCandidate=nil,ammoRef=e.resrefRaw},nil
 end
 return nil,'SELECTED_SLOT_UNSUPPORTED'
end
local function snapshot_key(v)
 return tostring(v.actor)..':'..tostring(v.partyIndex)
end
local function copy(s)
 local out={};if type(s)=='table' then for k,v in pairs(s) do out[k]=v end end
 return out
end
function M.observe(r4,r2,r1,previous)
 if not same(r4,r2,r1) then return hold('R1_R2_R4_NOT_MATCHED_SAME_ACTION'),nil end
 local selection,why=resolve(r4,r2)
 if not selection then return hold(why),nil end
 local key=snapshot_key(r4)
 local prior=type(previous)=='table' and previous or nil
 local canReuse=prior~=nil and prior.version==M.version and
  prior.actorKey==key and integer(prior.lastSeq,1,64) and
  prior.lastSeq+1==r4.seq and type(prior.history)=='table'
 local history=canReuse and copy(prior.history) or {}
 local entry={selectedRef=selection.selectedRef,selectedSlot=selection.selectedSlot,
  selectedAPRRaw=r1.aprRaw,selectedAPRDecoded=standardAPR[r1.aprRaw],
  thac0Raw=r1.thac0Raw,actionRaw=r4.actionRaw,
  sequence=r4.seq,selection=selection.selection,
  currentActionOnlyAtRecordedEvent=true,contextExhaustivelyVerified=false}
 -- 4 weapon quickslots + 4 ammo selected references, bounded by key.
 history[selection.selectedRef]=entry
 -- Fixed cap: older selected references are evicted; never store full action log.
 local count=0
 for _ in pairs(history) do count=count+1 end
 while count>8 do
  local oldest,oldestSeq=nil,1000000
  for name,value in pairs(history) do
   if type(value)=='table' and integer(value.sequence,1,64) and value.sequence<oldestSeq then
    oldest=name;oldestSeq=value.sequence
   end
  end
  if oldest==nil then history={} break end -- untrusted prior state; drop everything.
  history[oldest]=nil;count=count-1
 end
 local next={version=M.version,actorKey=key,lastSeq=r4.seq,history=history}
 local quick={}
 for i=1,4 do
  local w=r2.quickWeapons[i]
  local h=w.resrefRaw and history[w.resrefRaw] or nil
  local currentlySelected=r4.selectedWeaponRaw==w.index
  local proof='UNOBSERVED_ALTERNATE_NO_EFFECTIVE_APR'
  if currentlySelected then proof='SELECTED_EFFECTIVE_APR_OBSERVED_THIS_ACTION'
  elseif h then proof='HISTORICAL_SELECTED_APR_NOT_CURRENT_PROJECTION' end
  quick[i]={slot=w.index,itemResRef=w.resrefRaw,
   evidenceClass=proof,selectedNow=currentlySelected,
   -- Historical APR is shown separately, never copied into a current projection.
   historicalSelectedAPR=h and h.selectedAPRDecoded or nil,
   effectiveAPRForUnselected=nil,activeBuffsFullyObserved=false,
   perSlotEffectiveTHAC0Verified=false}
 end
 local out={schema=M.version,status='SELECTED_ONLY_EFFECTIVE_APR_OBSERVED_PRIORITY_HOLD',
  actor=r4.actor,partyIndex=r4.partyIndex,sequence=r4.seq,
  currentSelected=entry,quickslots=quick,
  selectedAPRDecoded=entry.selectedAPRDecoded,
  targetStatsObserved=false,buffsFullyObserved=false,
  alternateSlotAPRVerified=false,offhandRateVerified=false,
  manualOrderProven=false,epsQueueProven=false,
  executable=false,weaponSwitchAuthorized=false,dispatchAuthorized=false,
  ordersSent=0,actionQueueCleared=false,currentActionPreserved=true}
 return out,next
end
return M
