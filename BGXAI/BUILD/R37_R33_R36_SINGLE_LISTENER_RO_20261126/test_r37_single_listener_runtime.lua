-- R37: full 60KB R33-derived observer runtime mock, WITHOUT real EEex/game writes.
local filename=assert(arg and arg[1],"Pass R37 source file path")
local listeners,logs,commands={}, {},0
Infinity_Log=function(line)logs[#logs+1]=line end
EEex_ReadLString=function()return 'MOCORE.BCS' end
EEex_Sprite_GetInPortraitID=function(i)return i==2 and 1001 or nil end
EEex_Action_AddSpriteStartedActionListener=function(f)listeners[#listeners+1]=f end
SelectWeaponAbility=function()commands=commands+1;error('BLOCK GAME SWITCH')end
ClearActions=function()commands=commands+1;error('BLOCK QUEUE CLEAR')end
Stop=function()commands=commands+1;error('BLOCK STOP')end
Attack=function()commands=commands+1;error('BLOCK ATTACK')end
local function yes(v,m)assert(v,m)end
local function has(s,p)return type(s)=='string' and s:find(p,1,true)~=nil end
local stats=setmetatable({
 m_nNumberOfAttacks=2,m_nTHAC0=20,m_nSTR=15,m_nSTRExtra=0,
 m_bImprovedHaste=0,m_nHitBonus=0,m_nLevel1=1,m_nLevel2=1,
 m_nLevel3=1,m_nKit=16384,m_nProficiencyLongSword=2,
 m_nProficiencyShortBow=0}, {__index=function()return 1 end})
local getStats=function()return stats end
local reads=0
EEex_Sprite_GetActiveStats=function()
 reads=reads+1
 return getStats()
end
local function item(resref,count)
 return {cResRef={get=function()return resref end},
         m_useCount1=count,m_useCount2=1,m_useCount3=1,
         m_flags=1,m_itemType=5}
end
local equipment={
 [35]=item('SW1H04',0),[36]=item('BOW05',0),
 [38]=item('STAF01',0),[12]=item('AROW01',20),
 [9]=item('SHLD03A',0)}
local act={m_actionID=23,m_source={m_pchData=65536}}
local sprite={
 m_id=1001,m_typeAI={m_Class=2},m_bAllowEffectListCall=1,
 m_curAction=act,m_queuedActions={m_nCount=0},
 m_bInActionExecution=0,m_bNoInterrupt=0,
 m_curScriptNum=-1,m_actionCount=0,m_interrupt=0,
 m_lOrderedBy={},m_lOrderedBySent={},
 m_equipment={m_selectedWeapon=12,m_selectedWeaponAbility=0,
 m_items={get=function(_,i)return equipment[i] end}},
}
dofile(filename)
yes(#listeners==1,'exactly one listener, no new R37 hook')
yes(#logs==2,'one session each R33 and R37')
yes(has(logs[1],'[BGXR27]') and has(logs[2],'[BGXR37]'),'same original console sink')
yes(has(logs[2],'"actionOrigin":"UNKNOWN"'),'never claim EPS or manual origin')
yes(BGXAI_R27_ObserverPilot.version=='BGXAI_R37_R33_R36_SINGLE_LISTENER_CANDIDATE','new source candidate version')
local function fire()
 local before=reads
 listeners[1](sprite,act)
 local delta=reads-before
 yes(delta==2,'R37 must reuse EXACT R33 double-read count (2) with no extra getter')
 yes(logs[#logs-1]:find('[BGXR27]',1,true)~=nil,'original R33 event still emitted')
 yes(logs[#logs]:find('[BGXR37]',1,true)~=nil,'R37 bounded status in same console')
 yes(has(logs[#logs],'"weaponSwitchAuthorized":false'),'no switch')
 yes(has(logs[#logs],'"dispatchAuthorized":false'),'no dispatch')
 yes(commands==0,'no engine calls')
 return logs[#logs-1],logs[#logs]
end
local _,advice=fire()
yes(has(advice,'"R37_FIRST_R33_SAMPLE_NO_PRIOR"'),'first sample has no prior')
yes(has(advice,'"invalidateCachedAdvice":true'),'first sample fail closed')
_,advice=fire()
yes(has(advice,'"RAW_FIELDS_EQUAL_NOT_EFFECT_OR_EPS_PROOF"'),'unchanged raw context not full effects proof')
yes(has(advice,'"invalidateCachedAdvice":false'),'same raw fields do not invalidate')
equipment[12].m_useCount1=19
_,advice=fire()
yes(has(advice,'"EQUIPMENT_OR_AMMO_CHANGED_INVALIDATE_ADVICE"'),'observed ammo consumption invalidates cache')
yes(has(advice,'"invalidateCachedAdvice":true'),'ammo invalidation true')
act.m_actionID=3
_,advice=fire()
yes(has(advice,'"ACTION_CONTEXT_CHANGED_INVALIDATE_ADVICE"'),'action transition invalidates without interrupt')
yes(has(advice,'"invalidateCachedAdvice":true'),'action invalidation true')
stats.m_nSTR=18
_,advice=fire()
yes(has(advice,'"OBSERVED_STATS_CHANGED_INVALIDATE_ADVICE"'),'buff/stat transition invalidates')
-- When R33 cannot capture, R37 drops prior to avoid cross-HOLD reuse.
local alternating=0
getStats=function()
 alternating=alternating+1
 if alternating%2==1 then
  return setmetatable({m_nNumberOfAttacks=2,m_nTHAC0=20,m_nSTR=15},{__index=function()return 1 end})
 end
 return setmetatable({m_nNumberOfAttacks=2,m_nTHAC0=20,m_nSTR=17},{__index=function()return 1 end})
end
local raw,hold=fire()
yes(has(raw,'"status":"HOLD_SINGLE_CALLBACK_NO_DISPATCH"'),'unchanged R33 fail-closed on stats drift')
yes(has(hold,'"R37_R33_CAPTURE_HOLD_NO_DISPATCH"'),'R37 clears cached advice on HOLD')
getStats=function()return stats end
_,advice=fire()
yes(has(advice,'"R37_FIRST_R33_SAMPLE_NO_PRIOR"'),'after HOLD no stale advice is reused')
dofile(filename)
yes(#listeners==1,'re-loading source must not register another listener')
yes(commands==0,'all cases zero action orders')
print('PASS R37 one-listener real R33+R36 pipeline 7 transitions, 2 stats reads/callback, 0 engine orders')
