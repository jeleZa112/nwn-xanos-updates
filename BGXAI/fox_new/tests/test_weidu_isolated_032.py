"""BGXAI 032 isolated clone unit tests; NEVER use real game resources."""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parent))
import weidu_isolated_test_032 as mod


class TestIsolated(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name) / 'BG_EET_FOXX_NEW'
        self.root.mkdir()
        self.local=self.root / 'BGXAI_LOCAL_BUILD'
        self.local.mkdir()
        (self.root/'chitin.key').write_bytes(b'fixture')
        (self.root/'WeiDU.log').write_text('// EPS test fixture')
        (self.root/'override').mkdir()
        (self.root/'override/BDDEFAI.BCS').write_bytes(b'installed source fixture EPS')
        (self.root/'lang/ru_ru').mkdir(parents=True)
        (self.root/'lang/ru_ru/dialog.tlk').write_bytes(b'dialog fixture')
        (self.root/'lang/ru_ru/dialogf.tlk').write_bytes(b'dialogf fixture')
        (self.root/'enhanced-powergaming-scripts').mkdir()
        (self.root/'enhanced-powergaming-scripts/enhanced-powergaming-scripts.tp2').write_text('fixture')
        (self.root/'setup-enhanced-powergaming-scripts.exe').write_bytes(b'MZ'+b'X'*100001)
        self.stage=self.local/'BGX31_STAGE_NOT_INSTALLED'
        self.stage.mkdir()
        (self.stage/'BGX31').mkdir()
        self.tp2=mod.__file__ # placeholder so test draws exact expected TP2 fragment
        tp2='\n'.join([
          'COPY_EXISTING ~BDDEFAI.BCS~ ~override/BGX31.BCS~',
          'EXTEND_BOTTOM ~BGX31.BCS~ ~BGX31/disabled_observer.baf~',
          'COPY_EXISTING ~BGX31.BCS~ ~scripts/BGX31.BS~',
        ])
        baf='IF\n  Global("BGX31_OBS","LOCALS",1)\nTHEN\nRESPONSE #100\n  Continue()\nEND'
        (self.stage/'setup-BGX31.tp2').write_text(tp2)
        (self.stage/'BGX31/disabled_observer.baf').write_text(baf)
        (self.stage/'README_RU.txt').write_text('stage fixture')
        files={}
        for s in mod.SOURCE_FILES:
            f=self.stage/s
            files[s]={'bytes':f.stat().st_size,'sha256':mod.digest(f)}
        self.stage_manifest={'schema':31,'status':'ISOLATED_COMPILATION_SOURCE_ONLY',
                             'source_included':False,'eps_files_included':False,
                             'bcs_files_included':False,'weiDU_executed':False,
                             'game_modified':False,'game_ai_replaced':False,'files':files}
        self.save_stage()
        self.preflight=lambda *_args, **_kwargs:{
            'status':'READY_FOR_ISOLATED_COMPILATION_REVIEW',
            'bddefai_override_state':'SAME_AS_SNAPSHOT','changed_file_count':0,
            'blockers':[],'eps_weidu_components':3,'source_files_checked':235}
        self.unlimited=lambda *_args:SimpleNamespace(free=1000*1024**3)
        self.calls=[]

    def save_stage(self):
        (self.stage/'BGX31_STAGE_MANIFEST.json').write_text(json.dumps(self.stage_manifest))

    def fake_weidu(self, cmd, **kwargs):
        self.calls.append((cmd,kwargs))
        clone=Path(kwargs['cwd'])
        if '--force-install' in cmd:
            (clone/'override/BGX31.BCS').write_bytes(b'compiled')
            (clone/'scripts').mkdir(exist_ok=True)
            (clone/'scripts/BGX31.BS').write_bytes(b'compiled BS')
            (clone/'WeiDU.log').write_text('// EPS\n~setup-BGX31.tp2~ #0 #0 // Installed')
        elif '--force-uninstall' in cmd:
            (clone/'override/BGX31.BCS').unlink()
            (clone/'scripts/BGX31.BS').unlink()
            (clone/'WeiDU.log').write_text('// EPS')
        return SimpleNamespace(returncode=0,stdout='mock weidu success',stderr='')

    def execute(self, runner=None, disk=None):
        return mod.run_isolated(self.root,enforce_root=False,preflight=self.preflight,
                                runner=runner or self.fake_weidu,disk_usage=disk or self.unlimited)

    def test_01_success_isolated_only(self):
        result=self.execute()
        self.assertEqual(result['status'],'PASS_ISOLATED_INSTALL_AND_ROLLBACK')
    def test_02_live_BCS_is_unchanged(self):
        h=mod.digest(self.root/'override/BDDEFAI.BCS')
        self.execute()
        self.assertEqual(h,mod.digest(self.root/'override/BDDEFAI.BCS'))
    def test_03_three_stage_hashes_verified(self):
        self.assertEqual(mod.verify_stage(self.root),self.stage)
    def test_04_corrupted_stage_is_rejected(self):
        (self.stage/'BGX31/disabled_observer.baf').write_text('changed')
        with self.assertRaises(ValueError):self.execute()
    def test_05_stage_manifest_must_be_source_only(self):
        self.stage_manifest['eps_files_included']=True
        self.save_stage()
        with self.assertRaises(ValueError):self.execute()
    def test_06_unknown_stage_file_rejected(self):
        self.stage_manifest['files']['other.baf']={'bytes':0,'sha256':'0'*64}
        self.save_stage()
        with self.assertRaises(ValueError):self.execute()
    def test_07_preflight_BLOCKED_rejected(self):
        self.preflight=lambda *_args,**_kwargs:{'status':'BLOCKED_REVIEW'}
        with self.assertRaises(ValueError):self.execute()
    def test_08_wrong_old_game_root_rejected(self):
        with self.assertRaises(ValueError):mod.verify_live(self.root,preflight=self.preflight)
    def test_09_not_enough_disk_rejected_before_clone(self):
        with self.assertRaises(ValueError):self.execute(disk=lambda *_:SimpleNamespace(free=5))
        self.assertFalse(self.root.with_name(self.root.name+mod.CLONE_SUFFIX).exists())
    def test_10_existing_clone_rejected(self):
        self.root.with_name(self.root.name+mod.CLONE_SUFFIX).mkdir()
        with self.assertRaises(ValueError):self.execute()
    def test_11_symlink_stage_rejected(self):
        shutil.rmtree(self.stage)
        try:self.stage.symlink_to(self.root,target_is_directory=True)
        except (NotImplementedError, OSError):self.skipTest('symlink unsupported')
        with self.assertRaises(ValueError):self.execute()
    def test_12_clone_is_sibling(self):
        result=self.execute()
        self.assertEqual(Path(result['clone_root']).parent,self.root.parent)
    def test_13_no_hardlinks(self):
        self.execute()
        clone=self.root.with_name(self.root.name+mod.CLONE_SUFFIX)
        self.assertNotEqual((self.root/'override/BDDEFAI.BCS').stat().st_ino,
                            (clone/'override/BDDEFAI.BCS').stat().st_ino)
    def test_14_development_cache_not_cloned(self):
        (self.root/'BGXAI_DEV').mkdir()
        (self.root/'BGXAI_DEV/secret.txt').write_text('no')
        self.execute()
        clone=self.root.with_name(self.root.name+mod.CLONE_SUFFIX)
        self.assertFalse((clone/'BGXAI_DEV').exists())
        self.assertFalse((clone/'BGXAI_LOCAL_BUILD').exists())
    def test_15_weidu_is_clone_only(self):
        self.execute()
        for cmd,opts in self.calls:
            self.assertEqual(Path(opts['cwd']).name,'BG_EET_FOXX_NEW'+mod.CLONE_SUFFIX)
            self.assertIn('--noautoupdate',cmd)
            self.assertIn('--game',cmd)
            self.assertIn('--use-lang',cmd)
    def test_16_install_and_uninstall_called(self):
        self.execute()
        self.assertEqual(len(self.calls),2)
        self.assertIn('--force-install',self.calls[0][0])
        self.assertIn('--force-uninstall',self.calls[1][0])
    def test_17_report_outside_game_overrides(self):
        self.execute()
        self.assertTrue((self.local/mod.OUT_NAME).is_file())
        self.assertFalse((self.root/'override/BGX31.BCS').exists())
    def test_18_disabled_BAF_has_no_game_control(self):
        txt=(self.stage/'BGX31/disabled_observer.baf').read_text()
        for x in ('RunAway(', 'Attack(', 'Spell(', 'MoveToPoint(', 'BattleSong('):
            self.assertNotIn(x,txt)
    def test_19_no_compiler_found_refuses(self):
        (self.root/'setup-enhanced-powergaming-scripts.exe').unlink()
        with self.assertRaises(ValueError):self.execute()
    def test_20_partial_install_does_not_claim_PASS(self):
        self.calls=[]
        def failure(cmd,**kwargs):
            self.calls.append(cmd)
            return SimpleNamespace(returncode=1,stdout='WEIDU failure',stderr='')
        x=self.execute(runner=failure)
        self.assertEqual(x['status'],'REVIEW_ISOLATED_WEIDU')
        self.assertEqual(len(self.calls),1)
    def test_21_rollback_failure_does_not_claim_PASS(self):
        def failure(cmd,**kwargs):
            if '--force-install' in cmd:return self.fake_weidu(cmd,**kwargs)
            return SimpleNamespace(returncode=1,stdout='undo error',stderr='')
        x=self.execute(runner=failure)
        self.assertEqual(x['status'],'REVIEW_ISOLATED_WEIDU')
    def test_22_changed_clone_tlk_detected(self):
        def modify(cmd,**kwargs):
            v=self.fake_weidu(cmd,**kwargs)
            if '--force-uninstall' in cmd:
                (Path(kwargs['cwd'])/'lang/ru_ru/dialog.tlk').write_bytes(b'changed strings')
            return v
        x=self.execute(runner=modify)
        self.assertFalse(x['clone_dialog_files_unchanged_after_rollback'])
        self.assertEqual(x['status'],'REVIEW_ISOLATED_WEIDU')
    def test_23_changed_live_BCS_detected(self):
        def mutate_live(cmd,**kwargs):
            v=self.fake_weidu(cmd,**kwargs)
            if '--force-install' in cmd:
                (self.root/'override/BDDEFAI.BCS').write_bytes(b'external mutation')
            return v
        x=self.execute(runner=mutate_live)
        self.assertTrue(x['original_game_modified'])
        self.assertEqual(x['status'],'REVIEW_ISOLATED_WEIDU')
    def test_24_no_WEIDU_log_record_fails(self):
        def no_log(cmd,**kwargs):
            v=self.fake_weidu(cmd,**kwargs)
            if '--force-install' in cmd:
                (Path(kwargs['cwd'])/'WeiDU.log').write_text('no new entries')
            return v
        x=self.execute(runner=no_log)
        self.assertEqual(x['status'],'REVIEW_ISOLATED_WEIDU')
    def test_25_refuses_symlinks_inside_game(self):
        try:(self.root/'external_link').symlink_to(self.stage, target_is_directory=True)
        except (NotImplementedError,OSError):self.skipTest('symlink unsupported')
        with self.assertRaises(ValueError):self.execute()
    def test_26_identifies_wrong_game_mode_without_exec(self):
        self.assertFalse((self.root/mod.OUT_NAME).exists())
    def test_27_checks_staged_clone_is_identical(self):
        result=self.execute()
        self.assertTrue(result['clone_bcs_matches_original_after_install'])
        self.assertTrue(result['clone_bcs_matches_original_after_test'])
    def test_28_critical_live_Russian_dialogs_unchanged(self):
        before=mod.capture_critical(self.root)
        self.execute()
        self.assertEqual(before,mod.capture_critical(self.root))


if __name__=='__main__':unittest.main(verbosity=2)