import unittest
import tempfile
import subprocess
from unittest.mock import patch
from pathlib import Path
from hashlib import sha256
import BGXAI66_INSTALL as m
import BGXAI64_INSTALL_SOURCE_ONLY as old

BASE=m.BASE.read_bytes()
CANDIDATE=m.CANDIDATE.read_bytes()

def put(root,rel,raw):
    p=root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)

class MockWeiDU:
    def __init__(self,fail_install=False,fail_uninstall=False):
        self.calls=[];self.fail_install=fail_install;self.fail_uninstall=fail_uninstall
    def __call__(self,cmd,*,cwd,**kwargs):
        game=Path(cwd)
        inst='--force-install' in cmd
        self.calls.append('install' if inst else 'rollback')
        if (inst and self.fail_install) or (not inst and self.fail_uninstall):
            return subprocess.CompletedProcess(cmd,1,'MOCK STOP','MOCK ERROR')
        log=game/'WeiDU.log'
        if inst:
            (game/m.LUA).write_bytes((game/m.STAGE).read_bytes())
            with log.open('ab') as f:f.write(b'~BGX66\\SETUP-BGX66.TP2~ #0 #0\n')
        else:
            (game/m.LUA).write_bytes(BASE)
            log.write_bytes(b''.join(log.read_bytes().splitlines(keepends=True)[:-1]))
        return subprocess.CompletedProcess(cmd,0,'MOCK SUCCESS','')

