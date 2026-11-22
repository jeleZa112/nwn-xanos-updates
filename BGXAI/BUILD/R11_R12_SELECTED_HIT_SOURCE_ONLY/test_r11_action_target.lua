local M=dofile('BGXAI_R11_ACTION_TARGET_CANDIDATE_RO.lua')
local n=0
local function test(name,fn)
 local ok,e=pcall(fn);if not ok then error(name..': '..tostring(e)) end
 n=n+1;print('PASS TARGET '..n..' '..name)
end
local function mock()
 local sprite={m_id=1}
 local act={m_actionID=3,m_acteeID={m_Instance=2}}
 local target={m_id=2,isSprite=function() return true end}
 local count=0
 local api={GameObject_Get=function(id) count=count+1;assert(id==2);return target end}
 return sprite,act,api,target,function() return count end
end
local function safe(o)
 assert(o.status=='TARGET_CANDIDATE_HOLD' and o.executable==false and
  o.dispatchAuthorized==false and o.weaponSwitchAuthorized==false and
  o.hitChanceCallAllowed==false and o.hostileTargetProven==false and
  o.actionTypeAttackProven==false and o.nativeEvidenceAuthenticated==false and
  o.ordersSent==0 and o.actionQueueCleared==false and
  o.currentActionPreserved==true)
end
test('valid actee is only candidate',function()
 local s,a,e,t,c=mock();local o=M.resolve(s,a,e);safe(o)
 assert(o.reason=='ACTEE_SPRITE_CANDIDATE_NOT_CONFIRMED_ENEMY' and
  o.sourceActor==1 and o.candidateTargetActor==2 and c()==1)
 assert(o.target==nil and a.m_acteeID.m_Instance==2)
end)
test('missing sprite blocks',function()
 local _,a,e=mock();local o=M.resolve(nil,a,e);safe(o);assert(o.reason=='MISSING_EVENT_OBJECTS')
end)
test('missing action blocks',function()
 local s,_,e=mock();local o=M.resolve(s,nil,e);safe(o)
end)
test('missing API blocks',function()
 local s,a=mock();local o=M.resolve(s,a,nil);safe(o)
end)
test('invalid API function blocks',function()
 local s,a,e=mock();e.GameObject_Get=5;local o=M.resolve(s,a,e);safe(o)
end)
test('invalid source ID blocks',function()
 local s,a,e=mock();s.m_id=0;local o=M.resolve(s,a,e);safe(o)
end)
test('invalid action ID blocks',function()
 local s,a,e=mock();a.m_actionID=0/0;local o=M.resolve(s,a,e);safe(o)
end)
test('missing actee blocks',function()
 local s,a,e=mock();a.m_acteeID=nil;local o=M.resolve(s,a,e);safe(o)
end)
test('self target blocks',function()
 local s,a,e=mock();a.m_acteeID.m_Instance=1;local o=M.resolve(s,a,e);safe(o)
end)
test('resolver nil blocks',function()
 local s,a,e=mock();e.GameObject_Get=function()return nil end
 local o=M.resolve(s,a,e);safe(o)
end)
test('resolver throws blocks',function()
 local s,a,e=mock();e.GameObject_Get=function()error('oops')end
 local o=M.resolve(s,a,e);safe(o)
end)
test('non sprite target blocks',function()
 local s,a,e,t=mock();t.isSprite=function() return false end
 local o=M.resolve(s,a,e);safe(o)
end)
test('target spoofed m_id blocks',function()
 local s,a,e,t=mock();t.m_id=3;local o=M.resolve(s,a,e);safe(o)
end)
test('missing isSprite blocks',function()
 local s,a,e,t=mock();t.isSprite=nil;local o=M.resolve(s,a,e);safe(o)
end)
test('action changed during resolve blocks',function()
 local s,a,e=mock()
 e.GameObject_Get=function()a.m_actionID=9;return {m_id=2,isSprite=function()return true end}end
 local o=M.resolve(s,a,e);safe(o);assert(o.reason=='ACTION_CHANGED_DURING_READ')
end)
test('target pointer never exported',function()
 local s,a,e,t=mock();local o=M.resolve(s,a,e);safe(o)
 for _,v in pairs(o) do assert(v~=t and v~=s)end
end)
test('action raw id is NOT verified attack',function()
 local s,a,e=mock();a.m_actionID=113
 local o=M.resolve(s,a,e);safe(o)
 assert(o.reason=='ACTEE_SPRITE_CANDIDATE_NOT_CONFIRMED_ENEMY' and
  o.actionTypeAttackProven==false)
end)
test('no globals hooked',function()
 assert(M.installed==false and _G.EEex_Action_AddSpriteStartedActionListener==nil)
end)
print(('TARGET total %d/%d PASS'):format(n,n))
