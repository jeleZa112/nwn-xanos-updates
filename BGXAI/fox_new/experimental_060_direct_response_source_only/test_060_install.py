"""Synthetic Windows-game install/rollback cycle, mocked WeiDU only."""
import unittest, tempfile, pathlib, sys, json, subprocess, hashlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import BGXAI60_INSTALL as i
import BGXAI60_BUILDER as b
from test_060 import base,candidate

class TestInstall(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=pathlib.Path(self.tmp.name)/'game';self.root.mkdir()
        self.old=base()
        self.orig_bcs=i.OLD_BCS_SHA;self.orig_lua=i.LUA_SHA
        i.OLD_BCS_SHA=i.sha(self.old)
        self.oldlua=b'ORIGINAL 056 LUA MOCK\n';i.LUA_SHA=i.sha(self.oldlua)
        self.write('WeiDU.log',b'~BGX56/SETUP-BGX56.TP2~ #0 #0 // original\n')
        self.write('chitin.key',b'K'*2000)
        self.write('InfinityLoader.exe',b'MZ'+b'I'*12000)
        self.write(i.WEIDU,b'MZ'+b'W'*100000)
        self.write(i.BCS_REL,self.old)
        self.write(i.LUA_REL,self.oldlua)
        for rel in i.BACKUP:
            p=self.root/rel
            if not p.exists():self.write(rel,b'original valid source\n')
        self.proposal,_=b.splice(self.old,candidate(),old_pin=i.sha(self.old))
        self.bd=pathlib.Path(self.tmp.name)/'backups'

    def tearDown(self):
        i.OLD_BCS_SHA=self.orig_bcs;i.LUA_SHA=self.orig_lua
        self.tmp.cleanup()

    def write(self,rel,content):
        p=self.root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(content)

    def build(self,root):
        self.assertEqual(root,self.root)
        return self.proposal,{'eps_unchanged':True,'patched_bcs_sha':i.sha(self.proposal)}

    def backup(self,r,s,tag):return i.make_backup(r,s,tag,parent=self.bd)

    def weidu(self,cmd,**kw):
        current=(self.root/'WeiDU.log').read_text()
        if '--force-install' in cmd:
            self.write(i.BCS_REL,(self.root/i.STAGED_BCS).read_bytes())
            self.write('WeiDU.log',(current+'~BGX60/SETUP-BGX60.TP2~ #0 #0 // installed\n').encode())
        elif '--force-uninstall' in cmd:
            self.write(i.BCS_REL,self.old)
            self.write('WeiDU.log',('\n'.join(current.splitlines()[:-1])+'\n').encode())
        else:raise AssertionError('unexpected WeiDU command')
        return subprocess.CompletedProcess(cmd,0,'WeiDU mock success','')

    def test_baseline_status_read_only(self):
        before=self.root.joinpath(i.BCS_REL).read_bytes()
        s=i.preflight(self.root,'056')
        self.assertTrue(i.LAST_056.search(s['last']))
        self.assertEqual(before,self.root.joinpath(i.BCS_REL).read_bytes())

    def test_install_rollback_and_lua_preserved(self):
        result=i.install(self.root,guard=lambda:None,backup=self.backup,runner=self.weidu,build=self.build)
        self.assertEqual(result['status'],'INSTALLED_060_EXPERIMENTAL')
        self.assertEqual((self.root/i.BCS_REL).read_bytes(),self.proposal)
        self.assertEqual((self.root/i.LUA_REL).read_bytes(),self.oldlua)
        self.assertTrue((pathlib.Path(result['backup'])/'BACKUP_PROOF.json').is_file())
        self.assertIn('COPY ~BGX60/staged/BDDEFAI.BCS~ ~override/BDDEFAI.BCS~',(self.root/i.TP2).read_text())
        back=i.rollback(self.root,guard=lambda:None,backup=self.backup,runner=self.weidu)
        self.assertEqual(back['status'],'ROLLED_BACK_TO_056')
        self.assertEqual((self.root/i.BCS_REL).read_bytes(),self.old)
        self.assertEqual((self.root/i.LUA_REL).read_bytes(),self.oldlua)

    def test_last_mod_not_056_blocks_before_stage(self):
        self.write('WeiDU.log',b'~OTHER/SETUP-OTHER.TP2~ #0 #0\n')
        with self.assertRaisesRegex(i.Stop,'WEIDU_LAST_UNEXPECTED'):
            i.install(self.root,guard=lambda:None,backup=self.backup,runner=self.weidu,build=self.build)
        self.assertFalse((self.root/i.STAGE).exists())

    def test_lua_drift_blocks(self):
        self.write(i.LUA_REL,b'changed!')
        with self.assertRaisesRegex(i.Stop,'LUA_056_DRIFT'):
            i.preflight(self.root,'056')

    def test_bcs_drift_blocks(self):
        self.write(i.BCS_REL,self.old+b'!')
        with self.assertRaisesRegex(i.Stop,'BCS_MISMATCH'):
            i.preflight(self.root,'056')

    def test_stage_collision_blocks(self):
        (self.root/i.STAGE).mkdir()
        with self.assertRaisesRegex(i.Stop,'STAGING_COLLISION'):
            i.preflight(self.root,'056')

    def test_unsafe_failed_proposal_never_weidu(self):
        def fail(_):raise ValueError('unexpected compiled action')
        with self.assertRaisesRegex(ValueError,'unexpected compiled'):
            i.install(self.root,guard=lambda:None,backup=self.backup,
                      runner=lambda *a,**k:self.fail('WeiDU called'),build=fail)
        self.assertEqual((self.root/i.BCS_REL).read_bytes(),self.old)
        self.assertFalse((self.root/i.STAGE).exists())

    def test_damaged_060_staging_blocks_rollback(self):
        i.install(self.root,guard=lambda:None,backup=self.backup,runner=self.weidu,build=self.build)
        (self.root/i.TP2).write_text('BAD')
        with self.assertRaisesRegex(i.Stop,'TP2_DRIFT'):
            i.rollback(self.root,guard=lambda:None,backup=self.backup,runner=self.weidu)

    def test_double_approval_required(self):
        self.assertIn('BGXAI_060_EXPERIMENTAL',pathlib.Path(i.__file__).read_text())
        self.assertNotIn('os.system(',pathlib.Path(i.__file__).read_text())

    def test_preserves_every_weidu_unchanged_on_compile_failure(self):
        snapshot={x:(self.root/x).read_bytes() for x in i.BACKUP}
        def fail(*a,**kw):raise ValueError('SYNTHETIC_COMPILE_FAILURE')
        with self.assertRaisesRegex(ValueError,'SYNTHETIC_COMPILE_FAILURE'):
            i.install(self.root,guard=lambda:None,backup=self.backup,runner=self.weidu,build=fail)
        self.assertEqual(snapshot,{x:(self.root/x).read_bytes() for x in i.BACKUP})

if __name__=='__main__':unittest.main(verbosity=2)
