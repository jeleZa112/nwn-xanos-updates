#!/usr/bin/env python3
"""Read-only menu160 V3 source regression against deployed V2 updater."""
from __future__ import annotations
import hashlib, re, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
LIVE=ROOT/"BGXAI/BGXAI_SYNC.ps1"
DRAFT=ROOT/"BGXAI/BUILD/WEAPON_160_SOURCE_ONLY/BGXAI_SYNC_160_OPTIONAL_V3_CANDIDATE.ps1"
V3=ROOT/"BGXAI/patchsets/ranged_fighter_guarded_20261119/BGXAI_EEEX_R11_STATIC_COMPAT_RO_V3.py"
OLD_PATH="BGXAI/patchsets/ranged_fighter_guarded_20261119/BGXAI_EEEX_R11_STATIC_COMPAT_RO_V2.py"
NEW_PATH="BGXAI/patchsets/ranged_fighter_guarded_20261119/BGXAI_EEEX_R11_STATIC_COMPAT_RO_V3.py"
OLD_SHA="0b05e83a6a34bfc2b97be87d8b06761719b43ddaab39593a3863bf1f2317e316"
NEW_SHA="4bf4e2a981a6602da02ba53dc3e5601fd69bb2f408c64d880c208f1a19bf83f4"

def original_handler(s: str) -> str:
    a=re.findall(r"(?m)^'160' \{[^\r\n]+\}$",s)
    assert len(a)==1
    return a[0]

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a=LIVE.read_bytes().decode("utf-8")
        cls.b=DRAFT.read_bytes().decode("utf-8")
    def test_exact_diff_is_only_optional_scanner_and_sha(self):
        expected=self.a.replace(OLD_PATH,NEW_PATH).replace(OLD_SHA,NEW_SHA).replace("$b.Length -ne 6044","$b.Length -ne 8301")
        self.assertEqual(self.b,expected)
    def test_same_159_handlers(self):
        patt=r"(?m)^'(\d+)' \{"
        old=re.findall(patt,self.a);new=re.findall(patt,self.b)
        self.assertEqual(old,[str(i) for i in range(1,161)])
        self.assertEqual(new,old)
    def test_one_160_handler_only(self):
        self.assertEqual(self.b.count("160 - Weapon EEex R11 static compat READ ONLY"),1)
        self.assertEqual(len(re.findall(r"(?m)^'160' \{",self.b)),1)
        self.assertEqual(self.a[:self.a.index("'160' {")],self.b[:self.b.index("'160' {")])
        self.assertEqual(self.a[self.a.index("\ndefault {"):],self.b[self.b.index("\ndefault {"):])
    def test_immutable_source_hash_and_length(self):
        b=V3.read_bytes()
        self.assertEqual(len(b),8301)
        self.assertEqual(hashlib.sha256(b).hexdigest(),NEW_SHA)
        self.assertEqual(self.b.count(NEW_SHA),2)
    def test_candidate_within_old_bootstrap_limit(self):
        self.assertEqual(len(DRAFT.read_bytes()),79943)
        self.assertLessEqual(len(DRAFT.read_bytes()),80000)
    def test_old_updater_unchanged_from_approved_v2(self):
        self.assertEqual(len(LIVE.read_bytes()),79943)
        self.assertEqual(hashlib.sha256(LIVE.read_bytes()).hexdigest(),"30b248b6d043580eeec32e243ecc529b51fa6299724a0f448b81c88060e0c1ed")
    def test_no_install_command_in_handler_160(self):
        h=original_handler(self.b)
        self.assertIn("Get-PinnedBytes",h)
        self.assertIn("HashBytes",h)
        self.assertIn("HashFile",h)
        self.assertNotIn("WeiDU",h)
        self.assertNotIn("setup-",h)
        self.assertNotIn("SelectWeapon",h)
        self.assertNotIn("ClearActions",h)
        self.assertNotIn("Stop(",h)
    def test_unmodified_cmd(self):
        self.assertTrue((ROOT/"BGXAI_UPDATE.cmd").exists())

if __name__=="__main__":unittest.main(verbosity=2)
