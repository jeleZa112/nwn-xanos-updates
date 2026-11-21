#!/usr/bin/env python3
"""Synthetic WeiDU-native V6 DPLAYER preflight checks; no real game needed."""
from __future__ import annotations
from pathlib import Path
from unittest.mock import patch
import tempfile
import unittest

import BGXRANGED_V6_DPLAYER_NATIVE_READONLY as N
import BGXRANGED_V5_NATIVE_CANDIDATE_READONLY as V

def bcs(parts):
    return b"SC\n"+b"".join(b"CR\nCO\n"+x.encode("ascii")+b"\nCR\n" for x in parts)+b"SC\n"

def original_baf():
    sections=[]
    for cond,actions,_ in N.BASE:
        sections.append("IF\n"+ "\n".join("  "+x for x in cond)+"\nTHEN\n"
                        "  RESPONSE #100\n"+ "\n".join("    "+x for x in actions)+"\nEND\n")
    return "\n".join(sections)

def evidence():
    return {"status":"BGXAI_SCRIPT_SLOTS_READONLY_REPORT",
            "saved_party":{"status":"SAVED_GAM_PARTY_READ",
                           "party":[{"status":"SAVED_CRE_SCRIPT_SLOTS_READ",
                                     "scripts":{"override":"KHALID","class":"BDDEFAI",
                                                "default":"DPLAYER"}}]},
            "scripts":[{"script":"DPLAYER","status":"DECOMPILED",
                        "source":"GAME_OVERRIDE_COPY",
                        "source_sha256":N.EXPECTED_DPLAYER_SHA,
                        "total_blocks":2}]}

class DplayerNativeReadOnly(unittest.TestCase):
    def test_saved_script_assignment_evidence_proven(self):
        self.assertTrue(N.valid_saved_handoff(evidence()))
        bad=evidence();bad["saved_party"]["party"][0]["scripts"]["default"]="DPLAYER2"
        self.assertFalse(N.valid_saved_handoff(bad))

    def test_exact_native_baf_matches_two_stored_blocks(self):
        proof=N.check_contract(original_baf(),N.SOURCE.read_text("utf-8"))
        self.assertTrue(proof["candidate_two_actions_preserved"])

    def test_original_changed_conditions_stop(self):
        wrong=original_baf().replace("ActionListEmpty()","!ActionListEmpty()")
        with self.assertRaisesRegex(ValueError,"ORIGINAL_DPLAYER_BAF_NOT_EXACTLY_EXPECTED"):
            N.check_contract(wrong,N.SOURCE.read_text("utf-8"))

    def test_v6_source_other_actions_stop(self):
        wrong=N.SOURCE.read_text("utf-8").replace("AttackOneRound(", "AttackReevaluate(",1)
        with self.assertRaisesRegex(ValueError,"V6_SOURCE_NOT_ONLY_FIVE_SAFE_GUARDS"):
            N.check_contract(original_baf(),wrong)

    def test_weidu_contract_has_no_game_write_actions(self):
        import inspect
        source=inspect.getsource(N.preview)+inspect.getsource(N.call_weidu)
        for unsafe in ("FillSlot(","ClearActions(","--force-install","--force-uninstall",
                       "rename(","unlink(","shutil.move("):
            self.assertNotIn(unsafe,source)

    def test_full_preview_synthetic_hash_and_game_unchanged(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root=Path(tempdir)/"game"; (root/"override").mkdir(parents=True)
            fake_dplayer=bcs(["D1","D2"])
            fake_candidate=bcs(["D1V6","D2V6"])
            for name,raw in ((N.DPLAYER,fake_dplayer),(N.BDDEFAI,b"BDDEF"),
                             (N.WTASIGHT,b"WTASIGHT")):
                (root/name).write_bytes(raw)
            (root/"WeiDU.log").write_text(
                "~BGXFENEMY\\SETUP-BGXFENEMY.TP2~ #0 #0 // installed\n")
            (root/"setup-enhanced-powergaming-scripts.exe").write_bytes(b"MZmock")
            watching=[root/x for x in (N.DPLAYER,N.BDDEFAI,N.WTASIGHT,N.WEIDU_LOG)]
            before={str(p):N.sha(p.read_bytes()) for p in watching}

            def mock_weidu(binary,game,work,src,out,stage):
                self.assertEqual(game,root)
                self.assertNotEqual(out.parent,root)
                if stage=="ORIGINAL_DECOMPILE":out.write_text(original_baf())
                elif stage=="V6_COMPILE":out.write_bytes(fake_candidate)
                elif stage=="V6_REDECOMPILE":out.write_text(N.SOURCE.read_text("utf-8"))
                else:raise AssertionError("unknown stage")
            patchers=[
                patch.object(N,"GAME",root),
                patch.object(N,"EXPECTED_DPLAYER_SHA",N.sha(fake_dplayer)),
                patch.object(N,"EXPECTED_BDDEFAI_SHA",N.sha(b"BDDEF")),
                patch.object(N,"EXPECTED_WTASIGHT_SHA",N.sha(b"WTASIGHT")),
                patch.object(N,"call_weidu",side_effect=mock_weidu)]
            # Preexisting saved audit reflects real source sha only: adapt
            # synthetic saved evidence to the synthetic DPLAYER sha.
            x=evidence();x["scripts"][0]["source_sha256"]=N.sha(fake_dplayer)
            for p in patchers:p.start()
            try:
                proof=N.preview(root,x)
            finally:
                for p in reversed(patchers):p.stop()
            self.assertEqual(proof["status"],"BGXRANGED_V6_DPLAYER_NATIVE_READONLY_PASS")
            self.assertEqual(proof["changed_blocks"],[1,2])
            self.assertEqual(proof["total_blocks"],2)
            self.assertTrue(proof["same_attack_actions"])
            self.assertFalse(proof["script_index6_association_verified"])
            self.assertFalse(proof["runtime_latency_fixed"])
            self.assertFalse(proof["game_modified"])
            self.assertEqual(before,{str(p):N.sha(p.read_bytes()) for p in watching})

    def test_v5_not_rolled_back_stops_before_any_weidu_call(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root=Path(tempdir)
            with patch.object(N,"GAME",root),patch.object(N,"call_weidu",
                 side_effect=AssertionError("must not call WeiDU")):
                with self.assertRaisesRegex(ValueError,"SAVED_KHALID_DPLAYER_ASSIGNMENT_NOT_VERIFIED"):
                    N.preview(root,{"status":"UNKNOWN"})

if __name__=="__main__":
    unittest.main(verbosity=2)
