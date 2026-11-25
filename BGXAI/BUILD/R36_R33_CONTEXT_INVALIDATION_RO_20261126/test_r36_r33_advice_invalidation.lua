-- Pure Lua real-shaped R33 direct callback tests (no installed game or EEex).
local folder=(arg and arg[0] or ''):match('^(.*[/\\])') or './'
local r36=dofile(folder..'BGXAI_R36_R33_ADVICE_INVALIDATION.lua')
local count=0
local function eq(a,b) assert(a==b,tostring(a)..' != '..tostring(b)) end
local function case(name,fn)fn();count=count+1;print('PASS R36 '..name)end
local function copy(x)
 if type(x)~='table' then return x end
 local r={}
 for k,v in pairs(x) do r[k]=copy(v) end
 return r
end
local function slot(index,kind,ordinal,refRaw,n)
 if refRaw==nil then
  return {index=index,kind=kind,ordinal=ordinal,access='NULL'}
 end
 return {index=index,kind=kind,ordinal=ordinal,
  access='OBJECT_RETURNED_UNVERIFIED',itemResrefRaw=refRaw,
  resrefAccess='RAW_RESREF_RETURNED_UNVERIFIED',
  useCount1Raw=n or 0,useCount2Raw=0,useCount3Raw=0,
  flagsRaw=1,itemTypeRaw=5}
end
local function record()
 local prof={} for i=1,46 do prof[i]=0 end
 prof[2]=2
 return {
  schema='BGXAI_R27_SINGLE_CALLBACK_SELECTED_RO_V1',
  status='CURRENT_SELECTED_SAME_CALLBACK_SOURCE_CANDIDATE',
  actor=1234,partyIndex=2,actionRaw=23,
  selectedWeaponRaw=12,selectedAbilityRaw=0,selectedAprKeyRaw=2,
  r4Status='RAW_CURRENT_SELECTED_DERIVED_STATS_STABLE_NOT_COMPLETE_EFFECTS',
  readOnly=true,ordersSent=0,localsWritten=0,
  dispatchAuthorized=false,weaponSwitchAuthorized=false,
  sourceOnly=true,sameLuaListenerInvocation=true,
  rawInventoryDoubleReadConsistent=true,
  selectedDerivedStatsDoubleReadConsistent=true,
  alternativeAPRVerified=false,launcherAmmoPairVerified=false,
  completeActiveEffectsVerified=false,epsManualQueueVerified=false,
  sampledStatsRaw={
    m_nNumberOfAttacks=2,m_nTHAC0=20,m_nSTR=15,m_nSTRExtra=0,
    m_bImprovedHaste=0,m_nHitBonus=0,
    m_nLevel1=1,m_nLevel2=1,m_nLevel3=1,m_nKit=16384,
  },
  rawProficiencyStat89to134=prof,
  quickWeaponsRaw={
    slot(35,'QUICKWEAPON',0,'SW1H04',0),
    slot(36,'QUICKWEAPON',1,'BOW05',0),
    slot(37,'QUICKWEAPON',2),
    slot(38,'QUICKWEAPON',3,'STAF01',0)},
  quiversRaw={
    slot(11,'QUIVER',0),
    slot(12,'QUIVER',1,'AROW01',20),
    slot(13,'QUIVER',2),
    slot(14,'QUIVER',3)},
  offhandRaw=slot(9,'OFFHAND_OR_SHIELD',0,'SHLD03A',0),
  queueSnapshotStable=true,queuedActionsRaw=0,
  actionSourceStable=false,actionSourceRaw=nil,
  actionOriginVerified=false,manualEpsQueueVerified=false,
 }
