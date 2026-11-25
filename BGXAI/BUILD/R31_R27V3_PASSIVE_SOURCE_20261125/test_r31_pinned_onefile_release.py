"""Independent SHA-locked BGXAI R31 one-CMD release verification.

Offline, read only; does not run any user game, WeiDU, PowerShell or installer.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import unittest

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SYNC = REPO / "BGXAI/BGXAI_SYNC.ps1"
PIN = REPO / "BGXAI/fox_new/BOOTSTRAP_PIN.json"
CMD = REPO / "BGXAI_UPDATE.cmd"
R31_GUARD = HERE / "R31_GUARDED_SOURCE_ONLY.py"
R31_LUA = HERE / "M_BGXR27_R31_SOURCE_ONLY.lua"

EXPECTED_SYNC_SHA = "c998ff6607ee3915b9cbb3c9b31955f715bee425b5ed882e04e1af1d515ed4aa"
EXPECTED_COMMIT = "fe992a60a4c7880912270cfed27be59c6a0bf359"
EXPECTED_GUARD_SHA = "0ac97a702c4ac5919549a5a54cf9ef6a01a8fbd582273fc556fe9c82a60950ee"
EXPECTED_LUA_SHA = "5a1f6b32db920a005161734605c8b3273614a1318d8b1b57dac79ed022a00f38"

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

class R31PinnedOnefileRelease(unittest.TestCase):
    def test_exact_pinned_backend_bytes(self):
        src=SYNC.read_bytes()
        manifest=json.loads(PIN.read_text(encoding="utf-8"))
        self.assertEqual(manifest["commit"],EXPECTED_COMMIT)
        self.assertEqual(manifest["script_path"],"BGXAI/BGXAI_SYNC.ps1")
        self.assertEqual(manifest["script_sha256"],EXPECTED_SYNC_SHA)
        self.assertEqual(manifest["script_size"],79941)
        self.assertEqual(len(src),79941)
        self.assertLessEqual(len(src),80000)
        self.assertEqual(sha(src),EXPECTED_SYNC_SHA)

    def test_original_one_cmd_preserved(self):
        src=CMD.read_bytes()
        self.assertIn(b"BEGIN_BGXAI_RAW_BOOTSTRAP_PS",src)
        self.assertIn(b"BOOTSTRAP_PIN.json",src)
        self.assertIn(b"80000",src)
        self.assertNotIn(b"INSTALL_BGXAI_R31_PASSIVE_V3_AFTER_R29",src)

    def test_r31_payload_exact_and_single_menu_handler(self):
        text=SYNC.read_text(encoding="utf-8")
        guard=R31_GUARD.read_bytes()
        lua=R31_LUA.read_bytes()
        self.assertEqual((len(guard),sha(guard)),(20305,EXPECTED_GUARD_SHA))
        self.assertEqual((len(lua),sha(lua)),(47550,EXPECTED_LUA_SHA))
        self.assertIn("Set-Alias wh Write-Host -Scope Script",text)
        self.assertEqual(text.count("'171' {"),1)
        self.assertEqual(text.count("'170' {RunR30ReadOnly;break}"),1)
        handler=next(line for line in text.splitlines() if line.startswith("'171' {"))
        for required in ("R31_GUARDED_SOURCE_ONLY.py",
                         "M_BGXR27_R31_SOURCE_ONLY.lua",EXPECTED_GUARD_SHA,
                         EXPECTED_LUA_SHA,"R31 PIN STOP","R31 STAGE SHA",
                         "R31 1=RO 2=install","'1'='preflight'",
                         "Remove-Item -LiteralPath $f,$c"):
            self.assertIn(required,handler)
        self.assertNotIn("INSTALL_BGXAI_R31_PASSIVE_V3_AFTER_R29",handler)
        self.assertIn("& py -3 $f --game $gr --candidate $c --mode $m",handler)
        self.assertEqual(
            re.findall(r"(?m)^'([1-9][0-9]*)' \{[^\n]+\}$",text),
            [str(i) for i in range(1,172)],
        )

    def test_guard_requires_exact_typed_install_and_last_only_rollback(self):
        src=R31_GUARD.read_text(encoding="utf-8")
        self.assertIn('INSTALL_TOKEN = "INSTALL_BGXAI_R31_PASSIVE_V3_AFTER_R29"',src)
        self.assertIn('ROLLBACK_TOKEN = "ROLLBACK_BGXAI_R31_PASSIVE_V3_ONLY"',src)
        self.assertIn('if token != INSTALL_TOKEN:',src)
        self.assertIn('if token != ROLLBACK_TOKEN:',src)
        self.assertIn('if len(rows) != 151 or not R31.match(rows[-1])',src)
        self.assertIn('"R31_NOT_LAST_NO_ROLLBACK"',src)
        self.assertIn('"queueBindingLiveVerified": False',src)
        self.assertIn('"manualEpsOriginVerified": False',src)

if __name__=="__main__":
    unittest.main()
