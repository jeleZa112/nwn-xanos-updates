local here=(arg and arg[0] or ''):match('^(.*[/\\])') or './'
local R6=dofile(here..'BGXAI_WEAPON_SELECTED_VS_ALTERNATE_V1.lua')
local n=0
local function check(name,fn) fn();n=n+1;print('PASS '..name) end
local function eq(a,b) assert(a==b,tostring(a)..' ~= '..tostring(b)) end
local function slot(i,ref,c)
 return {slot=i,resrefRaw=ref,useCount1Raw=c,useCount2Raw=0,useCount3Raw=0}
end
local function record(seq,chosen,apr)
 return {schema='BGXAI_R27_SINGLE_CALLBACK_SELECTED_RO_V1',
 status='CURRENT_SELECTED_SAME_CALLBACK_SOURCE_CANDIDATE',
 seq=seq,actor=251,partyIndex=1,actionRaw=23,selectedWeaponRaw=chosen,
 selectedAbilityRaw=0,selectedAprKeyRaw=apr,
 quickWeaponsRaw={slot(35,'SW1H04',1),slot(36,'BOW05',1),slot(37,nil,nil),slot(38,'STAF01',1)},
 quiversRaw={slot(11,nil,nil),slot(12,'AROW01',20),slot(13,nil,nil),slot(14,nil,nil)},
 offhandRaw={slot(9,nil,nil)},
 rawInventoryDoubleReadConsistent=true,selectedDerivedStatsDoubleReadConsistent=true,
 r4Status='RAW_CURRENT_SELECTED_DERIVED_STATS_STABLE_NOT_COMPLETE_EFFECTS',
 sameLuaListenerInvocation=true,
 nativeEventTokenAuthenticated=false,engineSessionVerified=false,
 alternativeAPRVerified=false,launcherAmmoPairVerified=false,
 completeActiveEffectsVerified=false,epsManualQueueVerified=false,
 ordersSent=0,localsWritten=0,dispatchAuthorized=false,
 weaponSwitchAuthorized=false,readOnly=true,
 selectedStatsRaw={m_nNumberOfAttacks=apr,m_nTHAC0=18}}
end
local function safe(x)
 eq(x.executable,false);eq(x.dispatchAuthorized,false)
 eq(x.weaponSwitchAuthorized,false);eq(x.alternateSlotAPRVerified,false)
 eq(x.ordersSent,0);eq(x.currentActionPreserved,true)
