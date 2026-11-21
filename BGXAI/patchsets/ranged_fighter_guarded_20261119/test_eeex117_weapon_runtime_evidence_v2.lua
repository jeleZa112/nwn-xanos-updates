-- EEex 1.1.7 runtime evidence observer V2 unit tests; mocked sprites only.
local root=(arg and arg[0] or ''):match('^(.*[/\\])') or './'
local M=dofile(root..'BGXAI_EEEX117_WEAPON_RUNTIME_EVIDENCE_V2.lua')
local count=0
local function eq(a,b) assert(a==b,tostring(a)..' ~= '..tostring(b)) end
local function test(label,fn) fn();count=count+1;print('PASS '..label) end
local function mk(flag,slot)
 local calls=0
 local obj={m_id=251,m_equipment={m_selectedWeapon=slot or 36},
   m_bAllowEffectListCall=flag or 1,m_curAction={m_actionID=105},
   m_curScriptNum=6,getActiveStats=function(self)
     calls=calls+1;return {m_derivedStats=true}
   end}
 return obj,function() return calls end
end
local function sample(sprite)
 return M.observe_portrait(0,function()return sprite end)
end
test('raw selected weapon observed while attacking; no interruption',function()
 local s,calls=mk(1,36);local r=sample(s)
 eq(r.status,'OBSERVED_RAW_SELECTED_AND_ACTIVE_STATS_CONTEXT_ONLY')
 eq(r.raw.selectedWeaponRaw,36);eq(r.raw.actionIdRaw,105)
 eq(r.raw.activeStatsBranch,'DERIVED_STATS_PATH')
 eq(calls(),1);eq(s.m_curAction.m_actionID,105)
 eq(r.currentActionPreserved,true);eq(r.ordersSent,0)
end)
test('read-only observes temp branch during effects-list processing',function()
 local s=mk(1);s.m_bAllowEffectListCall=0
 local r=sample(s)
 eq(r.raw.activeStatsBranch,'TEMP_STATS_PATH')
 eq(r.canSwitchWeapon,false);eq(r.completeBuffEffectsObserved,false)
end)
test('actionID zero proves neither empty EPS queue nor manual provenance',function()
 local s=mk(1);s.m_curAction.m_actionID=0
 local r=sample(s)
 eq(r.raw.actionIdRaw,0);eq(r.manualOrderOriginVerified,false)
 eq(r.epsQueueVerifiedEmpty,false);eq(r.dispatchAuthorized,false)
end)
test('selection change invalidates only weapon advice',function()
 local a=sample(mk(1,35));local b=sample(mk(1,36))
 local r=M.compare(a,b);eq(r.status,'INVALIDATE_WEAPON_ADVICE_KEEP_CURRENT_ACTION')
 eq(r.selectedWeaponChanged,true);eq(r.currentActionPreserved,true)
end)
test('effect-list branch change invalidates previous estimate',function()
 local a=sample(mk(1,35))
 local s=mk(1,35);s.m_bAllowEffectListCall=0
 local r=M.compare(a,sample(s))
 eq(r.status,'INVALIDATE_WEAPON_ADVICE_KEEP_CURRENT_ACTION')
 eq(r.activeStatsBranchChanged,true)
end)
test('same raw context cannot certify buff stability',function()
 local a=sample(mk(1,35));local b=sample(mk(1,35))
 local r=M.compare(a,b)
 eq(r.status,'RAW_CONTEXT_UNCHANGED_BUFFS_STILL_UNKNOWN')
 eq(r.completeBuffEffectsObserved,false);eq(r.canSwitchWeapon,false)
end)
test('invalid portrait index never fetches actor',function()
 local calls=0
 local r=M.observe_portrait(6,function()calls=calls+1;return mk(1)end)
 eq(r.status,'HOLD_INVALID_PORTRAIT');eq(calls,0)
end)
test('nil portrait does not raise or dispatch',function()
 local r=M.observe_portrait(0,function()return nil end)
 eq(r.status,'HOLD_NO_SPRITE');eq(r.ordersSent,0)
end)
test('getter failure is fail-closed',function()
 local r=M.observe_portrait(0,function()error('unavailable')end)
 eq(r.status,'HOLD_NO_SPRITE')
end)
test('missing selected slot cannot be mistaken for fists',function()
 local s=mk(1);s.m_equipment={}
 local r=sample(s);eq(r.status,'HOLD_SELECTED_WEAPON_OR_ID_UNAVAILABLE')
end)
test('missing stats context holds',function()
 local s=mk(1);s.getActiveStats=nil
 local r=sample(s);eq(r.status,'HOLD_ACTIVE_STATS_CONTEXT_UNAVAILABLE')
end)
test('derived stats getter throws => no false proof',function()
 local s=mk(1);s.getActiveStats=function()error('recompute')end
 local r=sample(s);eq(r.status,'HOLD_ACTIVE_STATS_CONTEXT_UNAVAILABLE')
end)
test('unknown effect-list flag stays unknown',function()
 local s=mk(1);s.m_bAllowEffectListCall=nil
 local r=sample(s);eq(r.status,'HOLD_ACTIVE_STATS_CONTEXT_UNAVAILABLE')
end)
test('actor identity mismatch cannot reuse prior observation',function()
 local a=sample(mk(1));local s=mk(1);s.m_id=252
 local r=M.compare(a,sample(s));eq(r.status,'HOLD_INCOMPARABLE_RAW_OBSERVATIONS')
end)
test('LIVE actor id 139135050 passes 31-bit actor guard',function()
 local s=mk(1,12);s.m_id=139135050
 local r=sample(s)
 eq(r.status,'OBSERVED_RAW_SELECTED_AND_ACTIVE_STATS_CONTEXT_ONLY')
 eq(r.raw.actorId,139135050);eq(r.raw.selectedWeaponRaw,12)
 eq(r.dispatchAuthorized,false)
end)
test('LIVE id and 12-to-35 selected slot change only invalidates advice',function()
 local a=mk(1,12);a.m_id=139135050
 local b=mk(1,35);b.m_id=139135050
 local r=M.compare(sample(a),sample(b))
 eq(r.status,'INVALIDATE_WEAPON_ADVICE_KEEP_CURRENT_ACTION')
 eq(r.selectedWeaponChanged,true);eq(r.currentActionPreserved,true)
 eq(r.ordersSent,0)
end)
test('31-bit range overflow stops',function()
 local s=mk(1,35);s.m_id=2147483648
 local r=sample(s)
 eq(r.status,'HOLD_SELECTED_WEAPON_OR_ID_UNAVAILABLE')
 eq(r.dispatchAuthorized,false)
end)
test('no writes occur to mocked game sprite',function()
 local s=mk(1);local before={id=s.m_id,slot=s.m_equipment.m_selectedWeapon,
  action=s.m_curAction.m_actionID,flag=s.m_bAllowEffectListCall}
 for i=1,20 do sample(s) end
 eq(s.m_id,before.id);eq(s.m_equipment.m_selectedWeapon,before.slot)
 eq(s.m_curAction.m_actionID,before.action)
 eq(s.m_bAllowEffectListCall,before.flag)
end)
print('PASS EEEX117 RUNTIME EVIDENCE '..count..'/'..count..' OFFLINE ONLY')
