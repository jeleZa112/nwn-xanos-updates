"""V136 existing onefile + one ZIP integration. Stubs native API; NOT gameplay proof."""
from __future__ import annotations
import io, json, shutil, tempfile, unittest, zipfile
from pathlib import Path
from unittest import mock

ROOT=Path(__file__).resolve().parents[1] if 'autofix' in str(Path(__file__).parent) else None
if ROOT is None:
    raise RuntimeError('INSTALL_TEST_IN_BG_EET_RU_AUTOFIX_FOR_CI')
UPDATER=ROOT/'onefile'/'BG_EET_RU_UPDATE.cmd'
SOURCES=ROOT/'native-correlation'

class TestOneFile136(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='V136_ONEFILE_RO_')
        self.addCleanup(self.tmp.cleanup)
        home=Path(self.tmp.name)
        self.game=home/'game'; self.game.mkdir()
        self.work=home/'outside_game';self.work.mkdir()
        code=UPDATER.read_text('utf8').split('\n',1)[1]
        self.ns={'__name__':'v136_test_non_main','__file__':str(UPDATER)}
        exec(compile(code,str(UPDATER),'exec'),self.ns)
        self.assertIn(self.ns['SELF_VERSION'],(136,140,142,144,146,151,153))
        self.live_label=('v151_ro' if self.ns['SELF_VERSION'] in (151,153) else ('v146_ro' if self.ns['SELF_VERSION']==146 else ('v144_ro' if self.ns['SELF_VERSION']==144 else ('v142_ro' if self.ns['SELF_VERSION']==142 else ('v140_ro' if self.ns['SELF_VERSION']==140 else 'v136_ro')))))
        self.live_entry=('72_V151_EXACT_UI_MENU_RO.json' if self.ns['SELF_VERSION'] in (151,153) else ('71_V146_FOLLOWUP_SOURCE_RO.json' if self.ns['SELF_VERSION']==146 else ('70_V144_DOWNSTREAM_SOURCE_RO.json' if self.ns['SELF_VERSION']==144 else ('69_V142_MESSAGE_DELIVERY_RO.json' if self.ns['SELF_VERSION']==142 else ('68_V140_EXACT_CALLEE_RO.json' if self.ns['SELF_VERSION']==140 else '67_V136_LIVE_JIT_TARGET_RO.json')))))
        self.ns['WORKDIR']=self.work
        cache=self.work/'.BG_EET_RU_AUTOFIX_CACHE';cache.mkdir()
        for version, filename in ((133,'v133_live_hit_inventory_ro.py'),((151 if self.ns['SELF_VERSION']==153 else self.ns['SELF_VERSION']),'v151_ro.py' if self.ns['SELF_VERSION'] in (151,153) else ('v146_ro.py' if self.ns['SELF_VERSION']==146 else ('v144_ro.py' if self.ns['SELF_VERSION']==144 else ('v142_ro.py' if self.ns['SELF_VERSION']==142 else ('v140_ro.py' if self.ns['SELF_VERSION']==140 else 'v136_jit_provenance_ro.py')))))):
            src=SOURCES/filename
            dst=cache/(f'V{version}_RO.py')
            dst.write_bytes(src.read_bytes().replace(b'\r\n',b'\n'))
            self.assertEqual(self.ns['sha_path'](dst),self.ns[f'V{version}_PIN'])
        self.zip=self.work/self.ns['REPORT_NAME']
        with zipfile.ZipFile(self.zip,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('00_OLDER_REPORT.json','{"old":true}')
            z.writestr('66_V133_LIVE_HIT_INVENTORY.json','{"historical":true}')
            if self.ns['SELF_VERSION']>=140:
                z.writestr('67_V136_LIVE_JIT_TARGET_RO.json','{"historical_v136":true}')
            if self.ns['SELF_VERSION']>=142:
                z.writestr('68_V140_EXACT_CALLEE_RO.json','{"historical_v140":true}')
            if self.ns['SELF_VERSION']>=144:
                z.writestr('69_V142_MESSAGE_DELIVERY_RO.json','{"historical_v142":true}')
            if self.ns['SELF_VERSION']>=146:
                z.writestr('70_V144_DOWNSTREAM_SOURCE_RO.json','{"historical_v144":true}')
            if self.ns['SELF_VERSION']==151:
                z.writestr('71_V146_FOLLOWUP_SOURCE_RO.json','{"historical_v146":true}')
        self.called=[]
        def fake_exec(code,namespace):
            label=namespace['__name__']
            self.called.append(label)
            namespace['selftest_windows']=lambda:{'status':'MOCK_NOT_REAL_WINDOWS'}
            namespace['run_game']=lambda *args:{
                'schema':'BG_EET_RU_MOCK_ROUTING_ONLY',
                'status':('V136_LIVE_PAIR_SITES_AND_EXECUTABLE_TARGET_OBSERVED_OWNER_HOLD'
                          if label in ('v136_ro','v140_ro','v142_ro','v144_ro','v146_ro','v151_ro') else 'V133_MOCK_STATUS'),
                'firstcall_owner_verified':False,
                'native_hooks_installed':False,'game_files_written':0,
                'gameplay_verified':False}
        self.ns['exec']=fake_exec
    def read(self,key):
        with zipfile.ZipFile(self.zip) as z:return json.loads(z.read(key))
    def test_v136_menu_routing_preserves_old_zip_and_game(self):
        rc=self.ns['v133_audit'](self.game,self.zip,True)
        self.assertEqual(rc,0)
        self.assertEqual(self.called,['v133_ro',self.live_label])
        entry=self.read(self.live_entry)
        self.assertEqual(entry['status'],'V136_LIVE_PAIR_SITES_AND_EXECUTABLE_TARGET_OBSERVED_OWNER_HOLD')
        self.assertFalse(entry['native_hook_install_allowed'])
        self.assertFalse(entry['gameplay_verified'])
        self.assertEqual(entry['game_files_written'],0)
        self.assertEqual(self.read('66_V133_LIVE_HIT_INVENTORY.json'),{'historical':True})
        self.assertEqual(self.read('00_OLDER_REPORT.json'),{'old':True})
        if self.ns['SELF_VERSION']>=140:
            self.assertEqual(self.read('67_V136_LIVE_JIT_TARGET_RO.json'),{'historical_v136':True})
        if self.ns['SELF_VERSION']>=142:
            self.assertEqual(self.read('68_V140_EXACT_CALLEE_RO.json'),{'historical_v140':True})
        if self.ns['SELF_VERSION']>=144:
            self.assertEqual(self.read('69_V142_MESSAGE_DELIVERY_RO.json'),{'historical_v142':True})
        if self.ns['SELF_VERSION']>=146:
            self.assertEqual(self.read('70_V144_DOWNSTREAM_SOURCE_RO.json'),{'historical_v144':True})
        if self.ns['SELF_VERSION']==151:
            self.assertEqual(self.read('71_V146_FOLLOWUP_SOURCE_RO.json'),{'historical_v146':True})
        self.assertEqual(list(self.game.iterdir()),[])
        with zipfile.ZipFile(self.zip) as z:
            self.assertIsNone(z.testzip())
            self.assertEqual(len(z.namelist()),len(set(z.namelist())))
            self.assertEqual(z.namelist().count(self.live_entry),1)
    def test_v133_original_option_still_works(self):
        rc=self.ns['v133_audit'](self.game,self.zip)
        self.assertEqual(rc,0)
        self.assertEqual(self.called,['v133_ro'])
        self.assertEqual(self.read('66_V133_LIVE_HIT_INVENTORY.json')['status'],'V133_MOCK_STATUS')
        with zipfile.ZipFile(self.zip) as z:self.assertNotIn(self.live_entry,z.namelist())
    def test_bad_remote_source_sha_fails_closed_and_reports(self):
        (self.work/'.BG_EET_RU_AUTOFIX_CACHE'/f"V{151 if self.ns['SELF_VERSION']==153 else self.ns['SELF_VERSION']}_RO.py").write_text('corrupted',encoding='utf8')
        with mock.patch.object(self.ns['urllib'].request,'urlopen',return_value=io.BytesIO(b'unverified')):
            rc=self.ns['v133_audit'](self.game,self.zip,True)
        self.assertEqual(rc,0) # Still emits HOLD into the existing ZIP.
        entry=self.read(self.live_entry)
        self.assertEqual(entry['status'],'V136_RUNTIME_OWNER_AND_GAMEPLAY_HOLD')
        self.assertIn('SHA_HOLD',entry['hold_reason'])
        self.assertEqual(entry['game_files_written'],0)
        self.assertEqual(self.read('66_V133_LIVE_HIT_INVENTORY.json'),{'historical':True})

if __name__=='__main__':unittest.main(verbosity=2)
