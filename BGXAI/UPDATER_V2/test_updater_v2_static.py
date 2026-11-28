"""One original CMD; staged V2 isolated-module dispatcher backward compatibility."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[2]
LEGACY=ROOT/'BGXAI/UPDATER_V2/BGXAI_SYNC_LEGACY_F282.ps1'
ORIGINAL=ROOT/'BGXAI/BGXAI_SYNC.ps1'
HUB=ROOT/'BGXAI/UPDATER_V2/BGXAI_HUB_V2_STAGED.ps1'
INDEX=ROOT/'BGXAI/UPDATER_V2/MODULES_V1.json'
CMD=ROOT/'BGXAI_UPDATE.cmd'
PIN=ROOT/'BGXAI/fox_new/BOOTSTRAP_PIN.json'

class OnefileV2Compatibility(unittest.TestCase):
    def test_old_script_is_unchanged_before_activation(self):
        b=ORIGINAL.read_bytes()
        self.assertEqual(len(b),79798)
        self.assertEqual(hashlib.sha256(b).hexdigest(),
            '4728e8a412c2b9497e12541447e9578604677440f344a207cc67b779154d15b5')

    def test_existing_cmd_exact_unmodified(self):
        self.assertEqual(hashlib.sha1(
            b'blob '+str(len(CMD.read_bytes())).encode()+b'\x00'+CMD.read_bytes()
        ).hexdigest(),'0c0428be14f12aea4e0cb027972139d77a860342')

    def test_legacy_menu_only_three_intentional_changes(self):
        base=ORIGINAL.read_text(encoding='ascii')
        expected=base.replace("param([string]$GameRoot='.')",
             "param([string]$GameRoot='.',[string]$HubChoice='')",1)
        expected=expected.replace(
            "$commitId=[IO.File]::ReadAllText($pinnedFile).Trim()",
            "$commitId=[IO.File]::ReadAllText($pinnedFile).Trim()\n"
            "if($HubChoice -ne '') {\n"
            "if($HubChoice -cnotmatch '^[0-9]{1,3}$'){throw 'HOLD_LEGACY_HUB_CHOICE_INVALID'}\n"
            "$commitId='f2827f25da5a01215fcbdc0b9a48e3900d654384'\n}",1)
        expected=expected.replace("$choice=rh 'Choice [0]'",
             "if($HubChoice -ne ''){$choice=$HubChoice}else{$choice=rh 'Choice [0]'}",1)
        self.assertEqual(LEGACY.read_text(encoding='ascii'),expected)
        self.assertEqual(len(LEGACY.read_bytes()),80027)
        self.assertEqual(hashlib.sha256(LEGACY.read_bytes()).hexdigest(),
             'edd1a67be9c5ea9d5ec7c52fb7eb1135cd3ae6f4d248f709459e11667053df75')

    def test_staged_same_cmd_can_restore_sha_checked_last_good_offline(self):
        raw=(ROOT/'BGXAI/UPDATER_V2/BGXAI_UPDATE_V2_STAGE.txt').read_bytes()
        old=CMD.read_bytes()
        self.assertTrue(raw.startswith(old[:120]))
        self.assertEqual(raw.count(b'# BEGIN_BGXAI_RAW_BOOTSTRAP_PS'),2)
        self.assertIn(b'trusted_lastgood_v2.json',raw)
        self.assertIn(b'Offline cached script SHA or size mismatch',raw)
        self.assertIn(b'BGXAI OFFLINE: verified last good ',raw)
        self.assertIn(b'Get-FileHash -LiteralPath $archive -Algorithm SHA256',raw)
        self.assertIn(b'No auto retry',HUB.read_bytes())
        self.assertNotIn(b'XEquipItem(',raw)

    def test_hub_staged_not_game_installer(self):
        s=HUB.read_text(encoding='ascii')
        self.assertLess(len(s),20000)
        for word in ('Get-PinnedAsset','Check-Index','Execute-Legacy',
                     'Execute-Module','Run-SelfTest','BGXAI_UPDATER_V2_SELFTEST_PASS',
                     "HOLD_UPDATER_V2_GUARDED_TOKEN"):
            self.assertIn(word,s)
        for forbidden in ('XEquipItem(', 'ClearActions(', 'EXTEND_TOP ', 'weidu --force'):
            self.assertNotIn(forbidden,s)

    def test_legacy_digest_pin_exact(self):
        s=HUB.read_text(encoding='ascii')
        digest=hashlib.sha256(LEGACY.read_bytes()).hexdigest()
        self.assertIn("$LegacyHash='"+digest+"'",s)
        self.assertIn("$LegacySize="+str(LEGACY.stat().st_size),s)
        self.assertIn("$LegacyCommit='8fb1296926925b1298085665255bb9ef95ebddd7'",s)

    def test_manifest_schema_and_future_module_extension(self):
        j=json.loads(INDEX.read_text(encoding='ascii'))
        self.assertEqual((j['schema'],j['channel'],j['branch']),
                         (1,'BGXAI_ONEFILE_MODULES_V2','bg-eet-ai'))
        codes=set()
        for item in j['modules']:
            code=item['code']
            self.assertTrue(180<=code<=899 and code not in codes)
            codes.add(code)
            self.assertRegex(item['commit'],r'^[a-f0-9]{40}$')
            self.assertIn(item['mode'],('readonly','guarded'))
            names={f['path'] for f in item['files']}
            self.assertIn(item['entry'],names)
            for file in item['files']:
                self.assertRegex(file['sha256'],r'^[a-f0-9]{64}$')
                self.assertLessEqual(file['size'],1000000)

    def test_existing_pin_unchanged_during_staging(self):
        j=json.loads(PIN.read_text(encoding='utf-8'))
        self.assertEqual(j['commit'],'f2827f25da5a01215fcbdc0b9a48e3900d654384')
        self.assertEqual(j['script_size'],79798)
        self.assertEqual(j['script_sha256'],hashlib.sha256(ORIGINAL.read_bytes()).hexdigest())

if __name__=='__main__':
    unittest.main(verbosity=2)
