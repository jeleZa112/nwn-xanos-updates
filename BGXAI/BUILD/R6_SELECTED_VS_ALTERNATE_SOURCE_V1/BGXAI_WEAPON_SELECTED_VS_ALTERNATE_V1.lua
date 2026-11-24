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
  ordersSent=0,actionQueueCleared=false,currentActionPreserved=true,
  alternateSlotAPRVerified=false,manualOrderProven=false,epsQueueProven=false}
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
local function legacy_r2_gear_key(r2)
 -- Legacy R1/R2/R4 reported equipment without a verified offhand or full
 -- effect list. Conservatively invalidate past observations whenever any
 -- available raw item field changes; this never authorizes an engine action.
 local t={}
 for _,arr in ipairs({r2.quickWeapons,r2.quivers}) do
  for i=1,4 do
   local v=arr[i]
   for _,field in ipairs({'index','resrefRaw','access',
       'useCount1Raw','useCount2Raw','useCount3Raw','flagsRaw'}) do
    t[#t+1]=field..'='..tostring(v[field]==nil and '-' or v[field])
   end
  end
 end
 return table.concat(t,'|')
end
function M.observe(r4,r2,r1,previous)
 if not same(r4,r2,r1) then return hold('R1_R2_R4_NOT_MATCHED_SAME_ACTION'),nil end
 local selection,why=resolve(r4,r2)
 if not selection then return hold(why),nil end
 local key=snapshot_key(r4)
 local gearKey=legacy_r2_gear_key(r2)
 local prior=type(previous)=='table' and previous or nil
 local canReuse=prior~=nil and prior.version==M.version and
  prior.actorKey==key and prior.gearKey==gearKey and
  integer(prior.lastSeq,1,64) and
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
 local next={version=M.version,actorKey=key,lastSeq=r4.seq,
  gearKey=gearKey,history=history}
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
  ordersSent=0,actionQueueCleared=false,currentActionPreserved=true,
  alternateSlotAPRVerified=false,manualOrderProven=false,epsQueueProven=false}
 return out,next
end
-- R27 (the existing single-callback observer) has its own schema. This
-- adapter shares R6's evidence vocabulary; it does NOT promote any historical
-- measurement to effective *current* alternative-slot APR. R27's double-read
-- verifies raw item stability only, never a complete effects / EPS snapshot.
local function r27slot(a, i, base)
 if type(a)~='table' or type(a[i])~='table' then return nil end
 local v=a[i]
 if v.slot~=base+i-1 then return nil end
 local ref=v.resrefRaw
 if ref~=nil and not resref(ref) then return nil end
 for _,key in ipairs({'useCount1Raw','useCount2Raw','useCount3Raw'}) do
  local n=v[key]
  if n~=nil and not integer(n,0,65535) then return nil end
 end
 return v
end
local function r27array(a,base)
 if type(a)~='table' then return false end
 local seen=0
 for k in pairs(a) do
  if not integer(k,1,4) then return false end
  seen=seen+1
 end
 if seen~=4 then return false end
 for i=1,4 do if not r27slot(a,i,base) then return false end end
 return true
