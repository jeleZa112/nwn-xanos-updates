#!/usr/bin/env python3
"""Offline install/preflight/rollback tests, mock WeiDU only. No game writes."""
from __future__ import annotations
import hashlib
import io
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from types import SimpleNamespace
from contextlib import redirect_stdout

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
import BGXAI43_PROBE_INSTALL as mod
SOURCE=Path('/mnt/data/BGXAI_042B_REVIEW/BDDEFAI_042B_VERIFY_ONLY.BCS')


def mocked_root(root:Path):
    (root/'override').mkdir()
    (root/'lang'/'ru_RU').mkdir(parents=True)
    (root/'chitin.key').write_bytes(b'K'*2048)
    (root/mod.WEIDU_EXE).write_bytes(b'MZ'+b'W'*120000)
    (root/'InfinityLoader.exe').write_bytes(b'MZ'+b'L'*12000)
    (root/mod.EEEX_BOOT).write_bytes(b'-- EEex mod load stub\n')
    (root/'InfinityLoader.ini').write_text('LuaPatchMode=REPLACE_INTERNAL_WITH_EXTERNAL\n')
    (root/'lang/ru_RU/dialog.tlk').write_bytes(b'TLK V1  '+b'\x00'*128)
    (root/'lang/ru_RU/dialogf.tlk').write_bytes(b'TLK V1  '+b'\x00'*128)
    shutil.copyfile(SOURCE,root/mod.BCS)
    (root/mod.WEIDU_LOG).write_text('~enhanced-powergaming-scripts/setup-enhanced-powergaming-scripts.tp2~ #0 #0\n~BGX42/setup-BGX42.tp2~ #0 #0\n')


class FakeWeiDU:
    def __init__(self, fail=False, modify_bcs=False):self.fail=fail;self.modify_bcs=modify_bcs;self.calls=[]
    def __call__(self,args,**kwargs):
        root=Path(kwargs['cwd']);self.calls.append(args)
        is_uninstall='--force-uninstall' in args
        if not is_uninstall:
            shutil.copyfile(root/mod.MOD_LUA,root/mod.INSTALLED_LUA)
            with (root/mod.WEIDU_LOG).open('a') as f:f.write('~BGX43/setup-BGX43.tp2~ #0 #0\n')
        else:
            (root/mod.INSTALLED_LUA).unlink()
            lines=(root/mod.WEIDU_LOG).read_text().splitlines()
            (root/mod.WEIDU_LOG).write_text('\n'.join(x for x in lines if 'BGX43' not in x)+'\n')
        if self.modify_bcs:(root/mod.BCS).write_bytes(b'BAD')
        return SimpleNamespace(returncode=1 if self.fail else 0,stdout='MOCK ONLY',stderr='')


