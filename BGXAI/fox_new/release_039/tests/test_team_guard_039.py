import importlib.util
import json
import os
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

BASE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('bgx39', BASE/'BGXAI39_INSTALL.py')
bgx39 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bgx39)
SRC = (BASE/'BGX39/team_guard_fallback.baf').read_text('ascii')
VALID38 = '~BGX38/SETUP-BGX38.TP2~ #0 #0 // bodyguard: 0.3.8-bodyguard-eps-in-place'
VALID39 = '~BGX39/SETUP-BGX39.TP2~ #0 #0 // team guard: 0.3.9'
EPS = '~ENHANCED-POWERGAMING-SCRIPTS/SETUP-ENHANCED-POWERGAMING-SCRIPTS.TP2~ #0 #0 // EPS'

class StaticGuards(unittest.TestCase):
    def test_blocks_10(self): self.assertEqual(len(re.findall(r'^IF$',SRC,re.M)),10)
    def test_guards_slots(self):
        for slot in (2,3,4,5,6):
            self.assertEqual(SRC.count(f'ProtectObject(Player{slot},6)'),2)
    def test_no_guard_player1(self): self.assertNotIn('ProtectObject(Player1',SRC)
    def test_no_self_guard(self):
        for slot in (2,3,4,5,6):
            self.assertEqual(SRC.count(f'!InPartySlot(Myself,{slot-1})'),2)
        self.assertEqual(SRC.count('!InPartySlot(Myself,0)'),10)
    def test_requires_old_opt_in_all(self): self.assertEqual(SRC.count('Global("BGX38_GUARD","LOCALS",1)'),10)
    def test_no_interrupt_actions(self):
        for bad in ('ClearActions','AttackOneRound','RunAway','ForceSpell','Spell(','UseItem','Equip','MoveToPoint','HotKey('):
            self.assertNotIn(bad,SRC)
    def test_queue_empty_all(self):self.assertEqual(SRC.count('ActionListEmpty()'),10)
    def test_cooldown_all(self):
        self.assertEqual(SRC.count('!GlobalTimerNotExpired("BGX39_TEAM_CD","LOCALS")'),10)
        self.assertEqual(SRC.count('SetGlobalTimer("BGX39_TEAM_CD","LOCALS",8)'),10)
    def test_visibility_party_and_range(self):
        for slot in (2,3,4,5,6):
            self.assertEqual(SRC.count(f'InParty(Player{slot})'),2)
            self.assertEqual(SRC.count(f'See(Player{slot})'),2)
            self.assertEqual(SRC.count(f'Range(Player{slot},10)'),2)
            self.assertEqual(SRC.count(f'See(NearestEnemyOf(Player{slot}))'),2)
            self.assertEqual(SRC.count(f'Range(NearestEnemyOf(Player{slot}),7)'),2)
    def test_priority_injured_first(self):
        a=SRC.split('IF\n')
        assert len(a)==11
        for b in a[1:6]:self.assertIn('HPPercentLT(',b)
        for b in a[6:]: self.assertNotIn('HPPercentLT(',b)
    def test_only_extension(self):
        s=(BASE/'setup-BGX39.tp2').read_text()
        self.assertEqual(s.count('EXTEND_BOTTOM ~BDDEFAI.BCS~'),1)
        self.assertNotIn('EXTEND_TOP',s)
        self.assertIn('REQUIRE_PREDICATE GAME_IS ~eet~',s)
    def test_manifest(self): self.assertEqual(bgx39.verify_source(BASE)['version'],'0.3.9')
    def test_no_foreign_binary(self):self.assertFalse((BASE/'setup-BGX39.exe').exists())

class Contract(unittest.TestCase):
    def test_version(self):self.assertEqual(bgx39.VERSION,'0.3.9')
    def test_038_dep(self): self.assertTrue(bgx39.base_installed([EPS,VALID38]))
    def test_no_038_dep(self):self.assertFalse(bgx39.base_installed([EPS]))
    def test_baseline_latest(self):self.assertTrue(bgx39.base_is_last([EPS,VALID38]))
    def test_other_mod_after(self):self.assertFalse(bgx39.base_is_last([EPS,VALID38,'~FOO/SETUP-FOO.TP2~ #0 #0']))
    def test_039_installed(self):self.assertTrue(bgx39.installed([EPS,VALID38,VALID39]))
    def test_039_last(self):self.assertTrue(bgx39.last_is_mod([EPS,VALID38,VALID39]))
    def test_039_not_last(self):self.assertFalse(bgx39.last_is_mod([EPS,VALID38,VALID39,'~OTHER/SETUP.TP2~ #0 #0']))
    def test_manifest_detects_tamper(self):
        with tempfile.TemporaryDirectory() as tmp:
            import shutil
            p=Path(tmp)
            (p/'BGX39').mkdir()
            for f in bgx39.SOURCE_FILES:
                d=p/f;d.parent.mkdir(exist_ok=True,parents=True);shutil.copy2(BASE/f,d)
            shutil.copy2(BASE/'SOURCE_MANIFEST.json',p/'SOURCE_MANIFEST.json')
            (p/'BGX39/team_guard_fallback.baf').write_bytes(b'CORRUPTED')
            with self.assertRaisesRegex(RuntimeError,'Package corrupted'):
                bgx39.verify_source(p)

