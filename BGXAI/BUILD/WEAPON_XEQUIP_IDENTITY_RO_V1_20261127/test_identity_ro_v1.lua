local ROOT='BGXAI/BUILD/WEAPON_XEQUIP_IDENTITY_RO_V1_20261127/'
local M=dofile(ROOT..'BGXAI_XEQUIP_IDENTITY_RO_V1.lua')
local N,P,F=0,0,0
local function run(name,fn)
 N=N+1; local ok,err=pcall(fn)
 if ok then P=P+1; print('PASS '..name)
 else F=F+1; print('FAIL '..name..' '..tostring(err)) end
end
local function assertStatus(got,expected)
 assert(got.status==expected,'expected '..expected..' got '..tostring(got.status))
 assert(got.ordersSent==0 and got.localsWritten==0 and got.dispatchAuthorized==false)
 assert(got.armAuthorized==false and got.gameModified==false and got.installed==false)
 assert(got.safeActionBoundaryVerified==false)
end
local function item(rr,flags,c1,c2,c3)
 return {cResRef={get=function() return rr end},m_flags=flags or 1,
         m_useCount1=c1 or 0,m_useCount2=c2 or 0,m_useCount3=c3 or 0}
end
local function env()
 local T={[20]=item('STAF01')}
 local actor={m_id=1234,m_typeAI={m_Class=3},m_equipment={m_items={
   get=function(self,s) return T[s] end},m_selectedWeapon=35,m_selectedWeaponAbility=0}}
 local p={123,1234,345,456,567,678}
 local ctx={actorId=1234,partyIndex=1,actionRaw=0,selectedWeaponRaw=35,
            selectedAbilityRaw=0,queuedActionsRaw=0,currentScriptNumberRaw=5}
 local calls=0
 local ports={portraitId=function(i) return p[i+1] end,
   contextReader=function(s) calls=calls+1;return ctx end}
 return actor,T,p,ctx,ports,function()return calls end
