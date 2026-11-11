"""Mock WeiDU install+rollback tests for source-only BGXAI 064.

Never calls any game process, never writes to a live game. Mocks a minimal
WeiDU trace and verifies that the exact signed 061 Lua becomes the exact 064
candidate, then returns to byte-identical 061 after WeiDU mock-uninstall.
"""
from __future__ import annotations
import tempfile
import unittest
from unittest.mock import patch
import subprocess
from pathlib import Path
import BGXAI64_INSTALL_SOURCE_ONLY as m
import BGXAI64_PREFLIGHT_READONLY as pre
import BGXAI64_PATCH as delta

HERE=Path(__file__).resolve().parent
LUA061=(HERE/'M_BX43_061_BASELINE_READONLY.lua').read_bytes()
LUA064=(HERE/'M_BX43_064_CANDIDATE.lua').read_bytes()

class FakeWeiDU:
    def __init__(self, *, fail_install=False, fail_rollback=False):
        self.actions=[]
        self.fail_install=fail_install
        self.fail_rollback=fail_rollback
    def __call__(self, cmd, *, cwd, **kwargs):
        root=Path(cwd)
        install='--force-install' in cmd
        self.actions.append('install' if install else 'rollback')
        if (install and self.fail_install) or (not install and self.fail_rollback):
            return subprocess.CompletedProcess(cmd,1,'MOCK WEIDU STOP','forced failure')
        log=root/'WeiDU.log'
        if install:
            (root/m.LUA).write_bytes((root/m.STAGED_LUA).read_bytes())
            with log.open('ab') as out:out.write(b'~BGX64\\SETUP-BGX64.TP2~ #0 #0\n')
        else:
            (root/m.LUA).write_bytes(LUA061)
            lines=log.read_bytes().splitlines(keepends=True)
            assert m.LAST064.search(lines[-1].decode())
            log.write_bytes(b''.join(lines[:-1]))
        return subprocess.CompletedProcess(cmd,0,'MOCK WEIDU PASS','')

