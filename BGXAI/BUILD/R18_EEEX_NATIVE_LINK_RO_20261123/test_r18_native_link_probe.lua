-- Pure Lua fake EEex adapter; tests do NOT launch EET or register listeners.
local M=dofile('BGXAI_R18_NATIVE_LINK_PROBE_RO.lua')
local cases=0
local function case(label,fn)
 cases=cases+1
 local ok,err=pcall(fn)
 if not ok then error('R18_TEST_FAILED '..label..' '..tostring(err)) end
end
local function eq(x,y) assert(x==y,tostring(x)..' != '..tostring(y)) end
local event={actor=139266124,target=135137293,action=3}
local selected={slot=12,abilityIndex=0,resref='AROW01'}
local launcher={slot=36,resref='BOW05'}
local stats={m_nNumberOfAttacks=2,m_nTHAC0=20,m_nSTR=15,m_nDEX=16,
 m_nMeleeTHAC0Bonus=0,m_nMissileTHAC0Bonus=0,m_bImprovedHaste=0,m_nLuck=0}
local function clone(x)
 local d={};for k,v in pairs(x) do d[k]=v end;return d
end
local function api()
 return {
  read_event=function()return clone(event)end,
  read_selection=function()return clone(selected)end,
  read_ability=function()return {present=true,handle={}}end,
  read_launcher=function()return clone(launcher)end,
  read_stats=function()return clone(stats)end}
