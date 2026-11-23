-- BGXAI R18: passive on-demand selected attack / launcher / current derived stats.
-- SOURCE ONLY, NOT INSTALLED. NO hooks, game state mutation, WeiDU, IO or dispatch.
-- Values originate only in an explicitly supplied adapter. This API contract
-- is NOT a native event token and is NOT proof of effective weapon behavior.
local M = { version = 'BGXAI_R18_NATIVE_LINK_PROBE_SOURCE_ONLY', installed = false }
local STATS = {
 'm_nNumberOfAttacks', 'm_nTHAC0', 'm_nSTR', 'm_nDEX',
 'm_nMeleeTHAC0Bonus', 'm_nMissileTHAC0Bonus', 'm_bImprovedHaste', 'm_nLuck'
}
M.stats = STATS
local function integer(x,low,high)
 return type(x)=='number' and x==x and x~=math.huge and x~=-math.huge and
  x%1==0 and x>=low and x<=high
end
local function resref(x)
 return type(x)=='string' and #x>=1 and #x<=8 and not x:find('[^%w_]')
end
local function flags(status, reason)
 return {schema=M.version,status=status,reason=reason,
  readOnly=true,installed=false,executable=false,dispatchAuthorized=false,
  weaponSwitchAuthorized=false,gameModified=false,ordersSent=0,
  currentActionPreserved=true,originalActionQueueUntouched=true,
  nativeActionEventIdVerified=false,nativeItemIdentityAuthenticated=false,
  nativeLauncherAmmoPairVerified=false,liveRuntimeVerified=false,
  abilityEffectPayloadVerified=false,fullActiveEffectsFingerprintVerified=false,
  derivedStatsFingerprintIsCompleteEffectState=false,
  activeBuffsComplete=false,alternateSlotAPRVerified=false,
  manualOrderOriginVerified=false,epsQueueVerified=false,
  allEnemyProtectionsVerified=false,combatPriorityAuthorized=false}
end
local function call(api,key,...)
 if type(api)~='table' or type(api[key])~='function' then return nil,'MISSING_ADAPTER_'..key end
 local ok,val=pcall(api[key],...)
 if not ok then return nil,'FAILED_ADAPTER_'..key end
 if val==nil then return nil,'EMPTY_ADAPTER_'..key end
 return val,nil
end
local function event_ok(e)
 return type(e)=='table' and integer(e.actor,1,2147483647) and
  integer(e.target,1,2147483647) and e.actor~=e.target and
  (e.action==3 or e.action==30)
end
local function select_ok(s)
 return type(s)=='table' and integer(s.slot,10,38) and
  (s.slot==10 or s.slot>=11 and s.slot<=14 or s.slot>=35 and s.slot<=38) and
  integer(s.abilityIndex,0,31) and
  (s.slot==10 or resref(s.resref))
end
local function slot_class(slot)
 if slot==10 then return 'FIST' end
 if slot>=11 and slot<=14 then return 'AMMO' end
 return 'WEAPON'
end
local function stats_ok(s)
 if type(s)~='table' then return false end
 for _,k in ipairs(STATS) do
  if not integer(s[k],-2147483648,2147483647) then return false end
 end
 return integer(s.m_nNumberOfAttacks,0,10)