end
run('genuine-shaped positive returns advisory, NEVER arm',function()
 local s,t,p,c,ports,count=env(); local r=M.capture(s,ports)
 assertStatus(r,'RUNTIME_JAGAN_INVENTORY_MATCH_READONLY_NO_ARM')
 assert(r.actorIdInMemory==1234 and r.topLevelSlotsCompared==38 and count()==2)
 assert(r.classKitItmUsabilityVerified==false and r.sessionMatchesSavedGamVerified==false)
end)
run('no actor',function()assertStatus(M.capture(nil,{}),'HOLD_MISSING_READONLY_PORTS')end)
run('no ports',function()local s=env();assertStatus(M.capture(s,{}),'HOLD_MISSING_READONLY_PORTS')end)
run('bad portrait',function()local s,t,p,c,ports=env();p[2]=222;assertStatus(M.capture(s,ports),'HOLD_PORTRAIT_ID_MISMATCH')end)
run('duplicate portrait actor',function()local s,t,p,c,ports=env();p[3]=1234;assertStatus(M.capture(s,ports),'HOLD_NONUNIQUE_PORTRAIT_ID')end)
run('wrong party in context',function()local s,t,p,c,ports=env();c.partyIndex=0;assertStatus(M.capture(s,ports),'HOLD_WRONG_PORTRAIT_CONTEXT')end)
run('wrong actor id context',function()local s,t,p,c,ports=env();c.actorId=1235;assertStatus(M.capture(s,ports),'HOLD_FIRST_ACTOR_ID_CONTEXT_MISMATCH')end)
run('unreadable actor id',function()local s,t,p,c,ports=env();s.m_id=nil;assertStatus(M.capture(s,ports),'HOLD_ACTOR_CLASS_OR_EQUIPMENT_UNREADABLE')end)
run('wrong class',function()local s,t,p,c,ports=env();s.m_typeAI.m_Class=2;assertStatus(M.capture(s,ports),'HOLD_CLASS_NOT_SAVED_CANDIDATE')end)
run('missing src',function()local s,t,p,c,ports=env();t[20]=nil;assertStatus(M.capture(s,ports),'HOLD_SOURCE_ITEM_NOT_AT_EXPECTED_SLOT')end)
run('wrong src resref',function()local s,t,p,c,ports=env();t[20]=item('HAMM01');assertStatus(M.capture(s,ports),'HOLD_SOURCE_ITEM_NOT_AT_EXPECTED_SLOT')end)
run('wrong flags',function()local s,t,p,c,ports=env();t[20]=item('STAF01',2);assertStatus(M.capture(s,ports),'HOLD_SOURCE_FLAGS_CHANGED')end)
run('wrong charges',function()local s,t,p,c,ports=env();t[20]=item('STAF01',1,5,0,0);assertStatus(M.capture(s,ports),'HOLD_SOURCE_CHARGES_CHANGED')end)
run('occupied target',function()local s,t,p,c,ports=env();t[35]=item('HAMM01');assertStatus(M.capture(s,ports),'HOLD_TARGET_WEAPON_SLOT_OCCUPIED')end)
run('duplicate resref in other slot',function()local s,t,p,c,ports=env();t[19]=item('STAF01');assertStatus(M.capture(s,ports),'HOLD_ITEM_RESREF_NOT_UNIQUE_ON_ACTOR')end)
run('duplicate resref in shield slot',function()local s,t,p,c,ports=env();t[9]=item('STAF01');assertStatus(M.capture(s,ports),'HOLD_ITEM_RESREF_NOT_UNIQUE_ON_ACTOR')end)
run('wrong source index but same staff elsewhere',function()local s,t,p,c,ports=env();t[20]=nil;t[21]=item('STAF01');assertStatus(M.capture(s,ports),'HOLD_SOURCE_ITEM_NOT_AT_EXPECTED_SLOT')end)
run('item getter throws',function()local s,t,p,c,ports=env();s.m_equipment.m_items.get=function()error('READ_ERROR')end;assertStatus(M.capture(s,ports),'HOLD_ITEM_GET_FAILED')end)
run('cResRef getter throws',function()local s,t,p,c,ports=env();t[20].cResRef.get=function()error('READ_ERROR')end;assertStatus(M.capture(s,ports),'HOLD_UNREADABLE_ITEM_RECORD')end)
run('missing charges',function()local s,t,p,c,ports=env();t[20].m_useCount2=nil;assertStatus(M.capture(s,ports),'HOLD_UNREADABLE_ITEM_RECORD')end)
run('context reader throws',function()local s,t,p,c,ports=env();ports.contextReader=function()error('NO_CONTEXT')end;assertStatus(M.capture(s,ports),'HOLD_CONTEXT_BEFORE_UNREADABLE')end)
run('context changes in second read',function()
 local s,t,p,c,ports=env();local n=0
 ports.contextReader=function()n=n+1;return {actorId=c.actorId,partyIndex=c.partyIndex,actionRaw=n==1 and 0 or 105,
 selectedWeaponRaw=c.selectedWeaponRaw,selectedAbilityRaw=c.selectedAbilityRaw,
 queuedActionsRaw=c.queuedActionsRaw,currentScriptNumberRaw=c.currentScriptNumberRaw}end
 assertStatus(M.capture(s,ports),'HOLD_ACTION_CONTEXT_CHANGED')
end)
run('queue changes in second read',function()
 local s,t,p,c,ports=env();local n=0
 ports.contextReader=function()n=n+1;return {actorId=c.actorId,partyIndex=c.partyIndex,actionRaw=0,
 selectedWeaponRaw=c.selectedWeaponRaw,selectedAbilityRaw=c.selectedAbilityRaw,
 queuedActionsRaw=n==1 and 0 or 1,currentScriptNumberRaw=c.currentScriptNumberRaw}end
 assertStatus(M.capture(s,ports),'HOLD_ACTION_CONTEXT_CHANGED')
end)
run('inventory changes on second pass',function()
 local s,t,p,c,ports=env(); local n=0
 local orig=s.m_equipment.m_items.get
 s.m_equipment.m_items.get=function(self,k)
   n=n+1
   if n>38 and k==19 then return item('HAMM01') end
   return orig(self,k)
 end
 assertStatus(M.capture(s,ports),'HOLD_EQUIPMENT_CHANGED_BETWEEN_READS')
end)
run('portrait changes on second pass',function()
 local s,t,p,c,ports=env(); local n=0
 ports.portraitId=function(i) if i==1 then n=n+1;return n==1 and 1234 or 777 end return p[i+1] end
 assertStatus(M.capture(s,ports),'HOLD_PORTRAIT_ID_MISMATCH')
end)
run('no implicit fist demand',function()
 local s,t,p,c,ports=env();s.m_equipment.m_items.get=function(self,slot)if slot==10 then error('FIST_IMPLICIT') end return t[slot] end
 assertStatus(M.capture(s,ports),'RUNTIME_JAGAN_INVENTORY_MATCH_READONLY_NO_ARM')
end)
run('busy action is NOT idle-proof',function()
 local s,t,p,c,ports=env();c.actionRaw=105;c.queuedActionsRaw=2
 local r=M.capture(s,ports);assertStatus(r,'RUNTIME_JAGAN_INVENTORY_MATCH_READONLY_NO_ARM')
 assert(r.safeActionBoundaryVerified==false)
end)
run('nil party reader result',function()local s,t,p,c,ports=env();ports.portraitId=function()return nil end;assertStatus(M.capture(s,ports),'HOLD_PORTRAIT_ID_MISMATCH')end)
run('bad action context',function()local s,t,p,c,ports=env();c.queuedActionsRaw=-1;assertStatus(M.capture(s,ports),'HOLD_CONTEXT_BEFORE_UNREADABLE')end)
run('metadata is correct',function()assert(M.schema=='BGXAI_XEQUIP_IDENTITY_RO_V1' and M.sourceOnly and M.readOnly)end)
print(string.format('RESULT total=%d PASS=%d FAIL=%d',N,P,F))
if F~=0 then os.exit(1) end