#!/usr/bin/env python3
"""V3 guarded updater unit tests: fail-closed and no game modifications."""
import ast,unittest
from pathlib import Path
from unittest import mock
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import BGXRANGED_V3_GUARDED_INSTALL as U
class GuardedV3Tests(unittest.TestCase):
    def test_import_and_parse(self):
        ast.parse((HERE/"BGXRANGED_V3_GUARDED_INSTALL.py").read_text())
    def test_three_distinct_versions_and_components(self):
        self.assertNotEqual(U.EXE,U.V2.EXE)
        self.assertNotEqual(U.PROOF,U.V2.PROOF)
        self.assertEqual(U.V2_SHA,"1991f04d0a6acc556f53e03a7aa4a9fcaab252668b689f3d6726be118ca7c1e2")
        self.assertEqual(U.SOURCE_SHA,"d6956a35bf80c2a451a335fafacd413125dac11a9096d694eaa59063255468fe")
    def test_user_approval_required(self):
        src=(HERE/"BGXRANGED_V3_GUARDED_INSTALL.py").read_text()
        self.assertIn("INSTALL_BGXRANGED_V3_WEAPON_FIX",src)
        self.assertIn("ROLLBACK_BGXRANGED_V3_WEAPON_FIX",src)
        self.assertIn('if args.mode=="status":result=status(root)',src)
        self.assertIn('elif args.mode=="preflight":result=V3.run(root)',src)
    def test_weidu_never_retries_on_error(self):
        bad=mock.Mock(returncode=1,stdout="",stderr="ERROR: TEST")
        with mock.patch.object(U.subprocess,"run",return_value=bad) as execute:
            with self.assertRaisesRegex(ValueError,"WEIDU_STOP_MANUAL_REVIEW"):
                U.weidu(U.ROOT)
            self.assertEqual(execute.call_count,1)
    def test_refuse_unknown_v2_before_snapshot(self):
        with mock.patch.object(U.V2.V1,"processes"),mock.patch.object(U,"check_root"),mock.patch.object(U.V3,"validate",side_effect=ValueError("V2_BCS_NOT_EXACT")),mock.patch.object(U,"backup") as backup:
            with self.assertRaisesRegex(ValueError,"V2_BCS_NOT_EXACT"):
                U.install(U.ROOT)
            backup.assert_not_called()
    def test_refuse_rollback_when_v3_not_last(self):
        with mock.patch.object(U.V2.V1,"processes"),mock.patch.object(U,"status",return_value={"status":"BGXRANGED_V3_INSTALLED_VERIFIED"}),mock.patch.object(U,"last",return_value="~OTHER/SETUP-OTHER.TP2~ #0 #0"):
            with self.assertRaisesRegex(ValueError,"V3_NOT_LAST"):U.rollback(U.ROOT)
    def test_backup_precedes_install(self):
        s=(HERE/"BGXRANGED_V3_GUARDED_INSTALL.py").read_text()
        self.assertLess(s.index("snap=backup(root)"),s.index("(root/STAGED).write_bytes(merged)"))
        self.assertLess(s.index("weidu(root)"),s.index("verified=status(root)"))
    def test_no_destructive_inventory(self):
        s=(HERE/"BGXRANGED_V3_GUARDED_INSTALL.py").read_text()
        self.assertNotIn("FillSlot(",s)
        self.assertNotIn("XEquipItem(",s)
if __name__=="__main__":unittest.main()
