"""BGXAI R20: only the one existing updater, no game access in tests."""
import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SYNC = ROOT / "BGXAI/BGXAI_SYNC.ps1"
R19 = ROOT / "BGXAI/patchsets/ranged_fighter_guarded_20261119/BGXAI_R19_INSTALLED_EEEX_AUDIT_RO.py"
ORIGINAL_SHA256 = "f5b9d565de595ffea0e04c26f3194152445a26743aa47348694b883cdd9ec8e0"
AUDIT_SHA256 = "7426faaa18c1a7bb9a8437ee0733854bed0f868a419e96593c58c7ec71451300"
BASELINE_COMMIT = "10905c8138dc72b3febb6629d164d9c33a6d292f"
SHORTS = (("token","ztok"),("active","zact"),("lines","zln"),("isCurrent","zcur"))

def contents():
    return SYNC.read_bytes().decode("utf-8")

def handler(s):
    match = re.search(r"(?m)^'164' \{[^\n]*\}\n", s)
    if not match:
        raise AssertionError("R20_HANDLER_MISSING")
    return match.group(0)

def dispatches(s):
    return {int(m.group(1)): m.group(0) for m in re.finditer(r"(?m)^'([0-9]+)' \{[^\n]*\}$", s)}

def baseline_script():
    import subprocess
    p=subprocess.run(["git","show",f"{BASELINE_COMMIT}:BGXAI/BGXAI_SYNC.ps1"],
                     cwd=ROOT,capture_output=True,check=True)
    return p.stdout.decode("utf-8")

class R20ReadOnlySingleUpdater(unittest.TestCase):
    def test_previous_1_to_169_dispatches_unchanged(self):
        current=dispatches(contents())
        previous=dispatches(baseline_script())
        self.assertEqual(list(current),list(range(1,171)))
        for n in range(1,170):
            self.assertEqual(current[n],previous[n],f"existing dispatch {n} changed")
        self.assertEqual(current[170],"'170' {RunR30ReadOnly;break}")
    def test_size_keeps_pin_limit(self):
        b=SYNC.read_bytes()
        self.assertEqual(len(b),79979)
        self.assertLessEqual(len(b),80000)
    def test_menu_and_switch_completeness(self):
        s=contents()
        ids=[int(x) for x in re.findall(r"(?m)^'(\d+)' \{",s)]
        self.assertEqual(ids,list(range(1,171)))
        self.assertIn("170 R30 RO",s)
    def test_r19_payload_verifies_exact_bytes(self):
        self.assertEqual(len(R19.read_bytes()),11013)
        self.assertEqual(hashlib.sha256(R19.read_bytes()).hexdigest(),AUDIT_SHA256)
    def test_existing_pinned_source_allowlist(self):
        s=contents()
        self.assertIn("patchsets/ranged_fighter_guarded_20261119",s)
        self.assertIn("Get-PinnedBytes $p",handler(s))
        self.assertIn("HashBytes $b",handler(s))
        self.assertIn("HashFile $f",handler(s))
    def test_164_no_game_writes_or_wei_du(self):
        h=handler(contents())
        for forbidden in ("WeiDU","ClearActions(","SelectWeaponAbility(","Attack(","Stop(",
                          "SetGlobal(","-Install","RunRelease ","SyncRelease ","Join-Path $gr"):
            self.assertNotIn(forbidden,h)
        self.assertIn("& py -3 $f --game $gr",h)
    def test_only_cache_and_report_file_created(self):
        h=handler(contents())
        self.assertIn("Join-Path $zcd",h)
        self.assertIn("'Documents\\BGXAI_LIVE_REPORTS'",h)
        self.assertIn("Out-File -LiteralPath $o -Encoding utf8",h)
        self.assertIn("REPORT_FILE=",h)
        self.assertIn("FileMode]::CreateNew",h)
        self.assertIn("Remove-Item -LiteralPath $f -Force",h)
    def test_no_r19_install_or_live_claim(self):
        s=R19.read_text(encoding="utf-8")
        for k in ("safeToCallGetAbility","safeToCallGetLauncher",
                  "weaponSwitchAuthorized","dispatchAuthorized","installAuthorized"):
            self.assertIn("'"+k+"':False",s)
        self.assertIn("'installedGameFilesInspected':False",s)
    def test_r19_only_known_windows_game(self):
        s=R19.read_text(encoding="utf-8")
        self.assertIn("C:\\Games\\BG_EET_FOXX_NEW",s)
        self.assertIn("HOLD_EXACT_WINDOWS_GAME_ONLY",s)
        self.assertNotIn("subprocess.run",s)
        self.assertNotIn("import ctypes",s)
    def test_hold_is_a_supported_scan_status(self):
        h=handler(contents())
        self.assertIn("$rc -ne 0 -and $rc -ne 2",h)
        self.assertIn("164 SCAN ERROR",h)

if __name__ == "__main__":
    unittest.main()
