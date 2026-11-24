"""V126 tests: reversible UI probe only on exact installed V125-like source."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock
import zipfile
import unittest

import visible_row_guarded_v1 as q

FIXTURE=b'''function clean(str)
  return str
end
menu
{
  name 'WORLD_MESSAGES'
  list
  {
    label
    {
      text lua "BG_EET_RU_LogView(clean(combatLog[rowNumber]))"
    }
    table "combatLog"
  }
}
'''

class Probe(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory(prefix="V126_GUARDED_FIXTURE_")
        self.base=Path(self.tmp.name)
        self.game=self.base/"game"
        (self.game/"override").mkdir(parents=True)
        (self.game/"chitin.key").write_bytes(b"TEST")
        self.ui=self.game/"override"/"UI.MENU"
        self.ui.write_bytes(FIXTURE)
        self.work=self.base/"out"
        self.work.mkdir()
        self.path=self.work/"SEND_TO_CHATGPT_BG_EET_RU.zip"
        with zipfile.ZipFile(self.path,"w") as z:z.writestr("00_LEGACY.txt",b"PRESERVE")
        self.log=self.work/"BG_EET_RU_V126_VISIBLE_ROWS.tsv"
    def tearDown(self):self.tmp.cleanup()
    def install(self):
        with mock.patch.object(q,"closed",return_value=(True,"CLOSED")):
            return q._status(self.game,self.work,"install",q.sha(FIXTURE),lambda _: True)
    def rollback(self):
        with mock.patch.object(q,"closed",return_value=(True,"CLOSED")):
            return q._status(self.game,self.work,"rollback",q.sha(FIXTURE),lambda _: True)

    def test_candidate_preserves_original_expression_and_wrapper(self):
        b=q.candidate(FIXTURE,self.log)
        self.assertIn(b'text lua "BG_EET_RU_V126_RowRecord(rowNumber, BG_EET_RU_LogView(clean(combatLog[rowNumber])))"',b)
        self.assertIn(b"return value -- identical display value",b)
        self.assertEqual(b.count(b"function BG_EET_RU_V126_RowRecord("),1)
        self.assertNotIn(b"EEex_Hook",b)
    def test_candidate_does_not_replace_gameplay_text(self):
        out=q.candidate(FIXTURE,self.log)
        self.assertEqual(out.count(b'combatLog[rowNumber]'),1)
        self.assertEqual(out.count(b'table "combatLog"'),1)
    def test_idempotent_source_rejected(self):
        with self.assertRaisesRegex(RuntimeError,"ALREADY_PRESENT"):
            q.candidate(q.candidate(FIXTURE,self.log),self.log)
    def test_extra_renderer_rejected(self):
        with self.assertRaisesRegex(RuntimeError,"NOT_UNIQUE"):
            q.candidate(FIXTURE+FIXTURE,self.log)
    def test_foreign_expression_rejected(self):
        with self.assertRaisesRegex(RuntimeError,"UNEXPECTED"):
            q.candidate(FIXTURE.replace(b'BG_EET_RU_LogView(clean(combatLog[rowNumber]))',b'tostring(combatLog[rowNumber])'),self.log)
    def test_clean_anchor_missing_rejected(self):
        with self.assertRaisesRegex(RuntimeError,"NOT_UNIQUE"):
            q.candidate(FIXTURE.replace(b"function clean(str)",b"function different(str)"),self.log)
    def test_installs_exact_patched_ui_with_external_backup(self):
        result=self.install()
        self.assertEqual(result["status"],"V126_VISIBLE_ROW_OBSERVER_INSTALLED_AWAITING_RUNTIME_UI_TEST")
        self.assertEqual(result["game_files_written"],1)
        state=q.load_state(self.work)
        self.assertEqual(state["phase"],"INSTALLED")
        self.assertEqual(state["old_sha"],q.sha(FIXTURE))
        self.assertEqual(q.sha(self.ui.read_bytes()),state["new_sha"])
        self.assertTrue(Path(state["backup"]).is_relative_to(self.work))
        self.assertEqual(Path(state["backup"]).read_bytes(),FIXTURE)
        self.assertEqual(len(list((self.game/"override").iterdir())),1)
    def test_rollback_restores_byte_exact_ui(self):
        self.install()
        ret=self.rollback()
        self.assertEqual(ret["game_files_written"],1)
        self.assertEqual(self.ui.read_bytes(),FIXTURE)
        self.assertEqual(q.load_state(self.work)["phase"],"ROLLED_BACK")
    def test_no_install_when_game_running(self):
        with mock.patch.object(q,"closed",return_value=(False,"baldur.exe")):
            with self.assertRaisesRegex(RuntimeError,"CLOSE_GAME"):
                q._status(self.game,self.work,"install",q.sha(FIXTURE),lambda _: True)
        self.assertEqual(self.ui.read_bytes(),FIXTURE)
    def test_no_install_without_typed_approval(self):
        with mock.patch.object(q,"closed",return_value=(True,"CLOSED")):
            r=q._status(self.game,self.work,"install",q.sha(FIXTURE),lambda _: False)
        self.assertEqual(r["status"],"INSTALL_NOT_APPROVED")
        self.assertEqual(self.ui.read_bytes(),FIXTURE)
        self.assertIsNone(q.load_state(self.work))
    def test_ui_exact_sha_drift_blocks_install(self):
        with self.assertRaisesRegex(RuntimeError,"LIVE_UI_SHA_NOT_V125_PINNED"):
            q._status(self.game,self.work,"install","0"*64,lambda _: True)
        self.assertEqual(self.ui.read_bytes(),FIXTURE)
    def test_pending_state_recovery_status(self):
        self.install()
        s=q.load_state(self.work);s["phase"]="PREPARED"
        q.save_json_atomic(q.state_file(self.work),s)
        st=q._status(self.game,self.work,"status",q.sha(FIXTURE),lambda _:False)
        self.assertEqual(st["status"],"PREPARED_RECOVERY_HOLD")
    def test_foreign_ui_after_install_fails_closed(self):
        self.install()
        self.ui.write_bytes(b"CHANGED_BY_FOREIGN_MOD")
        with self.assertRaisesRegex(RuntimeError,"UI_CHANGED"):
            self.rollback()
    def test_parse_visible_rows_without_inventing_message_pointer(self):
        self.log.write_text("ROW\t9\tХалид промахивается\nROW\t10\tМеч повреждает\n",encoding="utf8")
        c=q.capture(self.work)
        self.assertEqual(c["rows"],2)
        self.assertFalse(c["row_to_weapon_join_verified"])
        self.assertNotIn("message_ptr",c["samples"][0])
    def test_report_one_zip_preserves_old_members(self):
        q.zip_report(self.game,self.path,{"schema":q.SCHEMA,"status":"PASS"})
        q.zip_report(self.game,self.path,{"schema":q.SCHEMA,"status":"PASS"})
        with zipfile.ZipFile(self.path) as z:
            self.assertIsNone(z.testzip())
            self.assertEqual(z.namelist(),["00_LEGACY.txt",q.ENTRY])
            self.assertEqual(z.read("00_LEGACY.txt"),b"PRESERVE")
    def test_lua_emits_console_marker_without_file_io(self):
        lua=q.lua_observer(self.log)
        self.assertIn("pcall(print,'BG_EET_RU_V126_ROW",lua)
        self.assertIn("type(io)=='table'",lua)
        self.assertIn("return value -- identical display value",lua)
    def test_console_capture_parses_prefixed_engine_prints(self):
        log=self.work/"BG_EET_RU_V126_CONSOLE_20261124T150000000000Z.log"
        log.write_text("EEex log: BG_EET_RU_V126_ROW\t19\tХалид промахнулся\n",encoding="utf8")
        out=q.capture(self.work)
        self.assertEqual(out["rows"],1)
        self.assertEqual(out["samples"][0]["ui_row_number"],19)
        self.assertFalse(out["row_to_weapon_join_verified"])
    def test_launcher_capture_after_guarded_install(self):
        self.install()
        (self.game/"InfinityLoader.exe").write_bytes(b"MZ"+b"test")
        class Proc:
            def wait(self):return 0
        def fake_popen(cmd,**kwargs):
            kwargs["stdout"].write(b"game: BG_EET_RU_V126_ROW\t22\tTEST MISS\n")
            return Proc()
        with mock.patch.object(q,"closed",return_value=(True,"CLOSED")):
            with mock.patch.object(q.subprocess,"Popen",side_effect=fake_popen):
                result=q.launch_capture(self.game,self.work)
        self.assertEqual(result["capture_exit_code"],0)
        self.assertEqual(result["captured"]["rows"],1)
        self.assertEqual(result["captured"]["samples"][0]["ui_row_number"],22)
        self.assertEqual(result["game_files_written"],0)
        self.assertEqual(result["status"],"V126_CAPTURED_RENDERED_ROWS_UNCORRELATED")
    def test_patched_visible_row_passes_game_value_unchanged(self):
        output=q.candidate(FIXTURE,self.log)
        self.assertIn(b"return value",output)
        self.assertIn(b'rowNumber, BG_EET_RU_LogView(clean(combatLog[rowNumber]))',output)

if __name__=="__main__":unittest.main()