class SafeMockInstaller(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'EET'
        for sub in ('override','lang/ru_ru'):(self.root/sub).mkdir(parents=True,exist_ok=True)
        for rel in bgx39.CRITICAL:(self.root/rel).write_bytes(b'P'+rel.encode())
        (self.root/bgx39.WEIDU).write_bytes(b'MZ'+b'0'*130000)
        self.log=self.root/'WeiDU.log'
        self.log.write_text('\n'.join([EPS,VALID38])+'\n',encoding='utf-8')
        self.profile=Path(self.tmp.name)/'HOME'
        self.profile.mkdir()
    def write(self, lines): self.log.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    def call(self):
        with patch.dict(os.environ,{'USERPROFILE':str(self.profile)}):
            return bgx39.run_install(self.root,BASE,real_root=False,guard=lambda:None,runner=self.fake_weiDU)
    def fake_weiDU(self,cmd,**kwargs):
        from types import SimpleNamespace
        if '--force-install' in cmd:
            b=self.root/'override/BDDEFAI.BCS'; b.write_bytes(b.read_bytes()+b'BGX39_COMPILED')
            with self.log.open('a',encoding='utf-8') as f:f.write(VALID39+'\n')
        elif '--force-uninstall' in cmd:
            b=self.root/'override/BDDEFAI.BCS'; b.write_bytes(b.read_bytes().replace(b'BGX39_COMPILED',b''))
            self.write([EPS,VALID38])
        return SimpleNamespace(returncode=0,stdout='MOCK WeiDU',stderr='')
    def test_base_missing_rejected_unchanged(self):
        self.write([EPS]);before=bgx39.snapshot(self.root)
        with self.assertRaisesRegex(RuntimeError,'BGX38 is not installed'):self.call()
        self.assertEqual(before,bgx39.snapshot(self.root))
    def test_previous_other_mod_rejected_unchanged(self):
        self.write([EPS,VALID38,'~OTHER/SETUP.TP2~ #0 #0']);before=bgx39.snapshot(self.root)
        with self.assertRaisesRegex(RuntimeError,'not last WeiDU'): self.call()
        self.assertEqual(before,bgx39.snapshot(self.root))
    def test_duplicate_rejected(self):
        self.write([EPS,VALID38,VALID39]);
        with self.assertRaisesRegex(RuntimeError,'already installed'):self.call()
    def test_file_collision_rejected(self):
        (self.root/'setup-BGX39.tp2').write_text('foreign')
        with self.assertRaisesRegex(RuntimeError,'will not overwrite'):self.call()
        self.assertEqual((self.root/'setup-BGX39.tp2').read_text(),'foreign')
    def test_install_and_rollback(self):
        result=self.call()
        self.assertEqual(result['status'],'INSTALLED')
        self.assertTrue(bgx39.installed(bgx39.read_log(self.root)))
        self.assertTrue((self.root/'setup-BGX39.tp2').exists())
        self.assertTrue((self.root/'setup-BGX39.exe').exists())
        backup=Path(result['backup']);self.assertTrue((backup/'status.json').exists())
        with patch.dict(os.environ,{'USERPROFILE':str(self.profile)}):
            r=bgx39.run_uninstall(self.root,BASE,real_root=False,guard=lambda:None,runner=self.fake_weiDU)
        self.assertEqual(r['status'],'UNINSTALLED_AND_RESTORED')
        self.assertFalse(bgx39.installed(bgx39.read_log(self.root)))
    def test_readonly_status_does_not_change_game(self):
        import contextlib,io
        before=bgx39.snapshot(self.root)
        previous=self.log.read_bytes()
        with contextlib.redirect_stdout(io.StringIO()) as out:
            bgx39.status(self.root,BASE,real_root=False)
        self.assertIn('BGX38 baseline installed: True',out.getvalue())
        self.assertIn('BGX39 installed: False',out.getvalue())
        self.assertEqual(before,bgx39.snapshot(self.root))
        self.assertEqual(previous,self.log.read_bytes())
    def test_preflight_cannot_kill_processes(self):
        source=(BASE/'BGXAI39_INSTALL.py').read_text()
        self.assertNotIn('Stop-Process',source)
        self.assertNotIn('taskkill',source.lower())
    def test_039_rollback_blocks_later_mod(self):
        self.call();self.write([EPS,VALID38,VALID39,'~OTHER/SETUP.TP2~ #0 #0'])
        with patch.dict(os.environ,{'USERPROFILE':str(self.profile)}):
            with self.assertRaisesRegex(RuntimeError,'AFTER BGX39'):
                bgx39.run_uninstall(self.root,BASE,real_root=False,guard=lambda:None,runner=self.fake_weiDU)
    def test_install_no_false_success_no_BCS(self):
        from types import SimpleNamespace
        def bad(cmd,**kwargs):
            with self.log.open('a',encoding='utf-8') as f:f.write(VALID39+'\n')
            return SimpleNamespace(returncode=0,stdout='',stderr='')
        with patch.dict(os.environ,{'USERPROFILE':str(self.profile)}):
            r=bgx39.run_install(self.root,BASE,real_root=False,guard=lambda:None,runner=bad)
        self.assertEqual(r['status'],'REVIEW_INSTALL')

if __name__=='__main__': unittest.main()
