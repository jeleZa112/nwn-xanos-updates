-- Native Lua offline continuity tests. No game actions or hooks.
local root=(arg and arg[0] or ''):match('^(.*[/\\])') or './'
local M=dofile(root..'BGXAI_WEAPON_NONINTERRUPT_PLAN_V1.lua')
local function copy(v) if type(v)~='table' then return v end local o={} for k,x in pairs(v) do o[k]=copy(x) end return o end
local function eq(a,b) assert(a==b,tostring(a)..' != '..tostring(b)) end
local function sample()
 return {frame={tick=100,snapshotId='F100',area='AR1',actorId='P1',enemyId='E1',
    equipmentFingerprint='EQ1',protectionFingerprint='PR1',combatFingerprint='CB1',
    effectStatusFingerprint='EF1',selectedWeaponId='DART'},
  actor={actorId='P1',selectedWeaponId='DART',manualOrderActive=false,epsBusy=false,
   healingReserved=false,currentlyCasting=false,originVerified='AI',
   activeStatsEvidence={actorId='P1',snapshotId='F100',tick=100,
    activeFingerprint='ACTIVE1',buffFingerprint='BUFF1'}},
  quickslotIds={'SWORD','DART',false,false}}
end
local function score(s,prev)
 local n={signature='MODEL',lastTick=s.frame.tick,lastAdviceTick=prev and prev.lastAdviceTick or nil}
 if not prev then return {status='HOLD_STABILIZE_TARGET_AND_EQUIPMENT',next=n,
   executable=false,dispatchAuthorized=false,passivePreview=true} end
 if prev.lastAdviceTick then return {status='HOLD_ADVISORY_SWITCH_COOLDOWN',next=n,
   executable=false,dispatchAuthorized=false,passivePreview=true} end
 n.lastAdviceTick=s.frame.tick
 return {status='PASSIVE_RANKING_SUGGESTS_SLOT',fromWeaponId='DART',
   toWeaponId='SWORD',slotIndex=0,targetId=s.frame.enemyId,
   next=n,executable=false,dispatchAuthorized=false,passivePreview=true}
end
local function advance(s)
 local n=copy(s);n.frame.tick=n.frame.tick+1
 n.frame.snapshotId='F'..n.frame.tick
 n.actor.activeStatsEvidence.snapshotId=n.frame.snapshotId
 n.actor.activeStatsEvidence.tick=n.frame.tick
 return n
end
local count=0
local function test(n,fn) fn();count=count+1;print('PASS '..n) end
local function first_two(s,fn)
 local r=M.step(s,nil,fn or score);local t=advance(s)
 return r,M.step(t,r.next,fn or score),t
