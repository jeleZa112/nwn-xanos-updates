#!/usr/bin/env python3
"""BGXF3 protected noncombat Lua upgrade + Khalid started-movement trace tests."""
import hashlib,os,sys,tempfile,unittest
from pathlib import Path
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parent))
import BGXFTRACE_V3_GUARDED as I
import BGXFTRACE_CONSOLE_CAPTURE as CAP
import BGX_FRIEND_TRACE_REPORT as REPORT

DIR=Path(__file__).resolve().parent
def line(seq,actor,slot,act,a1,a2,target,tslot,status):
 return (f"[BGXFTRACE] ACTION seq={seq} actor={actor} slot={slot} action={act} "
         f"a1={a1} a2={a2} target={target} target_slot={tslot} script=-1 "
         f"status={status} origin=UNKNOWN\n")
class TestBGXF3(unittest.TestCase):
 def test_new_lua_pinned_and_noncombat(self):
  p=DIR/"M_BXFR_MOTION_V3.lua"
  data=p.read_bytes()
  self.assertEqual(hashlib.sha256(data).hexdigest(),I.SOURCE_SHA)
  self.assertEqual(I.source(),data)
  s=data.decode("ascii")
  self.assertIn("if slot~=3 and not party_target then return end",s)
  self.assertIn("EEex_Action_AddSpriteStartedActionListener(M.on_started)",s)
  self.assertIn("Infinity_Log",s)
  for forbidden in ("ClearActions(", "Attack(", "ProtectObject(", "Spell(", "SetGlobal(", "EEex_Action_Queue"):
   self.assertNotIn(forbidden,s)
 def test_tp2_changes_observer_file_only(self):
  self.assertEqual([l for l in I.TP2_DATA.splitlines() if l.startswith("COPY ")],
   ["COPY ~BGXF3/staged/M_BXFR.lua~ ~override/M_BXFR.lua~"])
  self.assertIn("INSTALL_BGXFTRACE_V3_MOTION",I.TOKEN_INSTALL)
  self.assertIn("ROLLBACK_BGXFTRACE_V3_MOTION",I.TOKEN_ROLLBACK)
 def test_fail_closed_when_v2_not_last(self):
  with mock.patch.object(I.V3.V2,"require_root"),mock.patch.object(
       I.V2,"status",return_value={"status":"BGXF2_INSTALLED_VERIFIED"}),mock.patch.object(
       I,"last",return_value="~OTHER/SETUP.TP2~ #0 #0"):
   with self.assertRaisesRegex(ValueError,"BGXF2_NOT_LAST_OR_DRIFT"):
    I.baseline(I.ROOT)
 def test_preflight_failure_no_install(self):
  with mock.patch.object(I.V3.V2.V1,"processes"),mock.patch.object(
       I,"preflight",side_effect=ValueError("BAD_BASE")),mock.patch.object(
       I,"weidu") as w:
   with self.assertRaisesRegex(ValueError,"BAD_BASE"):I.install(I.ROOT)
   w.assert_not_called()
 def test_installer_backup_order(self):
  s=(DIR/"BGXFTRACE_V3_GUARDED.py").read_text()
  self.assertLess(s.index("snap=backup(root)"),s.index("(root/STAGED).write_bytes(source())"))
  self.assertLess(s.index("snap=backup(root)"),s.index("weidu(root)"))
  self.assertIn("if not LAST.match(last(root)):",s)
 def test_capture_accepts_v3_without_v2_status(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)/"game";root.mkdir()
   (root/"InfinityLoader.exe").write_bytes(b"MZfake")
   with mock.patch.dict(os.environ,{"USERPROFILE":d}),mock.patch.object(
     CAP.V3.V2.V1,"processes"),mock.patch.object(CAP.V3TRACE,"last",
     return_value="~BGXF3/SETUP-BGXF3.TP2~ #0 #0"),mock.patch.object(
     CAP.V3TRACE,"status",return_value={"status":"BGXF3_INSTALLED_VERIFIED"}),mock.patch.object(
     CAP.V2,"status",side_effect=AssertionError("V2 status cannot run when V3 is last")),mock.patch.object(
     CAP.subprocess,"Popen",return_value=mock.Mock(pid=1234)) as pop:
    result=CAP.start(root)
    self.assertEqual(result["status"],"INFINITYLOADER_CAPTURE_LAUNCH_REQUESTED")
    self.assertTrue(Path(result["console_log"]).is_file())
    pop.assert_called_once()
 def test_v3_report_includes_khalid_movement(self):
  with tempfile.TemporaryDirectory() as d:
   folder=Path(d)/"Documents/BGXAI_LIVE_REPORTS";folder.mkdir(parents=True)
   payload=("[BGXFTRACE] SESSION version=3 origin=UNKNOWN coverage=KHALID_ALL_STARTED_ACTIONS_AND_PARTY_TARGET_ACTIONS\n"
     "[BGXFTRACE] READY hook=REGISTERED writer=CONSOLE origin=UNKNOWN\n"+
     line(1,200,4,3,100,-1,100,3,"PARTY_TARGET_OBSERVED")+
     line(2,100,3,999,200,-1,200,4,"PARTY_TARGET_OBSERVED")+
     line(3,100,3,123,-1,-1,-1,-1,"TARGET_NOT_CONFIRMED_PARTY"))
   (folder/"BGXAI_FRIEND_CONSOLE_20261120T125000Z.log").write_text(payload,encoding="utf-8")
   with mock.patch.dict(os.environ,{"USERPROFILE":d}):
    r=REPORT.console_capture_report(Path(d)/"game")
   self.assertEqual(r["trace_version"],3)
   self.assertEqual(r["attack_actions_observed"],1)
   self.assertEqual(r["party_target_attack_actions"],1)
   self.assertEqual(r["all_started_actions_observed"],3)
   self.assertEqual(r["khalid_started_actions_observed"],2)
   self.assertEqual(r["nonattack_party_target_actions"],1)
   self.assertEqual(r["khalid_started_action_records"][0]["action_id"],999)
   self.assertEqual(r["khalid_started_action_records"][0]["target_slot"],4)
   self.assertEqual(r["source_or_command_origin"],"UNKNOWN")
   self.assertFalse(r["absence_proves_safety"])
 def test_duplicate_console_lines_dedup(self):
  with tempfile.TemporaryDirectory() as d:
   folder=Path(d)/"Documents/BGXAI_LIVE_REPORTS";folder.mkdir(parents=True)
   one=line(1,100,3,999,200,-1,200,4,"PARTY_TARGET_OBSERVED")
   (folder/"BGXAI_FRIEND_CONSOLE_20261120T125000Z.log").write_text(one+one)
   with mock.patch.dict(os.environ,{"USERPROFILE":d}):
    r=REPORT.console_capture_report(Path(d)/"game")
   self.assertEqual(r["all_started_actions_observed"],1)
 def test_v2_legacy_report_stays_compatible(self):
  with tempfile.TemporaryDirectory() as d:
   folder=Path(d)/"Documents/BGXAI_LIVE_REPORTS";folder.mkdir(parents=True)
   (folder/"BGXAI_FRIEND_CONSOLE_20261120T125000Z.log").write_text(
    "[BGXFTRACE] SESSION version=2 origin=UNKNOWN coverage=STARTED_PARTY_ATTACK_ACTIONS_ONLY\n"+
    line(1,200,4,3,100,-1,100,3,"PARTY_TARGET_OBSERVED"))
   with mock.patch.dict(os.environ,{"USERPROFILE":d}):
    r=REPORT.console_capture_report(Path(d)/"game")
   self.assertEqual(r["attack_actions_observed"],1)
   self.assertEqual(r["party_target_attack_actions"],1)
   self.assertEqual(r["khalid_started_actions_observed"],0)
if __name__=="__main__":unittest.main()