end
local actor={};local action={}
local function probe(a)return M.observe(actor,action,a)end
case('ranged_candidate',function()
 local r=probe(api());eq(r.status,'CURRENT_ATTACK_NATIVE_READ_CANDIDATE_RO')
 eq(r.launcherSlotCandidate,36);eq(r.launcherResrefCandidate,'BOW05')
 eq(r.selectedItemResrefRaw,'AROW01');eq(r.currentSelectedAprKeyRaw,2)
 eq(r.derivedStatFieldsMeasured,8)
 eq(r.nativeLauncherAmmoPairVerified,false);eq(r.fullActiveEffectsFingerprintVerified,false)
 eq(r.weaponSwitchAuthorized,false);eq(r.dispatchAuthorized,false)
end)
case('melee_no_launcher',function()
 local a=api();a.read_selection=function()return {slot=35,abilityIndex=0,resref='SW1H04'}end
 a.read_launcher=function()error('must not request launcher for melee')end
 local r=probe(a);eq(r.status,'CURRENT_ATTACK_NATIVE_READ_CANDIDATE_RO')
 eq(r.slotClass,'WEAPON');eq(r.launcherSlotCandidate,nil)
end)
case('fist_no_item',function()
 local a=api();a.read_selection=function()return {slot=10,abilityIndex=0}end
 a.read_ability=function()error('must not dereference fist')end
 a.read_launcher=function()error('must not check launcher on fist')end
 local r=probe(a);eq(r.status,'CURRENT_ATTACK_NATIVE_READ_CANDIDATE_RO');eq(r.slotClass,'FIST')
end)
case('action_id_rejected',function()
 local a=api();a.read_event=function()return {actor=1,target=2,action=31}end
 eq(probe(a).reason,'ATTACK_ACTION_OR_ID_UNREADABLE')
end)
case('self_target_rejected',function()
 local a=api();a.read_event=function()return {actor=1,target=1,action=3}end
 eq(probe(a).status,'HOLD')
end)
case('target_missing',function()
 local a=api();a.read_event=function()return {actor=1,target=nil,action=3}end
 eq(probe(a).status,'HOLD')
end)
case('no_source',function()eq(M.observe(nil,action,api()).reason,'SOURCE_OR_ACTION_MISSING')end)
case('no_action',function()eq(M.observe(actor,nil,api()).reason,'SOURCE_OR_ACTION_MISSING')end)
case('missing_api',function()eq(probe({}).status,'HOLD')end)
case('invalid_selected_slot',function()
 local a=api();a.read_selection=function()return {slot=15,abilityIndex=0,resref='SW1H04'}end
 eq(probe(a).reason,'SELECTION_OR_RESREF_UNREADABLE')
end)
case('bad_resref',function()
 local a=api();a.read_selection=function()return {slot=12,abilityIndex=0,resref='AROW01_BIG'}end
 eq(probe(a).status,'HOLD')
end)
case('invalid_ability_index',function()
 local a=api();a.read_selection=function()return {slot=12,abilityIndex=255,resref='AROW01'}end
 eq(probe(a).status,'HOLD')
end)
case('missing_ability',function()
 local a=api();a.read_ability=function()return nil end
 eq(probe(a).reason,'EMPTY_ADAPTER_read_ability')
end)
case('unknown_ability',function()
 local a=api();a.read_ability=function()return {present=false} end
 eq(probe(a).reason,'SELECTED_ABILITY_NOT_FOUND')
end)
case('launcher_missing',function()
 local a=api();a.read_launcher=function()return nil end
 eq(probe(a).reason,'EMPTY_ADAPTER_read_launcher')
end)
case('launcher_not_quickslot',function()
 local a=api();a.read_launcher=function()return {slot=9,resref='BOW05'} end
 eq(probe(a).reason,'NATIVE_LAUNCHER_SLOT_OR_RESREF_UNAVAILABLE')
end)
case('launcher_same_as_ammo',function()
 local a=api();a.read_launcher=function()return {slot=36,resref='AROW01'} end
 eq(probe(a).reason,'LAUNCHER_AMMO_RESREF_ALIAS_UNVERIFIED')
end)
case('missing_derived_stat',function()
 local a=api();a.read_stats=function()local s=clone(stats);s.m_nLuck=nil;return s end
 eq(probe(a).reason,'ACTIVE_DERIVED_STATS_UNREADABLE')
end)
case('bad_apr_key',function()
 local a=api();a.read_stats=function()local s=clone(stats);s.m_nNumberOfAttacks=77;return s end
 eq(probe(a).status,'HOLD')
end)
case('action_target_changed',function()
 local a=api();local count=0
 a.read_event=function()count=count+1;return {actor=139266124,target=count==1 and 135137293 or 111,action=3}end
 eq(probe(a).reason,'ACTION_OR_TARGET_CHANGED_DURING_READ')
end)
case('selected_ability_changed',function()
 local a=api();local count=0
 a.read_selection=function()count=count+1;return {slot=12,abilityIndex=count==1 and 0 or 1,resref='AROW01'}end
 eq(probe(a).reason,'SELECTED_ITEM_OR_ABILITY_CHANGED_DURING_READ')
end)
case('selected_resref_changed',function()
 local a=api();local count=0
 a.read_selection=function()count=count+1;return {slot=12,abilityIndex=0,resref=count==1 and 'AROW01' or 'AROW02'}end
 eq(probe(a).reason,'SELECTED_ITEM_OR_ABILITY_CHANGED_DURING_READ')
end)
case('ability_dropped',function()
 local a=api();local count=0
 a.read_ability=function()count=count+1;return {present=count==1,handle={}}end
 eq(probe(a).reason,'SELECTED_ABILITY_DISAPPEARED_DURING_READ')
end)
case('launcher_swap',function()
 local a=api();local count=0
 a.read_launcher=function()count=count+1;return {slot=count==1 and 36 or 38,resref='BOW05'}end
 eq(probe(a).reason,'LAUNCHER_CHANGED_DURING_READ')
end)
case('stat_change',function()
 local a=api();local count=0
 a.read_stats=function()count=count+1;local s=clone(stats);s.m_nNumberOfAttacks=count==1 and 2 or 7;return s end
 eq(probe(a).reason,'ACTIVE_DERIVED_STATS_CHANGED_DURING_READ')
end)
case('caught_exception',function()
 local a=api();a.read_ability=function()error('native exception')end
 eq(probe(a).reason,'FAILED_ADAPTER_read_ability')
end)
case('source_data_unchanged',function()
 local a=api();local r=probe(a);eq(r.nativeItemIdentityAuthenticated,false)
 eq(r.manualOrderOriginVerified,false);eq(r.epsQueueVerified,false)
 eq(r.fullActiveEffectsFingerprintVerified,false)
 eq(r.derivedStatsFingerprintIsCompleteEffectState,false)
 eq(r.currentActionPreserved,true);eq(r.ordersSent,0)
end)
case('action30_candidate_only',function()
 local a=api();a.read_event=function()return {actor=2,target=3,action=30} end
 eq(probe(a).status,'CURRENT_ATTACK_NATIVE_READ_CANDIDATE_RO')
end)
print('BGXAI_R18_LUA_MOCK_PASS',cases)
