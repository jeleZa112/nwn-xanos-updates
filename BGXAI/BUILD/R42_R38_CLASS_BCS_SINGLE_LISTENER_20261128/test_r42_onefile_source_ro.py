"""R42 existing-CMD source-only child: mock network / game, no live writes."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
spec = importlib.util.spec_from_file_location('r42_onefile', HERE/'BGXAI_R42_ONEFILE_SOURCE_RO.py')
R = importlib.util.module_from_spec(spec);spec.loader.exec_module(R)
builder = (REPO / R.BUILDER).read_bytes()
bridge = (REPO / R.BRIDGE).read_bytes()
live = (REPO / R.LIVE_SOURCE).read_bytes()
COMMIT = 'f' * 40


class FakeCompleted:
    returncode = 0
    stdout = json.dumps({
        'status': 'R42_COMPOSED_CLASS_BCS_SINGLE_LISTENER_NO_INSTALL',
        'onlyExistingActionStartedListener': True,
        'additionalActionStartedListeners': 0,
        'gameModified': False, 'nativeGameInstalled': False,
        'ordersSent': 0, 'installAuthorized': False,
        'classScriptResrefAtLiveJaganVerified': False,
        'composedCandidateSha256': 'c' * 64,
        'composedCandidateBytes': 92000,
    })


class T(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.game = Path(self.temp.name) / "game"
        (self.game / 'override').mkdir(parents=True)
        (self.game / 'chitin.key').write_bytes(b"fixture")
        (self.game / 'override' / 'M_BGXR27.lua').write_bytes(live)
        self.fetches = []
        self.runner_calls = []

    def fetch(self, commit, path):
        self.fetches.append(path)
        self.assertEqual(commit, COMMIT)
        return {R.BUILDER: builder, R.BRIDGE: bridge}[path]

    def runner(self, command, **kw):
        self.runner_calls.append((command, kw))
        self.assertTrue(str(command[1]).endswith("BGXAI_R42_REUSE_R38_CLASS_BCS_RO.py"))
        self.assertIn('stdin', kw)
        self.assertTrue(kw['capture_output'])
        self.assertTrue(Path(kw['cwd']).is_dir())
        return FakeCompleted()

    def outcome(self):
        return R.run(self.game, COMMIT, fetcher=self.fetch,
                     runner=self.runner, require_windows=False)

    def test_exact_pins(self):
        self.assertEqual(R.verified(R.BUILDER, builder), builder)
        self.assertEqual(R.verified(R.BRIDGE, bridge), bridge)
        self.assertEqual(len(live), R.LIVE_R38_LEN)
        self.assertEqual(hashlib.sha256(live).hexdigest(), R.LIVE_R38_SHA)

    def test_onefile_source_stages_and_discards_outside_game(self):
        before = (self.game/'override'/'M_BGXR27.lua').read_bytes()
        result = self.outcome()
        self.assertEqual(result['status'], 'R42_EXISTING_ONEFILE_SOURCE_READY_NO_INSTALL')
        self.assertEqual(self.fetches, [R.BUILDER, R.BRIDGE])
        self.assertFalse(result['gameModified'])
        self.assertFalse(result['installed'])
        self.assertFalse(result['classScriptResrefAtLiveJaganVerified'])
        self.assertEqual(result['ordersSent'], 0)
        self.assertEqual((self.game/'override'/'M_BGXR27.lua').read_bytes(), before)
        self.assertEqual(len(list(self.game.rglob('*'))), 3)

    def test_invalid_commit(self):
        for v in ('HEAD', 'main', 'f'*39, 'z'*40, '', 'f'*41):
            with self.subTest(v=v), self.assertRaises(R.Hold):
                R.pin(v)

    def test_missing_game(self):
        with self.assertRaisesRegex(R.Hold, 'HOLD_GAME_FOLDER'):
            R.run(self.game/'missing', COMMIT, fetcher=self.fetch,
                  runner=self.runner, require_windows=False)

    def test_missing_chitin(self):
        (self.game/'chitin.key').unlink()
        with self.assertRaisesRegex(R.Hold, 'HOLD_CHITIN_KEY'):
            self.outcome()

    def test_missing_installed_observer(self):
        (self.game/'override'/'M_BGXR27.lua').unlink()
        with self.assertRaisesRegex(R.Hold, 'HOLD_INSTALLED_R38_NOT_PRESENT'):
            self.outcome()

    def test_stale_installed_observer(self):
        (self.game/'override'/'M_BGXR27.lua').write_bytes(live[:-1]+b'x')
        with self.assertRaisesRegex(R.Hold, 'HOLD_R38_INSTALLED_SHA_CHANGED'):
            self.outcome()

    def test_wrong_installed_length(self):
        (self.game/'override'/'M_BGXR27.lua').write_bytes(b'drift')
        with self.assertRaisesRegex(R.Hold, 'HOLD_R38_INSTALLED_LENGTH_CHANGED'):
            self.outcome()

    def test_symlink_live_observer_rejected(self):
        f=self.game/'override'/'M_BGXR27.lua'
        f.unlink()
        target=Path(self.temp.name)/'original.lua'
        target.write_bytes(live)
        try:
            f.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        with self.assertRaisesRegex(R.Hold, 'HOLD_INSTALLED_R38_NOT_PRESENT'):
            self.outcome()

    def test_bad_fetch_checksum(self):
        def bad(c,p):
            return builder[:-1]+b'x' if p==R.BUILDER else bridge
        with self.assertRaisesRegex(R.Hold, 'HOLD_SOURCE_SHA_DRIFT'):
            R.run(self.game, COMMIT, fetcher=bad, runner=self.runner, require_windows=False)

    def test_missing_fetch_source(self):
        def bad(c,p):
            raise R.Hold("HOLD_PINNED_R42_DOWNLOAD")
        with self.assertRaisesRegex(R.Hold, 'HOLD_PINNED_R42_DOWNLOAD'):
            R.run(self.game, COMMIT, fetcher=bad, runner=self.runner, require_windows=False)

    def test_fetch_path_allowlist(self):
        with self.assertRaisesRegex(R.Hold, 'HOLD_FETCH_PATH_NOT_ALLOWLISTED'):
            R.fetch(COMMIT, '../../../bad')
        with self.assertRaisesRegex(R.Hold, 'HOLD_NOT_PINNED_R42_SOURCE'):
            R.verified('../../../bad', b'abc')

    def test_bad_inner_install_claim_refused(self):
        class Mutated(FakeCompleted):
            stdout = json.dumps({**json.loads(FakeCompleted.stdout),'installed':True,
                                 'gameModified':True})
        with self.assertRaisesRegex(R.Hold, 'HOLD_R42_INNER_REPORT_NOT_READONLY'):
            R.run(self.game, COMMIT, fetcher=self.fetch,
                  runner=lambda *a,**k:Mutated(), require_windows=False)

    def test_inner_wrong_session_status_refused(self):
        class Mutated(FakeCompleted):
            stdout = json.dumps({**json.loads(FakeCompleted.stdout),
                                 'classScriptResrefAtLiveJaganVerified':True})
        with self.assertRaisesRegex(R.Hold, 'HOLD_R42_INNER_REPORT_NOT_READONLY'):
            R.run(self.game, COMMIT, fetcher=self.fetch,
                  runner=lambda *a,**k:Mutated(), require_windows=False)

    def test_failed_inner_return_code(self):
        class Bad(FakeCompleted): returncode = 9
        with self.assertRaisesRegex(R.Hold, 'HOLD_R42_COMPOSER_REJECTED'):
            R.run(self.game, COMMIT, fetcher=self.fetch,
                  runner=lambda *a,**k:Bad(), require_windows=False)

    def test_no_game_cli_write_installer_or_r38_capture(self):
        s=(HERE/'BGXAI_R42_ONEFILE_SOURCE_RO.py').read_text(encoding='utf-8')
        for blocked in ("--install", "--rollback", "WeiDU.exe",
                        "SetGlobal(", "XEquipItem(",
                        "InfinityLoader.exe", "r38.capture("):
            self.assertNotIn(blocked,s)
        self.assertIn("TemporaryDirectory",s)

    def test_weidu_log_not_opened_or_modified(self):
        log=self.game/'WeiDU.log'
        log.write_text("test",encoding="ascii")
        before=log.read_bytes()
        self.outcome()
        self.assertEqual(log.read_bytes(),before)

if __name__ == '__main__':
    unittest.main()
