import hashlib
import tempfile
from pathlib import Path
import unittest
import zipfile
from bgvoice_windows_probe_r3 import known_windows_paths, probe_local_environment

class TestWindowsProbe(unittest.TestCase):
    def test_no_mutation_with_mock_pc_layout(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);updater=root/'BG_VOICE_UPDATE.cmd';updater.write_bytes(b'@echo off\n')
            python=root/'venv'/'Scripts'/'python.exe';python.parent.mkdir(parents=True);python.write_bytes(b'python-placeholder')
            pkg=root/'venv'/'Lib'/'site-packages'/'voxcpm';pkg.mkdir(parents=True);(pkg/'__init__.py').write_bytes(b'# mock only')
            model=root/'model';model.mkdir();(model/'model.safetensors').write_bytes(b'mockweight')
            report=root/'SEND_TO_CHATGPT_BG_VOICE_RU.zip'
            with zipfile.ZipFile(report,'w') as z:z.writestr('status.json',b'{}')
            originals=[(p,hashlib.sha256(p.read_bytes()).hexdigest()) for p in (updater,python,report,model/'model.safetensors')]
            r=probe_local_environment(updater_path=updater,model_root=model,python_venv=python,report_path=report)
            self.assertEqual(r['status'],'READONLY_EVIDENCE_COLLECTED_STILL_TTS_HOLD')
            self.assertEqual(r['style_control_supported'],'NOT_VERIFIED')
            self.assertEqual(r['voxcpm_package']['status'],'VOXCPM_SOURCE_INVENTORY_ONLY')
            self.assertEqual(len(r['voxcpm_package']['python_modules']),1)
            self.assertFalse(r['movie_tts_allowed'])
            self.assertEqual(r['model_inventory']['status'],'SIZE_INVENTORY_ONLY_NOT_SHA_VERIFIED')
            for p,sha in originals:self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),sha)
            self.assertEqual(sorted(p.name for p in root.iterdir()),sorted(['BG_VOICE_UPDATE.cmd','venv','model','SEND_TO_CHATGPT_BG_VOICE_RU.zip']))
    def test_missing_files_hold(self):
        with tempfile.TemporaryDirectory() as d:
            r=probe_local_environment(updater_path=Path(d)/'none',model_root=Path(d)/'absent',python_venv=Path(d)/'none',report_path=Path(d)/'none')
            self.assertEqual(r['status'],'READONLY_EVIDENCE_INCOMPLETE_HOLD')
            self.assertFalse(r['wrote_files'])
    def test_home_paths_do_not_assume_username(self):
        r=known_windows_paths(Path('/example/home'))
        self.assertIn('BG_VOICE_UPDATE.cmd',str(r['updater_path']))
        self.assertNotIn('Drevo',str(r['updater_path']))

if __name__=='__main__':unittest.main(verbosity=2)