end
local s1,p1=R6.observe_r27(record(1,38,1))
check('selected staff APR 1 and no dispatch',function()
 safe(s1);eq(s1.selectedAPRDecoded,1)
 eq(s1.quickslots[4].effectiveAPRForUnselected,nil)
end)
local s2,p2=R6.observe_r27(record(2,12,2),p1)
check('selected ammo APR 2 never promoted to bow APR',function()
 safe(s2);eq(s2.selectedIsAmmoNotAuthenticatedLauncher,true)
 eq(s2.quickslots[2].historicalSelectedAPR,nil)
end)
local s3,p3=R6.observe_r27(record(3,35,7),p2)
check('selected sword APR 1.5, staff stays historical only',function()
 safe(s3);eq(s3.selectedAPRDecoded,1.5)
 eq(s3.quickslots[4].historicalSelectedAPR,1)
 eq(s3.quickslots[4].effectiveAPRForUnselected,nil)
end)
check('weapon replaced, same charges: old APR cleared',function()
 local v=record(4,35,7);v.quickWeaponsRaw[4].resrefRaw='STAF02'
 local x,p=R6.observe_r27(v,p3);safe(x)
 eq(p.slots[38],nil);eq(x.priorRawEquipmentSignatureMatched,false)
end)
check('quiver count changed: history cleared',function()
 local v=record(4,35,7);v.quiversRaw[2].useCount1Raw=19
 local x=R6.observe_r27(v,p3);safe(x)
 eq(x.quickslots[4].historicalSelectedAPR,nil)
end)
check('offhand change: history cleared',function()
 local v=record(4,35,7);v.offhandRaw[1].resrefRaw='SHLD01'
 local x=R6.observe_r27(v,p3);safe(x)
 eq(x.priorRawEquipmentSignatureMatched,false)
end)
check('ability changed: history cleared',function()
 local v=record(4,35,7);v.selectedAbilityRaw=1
 local x=R6.observe_r27(v,p3);safe(x)
 eq(x.priorRawEquipmentSignatureMatched,false)
end)
check('old one-read R27 never promoted',function()
 local v=record(4,35,7);v.rawInventoryDoubleReadConsistent=nil
 local x=R6.observe_r27(v,p3);safe(x)
 eq(x.status,'HOLD_UNVERIFIED_OBSERVATION')
end)
check('falsified effect or EPS proof denied',function()
 for _,f in ipairs({'engineSessionVerified','completeActiveEffectsVerified',
  'epsManualQueueVerified','alternativeAPRVerified','nativeEventTokenAuthenticated'}) do
  local v=record(4,35,7);v[f]=true
  local x=R6.observe_r27(v,p3);safe(x)
  eq(x.status,'HOLD_UNVERIFIED_OBSERVATION')
 end
end)
check('stale fabricated history cannot assert APR',function()
 local p={version=p3.version,source=p3.source,actor=p3.actor,partyIndex=p3.partyIndex,
 lastSeq=p3.lastSeq,gearKey=p3.gearKey,slots={},ammo={}}
 for k,v in pairs(p3.slots) do
  local copy={} for key,value in pairs(v) do copy[key]=value end
  p.slots[k]=copy
 end
 p.slots[38].aprAtSelection=9
 local x=R6.observe_r27(record(4,35,7),p);safe(x)
 eq(x.quickslots[4].historicalSelectedAPR,nil)
end)
check('different actor or sequence refuses carryover',function()
 local v=record(7,35,7);local x=R6.observe_r27(v,p3);safe(x)
 eq(x.priorRawEquipmentSignatureMatched,false)
 v=record(4,35,7);v.actor=299
 local y=R6.observe_r27(v,p3);safe(y)
 eq(y.priorRawEquipmentSignatureMatched,false)
end)
check('malformed inventory and stats fail closed',function()
 local v=record(4,35,7);v.offhandRaw[2]=slot(9,nil,nil)
 local x=R6.observe_r27(v,p3);safe(x)
 eq(x.status,'HOLD_UNVERIFIED_OBSERVATION')
 v=record(4,35,7);v.selectedStatsRaw.m_nNumberOfAttacks=2
 local y=R6.observe_r27(v,p3);safe(y)
 eq(y.status,'HOLD_UNVERIFIED_OBSERVATION')
end)
check('R27 work-in-progress temporary stats never enter R6 APR history',function()
 local v=record(4,35,7);v.selectedDerivedStatsDoubleReadConsistent=nil
 local x,next=R6.observe_r27(v,p3);safe(x)
 eq(x.status,'HOLD_UNVERIFIED_OBSERVATION');eq(next,nil)
end)
check('R27 missing or stale R4 status never enters selected APR history',function()
 for _,kind in ipairs({'RAW_CURRENT_SELECTED_STATS_OBSERVED_NOT_COMPLETE_EFFECTS',
                       'HOLD_DERIVED_STATS_TEMP_VIEW_DURING_READ'}) do
  local v=record(4,35,7);v.r4Status=kind
  local x,next=R6.observe_r27(v,p3);safe(x)
  eq(x.status,'HOLD_UNVERIFIED_OBSERVATION');eq(next,nil)
 end
 local v=record(4,35,7);v.r4Status=nil
 local x=R6.observe_r27(v,p3);safe(x);eq(x.status,'HOLD_UNVERIFIED_OBSERVATION')
end)
print('PASS R6 R27 evidence '..n..'/'..n)
