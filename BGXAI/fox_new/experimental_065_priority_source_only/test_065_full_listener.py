"""Actual full BGXAI 065 candidate vs 064 through native Lua VM EEex mocks."""
import unittest
from pathlib import Path
from hashlib import sha256
from lua65_harness import run_case
from build_065 import build, CANDIDATE, BASE as BASELINE, PIN064
HERE=Path(__file__).resolve().parent
BASE = r'''
local areaInside={} local areaOutside={}
local writes={}
local actions={}
local listeners={}
function EEex_Action_AddSpriteStartedActionListener(fn) listeners.action=fn end
function EEex_Sprite_AddBlockWeaponHitListener(fn) listeners.hit=fn end
local function sprite(id,x,y,area,guard,modal)
 local t={m_id=id,m_pos={x=x,y=y},m_pArea=area,m_nModalState=modal,
   locals={BGX38_GUARD=guard or 0,BGX52_LAST_TICK=0,BGX52_HAS_SENT=0},
   m_curAction={m_actionID=3}}
 function t:getLocalInt(k) return self.locals[k] or 0 end
 function t:setLocalInt(k,v)
   writes[#writes+1]={id=self.m_id,key=k,value=v};self.locals[k]=v
 end
 return t
end
local pc=sprite(100,100,100,areaInside,0,0)
local victim=sprite(203,0,0,areaInside,0,0)
local outside=sprite(301,1,1,areaOutside,1,0)
local inside=sprite(302,35,20,areaInside,1,0)
local inside2=sprite(303,40,20,areaInside,1,0)
local opponent=sprite(998,3,3,areaInside,0,0)
local portraits={[0]=100,[1]=301,[2]=203,[3]=302,[4]=303}
local objects={[100]=pc,[203]=victim,[301]=outside,[302]=inside,[303]=inside2,[998]=opponent}
function EEex_Sprite_GetInPortraitID(i) return portraits[i] end
function EEex_GameObject_Get(id) return objects[id] end
function EEex_UDEqual(a,b) return a==b end
EEex_EngineGlobal_CBaldurChitin={m_pObjectGame={m_worldTime={m_gameTime=100}}}
function Attack(...) actions[#actions+1]='Attack';error('forbidden') end
function AttackReevaluate(...) actions[#actions+1]='AttackReevaluate';error('forbidden') end
function ClearActions(...) actions[#actions+1]='ClearActions';error('forbidden') end
function MoveToObject(...) actions[#actions+1]='MoveToObject';error('forbidden') end
function ProtectObject(...) actions[#actions+1]='ProtectObject';error('forbidden') end
'''

class FullNativeObserver(unittest.TestCase):
    def run065(self, setup, checks):
        run_case(BASE+setup, checks, source_file=CANDIDATE)

    def test_exact_patch_proof_and_no_active_game_write(self):
        self.assertEqual(sha256(BASELINE.read_bytes()).hexdigest(),PIN064)
        self.assertEqual(build(),CANDIDATE.read_bytes())
        self.assertIn(b'BGX65Policy',CANDIDATE.read_bytes())

    def test_same_area_064_behavior_remains(self):
        self.run065('','''
          assert(type(listeners.hit)=='function')
          assert(listeners.hit({attackingSprite=opponent,targetSprite=victim})==false)
          assert(BGX52Bridge.prepared==1 and BGX52Bridge.last.chosen_guardian==302)
          assert(inside.locals.BGX52_REQ_SLOT==3 and outside.locals.BGX52_REQ_SLOT==nil)
          assert(#writes==5 and #actions==0)
          assert(BGX43Probe.weaponHitErrors==0)
          assert(BGX65Policy.lastPlan.ordersSent==0)
          assert(BGX65Policy.lastPlan.firstVictimID==203)
          assert(BGX65Policy.isInstalled==false)
        ''')

    def test_priority_observed_without_redirecting_064_order(self):
        self.run065('\npc.m_typeAI={m_Class=2}; pc.m_baseStats={m_hitPoints=80};pc.m_derivedStats={m_nMaxHitPoints=80}\nvictim.m_typeAI={m_Class=1};victim.m_baseStats={m_hitPoints=2}; victim.m_derivedStats={m_nMaxHitPoints=20}\ninside.m_typeAI={m_Class=2};inside.m_baseStats={m_hitPoints=60};inside.m_derivedStats={m_nMaxHitPoints=60}\ninside2.m_typeAI={m_Class=3};inside2.m_baseStats={m_hitPoints=50};inside2.m_derivedStats={m_nMaxHitPoints=50}\noutside.m_typeAI={m_Class=2};outside.m_baseStats={m_hitPoints=70};outside.m_derivedStats={m_nMaxHitPoints=70}\n','''
          assert(listeners.hit({attackingSprite=opponent,targetSprite=pc})==false)
          assert(BGX65Policy.lastPlan.firstVictimID==100)
          EEex_EngineGlobal_CBaldurChitin.m_pObjectGame.m_worldTime.m_gameTime=101
          assert(listeners.hit({attackingSprite=opponent,targetSprite=victim})==false)
          assert(BGX65Policy.lastPlan.firstVictimID==203)
          assert(BGX65Policy.lastPlan.highestUrgency==1)
          assert(BGX65Policy.observationCount==2 and BGX65Policy.lastPlan.ordersSent==0)
          assert(BGX43Probe.weaponHitErrors==0 and #actions==0)
        ''')

    def test_same_area_not_available_fails_closed(self):
        self.run065('inside.m_pArea=areaOutside;inside2.m_pArea=areaOutside','''
          assert(listeners.hit({attackingSprite=opponent,targetSprite=victim})==false)
          assert(BGX52Bridge.prepared==0 and #writes==0 and #actions==0)
          assert(BGX65Policy.lastPlan.assignedCount==0)
          assert(BGX43Probe.weaponHitErrors==0)
        ''')

    def test_broken_userdata_never_turns_into_attack(self):
        self.run065("EEex_UDEqual=function(...)error('bad userdata')end",'''
          assert(listeners.hit({attackingSprite=opponent,targetSprite=victim})==false)
          assert(#writes==0 and #actions==0)
          assert(BGX43Probe.weaponHitErrors==0)
          assert(BGX65Policy.lastPlan.ordersSent==0)
        ''')

    def test_no_policy_dispatch_even_when_second_guard_exists(self):
        self.run065('','''
          assert(listeners.hit({attackingSprite=opponent,targetSprite=victim})==false)
          assert(BGX52Bridge.prepared==1 and #writes==5)
          assert(inside2.locals.BGX52_REQ_SLOT==nil)
          assert(BGX65Policy.dispatchEnabled==false and #actions==0)
        ''')

    def test_party_actor_rejected_by_064(self):
        self.run065('opponent=inside','''
          assert(listeners.hit({attackingSprite=opponent,targetSprite=victim})==false)
          assert(BGX52Bridge.prepared==0 and #writes==0 and #actions==0)
          assert(BGX43Probe.weaponHitErrors==0)
          assert(BGX65Policy.observationCount==0)
        ''')

if __name__=='__main__':unittest.main()
