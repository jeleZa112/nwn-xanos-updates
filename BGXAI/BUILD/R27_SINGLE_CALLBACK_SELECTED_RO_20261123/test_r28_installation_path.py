from pathlib import Path
import hashlib
import importlib.util
import tempfile
import unittest
from unittest import mock

D=Path(__file__).parent
spec=importlib.util.spec_from_file_location('bgx_r27',D/'BGXAI_R27_GUARDED.py')
r27=importlib.util.module_from_spec(spec);spec.loader.exec_module(r27)

class InstallerTests(unittest.TestCase):
    def test_menu_path(self):
        s=(D/'BGXAI_R27_GUARDED.py').read_text()
        self.assertIn("'6':'native'",s)
        self.assertIn('result = native_items_from_r27(root)',s)
        self.assertIn("--game",s)
    def test_native_module_hash(self):
        p=D/'BGXAI_R28_NATIVE_FROM_R27_RO.py'
        self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),r27.R28_NATIVE_BRIDGE_SHA)
    def test_requires_installed_proof(self):
        with mock.patch.object(r27,'status',return_value={'status':'R27_NOT_INSTALLED'}):
            with self.assertRaisesRegex(ValueError,'NOT_INSTALLED'):
                r27.native_items_from_r27(Path('/game'))
    def test_module_tamper_fails(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'BGXAI_R28_NATIVE_FROM_R27_RO.py'
            p.write_text('print("bad")')
            class DummyFile:
                def resolve(self): return p.parent/'BGXAI_R27_GUARDED.py'
            with mock.patch.object(r27,'status',return_value={'status':'R27_PASSIVE_INSTALLED_AWAITING_RUNTIME_TEST'}), \
                 mock.patch.object(r27,'__file__',str(p.parent/'BGXAI_R27_GUARDED.py')):
                with self.assertRaisesRegex(ValueError,'SHA_MISMATCH'):
                    r27.native_items_from_r27(Path('/game'))
    def test_no_game_dispatch_in_bridge(self):
        t=(D/'BGXAI_R28_NATIVE_FROM_R27_RO.py').read_text()
        for command in ('SelectWeaponAbility(', 'ClearActions(', 'ActionOverride(',
                        'EEex_Action_QueueScriptFileResponseOnAIBase(',
                        'EEex_Resource_Demand(', 'SetGlobal('):
            self.assertNotIn(command,t)

if __name__=='__main__':unittest.main()
