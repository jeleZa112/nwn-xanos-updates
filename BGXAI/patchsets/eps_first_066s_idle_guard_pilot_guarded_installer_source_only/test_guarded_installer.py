"""Offline tests: synthetic game only. Never calls real WeiDU or Windows game."""
from __future__ import annotations
import hashlib
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main
from types import SimpleNamespace
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('pilot', HERE/'BGXAI_IDLE_GUARD_INSTALL_SOURCE_ONLY.py')
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)

def write(root, name, data):
    f = root / name
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_bytes(data)
    return f

class TestInstaller(TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / 'BG_EET_FOXX_NEW'
        self.root.mkdir()
        self.baseline_log = b'~BGX66S/SETUP-BGX66S.TP2~ #0 #0 ~BGXAI 066S~\n'
        write(self.root,'WeiDU.log',self.baseline_log)
        write(self.root,pilot.BCS, b'BINARY_BCS_TEST')
        write(self.root,pilot.LUA,(HERE/pilot.ORIGINAL_SOURCE).read_bytes())
        write(self.root,'BGX66S/setup-BGX66S.tp2',b'BEGIN ~066S~\n')
        write(self.root,'chitin.key',b'CHITIN_TEST')
        write(self.root,'weidu.conf',b'language=ru_RU\n')
        write(self.root,'lang/ru_RU/dialog.tlk',b'DIALOG TLK mock')
        write(self.root,'lang/ru_RU/dialogf.tlk',b'DIALOGF TLK mock')
        write(self.root,pilot.WEIDU,b'MZ'+b'x'*120001)
        # Only the BCS hash is synthetic; all other source and backup gates are real.
        self.bcs_orig = pilot.BCS_SHA
        pilot.BCS_SHA = hashlib.sha256((self.root/pilot.BCS).read_bytes()).hexdigest()
        self.addCleanup(lambda: setattr(pilot, 'BCS_SHA', self.bcs_orig))
        self.guards = 0
        self.calls = []

    def guard(self):
        self.guards += 1

    def backup(self, root, before, label):
        return pilot.make_backup(root,before,label,parent=self.base/'outside_game_backups')

    def runner(self, command, **kwargs):
        self.calls.append(command)
        if '--force-install' in command:
            self.assertEqual((self.root/pilot.TP2).read_text(encoding='utf-8'),pilot.TP2_TEXT)
            write(self.root,pilot.LUA,(self.root/pilot.STAGE).read_bytes())
            write(self.root,'WeiDU.log', self.baseline_log +
                  b'~BGXIDLE/SETUP-BGXIDLE.TP2~ #0 #0 ~BGXAI 066S idle guardian preference, reversible test~\n')
        elif '--force-uninstall' in command:
            write(self.root,pilot.LUA,(HERE/pilot.ORIGINAL_SOURCE).read_bytes())
            write(self.root,'WeiDU.log',self.baseline_log)
        else:
            raise AssertionError('WEIDU_UNEXPECTED_COMMAND')
        return SimpleNamespace(returncode=0,stdout='SUCCESS',stderr='')

    def test_baseline_status_only_no_writes(self):
        original={str(f.relative_to(self.root)):f.read_bytes() for f in self.root.rglob('*') if f.is_file()}
        s=pilot.verify_baseline(self.root)
        self.assertEqual(s['state'],'BASELINE_066S_VERIFIED')
        self.assertEqual(original,{str(f.relative_to(self.root)):f.read_bytes() for f in self.root.rglob('*') if f.is_file()})
        self.assertEqual(self.calls,[])

    def test_readonly_preflight_no_writes(self):
        original={str(f.relative_to(self.root)):f.read_bytes() for f in self.root.rglob('*') if f.is_file()}
        s=pilot.preflight(self.root)
        self.assertEqual(s['status'],'READ_ONLY_PREFLIGHT_PASS')
        self.assertFalse(s['authorized_to_install'])
        self.assertEqual(original,{str(f.relative_to(self.root)):f.read_bytes() for f in self.root.rglob('*') if f.is_file()})

    def test_last_mod_unrelated_rejected(self):
        (self.root/'WeiDU.log').write_bytes(self.baseline_log+b'~SOMEOTHER/SETUP-MOD.TP2~ #0 #0 ~Other~\n')
        with self.assertRaisesRegex(pilot.Stop,'WEIDU_LAST_MUST_BE_066S'):
            pilot.verify_baseline(self.root)

    def test_source_sha_rejected(self):
        saved=pilot.CANDIDATE_SHA
        pilot.CANDIDATE_SHA='0'*64
        try:
            with self.assertRaisesRegex(pilot.Stop,'SOURCE_HASH_MISMATCH'):
                pilot.preflight(self.root)
        finally:
            pilot.CANDIDATE_SHA=saved

    def test_tampered_lua_rejected(self):
        (self.root/pilot.LUA).write_bytes(b'TAMPERED')
        with self.assertRaisesRegex(pilot.Stop,'LIVE_HASH_MISMATCH'):
            pilot.preflight(self.root)

    def test_tampered_bcs_rejected(self):
        (self.root/pilot.BCS).write_bytes(b'TAMPERED_BCS')
        with self.assertRaisesRegex(pilot.Stop,'LIVE_HASH_MISMATCH'):
            pilot.preflight(self.root)

    def test_missing_dialogf_preflight_rejected(self):
        (self.root/'lang/ru_RU/dialogf.tlk').unlink()
        with self.assertRaisesRegex(pilot.Stop,'FILE_MISSING'):
            pilot.preflight(self.root)

    def test_stage_collision_rejected(self):
        (self.root/'BGXIDLE').mkdir()
        with self.assertRaisesRegex(pilot.Stop,'PILOT_STAGE_ALREADY_PRESENT'):
            pilot.preflight(self.root)

    def test_install_then_uninstall_restores_exact_baseline(self):
        before={p:(self.root/p).read_bytes() for p in pilot.BACKUP}
        r=pilot.install(self.root,guard=self.guard,backup=self.backup,runner=self.runner)
        self.assertEqual(r['status'],'PILOT_INSTALLED_VERIFIED')
        self.assertEqual(self.guards,3)
        self.assertEqual(pilot.verify_pilot(self.root)['lua_sha256'],pilot.CANDIDATE_SHA)
        self.assertEqual((self.root/pilot.BCS).read_bytes(),before[pilot.BCS])
        self.assertTrue((Path(r['backup'])/'BACKUP_PROOF.json').exists())
        with self.assertRaisesRegex(pilot.Stop,'WEIDU_LAST_MUST_BE_066S'):
            pilot.preflight(self.root)  # already installed
        rb=pilot.rollback(self.root,guard=self.guard,backup=self.backup,runner=self.runner)
        self.assertEqual(rb['status'],'RETURNED_TO_066S_VERIFIED')
        self.assertEqual({p:(self.root/p).read_bytes() for p in pilot.BACKUP},before)
        self.assertEqual(pilot.verify_baseline(self.root,stage_allowed=True)['state'],'BASELINE_066S_VERIFIED')
        self.assertEqual(len(self.calls),2)
        self.assertIn('--force-install',self.calls[0])
        self.assertIn('--force-uninstall',self.calls[1])

    def test_weidu_non_target_mutation_detected_after_install(self):
        def faulty_runner(command, **kwargs):
            result=self.runner(command, **kwargs)
            write(self.root, 'lang/ru_RU/dialog.tlk', b'CORRUPTED BY MOCK')
            return result
        with self.assertRaisesRegex(pilot.Stop, 'UNEXPECTED_NON_TARGET_FILE_MUTATION'):
            pilot.install(self.root, guard=self.guard, backup=self.backup, runner=faulty_runner)
        self.assertTrue(list((self.base/'outside_game_backups').glob('PRE_INSTALL_*')))

    def test_weidu_non_target_mutation_detected_after_rollback(self):
        pilot.install(self.root, guard=self.guard, backup=self.backup, runner=self.runner)
        def faulty_rollback(command, **kwargs):
            result=self.runner(command, **kwargs)
            write(self.root, 'chitin.key', b'CORRUPTED BY MOCK')
            return result
        with self.assertRaisesRegex(pilot.Stop, 'UNEXPECTED_NON_TARGET_FILE_MUTATION'):
            pilot.rollback(self.root,guard=self.guard,backup=self.backup,runner=faulty_rollback)

    def test_weidu_failure_stops_no_false_success(self):
        def bad_runner(command,**kwargs):
            return SimpleNamespace(returncode=1,stdout='FATAL ERROR: mock failure',stderr='')
        with self.assertRaisesRegex(pilot.Stop,'WEIDU_FAILED_NO_AUTORETRY'):
            pilot.install(self.root,guard=self.guard,backup=self.backup,runner=bad_runner)
        self.assertEqual((self.root/pilot.LUA).read_bytes(),(HERE/pilot.ORIGINAL_SOURCE).read_bytes())
        self.assertFalse((self.root/'WeiDU.log').read_bytes()!=self.baseline_log)
        self.assertTrue(list((self.base/'outside_game_backups').glob('PRE_INSTALL_*')))

    def test_backup_verification_rejects_tamper(self):
        state=pilot.verify_baseline(self.root)
        backup=self.backup(self.root,state,'PRE_TEST')
        (backup/pilot.LUA).write_bytes(b'BROKEN')
        with self.assertRaisesRegex(pilot.Stop,'BACKUP_PROOF_MISMATCH'):
            pilot.check_backup(backup,self.root)

    def test_refuse_unsupported_live_mutation_on_linux_or_wrong_root(self):
        self.assertEqual(pilot.main(['install','--game-root',str(self.root),
            '--yes','--confirm',pilot.APPROVE_INSTALL]),2)
        self.assertEqual(pilot.main(['install','--game-root',str(self.root)]),2)
        self.assertEqual(pilot.main(['rollback','--game-root',str(self.root)]),2)
        self.assertEqual(len(self.calls),0)

    def test_process_guard_linux_fails_closed(self):
        if sys.platform != 'win32':
            with self.assertRaisesRegex(pilot.Stop,'WINDOWS_REQUIRED'):
                pilot.process_guard()

if __name__=='__main__':
    main(verbosity=2)
