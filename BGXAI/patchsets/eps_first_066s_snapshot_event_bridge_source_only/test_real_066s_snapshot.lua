
local a={} local b={} local writes={} local actions={} local registrations={}
function EEex_Action_AddSpriteStartedActionListener(fn) registrations.action=(registrations.action or 0)+1; registrations.a=fn end
function EEex_Sprite_AddBlockWeaponHitListener(fn) registrations.hit=(registrations.hit or 0)+1; registrations.h=fn end
function Infinity_DisplayString(_) end
function sprite(id,x,y,area,cls,guard,hp,maxhp)
 local o={m_id=id,m_pos={x=x,y=y},m_pArea=area,m_nModalState=0,
     m_typeAI={m_Class=cls},m_baseStats={m_hitPoints=hp},m_derivedStats={m_nMaxHitPoints=maxhp},
     m_curAction={m_actionID=3},locals={BGX38_GUARD=guard,BGX52_REQ_SLOT=0,BGX52_LAST_TICK=0,BGX52_HAS_SENT=0}}
 function o:getLocalInt(k) return self.locals[k] or 0 end
 function o:setLocalInt(k,v) writes[#writes+1]={id=self.m_id,key=k,val=v};self.locals[k]=v end
 return o
end
local pc=sprite(101,0,0,a,2,0,14,14)
local v1=sprite(102,10,0,a,1,0,8,14)
local v2=sprite(103,20,0,a,3,0,8,14)
local g1=sprite(104,30,0,a,2,1,30,30)
local g2=sprite(105,40,0,a,6,1,35,35)
local e=sprite(999,22,1,a,2,0,60,60)
local portraits={[0]=101,[1]=102,[2]=103,[3]=104,[4]=105}
local objs={[101]=pc,[102]=v1,[103]=v2,[104]=g1,[105]=g2,[999]=e}
function EEex_Sprite_GetInPortraitID(i) return portraits[i] end
function EEex_GameObject_Get(id) return objs[id] end
function EEex_UDEqual(x,y) return x==y end
EEex_EngineGlobal_CBaldurChitin={m_pObjectGame={m_worldTime={m_gameTime=100}}}
function Attack(...) actions[#actions+1]='Attack';error('forbidden') end
function Spell(...) actions[#actions+1]='Spell';error('forbidden') end
function ClearActions(...) actions[#actions+1]='ClearActions';error('forbidden') end
function ProtectObject(...) actions[#actions+1]='ProtectObject';error('forbidden') end
function hit(victim,enemy) assert(type(registrations.h)=='function');return registrations.h({attackingSprite=enemy or e,targetSprite=victim}) end

dofile('M_BX43_066S_VERIFIED_ORIGINAL.lua')
assert(BGX43Probe.installed==true and BGX43Probe.weaponHitRegistered==true)
assert(hit(v1)==false)
assert(hit(v2)==false)
local original=BGX43Probe.snapshot()
assert(original.schema==1 and #original.events>=2 and #original.guard_signals==2)
local adapter=dofile('BGXAI066S_080_CONFIRMED_HIT_BRIDGE_SOURCE_ONLY.lua')
local before=#writes
local result=adapter.observe(original)
assert(result.status=='CONFIRMED_HIT_HISTORY_ONLY')
assert(result.observed_count==1) -- Same default enemy hit two separate victims.
assert(result.observed_hits[1].attacker_id==999)
assert(result.observed_hits[1].victim_id==103)
assert(result.observed_hits[1].active_now_verified==false)
assert(#writes==before and result.orders_sent==0 and result.locals_written==0)
assert(adapter.readiness(original).status=='HOLD_NO_ENGINE_DISPATCH')
assert(#actions==0)
print('BGXAI_REAL_066S_SNAPSHOT_BRIDGE_PASS')
-- Two distinct engine-confirmed attackers are retained independently.
local e2=sprite(998,26,2,a,2,0,60,60)
objs[998]=e2
BGX43Probe.clearMemory()
assert(hit(v1,e)==false)
assert(hit(v2,e2)==false)
local two=BGX43Probe.snapshot()
local writesBefore=#writes
local seen=adapter.observe(two)
assert(seen.status=='CONFIRMED_HIT_HISTORY_ONLY' and seen.observed_count==2)
assert(seen.observed_hits[1].attacker_id==998 and seen.observed_hits[1].victim_id==103)
assert(seen.observed_hits[2].attacker_id==999 and seen.observed_hits[2].victim_id==102)
assert(seen.active_now_verified==false and seen.origin_verified==false)
assert(#writes==writesBefore and #actions==0)
BGX43Probe.clearMemory()
assert(adapter.observe(BGX43Probe.snapshot()).status=='HOLD_NO_ENGINE_DISPATCH')
print('BGXAI_REAL_066S_TWO_ATTACKERS_PASS')
