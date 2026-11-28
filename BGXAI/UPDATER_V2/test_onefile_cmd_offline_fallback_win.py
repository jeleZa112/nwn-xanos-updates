"""Windows CI only: verify offline fallback of THE SAME original onefile CMD.

Uses a disposable synthetic C:\\Games\\BG_EET_FOXX_NEW/chitin.key on the CI
runner, never user's game. The tested body is the embedded PS code in V2 CMD.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
CMD=ROOT/"BGXAI/UPDATER_V2/BGXAI_UPDATE_V2_STAGE.txt"
HUB=ROOT/"BGXAI/UPDATER_V2/BGXAI_HUB_V2.ps1"
COMMIT="40cd303fdcf9e776e6062b9ce6c8eaa3d00a7376"

@unittest.skipUnless(os.name=="nt","Native Windows PowerShell 5.1 only")
class TestOfflineBounded(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.game=Path(r"C:\Games\BG_EET_FOXX_NEW")
        if cls.game.exists():
            raise RuntimeError("CI synthetic game root already exists, refusing alteration")
        cls.game.mkdir(parents=True)
        (cls.game/"chitin.key").write_bytes(b"synthetic test chitin")
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.game,ignore_errors=True)
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home=Path(self.temp.name)
        self.cache=self.home/"BGXAI_UPDATER"
        self.cache.mkdir()
        self.sha=hashlib.sha256(HUB.read_bytes()).hexdigest()
        self.archive=self.cache/("verified_"+self.sha+".ps1")
        self.archive.write_bytes(HUB.read_bytes())
        self.state=self.cache/"trusted_lastgood_v2.json"
        self.state.write_text(json.dumps({
            "schema":2,"commit":COMMIT,"sha256":self.sha,"size":HUB.stat().st_size
        }),encoding="ascii")
    def exercise(self):
        script=self.home/"run_embedded_offline.ps1"
        script.write_text("""
$ErrorActionPreference='Stop'
$env:BGX_ROOT='C:\\Games\\BG_EET_FOXX_NEW\\'
$env:BGX_SELF='"""+str(CMD).replace("'","''")+"""'
$env:LOCALAPPDATA='"""+str(self.home).replace("'","''")+"""'
function global:Invoke-WebRequest { throw 'FORCED_NET_FAILURE_CI_ONLY' }
$raw=[IO.File]::ReadAllText($env:BGX_SELF)
$at=$raw.LastIndexOf('# BEGIN_BGXAI_RAW_BOOTSTRAP_PS')
if($at -lt 0){throw 'NO_EMBEDDED_PS'}
& ([ScriptBlock]::Create($raw.Substring($at)))
""",encoding="ascii")
        return subprocess.run(["powershell.exe","-NoProfile","-ExecutionPolicy","Bypass",
                               "-File",str(script)],capture_output=True,text=True,
                              encoding="utf-8",errors="replace",timeout=65)
    def test_old_verified_immutable_hub_runs_without_network(self):
        p=self.exercise()
        self.assertEqual(p.returncode,0,p.stdout+"\n"+p.stderr)
        self.assertIn("BGXAI OFFLINE: verified last good",p.stdout)
        self.assertEqual((self.cache/"head.txt").read_text(encoding="ascii"),COMMIT)
        self.assertEqual((self.cache/"BGXAI_SYNC.current.ps1").read_bytes(),HUB.read_bytes())
    def test_tampered_offline_hub_fail_closed_no_execution(self):
        self.archive.write_bytes(b"malicious cache")
        p=self.exercise()
        self.assertNotEqual(p.returncode,0)
        self.assertIn("Offline cached script SHA or size mismatch",p.stdout)
        self.assertFalse((self.cache/"BGXAI_SYNC.current.ps1").exists())
    def test_offline_manifest_without_trust_not_run(self):
        self.state.unlink()
        p=self.exercise()
        self.assertNotEqual(p.returncode,0)
        self.assertIn("No verified offline cache",p.stdout)
        self.assertFalse((self.cache/"BGXAI_SYNC.current.ps1").exists())

if __name__=="__main__":unittest.main(verbosity=2)
