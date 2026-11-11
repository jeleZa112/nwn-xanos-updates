"""Actual complete 061 vs 064 EEex Lua modules under native Lua 5.4 mocked hooks.

The user game is neither accessed nor modified. These tests prove the actual
listener -> event -> advisory -> single guardian request pathway, not just B.prepare.
"""
import unittest
from pathlib import Path
from lua64_harness import run_case

HERE = Path(__file__).parent
LUA061 = HERE / 'M_BX43_061_BASELINE_READONLY.lua'
LUA064 = HERE / 'M_BX43_064_CANDIDATE.lua'

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

class FullListenerLiveSourceTests(unittest.TestCase):
 def run_case(self, scenario, assertions, source=LUA064):
  run_case(BASE + scenario, assertions, source_file=source)

 def test_061_reproduces_cross_area_defect(self):
  self.run_case('', '''
   assert(type(listeners.hit)=='function')
   assert(listeners.hit({attackingSprite=opponent,targetSprite=victim})==false)
   assert(BGX52Bridge.prepared==1)
   assert(BGX52Bridge.last.chosen_guardian==301)
   assert(outside.locals.BGX52_REQ_SLOT==3)
   assert(inside.locals.BGX52_REQ_SLOT==nil)
   assert(#actions==0)
  ''',LUA061)

 def test_064_selects_same_area_not_nearest_wrong_area(self):
  self.run_case('', '''
   assert(type(listeners.hit)=='function')
   assert(listeners.hit({attackingSprite=opponent,targetSprite=victim})==false)
   assert(BGX52Bridge.prepared==1)
   assert(BGX52Bridge.last.chosen_guardian==302)
   assert(outside.locals.BGX52_REQ_SLOT==nil)
   assert(inside.locals.BGX52_REQ_SLOT==3)
   assert(inside.locals.BGX52_EXPIRE==400)
   assert(inside2.locals.BGX52_REQ_SLOT==nil)
   assert(#actions==0)
  ''')

 def test_064_one_guardian_only_for_one_hit(self):
  self.run_case('', '''
   listeners.hit({attackingSprite=opponent,targetSprite=victim})
   assert(BGX52Bridge.prepared==1)
   assert(#writes==5)
   assert(BGX43Probe.weaponHitErrors==0)
   assert(BGX43Probe.weaponHitCalls==1)
  ''')

 def test_064_second_eligible_guardian_if_first_f_off(self):
  self.run_case('inside.locals.BGX38_GUARD=0', '''
   listeners.hit({attackingSprite=opponent,targetSprite=victim})
   assert(BGX52Bridge.last.chosen_guardian==303)
   assert(inside2.locals.BGX52_REQ_SLOT==3)
   assert(outside.locals.BGX52_REQ_SLOT==nil)
  ''')

 def test_064_no_same_area_defender_fails_closed(self):
  self.run_case('inside.m_pArea=areaOutside;inside2.m_pArea=areaOutside', '''
   listeners.hit({attackingSprite=opponent,targetSprite=victim})
   assert(BGX52Bridge.prepared==0)
   assert(BGX52Bridge.last.reason=='no_guardian_with_f_mode_in_same_area')
   assert(#writes==0 and #actions==0)
   assert(BGX43Probe.weaponHitErrors==0)
  ''')

 def test_064_no_area_api_fails_closed_not_disable_hook(self):
  self.run_case('EEex_UDEqual=nil', '''
   assert(listeners.hit({attackingSprite=opponent,targetSprite=victim})==false)
   assert(BGX52Bridge.prepared==0)
   assert(BGX52Bridge.last.reason=='area_comparison_unavailable')
   assert(BGX43Probe.weaponHitErrors==0 and #writes==0)
  ''')

 def test_064_area_api_errors_fail_closed(self):
  self.run_case("EEex_UDEqual=function(...)error('bad userdata')end", '''
   assert(listeners.hit({attackingSprite=opponent,targetSprite=victim})==false)
   assert(BGX52Bridge.prepared==0 and #writes==0)
   assert(BGX43Probe.weaponHitErrors==0)
  ''')

 def test_064_party_attacker_rejected_without_request(self):
  self.run_case('opponent=inside', '''
   assert(listeners.hit({attackingSprite=opponent,targetSprite=victim})==false)
   assert(BGX52Bridge.prepared==0 and #writes==0)
   assert(BGX43Probe.lastWeaponHit.reason=='party_actor')
  ''')

 def test_064_hits_not_confirmed_outside_party_rejected(self):
  self.run_case('victim=opponent', '''
   assert(listeners.hit({attackingSprite=opponent,targetSprite=victim})==false)
   assert(BGX52Bridge.prepared==0 and #writes==0)
   assert(BGX43Probe.lastWeaponHit.reason=='not_party_victim')
  ''')

 def test_064_duplicate_same_tick_not_repeated(self):
  self.run_case('', '''
   listeners.hit({attackingSprite=opponent,targetSprite=victim})
   assert(listeners.hit({attackingSprite=opponent,targetSprite=victim})==false)
   assert(BGX52Bridge.prepared==1 and #writes==5)
   assert(BGX52Bridge.last.reason=='duplicate_same_tick_or_clock_rewound')
  ''')

 def test_064_eeex_hook_registration_error_fails_passively(self):
  self.run_case('EEex_Sprite_AddBlockWeaponHitListener=function()error("registration")end', '''
   assert(BGX43Probe.installed==true)
   assert(BGX43Probe.weaponHitRegistered==false)
   assert(BGX43Probe.lastError=='WEAPON_HIT_LISTENER_REGISTRATION_FAILED')
   assert(BGX52Bridge.prepared==0 and #writes==0)
  ''')

 def test_064_historical_register_missing_gracefully(self):
  self.run_case('EEex_Sprite_AddBlockWeaponHitListener=nil', '''
   assert(BGX43Probe.weaponHitRegistered==false)
   assert(BGX43Probe.lastError=='WEAPON_HIT_LISTENER_UNAVAILABLE')
   assert(BGX52Bridge.prepared==0 and #writes==0)
  ''')

 def test_064_does_not_reinstall_hook_on_repeat_init(self):
  self.run_case('', '''
   assert(BGX43Probe.init()==true)
   assert(type(listeners.hit)=='function')
   assert(BGX43Probe.weaponHitCalls==0)
   assert(#writes==0)
  ''')

if __name__=='__main__':unittest.main()
