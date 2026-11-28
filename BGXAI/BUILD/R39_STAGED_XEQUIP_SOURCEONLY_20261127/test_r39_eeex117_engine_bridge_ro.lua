-- Tests the *missing* native binding only, not V3/R37/084 logic again.
local M=assert(loadfile('BGXAI_R39_EEEX117_ENGINE_BRIDGE_RO.lua'))()
local tests=0
local function check(label,fn)
 tests=tests+1
 local ok,err=pcall(fn)
 if not ok then error(label..': '..tostring(err)) end
end
local function eq(a,b)assert(a==b,tostring(a)..' ~= '..tostring(b))end
local function fixture(opts)
 opts=opts or {}
 local items={}
 items[20]={cResRef={get=function()return 'STAF01'end},m_flags=1,
   m_useCount1=0,m_useCount2=0,m_useCount3=0}
 local eqp={m_items={get=function(_,i)return items[i] end}}
 local stats={m_nKit=16384,m_nSTR=12}
 local actor={m_id=1002,m_typeAI={m_Class=3},m_equipment=eqp,
    getActiveStats=function()return stats end}
 local selected={1002}
 local ports={getPortraitSprite=function()return actor end,
   getPortraitID=function()return actor.m_id end,
   getSelectedIDs=function()return selected end,
   evalNativeTrigger=function()return true end}
 return ports,actor,items,stats,selected
end
local function hold(x)assert(x.canArm==false and x.installed==false and
 x.ordersSent==0 and x.localsWritten==0 and x.dispatchAuthorized==false)
end
check('exact physical gate seen but no authorization',function()
 local p=fixture();local r=M.probe(p)
 eq(r.status,'PARTIAL_ENGINE_PHYSICAL_AND_TRIGGER_MATCH_NO_ARM')
 eq(r.nativeTriggerSamples,12)
 assert(r.physicalSnapshotMatched==true and r.actorIdentityDoubleRead==true)
 assert(r.engineUsabilityProven==false and r.activeEffectsFullyChecked==false)
 hold(r)
end)
check('missing native evaluator',function()
 local p=fixture();p.evalNativeTrigger=nil
 local r=M.probe(p);eq(r.status,'HOLD_REQUIRED_EEEX_PORTS_UNAVAILABLE');hold(r)
end)
check('multi-selected party refused',function()
 local p,a,it,st,selected=fixture();selected[2]=15
 local r=M.probe(p);eq(r.status,'HOLD_SELECTION_NOT_EXACTLY_THIS_ACTOR');hold(r)
end)
check('wrong actor portrait refused',function()
 local p=fixture();p.getPortraitID=function()return 999 end
 local r=M.probe(p);eq(r.status,'HOLD_PORTRAIT_ACTOR_ID');hold(r)
end)
check('wrong kit refused',function()
 local p,a,it,st=fixture();st.m_nKit=5
 local r=M.probe(p);eq(r.status,'HOLD_KIT_OR_STRENGTH_NOT_MATCHED');hold(r)
end)
check('wrong class refused',function()
 local p,a=fixture();a.m_typeAI.m_Class=4
 local r=M.probe(p);eq(r.status,'HOLD_ACTOR_NOT_CLERIC');hold(r)
end)
check('duplicate item refused',function()
 local p,a,it=fixture();it[24]=it[20]
 local r=M.probe(p);eq(r.status,'HOLD_SOURCE_TARGET_OR_ITEM_UNIQUENESS_CHANGED');hold(r)
end)
check('fist slot10 excluded and no false item duplicates',function()
 local p,a,it=fixture();it[10]=it[20]
 local r=M.probe(p);eq(r.status,'PARTIAL_ENGINE_PHYSICAL_AND_TRIGGER_MATCH_NO_ARM');hold(r)
end)
check('target occupied refused',function()
 local p,a,it=fixture();it[35]=it[20]
 local r=M.probe(p);eq(r.status,'HOLD_SOURCE_TARGET_OR_ITEM_UNIQUENESS_CHANGED');hold(r)
end)
check('shield occupies offhand refused',function()
 local p,a,it=fixture();it[9]={cResRef={get=function()return 'SHLD01'end},m_flags=1,m_useCount1=0,m_useCount2=0,m_useCount3=0}
 local r=M.probe(p);eq(r.status,'HOLD_SOURCE_TARGET_OR_ITEM_UNIQUENESS_CHANGED');hold(r)
end)
check('bad item charges refused',function()
 local p,a,it=fixture();it[20].m_useCount1=1
 local r=M.probe(p);eq(r.status,'HOLD_SOURCE_TARGET_OR_ITEM_UNIQUENESS_CHANGED');hold(r)
end)
check('native trigger false refused',function()
 local p=fixture();p.evalNativeTrigger=function(t)if t=='ActionListEmpty()' then return false else return true end end
 local r=M.probe(p);eq(r.status,'HOLD_NATIVE_TRIGGER_FALSE_OR_UNKNOWN');eq(r.trigger,'ActionListEmpty()');hold(r)
end)
check('native trigger unknown refused',function()
 local p=fixture();p.evalNativeTrigger=function()return 1 end
 local r=M.probe(p);eq(r.status,'HOLD_NATIVE_TRIGGER_FALSE_OR_UNKNOWN');hold(r)
end)
check('native trigger exception refused',function()
 local p=fixture();p.evalNativeTrigger=function()error('engine')end
 local r=M.probe(p);eq(r.status,'HOLD_NATIVE_TRIGGER_FALSE_OR_UNKNOWN');hold(r)
end)
check('actor changed after eval refused',function()
 local p=fixture();local count=0
 p.getPortraitSprite=function()count=count+1;if count==1 then return p.actor end end
 -- Use actual captured sprite from a separate known-safe fixture
 local pp,a=fixture();p.getPortraitSprite=function()count=count+1;return count==1 and a or {} end
 local r=M.probe(p);eq(r.status,'HOLD_ACTOR_CHANGED_IN_PROBE');hold(r)
end)
check('slot mutation detected',function()
 local p,a,it=fixture();local n=0
 p.evalNativeTrigger=function(t) n=n+1;if n==12 then it[20]=nil end;return true end
 local r=M.probe(p);eq(r.status,'HOLD_SOURCE_TARGET_OR_ITEM_UNIQUENESS_CHANGED');hold(r)
end)
check('unavailable installed APIs refused',function()
 local r=M.probeInstalledEEex();eq(r.status,'HOLD_INSTALLED_EEEX117_REQUIRED_APIS_MISSING');hold(r)
end)
check('no source autohooks or arms',function()
 eq(M.registered,false);eq(M.sourceOnly,true);eq(M.ordersSent,0)
 hold(M.getStatus())
end)


