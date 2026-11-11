"""061 guarded installer integration tests; WeiDU simulated, no actual game modification."""
import unittest, tempfile, pathlib, sys, hashlib, subprocess
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import BGXAI61_INSTALL as i
import BGXAI61_BUILDER as b
from test_061 import base,candidate

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=pathlib.Path(self.tmp.name)/'game';self.root.mkdir()
        self.old=base();self.oldlua=(b'PREAMBLE\n'+i.OLD_TTL+b'\n'+i.OLD_MAX+b'\nPOSTAMBLE\n')
        self.orig_bcs=i.OLD_BCS_SHA;self.orig_lua=i.OLD_LUA_SHA
        i.OLD_BCS_SHA=i.sha(self.old)
        i.OLD_LUA_SHA=i.sha(self.oldlua)
        self.write('WeiDU.log',b'~BGX60/SETUP-BGX60.TP2~ #0 #0 // existing\n')
        self.write('chitin.key',b'K'*2000)
        self.write('InfinityLoader.exe',b'MZ'+b'I'*12000)
        self.write(i.WEIDU,b'MZ'+b'W'*100000)
        self.write(i.BCS_REL,self.old)
        self.write(i.LUA_REL,self.oldlua)
        for rel in i.BACKUP:
            if not (self.root/rel).exists():self.write(rel,b'valid file\n')
        self.new,self.proof=b.splice(self.old,candidate(),old_pin=i.sha(self.old))
        self.newlua=i.patch_lua(self.oldlua,source_pin=i.sha(self.oldlua))
        self.proof['patched_lua_sha']=i.sha(self.newlua)
        self.backupdir=pathlib.Path(self.tmp.name)/'external_backups'
    def tearDown(self):
        i.OLD_BCS_SHA=self.orig_bcs;i.OLD_LUA_SHA=self.orig_lua
        self.tmp.cleanup()
    def write(self,rel,raw):
        f=self.root/rel;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(raw)
    def build(self,root):
        self.assertEqual(root,self.root)
        return self.new,self.newlua,self.proof
    def backup(self,root,proof,tag):return i.make_backup(root,proof,tag,parent=self.backupdir)
    def weidu(self,cmd,**kwargs):
        self.assertEqual(kwargs['stdin'],subprocess.DEVNULL)
        text=(self.root/'WeiDU.log').read_text()
        if '--force-install' in cmd:
            self.write(i.BCS_REL,(self.root/i.STAGED_BCS).read_bytes())
            self.write(i.LUA_REL,(self.root/i.STAGED_LUA).read_bytes())
            text+='~BGX61/SETUP-BGX61.TP2~ #0 #0 // installed\n'
        elif '--force-uninstall' in cmd:
            self.write(i.BCS_REL,self.old);self.write(i.LUA_REL,self.oldlua)
            text='\n'.join(text.splitlines()[:-1])+'\n'
        else:raise AssertionError('unexpected WeiDU')
        self.write('WeiDU.log',text.encode())
        return subprocess.CompletedProcess(cmd,0,'WeiDU mock success','')
    def test_preflight_status_read_only(self):
        before={x:(self.root/x).read_bytes() for x in i.BACKUP}
        res=i.preflight(self.root,'060')
        self.assertTrue(i.LAST_060.search(res['last']))
        self.assertEqual(before,{x:(self.root/x).read_bytes() for x in i.BACKUP})
    def test_patched_lua_changes_only_two_literals(self):
        newer=i.patch_lua(self.oldlua)
        self.assertIn(i.NEW_TTL,newer);self.assertIn(i.NEW_MAX,newer)
        self.assertNotIn(i.OLD_TTL,newer);self.assertNotIn(i.OLD_MAX,newer)
        self.assertEqual(newer,self.oldlua.replace(i.OLD_TTL,i.NEW_TTL).replace(i.OLD_MAX,i.NEW_MAX))
    def test_lua_patch_blocks_unknown_sha(self):
        with self.assertRaisesRegex(i.Stop,'SHA_MISMATCH'):i.patch_lua(self.oldlua+b'X')
    def test_lua_patch_blocks_missing_marker(self):
        bad=self.oldlua.replace(i.OLD_MAX,b'MISSING')
        with self.assertRaisesRegex(i.Stop,'PATCH_SOURCE_UNEXPECTED'):i.patch_lua(bad,source_pin=i.sha(bad))
    def test_install_and_rollback_cycle(self):
        installed=i.install(self.root,guard=lambda:None,backup=self.backup,runner=self.weidu,build=self.build)
        self.assertEqual(installed['status'],'INSTALLED_061_EXPERIMENTAL')
        self.assertEqual((self.root/i.BCS_REL).read_bytes(),self.new)
        self.assertEqual((self.root/i.LUA_REL).read_bytes(),self.newlua)
        self.assertTrue((pathlib.Path(installed['backup'])/'BACKUP_PROOF.json').is_file())
        self.assertIn('COPY ~BGX61/staged/M_BX43.lua~ ~override/M_BX43.lua~',(self.root/i.TP2).read_text())
        restored=i.rollback(self.root,guard=lambda:None,backup=self.backup,runner=self.weidu)
        self.assertEqual(restored['status'],'ROLLED_BACK_TO_060')
        self.assertEqual((self.root/i.BCS_REL).read_bytes(),self.old)
        self.assertEqual((self.root/i.LUA_REL).read_bytes(),self.oldlua)
    def test_block_wrong_weidu_last(self):
        self.write('WeiDU.log',b'~SOMEONE/OTHER.TP2~ #0 #0\n')
        with self.assertRaisesRegex(i.Stop,'WEIDU_LAST_UNEXPECTED'):i.preflight(self.root)
    def test_block_modified_060_bcs(self):
        self.write(i.BCS_REL,self.old+b'X')
        with self.assertRaisesRegex(i.Stop,'BCS_MISMATCH'):i.preflight(self.root)
    def test_block_modified_060_lua(self):
        self.write(i.LUA_REL,self.oldlua+b'X')
        with self.assertRaisesRegex(i.Stop,'LUA_MISMATCH'):i.preflight(self.root)
    def test_prevent_stage_collision(self):
        (self.root/i.STAGE).mkdir()
        with self.assertRaisesRegex(i.Stop,'STAGING_COLLISION'):i.preflight(self.root)
    def test_reject_weidu_failed_install(self):
        def bad(cmd,**kwargs):return subprocess.CompletedProcess(cmd,1,'fail','')
        with self.assertRaisesRegex(i.Stop,'WEIDU_INSTALL_FAILED_DO_NOT_RETRY'):
            i.install(self.root,guard=lambda:None,backup=self.backup,runner=bad,build=self.build)
        self.assertEqual((self.root/i.BCS_REL).read_bytes(),self.old)
        self.assertEqual((self.root/i.LUA_REL).read_bytes(),self.oldlua)
    def test_modified_stage_blocks_rollback(self):
        i.install(self.root,guard=lambda:None,backup=self.backup,runner=self.weidu,build=self.build)
        (self.root/i.TP2).write_text('BAD')
        with self.assertRaisesRegex(i.Stop,'TP2_DRIFT'):i.rollback(self.root,guard=lambda:None,backup=self.backup,runner=self.weidu)
    def test_compile_failure_no_game_mutation(self):
        snapshot={r:(self.root/r).read_bytes() for r in i.BACKUP}
        with self.assertRaisesRegex(ValueError,'COMPILE_FAILED'):
            i.install(self.root,guard=lambda:None,backup=self.backup,runner=self.weidu,build=lambda _:(_ for _ in ()).throw(ValueError('COMPILE_FAILED')))
        self.assertEqual(snapshot,{r:(self.root/r).read_bytes() for r in i.BACKUP})
    def test_requires_double_approval_in_cli(self):
        src=pathlib.Path(i.__file__).read_text()
        self.assertIn("a.confirm!='BGXAI_061_EXPERIMENTAL'",src)
        self.assertIn('EXPLICIT_--yes_AND_',src)
    def test_bcs_and_lua_verified_after_install(self):
        x=i.install(self.root,guard=lambda:None,backup=self.backup,runner=self.weidu,build=self.build)
        self.assertEqual(x['target_bcs_sha256'],i.sha(self.new))
        self.assertEqual(x['target_lua_sha256'],i.sha(self.newlua))
        self.assertTrue(i.LAST_061.search(i.last_mod(self.root)))
    def test_symlink_block(self):
        root=self.root
        f=root/i.LUA_REL;f.unlink();f.symlink_to(root/i.BCS_REL)
        with self.assertRaisesRegex(i.Stop,'REPARSE_BLOCKED'):i.preflight(root)
    def test_rollback_only_last(self):
        i.install(self.root,guard=lambda:None,backup=self.backup,runner=self.weidu,build=self.build)
        self.write('WeiDU.log',(self.root/'WeiDU.log').read_bytes()+b'~ANOTHER/SETUP-X.TP2~ #0 #0\n')
        with self.assertRaisesRegex(i.Stop,'WEIDU_LAST_UNEXPECTED'):i.rollback(self.root,guard=lambda:None,backup=self.backup,runner=self.weidu)

if __name__=='__main__':unittest.main(verbosity=2)
