#!/usr/bin/env python3
"""Fail-closed offline tests: source-safe retaliation patch, no game writes."""
from pathlib import Path
from unittest import mock
import sys,unittest
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import BGX_FRIENDLY_RETALIATION_GUARDED as A
def block(cond,action):
 return "IF\n  ActionListEmpty()\n"+cond+"\nTHEN\n  RESPONSE #100\n    "+action+"\nEND\n"
def fixture(name):
 s=A.SCRIPTS[name];arr=[]
 for i in range(1,s["count"]+1):
  if i in s["patch"]:
   a,target=s["patch"][i]
   if target=="LastAttackerOf(Myself)":
    cond="  AttackedBy([ANYONE],DEFAULT)"
   else:
    cond="  See("+target+")"
   arr.append(block(cond,a))
  else:
   arr.append(block("  True()","NoAction()"))
 return "\n".join(arr)
class FriendlyFix(unittest.TestCase):
 def test_all_expected_script_shapes(self):
  self.assertEqual({n:s["count"] for n,s in A.SCRIPTS.items()},
      {"WTASIGHT":6,"DPLAYER":2,"PRIEST1":5})
  self.assertEqual(A.SCRIPTS["WTASIGHT"]["sha"],
      "d3055bb06a50e2a6152e4ace8d2753e5450df28e066148eae2a0c01651e24605")
  self.assertIsNone(A.SCRIPTS["DPLAYER"]["sha"])
  self.assertEqual(A.SCRIPTS["PRIEST1"]["sha"],
      "e241bf986f4dfce72a9a5784d21111b10d0ee979ef5e065f6f6e145012434b3a")
 def test_five_unsafe_attacks_all_gated(self):
  count=0
  for name,spec in A.SCRIPTS.items():
   src=fixture(name);patched=A.guard_baf(src,name)
   original=A.text_blocks(src);updated=A.text_blocks(patched)
   self.assertEqual(len(original),len(updated))
   for i,(before,after) in enumerate(zip(original,updated),1):
    if i not in spec["patch"]:
     self.assertEqual(before.group(),after.group())
    else:
     target=spec["patch"][i][1]
     self.assertIn("!InParty("+target+")",after.group())
     self.assertIn("!Allegiance("+target+",GOODCUTOFF)",after.group())
     self.assertIn(spec["patch"][i][0],after.group())
     count+=1
  self.assertEqual(count,5)
 def test_wrong_script_target_refused(self):
  text=fixture("DPLAYER").replace("LastAttackerOf(Myself)","LastHitter(Myself)")
  with self.assertRaisesRegex(ValueError,"ACTION_SIGNATURE_MISMATCH"):
   A.guard_baf(text,"DPLAYER")
 def test_attack_event_required(self):
  text=fixture("WTASIGHT").replace("AttackedBy([ANYONE],DEFAULT)","True()")
  with self.assertRaisesRegex(ValueError,"ATTACK_EVENT_SIGNATURE"):
   A.guard_baf(text,"WTASIGHT")
 def test_second_install_refused(self):
  text=fixture("DPLAYER").replace("  AttackedBy([ANYONE],DEFAULT)",
   "  AttackedBy([ANYONE],DEFAULT)\n  !InParty(LastAttackerOf(Myself))")
  with self.assertRaisesRegex(ValueError,"ALREADY_GUARDED_STOP"):
   A.guard_baf(text,"DPLAYER")
 def test_wrong_block_count_refused(self):
  with self.assertRaisesRegex(ValueError,"BAF_BLOCK_COUNT"):
   A.guard_baf(fixture("PRIEST1")+"\n"+block("  True()","NoAction()"),"PRIEST1")
 def test_tp2_distinct_new_component(self):
  self.assertIn("COPY ~BGXFRIEND/staged/DPLAYER.BCS~ ~override/DPLAYER.BCS~",A.TP2_DATA)
  self.assertIn("COPY ~BGXFRIEND/staged/WTASIGHT.BCS~ ~override/WTASIGHT.BCS~",A.TP2_DATA)
  self.assertIn("COPY ~BGXFRIEND/staged/PRIEST1.BCS~ ~override/PRIEST1.BCS~",A.TP2_DATA)
  self.assertEqual(A.TOKEN_INSTALL,"INSTALL_BGXFRIEND_RETALIATION_GUARD")
 def test_rollback_requires_last(self):
  with mock.patch.object(A.V3.V2.V1,"processes"),mock.patch.object(
   A,"status",return_value={"status":"BGXFRIEND_INSTALLED_VERIFIED"}),mock.patch.object(
   A,"last",return_value="~OTHER/SETUP.TP2~ #0 #0"):
   with self.assertRaisesRegex(ValueError,"FRIEND_COMPONENT_NOT_LAST"):
    A.rollback(A.ROOT)
 def test_failure_does_not_run_weidu(self):
  with mock.patch.object(A.V3.V2.V1,"processes"),mock.patch.object(
   A,"stage_data",side_effect=ValueError("WEIDU_COMPILE_STOP")),mock.patch.object(
   A,"digest",return_value="synthetic"),mock.patch.object(A,"run_weidu") as rw:
   with self.assertRaisesRegex(ValueError,"WEIDU_COMPILE_STOP"):
    A.install(A.ROOT)
   rw.assert_not_called()
 def test_guarded_mutation(self):
  source=(HERE/"BGX_FRIENDLY_RETALIATION_GUARDED.py").read_text()
  self.assertLess(source.index("snap=backup(root)"),source.index("(root/STAGED(name)).write_bytes(data)"))
  self.assertLess(source.index("run_weidu(root)\n result=status(root)"),
                  source.index('if result["status"]!="BGXFRIEND_INSTALLED_VERIFIED"'))
  self.assertIn("if (root/\"override/DPLAYER.BCS\").exists()",source)
  self.assertIn("DPLAYER_OVERRIDE_NOT_REMOVED",source)
  self.assertNotIn("ClearActions(",source)
if __name__=="__main__":unittest.main()
