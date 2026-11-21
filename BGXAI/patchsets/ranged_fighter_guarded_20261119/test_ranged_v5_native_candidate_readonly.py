#!/usr/bin/env python3
"""Mocks only. Native TEST with current EET executable remains user-side RO."""
import pathlib
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import BGXRANGED_V5_NATIVE_CANDIDATE_READONLY as V

def fake_bcs(tags):
    return b"SC\n"+b"".join(b"CR\nCO\n"+str(x).encode("ascii")+b"\nCR\n" for x in tags)+b"SC\n"

def baf_fixture():
    base=V.V4.read_text("utf-8")
    extra="IF\n  ActionListEmpty()\nTHEN\n  RESPONSE #100\n    NoAction()\nEND\n"
    return base+"\n"+extra*(V.EXPECTED_BLOCKS-3)

class NativeV5Readonly(unittest.TestCase):
    def test_expected_source_handoff_contract(self):
        proof=V.source_contract(baf_fixture(),V.V4.read_text("utf-8"),
                                  V.V5.read_text("utf-8"))
        self.assertEqual(proof["status"],"V5_SOURCE_PRECONDITIONS_MATCH_INSTALLED_V4")
        self.assertEqual(proof["observed_live_bcs_decompiled_blocks"],1162)
        self.assertTrue(proof["candidate_only_two_range_changes"])

    def test_actual_v4_script_mismatch_stops(self):
        mutated=baf_fixture().replace(
            "Range(NearestEnemyOf(Myself),4)",
            "Range(NearestEnemyOf(Myself),8)",1)
        with self.assertRaisesRegex(ValueError,"LIVE_FIRST_THREE_NOT_EXACT_V4"):
            V.source_contract(mutated,V.V4.read_text("utf-8"),
                              V.V5.read_text("utf-8"))

    def test_compiled_v5_only_two_blocks_differ(self):
        orig=fake_bcs(["A4","B10","C4"]+["KEEP%04d"%n for n in range(3,1162)])
        compiled=fake_bcs(["A6","B10","C6"])
        binary,proof=V.splice_native(orig,compiled)
        self.assertEqual(proof["changed_blocks"],[1,3])
        self.assertEqual(proof["preserved_blocks"],1160)
        self.assertEqual(V.bcs_parts(binary)[3:],V.bcs_parts(orig)[3:])
        self.assertEqual(V.bcs_parts(binary)[1],V.bcs_parts(orig)[1])
        self.assertNotEqual(V.sha(binary),V.sha(orig))

    def test_compiler_changed_bow_return_stops(self):
        orig=fake_bcs(["A4","B10","C4"]+["KEEP%04d"%n for n in range(3,1162)])
        with self.assertRaisesRegex(ValueError,"MIDDLE_RANGED_RETURN_NATIVE_BLOCK_DRIFT"):
            V.splice_native(orig,fake_bcs(["A6","B11","C6"]))

    def test_unknown_native_block_count_stops(self):
        orig=fake_bcs(["A4","B10","C4"])
        with self.assertRaisesRegex(ValueError,"NATIVE_BCS_COUNT_DRIFT"):
            V.splice_native(orig,fake_bcs(["A6","B10","C6"]))

    def test_last_weidu_guard_is_strict(self):
        self.assertTrue(V.EXPECTED_LAST.match(
            r"~BGXFENEMY\SETUP-BGXFENEMY.TP2~ #0 #0 // installed"))
        self.assertFalse(V.EXPECTED_LAST.match(
            r"~BGXF3\SETUP-BGXF3.TP2~ #0 #0"))
        self.assertFalse(V.EXPECTED_LAST.match(
            r"~BGXFENEMY\SETUP-BGXFENEMY.TP2~ #0 #1"))

    def test_diagnostic_flags_other_ranged_attack_sources(self):
        extra="""IF
  InParty(Myself)
  IsWeaponRanged(Myself)
  ActionListEmpty()
  Range(NearestEnemyOf(Myself),4)
THEN
  RESPONSE #100
    AttackOneRound(NearestEnemyOf(Myself))
END
"""
        text=V.V4.read_text("utf-8")+extra
        observed=V.attack_sources(text)
        self.assertTrue(any(x["ranged_attack_condition"] for x in observed))
        self.assertTrue(all("block" in x and "actions" in x for x in observed))

    def test_native_preview_mock_full_without_game_writes(self):
        with tempfile.TemporaryDirectory() as dirname:
            root=pathlib.Path(dirname)
            (root/"override").mkdir()
            (root/"chitin.key").write_bytes(b"MOCK")
            old=fake_bcs(["A4","B10","C4"]+["KEEP%04d"%n for n in range(3,1162)])
            compiled=fake_bcs(["A6","B10","C6"])
            (root/V.BCS).write_bytes(old)
            wtasight=(root/V.WTASIGHT);wtasight.write_bytes(b"MOCK_WTASIGHT")
            (root/"WeiDU.log").write_text("MOCK_WEIDU_LOG")
            weidu=root/"weidu.exe";weidu.write_bytes(b"MZFAKE")
            watch=[root/V.BCS,wtasight,root/"WeiDU.log"]
            before={str(p):V.sha(p.read_bytes()) for p in watch}
            def compile_stub(command,**kwargs):
                out=pathlib.Path(command[command.index("--out")+1])
                (out/"BGXAIW5.BCS").write_bytes(compiled)
                return SimpleNamespace(returncode=0,stdout="mock compiled",stderr="")
            with patch.object(V,"GAME",root), \
                 patch.object(V,"EXACT_BCS_SHA",V.sha(old)), \
                 patch.object(V,"EXACT_WTASIGHT_SHA",V.sha(wtasight.read_bytes())), \
                 patch.object(V.subprocess,"run",side_effect=compile_stub):
                report=V.preview(root,old,baf_fixture(),weidu,
                        r"~BGXFENEMY\SETUP-BGXFENEMY.TP2~ #0 #0")
            self.assertEqual(report["status"],"BGXRANGED_V5_NATIVE_READONLY_CANDIDATE_PASS")
            self.assertEqual(report["changed_blocks"],[1,3])
            self.assertEqual(report["preserved_blocks"],1160)
            self.assertFalse(report["game_modified"])
            self.assertFalse(report["install_performed"])
            self.assertFalse(report["predicted_latency_improvement_verified"])
            after={str(p):V.sha(p.read_bytes()) for p in watch}
            self.assertEqual(before,after)

    def test_native_preview_rejects_wrong_last_before_compiler(self):
        with tempfile.TemporaryDirectory() as dirname:
            root=pathlib.Path(dirname)
            with patch.object(V,"GAME",root):
                with self.assertRaisesRegex(ValueError,"BGXFENEMY_NOT_LAST_WEIDU"):
                    V.preview(root,b"",b"",root/"NOT_WEIDU",
                              r"~BGXF3\SETUP-BGXF3.TP2~ #0 #0")

    def test_native_preview_rejects_unrecognized_bcs(self):
        with tempfile.TemporaryDirectory() as dirname:
            root=pathlib.Path(dirname)
            with patch.object(V,"GAME",root):
                with self.assertRaisesRegex(ValueError,"LIVE_BDDEFAI_SHA_DRIFT"):
                    V.preview(root,b"GARBAGE",b"",root/"NOT_WEIDU",
                             r"~BGXFENEMY\SETUP-BGXFENEMY.TP2~ #0 #0")

if __name__=="__main__":
    unittest.main(verbosity=2)
