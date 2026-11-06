import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

P=Path(__file__).resolve().parent
# Lightweight fake 032 with precisely the functions that 035 calls.
class FakeOld:
    CLONE_SUFFIX='__BGX32_TEST'
    @staticmethod
    def junction_or_link(p):return p.is_symlink()
    @staticmethod
    def verify_live(root,**kwargs):return root
    @staticmethod
    def verify_stage(root):return root/'BGXAI_LOCAL_BUILD/BGX31_STAGE_NOT_INSTALLED'
    @staticmethod
    def choose_weidu(root):return root/'weidu.exe'

sys.modules['weidu_isolated_test_032']=FakeOld
spec=importlib.util.spec_from_file_location('bgx35',P/'weidu_compile_only_035.py')
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class TestCompileOnly(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'newFoxx';self.root.mkdir()
        self.local=self.root/'BGXAI_LOCAL_BUILD';self.local.mkdir()
        self.stage=self.local/'BGX31_STAGE_NOT_INSTALLED/BGX31';self.stage.mkdir(parents=True)
        (self.stage/'disabled_observer.baf').write_text('IF\n Global("BGX31_OBS","LOCALS",1)\nTHEN\n RESPONSE #100\n Continue()\nEND')
        for name in m.CRITICAL:
            path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(('INERT '+name).encode())
        (self.root/'weidu.exe').write_bytes(b'MZ'+b'X'*200000)
        self.calls=[]
    def fake_runner(self,cmd,**kw):
        self.calls.append((cmd,kw))
        Path(cmd[cmd.index('--out')+1]).write_bytes(b'BCS fake')
        class R:returncode=0;stdout='compiled';stderr=''
        return R()
    def execute(self,**extra):
        return m.compile_only(self.root,enforce_root=False,
            validate_live=lambda root,**kw:root,choose_exe=FakeOld.choose_weidu,
            runner=self.fake_runner,tag='TEST1',**extra)
    def test_01_default_command_no_action(self):self.assertEqual(m.main([]),0)
    def test_02_compiles_only_to_local_scratch(self):
        r=self.execute();self.assertEqual(r['status'],'COMPILE_ONLY_OK')
        self.assertTrue((self.local/'BGX35_COMPILE_ONLY_TEST1/BGX31_OBSERVER.BCS').is_file())
    def test_03_no_original_files_modified(self):
        before=m.snapshots(self.root);self.execute();self.assertEqual(before,m.snapshots(self.root))
    def test_04_compiler_no_tp2_commands(self):
        r=self.execute();args=self.calls[0][0]
        self.assertTrue(m.command_is_safe(args,self.root,Path(r['target'])))
        self.assertFalse(any(x in ' '.join(args) for x in ['--force-install','--force-uninstall']))
    def test_05_out_side_local(self):
        r=self.execute();c=self.calls[0][0]
        for x in ('--out','--tlkout','--ftlkout','--log'):
            self.assertEqual(Path(c[c.index(x)+1]).parent,Path(r['target']))
    def test_06_sandbox_tlk_copy(self):
        r=self.execute();self.assertEqual((Path(r['target'])/'input_dialog.tlk').read_bytes(),(self.root/'lang/ru_ru/dialog.tlk').read_bytes())
    def test_07_no_eps_or_bcs_source_copied(self):
        r=self.execute();self.assertEqual({x.name for x in Path(r['target']).iterdir()},
            {'input_dialog.tlk','input_dialogf.tlk','BGX31_DISABLED_OBSERVER.BAF','BGX31_OBSERVER.BCS','BGX35_COMPILE_REPORT.json'})
    def test_08_no_weidu_log_change(self):
        before=(self.root/'WeiDU.log').read_bytes();self.execute();self.assertEqual(before,(self.root/'WeiDU.log').read_bytes())
    def test_09_reports_not_game_ai(self):
        r=self.execute();self.assertFalse(r['bgxai_installed']);self.assertFalse(r['full_game_clone_created'])
    def test_10_refuses_existing_scratch(self):
        self.execute();
        with self.assertRaises(ValueError):self.execute()
    def test_11_refuses_outside_root(self):
        with self.assertRaises(ValueError):m.compile_only(self.root)
    def test_12_refuses_missing_local(self):
        self.local.rename(self.root/'localMoved')
        with self.assertRaises(ValueError):self.execute()
    def test_13_rejects_force_install(self):
        s=self.local/'BGX35_COMPILE_ONLY_X';a=m.command(self.root/'weidu.exe',self.root,s)
        a.append('--force-install');self.assertFalse(m.command_is_safe(a,self.root,s))
    def test_14_rejects_output_into_game(self):
        s=self.local/'BGX35_COMPILE_ONLY_X';a=m.command(self.root/'weidu.exe',self.root,s)
        a[a.index('--out')+1]=str(self.root/'override/HACK.BCS')
        self.assertFalse(m.command_is_safe(a,self.root,s))
    def test_15_failed_weidu_not_success(self):
        def fail(cmd,**kw):
            class R:returncode=1;stdout='err';stderr='bad'
            return R()
        r=m.compile_only(self.root,enforce_root=False,runner=fail,tag='TEST2')
        self.assertEqual(r['status'],'COMPILER_REVIEW');self.assertFalse(r['compile_verified'])
    def test_16_detect_live_hash_mutation(self):
        def mutate(cmd,**kw):
            (self.root/'WeiDU.log').write_text('MUTATED')
            return self.fake_runner(cmd,**kw)
        r=m.compile_only(self.root,enforce_root=False,runner=mutate,tag='TEST3')
        self.assertEqual(r['status'],'STOP_LIVE_HASH_CHANGED')
    def test_17_no_new_game_clone(self):
        self.execute();self.assertFalse((self.root.parent/(self.root.name+'__BGX32_TEST')).exists())
    def test_18_command_has_no_auto_tp2(self):
        a=m.command(self.root/'weidu.exe',self.root,self.local/'BGX35_COMPILE_ONLY_X')
        self.assertIn('--no-auto-tp2',a);self.assertIn('--noautoupdate',a)
    def test_19_compiled_bcs_report_metadata_only(self):
        r=self.execute();d=json.loads((Path(r['target'])/'BGX35_COMPILE_REPORT.json').read_text());self.assertTrue(d['compile_verified']);self.assertFalse(d['eps_files_uploaded'])

if __name__=='__main__':unittest.main(verbosity=2)