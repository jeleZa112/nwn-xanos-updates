import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import BGXW2_OBSERVER_GUARDED as m


class Guarded(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/'game';self.root.mkdir()
        (self.root/'override').mkdir()
        (self.root/'BGXWP').mkdir()
        (self.root/'BGXWP/PROOF.json').write_text(json.dumps({'source_sha256':m.R1_SHA}))
        (self.root/'chitin.key').write_bytes(b'game')
        (self.root/m.WEIDU).write_bytes(b'MZ'+b'READ_ONLY_MOCK_WEIDU')
        (self.root/'WeiDU.log').write_text('~BGXWP/SETUP-BGXWP.TP2~ #0 #0 // old live observer\n')
        self.sha={}
        for rel in m.BASELINE:
            p=self.root/rel;p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text('FAKE_BASELINE '+rel)
            self.sha[rel]=m.digest(p)
        for key,val in [('BASELINE',self.sha)]:
            v=mock.patch.object(m,key,val);v.start();self.addCleanup(v.stop)
        for fun in ('guard_root','check_processes'):
            v=mock.patch.object(m,fun);v.start();self.addCleanup(v.stop)
        v=mock.patch.dict(os.environ,{'USERPROFILE':str(Path(self.temp.name)/'home')});v.start();self.addCleanup(v.stop)
    def weidu(self,root,uninstall=False):
        if uninstall:
            (root/m.MODULE).unlink()
            (root/'WeiDU.log').write_text('~BGXWP/SETUP-BGXWP.TP2~ #0 #0 // old\n')
        else:
            (root/m.MODULE).write_bytes((root/m.STAGED).read_bytes())
            with (root/'WeiDU.log').open('a') as f:f.write('~BGXW2/SETUP-BGXW2.TP2~ #0 #0 // R2 passive\n')
    def test_source_pinned(self):m.check_source()
    def test_preflight_does_not_change_game(self):
        before={str(p.relative_to(self.root)):m.digest(p) for p in self.root.rglob('*') if p.is_file()}
        result=m.preflight(self.root)
        self.assertEqual(result['status'],'BGXW2_SOURCE_PREFLIGHT_PASS_NOT_INSTALLED')
        after={str(p.relative_to(self.root)):m.digest(p) for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before,after)
    def test_source_reject_sha_drift(self):
        with mock.patch.object(m,'SOURCE_SHA','0'*64),self.assertRaisesRegex(ValueError,'SOURCE_SHA'):
            m.check_source()
    def test_preflight_require_r1_last(self):
        (self.root/'WeiDU.log').write_text('~OTHER/SETUP-OTHER.TP2~ #0 #0 // changed\n')
        with self.assertRaisesRegex(ValueError,'MUST_BE_LAST'):m.preflight(self.root)
    def test_preflight_reject_collision(self):
        (self.root/'override'/'M_BGXW2.lua').write_text('not ours')
        with self.assertRaisesRegex(ValueError,'ALREADY_EXISTS'):m.preflight(self.root)
    def test_preflight_missing_r1_proof(self):
        (self.root/'BGXWP/PROOF.json').unlink()
        with self.assertRaisesRegex(ValueError,'BGXWP_PROOF'):m.preflight(self.root)
    def test_preflight_r1_baseline_drift(self):
        (self.root/'override/M_BGXWP.lua').write_text('drift')
        with self.assertRaisesRegex(ValueError,'BASELINE_SHA_DRIFT'):m.preflight(self.root)
    def test_preflight_game_running_stop(self):
        with mock.patch.object(m,'check_processes',side_effect=ValueError('GAME_OR_WEIDU_RUNNING')):
            with self.assertRaisesRegex(ValueError,'RUNNING'):m.preflight(self.root)
    def test_external_backup_sha(self):
        p=m.external_backup(self.root)
        checks=json.loads((p/'SHA256.json').read_text())
        self.assertIn('BGXWP/PROOF.json',checks)
        for path,sha in checks.items():self.assertEqual(m.digest(p/path),sha)
    def test_status_before_install(self):
        self.assertEqual(m.status(self.root)['status'],'BGXW2_NOT_INSTALLED')
    def test_install_and_last_only_rollback(self):
        originals={name:m.digest(self.root/name) for name in m.BASELINE}
        with mock.patch.object(m,'run_weidu',side_effect=self.weidu):
            result=m.install(self.root)
            self.assertEqual(result['status'],'BGXW2_PASSIVE_INSTALLED_AWAITING_RUNTIME_TEST')
            self.assertEqual(m.digest(self.root/m.MODULE),m.SOURCE_SHA)
            self.assertEqual(m.status(self.root)['status'],'BGXW2_PASSIVE_INSTALLED_SOURCE_EXACT')
            self.assertTrue(Path(result['external_backup']).is_dir())
            done=m.rollback(self.root)
            self.assertEqual(done['status'],'BGXW2_LAST_ONLY_ROLLBACK_R1_RESTORED')
        self.assertFalse((self.root/m.MODULE).exists())
        for name,sha in originals.items():self.assertEqual(m.digest(self.root/name),sha)
    def test_weidu_partial_failure_retains_proof_and_last_only_rollback(self):
        def partial(root,uninstall=False):
            self.weidu(root,uninstall=uninstall)
            if not uninstall:raise ValueError('INJECTED_WEIDU_POST_INSTALL_FAILURE')
        with mock.patch.object(m,'run_weidu',side_effect=partial):
            with self.assertRaisesRegex(ValueError,'INJECTED_WEIDU'):
                m.install(self.root)
        proof=self.root/m.PROOF
        self.assertTrue(proof.is_file())
        record=json.loads(proof.read_text())
        self.assertEqual(record['status'],'BGXW2_INSTALL_PENDING_WEIDU')
        self.assertTrue(Path(record['external_backup']).is_dir())
        with mock.patch.object(m,'run_weidu',side_effect=self.weidu):
            self.assertEqual(m.rollback(self.root)['status'],
                             'BGXW2_LAST_ONLY_ROLLBACK_R1_RESTORED')

    def test_rollback_wrong_last_never_calls_weidu(self):
        with mock.patch.object(m,'run_weidu',side_effect=self.weidu):m.install(self.root)
        with (self.root/'WeiDU.log').open('a') as f:f.write('~SOMETHING/SETUP-SOMETHING.TP2~ #0 #0 // later\n')
        with mock.patch.object(m,'run_weidu') as f, self.assertRaisesRegex(ValueError,'NOT_LAST'):
            m.rollback(self.root)
        f.assert_not_called()
    def test_rollback_backup_drift_stop(self):
        with mock.patch.object(m,'run_weidu',side_effect=self.weidu):out=m.install(self.root)
        (Path(out['external_backup'])/'chitin.key').write_text('CHANGED')
        with mock.patch.object(m,'run_weidu') as f,self.assertRaisesRegex(ValueError,'BACKUP_DRIFT'):
            m.rollback(self.root)
        f.assert_not_called()
    def test_typing_denied_no_install(self):
        with mock.patch('builtins.input',side_effect=['2','NOPE']),mock.patch.object(m,'install') as f:
            self.assertEqual(m.menu(self.root),2)
            f.assert_not_called()
    def test_typing_denied_no_rollback(self):
        with mock.patch('builtins.input',side_effect=['4','NOPE']),mock.patch.object(m,'rollback') as f:
            self.assertEqual(m.menu(self.root),2)
            f.assert_not_called()
    def test_do_not_ask_if_cancel(self):
        with mock.patch('builtins.input',return_value='0'),mock.patch.object(m,'install') as f:
            self.assertEqual(m.menu(self.root),0)
            f.assert_not_called()


if __name__=='__main__':unittest.main(verbosity=2)