end
local function stats_key(s)
 local v={}
 for _,k in ipairs(STATS) do v[#v+1]=tostring(s[k]) end
 -- Not a collision resistant effect fingerprint; only eight measured scalars.
 return table.concat(v, ':')
end
local function same_event(a,b)
 return a.actor==b.actor and a.target==b.target and a.action==b.action
end
local function same_selection(a,b)
 return a.slot==b.slot and a.abilityIndex==b.abilityIndex and a.resref==b.resref
end
local function launcher_ok(l)
 return type(l)=='table' and integer(l.slot,35,38) and resref(l.resref)
end
local function same_launcher(a,b)
 return a.slot==b.slot and a.resref==b.resref
end
local function hold(why,context)
 local o=flags('HOLD',why)
 if type(context)=='table' then
  -- The small raw candidate context is never interpreted as authorization.
  o.actor=context.actor;o.target=context.target;o.action=context.action
  o.selectedSlot=context.slot;o.selectedAbilityIndex=context.abilityIndex
 end
 return o
end
function M.observe(sprite,action,api)
 if sprite==nil or action==nil then return hold('SOURCE_OR_ACTION_MISSING') end
 local e,er=call(api,'read_event',sprite,action)
 if er then return hold(er) end
 if not event_ok(e) then return hold('ATTACK_ACTION_OR_ID_UNREADABLE') end
 local s,err=call(api,'read_selection',sprite)
 if err then return hold(err,e) end
 local c={actor=e.actor,target=e.target,action=e.action,
          slot=s.slot,abilityIndex=s.abilityIndex}
 if not select_ok(s) then return hold('SELECTION_OR_RESREF_UNREADABLE',c) end
 local kind=slot_class(s.slot)
 local ab,l=nil,nil
 if kind~='FIST' then
  ab,err=call(api,'read_ability',sprite,s)
  if err or type(ab)~='table' or ab.present~=true then
   return hold(err or 'SELECTED_ABILITY_NOT_FOUND',c)
  end
 end
 if kind=='AMMO' then
  l,err=call(api,'read_launcher',sprite,s,ab)
  if err or not launcher_ok(l) then
   return hold(err or 'NATIVE_LAUNCHER_SLOT_OR_RESREF_UNAVAILABLE',c)
  end
  -- The selected ammunition and launcher must be distinct inventory slots.
  if l.resref==s.resref then return hold('LAUNCHER_AMMO_RESREF_ALIAS_UNVERIFIED',c) end
 end
 local st,es=call(api,'read_stats',sprite)
 if es or not stats_ok(st) then return hold(es or 'ACTIVE_DERIVED_STATS_UNREADABLE',c) end
 -- No effect-list traversal: m_derivedStats alone does not prove all buffs.
 -- Double-read guards against obvious source selection/target/stat changes.
 local e2,ee=call(api,'read_event',sprite,action)
 if ee or not event_ok(e2) or not same_event(e,e2) then
  return hold('ACTION_OR_TARGET_CHANGED_DURING_READ',c)
 end
 local s2,se=call(api,'read_selection',sprite)
 if se or not select_ok(s2) or not same_selection(s,s2) then
  return hold('SELECTED_ITEM_OR_ABILITY_CHANGED_DURING_READ',c)
 end
 if kind~='FIST' then
  local ab2,ae=call(api,'read_ability',sprite,s2)
  if ae or type(ab2)~='table' or ab2.present~=true then
   return hold('SELECTED_ABILITY_DISAPPEARED_DURING_READ',c)
  end
 end
 if kind=='AMMO' then
  local l2,le=call(api,'read_launcher',sprite,s2,ab)
  if le or not launcher_ok(l2) or not same_launcher(l,l2) then
   return hold('LAUNCHER_CHANGED_DURING_READ',c)
  end
 end
 local st2,ts=call(api,'read_stats',sprite)
 if ts or not stats_ok(st2) or stats_key(st)~=stats_key(st2) then
  return hold('ACTIVE_DERIVED_STATS_CHANGED_DURING_READ',c)
 end
 local result=flags('CURRENT_ATTACK_NATIVE_READ_CANDIDATE_RO',
  'UPSTREAM_EEEX_API_CONTRACT_ONLY_NOT_RUNTIME_AUTHENTICATED')
 result.actor=e.actor; result.target=e.target; result.rawActionId=e.action
 result.selectedSlot=s.slot;result.slotClass=kind
 result.selectedAbilityIndex=s.abilityIndex
 result.selectedItemResrefRaw=(kind=='FIST' and nil or s.resref)
 result.selectedAbilityObjectSeen=(kind~='FIST')
 result.launcherSlotCandidate=l and l.slot or nil
 result.launcherResrefCandidate=l and l.resref or nil
 result.launcherLinkStatus=(kind=='AMMO' and 'NATIVE_GETLAUNCHER_READ_CANDIDATE_ONLY'
   or 'NOT_APPLICABLE_TO_SELECTED_SLOT')
 result.currentSelectedAprKeyRaw=st.m_nNumberOfAttacks
 result.derivedStatSnapshotKey=stats_key(st)
 result.derivedStatFieldsMeasured=#STATS
 result.derivedStatsOnly=true
 result.uncertainties={
  'NO_SHARED_NATIVE_EVENT_ID','ABILITY_HEADER_EFFECTS_NOT_READ',
  'NOT_FULL_ACTIVE_EFFECT_LIST','NO_LIVE_EEEX_V117_ADAPTER_SHA_PROOF',
  'LAUNCHER_AMMO_LINK_NOT_LIVE_VERIFIED','NO_ALTERNATE_SLOTS_APR',
  'NO_MANUAL_EPS_QUEUE_BOUNDARY'}
 return result
end
return M
