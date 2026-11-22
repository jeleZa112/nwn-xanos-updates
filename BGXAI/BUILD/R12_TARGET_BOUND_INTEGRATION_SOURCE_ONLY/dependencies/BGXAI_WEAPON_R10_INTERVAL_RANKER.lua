-- BGXAI R10: fail-closed physical-damage forecast intervals (not a native engine observer).
-- SOURCE ONLY. All input evidence, even if marked "verified", is UNAUTHENTICATED here.
-- Never issue commands, change equipment, call EEex, mutate scenes or clear action queues.
-- Models only noncritical physical damage. Poison, spells, effects, critical hits, immunities
-- and resistances must be represented by cautious [0, 1] factors, not silently assumed.
local M={version='BGXAI_WEAPON_R10_INTERVAL_RANKER_V1',installed=false}
local function finite(x,lo,hi)
 return type(x)=='number' and x==x and x~=math.huge and x~=-math.huge and x>=lo and x<=hi
end
local function integer(x,lo,hi)
 return finite(x,lo,hi) and x%1==0
end
local function ident(x)
 return type(x)=='string' and #x>0 and #x<=128 and not x:find('[^%w_%.:%-]')
end
local function ref(x)
 return type(x)=='string' and #x>=1 and #x<=8 and not x:find('[^%w_]')
end
local function output(status,reason,extra)
 local o={schema=M.version,status=status,reason=reason,
  installed=false,executable=false,weaponSwitchAuthorized=false,dispatchAuthorized=false,
  ordersSent=0,actionQueueCleared=false,currentActionPreserved=true,
  liveAlternateAPRVerified=false,nativeEvidenceAuthenticated=false,
  manualOrderProven=false,epsQueueProven=false,
  modeledScope='NONCRITICAL_PHYSICAL_DAMAGE_ONLY_NO_ONHIT_EFFECTS',
  rankingAuthority='UNAUTHENTICATED_FORECAST_NEVER_ENGINE_FACT'}
 if type(extra)=='table' then for k,v in pairs(extra) do o[k]=v end end
 return o
end
local FIELDS={'sessionId','snapshotId','actor','partyIndex','sequence',
 'equipmentFingerprint','activeStatsFingerprint','buffFingerprint','effectFingerprint',
 'proficiencyFingerprint','targetFingerprint'}
local function valid_frame(f)
 if type(f)~='table' or not ident(f.sessionId) or not ident(f.snapshotId) or
  not integer(f.actor,1,2147483647) or not integer(f.partyIndex,0,5) or
  not integer(f.sequence,1,64) or not integer(f.selectedSlot,35,38) or
  not ref(f.selectedRef) or not ident(f.targetFingerprint) then return false end
 for _,k in ipairs({'equipmentFingerprint','activeStatsFingerprint','buffFingerprint',
  'effectFingerprint','proficiencyFingerprint','targetFingerprint'}) do
  if not ident(f[k]) then return false end
 end
 return true
end
local function same_frame(a,b)
 if type(a)~='table' or type(b)~='table' then return false end
 for _,k in ipairs(FIELDS) do if a[k]~=b[k] then return false end end
 return a.selectedSlot==b.selectedSlot and a.selectedRef==b.selectedRef
