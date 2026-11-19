#!/usr/bin/env python3
"""No-game regression tests for saved GAM CRE script slots and runtime limits."""
from pathlib import Path
from unittest import mock
import struct,sys,tempfile,unittest
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import BGXAI_SAVE_SCRIPT_AUDIT_READONLY as A
import BGX_FRIENDLY_AGGRO_AUDIT_READONLY as OLD

def fixture():
    raw=bytearray(0x1200)
    raw[:8]=b"GAMEV2.0"
    struct.pack_into("<II",raw,0x20,0x100,1)
    struct.pack_into("<I",raw,0x60,1)
    struct.pack_into("<H",raw,0x102,2)
    struct.pack_into("<II",raw,0x104,0x600,0x2D4)
    raw[0x100+0xC0:0x100+0xC0+6]=b"Khalid"
    raw[0x600:0x608]=b"CRE V1.0"
    struct.pack_into("<h",raw,0x600+0x24,9)
    raw[0x600+0x270]=2
    raw[0x600+0x248:0x600+0x250]=b"BDDEFAI\0"
    raw[0x600+0x250:0x600+0x258]=b"PRIEST1\0"
    raw[0x600+0x268:0x600+0x270]=b"DEFAULT\0"
    return bytes(raw)
class SlotAudit(unittest.TestCase):
    def test_party_slots_and_ai_flag(self):
        party=A.gam_party(fixture())
        self.assertEqual(party["status"],"SAVED_GAM_PARTY_READ")
        self.assertTrue(party["gui_party_ai_flag_at_save"])
        actor=party["party"][0]
        self.assertEqual(actor["name_from_saved_record"],"Khalid")
        self.assertEqual(actor["scripts"]["override"],"BDDEFAI")
        self.assertEqual(actor["scripts"]["class"],"PRIEST1")
        self.assertEqual(actor["scripts"]["default"],"DEFAULT")
        self.assertEqual(actor["current_hp_in_saved_cre"],9)
    def test_refuse_unsupported_gam(self):
        with self.assertRaisesRegex(ValueError,"UNSUPPORTED"):
            A.gam_party(b"not a save"+b"\0"*200)
    def test_refuse_overflow_party_and_cre(self):
        b=bytearray(fixture())
        struct.pack_into("<I",b,0x24,99999)
        with self.assertRaisesRegex(ValueError,"GAM_PARTY_BOUNDS"):
            A.gam_party(b)
        b=bytearray(fixture())
        struct.pack_into("<I",b,0x104,0xFFFFFF00)
        self.assertEqual(A.gam_party(b)["party"][0]["status"],"INVALID_CRE_BOUNDS")
    def test_bounded_script_names(self):
        saved=A.gam_party(fixture())
        names=A.script_names(saved)
        self.assertIn("BDDEFAI",names)
        self.assertIn("PRIEST1",names)
        self.assertIn("DEFAULT",names)
        saved["party"][0]["scripts"]["class"]="../SECRET"
        self.assertNotIn("../SECRET",A.script_names(saved))
    def test_saved_ai_bit_can_be_off(self):
        b=bytearray(fixture());struct.pack_into("<I",b,0x60,0)
        self.assertFalse(A.gam_party(b)["gui_party_ai_flag_at_save"])
    def test_missing_save_is_not_live_proof(self):
        with tempfile.TemporaryDirectory() as d:
            with mock.patch.object(A,"save_roots",return_value=[Path(d)]):
                s=A.latest_saved_party(Path(d))
                self.assertEqual(s["status"],"NO_SUPPORTED_SAVE_DISCOVERED")
                self.assertNotIn("party",s)
    def test_reads_most_recent_save_only(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d);save=base/"save";(save/"quick").mkdir(parents=True)
            (save/"quick"/"BALDUR.GAM").write_bytes(fixture())
            with mock.patch.object(A,"save_roots",return_value=[save]):
                result=A.latest_saved_party(base)
                self.assertEqual(result["status"],"SAVED_GAM_PARTY_READ")
                self.assertFalse(result["runtime_state_verified"])
    def test_native_script_actions_are_labeled_not_provenance(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d);override=base/"override";override.mkdir()
            (override/"BDDEFAI.BCS").write_bytes(b"dummy BCS")
            exe=base/"weidu.exe";exe.write_bytes(b"MZ")
            def fake_run(cmd,**kwargs):
                Path(cmd[cmd.index("--out")+1]).write_text(
                    "IF\n  AttackedBy([ANYONE],DEFAULT)\nTHEN\n"
                    "  RESPONSE #100\n    Attack(LastAttackerOf(Myself))\nEND\n")
                return mock.Mock(returncode=0)
            with mock.patch.object(A.subprocess,"run",side_effect=fake_run):
                report=A.inspect_script(base,"BDDEFAI",exe,base,OLD.parse_baf)
                self.assertEqual(report["status"],"DECOMPILED")
                self.assertEqual(report["attack_or_protect_blocks"],1)
                self.assertTrue(report["matches"][0]["reacts_to_last_attacker"])
                self.assertFalse(report["matches"][0]["has_party_filter"])
    def test_static_only_no_game_write(self):
        source=(HERE/"BGXAI_SAVE_SCRIPT_AUDIT_READONLY.py").read_text()
        self.assertNotIn("--force-install",source)
        self.assertNotIn("--force-uninstall",source)
        self.assertNotIn('open("override/',source)
        self.assertIn('"runtime_action_origin":"UNKNOWN"',source)
        self.assertIn('"game_modified":False',source)
if __name__=="__main__":unittest.main()
