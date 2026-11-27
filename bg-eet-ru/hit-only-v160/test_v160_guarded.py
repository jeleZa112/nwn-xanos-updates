# -*- coding: utf-8 -*-
import importlib.util, hashlib, json, os, tempfile, unittest
from pathlib import Path
from unittest.mock import patch

SOURCE = Path(__file__).with_name('v160_guarded.py')
SPEC = importlib.util.spec_from_file_location('v160_guarded', SOURCE)
v = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(v)
ADDITION = Path(__file__).with_name('BG_EET_RU_V160_HIT_ONLY_APPEND.lua').read_bytes()


def sha(x): return hashlib.sha256(x).hexdigest()

class GuardedV160Test(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.game = Path(self.tmp.name)/'game'; self.game.mkdir()
        self.work = Path(self.tmp.name)/'outside'; self.work.mkdir()
        (self.game/'chitin.key').write_bytes(b'CHITIN')
        self.prefix = b'''-- baseline V106 fixture\nfunction BG_EET_RU_WEAPON_EVENT_OBSERVER_V1_OnBaseDamage(context) return nil end\n'''
        self.tail = b'''\n-- V108 fixture\nfunction BG_EET_RU_WEAPON_EVENT_OBSERVER_V1_OnBaseDamage(context) return nil end\n'''
        self.baseline = self.prefix + self.tail
        self.target = self.game/v.MODULE_REL
        self.target.parent.mkdir(parents=True)
        self.target.write_bytes(self.baseline)
        self.pin_override={
            'V106_BASE_SHA':sha(self.prefix), 'V108_TAIL_SHA':sha(self.tail),
            'V108_TAIL_SIZE':len(self.tail),
        }
        self.patches=[patch.object(v,n,k) for n,k in self.pin_override.items()]
        for p in self.patches: p.start(); self.addCleanup(p.stop)
        gamepins={}
        for rel in v.GAME_PINS:
            item=self.game/rel
            item.parent.mkdir(parents=True,exist_ok=True)
            item.write_bytes(('CHECK_'+rel).encode())
            gamepins[rel]=sha(item.read_bytes())
        (self.game/'WeiDU.log').write_bytes(b'// installed mod entry\n'*15)
        p=patch.object(v,'GAME_PINS',gamepins);p.start();self.addCleanup(p.stop)
        (self.work/'BG_EET_RU_V108_NATIVE_ITEM_STATE.json').write_text(
            json.dumps({'phase':'INSTALLED','candidate_sha256':sha(self.baseline)}),'utf8')

    def test_pinned_lua_and_callback_contract(self):
        self.assertEqual(len(ADDITION),v.APPEND_SIZE)
        self.assertEqual(sha(ADDITION),v.APPEND_SHA)
        self.assertEqual(ADDITION.count(b'BG_EET_RU_V160_previous'),2)
        self.assertNotIn(b'EEex_Sprite_AddAlterBaseWeaponDamageListener(',ADDITION)
        self.assertNotIn(b'os.execute',ADDITION)
        self.assertNotIn(b'io.open',ADDITION)

    def test_weidu_may_change_before_preflight_but_is_captured(self):
        data = b'// mod list updated yesterday\r\n' * 12
        (self.game/'WeiDU.log').write_bytes(data)
        result = v.run('preflight', self.game, self.work)
        self.assertEqual(result['status'], 'V160_PREFLIGHT_PASS')
        self.assertEqual(result['current_weidu_sha256'], sha(data))
        self.assertEqual(self.target.read_bytes(), self.baseline)

    def test_weidu_changes_during_confirmed_install_must_stop(self):
        original_game_closed = v._game_closed
        calls = []
        def mutate_after_first():
            calls.append(1)
            if len(calls) == 2:
                (self.game/'WeiDU.log').write_bytes(b'// changed during confirm\n'*10)
        with patch.object(v, '_game_closed', side_effect=mutate_after_first):
            r = v.run('install', self.game, self.work, ADDITION, approval=v.APPROVE_INSTALL)
        self.assertEqual(r['status'], 'V160_SAFE_STOP')
        self.assertEqual(self.target.read_bytes(), self.baseline)
        self.assertFalse((self.work/v.STATE_NAME).exists())

    def test_weidu_missing_denied(self):
        (self.game/'WeiDU.log').unlink()
        self.assertEqual(v.run('preflight',self.game,self.work)['status'],'V160_SAFE_STOP')

    def test_preflight_has_zero_writes(self):
        before=self.target.read_bytes()
        r=v.run('preflight',self.game,self.work)
        self.assertEqual(r['status'],'V160_PREFLIGHT_PASS')
        self.assertEqual(self.target.read_bytes(),before)
        self.assertFalse((self.work/v.STATE_NAME).exists())

    def test_untyped_rejected_before_backup(self):
        r=v.run('install',self.game,self.work,ADDITION,approval='')
        self.assertEqual(r['status'],'V160_SAFE_STOP')
        self.assertEqual(self.target.read_bytes(),self.baseline)
        self.assertFalse((self.work/v.STATE_NAME).exists())

    def test_install_status_rollback_preserves_exact_bytes(self):
        r=v.run('install',self.game,self.work,ADDITION,approval=v.APPROVE_INSTALL)
        self.assertEqual(r['status'],'V160_INSTALLED_AWAITING_GAMEPLAY')
        self.assertEqual(r['game_files_written'],1)
        candidate=self.target.read_bytes()
        self.assertEqual(candidate,self.baseline+b'\n'+ADDITION)
        self.assertEqual(v.run('status',self.game,self.work)['status'],'V160_INSTALLED_AWAITING_GAMEPLAY')
        self.assertEqual(v.run('preflight',self.game,self.work)['status'],'V160_SAFE_STOP')
        r=v.run('rollback',self.game,self.work,approval=v.APPROVE_ROLLBACK)
        self.assertEqual(r['status'],'V160_ROLLED_BACK')
        self.assertEqual(self.target.read_bytes(),self.baseline)
        self.assertEqual(v.run('status',self.game,self.work)['status'],'V160_STATE_HOLD')

    def test_rollback_guard_blocks_drift(self):
        r=v.run('install',self.game,self.work,ADDITION,approval=v.APPROVE_INSTALL)
        self.assertEqual(r['status'],'V160_INSTALLED_AWAITING_GAMEPLAY')
        self.target.write_bytes(self.target.read_bytes()+b'NEWMOD')
        r=v.run('rollback',self.game,self.work,approval=v.APPROVE_ROLLBACK)
        self.assertEqual(r['status'],'V160_SAFE_STOP')
        self.assertIn(b'NEWMOD',self.target.read_bytes())

    def test_rollback_guard_blocks_weidu_drift(self):
        r=v.run('install',self.game,self.work,ADDITION,approval=v.APPROVE_INSTALL)
        self.assertEqual(r['status'],'V160_INSTALLED_AWAITING_GAMEPLAY')
        (self.game/'WeiDU.log').write_bytes(b'different')
        r=v.run('rollback',self.game,self.work,approval=v.APPROVE_ROLLBACK)
        self.assertEqual(r['status'],'V160_SAFE_STOP')
        self.assertNotEqual(self.target.read_bytes(),self.baseline)

    def test_preflight_requires_exact_v108_and_no_symlink(self):
        self.target.write_bytes(self.baseline+b'surprise')
        self.assertEqual(v.run('preflight',self.game,self.work)['status'],'V160_SAFE_STOP')
        self.target.unlink(); self.target.symlink_to(self.game/'chitin.key')
        self.assertEqual(v.run('preflight',self.game,self.work)['status'],'V160_SAFE_STOP')

    def test_preflight_blocks_v108_state_drift(self):
        (self.work/'BG_EET_RU_V108_NATIVE_ITEM_STATE.json').write_text(
            json.dumps({'phase':'ROLLED_BACK','candidate_sha256':sha(self.baseline)}),'utf8')
        self.assertEqual(v.run('preflight',self.game,self.work)['status'],'V160_SAFE_STOP')

    def test_preflight_blocks_no_v159_sha(self):
        (self.game/'lang/ru_RU/dialog.tlk').write_bytes(b'old')
        self.assertEqual(v.run('preflight',self.game,self.work)['status'],'V160_SAFE_STOP')

    def test_changed_lua_is_rejected(self):
        before=self.target.read_bytes()
        r=v.run('install',self.game,self.work,ADDITION+b' ',approval=v.APPROVE_INSTALL)
        self.assertEqual(r['status'],'V160_SAFE_STOP')
        self.assertEqual(self.target.read_bytes(),before)

    def test_no_external_inside_game(self):
        self.assertEqual(v.run('preflight',self.game,self.game/'backup')['status'],'V160_SAFE_STOP')

    def test_rollback_requires_typed_phrase(self):
        self.assertEqual(v.run('install',self.game,self.work,ADDITION,approval=v.APPROVE_INSTALL)['status'],'V160_INSTALLED_AWAITING_GAMEPLAY')
        snapshot=self.target.read_bytes()
        self.assertEqual(v.run('rollback',self.game,self.work,approval='')['status'],'V160_SAFE_STOP')
        self.assertEqual(self.target.read_bytes(),snapshot)

    def test_status_without_state(self):
        self.assertEqual(v.run('status',self.game,self.work)['status'],'V160_NOT_INSTALLED')

if __name__=='__main__':unittest.main(verbosity=2)