end
local function valid_ledger(f,l)
 if type(l)~='table' or l.schema~='BGXAI_WEAPON_R9_CONTEXT_LEDGER_V1' or
  l.status~='PASSIVE_LEDGER_ONLY' or l.nativeEvidenceAuthenticated~=false or
  l.liveAlternateAPRVerified~=false or l.weaponSwitchAuthorized~=false or
  l.dispatchAuthorized~=false or l.manualOrderProven~=false or
  l.epsQueueProven~=false or l.selectedQuickslotObserved~=true or
  l.launcherIdentified~=false or l.selectedSlot~=f.selectedSlot or
  l.selectedRef~=f.selectedRef or type(l.rows)~='table' or #l.rows~=4 or
  type(l.next)~='table' then return false end
 local next=l.next
 if next.sessionId~=f.sessionId or next.actor~=f.actor or
  next.partyIndex~=f.partyIndex or next.sequence~=f.sequence then return false end
 -- This verifies linkage only, NOT native authenticity. R9's actual key format.
 local expected=table.concat({f.sessionId,tostring(f.actor),tostring(f.partyIndex),
  f.equipmentFingerprint,f.activeStatsFingerprint,f.buffFingerprint,
  f.effectFingerprint,f.proficiencyFingerprint},'|')
 if next.context~=expected then return false end
 local present=0
 for i=1,4 do
  local q=l.rows[i]
  if type(q)~='table' or q.slot~=i+34 or q.currentAlternateAPR~=nil or
    (q.itemRef~=nil and not ref(q.itemRef)) then return false end
  if q.slot==f.selectedSlot then
   present=present+1
   if q.itemRef~=f.selectedRef or
     q.evidence~='SELECTED_EVENT_APR_OBSERVED_R6_UNAUTHENTICATED' or
     not finite(q.currentSelectedAPR,0.5,20) or
     q.currentSelectedAPR~=l.selectedEventAPR then return false end
  elseif q.currentSelectedAPR~=nil then return false end
 end
 return present==1
end
local function bounds(b,lo,hi)
 return type(b)=='table' and finite(b.lo,lo,hi) and finite(b.hi,lo,hi) and
  b.lo<=b.hi
end
local function hit_probability(thac0,ac)
 -- Natural 1 always misses; natural 20 always hits. Integer forecast only.
 -- No modified critical range, concealment, mirror image or on-hit effects.
 local needed=thac0-ac
 local first=math.max(2,math.ceil(needed))
 local regular=math.max(0,20-first)
 return (1+math.min(18,regular))/20
end
M.hitProbability=hit_probability
local function valid_slot(s,idx,frame,ledgerrow)
 if type(s)~='table' or s.slot~=idx or (s.occupied~=true and s.occupied~=false) then
  return false,'SLOT_SHAPE_INVALID' end
 if s.occupied==false then
  if s.itemRef~=nil or ledgerrow.itemRef~=nil or s.apr~=nil or s.thac0~=nil or
    s.targetAC~=nil or s.damage~=nil then return false,'EMPTY_SLOT_HAS_MODEL' end
  return true
 end
 if not ref(s.itemRef) or s.itemRef~=ledgerrow.itemRef then
  return false,'LOADOUT_DIFFERS_FROM_R9' end
 if s.modelSource~='ITM_2DA_CONTEXTUAL_FORECAST_NOT_NATIVE' or
  s.effectiveAPRNativeVerified~=false or s.effectiveTHAC0NativeVerified~=false or
  s.forecastNotEngineObservation~=true then
  return false,'FORECAST_PROVENANCE_INCOMPLETE' end
 if not bounds(s.apr,0.5,20) or not bounds(s.thac0,-60,100) or
  not bounds(s.targetAC,-60,100) or not bounds(s.damage,0,100000) or
  not bounds(s.damageThrough,0,1) or not bounds(s.contact,0,1) then
  return false,'NUMERIC_BOUNDS_INVALID' end
 -- Integer THAC0 / AC forecasts in the standard d20 system.
 if s.thac0.lo%1~=0 or s.thac0.hi%1~=0 or
  s.targetAC.lo%1~=0 or s.targetAC.hi%1~=0 then
  return false,'THAC0_AC_NOT_INTEGER' end
 if s.apr.lo* s.damage.hi* s.damageThrough.hi* s.contact.hi>2e6 then
  return false,'FORECAST_MAGNITUDE_UNSAFE' end
 if s.itemRef==frame.selectedRef and s.slot==frame.selectedSlot and
  (s.selectedAPRAnchor~=ledgerrow.currentSelectedAPR or
   s.apr.lo>ledgerrow.currentSelectedAPR or s.apr.hi<ledgerrow.currentSelectedAPR) then
  return false,'SELECTED_APR_ANCHOR_CONTRADICTION' end
 if s.slot~=frame.selectedSlot and s.selectedAPRAnchor~=nil then
  return false,'HISTORICAL_AS_CURRENT_APR_FORBIDDEN' end
 return true
