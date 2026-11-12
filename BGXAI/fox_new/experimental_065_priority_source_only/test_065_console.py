"""Read-only user console smoke snippet against mocked live x64 sprite structures."""
import unittest
from pathlib import Path
from lua65_harness import run_case
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'BGXAI65_CLASS_HP_CONSOLE.lua'

class ConsoleProbeTests(unittest.TestCase):
 def test_reads_two_party_class_and_hp(self):
  run_case(r'''
  output={}
  C={DisplayText=function(self,s)output[#output+1]=s end}
  function EEex_Sprite_GetInPortraitID(i)
    if i==0 then return 100 elseif i==1 then return 101 end
  end
  function EEex_GameObject_Get(id)
    if id==100 then return {m_typeAI={m_Class=2},m_baseStats={m_hitPoints=14},m_derivedStats={m_nMaxHitPoints=14}} end
    if id==101 then return {m_typeAI={m_Class=1},m_baseStats={m_hitPoints=7},m_derivedStats={m_nMaxHitPoints=12}} end
  end
  function setLocalInt()error('UNEXPECTED WRITE')end
  ''',"""assert(#output==6)
  assert(output[1]=='BGX65 P0 2:14/14')
  assert(output[2]=='BGX65 P1 1:7/12')
  assert(output[3]=='BGX65 P2 absent')""",SOURCE)
 def test_fails_safe_when_field_missing(self):
  run_case(r'''
  output={}; C={DisplayText=function(_,s)output[#output+1]=s end}
  function EEex_Sprite_GetInPortraitID(i)if i==0 then return 100 end end
  function EEex_GameObject_Get(id)return {m_typeAI={m_Class=2},m_baseStats={m_hitPoints=4}} end
  ''',"""assert(output[1]=='BGX65 P0 API_ERROR');assert(output[2]=='BGX65 P1 absent')""",SOURCE)
 def test_command_no_game_writes(self):
  text=SOURCE.read_text()
  for bad in ['setLocalInt','C:SetGlobal','CreateCreature','MoveToObject','Attack(','ClearActions','WEIDU','os.','io.']:
   self.assertNotIn(bad,text)

if __name__=='__main__':unittest.main()
