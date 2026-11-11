"""NATIVE LUA tests of real historical 059 eligibility helper, not installed 061 Lua."""
import unittest
from pathlib import Path
from lua_harness import run_case

SOURCE=Path(__file__).with_name('BGX59_ELIGIBILITY_059_HISTORICAL.lua')
BASE='''
local areaA = {}; local areaB={}
local victim = {m_id=501, m_pArea=areaA}
local g1 = {m_id=102, m_pArea=areaA}
local g2 = {m_id=103, m_pArea=areaA}
local g3 = {m_id=104, m_pArea=areaB}
function EEex_UDEqual(a,b) return a == b end
function EEex_Sprite_ForAllOfTypeStringInRange(guard, objectType, range, callback)
    assert(objectType=='[ANYONE]' and range<=128)
    callback(victim)
end
local options = {{sprite=g1,id=102,slot=2,dist=200},
                 {sprite=g2,id=103,slot=3,dist=100},
                 {sprite=g3,id=104,slot=4,dist=25}}
'''
class NativeGuardEligibilityTests(unittest.TestCase):
 def test_picks_one_nearest_in_area(self):
  run_case(BASE,'''local best,reason=BGX59Eligibility.choose(victim,options)
      assert(reason=='selected' and best.id==103 and best.slot==3)''',SOURCE)
 def test_equal_distance_tie_slot(self):
  run_case(BASE+'''options[1].dist=100''','''local best=BGX59Eligibility.choose(victim,options)
      assert(best.id==102)''',SOURCE)
 def test_no_cross_area_choice(self):
  run_case(BASE+'''options={options[3]}''','''local best,reason=BGX59Eligibility.choose(victim,options)
      assert(best==nil and reason=='no_guardian_same_area')''',SOURCE)
 def test_empty_candidates(self):
  run_case(BASE+'''options={}''','''local best,reason=BGX59Eligibility.choose(victim,options)
      assert(best==nil and reason=='no_f_mode_guardian')''',SOURCE)
 def test_visibility_absent(self):
  run_case(BASE+'''EEex_Sprite_ForAllOfTypeStringInRange=function()end''','''
      local best,reason=BGX59Eligibility.choose(victim,options)
      assert(best==nil and reason=='no_guardian_visible_nearby')''',SOURCE)
 def test_missing_api(self):
  run_case(BASE+'''EEex_UDEqual=nil''','''local ok,reason=BGX59Eligibility.check(g1,victim)
      assert(not ok and reason=='area_comparison_unavailable')''',SOURCE)
 def test_failing_visibility_api(self):
  run_case(BASE+'''EEex_Sprite_ForAllOfTypeStringInRange=function()error('unavailable')end''','''
      local ok,reason=BGX59Eligibility.check(g1,victim)
      assert(not ok and reason=='sight_query_failed')''',SOURCE)
 def test_only_read_no_actions(self):
  run_case(BASE+'''
       function Attack()error('FORBIDDEN')end
       function ClearActions()error('FORBIDDEN')end
       function MoveToObject()error('FORBIDDEN')end
       function SetGlobal()error('FORBIDDEN')end
       ''','''local best=BGX59Eligibility.choose(victim,options)
       assert(best.id==103)''',SOURCE)

if __name__=='__main__':unittest.main()