end
function M.assess(frame,ledger,model)
 if not valid_frame(frame) then return output('HOLD','FRAME_INVALID') end
 if not valid_ledger(frame,ledger) then return output('HOLD','R9_LEDGER_INVALID_OR_STALE') end
 if type(model)~='table' or not same_frame(frame,model.frame) or
  model.source~='STATIC_FORECAST_UNAUTHENTICATED' or
  model.nativeProof~=false or model.weaponSwitchAuthorized~=false or
  type(model.slots)~='table' or #model.slots~=4 then
  return output('HOLD','MODEL_FRAME_OR_PROVENANCE_INVALID') end
 local rows,selected=nil,nil
 rows={}
 for i=1,4 do
  local s=model.slots[i]
  local valid,err=valid_slot(s,34+i,frame,ledger.rows[i])
  if not valid then return output('HOLD',err,{blockedSlot=34+i}) end
  if s.occupied then
   -- Higher THAC0 and lower target AC are harder; never reverse bounds.
   local pLo=hit_probability(s.thac0.hi,s.targetAC.lo)
   local pHi=hit_probability(s.thac0.lo,s.targetAC.hi)
   local low=s.apr.lo*pLo*s.damage.lo*s.damageThrough.lo*s.contact.lo
   local high=s.apr.hi*pHi*s.damage.hi*s.damageThrough.hi*s.contact.hi
   if not finite(low,0,2e6) or not finite(high,0,2e6) or low>high then
    return output('HOLD','INTERVAL_COMPUTATION_INVALID',{blockedSlot=s.slot}) end
   local row={slot=s.slot,itemRef=s.itemRef,selected=(s.slot==frame.selectedSlot),
     minPhysicalDamagePerRound=low,maxPhysicalDamagePerRound=high,
     hitChanceMin=pLo,hitChanceMax=pHi,aprMin=s.apr.lo,aprMax=s.apr.hi,
     evidence='CONSERVATIVE_STATIC_FORECAST_NOT_MEASURED_ALTERNATE_APR'}
   rows[#rows+1]=row
   if row.selected then selected=row end
  end
 end
 if selected==nil then return output('HOLD','SELECTED_SLOT_NOT_OCCUPIED') end
 local dominance=nil
 for _,candidate in ipairs(rows) do
  local better=true
  for _,other in ipairs(rows) do
   if other.slot~=candidate.slot and candidate.minPhysicalDamagePerRound<=other.maxPhysicalDamagePerRound then
    better=false;break
   end
  end
  if better then dominance=candidate.slot;break end
 end
 local overlapping=dominance==nil
 return output('INTERVAL_FORECAST_ONLY',overlapping and 'RANGES_OVERLAP_NO_STABLE_PREFERENCE' or
  'MODEL_ONLY_DOMINANCE_DISPATCH_BLOCKED',{
  rows=rows,modelDominantSlot=dominance,selectedSlot=frame.selectedSlot,
  currentSelectedAprObservedOnlyAtR9Event=ledger.selectedEventAPR,
  targetFingerprint=frame.targetFingerprint,unmodeledHazards={
    'CRITICAL_HITS','ON_HIT_STATUS','MAGICAL_EFFECTS','TARGET_PROTECTION_STATE',
    'EXACT_CURRENT_ALTERNATE_APR','EPS_OR_MANUAL_ACTION_QUEUE'},
  mayRecommendWeaponSwitch=false,rankedNative=false})
end
return M
