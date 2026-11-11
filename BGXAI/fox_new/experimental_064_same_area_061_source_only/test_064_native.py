"""Execute actual BGX64 B.prepare excerpt in Lua 5.4 mocked EEex, no game."""
import unittest
from pathlib import Path
from lua64_harness import run_case

SOURCE=Path(__file__).with_name('BGX64_BRIDGE_PREPARE_NATIVE.lua')
BASE='''
local areaA={} local areaB={}
local writes={}
local function actor(id,x,y,area,guard,modal)
 local p={m_id=id,m_pos={x=x,y=y},m_pArea=area,m_nModalState=modal,
    locals={BGX38_GUARD=guard or 0,BGX52_LAST_TICK=0,BGX52_HAS_SENT=0}}
 function p:getLocalInt(k) return self.locals[k] or 0 end
 function p:setLocalInt(k,v)
   writes[#writes+1]={id=id,key=k,value=v}
   self.locals[k]=v
 end
 return p
end
local victim=actor(203,0,0,areaA,0,0)
local gOutside=actor(301,1,1,areaB,1,0)
local gInside=actor(302,30,20,areaA,1,0)
local gInside2=actor(303,40,20,areaA,1,0)
local portraits={[0]=100,[1]=301,[2]=203,[3]=302,[4]=303,[5]=nil}
local objects={[100]=actor(100,100,20,areaA,0,0),[203]=victim,
 [301]=gOutside,[302]=gInside,[303]=gInside2}
function EEex_Sprite_GetInPortraitID(i) return portraits[i] end
function EEex_GameObject_Get(id) return objects[id] end
function EEex_UDEqual(a,b) return a==b end
EEex_EngineGlobal_CBaldurChitin={m_pObjectGame={m_worldTime={m_gameTime=100}}}
local hit={event='PASSIVE_GUARD_ADVISORY_ON_CONFIRMED_HIT',
 confirmation='ENGINE_WEAPON_HIT_CONTEXT',protected_id=203,
 attacker_id=998,source_event_sequence=1}
'''

class NativeBridge064Tests(unittest.TestCase):
 def test_excludes_nearer_defender_other_area(self):
  run_case(BASE,'''local ok,msg=BGXMODULE.prepare(hit)
   assert(ok and msg=='prepared')
   assert(BGXMODULE.last.chosen_guardian==302)
   assert(gOutside.locals.BGX52_REQ_SLOT==nil)
   assert(gInside.locals.BGX52_REQ_SLOT==3 and gInside.locals.BGX52_EXPIRE==400)
   assert(#writes==5 and writes[5].key=='BGX52_REQ_SLOT')''',SOURCE)
 def test_nearest_same_area(self):
  run_case(BASE+'''gInside2.m_pos.x=1''','''assert(BGXMODULE.prepare(hit))
   assert(BGXMODULE.last.chosen_guardian==303)''',SOURCE)
 def test_equal_distance_slot_tiebreak(self):
  run_case(BASE+'''gInside2.m_pos.x=30''','''assert(BGXMODULE.prepare(hit))
   assert(BGXMODULE.last.chosen_guardian==302)''',SOURCE)
 def test_no_same_area_guard_no_write(self):
  run_case(BASE+'''gInside.m_pArea=areaB;gInside2.m_pArea=areaB''','''local ok,reason=BGXMODULE.prepare(hit)
   assert(not ok and reason=='no_guardian_with_f_mode_in_same_area' and #writes==0)''',SOURCE)
 def test_missing_equality_api_no_write(self):
  run_case(BASE+'''EEex_UDEqual=nil''','''local ok,reason=BGXMODULE.prepare(hit)
   assert(not ok and reason=='area_comparison_unavailable' and #writes==0)''',SOURCE)
 def test_missing_victim_area_no_write(self):
  run_case(BASE+'''victim.m_pArea=nil''','''local ok,reason=BGXMODULE.prepare(hit)
   assert(not ok and reason=='area_comparison_unavailable' and #writes==0)''',SOURCE)
 def test_equality_error_fail_closed(self):
  run_case(BASE+'''EEex_UDEqual=function()error('bad userdata')end''','''local ok,reason=BGXMODULE.prepare(hit)
   assert(not ok and reason=='no_guardian_with_f_mode_in_same_area' and #writes==0)''',SOURCE)
 def test_f_off_nearest_skipped(self):
  run_case(BASE+'''gInside.locals.BGX38_GUARD=0''','''assert(BGXMODULE.prepare(hit))
   assert(BGXMODULE.last.chosen_guardian==303)''',SOURCE)
 def test_modal_busy_skip(self):
  run_case(BASE+'''gInside.m_nModalState=2''','''assert(BGXMODULE.prepare(hit))
   assert(BGXMODULE.last.chosen_guardian==303)''',SOURCE)
 def test_no_confirmed_hit_no_write(self):
  run_case(BASE+'''hit.confirmation='PARTY_ATTACK' ''','''local ok,reason=BGXMODULE.prepare(hit)
   assert(not ok and reason=='unconfirmed_hit' and #writes==0)''',SOURCE)
 def test_busy_same_tick_preserved(self):
  run_case(BASE+'''gInside.locals.BGX52_HAS_SENT=1;gInside.locals.BGX52_LAST_TICK=100''','''local ok,reason=BGXMODULE.prepare(hit)
   assert(not ok and reason=='duplicate_same_tick_or_clock_rewound' and #writes==0)''',SOURCE)
 def test_selected_only_one_guard(self):
  run_case(BASE,'''assert(BGXMODULE.prepare(hit))
   assert(gInside.locals.BGX52_REQ_SLOT==3)
   assert(gInside2.locals.BGX52_REQ_SLOT==nil)
   assert(gOutside.locals.BGX52_REQ_SLOT==nil)''',SOURCE)
 def test_no_game_combat_commands(self):
  run_case(BASE+'''function Attack()error('BAD')end
    function ClearActions()error('BAD')end
    function MoveToObject()error('BAD')end
    function ProtectObject()error('BAD')end''','''assert(BGXMODULE.prepare(hit))''',SOURCE)
 def test_dedup_unreadable_fails_without_write(self):
  run_case(BASE+'''gInside.locals.BGX52_LAST_TICK=-1''','''local ok,msg=BGXMODULE.prepare(hit)
   assert(not ok and msg=='dedup_unreadable' and #writes==0)''',SOURCE)
 def test_wrong_victim_rejected(self):
  run_case(BASE+'''hit.protected_id=501''','''local ok,msg=BGXMODULE.prepare(hit)
   assert(not ok and msg=='victim_not_in_party' and #writes==0)''',SOURCE)

if __name__=='__main__':unittest.main()