class InstallGuard066(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory(prefix='bgx66_mock_');self.addCleanup(tmp.cleanup)
        self.home=Path(tmp.name);self.game=self.home/'game';self.game.mkdir()
        self.backups=self.home/'external_backups'
        self.bcs=b'SC\nMOCK_BCS_UNCHANGED\nSC\n';self.bcs_pin=sha256(self.bcs).hexdigest()
        put(self.game,'WeiDU.log',b'~BGX64\\SETUP-BGX64.TP2~ #0 #0\n')
        for k in ('chitin.key','weidu.conf','lang/ru_RU/dialog.tlk','lang/ru_RU/dialogf.tlk'):put(self.game,k,b'DUMMY:'+k.encode())
        put(self.game,m.BCS,self.bcs)
        put(self.game,m.LUA,BASE)
        put(self.game,old.STAGED_LUA,BASE)
        put(self.game,old.TP2,old.TP2_TEXT.encode())
        put(self.game,old.EXE,b'MZ'+b'B'*100001)
        put(self.game,m.WEIDU,b'MZ'+b'A'*100001)
        self.patchers=[patch.object(m,'PINBCS',self.bcs_pin),patch.object(old,'BCS_SHA',self.bcs_pin)]
        for p in self.patchers:p.start();self.addCleanup(p.stop)
        self.fake=MockWeiDU()
        self.backup=lambda root,before,label:old.make_backup(root,before,label,parent=self.backups)
        self.none=lambda:None
    def install(self,**kw):return m.install(self.game,process_guard=kw.get('guard',self.none),make_backup=kw.get('backup',self.backup),runner=kw.get('runner',self.fake))
    def rollback(self,**kw):return m.rollback(self.game,process_guard=kw.get('guard',self.none),make_backup=kw.get('backup',self.backup),runner=kw.get('runner',self.fake))
    def test_001_preflight_succeeds_without_mutation(self):
        before={p.relative_to(self.game):p.read_bytes() for p in self.game.rglob('*') if p.is_file()}
        self.assertEqual(m.read_064(self.game)['status'],'INSTALLED_064_VERIFIED')
        self.assertEqual(before,{p.relative_to(self.game):p.read_bytes() for p in self.game.rglob('*') if p.is_file()})
    def test_002_source_pins(self):
        self.assertEqual(m.source_check(),m.PIN066)
        self.assertEqual(sha256(BASE).hexdigest(),old.LUA064_SHA)
    def test_003_full_install_backups_and_rollback(self):
        saved={p.relative_to(self.game):p.read_bytes() for p in self.game.rglob('*') if p.is_file()}
        inst=self.install();self.assertEqual(inst['after']['status'],'INSTALLED_066_VERIFIED')
        self.assertEqual((self.game/m.LUA).read_bytes(),CANDIDATE)
        self.assertEqual((self.game/m.BCS).read_bytes(),self.bcs)
        self.assertEqual((self.game/old.STAGED_LUA).read_bytes(),BASE)
        self.assertEqual(self.fake.calls,['install'])
        backup=Path(inst['backup']);self.assertTrue((backup/'BACKUP_PROOF.json').exists())
        self.assertEqual((backup/m.LUA).read_bytes(),BASE)
        back=self.rollback();self.assertEqual(back['status'],'ROLLED_BACK_TO_064_VERIFIED')
        self.assertEqual(self.fake.calls,['install','rollback'])
        self.assertEqual((self.game/m.LUA).read_bytes(),BASE)
        self.assertEqual((self.game/'WeiDU.log').read_bytes(),saved[Path('WeiDU.log')])
    def test_004_status_066_no_writes(self):
        self.install();before={p.relative_to(self.game):p.read_bytes() for p in self.game.rglob('*') if p.is_file()}
        self.assertEqual(m.status066(self.game)['status'],'INSTALLED_066_VERIFIED')
        self.assertEqual(before,{p.relative_to(self.game):p.read_bytes() for p in self.game.rglob('*') if p.is_file()})
    def test_005_reject_weidu_other_last(self):
        with (self.game/'WeiDU.log').open('ab') as f:f.write(b'~OTHER\\SETUP.TP2~ #0 #0\n')
        with self.assertRaisesRegex(m.Stop,'BASE_064_NOT_VERIFIED'):self.install()
        self.assertFalse((self.game/'BGX66').exists())
    def test_006_reject_old_lua_hash(self):
        (self.game/m.LUA).write_bytes(b'DRIFT')
        with self.assertRaisesRegex(m.Stop,'BASE_064_NOT_VERIFIED'):self.install()
    def test_007_reject_bcs_drift(self):
        (self.game/m.BCS).write_bytes(b'DRIFT')
        with self.assertRaisesRegex(m.Stop,'BASE_064_NOT_VERIFIED'):self.install()
    def test_008_reject_064_stage_drift(self):
        (self.game/old.STAGED_LUA).write_bytes(b'DRIFT')
        with self.assertRaisesRegex(m.Stop,'BASE_064_NOT_VERIFIED'):self.install()
    def test_009_reject_game_running_before_stage(self):
        def busy():raise m.Stop('GAME_RUNNING')
        with self.assertRaisesRegex(m.Stop,'GAME_RUNNING'):self.install(guard=busy)
        self.assertFalse((self.game/'BGX66').exists())
    def test_010_reject_game_started_after_stage(self):
        count=[0]
        def guard():
            count[0]+=1
            if count[0]==3:raise m.Stop('GAME_STARTED')
        with self.assertRaisesRegex(m.Stop,'GAME_STARTED'):self.install(guard=guard)
        self.assertEqual(self.fake.calls,[])
        self.assertEqual((self.game/m.LUA).read_bytes(),BASE)
        self.assertTrue(list(self.backups.glob('PRE_INSTALL_*/BACKUP_PROOF.json')))
    def test_011_backup_failure_prevents_stage(self):
        def bad(*a):raise m.Stop('BACKUP_FAIL')
        with self.assertRaisesRegex(m.Stop,'BACKUP_FAIL'):self.install(backup=bad)
        self.assertFalse((self.game/'BGX66').exists())
    def test_012_stage_collision(self):
        (self.game/'BGX66').mkdir()
        with self.assertRaisesRegex(m.Stop,'066_STAGE_COLLISION'):self.install()
        self.assertEqual(self.fake.calls,[])
    def test_013_exe_collision(self):
        put(self.game,m.EXE,b'EXISTING')
        with self.assertRaisesRegex(m.Stop,'066_STAGE_COLLISION'):self.install()
    def test_014_weidu_error_no_auto_retry(self):
        failed=MockWeiDU(fail_install=True)
        with self.assertRaisesRegex(m.Stop,'DO_NOT_RETRY'):self.install(runner=failed)
        self.assertEqual(failed.calls,['install'])
        self.assertEqual((self.game/m.LUA).read_bytes(),BASE)
    def test_015_rollback_only_if_last(self):
        self.install()
        with (self.game/'WeiDU.log').open('ab') as f:f.write(b'~OTHER\\SETUP.TP2~ #0 #0\n')
        with self.assertRaisesRegex(m.Stop,'066_NOT_LAST_WEIDU'):self.rollback()
        self.assertEqual(self.fake.calls,['install'])
    def test_016_rollback_blocks_lua_drift(self):
        self.install();(self.game/m.LUA).write_bytes(b'DRIFT')
        with self.assertRaisesRegex(m.Stop,'066_LUA_MISMATCH'):self.rollback()
    def test_017_rollback_blocks_bcs_drift(self):
        self.install();(self.game/m.BCS).write_bytes(b'DRIFT')
        with self.assertRaisesRegex(m.Stop,'066_BCS_MISMATCH'):self.rollback()
    def test_018_rollback_needs_backup(self):
        self.install()
        def bad(*a):raise m.Stop('BACKUP_FAIL')
        with self.assertRaisesRegex(m.Stop,'BACKUP_FAIL'):self.rollback(backup=bad)
        self.assertEqual(self.fake.calls,['install'])
    def test_019_no_fake_success_on_rollback_error(self):
        self.install();failed=MockWeiDU(fail_uninstall=True)
        with self.assertRaisesRegex(m.Stop,'DO_NOT_RETRY'):self.rollback(runner=failed)
        self.assertEqual(failed.calls,['rollback'])
    def test_020_wrong_token_install(self):
        with patch.object(m,'install') as x:
            self.assertEqual(m.main(['install','--yes','--confirm','BAD','--game-root',str(self.game)]),2)
            x.assert_not_called()
    def test_021_wrong_token_rollback(self):
        with patch.object(m,'rollback') as x:
            self.assertEqual(m.main(['rollback','--yes','--confirm','BAD','--game-root',str(self.game)]),2)
            x.assert_not_called()
    def test_022_noncanonical_root_denied_even_with_token(self):
        with patch.object(m,'install') as x:
            self.assertEqual(m.main(['install','--yes','--confirm','INSTALL_BGXAI_066','--game-root',str(self.game)]),2)
            x.assert_not_called()
    def test_023_fixed_root_in_mock_requires_explicit_yes(self):
        with patch.object(m,'ROOT',self.game),patch.object(m,'install',return_value={'status':'MOCK'}) as x:
            self.assertEqual(m.main(['install','--game-root',str(self.game)]),2)
            self.assertEqual(m.main(['install','--yes','--confirm','INSTALL_BGXAI_066','--game-root',str(self.game)]),0)
            x.assert_called_once()
    def test_024_rollback_if_process_starts_last_minute(self):
        self.install();count=[0]
        def guard():
            count[0]+=1
            if count[0]==3:raise m.Stop('ACTIVE_PROCESS')
        with self.assertRaisesRegex(m.Stop,'ACTIVE_PROCESS'):self.rollback(guard=guard)
        self.assertEqual(self.fake.calls,['install'])
    def test_025_status_install_rollback_no_game_running_default_on_linux(self):
        if old.os.name!='nt':
            with self.assertRaisesRegex(old.Stop,'WINDOWS_REQUIRED'):m.guard()
    def test_026_source_change_denied(self):
        with patch.object(m,'build',side_effect=ValueError('MUTATED_SOURCE')):
            with self.assertRaisesRegex(ValueError,'MUTATED_SOURCE'):m.source_check()

if __name__=='__main__':unittest.main()
