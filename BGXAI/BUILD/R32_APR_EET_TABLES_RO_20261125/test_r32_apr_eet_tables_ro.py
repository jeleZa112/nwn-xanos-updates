"""R32 offline fixtures from public IESDP structure; never claims a real EET table."""
from __future__ import annotations
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("bgxai_r32", ROOT / "BGXAI_R32_APR_EET_TABLES_RO.py")
r32 = importlib.util.module_from_spec(SPEC)
import sys
sys.modules[SPEC.name] = r32
SPEC.loader.exec_module(r32)


def fixture_wsp() -> str:
    cols = ["LEVEL1"] + [str(i) for i in range(2, 41)]
    rows = []
    for rank in range(6):
        values = []
        for level in range(1, 41):
            if rank < 2:
                value = 0 if level < 7 else -1 if level < 13 else 1
            else:
                value = -1 if level < 7 else 1 if level < 13 else -2
            values.append(str(value))
        rows.append(f"{rank}  " + " ".join(values))
    return "2DA V1.0\n0\n" + " ".join(cols) + "\n" + "\n".join(rows) + "\n"


def fixture_cls() -> str:
    return ("2DA V1.0\n0\n"
            "GETS_PROF_APR UNARMED_DIVISOR ZERO_SKILL_THAC0\n"
            "FIGHTER 1 0 2\n"
            "THIEF 0 0 3\n"
            "FIGHTER_MAGE 1 0 2\n"
            "MONK 1 3 2\n")


class TablesTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.override = self.root / "override"
        self.override.mkdir()
        self.wsp = self.override / "WSPATCK.2DA"
        self.cls = self.override / "CLSWPBON.2DA"
        self.wsp.write_text(fixture_wsp(), encoding="ascii")
        self.cls.write_text(fixture_cls(), encoding="ascii")

    def result(self, row="FIGHTER", pip=2, level=1):
        return r32.audit(self.root, row, pip, level)

    def test_real_format_wspatck_half_apr_first_level(self):
        o = self.result()
        self.assertEqual(o["status"], "SOURCE_TABLE_LOOKUP_PASS_NO_ENGINE_APR")
        self.assertEqual(o["wspatckRawValue"], -1)
        self.assertEqual(o["wspatckDecodedBonusAPR"], 0.5)
        self.assertEqual(o["tableBonusAPRIfActorClassVerified"], 0.5)
        self.assertIsNone(o["finalApr"])

    def test_bonus_is_delta_not_final_and_not_added_twice(self):
        o = self.result(level=7)
        self.assertEqual(o["wspatckRawValue"], 1)
        self.assertEqual(o["wspatckDecodedBonusAPR"], 1)
        self.assertTrue(o["bonusIsAdditiveNotFinalAPR"])
        self.assertFalse(o["selectedEngineAprVerified"])
        self.assertFalse(o["alternateEffectiveAprVerified"])

    def test_negative_two_means_additive_one_and_half(self):
        o = self.result(level=13)
        self.assertEqual(o["wspatckRawValue"], -2)
        self.assertEqual(o["wspatckDecodedBonusAPR"], 1.5)
        self.assertIsNone(o["finalApr"])

    def test_pip_one_no_specialization_bonus_at_level_one(self):
        o = self.result(pip=1, level=1)
        self.assertEqual(o["tableBonusAPRIfActorClassVerified"], 0)

    def test_non_fighter_flag_0_does_not_get_wspatck_bonus(self):
        o = self.result(row="THIEF", level=13)
        self.assertFalse(o["getsProfAprTableFlag"])
        self.assertEqual(o["wspatckDecodedBonusAPR"], 1.5)
        self.assertEqual(o["tableBonusAPRIfActorClassVerified"], 0)

    def test_multiclass_row_is_read_not_inferred(self):
        o = self.result(row="FIGHTER_MAGE")
        self.assertTrue(o["getsProfAprTableFlag"])
        self.assertFalse(o["activeDualMultiClassVerified"])
        self.assertFalse(o["liveActorIdentityVerified"])

    def test_unarmed_divisor_is_not_used_as_weapon_apr(self):
        o = self.result(row="MONK", level=13)
        self.assertEqual(o["wspatckDecodedBonusAPR"], 1.5)
        self.assertEqual(o["tableBonusAPRIfActorClassVerified"], 1.5)
        self.assertFalse(o["gameplayWeaponPriorityVerified"])

    def test_read_only_and_exact_sha(self):
        before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (self.wsp, self.cls)}
        o = self.result()
        self.assertEqual(o["wspatckSha256"], before["WSPATCK.2DA"])
        self.assertEqual(o["clswpbonSha256"], before["CLSWPBON.2DA"])
        self.assertFalse(o["gameModified"])
        self.assertFalse(o["weaponSwitchAuthorized"])
        self.assertEqual(o["ordersSent"], 0)
        self.assertEqual(before,
                         {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (self.wsp, self.cls)})
        self.assertEqual(set(p.name for p in self.override.iterdir()), {"WSPATCK.2DA", "CLSWPBON.2DA"})

    def test_missing_resource_holds_without_bif_guess(self):
        self.cls.unlink()
        o = self.result()
        self.assertEqual(o["status"], "HOLD")
        self.assertIn("NO_BIF_FALLBACK", o["reason"])
        self.assertFalse(o["alternateEffectiveAprVerified"])

    def test_missing_level_holds_without_default_lookup(self):
        o = self.result(level=41)
        self.assertEqual(o["reason"], "LEVEL_NOT_EXPLICITLY_IN_WSPATCK")

    def test_unknown_class_holds_without_default(self):
        o = self.result(row="FIGHTER_THIEF")
        self.assertEqual(o["reason"], "CLASS_NOT_EXPLICITLY_IN_CLSWPBON")

    def test_bad_rank_and_level_reject(self):
        for value in (-1, 6, 2.5, None, True):
            o = self.result(pip=value)
            self.assertEqual(o["status"], "HOLD")
        for value in (-1, 0, 51, True, "7"):
            o = self.result(level=value)
            self.assertEqual(o["status"], "HOLD")

    def test_duplicate_proficiency_row_rejects(self):
        self.wsp.write_text(fixture_wsp() + "2 " + " ".join(["-1"]*40) + "\n")
        self.assertEqual(self.result()["reason"], "2DA_ROW_KEY_INVALID_OR_DUPLICATE")

    def test_missing_prof_rank_row_rejects(self):
        self.wsp.write_text(fixture_wsp().rsplit("\n", 2)[0] + "\n")
        self.assertEqual(self.result()["status"], "HOLD")

    def test_malformed_decimal_and_star_reject(self):
        for val in ("*", "1.5", "HACK"):
            data = fixture_wsp().replace("2  -1", "2  " + val, 1)
            self.wsp.write_text(data)
            self.assertEqual(self.result()["status"], "HOLD")

    def test_level_columns_must_be_contiguous(self):
        self.wsp.write_text(fixture_wsp().replace("LEVEL1 2 3 4", "LEVEL1 2 5 4", 1))
        self.assertIn(self.result()["reason"], ("WSPATCK_LEVELS_NONCONTIGUOUS", "2DA_COLUMNS_INVALID"))

    def test_malformed_clswpbon_flag_rejects(self):
        self.cls.write_text(fixture_cls().replace("THIEF 0 0 3", "THIEF 3 0 3"))
        self.assertEqual(self.result()["reason"], "CLSWPBON_PROF_APR_FLAG_NOT_BOOLEAN")

    def test_no_filesystem_escape_through_symlink(self):
        try:
            self.wsp.unlink()
            self.wsp.symlink_to(self.cls)
        except OSError:
            self.skipTest("Windows symlinks unavailable")
        self.assertIn("NOT_IN_OVERRIDE", self.result()["reason"])

    def test_comment_whitespace_and_crlf(self):
        self.wsp.write_bytes(("// custom\n" + fixture_wsp()).replace("\n", "\r\n").encode())
        self.assertEqual(self.result()["status"], "SOURCE_TABLE_LOOKUP_PASS_NO_ENGINE_APR")

    def test_no_automation_of_level_41_even_if_base_apr_present(self):
        o = self.result(level=41)
        self.assertIsNone(o.get("finalApr"))
        self.assertFalse(o["dispatchAuthorized"])
        self.assertFalse(o["liveActorIdentityVerified"])

    def test_parser_never_executes_or_mutates_game_files(self):
        source = (ROOT / "BGXAI_R32_APR_EET_TABLES_RO.py").read_text()
        for forbidden in ("subprocess.", "os.system(", "SelectWeaponAbility(",
                          "ActionOverride(", "ClearActions(", ".write_bytes(", ".write_text(",
                          "OpenProcess(", "ctypes."):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
