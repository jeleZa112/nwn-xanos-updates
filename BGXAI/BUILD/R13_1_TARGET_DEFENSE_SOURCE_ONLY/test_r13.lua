local R=dofile('BGXAI_R13_TARGET_DEFENSE_OBSERVER.lua')
local function clone(t)
 if type(t)~='table' then return t end
 local out={} for k,v in pairs(t) do out[k]=clone(v) end return out
end
local COUNT=0
local function T(name,fn)
 local ok,err=pcall(fn)
 if not ok then error('FAIL '..name..' '..tostring(err)) end
 COUNT=COUNT+1;print('PASS '..COUNT..' '..name)
end
local function fixture()
 local item={resref='SW1H04'}
 local s={m_id=111,m_equipment={m_selectedWeapon=35,m_selectedWeaponAbility=0,m_items={get=function(_,slot)return item end}}}
 local a={m_actionID=3,m_acteeID={m_Instance=222}}
 local t={m_id=222,m_bAllowEffectListCall=1,isSprite=function() return true end}
 local stats={m_nArmorClass=-2,m_nACCrushingMod=2,m_nACMissileMod=-4,
  m_nACPiercingMod=-1,m_nACSlashingMod=0,m_nResistCrushing=30,
  m_nResistPiercing=0,m_nResistSlashing=50,m_nResistMissile=40}
 local api={GameObject_Get=function(id)if id==222 then return t end end,
  GetActiveStats=function()return stats end}
 local ctx={sessionId='S1',snapshotId='snap001',sequence=1,
  actor=111,targetActor=222,actionRaw=3,selectedSlot=35,selectedAbility=0,
  readOnlyContextOnly=true,switchAttempted=false,manualEPSBoundaryProven=false}
 return s,a,api,ctx,stats,t,item
end
local function safety(o)
 assert(o.installed==false and o.readOnly==true and o.executable==false)
 assert(o.weaponSwitchAuthorized==false and o.dispatchAuthorized==false and o.rankingAuthorized==false)
 assert(o.ordersSent==0 and o.actionQueueCleared==false and o.currentActionPreserved==true)
 assert(o.gameFilesModified==false and o.nativeEvidenceAuthenticated==false)
 assert(o.liveReadVerified==false and o.runtimeApiAuthenticated==false)
 assert(o.manualOrderProven==false and o.epsQueueProven==false)
 assert(o.eligibleForR10Model==false and o.eligibleForR12HitChance==false)
 assert(o.exactHitChanceProven==false and o.hostileTargetProven==false)
end
local function call(modifier)
 local s,a,api,c,stats,t,item=fixture()
 if modifier then modifier(s,a,api,c,stats,t,item) end
 local o=R.inspect(s,a,api,c);safety(o);return o
