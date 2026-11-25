import hashlib
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest import mock
ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('r30_preflight', ROOT/'BGXAI_R30_QUEUE_DEPLOY_PREFLIGHT_RO.py')
p = importlib.util.module_from_spec(spec);spec.loader.exec_module(p)

class Checks(unittest.TestCase):
    def source_fixture(self):
        return (b'local R27={}\n' +
                b'\n'.join(p.REQUIRED_OBSERVER_MARKERS) +
                b'\nreturn R27\n')

    def test_actual_source_sha_and_context_gate_are_pinned(self):
        candidate = ROOT.parent/'R27_R2_IDENTITY_REFRESH_20261124'/'BGXAI_R27_R2_REFRESH_SOURCE_ONLY.lua'
        data = candidate.read_bytes()
        self.assertEqual(len(data),44805)
        self.assertEqual(hashlib.sha256(data).hexdigest(),p.SOURCE_CANDIDATE_SHA)
        self.assertTrue(all(m in data for m in p.REQUIRED_OBSERVER_MARKERS))
        self.assertNotIn(b'P.initialized=start()', data)
        self.assertNotIn(b'EEex_Action_AddSpriteStartedActionListener(',data)

    def test_unverified_queue_only_candidate_cannot_pass_even_with_patched_sha(self):
        with TemporaryDirectory() as td:
            root=self.make(td)
            c=root.parent/'candidate_test.lua'
            c.write_bytes(b'local R27={}\nqueueSnapshotStable=qStable\nreturn R27\n')
            with mock.patch.object(p,'SOURCE_CANDIDATE_SHA',hashlib.sha256(c.read_bytes()).hexdigest()):
                result=self.patched(root,c)
            self.assertEqual(result['reason'],'CANDIDATE_V3_CONTEXT_CONTRACT_MISSING')
            c.unlink()

    def make(self, folder, last='~OTHER/SETUP-OTHER.TP2~ #0 #0 // another component', r27=True):
        root=Path(folder)
        for path, data in {
          'WeiDU.log': (( '~BGXR27/SETUP-BGXR27.TP2~ #0 #0 // original\n' if r27 else '') + last + '\n').encode(),
          'override/M_BGXR27.lua': b'placeholder P.initialized=start()\n',
          'EEex/copy/EEex_scripts/EEex_Action.lua': b'action',
          'EEex/copy/EEex_scripts/EEex_Sprite.lua': b'sprite',
          'enhanced-powergaming-scripts/lib/core_base.tph': b'eps'
        }.items():
            target=root/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        return root
    def patched(self, root, candidate=None):
        values={
            p.OLD_R27_SHA: hashlib.sha256((root/'override/M_BGXR27.lua').read_bytes()).hexdigest(),
            p.EEEX_ACTION_SHA: hashlib.sha256((root/'EEex/copy/EEex_scripts/EEex_Action.lua').read_bytes()).hexdigest(),
            p.EEEX_SPRITE_SHA: hashlib.sha256((root/'EEex/copy/EEex_scripts/EEex_Sprite.lua').read_bytes()).hexdigest(),
            p.EPS_CORE_SHA: hashlib.sha256((root/'enhanced-powergaming-scripts/lib/core_base.tph').read_bytes()).hexdigest()
        }
        with mock.patch.multiple(p, OLD_R27_SHA=values[p.OLD_R27_SHA], EEEX_ACTION_SHA=values[p.EEEX_ACTION_SHA], EEEX_SPRITE_SHA=values[p.EEEX_SPRITE_SHA], EPS_CORE_SHA=values[p.EPS_CORE_SHA]):
            return p.inspect(root,candidate)
    def test_one_r27_not_last_history_is_inspected_without_requiring_last(self):
        with TemporaryDirectory() as td:
            root=self.make(td)
            result=self.patched(root)
            self.assertEqual(result['weiduComponentCount'],2)
            self.assertEqual(result['r27ComponentPosition'],1)
            self.assertFalse(result['r27IsLast'])
            self.assertEqual(result['reason'],'CANDIDATE_PATH_REQUIRED_FOR_SOURCE_CHECK')
            self.assertFalse(result['typedInstallApproved'])
            self.assertFalse(result['queueBindingLiveVerified'])
    def test_installed_r27_must_be_exact(self):
        with TemporaryDirectory() as td:
            root=self.make(td)
            result=p.inspect(root)
            self.assertEqual(result['reason'],'INSTALLED_R27_RESOURCE_NOT_HISTORICAL_EXACT')
    def test_missing_r27_and_duplicate_r27_hold(self):
        with TemporaryDirectory() as td:
            root=self.make(td,r27=False)
            self.assertEqual(p.inspect(root)['reason'],'R27_COMPONENT_MISSING_OR_AMBIGUOUS')
            root=self.make(td)
            (root/'WeiDU.log').write_text('~BGXR27/SETUP-BGXR27.TP2~ #0 #0\n~BGXR27/SETUP-BGXR27.TP2~ #0 #0\n')
            self.assertEqual(p.inspect(root)['reason'],'R27_COMPONENT_MISSING_OR_AMBIGUOUS')
    def test_r30_component_already_installed_hold(self):
        with TemporaryDirectory() as td:
            root=self.make(td,last='~BGXQ30/SETUP-BGXQ30.TP2~ #0 #0')
            self.assertEqual(p.inspect(root)['reason'],'R30_COMPONENT_ALREADY_IN_HISTORY')
    def test_weidu_log_malformed_hold(self):
        with TemporaryDirectory() as td:
            root=self.make(td)
            (root/'WeiDU.log').write_text('~BGXR27/SETUP-BGXR27.TP2~ #0 #0\n~BROKEN\n')
            self.assertEqual(p.inspect(root)['reason'],'WEIDU_MALFORMED_COMPONENT')
    def test_missing_and_oversize_paths_hold(self):
        with TemporaryDirectory() as td:
            root=self.make(td)
            (root/'WeiDU.log').unlink()
            self.assertEqual(p.inspect(root)['reason'],'SOURCE_MISSING_OR_OVERSIZE:WeiDU.log')
    def test_symlink_is_refused(self):
        with TemporaryDirectory() as td:
            root=self.make(td)
            src=root/'EEex/copy/EEex_scripts/EEex_Sprite.lua'
            src.unlink()
            try: src.symlink_to('missing')
            except (OSError,NotImplementedError):self.skipTest('symlinks unavailable')
            with mock.patch.multiple(p,OLD_R27_SHA=hashlib.sha256((root/'override/M_BGXR27.lua').read_bytes()).hexdigest(), EEEX_ACTION_SHA=hashlib.sha256((root/'EEex/copy/EEex_scripts/EEex_Action.lua').read_bytes()).hexdigest()):
                result=p.inspect(root)
            self.assertEqual(result['reason'],'REPARSE_POINT_DENIED:EEex/copy/EEex_scripts/EEex_Sprite.lua')
    def test_exact_candidate_accepted_only_as_source(self):
        with TemporaryDirectory() as td:
            root=self.make(td)
            c=root.parent/'candidate_test.lua';c.write_bytes(self.source_fixture())
            with mock.patch.object(p,'SOURCE_CANDIDATE_SHA',hashlib.sha256(c.read_bytes()).hexdigest()):
                x=self.patched(root,c)
            self.assertTrue(x['candidateSourceVerified'])
            self.assertFalse(x['installationPerformed'])
            self.assertFalse(x['dispatchAuthorized'])
            c.unlink()
    def test_modified_candidate_and_dispatch_token_hold(self):
        with TemporaryDirectory() as td:
            root=self.make(td)
            c=root.parent/'candidate_test.lua';c.write_bytes(b'local R27={}\nSelectWeaponAbility(35,0)\nreturn R27\n')
            with mock.patch.object(p,'SOURCE_CANDIDATE_SHA',hashlib.sha256(c.read_bytes()).hexdigest()):
                x=self.patched(root,c)
            self.assertEqual(x['reason'],'CANDIDATE_CONTAINS_ENGINE_ACTION_OR_HOOK')
            c.unlink()
    def test_no_write_calls_in_production(self):
        src=(ROOT/'BGXAI_R30_QUEUE_DEPLOY_PREFLIGHT_RO.py').read_text()
        for needle in ('write_text(', 'write_bytes(', 'mkdir(', 'shutil.copy', 'subprocess.', 'os.system(', 'unlink('):
            # Rule checks callable expressions, not security strings in source.
            self.assertNotIn(needle,src)

if __name__ == '__main__': unittest.main()
