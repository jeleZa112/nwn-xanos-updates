"""R24 source-only integrity tests; no game access or actions."""
from pathlib import Path
import hashlib
import json
import re
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2] if HERE.parts[-3] == 'BGXAI' else HERE.parent
# From BGXAI/BUILD/R24_.../, parents[1] is the repo root.
REPO = HERE.parents[2]
SOURCES = REPO / 'BGXAI' / 'patchsets' / 'ranged_fighter_guarded_20261119'
MODULE = HERE / 'BGXAI_R24_SESSION_ADVISORY_BRIDGE_RO.lua'
TEST = HERE / 'test_r24_session_bridge.lua'
MANIFEST = HERE / 'SHA256_MANIFEST.json'

def blobsha(p: Path) -> str:
    data = p.read_bytes()
    return hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest()

class R24ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lua = MODULE.read_text('utf-8')
        cls.test = TEST.read_text('utf-8')
        cls.meta = json.loads(MANIFEST.read_text('utf-8'))

    def test_01_manifest_reuse_real_dependencies(self):
        self.assertEqual(len(self.meta['pinnedGitBlobs']), 5)
        for name, sha in self.meta['pinnedGitBlobs'].items():
            self.assertEqual(blobsha(SOURCES / name), sha, name)

    def test_02_self_files_hash(self):
        for name, expected in self.meta['files'].items():
            self.assertEqual(hashlib.sha256((HERE / name).read_bytes()).hexdigest(), expected)

    def test_03_explicit_offline_mode(self):
        self.assertIn("input.mode~='OFFLINE_SYNTHETIC_FIXTURE'", self.lua)
        self.assertIn('REAL_SOURCE_ALT_APR_EFFECTS_EPS_AND_LAUNCHER_UNVERIFIED', self.lua)

    def test_04_inert_results_for_all_paths(self):
        for part in ['readOnly=true','sourceOnly=true','installed=false',
                     'executable=false','dispatchAuthorized=false',
                     'weaponSwitchAuthorized=false','ordersSent=0',
                     'localsWritten=0','actionQueueCleared=false',
                     'currentActionPreserved=true']:
            self.assertGreaterEqual(self.lua.count(part), 2, part)

    def test_05_zero_game_calls(self):
        for bad in ('ClearActions(', 'SelectWeaponAbility(', 'ActionOverride(',
                    'SetGlobal(', 'Attack(', 'Stop(', 'EEex_PtrToUD(',
                    'EEex_UDToPtr(', 'getLauncher(', 'getAbility(',
                    'os.execute(', 'io.open(', 'WriteFile(', 'table.insert('):
            self.assertNotIn(bad,self.lua,bad)

    def test_06_existing_noninterrupt_reused(self):
        self.assertIn('deps.noninterrupt.step',self.lua)
        self.assertIn('previous=prior.plan',self.lua)

    def test_07_existing_v3_v4_v5_bridge_reused(self):
        for term in ('deps.currentStats','deps.apr','deps.effects.choose',
                     'deps.priority.preview','bridge.choose('):
            self.assertIn(term,self.lua)

    def test_08_session_is_separate_from_frame_snapshot(self):
        self.assertRegex(self.lua,r'prior.sessionToken~=input.sessionToken')
        self.assertRegex(self.lua,r'valid_id\(s.frame.snapshotId\)')
        self.assertNotIn('prior.snapshotId~=s.frame.snapshotId',self.lua)

    def test_09_untrusted_scheduler_response_rejected(self):
        self.assertIn('SCHEDULER_READ_ONLY_INVARIANT_VIOLATED',self.lua)
        self.assertIn('res.ordersSent~=0',self.lua)
        self.assertIn('res.actionQueueCleared~=false',self.lua)

    def test_10_real_and_synthetic_paths_tested(self):
        self.assertIn('real R17/R20 reports cannot grant scorer',self.test)
        self.assertIn('existing V5 APR path also produces advisory only',self.test)
        self.assertIn('changed session drops old pending',self.test)
        self.assertIn('EPS and manual orders remain uninterrupted',self.test)

    def test_11_manifest_policy_hard_off(self):
        for k in ('gameModified','installAuthorized','dispatchAuthorized','weaponSwitchAuthorized'):
            self.assertIs(self.meta[k],False,k)
        self.assertIs(self.meta['sourceOnly'],True)

    def test_12_never_edit_original_modules(self):
        self.assertIn('source_folder',self.test)
        self.assertIn('../../patchsets/ranged_fighter_guarded_20261119/',self.test)
        self.assertTrue(self.lua.rstrip().endswith('return M'))

if __name__ == '__main__': unittest.main()
