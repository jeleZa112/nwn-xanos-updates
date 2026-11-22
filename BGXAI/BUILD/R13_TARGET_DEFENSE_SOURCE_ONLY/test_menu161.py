#!/usr/bin/env python3
"""Invariant test: menu161 adds a pinned R13 pilot without altering 1..160.
This test runs on a disposable GitHub CI checkout, never in the game.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[3]
OLD=ROOT/'BGXAI/BGXAI_SYNC.ps1'
NEW=ROOT/'BGXAI/BUILD/R13_TARGET_DEFENSE_SOURCE_ONLY/BGXAI_SYNC_161_CANDIDATE.ps1'
STAGE=ROOT/'BGXAI/patchsets/ranged_fighter_guarded_20261119'
RENAMES=[('remoteRoot','xrr'),('release064g','x64'),('release066s','x6s'),
 ('release066','x66'),('release056','x56'),('release061','x61'),
 ('release067','x67'),('release043p','x43')]
DECL="$td13=@{id='TD13';version='0.3.84-R13-TARGET-RO';manifest=($rg.prefix+'BGXAI_R13_MANIFEST_V1.json');prefix=$rg.prefix;localPath=Join-Path $GameRoot 'BGXAI_DEV\\weapon_target_r13';names=@('BGXAI_R13_GUARDED.py','M_BGXTDEF13.lua')}\n"
MENU='161 - Target defense R13 (READ ONLY preflight / guarded pilot)\n'
HANDLER="'161' {SyncRelease $td13;& py -3 (Join-Path $td13.localPath 'BGXAI_R13_GUARDED.py') --game $GameRoot;if($LASTEXITCODE){throw '161 STOP'};break}\n"

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old=OLD.read_bytes().decode('utf-8')
        cls.new=NEW.read_bytes().decode('utf-8')
    def test_01_old_updater_unchanged(self):
        self.assertEqual(len(OLD.read_bytes()),79943)
        self.assertEqual(hashlib.sha256(OLD.read_bytes()).hexdigest(),
          'b7e62b0e1fba2a6f6730508c02718da2c56211b1f98344adbb135735abfe9697')
    def test_02_new_updater_under_limit(self):
        self.assertEqual(len(NEW.read_bytes()),79610)
        self.assertLessEqual(len(NEW.read_bytes()),80000)
    def test_03_old_handlers_unmodified(self):
        f=lambda text:re.findall(r"(?m)^'(\d+)' \{",text)
        self.assertEqual(f(self.old),[str(i) for i in range(1,161)])
        self.assertEqual(f(self.new),[str(i) for i in range(1,162)])
    def test_04_full_reversible_patch(self):
        a=self.new.replace(DECL,'').replace(MENU,'').replace(HANDLER,'')
        for old,new in RENAMES:
            a=re.sub(r'\$'+re.escape(new)+r'\b','$'+old,a)
        self.assertEqual(a,self.old)
    def test_05_one_new_handler_and_menu(self):
        self.assertEqual(self.new.count(MENU),1)
        self.assertEqual(self.new.count(HANDLER),1)
        self.assertEqual(self.new.count(DECL),1)
    def test_06_source_release_files_and_sha(self):
        manifest=json.loads((STAGE/'BGXAI_R13_MANIFEST_V1.json').read_text())
        self.assertEqual(manifest['schema'],1)
        self.assertEqual(manifest['version'],'0.3.84-R13-TARGET-RO')
        self.assertEqual(len(manifest['files']),2)
        for x in manifest['files']:
            self.assertEqual(x['source'],'BGXAI/patchsets/ranged_fighter_guarded_20261119/'+x['dest'])
            b=(STAGE/x['dest']).read_bytes()
            self.assertEqual(len(b),x['size'])
            self.assertEqual(hashlib.sha256(b).hexdigest(),x['sha256'])
    def test_07_no_direct_game_commands_in_r13(self):
        source=(STAGE/'M_BGXTDEF13.lua').read_text()
        for cmd in ('SelectWeaponAbility(','ClearActions(','ActionOverride(',
                    'SetGlobal(','XEquipItem(','Attack(','Stop('):
            self.assertNotIn(cmd,source)
        self.assertEqual(source.count('EEex_Action_AddSpriteStartedActionListener(R.on_started)'),1)
    def test_08_install_guard_requires_token(self):
        script=(STAGE/'BGXAI_R13_GUARDED.py').read_text()
        self.assertIn('INSTALL_BGXAI_R13_PASSIVE_TARGET',script)
        self.assertIn('ROLLBACK_BGXAI_R13_PASSIVE_TARGET',script)
        self.assertIn('NOT_LAST_WEIDU_ROLLBACK_FORBIDDEN',script)
        self.assertIn('external_backup(root)',script)
    def test_09_161_handler_has_no_inline_install(self):
        self.assertNotIn('install',HANDLER.lower())
        self.assertIn('SyncRelease',HANDLER)
        self.assertIn('BGXAI_R13_GUARDED.py',HANDLER)
    def test_10_no_legacy_bootstrap_change(self):
        cmd=ROOT/'BGXAI_UPDATE.cmd'
        self.assertTrue(cmd.is_file())
        self.assertNotIn('M_BGXTDEF13',cmd.read_text(errors='replace'))

if __name__=='__main__':unittest.main(verbosity=2)