end
T('full nine raw defense fields',function()
 local o=call();assert(o.status=='TARGET_RAW_DEFENSE_FIELDS_CANDIDATE_ONLY')
 assert(o.rawFields.m_nArmorClass==-2 and o.rawFields.m_nACMissileMod==-4)
 assert(o.rawFields.m_nResistSlashing==50 and o.rawFields.m_nResistMissile==40 and o.rawDefenseFieldsComplete==true)
 assert(o.actualTargetHitProbability==nil and o.nativeItemDamageTypeUnknown)
end)
T('missing optional defense stat partial',function()
 local o=call(function(_,_,_,_,stat)stat.m_nACMissileMod=nil end)
 assert(o.status=='TARGET_PARTIAL_DEFENSE_FIELDS_CANDIDATE_ONLY')
 assert(o.rawFields.m_nACMissileMod==false and #o.missingFields==1)
end)
T('action id 30 permitted candidate only',function()
 local o=call(function(_,a,_,c)a.m_actionID=30;c.actionRaw=30 end)
 assert(o.status=='TARGET_RAW_DEFENSE_FIELDS_CANDIDATE_ONLY')
 assert(o.attackActionProven==false)
end)
T('spell action held',function()assert(call(function(_,a,_,c)a.m_actionID=31;c.actionRaw=31 end).status=='HOLD')end)
T('actor changed held',function()assert(call(function(s)s.m_id=112 end).reason=='ACTION_CONTEXT_MISMATCH')end)
T('context source wrong held',function()assert(call(function(_,_,_,c)c.actor=112 end).reason=='ACTION_CONTEXT_MISMATCH')end)
T('target changed before held',function()assert(call(function(_,a)a.m_acteeID.m_Instance=223 end).status=='HOLD')end)
T('context target spoof held',function()assert(call(function(_,_,_,c)c.targetActor=999 end).reason=='ACTION_CONTEXT_MISMATCH')end)
T('context snapshot absent held',function()assert(call(function(_,_,_,c)c.snapshotId=nil end).reason=='CONTEXT_INCOMPLETE')end)
T('context switch attempted held',function()assert(call(function(_,_,_,c)c.switchAttempted=true end).reason=='CONTEXT_INCOMPLETE')end)
T('context claimed EPS proof held',function()assert(call(function(_,_,_,c)c.manualEPSBoundaryProven=true end).reason=='CONTEXT_INCOMPLETE')end)
T('no required API held',function()assert(call(function(_,_,api)api.GetActiveStats=nil end).reason=='REQUIRED_BASE_EEEX_ADAPTER_MISSING')end)
T('target non sprite held',function()assert(call(function(_,_,_,_,_,t)t.isSprite=function()return false end end).reason=='TARGET_NOT_A_SPRITE')end)
T('target id mismatch held',function()assert(call(function(_,_,_,_,_,t)t.m_id=13 end).reason=='TARGET_NOT_A_SPRITE')end)
T('stats reader exception held',function()assert(call(function(_,_,api)api.GetActiveStats=function()error('bad')end end).reason=='TARGET_ACTIVE_STATS_UNAVAILABLE')end)
T('stats reader nil held',function()assert(call(function(_,_,api)api.GetActiveStats=function()return nil end end).reason=='TARGET_ACTIVE_STATS_UNAVAILABLE')end)
T('selected slot mismatch held',function()assert(call(function(s)s.m_equipment.m_selectedWeapon=36 end).reason=='SELECTION_CONTEXT_MISMATCH')end)
T('selected ability mismatch held',function()assert(call(function(s)s.m_equipment.m_selectedWeaponAbility=2 end).reason=='SELECTION_CONTEXT_MISMATCH')end)
T('missing item held',function()assert(call(function(s)s.m_equipment.m_items.get=function()return nil end end).reason=='SELECTION_UNREADABLE')end)
T('ammo slot read but no launcher proof',function()
 local o=call(function(s,_,_,c)s.m_equipment.m_selectedWeapon=11;c.selectedSlot=11 end)
 assert(o.status=='TARGET_RAW_DEFENSE_FIELDS_CANDIDATE_ONLY' and o.selectedSlotIsAmmo)
 assert(o.selectedItemRefVerified==false)
end)
T('target changed during stat read held',function()
 local o=call(function(_,a,api)
  local original=api.GetActiveStats
  api.GetActiveStats=function(t)a.m_acteeID.m_Instance=333;return original(t)end
 end)
 assert(o.reason=='SOURCE_TARGET_CHANGED_DURING_READ')
end)
T('target changed between duplicate reads held',function()
 local o=call(function(_,_,api,_,stat)
  local count=0
  api.GetActiveStats=function()count=count+1;if count==2 then stat.m_nArmorClass=-4 end;return stat end
 end)
 assert(o.reason=='DEFENSE_STATS_CHANGED_DURING_READ')
end)
T('target object changed after first read held',function()
 local o=call(function(_,_,api,_,_,t)
  local other={m_id=222,isSprite=function()return true end}
  local n=0;api.GameObject_Get=function() n=n+1;return n>=3 and other or t end
 end)
 assert(o.status=='HOLD')
end)
T('replaced selected item during read held',function()
 local o=call(function(s,_,api)
  local orig=api.GetActiveStats
  api.GetActiveStats=function(t)s.m_equipment.m_items.get=function()return {} end;return orig(t)end
 end)
 assert(o.reason=='SOURCE_TARGET_CHANGED_DURING_READ')
end)
T('NaN in defensive reading partial',function()
 local o=call(function(_,_,_,_,stat)stat.m_nArmorClass=0/0 end)
 assert(o.status=='TARGET_PARTIAL_DEFENSE_FIELDS_CANDIDATE_ONLY' and o.rawFields.m_nArmorClass==false)
end)
T('noninteger ac partial',function()
 local o=call(function(_,_,_,_,stat)stat.m_nArmorClass=2.5 end)
 assert(o.status=='TARGET_PARTIAL_DEFENSE_FIELDS_CANDIDATE_ONLY')
end)
T('out of range resistance partial',function()
 local o=call(function(_,_,_,_,stat)stat.m_nResistPiercing=999999 end)
 assert(o.rawFields.m_nResistPiercing==false)
end)
T('source nil held safe',function()
 local o=R.inspect(nil,{}, {}, {});safety(o);assert(o.status=='HOLD')
end)
T('action nil held safe',function()
 local o=R.inspect({},nil, {}, {});safety(o);assert(o.status=='HOLD')
end)
T('non-string session held',function()assert(call(function(_,_,_,c)c.sessionId={} end).reason=='CONTEXT_INCOMPLETE')end)
T('empty stats table partial',function()
 local o=call(function(_,_,api)api.GetActiveStats=function()return {} end end)
 assert(o.status=='TARGET_PARTIAL_DEFENSE_FIELDS_CANDIDATE_ONLY' and #o.missingFields==9)
end)
T('selected resref not claimed',function()
 local o=call();assert(o.selectedItemRefVerified==false and o.alternateSlotAPRVerified==false)
end)
T('all safety flags unchanged on a second run',function()
 local o=call();local o2=call();safety(o);safety(o2);assert(o2.status==o.status)
end)
T('missing missile resistance partial never guessed',function()
 local o=call(function(_,_,_,_,stats)stats.m_nResistMissile=nil end)
 assert(o.status=='TARGET_PARTIAL_DEFENSE_FIELDS_CANDIDATE_ONLY')
 assert(o.rawFields.m_nResistMissile==false and #o.missingFields==1)
 assert(o.eligibleForR10Model==false and o.weaponSwitchAuthorized==false)
end)
T('missile resistance modified between reads held',function()
 local o=call(function(_,_,api,_,stats)
  local n=0
  api.GetActiveStats=function()n=n+1;if n==2 then stats.m_nResistMissile=95 end;return stats end
 end)
 assert(o.status=='HOLD' and o.reason=='DEFENSE_STATS_CHANGED_DURING_READ')
end)
T('missile resistance out of bounds partial',function()
 local o=call(function(_,_,_,_,stats)stats.m_nResistMissile=9999 end)
 assert(o.status=='TARGET_PARTIAL_DEFENSE_FIELDS_CANDIDATE_ONLY')
 assert(o.rawFields.m_nResistMissile==false)
end)
-- Real observed BGXAI actor actions were AttackOneRound (105) and
-- AttackReevaluate (134); old R13 allowed only 3/30. Verify both read only.
T('real AttackOneRound 105 now binds actual hostile-candidate target',function()
 local o=call(function(_,a,_,c) a.m_actionID=105;c.actionRaw=105 end)
 assert(o.status=='TARGET_RAW_DEFENSE_FIELDS_CANDIDATE_ONLY')
 assert(o.rawActionId==105 and o.targetActor==222)
 assert(o.activeStatsNotTempDoubleRead==true and o.hostileTargetProven==false)
end)
T('real AttackReevaluate 134 now binds candidate target',function()
 local o=call(function(_,a,_,c)a.m_actionID=134;c.actionRaw=134 end)
 assert(o.status=='TARGET_RAW_DEFENSE_FIELDS_CANDIDATE_ONLY')
 assert(o.rawActionId==134 and o.dispatchAuthorized==false)
end)
T('weapon ability selection action 92 not assumed an attack',function()
 local o=call(function(_,a,_,c)a.m_actionID=92;c.actionRaw=92 end)
 assert(o.status=='HOLD' and o.reason=='NOT_AN_ATTACK_CANDIDATE_ACTION')
end)
T('temporary target-derived stats during effect list HOLD',function()
 local o=call(function(_,_,_,_,_,target)target.m_bAllowEffectListCall=0 end)
 assert(o.status=='HOLD' and o.reason=='TARGET_ACTIVE_STATS_TEMP_OR_EFFECTS_IN_PROGRESS')
end)
T('unreadable active stats guard held',function()
 local o=call(function(_,_,_,_,_,target)target.m_bAllowEffectListCall=nil end)
 assert(o.status=='HOLD' and o.reason=='TARGET_ACTIVE_STATS_TEMP_OR_EFFECTS_IN_PROGRESS')
end)
T('target derived-stats processing switched during read HOLD',function()
 local o=call(function(_,_,api,_,_,target)
   local before=api.GetActiveStats
   api.GetActiveStats=function(t)target.m_bAllowEffectListCall=2;return before(t)end
 end)
 assert(o.status=='HOLD' and o.reason=='TARGET_ACTIVE_STATS_GUARD_CHANGED')
end)
T('real attack action target changed midread cannot be ranked',function()
 local o=call(function(_,act,api,ctx)
   act.m_actionID=105;ctx.actionRaw=105
   local before=api.GetActiveStats
   api.GetActiveStats=function(target)act.m_acteeID.m_Instance=333;return before(target)end
 end)
 assert(o.status=='HOLD' and o.reason=='SOURCE_TARGET_CHANGED_DURING_READ')
end)
print(('R13 %d/%d PASS'):format(COUNT,COUNT))
