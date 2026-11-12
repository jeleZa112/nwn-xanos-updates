"""Source-only Lua 5.4 tests for native x64 EEex read probes. Never modify EET."""
import unittest
from pathlib import Path
from lua65_harness import run_case

ROOT = Path(__file__).resolve().parent
HP = ROOT / 'BGXAI65_CLASS_HP_CONSOLE_R1.lua'
GATE = ROOT / 'BGXAI65_POLICY_SNAPSHOT_GATE.lua'

BASE = r'''
output={}
C={DisplayText=function(_,s)output[#output+1]=s end}
local A={}
local ids={[0]=100,[1]=101,[2]=102,[3]=103,[4]=-1,[5]=4294967295}
local objs={}
for i=0,3 do
 local id=100+i
 local s={m_id=id,m_typeAI={m_Class=i+1},m_baseStats={m_hitPoints=14-i},
          m_derivedStats={m_nMaxHitPoints=14},m_pos={x=10+i,y=20+i},
          m_nModalState=0,m_pArea=A,guard=i%2}
 function s:getLocalInt(k) assert(k=='BGX38_GUARD');return self.guard end
 function s:setLocalInt(...) error('GAME_WRITE_FORBIDDEN') end
 objs[id]=s
end
function EEex_Sprite_GetInPortraitID(i)return ids[i] end
function EEex_GameObject_Get(id)assert(id>=0 and id<2147483647);return objs[id] end
'''

class NativeLiveGateTests(unittest.TestCase):
 def test_four_occupied_and_two_sentinels_hp(self):
  run_case(BASE, """assert(#output==6);assert(output[1]=='BGX65R1 P0 1:14/14')
assert(output[4]=='BGX65R1 P3 4:11/14')
assert(output[5]=='BGX65R1 P4 absent' and output[6]=='BGX65R1 P5 absent')""", HP)
 def test_four_occupied_guard_coords_modal_area(self):
  run_case(BASE, """assert(#output==6);assert(output[1]=='BGX65G P0 id=true xy=10,20 F=0 modal=0 area=true')
assert(output[2]=='BGX65G P1 id=true xy=11,21 F=1 modal=0 area=true')
assert(output[5]=='BGX65G P4 absent' and output[6]=='BGX65G P5 absent')""", GATE)
 def test_unresolved_valid_sprite_is_distinct_from_absent(self):
  run_case(BASE+"\nfunction EEex_GameObject_Get(id)if id==100 then return nil end;return {m_typeAI={m_Class=2},m_baseStats={m_hitPoints=1},m_derivedStats={m_nMaxHitPoints=3}} end\n", "assert(output[1]=='BGX65R1 P0 OBJECT_MISSING')", HP)
 def test_broken_hp_fields_report_api_error(self):
  run_case(BASE+"\nfunction EEex_GameObject_Get(id)if id==100 then return {m_baseStats={}} end end\n", "assert(output[1]=='BGX65R1 P0 API_ERROR')", HP)
 def test_missing_pos_reports_field_error_not_absence(self):
  run_case(BASE+"\nfunction EEex_GameObject_Get(id)if id==100 then return {m_id=100,getLocalInt=function() return 1 end} end end\n", "assert(output[1]=='BGX65G P0 FIELD_ERROR')", GATE)
 def test_object_identity_mismatch_is_visible(self):
  run_case(BASE+"\nfunction EEex_GameObject_Get(id)if id==100 then return {m_id=101,m_pos={x=10,y=20},getLocalInt=function() return 0 end,m_nModalState=0,m_pArea={}} end end\n", "assert(output[1]=='BGX65G P0 id=false xy=10,20 F=0 modal=0 area=true')",GATE)
 def test_guard_method_error_is_not_hidden(self):
  run_case(BASE+"\nfunction EEex_GameObject_Get(id)if id==100 then return {m_id=100,m_pos={x=10,y=20},getLocalInt=function()error('bad API')end,m_nModalState=0,m_pArea={}} end end\n", "assert(output[1]=='BGX65G P0 FIELD_ERROR')",GATE)
 def test_all_empty_is_safe(self):
  run_case(BASE+"\nfunction EEex_Sprite_GetInPortraitID(i)return -1 end\n", "for i=1,6 do assert(output[i]=='BGX65R1 P'..(i-1)..' absent') end",HP)
 def test_api_exception_rejected(self):
  run_case(BASE+"\nfunction EEex_Sprite_GetInPortraitID(i)error('unavailable')end\n", "assert(output[1]=='BGX65G P0 FIELD_ERROR')",GATE)
 def test_never_writes_game_and_no_attack(self):
  for source in (HP,GATE):
   txt=source.read_text()
   for bad in ['setLocalInt','C:SetGlobal','CreateCreature','MoveToObject','Attack(','ClearActions','ForceSpell','Infinity_','io.open','os.execute','os.remove']:
    self.assertNotIn(bad,txt)

if __name__ == '__main__': unittest.main()
