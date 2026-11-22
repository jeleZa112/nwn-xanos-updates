-- BGXAI R9: conservative cross-event selected-APR ledger.
-- SOURCE ONLY, offline. Does not access engine, hook, files, globals or issue orders.
-- Input R6 is a prior checked observation, NOT an authenticated native reading.
-- Never converts historic selected APR into current alternate-slot APR.
local M={version='BGXAI_WEAPON_R9_CONTEXT_LEDGER_V1',installed=false}
local function ident(x) return type(x)=='string' and #x>0 and #x<=128 and not x:find('[^%w_%.:%-]') end
local function integer(x,lo,hi) return type(x)=='number' and x==x and x%1==0 and x>=lo and x<=hi end
local function apr(x) return type(x)=='number' and x==x and x~=math.huge and x~=-math.huge and x>=0.5 and x<=20 end
local function result(status,reason,next,extra)
 local r={schema=M.version,status=status,reason=reason,next=next,
 executable=false,dispatchAuthorized=false,weaponSwitchAuthorized=false,
 currentActionPreserved=true,actionQueueCleared=false,ordersSent=0,
 liveAlternateAPRVerified=false,nativeEvidenceAuthenticated=false,
 manualOrderProven=false,epsQueueProven=false,installed=false}
 if type(extra)=='table' then for k,v in pairs(extra) do r[k]=v end end
 return r
end
local fields={'equipmentFingerprint','activeStatsFingerprint','buffFingerprint','effectFingerprint','proficiencyFingerprint'}
local function context(f)
 if type(f)~='table' or not ident(f.sessionId) or not ident(f.snapshotId) or
    not integer(f.actor,1,2147483647) or not integer(f.partyIndex,0,5) or
    not integer(f.sequence,1,64) then return nil end
 local t={f.sessionId,tostring(f.actor),tostring(f.partyIndex)}
 for _,k in ipairs(fields) do if not ident(f[k]) then return nil end;t[#t+1]=f[k] end
 return table.concat(t,'|')
end
local function safeR6(r,f)
 if type(r)~='table' or r.schema~='BGXAI_WEAPON_SELECTED_VS_ALTERNATE_V1' or
  r.status~='SELECTED_ONLY_EFFECTIVE_APR_OBSERVED_PRIORITY_HOLD' or
  r.actor~=f.actor or r.partyIndex~=f.partyIndex or r.sequence~=f.sequence or
  r.weaponSwitchAuthorized~=false or r.dispatchAuthorized~=false or
  r.alternateSlotAPRVerified~=false or r.targetStatsObserved~=false or
  r.epsQueueProven~=false or r.manualOrderProven~=false or
  type(r.currentSelected)~='table' or type(r.quickslots)~='table' or #r.quickslots~=4 then return false end
 local c=r.currentSelected
 if c.sequence~=f.sequence or c.selectedSlot~=f.selectedSlot or
  c.selectedRef~=f.selectedRef or c.selectedAPRDecoded~=r.selectedAPRDecoded or
  not apr(c.selectedAPRDecoded) or c.currentActionOnlyAtRecordedEvent~=true or
  c.contextExhaustivelyVerified~=false then return false end
 if not integer(c.selectedSlot,11,14) and not integer(c.selectedSlot,35,38) then return false end
 for i=1,4 do
  local q=r.quickslots[i]
  if type(q)~='table' or q.slot~=i+34 or
    q.effectiveAPRForUnselected~=nil or q.activeBuffsFullyObserved~=false or
    q.perSlotEffectiveTHAC0Verified~=false then return false end
  if integer(c.selectedSlot,35,38) and q.slot==c.selectedSlot and
     (q.itemResRef~=c.selectedRef or q.selectedNow~=true) then return false end
  if q.slot~=c.selectedSlot and q.selectedNow==true then return false end
 end
 return true
end
local function copy_history(h)
 local out={}
 if type(h)=='table' then
  for k,v in pairs(h) do
   if ident(k) and type(v)=='table' and apr(v.apr) and integer(v.sequence,1,64) then
    out[k]={apr=v.apr,sequence=v.sequence,selectedSlot=v.selectedSlot}
   end
  end
 end
 return out
end
function M.step(f,r6,previous)
 local ck=context(f)
 if not ck then return result('HOLD','FRAME_INVALID',nil) end
 if not safeR6(r6,f) then return result('HOLD','R6_UNTRUSTED_OR_MISMATCH',nil) end
 local sameActor=type(previous)=='table' and previous.schema==M.version and
  previous.sessionId==f.sessionId and previous.actor==f.actor and previous.partyIndex==f.partyIndex
 if sameActor and (not integer(previous.sequence,1,64) or f.sequence<=previous.sequence) then
  return result('HOLD','REPLAY_OR_NONMONOTONIC_SEQUENCE',nil)
 end
 local continuous=sameActor and f.sequence==previous.sequence+1
 local sameContext=continuous and previous.context==ck
 local priorHistory=sameContext and copy_history(previous.history) or {}
 local c=r6.currentSelected
 -- AMMO selection never identifies a launcher, therefore no slot-level APR claim.
 local selectedQuick=integer(c.selectedSlot,35,38)
 if selectedQuick then
  priorHistory[c.selectedRef]={apr=c.selectedAPRDecoded,sequence=f.sequence,selectedSlot=c.selectedSlot}
 end
 -- Only the currently selected quickslot may have currently observed APR.
 local rows={}
 for i=1,4 do
  local q=r6.quickslots[i]
  local selected=selectedQuick and c.selectedSlot==q.slot and c.selectedRef==q.itemResRef
  local old=q.itemResRef and priorHistory[q.itemResRef] or nil
  rows[i]={slot=q.slot,itemRef=q.itemResRef,
   evidence=selected and 'SELECTED_EVENT_APR_OBSERVED_R6_UNAUTHENTICATED' or
     (old and 'HISTORICAL_SELECTED_APR_NOT_CURRENT' or 'ALTERNATE_APR_UNKNOWN'),
   currentSelectedAPR=selected and c.selectedAPRDecoded or nil,
   historicalAPR=(not selected and old and old.apr or nil),
   currentAlternateAPR=nil}
 end
 local nextState={schema=M.version,sessionId=f.sessionId,actor=f.actor,partyIndex=f.partyIndex,
  sequence=f.sequence,context=ck,history=priorHistory}
 return result('PASSIVE_LEDGER_ONLY',sameContext and 'SAME_CONTEXT_UNPROVEN_NATIVE_APR' or
  'CONTEXT_NEW_OR_CHANGED_HISTORY_INVALIDATED',nextState,{
  rows=rows,selectedSlot=c.selectedSlot,selectedRef=c.selectedRef,
  selectedEventAPR=c.selectedAPRDecoded,
  selectedQuickslotObserved=selectedQuick,launcherIdentified=false,
  relevantContextChanged=not sameContext,
  nextRequiredEvidence={'NATIVE_ALTERNATE_SLOT_APR_SAME_EFFECTIVE_CONTEXT',
   'NATIVE_TARGET_RESISTANCES','MANUAL_AND_EPS_SAFE_ACTION_BOUNDARY'}})
end
return M
