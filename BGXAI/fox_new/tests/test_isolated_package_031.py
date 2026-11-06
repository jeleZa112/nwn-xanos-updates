import hashlib,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import build_isolated_package_031 as mod

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'GAME'
        self.root.mkdir()
        (self.root/'chitin.key').write_bytes(b'game')
        (self.root/'override').mkdir()
        (self.root/'override'/'BDDEFAI.BCS').write_bytes(b'actual installed EPS script fixture')
        (self.root/'enhanced-powergaming-scripts').mkdir()
        (self.root/'enhanced-powergaming-scripts'/'enhanced-powergaming-scripts.tp2').write_text('no EPS code fixture')
        local=self.root/'BGXAI_LOCAL_BUILD';local.mkdir()
        snap=local/'EPS_BASELINE_test';snap.mkdir()
        snapshot={'schema':27,'weidu_eps_components':3,
                  'source_files':[{'path':str(i)} for i in range(235)],
                  'binary_bcs_info':{'present_in_override':True,'sha256':mod.sha256(self.root/'override'/'BDDEFAI.BCS')}}
        (snap/'LOCAL_MANIFEST.json').write_text(json.dumps(snapshot))
        self.report={'schema':30,'mode':'OFFLINE_READ_ONLY_PREFLIGHT','status':'READY_FOR_ISOLATED_COMPILATION_REVIEW',
                     'source_files_checked':235,'changed_file_count':0,'eps_weidu_components':3,
                     'bddefai_override_state':'SAME_AS_SNAPSHOT','blockers':[],
                     'bgxai_installed':False,'game_modified':False,'uploaded':False,
                     'snapshot_id':'EPS_BASELINE_test'}
        self.save()
    def save(self):
        (self.root/'BGXAI_LOCAL_BUILD'/'BGXAI_030_COMPATIBILITY_REPORT.json').write_text(json.dumps(self.report))
    def build(self):return mod.build(self.root,enforce_path=False)
    def test_01_build_sources(self):
        out=self.build();self.assertEqual(len(out['files']),3)
        self.assertTrue((self.root/'BGXAI_LOCAL_BUILD'/mod.STAGE_NAME/'setup-BGX31.tp2').is_file())
    def test_02_no_game_modified(self):
        a=mod.sha256(self.root/'override'/'BDDEFAI.BCS');self.build()
        self.assertEqual(a,mod.sha256(self.root/'override'/'BDDEFAI.BCS'))
        self.assertFalse((self.root/'override'/'BGX31.BCS').exists())
    def test_03_no_eps_sources_copied(self):
        self.build();stage=self.root/'BGXAI_LOCAL_BUILD'/mod.STAGE_NAME
        self.assertEqual({str(p.relative_to(stage)) for p in stage.rglob('*') if p.is_file()},
                         {'setup-BGX31.tp2','BGX31/disabled_observer.baf','README_RU.txt','BGX31_STAGE_MANIFEST.json'})
    def test_04_refuse_report_blocked(self):
        self.report['status']='BLOCKED_REVIEW';self.save()
        with self.assertRaises(ValueError):self.build()
    def test_05_refuse_unverified_bcs(self):
        self.report['bddefai_override_state']='UNVERIFIED';self.save()
        with self.assertRaises(ValueError):self.build()
    def test_06_refuse_count_change(self):
        self.report['source_files_checked']=234;self.save()
        with self.assertRaises(ValueError):self.build()
    def test_07_refuse_weidu_changed(self):
        self.report['eps_weidu_components']=2;self.save()
        with self.assertRaises(ValueError):self.build()
    def test_08_refuse_modified_actual_bcs(self):
        (self.root/'override'/'BDDEFAI.BCS').write_bytes(b'CHANGED')
        with self.assertRaises(ValueError):self.build()
    def test_09_refuse_missing_eps(self):
        (self.root/'enhanced-powergaming-scripts'/'enhanced-powergaming-scripts.tp2').unlink()
        with self.assertRaises(ValueError):self.build()
    def test_10_refuse_old_game_path_default(self):
        with self.assertRaises(ValueError):mod.build(self.root)
    def test_11_refuse_existing_stage(self):
        self.build()
        with self.assertRaises(ValueError):self.build()
    def test_12_refuse_symlink_stage(self):
        (self.root/'BGXAI_LOCAL_BUILD'/mod.STAGE_NAME).symlink_to(self.root,target_is_directory=True)
        with self.assertRaises(ValueError):self.build()
    def test_13_refuse_unsafe_snapshot_id(self):
        self.report['snapshot_id']='../../old';self.save()
        with self.assertRaises(ValueError):self.build()
    def test_14_no_combat_actions(self):
        for s in ('Attack(', 'AttackOneRound(', 'RunAway(', 'MoveToPoint(', 'Spell(', 'BattleSong('):
            self.assertNotIn(s,mod.BAF)
    def test_15_only_clone_own_script(self):
        self.assertIn('COPY_EXISTING ~BDDEFAI.BCS~ ~override/BGX31.BCS~',mod.TP2)
        self.assertNotIn('EXTEND_BOTTOM ~BDDEFAI.BCS~',mod.TP2)
        self.assertIn('EXTEND_BOTTOM ~BGX31.BCS~',mod.TP2)
    def test_16_requires_local_optin(self):
        self.assertIn('Global("BGX31_OBS","LOCALS",1)',mod.BAF)
        self.assertNotIn('SetGlobal("BGX31_OBS"',mod.BAF)
    def test_17_no_installers_executed(self):
        o=self.build();self.assertIs(o['weiDU_executed'],False)
        self.assertIs(o['game_ai_replaced'],False)
    def test_18_blocker_rejected(self):
        self.report['blockers']=['unsafe'];self.save()
        with self.assertRaises(ValueError):self.build()

if __name__=='__main__':unittest.main(verbosity=2)