class SetUp(unittest.TestCase):
    def setUp(self):
        if not SOURCE.is_file() or mod.sha(SOURCE)!=mod.BCS_042B_HASH:
            raise unittest.SkipTest('private source fixture BCS not mounted; no fake substitute')
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)/'game'
        self.root.mkdir()
        mocked_root(self.root)
        self.pkg=ROOT
        self.bkp=Path(self.tmp.name)/'backups'
    def tearDown(self):self.tmp.cleanup()
    def test_source_manifest(self):self.assertEqual(mod.verify_package(self.pkg)['version'],'0.3.14-043-PROBE')
    def test_game_preflight(self):
        x=mod.check_game(self.root,require_root=False)
        self.assertEqual(x['bcs_sha256'],mod.BCS_042B_HASH)
    def test_existing_042b_last(self):self.assertRegex(mod.active(self.root)[-1],mod.MOD42_RE)
    def test_wrong_last_mod(self):
        with (self.root/mod.WEIDU_LOG).open('a') as f:f.write('~SOMETHING/setup.tp2~ #0 #0\n')
        with self.assertRaisesRegex(RuntimeError,'042B not last'):mod.check_game(self.root,require_root=False)
    def test_wrong_bcs(self):
        (self.root/mod.BCS).write_bytes(b'CORRUPTED'*2000)
        with self.assertRaisesRegex(RuntimeError,'not exact live 042B'):mod.check_game(self.root,require_root=False)
    def test_eeex_missing(self):
        (self.root/mod.EEEX_BOOT).unlink()
        with self.assertRaisesRegex(RuntimeError,'M___EEex'):mod.check_game(self.root,require_root=False)
    def test_existing_probe_collision(self):
        (self.root/mod.INSTALLED_LUA).write_text('-- collision')
        with self.assertRaisesRegex(RuntimeError,'probe file collision'):mod.check_game(self.root,require_root=False)
    def test_manifest_tampering(self):
        tmp=Path(self.tmp.name)/'pkg';shutil.copytree(self.pkg,tmp,ignore=shutil.ignore_patterns('__pycache__'))
        with (tmp/mod.MOD_LUA).open('a') as f:f.write('-- modified\n')
        with self.assertRaisesRegex(RuntimeError,'tampered source'):mod.verify_package(tmp)
    def test_symlink_rejected(self):
        p=self.root/'override'/'bad_alias';p.symlink_to(self.root/'chitin.key')
        with self.assertRaisesRegex(RuntimeError,'symlink'):mod.safe(self.root,'override/bad_alias')
    def test_hidden_game_altered_rejected(self):
        with (self.root/mod.WEIDU_LOG).open('a') as f:f.write('~BGX43/setup-BGX43.tp2~ #0 #0\n')
        with self.assertRaisesRegex(RuntimeError,'042B not last'):mod.check_game(self.root,require_root=False)
    def test_status_read_only_baseline(self):
        before=mod.sha(self.root/mod.BCS)
        with redirect_stdout(io.StringIO()) as stream:mod.status(self.root,self.pkg,require_root=False,backup_dir=self.bkp)
        self.assertIn('BGX43 installed: False',stream.getvalue())
        self.assertEqual(mod.sha(self.root/mod.BCS),before)
    def install(self):
        fake=FakeWeiDU()
        r=mod.install(self.root,self.pkg,guard=lambda:None,runner=fake,require_root=False,backup_dir=self.bkp)
        return r,fake
    def test_install_success(self):
        res,fw=self.install()
        self.assertEqual(res['status'],'INSTALLED_PASSIVE_043')
        self.assertEqual(len(fw.calls),1)
        self.assertEqual(mod.sha(self.root/mod.BCS),mod.BCS_042B_HASH)
        self.assertEqual(mod.sha(self.root/mod.INSTALLED_LUA),mod.sha(self.pkg/mod.MOD_LUA))
    def test_only_lua_override_added(self):
        before=set(p.name for p in (self.root/'override').iterdir());res,_=self.install()
        after=set(p.name for p in (self.root/'override').iterdir())
        self.assertEqual(after-before,{'M_BGX43Probe.lua'})
    def test_external_backup(self):
        res,_=self.install();p=Path(res['backup'])
        self.assertTrue((p/'chitin.key').is_file());self.assertTrue((p/mod.BCS).is_file())
        self.assertEqual(mod.sha(p/mod.BCS),mod.BCS_042B_HASH)
        self.assertTrue((p/'before.json').is_file());self.assertTrue((p/'report.json').is_file())
    def test_backup_verified(self):
        _,_=self.install()
        self.assertTrue(mod.backup_for_uninstall(self.root,base=self.bkp).is_dir())
    def test_uninstall_success(self):
        self.install()
        proc=FakeWeiDU()
        result=mod.uninstall(self.root,self.pkg,guard=lambda:None,runner=proc,require_root=False,backup_dir=self.bkp)
        self.assertEqual(result['status'],'UNINSTALLED_PASSIVE_043')
        self.assertFalse((self.root/mod.INSTALLED_LUA).exists())
        self.assertEqual(mod.sha(self.root/mod.BCS),mod.BCS_042B_HASH)
    def test_rollback_wrong_last_refused(self):
        self.install()
        with (self.root/mod.WEIDU_LOG).open('a') as f:f.write('~OTHER/setup.tp2~ #0 #0\n')
        with self.assertRaisesRegex(RuntimeError,'043 probe not the last'):mod.uninstall(self.root,self.pkg,guard=lambda:None,require_root=False,backup_dir=self.bkp)
    def test_rollback_missing_backup_refused(self):
        self.install()
        shutil.rmtree(self.bkp)
        with self.assertRaisesRegex(RuntimeError,'backup missing'):mod.uninstall(self.root,self.pkg,guard=lambda:None,require_root=False,backup_dir=self.bkp)
    def test_rollback_tampered_backup_refused(self):
        res,_=self.install()
        (Path(res['backup'])/mod.BCS).write_bytes(b'tampered')
        with self.assertRaisesRegex(RuntimeError,'no verified successful'):mod.uninstall(self.root,self.pkg,guard=lambda:None,require_root=False,backup_dir=self.bkp)
    def test_rollback_modified_lua_refused(self):
        self.install()
        (self.root/mod.INSTALLED_LUA).write_text('-- tampered')
        with self.assertRaisesRegex(RuntimeError,'observer Lua was changed'):mod.uninstall(self.root,self.pkg,guard=lambda:None,require_root=False,backup_dir=self.bkp)
    def test_rollback_invalid_chitin_refused(self):
        self.install()
        (self.root/'chitin.key').write_bytes(b'changed'*400)
        with self.assertRaisesRegex(RuntimeError,'chitin changed'):mod.uninstall(self.root,self.pkg,guard=lambda:None,require_root=False,backup_dir=self.bkp)
    def test_double_install_refused(self):
        self.install()
        with self.assertRaisesRegex(RuntimeError,'042B not last'):mod.install(self.root,self.pkg,guard=lambda:None,require_root=False,backup_dir=self.bkp)
    def test_install_nonzero_mock_weidu(self):
        fake=FakeWeiDU(fail=True)
        out=mod.install(self.root,self.pkg,guard=lambda:None,runner=fake,require_root=False,backup_dir=self.bkp)
        self.assertEqual(out['status'],'REVIEW_WEIDU')
    def test_install_bcs_changed_by_mock_is_review(self):
        fake=FakeWeiDU(modify_bcs=True)
        out=mod.install(self.root,self.pkg,guard=lambda:None,runner=fake,require_root=False,backup_dir=self.bkp)
        self.assertEqual(out['status'],'REVIEW_WEIDU')
    def test_rollback_prestate_snapshot(self):
        self.install()
        r=mod.uninstall(self.root,self.pkg,guard=lambda:None,runner=FakeWeiDU(),require_root=False,backup_dir=self.bkp)
        self.assertTrue(Path(r['backup']).is_dir())
        self.assertTrue((Path(r['backup'])/mod.INSTALLED_LUA).is_file())
    def test_status_after_install(self):
        self.install()
        with redirect_stdout(io.StringIO()) as out:mod.status(self.root,self.pkg,require_root=False,backup_dir=self.bkp)
        self.assertIn('BGX43 installed: True',out.getvalue())
        self.assertIn('Verified rollback backup:',out.getvalue())
    def test_password_fails_without_changes(self):
        self.assertFalse((self.root/mod.MOD_DIR).exists())
    def test_no_action_writes(self):
        code=(self.pkg/mod.MOD_LUA).read_text()
        self.assertNotIn('ClearActions(', '\n'.join(x.split('--')[0] for x in code.splitlines()))
        self.assertNotIn('EEex_Action_Queue', '\n'.join(x.split('--')[0] for x in code.splitlines()))
    def test_user_callback_notice_once(self):
        lua=(self.pkg/mod.MOD_LUA).read_text()
        self.assertIn('P.firstNoticeShown',lua)
        self.assertIn('type(Infinity_DisplayString) == "function"',lua)
    def test_strict_status_arg_supported(self):
        with redirect_stdout(io.StringIO()) as out:
            self.assertEqual(mod.main(['--status','--game-root',str(self.root)]),0)
        self.assertIn('STATUS',out.getvalue())