end
local function captured(e)return r36.capture(e)end
local function compare(a,b)return r36.compare(captured(a),captured(b))end
case('direct R33 no-extra-read capture',function()
 local a=captured(record())
 eq(a.status,'RAW_R33_CONTEXT_CAPTURED_ADVICE_ONLY')
 eq(a.sourceIsSameCallbackR33,true)
 eq(a.queueRaw,0)
 eq(a.selected,12)
 eq(a.stats[1],2)
 eq(a.stats[2],20)
 eq(a.gear[6][3],20)
 eq(a.ordersSent,0)
 eq(a.dispatchAuthorized,false)
end)
case('equal raw fields cannot imply identical effects',function()
 local a=record();local c=compare(a,copy(a))
 eq(c.status,'RAW_FIELDS_EQUAL_NOT_EFFECT_OR_EPS_PROOF')
 eq(c.invalidateCachedAdvice,false)
 eq(c.sameBuffContextVerified,false)
 eq(c.manualEpsOriginVerified,false)
 eq(c.weaponSwitchAuthorized,false)
end)
case('real R33 ammo 20 to 19 invalidates only advice',function()
 local a=record();local b=copy(a)
 b.quiversRaw[2].useCount1Raw=19
 local c=compare(a,b)
 eq(c.status,'EQUIPMENT_OR_AMMO_CHANGED_INVALIDATE_ADVICE')
 eq(c.observedAmmoDeltaInR33Raw,true)
 eq(c.invalidateCachedAdvice,true)
 eq(c.currentActionPreserved,true)
 eq(c.ordersSent,0)
 eq(c.weaponCommandsAllowed,false)
end)
case('same APR THAC0 with changed ammo still invalidates',function()
 local a=record();local b=copy(a)
 b.quiversRaw[2].useCount1Raw=19
 eq(a.sampledStatsRaw.m_nTHAC0,b.sampledStatsRaw.m_nTHAC0)
 eq(a.sampledStatsRaw.m_nNumberOfAttacks,b.sampledStatsRaw.m_nNumberOfAttacks)
 eq(compare(a,b).invalidateCachedAdvice,true)
end)
case('naturally selected sword not equivalent alternative weapon APR',function()
 local a=record();local b=copy(a)
 b.selectedWeaponRaw=35
 local c=compare(a,b)
 eq(c.status,'NATURAL_SELECTION_CHANGED_INVALIDATE_ADVICE')
 eq(c.alternateEffectiveAPRVerified,false)
end)
case('STR changes invalidate without interrupt',function()
 local a=record();local b=copy(a)
 b.sampledStatsRaw.m_nSTR=18
 local c=compare(a,b)
 eq(c.status,'OBSERVED_STATS_CHANGED_INVALIDATE_ADVICE')
 eq(c.currentActionPreserved,true)
end)
case('Improved Haste changing invalidates',function()
 local a=record();local b=copy(a)
 b.sampledStatsRaw.m_bImprovedHaste=1
 eq(compare(a,b).status,'OBSERVED_STATS_CHANGED_INVALIDATE_ADVICE')
end)
case('WPROF changed invalidates',function()
 local a=record();local b=copy(a)
 b.rawProficiencyStat89to134[2]=3
 eq(compare(a,b).status,'OBSERVED_STATS_CHANGED_INVALIDATE_ADVICE')
end)
case('action context change with 0 queue still no switch',function()
 local a=record();local b=copy(a)
 b.actionRaw=3
 local c=compare(a,b)
 eq(c.status,'ACTION_CONTEXT_CHANGED_INVALIDATE_ADVICE')
 eq(c.safeActionBoundaryVerified,false)
 eq(c.weaponCommandsAllowed,false)
end)
case('different actor holds even if all slots identical',function()
 local a=record();local b=copy(a)
 b.actor=5555
 eq(compare(a,b).reason,'ACTOR_OR_PARTY_CHANGED')
end)
case('unverified r4 must hold',function()
 local a=record();a.r4Status='HOLD_TEMP_STATS'
 eq(captured(a).status,'HOLD_R33_CONTEXT_UNVERIFIED')
end)
case('missing stat must hold, not default to zero',function()
 local a=record();a.sampledStatsRaw.m_nTHAC0=nil
 eq(captured(a).reason,'R33_STATS_MISSING_m_nTHAC0')
end)
case('selected APR mismatch must hold',function()
 local a=record();a.selectedAprKeyRaw=7
 eq(captured(a).reason,'R33_APR_MISMATCH')
end)
case('missing one of 46 WPROF must hold',function()
 local a=record();a.rawProficiencyStat89to134[46]=nil
 eq(captured(a).reason,'R33_PROF_46_MISSING')
end)
case('unknown ammo read must hold',function()
 local a=record();a.quiversRaw[2].useCount1Raw=nil
 eq(captured(a).reason,'R33_RAW_GEAR_INCOMPLETE')
end)
case('unreadable resref must hold',function()
 local a=record();a.quickWeaponsRaw[2].itemResrefRaw=nil
 eq(captured(a).reason,'R33_RAW_GEAR_INCOMPLETE')
end)
case('missing slot must hold',function()
 local a=record();a.quiversRaw[4]=nil
 eq(captured(a).reason,'R33_RAW_GEAR_INCOMPLETE')
end)
case('empty weapon slot never invents a resref',function()
 local a=captured(record())
 eq(a.gear[3][2],'-')
 eq(a.gear[3][3],-1)
end)
case('unsafe dispatch input must be rejected',function()
 local a=record();a.dispatchAuthorized=true
 eq(captured(a).status,'HOLD_R33_CONTEXT_UNVERIFIED')
end)
case('source must stay source-only with no engine orders',function()
 eq(r36.installed,false)
 local a=captured(record())
 eq(a.dispatchAuthorized,false)
 eq(a.currentActionPreserved,true)
 eq(a.actionQueueCleared,false)
end)
print('PASS R36 DIRECT R33 ADVICE INVALIDATION '..count..'/'..count..' OFFLINE ONLY')
