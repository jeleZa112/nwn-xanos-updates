#!/usr/bin/env python3
"""One-file pinned updater SOURCE-only regression; no game, no installation."""
from pathlib import Path
import hashlib,json,re,unittest
ROOT=Path(__file__).resolve().parents[3]
SCRIPT=ROOT/'BGXAI/BGXAI_SYNC.ps1'
PIN=ROOT/'BGXAI/fox_new/BOOTSTRAP_PIN.json'
SOURCE=ROOT/'BGXAI/patchsets/ranged_fighter_guarded_20261119'
MANIFEST=SOURCE/'BGXAI_WEAPON_NATIVE_COMPILE_MANIFEST_V1.json'
LEGACY_MENU_SHA='74f52097ccfcc6beb2117344df92f23150de37e2979063b79d3387c3cbc9a230'
SHORT_TO_ORIGINAL={"ANR":"AssertNotReparse","VM":"VerifiedManifest","RR":"RunRelease","BOM":"BGXOneFileManaged"}
VERSION='0.3.92-BGXAI-AUTO-BATCH-RO'
class Updater167(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=SCRIPT.read_bytes()
        cls.text=cls.raw.decode('utf-8')
        cls.pin=json.loads(PIN.read_text('utf-8'))
        cls.manifest=json.loads(MANIFEST.read_text('utf-8'))
    def test_01_single_updater_size_pin_and_immutable_ref(self):
        self.assertLessEqual(len(self.raw),80000)
        self.assertEqual(self.pin['script_size'],len(self.raw))
        self.assertEqual(self.pin['script_sha256'],hashlib.sha256(self.raw).hexdigest())
        self.assertRegex(self.pin['commit'],r'^[a-f0-9]{40}$')
        self.assertEqual(self.pin['script_path'],'BGXAI/BGXAI_SYNC.ps1')
        self.assertIn('Download-Limited $scriptSources $temporaryScript 80000',(ROOT/'BGXAI_UPDATE.cmd').read_text())
    def test_02_legacy_1_to_166_branch_bodies_preserved_after_aliasing(self):
        lines=re.findall(r"(?m)^'(\d+)' \{[^\r\n]*",self.text)
        self.assertEqual([int(x) for x in lines],list(range(1,169)))
        old=[line for line in self.text.splitlines() if re.match(r"^'\d+' \{",line) and int(line.split("'")[1])<=166]
        for short,long in SHORT_TO_ORIGINAL.items():
            old=[re.sub(r'\b'+re.escape(short)+r'\b',long,line) for line in old]
        self.assertEqual(hashlib.sha256(('\n'.join(old)+'\n').encode()).hexdigest(),LEGACY_MENU_SHA)
    def test_03_readonly_167_is_only_new_command(self):
        branch=next(x for x in self.text.splitlines() if x.startswith("'167' {"))
        self.assertIn('SyncRelease $w3',branch)
        self.assertIn('--game $gr',branch)
        self.assertIn('--source',branch)
        self.assertIn("REPORT_FILE=",branch)
        self.assertIn('Out-File -LiteralPath $o -Encoding utf8',branch)
        self.assertIn('ANR $d',branch)
        self.assertIn('BGXAI_LIVE_REPORTS',branch)
        self.assertIn('BGXAI_WEAPON_NATIVE_COMPILE_PREFLIGHT_RO.py',branch)
        for bad in ('--install','--uninstall','--rollback','WeiDU.log','override','SelectWeaponAbility','ClearActions','setup-'):
            self.assertNotIn(bad,branch)
        self.assertIn('167 - Weapon V3 native BAF compile (READ ONLY)',self.text)
        self.assertIn('166 - V7 DPLAYER close-fire fix (guarded)',self.text)
    def test_04_sha_pinned_manifest_and_allowlisted_sources(self):
        m=self.manifest
        self.assertEqual(m['schema'],1)
        self.assertEqual(m['channel'],'bgxai-fox-new-safe-source')
        self.assertEqual(m['version'],VERSION)
        self.assertEqual(len(m['files']),5)
        expected={'BGXAI_WEAPON_NATIVE_COMPILE_PREFLIGHT_RO.py','BGXAI_WEAPON_SLOT_CONSUMER_V3.baf','BGXAI_AUTO_BATCH_RO_V1.py','test_auto_batch_ro_v1.py','test_weapon_native_compile_ro_v1.py'}
        self.assertEqual({e['dest'] for e in m['files']},expected)
        for entry in m['files']:
            self.assertEqual(entry['source'],'BGXAI/patchsets/ranged_fighter_guarded_20261119/'+entry['dest'])
            raw=(SOURCE/entry['dest']).read_bytes()
            self.assertEqual(entry['size'],len(raw))
            self.assertEqual(entry['sha256'],hashlib.sha256(raw).hexdigest())
    def test_05_no_secondary_cmd_or_installer_and_checks_reused(self):
        for name in ('VM','ANR','RR','BOM'):
            self.assertIn('function '+name+'(',self.text)
        self.assertIn("$w3=@{id='W3'",self.text)
        self.assertIn('BGXAI_DEV\\weapon_priority_v3',self.text)
        self.assertIn('BGXAI_WEAPON_NATIVE_COMPILE_MANIFEST_V1.json',self.text)
        self.assertIn('BGXAI_WEAPON_SLOT_CONSUMER_V3.baf',self.text)
        self.assertIn('SyncRelease $r27',self.text)
        self.assertIn('SyncRelease $rg',self.text)
    def test_06_native_compiler_stays_readonly(self):
        source=(SOURCE/'BGXAI_WEAPON_NATIVE_COMPILE_PREFLIGHT_RO.py').read_text()
        for required in ('--no-auto-tp2','--noautoupdate','--no-exit-pause','SOURCE_SHA256',
                         'shutil.copy2','watchedFilesChanged','temporaryOutputRemoved','installPerformed'):
            self.assertIn(required,source)
        self.assertNotIn('force-install',source)
    def test_07_auto_batch_168_is_readonly_and_old_167_unmodified(self):
        self.assertIn('168 - AUTO batch weapon READ ONLY',self.text)
        branch=next(x for x in self.text.splitlines() if x.startswith("'168' {"))
        self.assertIn('SyncRelease $w3',branch)
        self.assertIn('BGXAI_AUTO_BATCH_RO_V1.py',branch)
        self.assertIn('--game $gr',branch)
        for banned in ('--install','--rollback','--uninstall','ClearActions','SelectWeaponAbility','setup-'):
            self.assertNotIn(banned,branch)
        self.assertIn('BGXAI_WEAPON_NATIVE_COMPILE_PREFLIGHT_RO.py',
                      next(x for x in self.text.splitlines() if x.startswith("'167' {")))
if __name__=='__main__':
    unittest.main(verbosity=2)
