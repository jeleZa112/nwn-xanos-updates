-- BGXAI R12 V2: strict SOURCE ONLY bridge, R9/R10 -> target-bound R11 -> R12.
-- Verifies correspondence of caller-supplied frames without claiming EEex LIVE.
-- Reuses original R10.assess and R12.compare; NO parallel weapon ranker.
-- Never registers listeners, issues orders, modifies files, or touches queues.
local M={version='BGXAI_WEAPON_R12_TARGET_BOUND_CROSSCHECK_V2',installed=false}
local function num(x,lo,hi)
 return type(x)=='number' and x==x and x~=math.huge and x~=-math.huge and x>=lo and x<=hi
end
local function int(x,lo,hi) return num(x,lo,hi) and x%1==0 end
local function ident(s)
 return type(s)=='string' and #s>0 and #s<=128 and not s:find('[^%w_.:%-]')
end
local function hold(reason,extra)
 local r={schema=M.version,status='HOLD',reason=reason,installed=false,
  executable=false,dispatchAuthorized=false,weaponSwitchAuthorized=false,
  rankingAuthorized=false,ordersSent=0,actionQueueCleared=false,
  currentActionPreserved=true,nativeEvidenceAuthenticated=false,
  liveReadVerified=false,manualOrderProven=false,epsQueueProven=false,
  alternateSlotAPRVerified=false,gameFilesModified=false}
 if extra then
  if int(extra.selectedSlot,35,38) then r.selectedSlot=extra.selectedSlot end
 end
 return r
end
local function frame_ok(f,m)
 if type(f)~='table' or type(m)~='table' or type(m.frame)~='table' then return false end
 if not ident(f.sessionId) or not ident(f.snapshotId) or not ident(f.targetFingerprint) or
    not int(f.actor,1,2147483647) or not int(f.targetActor,1,2147483647) or
    f.actor==f.targetActor or not int(f.sequence,1,64) or
    not int(f.selectedSlot,35,38) or not int(f.selectedAbility,0,255) then return false end
 -- R10's internal frame linkage does not include these two fields; require them
 -- explicitly to avoid accidental cross-target / cross-ability comparison.
 return m.frame.targetActor==f.targetActor and
        m.frame.selectedAbility==f.selectedAbility
end
local function bound_ok(f,b)
 if type(b)~='table' or
  b.schema~='BGXAI_R11_TARGET_BOUND_HIT_CANDIDATE_V2' or
  b.status~='TARGET_BOUND_SELECTED_HIT_CANDIDATE_NOT_NATIVE_PROOF' or
  b.sessionId~=f.sessionId or b.snapshotId~=f.snapshotId or
  b.sourceActor~=f.actor or b.targetActor~=f.targetActor or
  b.sequence~=f.sequence or b.selectedSlot~=f.selectedSlot or
  b.selectedAbility~=f.selectedAbility or
  (b.rawActionId~=3 and b.rawActionId~=30) or
  not int(b.hitChancePercentCandidate,0,100) or
  type(b.isImmuneCandidate)~='boolean' or
  b.candidateDerivedFromCallerSuppliedApi~=true then return false end
 for _,k in ipairs({'installed','executable','dispatchAuthorized',
  'weaponSwitchAuthorized','rankingAuthorized','nativeEvidenceAuthenticated',
  'liveReadVerified','hostileTargetProven','actionAttackProven',
  'alternativeWeaponProven','alternateSlotAPRVerified',
  'manualOrderProven','epsQueueProven','actionQueueCleared',
  'gameFilesModified'}) do if b[k]~=false then return false end end
 return b.ordersSent==0 and b.currentActionPreserved==true
end
local function safe_existing(o,schema)
 return type(o)=='table' and o.schema==schema and o.installed==false and
  o.executable==false and o.dispatchAuthorized==false and
  o.weaponSwitchAuthorized==false and o.nativeEvidenceAuthenticated==false and
  o.actionQueueCleared==false and o.currentActionPreserved==true and
  o.manualOrderProven==false and o.epsQueueProven==false and o.ordersSent==0
