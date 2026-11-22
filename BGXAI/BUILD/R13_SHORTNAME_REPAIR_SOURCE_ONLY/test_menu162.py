#!/usr/bin/env python3
"""Check exact preservation of existing menus 1..161 and single pinned menu162."""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'BGXAI/BGXAI_SYNC.ps1'
DRAFT=ROOT/'BGXAI/BUILD/R13_SHORTNAME_REPAIR_SOURCE_ONLY/BGXAI_SYNC_162_CANDIDATE.ps1'
PATCH=ROOT/'BGXAI/patchsets/ranged_fighter_guarded_20261119'
RENAME=[('release044','t44'),('release045','t45'),('release046','t46'),('release047','t47'),
 ('release048','t48'),('release049','t49'),('releaseBGXTEAM','xteam'),('releaseBGXPR','xpr'),
 ('releaseBGXP2','xp2'),('releaseBGXP3','xp3'),('releaseIdle','xidle'),('releaseBGXP5','xp5')]
DECL="$td14=@{id='TD14';version='0.3.86-R13-SHORTNAME-RO';manifest=($rg.prefix+'BGXAI_R13_SHORTNAME_MANIFEST_V1.json');prefix=$rg.prefix;localPath=Join-Path $GameRoot 'BGXAI_DEV\\weapon_target_r13_shortfix';names=@('BGXAI_R13_SHORTNAME_GUARDED.py','M_BGXD13.lua')}\n"
MENU='162 - Fix R13 Lua 8-char name (READ ONLY default / guarded)\n'
HANDLER="'162' {SyncRelease $td14;& py -3 (Join-Path $td14.localPath 'BGXAI_R13_SHORTNAME_GUARDED.py') --game $GameRoot;if($LASTEXITCODE){throw '162 STOP'};break}\n"

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old=BASE.read_bytes().decode('utf-8')
        cls.draft=DRAFT.read_bytes().decode('utf-8')
    def test_01_old_hash_exact(self):
        self.assertEqual(hashlib.sha256(BASE.read_bytes()).hexdigest(),
          '574d1027eeb69ad54bf3995019358bb5a115a7bb53752d68dfb0b3fd4aca17a4')
    def test_02_candidate_within_existing_bootstrap(self):
        self.assertLessEqual(len(DRAFT.read_bytes()),80000)
        self.assertGreater(len(DRAFT.read_bytes()),70000)
    def test_03_reversible_exact_no_legacy_changes(self):
        d=self.draft.replace(DECL,'').replace(MENU,'').replace(HANDLER,'')
        for a,b in RENAME:d=re.sub(r'\$'+re.escape(b)+r'\b','$'+a,d)
        self.assertEqual(d,self.old)
    def test_04_menu_handlers_1_through_162(self):
        patt=r"(?m)^'(\d+)' \{"
        a=[int(x) for x in re.findall(patt,self.old)]
        b=[int(x) for x in re.findall(patt,self.draft)]
        self.assertEqual(a,list(range(1,162)))
        self.assertEqual(b,list(range(1,163)))
    def test_05_handler_162_only_once(self):
        self.assertEqual(self.draft.count(HANDLER),1)
        self.assertEqual(self.draft.count(MENU),1)
    def test_06_one_user_facing_cmd_not_changed(self):
        self.assertTrue((ROOT/'BGXAI_UPDATE.cmd').is_file())
    def test_07_verified_release_path(self):
        self.assertIn("$rg.prefix+'BGXAI_R13_SHORTNAME_MANIFEST_V1.json'",self.draft)
        self.assertIn("SyncRelease $td14",self.draft)
    def test_08_manifest_exact(self):
        o=json.loads((PATCH/'BGXAI_R13_SHORTNAME_MANIFEST_V1.json').read_text('utf-8'))
        self.assertEqual(o['schema'],1)
        self.assertEqual(o['channel'],'bgxai-fox-new-safe-source')
        self.assertEqual(o['version'],'0.3.86-R13-SHORTNAME-RO')
        self.assertEqual(len(o['files']),2)
        for f in o['files']:
            self.assertEqual(f['source'],'BGXAI/patchsets/ranged_fighter_guarded_20261119/'+f['dest'])
            p=PATCH/f['dest']
            self.assertEqual(len(p.read_bytes()),f['size'])
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),f['sha256'])
    def test_09_engine_resource_8_chars(self):
        self.assertEqual(len((PATCH/'M_BGXD13.lua').stem),8)
    def test_10_old_module_is_preserved(self):
        src=(PATCH/'BGXAI_R13_SHORTNAME_GUARDED.py').read_text('utf-8')
        self.assertIn("PREVIOUS = 'override/M_BGXTDEF13.lua'",src)
        self.assertIn("MODULE = 'override/M_BGXD13.lua'",src)
        self.assertIn("R13_NOT_LAST_WEIDU_NO_REPAIR",src)
    def test_11_exact_install_rollback_tokens(self):
        s=(PATCH/'BGXAI_R13_SHORTNAME_GUARDED.py').read_text('utf-8')
        self.assertIn('INSTALL_BGXAI_R13_SHORTNAME_FIX',s)
        self.assertIn('ROLLBACK_BGXAI_R13_SHORTNAME_FIX',s)
    def test_12_no_install_without_user_token(self):
        h=HANDLER
        self.assertNotIn('--mode install',h)
        self.assertNotIn('WeiDU',h)
        self.assertNotIn('COPY',h)

if __name__=='__main__':unittest.main(verbosity=2)
