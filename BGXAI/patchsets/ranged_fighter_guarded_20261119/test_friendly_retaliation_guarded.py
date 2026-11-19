#!/usr/bin/env python3
"""Fail-closed offline tests: source-safe retaliation patch, no game writes."""
from pathlib import Path
from unittest import mock
import sys,unittest,tempfile
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
 def test_native_decompile_uses_a_temp_override_copy(self):
  # The user's WeiDU 251 printed only header and no BAF when passed an
  # absolute original game path. Reproduce the successful menu-135 contract.
  with tempfile.TemporaryDirectory() as d:
   from pathlib import Path
   root=Path(d)/"game";(root/"override").mkdir(parents=True)
   (root/"override/WTASIGHT.BCS").write_bytes(b"test original")
   tmp=Path(d)/"temp";tmp.mkdir()
   def fake_weidu(args,**kwargs):
    output=Path(args[args.index("--out")+1]);inp=Path(args[-1])
    self.assertEqual(inp.name,"WTASIGHT.BCS")
    self.assertEqual(output.name,"WTASIGHT.BAF")
    self.assertEqual(inp.parent,output.parent)
    self.assertNotEqual(inp.parent,root/"override")
    self.assertEqual(kwargs["cwd"],inp.parent)
    self.assertEqual(inp.read_bytes(),b"test original")
    output.write_text(fixture("WTASIGHT"),encoding="utf-8")
    return mock.Mock(returncode=0,stdout="ok",stderr="")
   with mock.patch.object(A,"digest",return_value=A.SCRIPTS["WTASIGHT"]["sha"]):
    with mock.patch.object(A.subprocess,"run",side_effect=fake_weidu) as runner:
     res=A.source_baf(Path(d)/"weidu.exe",root,tmp,"WTASIGHT")
     self.assertEqual(len(A.text_blocks(res)),6)
     self.assertEqual(runner.call_count,1)
 def test_game_resource_decompile_uses_relative_name(self):
  with tempfile.TemporaryDirectory() as d:
   from pathlib import Path
   root=Path(d)/"game";tmp=Path(d)/"temp";tmp.mkdir()
   def fake_weidu(args,**kwargs):
    inp=Path(args[-1]);out=Path(args[args.index("--out")+1])
    self.assertEqual(str(inp),"DPLAYER.BCS")
    self.assertEqual(out.name,"DPLAYER.BAF")
    self.assertEqual(out.parent,kwargs["cwd"])
    out.write_text(fixture("DPLAYER"),encoding="utf-8")
    return mock.Mock(returncode=0,stdout="",stderr="")
   with mock.patch.object(A.subprocess,"run",side_effect=fake_weidu):
    self.assertEqual(len(A.text_blocks(A.source_baf(Path(d)/"weidu.exe",root,tmp,"DPLAYER"))),2)
 def test_compile_separate_temp_output(self):
  with tempfile.TemporaryDirectory() as d:
   from pathlib import Path
   tmp=Path(d);root=tmp/"game"
   data=b"SC\n"+b"CR\nCO\nx\nCR\n"+b"CR\nCO\ny\nCR\nSC\n"
   def fake_weidu(args,**kwargs):
    inp=Path(args[-1]);out=Path(args[args.index("--out")+1])
    self.assertEqual(inp.parent,out.parent)
    self.assertEqual(inp.name,"DPLAYER.BAF")
    self.assertEqual(out.name,"DPLAYER.BCS")
    self.assertNotEqual(inp.parent,tmp/"source")
    out.write_bytes(data)
    return mock.Mock(returncode=0,stdout="",stderr="")
   with mock.patch.object(A.subprocess,"run",side_effect=fake_weidu):
    self.assertEqual(A.native_compile(tmp/"weidu.exe",root,tmp,"DPLAYER",fixture("DPLAYER")),data)
if __name__=="__main__":unittest.main()
