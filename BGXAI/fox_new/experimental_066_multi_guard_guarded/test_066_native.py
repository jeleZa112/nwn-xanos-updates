import unittest
from pathlib import Path
from hashlib import sha256
from build_066 import build,OUT,BASE,PIN064
from lua65_harness import run_case

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

def check(fragment, extra=''):
    run_case(PREAMBLE+extra, "assert(registrations.action==1 and registrations.hit==1)\n"+fragment, OUT)

class Team066Native(unittest.TestCase):
    def test_patch_immutable(self):
        self.assertEqual(sha256(BASE.read_bytes()).hexdigest(),PIN064)
        self.assertEqual(build(),OUT.read_bytes())
        self.assertEqual(OUT.read_text().count('EEex_Sprite_AddBlockWeaponHitListener, P.onWeaponHit'),1)
    def test_two_victims_two_guardians(self):
        check('''
assert(hit(v1)==false)
assert(g1.locals.BGX52_REQ_SLOT==2 and BGX66Team.prepared==1)
assert(hit(v2)==false)
assert(g2.locals.BGX52_REQ_SLOT==3 and BGX66Team.prepared==2)
assert(#writes==10 and #actions==0 and BGX43Probe.weaponHitErrors==0)
assert(BGX52Bridge.prepared==2 and BGX66Team.last.status=='PREPARED_BCS_ONLY')''')
    def test_single_hit_only_one_guardian(self):
        check('''assert(hit(v1)==false);assert(BGX66Team.prepared==1)
assert(g1.locals.BGX52_REQ_SLOT==2 and g2.locals.BGX52_REQ_SLOT==0)
assert(#writes==5 and #actions==0)''')
    def test_duplicate_hit_same_victim_no_duplicate(self):
        check('''assert(hit(v1)==false);assert(hit(v1)==false)
assert(BGX66Team.prepared==1 and #writes==5)
assert(BGX66Team.rejected.victim_reserved==1)''')
    def test_casters_only_no_melee(self):
        check('''assert(hit(v1)==false)
assert(BGX66Team.prepared==0 and #writes==0)
assert(BGX66Team.last.status=='NO_FRONTLINE' and #BGX66Team.last.support_candidates==2)
assert(#actions==0)''',"g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=3;")
    def test_025_master_bridge_toggle_off(self):
        check("BGX52Bridge.enabled=false;assert(hit(v1)==false);assert(BGX66Team.prepared==0 and #writes==0)")
    def test_f_off(self):
        check('''assert(hit(v1)==false);assert(BGX66Team.prepared==0 and #writes==0)''',"g1.locals.BGX38_GUARD=0;g2.locals.BGX38_GUARD=0;")
    def test_wrong_area(self):
        check('''assert(hit(v1)==false);assert(BGX66Team.prepared==0 and #writes==0)''',"g1.m_pArea=b;g2.m_pArea=b;")
    def test_missing_area_comparator(self):
        check('''assert(hit(v1)==false);assert(BGX66Team.prepared==0 and #writes==0)''',"EEex_UDEqual=nil;")
    def test_broken_area_userdata(self):
        check('''assert(hit(v1)==false);assert(BGX66Team.prepared==0 and #writes==0)''',"EEex_UDEqual=function()error('userdata')end;")
    def test_modal_busy(self):
        check('''assert(hit(v1)==false);assert(BGX66Team.prepared==0 and #writes==0)''',"g1.m_nModalState=1;g2.m_nModalState=2;")
    def test_low_health_guardian(self):
        check('''assert(hit(v1)==false);assert(BGX66Team.prepared==1 and g1.locals.BGX52_REQ_SLOT==0)
assert(g2.locals.BGX52_REQ_SLOT==2)''',"g1.m_baseStats.m_hitPoints=3;")
    def test_stale_req_slot_never_overwrites(self):
        check('''assert(hit(v1)==false);assert(BGX66Team.prepared==1 and g1.locals.BGX52_REQ_SLOT==5)
assert(g2.locals.BGX52_REQ_SLOT==2 and #writes==5)''',"g1.locals.BGX52_REQ_SLOT=5;")
    def test_same_tick_two_guards(self):
        check('''assert(hit(v1)==false);assert(hit(v2)==false);assert(BGX66Team.prepared==2)
assert(g1.locals.BGX52_LAST_TICK==100 and g2.locals.BGX52_LAST_TICK==100)''')
    def test_same_guardian_not_reused(self):
        check('''assert(hit(v1)==false);assert(hit(v2)==false)
assert(BGX66Team.prepared==1 and BGX66Team.last.status=='NO_FRONTLINE')''',"g2.locals.BGX38_GUARD=0;")
    def test_clock_rewind_refreshes_reservations_but_local_gate_fails(self):
        check('''assert(hit(v1)==false)
EEex_EngineGlobal_CBaldurChitin.m_pObjectGame.m_worldTime.m_gameTime=99
assert(hit(v2)==false);assert(BGX66Team.prepared==1 and g1.locals.BGX52_REQ_SLOT==2)''',"g2.locals.BGX38_GUARD=0;")
    def test_not_after_unconfirmed_signal(self):
        check('''local success,why=BGX66Team.prepare({event='SOME_ACTION',confirmation='GUESS'})
assert(success==false and why=='unconfirmed_hit' and #writes==0 and #actions==0)''')
    def test_party_attack_disallowed(self):
        check('''assert(hit(v1,g1)==false);assert(#writes==0 and BGX66Team.prepared==0)''')
    def test_target_not_in_party(self):
        check('''assert(hit(e)==false);assert(#writes==0 and BGX66Team.prepared==0)''')
    def test_partial_write_fails_closed(self):
        check('''assert(hit(v1)==false);assert(BGX66Team.prepared==0)
assert(g1.locals.BGX52_REQ_SLOT==0 and g2.locals.BGX52_REQ_SLOT==0 and BGX43Probe.weaponHitErrors==0)''',"g2.locals.BGX38_GUARD=0;local orig=g1.setLocalInt;local counter=0;function g1:setLocalInt(k,v)counter=counter+1;if counter==4 then error('mock write')end;return orig(self,k,v)end;")
    def test_magic_multiclass_excluded(self):
        check('''assert(hit(v1)==false);assert(BGX66Team.prepared==1 and g1.locals.BGX52_REQ_SLOT==0)
assert(g2.locals.BGX52_REQ_SLOT==2)''',"g1.m_typeAI.m_Class=7;")
    def test_no_authoritative_hp_fail_closed(self):
        check('''assert(hit(v1)==false);assert(BGX66Team.prepared==1 and g1.locals.BGX52_REQ_SLOT==0)''',"g1.m_baseStats=nil;")
    def test_unknown_retrained_class_fail_closed(self):
        check('''assert(hit(v1)==false);assert(BGX66Team.prepared==0 and #writes==0)''',"g1.m_typeAI.m_Class=201;g2.m_typeAI.m_Class=999;")
    def test_expired_reservations_allow_second_then_existing_bcs_respects_pending(self):
        check('''assert(hit(v1)==false)
EEex_EngineGlobal_CBaldurChitin.m_pObjectGame.m_worldTime.m_gameTime=146
assert(hit(v2)==false);assert(BGX66Team.prepared==1)''',"g2.locals.BGX38_GUARD=0;")
    def test_existing_bcs_stays_intact(self):
        check('''assert(hit(v1)==false);assert(g1.locals.BGX52_REQ_SLOT==2)
assert(g1.locals.BGX52_EXPIRE==400 and g1.locals.BGX52_HAS_SENT==1)
assert(BGX43Probe.snapshot().weapon_hit_registered==true and #actions==0)''')

if __name__=='__main__':unittest.main()
