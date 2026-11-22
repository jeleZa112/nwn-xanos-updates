local M=dofile('BGXAI_R11_TARGET_BOUND_HIT_CANDIDATE_V2.lua')
local R=dofile('BGXAI_R11_ACTION_TARGET_CANDIDATE_RO.lua')
local P=dofile('BGXAI_WEAPON_R11_EEEX_SELECTED_HIT_PROBE.lua')
local n=0
local function test(name,fn)
 local ok,e=pcall(fn);if not ok then error(name..': '..tostring(e)) end
 n=n+1; print('PASS TARGETBOUND '..n..' '..name)
end
local function safe(o)
 assert(o.executable==false and o.dispatchAuthorized==false and
  o.weaponSwitchAuthorized==false and o.nativeEvidenceAuthenticated==false and
  o.liveReadVerified==false and o.ordersSent==0 and
  o.actionQueueCleared==false and o.currentActionPreserved==true and
  o.epsQueueProven==false and o.manualOrderProven==false)
end
local function mock()
 local item={name='SW1H04'}
 local src={m_id=10,m_equipment={m_selectedWeapon=35,m_selectedWeaponAbility=0,
  m_items={get=function(_,slot)return slot==35 and item or nil end}}}
 local target={m_id=20,isSprite=function()return true end}
 local action={m_actionID=3,m_acteeID={m_Instance=20}}
 local api={GetWeaponHitChance=function()return 65 end,
  IsImmuneToWeapon=function()return false end,
  GameObject_Get=function(id) assert(id==20);return target end}
 local ctx={sessionId='S',snapshotId='T',sequence=4,
  actor=10,targetActor=20,actionRaw=3,observeSelectedOnly=true,
  switchAttempted=false,manualEPSBoundaryProven=false,readOnlyProbeConsent=true}
 return src,action,api,ctx,item,target
end
local function inspect(src,act,api,ctx,r,p)
 return M.inspect(src,act,api,ctx,r or R,p or P)
end
test('valid selected item and target only candidate',function()
 local s,a,e,c=mock();local o=inspect(s,a,e,c);safe(o)
 assert(o.status=='TARGET_BOUND_SELECTED_HIT_CANDIDATE_NOT_NATIVE_PROOF')
 assert(o.hitChancePercentCandidate==65 and o.sourceActor==10 and o.targetActor==20)
 assert(o.hostileTargetProven==false and o.alternativeWeaponProven==false)
end)
test('missing source hold',function()local _,a,e,c=mock();safe(inspect(nil,a,e,c))end)
test('missing action hold',function()local s,_,e,c=mock();safe(inspect(s,nil,e,c))end)
test('missing context hold',function()local s,a,e=mock();safe(inspect(s,a,e,nil))end)
test('missing api hold',function()local s,a,_,c=mock();safe(inspect(s,a,nil,c))end)
test('missing resolver hold',function()local s,a,e,c=mock();safe(inspect(s,a,e,c,{}))end)
test('missing probe hold',function()local s,a,e,c=mock();safe(inspect(s,a,e,c,R,{}))end)
test('bad action hold',function()local s,a,e,c=mock();a.m_actionID=113;c.actionRaw=113;safe(inspect(s,a,e,c))end)
test('attack one round candidate, not proof',function()local s,a,e,c=mock();a.m_actionID=30;c.actionRaw=30;local o=inspect(s,a,e,c);safe(o);assert(o.actionAttackProven==false)end)
test('changed expected actor hold',function()local s,a,e,c=mock();c.actor=11;safe(inspect(s,a,e,c))end)
test('changed expected target hold',function()local s,a,e,c=mock();c.targetActor=21;safe(inspect(s,a,e,c))end)
test('changed expected action hold',function()local s,a,e,c=mock();c.actionRaw=30;safe(inspect(s,a,e,c))end)
test('invalid target ID hold',function()local s,a,e,c=mock();a.m_acteeID.m_Instance=-1;safe(inspect(s,a,e,c))end)
test('self target hold',function()local s,a,e,c=mock();a.m_acteeID.m_Instance=10;c.targetActor=10;safe(inspect(s,a,e,c))end)
test('ammo selection blocks, not attributing launcher',function()
 local s,a,e,c=mock();s.m_equipment.m_selectedWeapon=12
 s.m_equipment.m_items.get=function()return {}end
 local o=inspect(s,a,e,c);safe(o);assert(o.reason=='AMMO_LAUNCHER_NOT_PROVEN')
end)
test('target disappears after resolve',function()
 local s,a,e,c,t=mock();local reads=0
 e.GameObject_Get=function()reads=reads+1;if reads>1 then return nil end;return t end
 safe(inspect(s,a,e,c))
end)
test('target changes after selected hit probe',function()
 local s,a,e,c,it,t=mock();local reads=0
 e.GetWeaponHitChance=function()t.m_id=30;return 90 end
 local o=inspect(s,a,e,c);safe(o);assert(o.status=='HOLD')
end)
test('action changes inside probability callback',function()
 local s,a,e,c=mock();e.GetWeaponHitChance=function()a.m_actionID=160;return 80 end
 local o=inspect(s,a,e,c);safe(o);assert(o.reason=='STATE_CHANGED_AFTER_READ')
end)
test('selected item changes in probability callback',function()
 local s,a,e,c=mock();e.GetWeaponHitChance=function()s.m_equipment.m_items.get=function()return {}end;return 80 end
 local o=inspect(s,a,e,c);safe(o);assert(o.status=='HOLD')
end)
test('target object changes with same ID must hold',function()
 local s,a,e,c,t=mock();local reads=0
 e.GameObject_Get=function()
  reads=reads+1;if reads>=4 then return {m_id=20,isSprite=function()return true end} end
  return t
 end
 local o=inspect(s,a,e,c);safe(o);assert(o.status=='HOLD')
end)
test('missing EEex hit chance holds',function()local s,a,e,c=mock();e.GetWeaponHitChance=nil;safe(inspect(s,a,e,c))end)
test('wrong return chance holds',function()local s,a,e,c=mock();e.GetWeaponHitChance=function()return 200 end;safe(inspect(s,a,e,c))end)
test('throwing native method holds',function()local s,a,e,c=mock();e.GetWeaponHitChance=function()error('boom')end;safe(inspect(s,a,e,c))end)
test('fake probe trying to authorize dispatch must hold',function()
 local s,a,e,c=mock();local fake={inspect=function()
  local x=P.inspect(s,{m_id=20},e,{sessionId='S',snapshotId='T',actor=10,targetActor=20,
  sequence=4,usesAlreadySelectedWeapon=true,readOnlyProbeConsent=true,
  manualEPSBoundaryProven=false,switchAttempted=false})
  x.dispatchAuthorized=true;return x
 end}
 safe(inspect(s,a,e,c,R,fake))
end)
test('no object pointers exported',function()
 local s,a,e,c,it,t=mock();local o=inspect(s,a,e,c);safe(o)
 for _,v in pairs(o) do assert(v~=s and v~=a and v~=t and v~=it) end
end)
test('no writes or hooks by module',function()
 assert(M.installed==false and type(M.inspect)=='function')
 assert(_G.EEex_Action_AddSpriteStartedActionListener==nil)
end)
print(('TARGETBOUND total %d/%d PASS'):format(n,n))