end
test('recalculation preserves action; never clears queue',function()
 local s=sample();local r=M.step(s,nil,score)
 eq(r.status,'CONTINUE_CURRENT_ACTION_RECALCULATING')
 eq(r.actionQueueCleared,false);eq(r.currentActionPreserved,true)
 eq(r.ordersSent,0);eq(r.localsWritten,0);eq(r.executable,false)
end)
test('background planning while attack in progress',function()
 local s=sample();s.activity={snapshotId='F100',actorId='P1',tick=100,
  rawActionId=105,source='RAW_EEEX'}
 local _,b=first_two(s)
 eq(b.status,'CONTINUE_CURRENT_ACTION_SWITCH_PENDING')
 eq(b.proposedSlotIndex,0);eq(b.dispatchAuthorized,false)
end)
test('manual action is never overwritten by a pending plan',function()
 local s=sample();s.actor.manualOrderActive=true;s.actor.originVerified='UNKNOWN'
 local _,b=first_two(s);eq(b.status,'CONTINUE_CURRENT_ACTION_SWITCH_PENDING')
 eq(b.ordersSent,0);eq(b.currentActionPreserved,true)
end)
test('spellcasting or EPS healing stays uninterrupted',function()
 local s=sample();s.actor.epsBusy=true;s.actor.healingReserved=true;s.actor.currentlyCasting=true
 local _,b=first_two(s)
 eq(b.status,'CONTINUE_CURRENT_ACTION_SWITCH_PENDING')
 eq(b.dispatchAuthorized,false);eq(b.ordersSent,0)
end)
test('buff expiration invalidates pending plan but not current action',function()
 local _,b,s=first_two(sample())
 local c=advance(s);c.actor.activeStatsEvidence.buffFingerprint='BUFF_EXPIRED'
 local r=M.step(c,b.next,score)
 eq(r.status,'CONTINUE_CURRENT_ACTION_RECALCULATING')
 assert(r.next.pending==nil);eq(r.currentActionPreserved,true)
end)
test('strength APR change invalidates pending plan',function()
 local _,b,s=first_two(sample());local c=advance(s)
 c.actor.activeStatsEvidence.activeFingerprint='NEW_APR_OR_STRENGTH'
 local r=M.step(c,b.next,score);assert(r.next.pending==nil)
 eq(r.status,'CONTINUE_CURRENT_ACTION_RECALCULATING')
end)
test('changed target, protection, inventory all invalidate',function()
 for _,change in ipairs({'enemyId','protectionFingerprint','equipmentFingerprint'}) do
  local _,b,s=first_two(sample());local c=advance(s)
  c.frame[change]='CHANGED'
  local r=M.step(c,b.next,score)
  eq(r.status,'CONTINUE_CURRENT_ACTION_RECALCULATING');assert(r.next.pending==nil)
 end
end)
test('cooldown retains pending but does not stop attacks',function()
 local _,b,s=first_two(sample());local c=advance(s)
 local r=M.step(c,b.next,score)
 eq(r.status,'CONTINUE_CURRENT_ACTION_SWITCH_PENDING')
 eq(r.proposedWeaponId,'SWORD');eq(r.currentActionPreserved,true)
end)
test('m_actionID zero is not idle certification',function()
 local s=sample();s.activity={snapshotId='F100',actorId='P1',tick=100,
  rawActionId=0,source='RAW_EEEX'}
 local _,b=first_two(s);eq(b.status,'CONTINUE_CURRENT_ACTION_SWITCH_PENDING')
end)
test('even hypothetically proven safe boundary is advisory only',function()
 local s=sample();local _,b,scene=first_two(s)
 local c=advance(scene);c.activity={source='INDEPENDENTLY_AUDITED_EEEX_EPS_ACTIVITY',
  snapshotId=c.frame.snapshotId,actorId='P1',tick=c.frame.tick,
  provenNoManualOrder=true,provenEpsFree=true,provenActionBoundary=true,
  provenAttackRecoveryComplete=true,provenNoCasting=true,
  provenNoHealing=true,provenNoQueuedAction=true}
 local r=M.step(c,b.next,score)
 eq(r.status,'ADVISORY_SAFE_BOUNDARY_OBSERVED_NO_DISPATCH')
 eq(r.executable,false);eq(r.ordersSent,0);eq(r.actionQueueCleared,false)
end)
test('missing one safe-window proof keeps action in progress',function()
 local _,b,s=first_two(sample());local c=advance(s)
 c.activity={source='INDEPENDENTLY_AUDITED_EEEX_EPS_ACTIVITY',
  snapshotId=c.frame.snapshotId,actorId='P1',tick=c.frame.tick,
  provenNoManualOrder=true,provenEpsFree=true,provenActionBoundary=true,
  provenAttackRecoveryComplete=true,provenNoCasting=true,
  provenNoHealing=true,provenNoQueuedAction=false}
 eq(M.step(c,b.next,score).status,'CONTINUE_CURRENT_ACTION_SWITCH_PENDING')
end)
test('forged executable scorer cannot produce plan',function()
 local bad=function()return {status='PASSIVE_RANKING_SUGGESTS_SLOT',
  executable=true,dispatchAuthorized=true}end
 eq(M.step(sample(),nil,bad).status,'HOLD_SCORER_RESULT_UNTRUSTED')
end)
test('wrong-slot or target suggestion rejected',function()
 local s=sample()
 local bad=function(_,prev)
  return {status='PASSIVE_RANKING_SUGGESTS_SLOT',
   fromWeaponId='DART',toWeaponId='SWORD',slotIndex=3,
   targetId='DIFFERENT',next={lastTick=100},
   executable=false,dispatchAuthorized=false,passivePreview=true}
 end
 eq(M.step(s,nil,bad).status,'HOLD_RANKING_SLOT_OR_TARGET_MISMATCH')
end)
test('scorer errors hold without any action',function()
 eq(M.step(sample(),nil,function()error('simulated')end).status,'HOLD_SCORER_RESULT_UNTRUSTED')
end)
test('no scorer -> hold; no action',function()
 local r=M.step(sample(),nil,nil)
 eq(r.status,'HOLD_READONLY_SCORER_NOT_CONNECTED')
 eq(r.ordersSent,0)
end)
test('stale/duplicate/out-of-order tick drops pending plan',function()
 local _,b,s=first_two(sample());local same=copy(s)
 eq(M.step(same,b.next,score).status,'CONTINUE_CURRENT_ACTION_RECALCULATING')
end)
test('ranker KEEP_CURRENT drops pending',function()
 local _,b,s=first_two(sample());local c=advance(s)
 local f=function() return {status='KEEP_CURRENT',executable=false,dispatchAuthorized=false,passivePreview=true}
 end
 local r=M.step(c,b.next,f)
 eq(r.status,'CONTINUE_CURRENT_ACTION_KEEP_WEAPON');assert(r.next.pending==nil)
end)
test('no input mutation on successful ranking',function()
 local s=sample();local before=s.frame.tick..s.actor.activeStatsEvidence.buffFingerprint
 local _,b=first_two(s)
 eq(s.frame.tick..s.actor.activeStatsEvidence.buffFingerprint,before)
 eq(b.next.pending.toWeaponId,'SWORD')
end)
local function certifyCache(s)
 s.cacheEvidence={source='INDEPENDENTLY_AUDITED_FULL_WEAPON_CACHE_SNAPSHOT',
  snapshotId=s.frame.snapshotId,actorId=s.frame.actorId,tick=s.frame.tick,
  allRelevantStateFingerprintComplete=true,ammoAndItemEffectsCovered=true,
  activeBuffsCovered=true,targetProtectionsCovered=true}