class InstallMock064(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='bgx64_mock_');self.addCleanup(self.temp.cleanup)
        self.home=Path(self.temp.name)
        self.game=self.home/'game';self.game.mkdir()
        self.bcs=b'SC\nDUMMY_BCS_NO_REAL_GAME_RESOURCE\nSC\n'
        self.bcs_sha=delta.digest(self.bcs)
        self.backup=self.home/'safe_backups'
        def put(name, b):
            dest=self.game/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
        put('WeiDU.log',b'~BGX61\\SETUP-BGX61.TP2~ #0 #0\n')
        put('chitin.key',b'MOCK GAME KEY')
        put('weidu.conf',b'MOCK CONFIG')
        put('lang/ru_RU/dialog.tlk',b'MOCK dialog')
        put('lang/ru_RU/dialogf.tlk',b'MOCK dialogf')
        put(m.BCS,self.bcs)
        put(m.LUA,LUA061)
        put('BGX61/staged/BDDEFAI.BCS',self.bcs)
        put('BGX61/staged/M_BX43.lua',LUA061)
        put(m.WEIDU,b'MZ'+b'1'*100005)
        self.fake=FakeWeiDU()
        self.realcheck=pre.check
        self.patches=[
            patch.object(m,'BCS_SHA',self.bcs_sha),
            patch.object(pre,'BCS_SHA',self.bcs_sha),
            patch.object(pre,'check',side_effect=lambda root:self.realcheck(root,bcs_pin=self.bcs_sha)),
        ]
        for p in self.patches:p.start();self.addCleanup(p.stop)
        self.mockbackup=lambda root,state,label:m.make_backup(root,state,label,parent=self.backup)
    def install(self, *, run=None, guard=lambda:None):
        return m.install(self.game,guard=guard,backup=self.mockbackup,runner=run or self.fake)
    def rollback(self, *, run=None, guard=lambda:None):
        return m.rollback(self.game,guard=guard,backup=self.mockbackup,runner=run or self.fake)
    def test_live_candidate_pin(self):
        self.assertEqual(delta.digest(LUA061),m.LUA061_SHA)
        self.assertEqual(delta.digest(LUA064),m.LUA064_SHA)
        self.assertEqual(m.source_check(),LUA064)
    def test_full_install_and_rollback_cycle(self):
        before={rel:(self.game/rel).read_bytes() for rel in m.BACKUP}
        result=self.install()
        self.assertEqual(result['status'],'INSTALLED_064_EXPERIMENTAL')
        self.assertEqual(self.fake.actions,['install'])
        self.assertEqual((self.game/m.LUA).read_bytes(),LUA064)
        self.assertEqual((self.game/m.BCS).read_bytes(),self.bcs)
        self.assertEqual((self.game/'BGX61/staged/M_BX43.lua').read_bytes(),LUA061)
        self.assertEqual((self.game/m.STAGED_LUA).read_bytes(),LUA064)
        proof=Path(result['backup'])/'BACKUP_PROOF.json'
        self.assertTrue(proof.is_file())
        for rel in m.BACKUP:
            self.assertEqual((Path(result['backup'])/rel).read_bytes(),before[rel])
        rollback=self.rollback()
        self.assertEqual(rollback['status'],'ROLLED_BACK_TO_061')
        self.assertEqual(self.fake.actions,['install','rollback'])
        self.assertEqual((self.game/m.LUA).read_bytes(),LUA061)
        self.assertEqual((self.game/m.BCS).read_bytes(),self.bcs)
        self.assertEqual((self.game/'WeiDU.log').read_bytes(),before['WeiDU.log'])
    def test_process_guard_denies_before_stage(self):
        def deny():raise m.Stop('PROCESS_ACTIVE')
        with self.assertRaisesRegex(m.Stop,'PROCESS_ACTIVE'):self.install(guard=deny)
        self.assertFalse((self.game/'BGX64').exists())
        self.assertEqual(self.fake.actions,[])
    def test_source_requires_061_last(self):
        with (self.game/'WeiDU.log').open('ab') as f:f.write(b'~OTHER/SETUP-OTHER.TP2~ #0 #0\n')
        with self.assertRaisesRegex(m.Stop,'LAST_WEIDU_NOT_061'):self.install()
        self.assertFalse((self.game/'BGX64').exists())
    def test_bcs_drift_blocks_stage(self):
        (self.game/m.BCS).write_bytes(b'BAD BCS')
        with self.assertRaisesRegex(m.Stop,'INSTALLED_BCS_MISMATCH'):self.install()
        self.assertFalse((self.game/'BGX64').exists())
    def test_lua_drift_blocks_stage(self):
        (self.game/m.LUA).write_bytes(b'BAD LUA')
        with self.assertRaisesRegex(m.Stop,'INSTALLED_LUA_MISMATCH'):self.install()
        self.assertFalse((self.game/'BGX64').exists())
    def test_stage_collision_blocks(self):
        (self.game/'BGX64').mkdir()
        with self.assertRaisesRegex(m.Stop,'064_STAGE_COLLISION'):self.install()
    def test_backup_failure_blocks_game_staging(self):
        def failbackup(*args):raise m.Stop('BACKUP_VERIFICATION_FAIL')
        with self.assertRaisesRegex(m.Stop,'BACKUP_VERIFICATION_FAIL'):
            m.install(self.game,guard=lambda:None,backup=failbackup,runner=self.fake)
        self.assertFalse((self.game/'BGX64').exists())
    def test_weidu_install_failure_no_blind_retry(self):
        failed=FakeWeiDU(fail_install=True)
        with self.assertRaisesRegex(m.Stop,'DO_NOT_RETRY'):self.install(run=failed)
        self.assertEqual(failed.actions,['install'])
        self.assertEqual((self.game/m.LUA).read_bytes(),LUA061)
        self.assertTrue(any(self.backup.glob('PRE_INSTALL_*/BACKUP_PROOF.json')))
    def test_rollback_blocks_foreign_last(self):
        self.install()
        with (self.game/'WeiDU.log').open('ab') as f:f.write(b'~OTHER/SETUP-OTHER.TP2~ #0 #0\n')
        with self.assertRaisesRegex(m.Stop,'WEIDU_LAST_NOT_064'):self.rollback()
        self.assertEqual(self.fake.actions,['install'])
    def test_rollback_blocks_lua_drift(self):
        self.install()
        (self.game/m.LUA).write_bytes(b'CHANGED')
        with self.assertRaisesRegex(m.Stop,'LUA_NOT_064'):self.rollback()
        self.assertEqual(self.fake.actions,['install'])
    def test_manual_confirmation_mandatory(self):
        self.assertEqual(m.main(['install','--game-root',str(self.game)]),2)
        self.assertEqual(m.main(['install','--yes','--confirm','WRONG','--game-root',str(self.game)]),2)
        self.assertEqual(m.main(['rollback','--yes','--confirm','WRONG','--game-root',str(self.game)]),2)
        self.assertFalse((self.game/'BGX64').exists())
    def test_valid_preflight_is_read_only(self):
        before={p.relative_to(self.game):p.read_bytes() for p in self.game.rglob('*') if p.is_file()}
        out=m.read_status_061(self.game)
        after={p.relative_to(self.game):p.read_bytes() for p in self.game.rglob('*') if p.is_file()}
        self.assertEqual(out['game_lua_sha'],m.LUA061_SHA)
        self.assertEqual(before,after)
    def test_installer_still_blocked_on_non_windows(self):
        if m.os.name!='nt':
            with self.assertRaisesRegex(m.Stop,'WINDOWS_REQUIRED'):m.process_guard()

    def test_fixed_windows_game_root_enforced_for_install(self):
        # Even a correct authorization token cannot change a different game.
        with patch.object(m,'install') as installed:
            self.assertEqual(m.main(['install','--game-root',str(self.game),
                                     '--yes','--confirm','INSTALL_BGXAI_064']),2)
            installed.assert_not_called()
        self.assertFalse((self.game/'BGX64').exists())

    def test_fixed_windows_game_root_enforced_for_rollback(self):
        with patch.object(m,'rollback') as rolled:
            self.assertEqual(m.main(['rollback','--game-root',str(self.game),
                                     '--yes','--confirm','ROLLBACK_BGXAI_064']),2)
            rolled.assert_not_called()

    def test_read_only_status_061_validates_all_pinned_bytes(self):
        self.assertEqual(m.main(['status','--game-root',str(self.game)]),0)
        (self.game/m.LUA).write_bytes(b'CORRUPTED')
        self.assertEqual(m.main(['status','--game-root',str(self.game)]),2)

    def test_read_only_status_064_validates_actual_stage(self):
        self.install()
        self.assertEqual(m.main(['status','--game-root',str(self.game)]),0)
        (self.game/m.STAGED_LUA).write_bytes(b'CORRUPTED')
        self.assertEqual(m.main(['status','--game-root',str(self.game)]),2)

    def test_last_guard_blocks_install_if_game_opens_after_staging(self):
        count=[0]
        def changing_state():
            count[0]+=1
            if count[0]==3:raise m.Stop('GAME_BECAME_ACTIVE')
        with self.assertRaisesRegex(m.Stop,'GAME_BECAME_ACTIVE'):
            self.install(guard=changing_state)
        self.assertEqual(count[0],3)
        self.assertEqual(self.fake.actions,[])
        self.assertEqual((self.game/m.LUA).read_bytes(),LUA061)
        self.assertTrue(any(self.backup.glob('PRE_INSTALL_*/BACKUP_PROOF.json')))

    def test_last_guard_blocks_rollback_if_game_opens(self):
        self.install()
        count=[0]
        def changing_state():
            count[0]+=1
            if count[0]==3:raise m.Stop('GAME_BECAME_ACTIVE')
        with self.assertRaisesRegex(m.Stop,'GAME_BECAME_ACTIVE'):
            self.rollback(guard=changing_state)
        self.assertEqual(count[0],3)
        self.assertEqual(self.fake.actions,['install'])
        self.assertEqual((self.game/m.LUA).read_bytes(),LUA064)

    def test_valid_fixed_root_optin_only_with_exact_phrase(self):
        with patch.object(m,'ROOT',self.game), patch.object(m,'install',return_value={'status':'MOCK_OK'}) as mock:
            self.assertEqual(m.main(['install','--game-root',str(self.game),
                                     '--yes','--confirm','INSTALL_BGXAI_064']),0)
            mock.assert_called_once_with(self.game)

if __name__=='__main__':unittest.main()
