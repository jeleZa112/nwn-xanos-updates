#!/usr/bin/env python3
"""Offline regression for INTERNAL Lua console fallback, guarded patch and capture."""
from pathlib import Path
from unittest import mock
import hashlib,os,sys,tempfile,unittest
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import BGXFTRACE_V2_GUARDED as I
import BGXFTRACE_CONSOLE_CAPTURE as L
import BGX_FRIEND_TRACE_REPORT as R

def line(seq,action,target=102,slot=2):
 return (f"[BGXFTRACE] ACTION seq={seq} actor=101 slot=1 action={action} a1={target} a2=-1 "
         f"target={target} target_slot={slot} script=-1 status=PARTY_TARGET_OBSERVED origin=UNKNOWN\n")

class TestBGXF2(unittest.TestCase):
 def test_lua_source_sha_and_no_attack_mutations(self):
  raw=(HERE/"M_BXFR_CONSOLE_V2.lua").read_bytes()
  self.assertEqual(hashlib.sha256(raw).hexdigest(),I.SOURCE_SHA)
  self.assertEqual(I.pinned_source(),raw)
  s=raw.decode("ascii")
  self.assertIn('type(io)=="table"',s)
  self.assertIn("Infinity_Log",s)
  self.assertIn("pcall(print,line)",s)
  self.assertIn("EEex_Action_AddSpriteStartedActionListener(M.on_started)",s)
  self.assertIn("M.writer=M.handle and \"FILE\" or \"CONSOLE\"",s)
  for suspect in ("ClearActions(", "Spell(", "Attack(", "ProtectObject(", "SetGlobal(", "EEex_Action_Queue"):
   self.assertNotIn(suspect,s)
 def test_distinct_wei_du_file_only(self):
  self.assertEqual([x for x in I.TP2_DATA.splitlines() if x.startswith("COPY ")],
    ["COPY ~BGXF2/staged/M_BXFR.lua~ ~override/M_BXFR.lua~"])
  self.assertIn("BGXFTRACE_V1_NOT_LAST_OR_DRIFT",(HERE/"BGXFTRACE_V2_GUARDED.py").read_text())
 def test_no_weidu_if_preflight_fails(self):
  with mock.patch.object(I.V3.V2.V1,"processes"),mock.patch.object(
    I,"preflight",side_effect=ValueError("bad old source")),mock.patch.object(I,"run_weidu") as runner:
   with self.assertRaisesRegex(ValueError,"bad old source"):I.install(I.ROOT)
   runner.assert_not_called()
 def test_install_backup_before_game_write(self):
  s=(HERE/"BGXFTRACE_V2_GUARDED.py").read_text()
  self.assertLess(s.index("snap=backup(root)"),s.index("(root/STAGED).write_bytes(pinned_source())"))
  self.assertLess(s.index("snap=backup(root)"),s.index("run_weidu(root)"))
  self.assertIn('TOKEN_INSTALL="INSTALL_BGXFTRACE_V2_CONSOLE"',s)
 def test_rollback_last_only(self):
  with mock.patch.object(I.V3.V2.V1,"processes"),mock.patch.object(
       I,"status",return_value={"status":"BGXF2_INSTALLED_VERIFIED"}),mock.patch.object(
       I.V1,"last",return_value="~OTHER/SETUP.TP2~ #0 #0"):
   with self.assertRaisesRegex(ValueError,"BGXF2_NOT_LAST"):
    I.rollback(I.ROOT)
 def test_capture_launch_uses_standard_exe_and_no_ini(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)/"game";root.mkdir();(root/"InfinityLoader.exe").write_bytes(b"MZsome executable")
   with mock.patch.dict(os.environ,{"USERPROFILE":d}),mock.patch.object(
        L.V3.V2.V1,"processes"),mock.patch.object(
        L.V3TRACE,"last",return_value="~BGXF2/SETUP-BGXF2.TP2~ #0 #0"),mock.patch.object(
        L.V2,"status",return_value={"status":"BGXF2_INSTALLED_VERIFIED"}),mock.patch.object(
        L.subprocess,"Popen",return_value=mock.Mock(pid=12345)) as pop:
    info=L.start(root)
    self.assertEqual(info["status"],"INFINITYLOADER_CAPTURE_LAUNCH_REQUESTED")
    self.assertEqual(pop.call_args[0][0],[str(root/"InfinityLoader.exe")])
    self.assertEqual(pop.call_args.kwargs["cwd"],root)
    self.assertEqual(pop.call_args.kwargs["stderr"],L.subprocess.STDOUT)
    self.assertTrue(Path(info["console_log"]).is_file())
    self.assertFalse((root/"InfinityLoader.ini").exists())
 def test_read_console_dedup_unknown_source(self):
  with tempfile.TemporaryDirectory() as d:
   folder=Path(d)/"Documents/BGXAI_LIVE_REPORTS";folder.mkdir(parents=True)
   text=("[BGXFTRACE] SESSION version=2 origin=UNKNOWN coverage=STARTED_PARTY_ATTACK_ACTIONS_ONLY\n"
         "[BGXFTRACE] READY hook=REGISTERED writer=CONSOLE origin=UNKNOWN\n"+line(1,3)+line(1,3))
   (folder/"BGXAI_FRIEND_CONSOLE_20261120T140000Z.log").write_text(text,encoding="utf-8")
   with mock.patch.dict(os.environ,{"USERPROFILE":d}):
    r=R.console_capture_report(Path(d)/"game")
   self.assertEqual(r["status"],"CAPTURE_PARTY_ACTIONS_OBSERVED")
   self.assertEqual(r["attack_actions_observed"],1)
   self.assertEqual(r["party_target_attack_actions"],1)
   self.assertEqual(r["party_target_pairs"][0]["origin"],"UNKNOWN")
 def test_no_console_log_is_not_proof_of_safety(self):
  with tempfile.TemporaryDirectory() as d:
   with mock.patch.dict(os.environ,{"USERPROFILE":d}):
    self.assertEqual(R.console_capture_report(Path(d))["status"],"CAPTURE_DIRECTORY_ABSENT")
 def test_malformed_target_does_not_prove_party(self):
  with tempfile.TemporaryDirectory() as d:
   folder=Path(d)/"Documents/BGXAI_LIVE_REPORTS";folder.mkdir(parents=True)
   data=("[BGXFTRACE] READY hook=REGISTERED writer=CONSOLE origin=UNKNOWN\n"+
         line(1,3,target=9999,slot=-1).replace("status=PARTY_TARGET_OBSERVED","status=TARGET_NOT_CONFIRMED_PARTY"))
   (folder/"BGXAI_FRIEND_CONSOLE_20261120T140000Z.log").write_text(data)
   with mock.patch.dict(os.environ,{"USERPROFILE":d}):
    r=R.console_capture_report(Path(d))
   self.assertEqual(r["party_target_attack_actions"],0)
   self.assertFalse(r["absence_proves_safety"])
if __name__=="__main__":unittest.main()
