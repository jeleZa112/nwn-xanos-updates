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

    def test_original_cmd_legacy_release_still_untouched(self):
        raw=CMD.read_bytes()
        self.assertEqual(hashlib.sha1(
            b'blob '+str(len(raw)).encode()+bytes([0])+raw
        ).hexdigest(),'0c0428be14f12aea4e0cb027972139d77a860342')
        released=(ROOT/'BGXAI/UPDATER_V2/BGXAI_UPDATE_V2_RELEASE.cmd').read_bytes()
        stage=(ROOT/'BGXAI/UPDATER_V2/BGXAI_UPDATE_V2_STAGE.txt').read_bytes()
        self.assertEqual(released,stage)
        self.assertNotEqual(raw,released)


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
        self.assertIn(b'function File-SHA256',raw)
        self.assertIn(b'File-SHA256 $archive',raw)
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

    def test_separate_v2_bootstrap_is_exact_sha_and_under_old_cmd_limit(self):
        pin=json.loads((ROOT/'BGXAI/UPDATER_V2/BOOTSTRAP_PIN_V2.json').read_text())
        self.assertEqual(pin['schema'],2)
        self.assertEqual(pin['channel'],'bgxai-fox-new-modular-v2')
        self.assertEqual(pin['script_path'],'BGXAI/UPDATER_V2/BGXAI_HUB_V2.ps1')
        final=ROOT/pin['script_path']
        self.assertLess(final.stat().st_size,80000)
        self.assertEqual(final.stat().st_size,pin['script_size'])
        self.assertEqual(hashlib.sha256(final.read_bytes()).hexdigest(),pin['script_sha256'])
        self.assertEqual(final.read_bytes(),HUB.read_bytes())
        cmd=(ROOT/'BGXAI/UPDATER_V2/BGXAI_UPDATE_V2_STAGE.txt').read_bytes()
        self.assertIn(b"BGXAI/UPDATER_V2/BOOTSTRAP_PIN_V2.json",cmd)
        self.assertIn(b"BGXAI/UPDATER_V2/BGXAI_HUB_V2.ps1",cmd)
        self.assertNotIn(b"BGXAI/fox_new/BOOTSTRAP_PIN.json",cmd)

    def test_module180_manifest_assets_are_SHA_pinned_to_current_source(self):
        data=json.loads(INDEX.read_text(encoding='ascii'))
        modules=[x for x in data['modules'] if x['code']==180]
        self.assertEqual(len(modules),1)
        m=modules[0]
        self.assertEqual(m['mode'],'readonly')
        self.assertEqual(len(m['files']),3)
        for entry in m['files']:
            f=ROOT/entry['path']
            self.assertEqual(len(f.read_bytes()),entry['size'])
            self.assertEqual(hashlib.sha256(f.read_bytes()).hexdigest(),entry['sha256'])

    def test_r48_guarded_181_182_exact_pins_and_no_new_cmd(self):
        index=json.loads(INDEX.read_text(encoding='ascii'))
        self.assertEqual([m['code'] for m in index['modules']],[180,181,182,183,184,185,186])
        r181,r182=index['modules'][1:3]
        self.assertEqual(r181['mode'],'guarded')
        self.assertEqual(r182['mode'],'guarded')
        self.assertEqual(r181['language'],'python')
        self.assertEqual(r182['language'],'python')
        self.assertEqual(r181['approval'],
            'INSTALL_BGXAI_R48_ONE_STAF01_FROM_BACKPACK_TO_WEAPON_AFTER_R47')
        self.assertEqual(r182['approval'],'ROLLBACK_BGXAI_R48_RESTORE_R47_ONLY')
        self.assertEqual(r181['commit'],r182['commit'])
        self.assertEqual(r181['entry'],r182['entry'])
        self.assertEqual(r181['files'],r182['files'])
        self.assertEqual(len(r181['files']),18)
        paths={x['path'] for x in r181['files']}
        self.assertIn('BGXAI/UPDATER_V2/BGXAI_MODULE181_182_R48_ONE_SHOT_GUARDED.py',paths)
        self.assertIn(
            'BGXAI/BUILD/R48_ONE_REAL_STAF01_EQUIP_AFTER_R47_20261128/'
            'BGXAI_R48_LAST158_TO159_ONE_ITEM_GUARDED.py',paths)
        self.assertIn(
            'BGXAI/BUILD/R39_STAGED_XEQUIP_SOURCEONLY_20261127/'
            'BGXAI_R39_JAGAN_STAF01_EEEX_SESSION_SOURCE_ONLY.baf',paths)
        for entry in r181['files']:
            f=ROOT/entry['path']
            payload=f.read_bytes()
            self.assertEqual(len(payload),entry['size'],entry['path'])
            self.assertEqual(hashlib.sha256(payload).hexdigest(),
                             entry['sha256'],entry['path'])
            self.assertFalse(f.is_symlink())
        # Installed original hub already supports guarded exact confirmation.
        original=HUB.read_text(encoding='ascii')
        self.assertIn("GUARDED MODULE: a separate exact confirmation is required.",original)
        self.assertIn("if($typed -cne $approval)",original)
        self.assertIn("--onefile-hub-guarded --approved-token",original)
        self.assertNotIn('XEquipItem(',original)
        self.assertNotIn('XEquipItem(',((ROOT/r181['entry']).read_text(encoding='ascii')))
        self.assertNotIn(b'BGXAI_MODULE181_182',CMD.read_bytes())
        self.assertNotIn(b'R48_ONE_REAL_STAF01',CMD.read_bytes())

    def test_r48_post_closed_console_status_183_is_readonly_and_sha_pinned(self):
        index=json.loads(INDEX.read_text(encoding='ascii'))
        r183=index['modules'][3]
        self.assertEqual(r183['code'],183)
        self.assertEqual(r183['label'],'R48 install state recovery RO')
        self.assertEqual(r183['mode'],'readonly')
        self.assertNotIn('approval',r183)
        self.assertEqual(r183['entry'],'BGXAI/UPDATER_V2/BGXAI_MODULE183_R48_STATUS_RO.py')
        self.assertEqual(len(r183['files']),19)
        self.assertEqual(r183['files'][1:],index['modules'][1]['files'])
        for entry in r183['files']:
            p=ROOT/entry['path']
            self.assertFalse(p.is_symlink())
            self.assertEqual(len(p.read_bytes()),entry['size'])
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),
                             entry['sha256'],entry['path'])
        reader=(ROOT/r183['entry']).read_text(encoding='ascii')
        self.assertIn('native.status(',reader)
        for danger in ('native.install(', 'native.rollback(', 'XEquipItem(',
                       'ClearActions(', 'EXTEND_TOP', 'BGXAI_UPDATE2.cmd'):
            self.assertNotIn(danger,reader)
        hub=HUB.read_text(encoding='ascii')
        self.assertIn('--onefile-hub-source-only',hub)
        self.assertNotIn(b'BGXAI_MODULE183',CMD.read_bytes())

    def test_r49_184_185_186_exact_native_21_pins_and_distinct_consent(self):
        index=json.loads(INDEX.read_text(encoding='ascii'))
        self.assertEqual(len(index['modules']),7)
        one,two,three=index['modules'][4:]
        self.assertEqual([x['code'] for x in (one,two,three)],[184,185,186])
        self.assertEqual([x['mode'] for x in (one,two,three)],
                         ['readonly','guarded','guarded'])
        self.assertNotIn('approval',one)
        self.assertEqual(two['approval'],
          'INSTALL_BGXAI_R49_BACKPACK16_ONE_STAF01_AFTER_R48_LAST159')
        self.assertEqual(three['approval'],
          'ROLLBACK_BGXAI_R49_RESTORE_R48_LAST159_ONLY')
        self.assertEqual(one['commit'],two['commit'])
        self.assertEqual(one['commit'],three['commit'])
        self.assertEqual(one['entry'],two['entry'])
        self.assertEqual(one['entry'],three['entry'])
        self.assertEqual(one['files'],two['files'])
        self.assertEqual(one['files'],three['files'])
        self.assertEqual(one['files'][:18],index['modules'][1]['files'])
        self.assertEqual(len(one['files']),21)
        expected={
          'BGXAI/BUILD/R49_R48_BACKPACK16_SOURCE_ONLY_20261128/BGXAI_R49_REUSE_R48_BACKPACK16_SOURCE_ONLY.py',
          'BGXAI/BUILD/R49_R48_BACKPACK16_SOURCE_ONLY_20261128/BGXAI_R49_LAST159_TO160_GUARDED.py',
          'BGXAI/UPDATER_V2/BGXAI_MODULE184_186_R49_ORIGINAL_GUARDED.py'}
        self.assertEqual({x['path'] for x in one['files'][18:]},expected)
        self.assertEqual(one['entry'],
          'BGXAI/UPDATER_V2/BGXAI_MODULE184_186_R49_ORIGINAL_GUARDED.py')
        for entry in one['files']:
            f=ROOT/entry['path']
            self.assertFalse(f.is_symlink())
            self.assertEqual(f.stat().st_size,entry['size'],entry['path'])
            self.assertEqual(hashlib.sha256(f.read_bytes()).hexdigest(),
                             entry['sha256'],entry['path'])
        self.assertLessEqual(INDEX.stat().st_size,32768)
        original=HUB.read_text(encoding='ascii')
        self.assertIn("Check-Index",original)
        self.assertIn("if($typed -cne $approval)",original)
        self.assertNotIn(b'BGXAI_MODULE184_186',CMD.read_bytes())
        bridge=(ROOT/one['entry']).read_text(encoding='ascii')
        self.assertNotIn('XEquipItem(',bridge)
        self.assertIn("native.preflight(",bridge)
        self.assertIn("native.install(",bridge)
        self.assertIn("native.rollback(",bridge)

    def test_existing_pin_unchanged_during_staging(self):
        j=json.loads(PIN.read_text(encoding='utf-8'))
        self.assertEqual(j['commit'],'f2827f25da5a01215fcbdc0b9a48e3900d654384')
        self.assertEqual(j['script_size'],79798)
        self.assertEqual(j['script_sha256'],hashlib.sha256(ORIGINAL.read_bytes()).hexdigest())

if __name__=='__main__':
    unittest.main(verbosity=2)