end
function M.compare(frame,ledger,model,targetBound,r10Module,r12Module)
 if not frame_ok(frame,model) then return hold('FRAME_TARGET_OR_ABILITY_UNBOUND') end
 if not bound_ok(frame,targetBound) then return hold('R11_TARGET_BOUND_EVIDENCE_NOT_MATCHED') end
 if type(r10Module)~='table' or type(rawget(r10Module,'assess'))~='function' or
  type(r12Module)~='table' or type(rawget(r12Module,'compare'))~='function' then
  return hold('PURE_MODULE_DEPENDENCY_MISSING') end
 -- Re-evaluate the static forecast from this exact supplied frame and ledger;
 -- accepting a detached R10 result would lose actor/session provenance.
 local ok,forecast=pcall(r10Module.assess,frame,ledger,model)
 if not ok or not safe_existing(forecast,'BGXAI_WEAPON_R10_INTERVAL_RANKER_V1') then
  return hold('R10_CALCULATION_UNAVAILABLE_OR_UNTRUSTED') end
 if forecast.status~='INTERVAL_FORECAST_ONLY' or forecast.mayRecommendWeaponSwitch~=false or
    forecast.rankedNative~=false or forecast.selectedSlot~=frame.selectedSlot or
    forecast.targetFingerprint~=frame.targetFingerprint then
  return hold('R10_CALCULATION_HELD:'..tostring(forecast.reason or 'UNTRUSTED')) end
 -- Legacy R12 accepts V1 probe shape only. This view is generated ONLY after
 -- validating R11 target-bound V2. It is NOT a native attestation.
 local candidate={schema='BGXAI_WEAPON_R11_EEEX_SELECTED_HIT_PROBE_V1',
  status='SELECTED_HIT_CHANCE_CANDIDATE_ONLY',installed=false,
  executable=false,dispatchAuthorized=false,weaponSwitchAuthorized=false,
  nativeEvidenceAuthenticated=false,engineMethodProvenInstalled=false,
  targetActorBindingProven=false,liveReadVerified=false,
  currentActionPreserved=true,actionQueueCleared=false,
  manualOrderProven=false,epsQueueProven=false,
  alternateSlotHitChanceVerified=false,alternateSlotAPRVerified=false,
  sessionId=frame.sessionId,snapshotId=frame.snapshotId,actor=frame.actor,
  targetActor=frame.targetActor,sequence=frame.sequence,
  selectedSlot=frame.selectedSlot,hitChancePercent=targetBound.hitChancePercentCandidate,
  isImmuneToSelectedWeapon=targetBound.isImmuneCandidate}
 local view={sessionId=frame.sessionId,snapshotId=frame.snapshotId,
  targetFingerprint=frame.targetFingerprint,actor=frame.actor,
  targetActor=frame.targetActor,sequence=frame.sequence,selectedSlot=frame.selectedSlot}
 local yes,out=pcall(r12Module.compare,view,forecast,candidate)
 if not yes or not safe_existing(out,'BGXAI_WEAPON_R12_SELECTED_HIT_CROSSCHECK_V1') or
  out.rankingAuthorized~=false or out.liveReadVerified~=false then
  return hold('R12_COMPARISON_UNAVAILABLE_OR_UNTRUSTED') end
 if out.status~='SELECTED_ONLY_CONSISTENCY_UNAUTHENTICATED' then
  return hold('R12_COMPARISON_HELD:'..tostring(out.reason or 'UNTRUSTED')) end
 if out.candidateSelectedHitPercent~=targetBound.hitChancePercentCandidate or
    out.selectedImmunityCandidate~=targetBound.isImmuneCandidate or
    out.selectedSlot~=frame.selectedSlot or out.sourceActor~=frame.actor or
    out.targetActor~=frame.targetActor or out.alternativeWeaponEvidenceAdded~=false or
    out.candidateWithinForecast~=true then
  return hold('R12_COMPARISON_RESULT_MISMATCH') end
 return {schema=M.version,status='R10_R11_TARGET_BOUND_R12_CONSISTENT_SOURCE_ONLY',
  selectedSlot=frame.selectedSlot,selectedAbility=frame.selectedAbility,
  sourceActor=frame.actor,targetActor=frame.targetActor,
  sessionId=frame.sessionId,snapshotId=frame.snapshotId,sequence=frame.sequence,
  candidateHitChancePercent=targetBound.hitChancePercentCandidate,
  candidateImmunity=targetBound.isImmuneCandidate,
  forecastFingerprint=frame.targetFingerprint,
  selectedItemRefUnverifiedAtRead=true,
  targetFingerprintUnauthenticated=true,
  historicalOrEstimatedAlternateAPRNotCurrentProof=true,
  readOnly=true,installed=false,executable=false,dispatchAuthorized=false,
  weaponSwitchAuthorized=false,rankingAuthorized=false,ordersSent=0,
  actionQueueCleared=false,currentActionPreserved=true,nativeEvidenceAuthenticated=false,
  liveReadVerified=false,manualOrderProven=false,epsQueueProven=false,
  alternateSlotAPRVerified=false,gameFilesModified=false}
end
return M