end
test('pending plan skips redundant scoring for unchanged 4 ticks',function()
 local calls=0
 local wrapped=function(s,p) calls=calls+1;return score(s,p) end
 local s=sample()
 local a=M.step(s,nil,wrapped)
 local s2=advance(s)
 local b=M.step(s2,a.next,wrapped)
 eq(b.status,'CONTINUE_CURRENT_ACTION_SWITCH_PENDING')
 eq(calls,2)
 for j=1,4 do
  s2=advance(s2);certifyCache(s2)
  b=M.step(s2,b.next,wrapped)
  eq(b.status,'CONTINUE_CURRENT_ACTION_SWITCH_PENDING')
  eq(b.scorerCalls,0)
  eq(b.ordersSent,0)
 end
 eq(calls,2)
 s2=advance(s2)
 b=M.step(s2,b.next,wrapped)
 eq(calls,3)
end)
test('changed buff invalidates cache, recomputes without stopping attack',function()
 local calls=0
 local wrapped=function(s,p)calls=calls+1;return score(s,p)end
 local s=sample()
 local a=M.step(s,nil,wrapped)
 s=advance(s);local b=M.step(s,a.next,wrapped)
 s=advance(s);certifyCache(s);b=M.step(s,b.next,wrapped)
 eq(calls,2)
 s=advance(s);s.actor.activeStatsEvidence.buffFingerprint='HASTE_ENDED'
 local c=M.step(s,b.next,wrapped)
 eq(calls,3);eq(c.status,'CONTINUE_CURRENT_ACTION_RECALCULATING')
 eq(c.currentActionPreserved,true);eq(c.ordersSent,0)
end)
test('cached plan remains nonexecutable at independently proven boundary',function()
 local s=sample();local a=M.step(s,nil,score)
 s=advance(s);local b=M.step(s,a.next,score)
 s=advance(s)
 s.activity={source='INDEPENDENTLY_AUDITED_EEEX_EPS_ACTIVITY',
  snapshotId=s.frame.snapshotId,actorId=s.frame.actorId,tick=s.frame.tick,
  provenNoManualOrder=true,provenEpsFree=true,provenActionBoundary=true,
  provenAttackRecoveryComplete=true,provenNoCasting=true,
  provenNoHealing=true,provenNoQueuedAction=true}
 certifyCache(s)
 local c=M.step(s,b.next,score)
 eq(c.scorerCalls,0);eq(c.status,'ADVISORY_SAFE_BOUNDARY_OBSERVED_NO_DISPATCH')
 eq(c.dispatchAuthorized,false);eq(c.ordersSent,0)
end)
test('changed target while cached prevents reuse of pending slot',function()
 local s=sample();local a=M.step(s,nil,score)
 s=advance(s);local b=M.step(s,a.next,score)
 s=advance(s);certifyCache(s);s.frame.enemyId='E2'
 certifyCache(s)
 local c=M.step(s,b.next,score)
 eq(c.status,'CONTINUE_CURRENT_ACTION_RECALCULATING');assert(not c.next.pending)
end)
test('R27 real queue busy preserves actions without running scorer',function()
 local s=sample();s.actor.engineActorRaw=142;s.actor.currentActionRaw=23
 s.observedR27Queue={schema='BGXAI_R27_SINGLE_CALLBACK_SELECTED_RO_V1',
  status='CURRENT_SELECTED_SAME_CALLBACK_SOURCE_CANDIDATE',
  queueSnapshotStable=true,readOnly=true,sameLuaListenerInvocation=true,
  ordersSent=0,dispatchAuthorized=false,actionOriginVerified=false,
  manualEpsQueueVerified=false,actor=142,actionRaw=23,queuedActionsRaw=3}
 local calls=0;local r=M.step(s,{pending={toWeaponId='SWORD'}},function()
  calls=calls+1;error('scorer must not run while queue busy') end)
 eq(r.status,'PRESERVE_KNOWN_NONEMPTY_ACTION_QUEUE')
 eq(calls,0);eq(r.scorerCalls,0);eq(r.queuedActionsRaw,3)
 eq(r.next,nil);eq(r.actionQueueCleared,false);eq(r.currentActionPreserved,true)
 eq(r.dispatchAuthorized,false);eq(r.ordersSent,0)
end)
test('R27 zero queue count never grants EPS or manual permission',function()
 local s=sample();s.actor.engineActorRaw=142;s.actor.currentActionRaw=0
 s.observedR27Queue={schema='BGXAI_R27_SINGLE_CALLBACK_SELECTED_RO_V1',
  status='CURRENT_SELECTED_SAME_CALLBACK_SOURCE_CANDIDATE',
  queueSnapshotStable=true,readOnly=true,sameLuaListenerInvocation=true,
  ordersSent=0,dispatchAuthorized=false,actionOriginVerified=false,
  manualEpsQueueVerified=false,actor=142,actionRaw=0,queuedActionsRaw=0}
 local calls=0
 local r=M.step(s,nil,function()calls=calls+1;return score(s,nil) end)
 eq(calls,1);eq(r.status,'CONTINUE_CURRENT_ACTION_RECALCULATING')
 eq(r.dispatchAuthorized,false)
end)
test('R27 queued count must match actor, action and strict no-dispatch flags',function()
 local s=sample();s.actor.engineActorRaw=142;s.actor.currentActionRaw=23
 s.observedR27Queue={schema='BGXAI_R27_SINGLE_CALLBACK_SELECTED_RO_V1',
  status='CURRENT_SELECTED_SAME_CALLBACK_SOURCE_CANDIDATE',
  queueSnapshotStable=true,readOnly=true,sameLuaListenerInvocation=true,
  ordersSent=0,dispatchAuthorized=false,actionOriginVerified=false,
  manualEpsQueueVerified=false,actor=142,actionRaw=23,queuedActionsRaw=5}
 local base=copy(s.observedR27Queue)
 local mutate={
  function(q)q.actor=999 end,function(q)q.actionRaw=3 end,
  function(q)q.queuedActionsRaw=-1 end,function(q)q.queuedActionsRaw=513 end,
  function(q)q.queuedActionsRaw=0.5 end,
  function(q)q.queueSnapshotStable=false end,
  function(q)q.actionOriginVerified=true end,
  function(q)q.manualEpsQueueVerified=true end,
  function(q)q.dispatchAuthorized=true end,
  function(q)q.ordersSent=1 end,
  function(q)q.sameLuaListenerInvocation=false end,
  function(q)q.status='HOLD_SINGLE_CALLBACK_NO_DISPATCH' end,
 }
 for _,alter in ipairs(mutate) do
  local q=copy(base);alter(q);s.observedR27Queue=q
  local calls=0;local r=M.step(s,nil,function()calls=calls+1;return score(s,nil) end)
  eq(calls,1);eq(r.dispatchAuthorized,false)
  assert(r.status~='PRESERVE_KNOWN_NONEMPTY_ACTION_QUEUE')
 end
end)
test('R31 real LIVE: action3 attack with raw queue zero is NOT safe idle',function()
 -- Source: 25.11.2026 real R31 12/12 capture; actionRaw=3, queueRaw=0,
 -- source pointer unavailable, origin UNKNOWN. This is NOT a claimed
 -- proof that manual/EPS action queue is empty.
 local s=sample()
 s.actor.engineActorRaw=139266124
 s.actor.currentActionRaw=3
 s.actor.originVerified='UNKNOWN'
 s.actor.manualOrderActive=nil
 s.actor.epsBusy=nil
 s.observedR27Queue={
  schema='BGXAI_R27_SINGLE_CALLBACK_SELECTED_RO_V1',
  status='CURRENT_SELECTED_SAME_CALLBACK_SOURCE_CANDIDATE',
  actor=139266124,actionRaw=3,selectedWeaponRaw=12,
  queuedActionsRaw=0,queueSnapshotStable=true,
  actionContextSnapshotStable=true,
  actionSourceReadStatus='ACTION_SOURCE_POINTER_UNAVAILABLE',
  actionSourceStable=false,actionOriginVerified=false,
  manualEpsQueueVerified=false,readOnly=true,
  sameLuaListenerInvocation=true,ordersSent=0,dispatchAuthorized=false
 }
 s.activity={source='RAW_EEEX',snapshotId='F100',actorId='P1',tick=100,
  rawActionId=3,queueCountRaw=0}
 local first=M.step(s,nil,score)
 eq(first.status,'CONTINUE_CURRENT_ACTION_RECALCULATING')
 eq(first.dispatchAuthorized,false);eq(first.ordersSent,0)
 local n=advance(s)
 n.activity.tick=n.frame.tick;n.activity.snapshotId=n.frame.snapshotId
 local second=M.step(n,first.next,score)
 eq(second.status,'CONTINUE_CURRENT_ACTION_SWITCH_PENDING')
 eq(second.proposedWeaponId,'SWORD') -- advisory only, not game dispatch
 eq(second.dispatchAuthorized,false);eq(second.ordersSent,0)
 eq(second.actionQueueCleared,false);eq(second.currentActionPreserved,true)
end)
print('PASS NONINTERRUPT SCHEDULER '..count..'/'..count..' SOURCE ONLY')
