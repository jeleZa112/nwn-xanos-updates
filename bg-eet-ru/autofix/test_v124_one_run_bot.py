"""V126 one-click batch: V121 failure cannot suppress independent V122 live scan."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import zipfile
import unittest

UPDATER=Path(__file__).resolve().parents[1]/'onefile'/'BG_EET_RU_UPDATE.cmd'

class Batch(unittest.TestCase):
    def test_one_default_batch_collects_every_stage_after_exception(self):
        text=UPDATER.read_text('utf8')
        source=text.split('\n',1)[1]
        self.assertIn("def v126_dispatch(",source)
        self.assertIn("V126_SHA='3c079918170ecbea959e1148e1fc9c629d84c751bf0d89415166c98a26921703'",source)
        self.assertIn("mode={'2':'install','3':'rollback','4':'capture','5':'status'}.get(a)",source)
        self.assertIn('rc=v124_one_run(',source)
        ns={'__name__':'v124_ci_fixture','__file__':str(UPDATER)}
        exec(compile(source,str(UPDATER),'exec'),ns)
        with TemporaryDirectory(prefix='BG_EET_RU_V124_ONE_RUN_') as td:
            base=Path(td)
            game=base/'game'
            game.mkdir()
            path=base/'SEND_TO_CHATGPT_BG_EET_RU.zip'
            with zipfile.ZipFile(path,'w') as z:
                z.writestr('preserved-legacy-report.txt',b'UNMODIFIED')
            stages={
              'v85_run':'33_V85_COMBAT_FORMAT_GUARDED.json',
              'v102_run':'48_V102_ROLL_MODIFIER_LABELS.json',
              'v103_run':'49_V103_WEAPON_AMMO_SOURCE_AUDIT.json',
              'v104_run':'50_V104_EEEX_ATTACK_CONTEXT_EVIDENCE.json',
              'v105_run':'51_V105_WEAPON_OBSERVER_BRIDGE.json',
              'v106_run':'52_V106_WEAPON_CONSOLE_BRIDGE.json',
              'v107_run':'53_V107_CITEM_STATIC_ABI_PREFLIGHT.json',
              'v108_run':'54_V108_NATIVE_ITEM_RESREF_PILOT.json',
              'v111_run':'55_V111_ACTUAL_ITM_TLK_NAMES_READONLY.json',
              'v112_run':'56_V112_COMBAT_JOURNAL_CORRELATION_PREFLIGHT.json',
              'v116_run':'57_V116_DISPATCH_CALLEE_STATIC_READONLY.json',
              'full_audit_run':'58_FULL_SPECTRUM_STATIC_AUDIT.json',
              'v121_run':'60_V121_AUTOFIX_SOURCE_ONLY.json',
              'v122_run':'61_V122_LIVE_HIT_READONLY.json',
            }
            invoked=[]
            def mk(name,entry):
                def fake(g,z,*args):
                    invoked.append(name)
                    if name=='v104_run':raise RuntimeError('SYNTHETIC_SINGLE_STAGE_FAILURE')
                    if name=='v121_run':raise RuntimeError('SYNTHETIC_AUTOFIX_FAILURE')
                    report={'status':'SOURCE_TEST_PASS_GAMEPLAY_HOLD',
                            'game_files_written':0,'gameplay_verified':False}
                    ns['v116_zip'](g,z,report,entry=entry)
                    return 0
                return fake
            for name,entry in stages.items():ns[name]=mk(name,entry)
            self.assertEqual(ns['v124_one_run'](game,path,True),0)
            self.assertEqual(len(invoked),14)
            self.assertEqual(invoked[-1],'v122_run')
            self.assertEqual(len(list(game.iterdir())),0)
            with zipfile.ZipFile(path) as z:
                self.assertIsNone(z.testzip())
                self.assertEqual(z.read('preserved-legacy-report.txt'),b'UNMODIFIED')
                self.assertEqual(z.namelist().count(ns['V124_ENTRY']),1)
                report=json.loads(z.read(ns['V124_ENTRY']))
                self.assertEqual(report['stage_count'],14)
                self.assertEqual(report['updater_version'],ns['SELF_VERSION'])
                self.assertEqual(report['game_files_written'],0)
                self.assertFalse(report['native_hooks_installed'])
                self.assertFalse(report['gameplay_verified'])
                self.assertEqual(len(report['stages']),14)
                self.assertEqual(report['stages'][3]['status'],'HOLD')
                self.assertIn('SYNTHETIC_SINGLE_STAGE_FAILURE',report['stages'][3]['error'])
                self.assertEqual(report['stages'][12]['status'],'HOLD')
                self.assertIn('SYNTHETIC_AUTOFIX_FAILURE',report['stages'][12]['error'])
                self.assertEqual(report['stages'][13]['stage'],'memory')
                self.assertEqual(report['stages'][13]['source_status'],'SOURCE_TEST_PASS_GAMEPLAY_HOLD')
                self.assertIn('61_V122_LIVE_HIT_READONLY.json',z.namelist())
                self.assertEqual(report['status'],'COMPLETED_WITH_HOLDS')

if __name__=='__main__':
    unittest.main()
