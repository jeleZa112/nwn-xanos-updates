-- BGXAI R12: purely structural cross-check between R10 forecast and R11 candidate.
-- SOURCE ONLY: proof that two UNAUTHENTICATED inputs agree is not native proof.
-- No ranking override, game commands, hooks, I/O, globals or EPS changes.
local M={version='BGXAI_WEAPON_R12_SELECTED_HIT_CROSSCHECK_V1',installed=false}
local function finite(v,lo,hi)
 return type(v)=='number' and v==v and v~=math.huge and v~=-math.huge and v>=lo and v<=hi
end
local function integer(v,lo,hi) return finite(v,lo,hi) and v%1==0 end
local function ident(v)
 return type(v)=='string' and #v>=1 and #v<=128 and not v:find('[^%w_.:%-]')
end
local function result(status,reason,extra)
 local r={schema=M.version,status=status,reason=reason,
  installed=false,executable=false,dispatchAuthorized=false,weaponSwitchAuthorized=false,
  ordersSent=0,currentActionPreserved=true,actionQueueCleared=false,
  nativeEvidenceAuthenticated=false,liveReadVerified=false,
  alternateAPRVerified=false,rankingAuthorized=false,
  manualOrderProven=false,epsQueueProven=false,gameFilesModified=false}
 if type(extra)=='table' then for k,v in pairs(extra) do r[k]=v end end
 return r
end
local function check_frame(f)
 return type(f)=='table' and ident(f.sessionId) and ident(f.snapshotId) and
  ident(f.targetFingerprint) and integer(f.actor,1,2147483647) and
  integer(f.targetActor,1,2147483647) and f.targetActor~=f.actor and
  integer(f.sequence,1,1000000) and integer(f.selectedSlot,35,38)
end
local function validate_r10(f,o)
 if type(o)~='table' or o.schema~='BGXAI_WEAPON_R10_INTERVAL_RANKER_V1' or
    o.status~='INTERVAL_FORECAST_ONLY' or o.installed~=false or
    o.executable~=false or o.nativeEvidenceAuthenticated~=false or
    o.weaponSwitchAuthorized~=false or o.dispatchAuthorized~=false or
    o.mayRecommendWeaponSwitch~=false or o.rankedNative~=false or
    o.currentActionPreserved~=true or o.actionQueueCleared~=false or
    o.manualOrderProven~=false or o.epsQueueProven~=false or
    o.selectedSlot~=f.selectedSlot or o.targetFingerprint~=f.targetFingerprint or
    type(o.rows)~='table' or #o.rows>4 then return nil,'R10_UNTRUSTED_OR_NOT_MATCHED' end
 local row,count=nil,0
 for _,x in ipairs(o.rows) do
  if type(x)~='table' or not integer(x.slot,35,38) or
     not finite(x.hitChanceMin,0,1) or not finite(x.hitChanceMax,0,1) or
     x.hitChanceMin>x.hitChanceMax or
     x.evidence~='CONSERVATIVE_STATIC_FORECAST_NOT_MEASURED_ALTERNATE_APR' then
    return nil,'R10_ROWS_INVALID' end
  if x.slot==f.selectedSlot then
   if x.selected~=true then return nil,'R10_SELECTED_ROW_MISMATCH' end
   count=count+1;row=x
  elseif x.selected==true then return nil,'R10_MULTIPLE_SELECTED_ROWS' end
 end
 if count~=1 then return nil,'R10_SELECTED_ROW_MISSING' end
 return row,nil
end
local function validate_r11(f,o)
 if type(o)~='table' or o.schema~='BGXAI_WEAPON_R11_EEEX_SELECTED_HIT_PROBE_V1' or
    o.status~='SELECTED_HIT_CHANCE_CANDIDATE_ONLY' or
    o.installed~=false or o.liveReadVerified~=false or
    o.nativeEvidenceAuthenticated~=false or o.engineMethodProvenInstalled~=false or
    o.targetActorBindingProven~=false or o.weaponSwitchAuthorized~=false or
    o.dispatchAuthorized~=false or o.executable~=false or
    o.currentActionPreserved~=true or o.actionQueueCleared~=false or
    o.epsQueueProven~=false or o.manualOrderProven~=false or
    o.alternateSlotHitChanceVerified~=false or o.alternateSlotAPRVerified~=false or
    o.sessionId~=f.sessionId or o.snapshotId~=f.snapshotId or
    o.actor~=f.actor or o.targetActor~=f.targetActor or
    o.sequence~=f.sequence or o.selectedSlot~=f.selectedSlot or
    not integer(o.hitChancePercent,0,100) or
    type(o.isImmuneToSelectedWeapon)~='boolean' then return false end
 return true
end
function M.compare(frame,r10,r11)
 if not check_frame(frame) then return result('HOLD','FRAME_INVALID') end
 local row,err=validate_r10(frame,r10)
 if not row then return result('HOLD',err) end
 if not validate_r11(frame,r11) then return result('HOLD','R11_NOT_MATCHED_OR_UNTRUSTED') end
 local observed=r11.hitChancePercent/100
 if observed+1e-12<row.hitChanceMin or observed>row.hitChanceMax+1e-12 then
  return result('HOLD','FORECAST_ENGINE_CANDIDATE_DISAGREEMENT',{
   selectedSlot=frame.selectedSlot,forecastHitMin=row.hitChanceMin,
   forecastHitMax=row.hitChanceMax,candidateSelectedHitPercent=r11.hitChancePercent})
 end
 return result('SELECTED_ONLY_CONSISTENCY_UNAUTHENTICATED',
  r11.isImmuneToSelectedWeapon and 'SELECTED_IMMUNITY_CANDIDATE_NO_RANK' or
    'SELECTED_HIT_CANDIDATE_WITHIN_FORECAST_NO_RANK',{
   selectedSlot=frame.selectedSlot,sourceActor=frame.actor,targetActor=frame.targetActor,
   candidateSelectedHitPercent=r11.hitChancePercent,
   selectedImmunityCandidate=r11.isImmuneToSelectedWeapon,
   candidateWithinForecast=true,
   selectedOnly=true,alternativeWeaponEvidenceAdded=false,
   nextRequiredEvidence={'INSTALLED_EEEX_VERSION_PROOF',
    'LIVE_TARGET_BOUND_NATIVELY','ALTERNATE_EFFECTIVE_APR',
    'COMPLETE_EFFECTS_AND_TARGET_PROTECTIONS','EPS_MANUAL_SAFE_BOUNDARY'}})
end
return M