end
local function r27key(v)
 -- Each raw item identity and charge state participates in cache freshness.
 -- This is *only* a raw equipment signature, not a cryptographic digest or
 -- proof that invisible equipped effects, buffs, spells or a manual order stayed unchanged.
 local t={}
 for _,arr in ipairs({v.quickWeaponsRaw,v.quiversRaw}) do
  for i=1,4 do
   local x=arr[i]
   t[#t+1]=table.concat({tostring(x.slot),x.resrefRaw or '-',
     tostring(x.useCount1Raw or '-'),tostring(x.useCount2Raw or '-'),
     tostring(x.useCount3Raw or '-')},'/')
  end
 end
 local h=v.offhandRaw[1]
 t[#t+1]=table.concat({'9',h.resrefRaw or '-',
  tostring(h.useCount1Raw or '-'),tostring(h.useCount2Raw or '-'),
  tostring(h.useCount3Raw or '-')},'/')
 t[#t+1]='ABILITY:'..tostring(v.selectedAbilityRaw)
 return table.concat(t,'|')
end
local function r27valid(v)
 if type(v)~='table' or
   v.schema~='BGXAI_R27_SINGLE_CALLBACK_SELECTED_RO_V1' or
   v.status~='CURRENT_SELECTED_SAME_CALLBACK_SOURCE_CANDIDATE' or
   not integer(v.seq,1,64) or not integer(v.actor,1,2147483647) or
   not integer(v.partyIndex,0,5) or
   not integer(v.actionRaw,0,65535) or
   not integer(v.selectedWeaponRaw,11,38) or
   not integer(v.selectedAbilityRaw,0,31) or
   not integer(v.selectedAprKeyRaw,0,10) or
   not standardAPR[v.selectedAprKeyRaw] or
   v.rawInventoryDoubleReadConsistent~=true or
   v.sameLuaListenerInvocation~=true or
   v.nativeEventTokenAuthenticated~=false or
   v.engineSessionVerified~=false or
   v.alternativeAPRVerified~=false or
   v.launcherAmmoPairVerified~=false or
   v.completeActiveEffectsVerified~=false or
   v.epsManualQueueVerified~=false or
   v.ordersSent~=0 or v.localsWritten~=0 or
   v.dispatchAuthorized~=false or v.weaponSwitchAuthorized~=false or
   v.readOnly~=true then return false end
 if v.selectedWeaponRaw>14 and v.selectedWeaponRaw<35 then return false end
 if not r27array(v.quickWeaponsRaw,35) or
   not r27array(v.quiversRaw,11) or
   type(v.offhandRaw)~='table' or
   next(v.offhandRaw)==nil or next(v.offhandRaw,1)~=nil or
   not r27slot(v.offhandRaw,1,9) then return false end
 local stats=v.selectedStatsRaw
 if type(stats)~='table' or
   stats.m_nNumberOfAttacks~=v.selectedAprKeyRaw or
   not integer(stats.m_nTHAC0,-50,100) then return false end
 -- The record must actually describe a selected nonempty item. If ammo has
 -- depleted while queued, this does not certify a usable attack.
 local index=v.selectedWeaponRaw
 local selected=index>=35 and v.quickWeaponsRaw[index-34] or v.quiversRaw[index-10]
 if not selected or not resref(selected.resrefRaw) then return false end
 if index<=14 and not integer(selected.useCount1Raw,1,65535) then return false end
 return true
end
local function bounded_r27_history(map,low,high,seq)
 if type(map)~='table' then return false end
 local count=0
 for index,h in pairs(map) do
  count=count+1
  if count>4 or not integer(index,low,high) or type(h)~='table' or
    h.slot~=index or not resref(h.resref) or
    not integer(h.ability,0,31) or
    not integer(h.aprKey,0,10) or
    standardAPR[h.aprKey]~=h.aprAtSelection or
    not integer(h.thac0AtSelection,-50,100) or
    not integer(h.sequence,1,64) or h.sequence>seq or
    h.isHistoricalSelectedOnly~=true or
    h.activeEffectsFullyVerified~=false or
    h.engineLauncherVerified~=false or
    h.stableManualEPSQueueVerified~=false then return false end
 end
 return true
end
local function same_r27_history(state, v, gearKey)
 return type(state)=='table' and state.version==M.version and
   state.source=='R27_DOUBLE_READ_RAW' and
   state.actor==v.actor and state.partyIndex==v.partyIndex and
   integer(state.lastSeq,1,64) and state.lastSeq+1==v.seq and
   state.gearKey==gearKey and
   bounded_r27_history(state.slots,35,38,state.lastSeq) and
   bounded_r27_history(state.ammo,11,14,state.lastSeq)
end
function M.observe_r27(v, previous)
 if not r27valid(v) then
  return hold('R27_RAW_DOUBLE_READ_EVIDENCE_INCOMPLETE'),nil end
 local gear=r27key(v)
 local carry=same_r27_history(previous,v,gear)
 -- Only a raw-signature match permits *historical* carryover. Never copy
 -- selected APR into w.apr or V3's completeEffectiveStats evidence.
 local past=carry and copy(previous.slots) or {}
 local ammo=carry and copy(previous.ammo) or {}
 local index=v.selectedWeaponRaw
 local isWeapon=index>=35
 local entrySlot=isWeapon and v.quickWeaponsRaw[index-34] or v.quiversRaw[index-10]
 local selectedRef=entrySlot.resrefRaw
 local entry={slot=index,resref=selectedRef,ability=v.selectedAbilityRaw,
   aprKey=v.selectedAprKeyRaw,aprAtSelection=standardAPR[v.selectedAprKeyRaw],
   thac0AtSelection=v.selectedStatsRaw.m_nTHAC0,sequence=v.seq,
   isHistoricalSelectedOnly=true,activeEffectsFullyVerified=false,
   engineLauncherVerified=false,stableManualEPSQueueVerified=false}
 if isWeapon then past[index]=entry else ammo[index]=entry end
 local slots={}
 for i=1,4 do
  local w=v.quickWeaponsRaw[i]
  local h=past[w.slot]
  local validPast=type(h)=='table' and h.slot==w.slot and h.resref==w.resrefRaw
  local currentlySelected=index==w.slot
  slots[i]={slot=w.slot,itemResRef=w.resrefRaw,
   evidenceClass=currentlySelected and 'SELECTED_EFFECTIVE_APR_OBSERVED_THIS_ACTION' or
     (validPast and 'HISTORICAL_SELECTED_APR_NOT_CURRENT_PROJECTION' or
       'UNOBSERVED_ALTERNATE_NO_EFFECTIVE_APR'),
   historicalSelectedAPR=validPast and h.aprAtSelection or nil,
   effectiveAPRForUnselected=nil,perSlotEffectiveTHAC0Verified=false,
   activeBuffsFullyObserved=false}
 end
 local out={schema=M.version,status='R27_SELECTED_RAW_APR_HISTORY_ONLY',
  source='R27_DOUBLE_READ_RAW',sequence=v.seq,selectedSlot=index,
  selectedResRef=selectedRef,selectedAPRDecoded=entry.aprAtSelection,
  selectedStatsAtThisEvent=v.selectedStatsRaw,
  selectedIsAmmoNotAuthenticatedLauncher=not isWeapon,
  quickslots=slots,
  priorRawEquipmentSignatureMatched=carry,
  historicalMeasurementsNeverCurrentAlternate=true,
  activeBuffsFullyObserved=false,alternateSlotAPRVerified=false,
  manualOrderProven=false,epsQueueProven=false,
  executable=false,weaponSwitchAuthorized=false,dispatchAuthorized=false,
  ordersSent=0,actionQueueCleared=false,currentActionPreserved=true,
  alternateSlotAPRVerified=false,manualOrderProven=false,epsQueueProven=false}
 local nextState={version=M.version,source='R27_DOUBLE_READ_RAW',actor=v.actor,
  partyIndex=v.partyIndex,lastSeq=v.seq,gearKey=gear,slots=past,ammo=ammo}
 return out,nextState
end
return M
