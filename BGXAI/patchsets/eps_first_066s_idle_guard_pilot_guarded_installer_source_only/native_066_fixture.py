PREAMBLE=r'''
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
'''