local function scriptsFixture()
 local a={m_id=1002,m_typeAI={m_Class=3},getActiveStats=function()return {m_nKit=16384}end}
 local scripts={[0]='BDDEFAI',[1]='',[2]='',[4]='PRIEST1',[5]='',[6]='',[7]=''}
 local ports={getPortraitSprite=function()return a end,
   getPortraitID=function()return 1002 end,
   getScriptLevelResRef=function(_,level)return scripts[level] end}
 return ports,a,scripts
end
check('script assignment: native EEex resref list observed without deploy',function()
 local p=scriptsFixture();local r=M.probeScriptAssignments(p)
 eq(r.status,'R39_SCRIPT_RESREFS_OBSERVED_NO_DEPLOY')
 eq(r.bddefaiAssigned,true);eq(r.bddefaiAssignedLevels[1],0)
 eq(r.scriptLevelResrefs[4],'PRIEST1')
 eq(r.actualBcsExecutionVerified,false);eq(r.scriptSlotOwnershipVerified,false)
 hold(r)
end)
check('script assignment: BDDEFAI absent still NO deploy',function()
 local p,a,s=scriptsFixture();s[0]='DEFAULT'
 local r=M.probeScriptAssignments(p)
 eq(r.status,'R39_SCRIPT_RESREFS_OBSERVED_NO_DEPLOY')
 eq(r.bddefaiAssigned,false);hold(r)
end)
check('script assignment: unknown scripting API refused',function()
 local p=scriptsFixture();p.getScriptLevelResRef=nil
 local r=M.probeScriptAssignments(p)
 eq(r.status,'HOLD_SCRIPT_ASSIGNMENT_APIS_UNAVAILABLE');hold(r)
end)
check('script assignment: actor mismatch refused',function()
 local p=scriptsFixture();p.getPortraitID=function()return 20 end
 local r=M.probeScriptAssignments(p);eq(r.status,'HOLD_SCRIPT_ASSIGNMENT_ACTOR_ID');hold(r)
end)
check('script assignment: wrong class refused',function()
 local p,a=scriptsFixture();a.m_typeAI.m_Class=4
 local r=M.probeScriptAssignments(p);eq(r.status,'HOLD_SCRIPT_ASSIGNMENT_CLASS_OR_KIT');hold(r)
end)
check('script assignment: malformed resref refused',function()
 local p,a,s=scriptsFixture();s[4]='TOO_LONG_NAME'
 local r=M.probeScriptAssignments(p);eq(r.status,'HOLD_SCRIPT_RESREF_UNREADABLE');hold(r)
end)
check('script assignment: change across double read refused',function()
 local p,a,s=scriptsFixture();local n=0
 p.getScriptLevelResRef=function(_,level)
  if level==0 then n=n+1;if n>1 then return 'DEFAULT' end end
  return s[level]
 end
 local r=M.probeScriptAssignments(p);eq(r.status,'HOLD_SCRIPT_RESREF_CHANGED');hold(r)
end)
check('script assignment: portrait changes between reads refused',function()
 local p,a=scriptsFixture();local n=0
 p.getPortraitSprite=function()n=n+1;return n==1 and a or {} end
 local r=M.probeScriptAssignments(p);eq(r.status,'HOLD_SCRIPT_ACTOR_CHANGED');hold(r)
end)
print('BGXAI R39 EEex117 engine bridge RO '..tests..'/'..tests..' PASS')
