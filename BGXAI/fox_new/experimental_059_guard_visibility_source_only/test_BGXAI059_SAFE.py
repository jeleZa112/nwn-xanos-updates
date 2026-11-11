"""All tests are synthetic; never access or change the real EET installation."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("installer", HERE / "BGXAI059_SAFE.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)

MOCK_NEW_SOURCE = b'''P.version = "0.3.25-059-GUARD-VISIBILITY-SOURCE"
-- BGX59Eligibility.choose(victim, options)
-- EEex_UDEqual(guardArea,victimArea)
-- guardian, "[ANYONE]", E.maxVisualDistancePixels
function B.prepare(advisory) end
function P.onWeaponHit(context) return false -- CRITICAL
end
'''

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)/'BG_TEST'
        self.root.mkdir()
        self.ext = Path(self.tmp.name)/'EXTERNAL'
        def write(rel,data):
            p=self.root/rel
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes(data)
        write('WeiDU.log',b'~BGX49/setup-BGX49.tp2~ #0 #0 // 049\n~BGX56/setup-BGX56.tp2~ #0 #0 // 056\n')
        write('chitin.key',b'KEY!'+b'Z'*1050)
        write('weidu.conf',b'lang=ru_RU\n')
        write('lang/ru_RU/dialog.tlk',b'TLK0'*100)
        write('lang/ru_RU/dialogf.tlk',b'TLKF'*100)
        write('InfinityLoader.exe',b'MZ'+b'I'*12000)
        write(installer.WEIDU_EXE,b'MZ'+b'E'*110000)
        self.bcs=b'BCSx'+b'Z'*1000
        self.lua=b'base_056_lua_sample'
        write(installer.BCS,self.bcs)
        write(installer.LUA,self.lua)
        self.patches=[patch.object(installer,'SOURCE_BLOB',installer.git_blob(MOCK_NEW_SOURCE)),
            patch.object(installer,'BCS_SHA',installer.sha(self.bcs)),
            patch.object(installer,'BASE_LUA_SHA',installer.sha(self.lua))]
        for p in self.patches:
            p.start();self.addCleanup(p.stop)

    def backup(self,root,state,tag):
        return installer.make_backup(root,state,tag,dest_root=self.ext)

    def guard(self):
        pass

    def run_weidu(self,cmd,**kw):
        root=Path(kw['cwd'])
        logfile=root/'WeiDU.log'
        if '--force-uninstall' in cmd:
            (root/installer.LUA).write_bytes(self.lua)
            text=logfile.read_text().splitlines(keepends=True)
            assert 'BGX59' in text[-1]
            logfile.write_text(''.join(text[:-1]))
        else:
            (root/installer.LUA).write_bytes((root/installer.STAGE_LUA).read_bytes())
            logfile.write_text(logfile.read_text()+'~BGX59/setup-BGX59.tp2~ #0 #0 // 059\n')
        return subprocess.CompletedProcess(cmd,0,'mock-weidu-success','')

    def test_good_056_baseline(self):
        proof=installer.game_check(self.root,'056')
        self.assertIn('BGX56',proof['last_mod'])

    def test_source_valid(self):
        self.assertEqual(installer.validate_source(MOCK_NEW_SOURCE)['git_blob'],installer.SOURCE_BLOB)

    def test_wrong_source_blocked(self):
        with self.assertRaisesRegex(installer.Stop,'SOURCE_BLOB_MISMATCH'):
            installer.validate_source(MOCK_NEW_SOURCE+b'ATTACK')
        self.assertFalse((self.root/installer.STAGE).exists())

    def test_wrong_last_weidu_blocked(self):
        (self.root/'WeiDU.log').write_text('~WRONG/setup-WRONG.tp2~ #0 #0\n')
        with self.assertRaisesRegex(installer.Stop,'UNEXPECTED_LAST_MOD'):
            installer.game_check(self.root,'056')

    def test_changed_bcs_blocked(self):
        (self.root/installer.BCS).write_bytes(b'altered')
        with self.assertRaisesRegex(installer.Stop,'BCS_HASH_DRIFT'):
            installer.game_check(self.root,'056')

    def test_changed_lua_blocked(self):
        (self.root/installer.LUA).write_bytes(b'altered')
        with self.assertRaisesRegex(installer.Stop,'LUA_HASH_DRIFT'):
            installer.game_check(self.root,'056')

    def test_existing_stage_blocked(self):
        (self.root/installer.STAGE).mkdir()
        with self.assertRaisesRegex(installer.Stop,'STAGING_ALREADY_PRESENT'):
            installer.game_check(self.root,'056')

    def test_symlink_component_blocked(self):
        (self.root/'override'/'symlink.lua').symlink_to(self.root/'chitin.key')
        with self.assertRaisesRegex(installer.Stop,'REPARSE_BLOCKED'):
            installer.secure_file(self.root,'override/symlink.lua')

    def test_guard_fail_prevents_write(self):
        def fail():raise installer.Stop('GAME_RUNNING')
        with self.assertRaisesRegex(installer.Stop,'GAME_RUNNING'):
            installer.install(self.root,MOCK_NEW_SOURCE,guard=fail,backup=self.backup,runner=self.run_weidu)
        self.assertEqual((self.root/installer.LUA).read_bytes(),self.lua)
        self.assertFalse((self.root/installer.STAGE).exists())

    def test_install_and_rollback(self):
        a=installer.install(self.root,MOCK_NEW_SOURCE,guard=self.guard,backup=self.backup,runner=self.run_weidu)
        self.assertEqual(a['status'],'INSTALLED_GUARDED_059')
        self.assertTrue((Path(a['backup'])/'BACKUP_PROOF.json').exists())
        self.assertEqual((self.root/installer.LUA).read_bytes(),MOCK_NEW_SOURCE)
        self.assertEqual((self.root/installer.BCS).read_bytes(),self.bcs)
        self.assertIn('BGX59',installer.last_weidu(self.root))
        b=installer.rollback(self.root,MOCK_NEW_SOURCE,guard=self.guard,backup=self.backup,runner=self.run_weidu)
        self.assertEqual(b['status'],'ROLLED_BACK_TO_056')
        self.assertEqual((self.root/installer.LUA).read_bytes(),self.lua)
        self.assertEqual((self.root/installer.BCS).read_bytes(),self.bcs)
        self.assertIn('BGX56',installer.last_weidu(self.root))
        self.assertEqual(len(list(self.ext.iterdir())),2)

    def test_rollback_refuses_later_weidu(self):
        installer.install(self.root,MOCK_NEW_SOURCE,guard=self.guard,backup=self.backup,runner=self.run_weidu)
        with (self.root/'WeiDU.log').open('a') as f:f.write('~NEXT/setup-NEXT.tp2~ #0 #0 //NEXT\n')
        with self.assertRaisesRegex(installer.Stop,'UNEXPECTED_LAST_MOD'):
            installer.rollback(self.root,MOCK_NEW_SOURCE,guard=self.guard,backup=self.backup,runner=self.run_weidu)
        self.assertEqual((self.root/installer.LUA).read_bytes(),MOCK_NEW_SOURCE)

    def test_rollback_refuses_modified_stage(self):
        installer.install(self.root,MOCK_NEW_SOURCE,guard=self.guard,backup=self.backup,runner=self.run_weidu)
        (self.root/installer.STAGE_LUA).write_text('tampered')
        with self.assertRaisesRegex(installer.Stop,'INSTALLED_STAGING_SOURCE_DRIFT'):
            installer.rollback(self.root,MOCK_NEW_SOURCE,guard=self.guard,backup=self.backup,runner=self.run_weidu)

    def test_failed_weidu_keeps_backup_and_staging(self):
        def fail(cmd,**kw):return subprocess.CompletedProcess(cmd,1,'fake fail','')
        with self.assertRaisesRegex(installer.Stop,'WEIDU_INSTALL_FAILED'):
            installer.install(self.root,MOCK_NEW_SOURCE,guard=self.guard,backup=self.backup,runner=fail)
        self.assertEqual((self.root/installer.LUA).read_bytes(),self.lua)
        self.assertTrue(list(self.ext.rglob('BACKUP_PROOF.json')))
        self.assertTrue((self.root/installer.STAGE_LUA).is_file())

    def test_fetch_pinned_source_with_mock_https(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self,*args): pass
            def read(self,limit):
                self.limit=limit
                return MOCK_NEW_SOURCE
        seen=[]
        def opener(request,timeout):
            seen.append((request.full_url,timeout))
            return Response()
        self.assertEqual(installer.fetch_source(opener=opener),MOCK_NEW_SOURCE)
        self.assertEqual(seen,[(installer.RAW_URL,20)])

    def test_fetch_rejects_wrong_content_with_mock_https(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self,*args): pass
            def read(self,limit):return b"not pinned"
        with self.assertRaisesRegex(installer.Stop,"SOURCE_BLOB_MISMATCH"):
            installer.fetch_source(opener=lambda req,timeout:Response())

    def test_readonly_preflight_does_not_mutate_game(self):
        source_file=Path(self.tmp.name)/"candidate.lua"
        source_file.write_bytes(MOCK_NEW_SOURCE)
        before={p.relative_to(self.root):installer.sha(p.read_bytes()) for p in self.root.rglob('*') if p.is_file()}
        installer.game_check(self.root,"056")
        installer.source_from_disk(source_file)
        after={p.relative_to(self.root):installer.sha(p.read_bytes()) for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before,after)

    def test_readonly_status_cli_requires_no_network(self):
        cp=subprocess.run([sys.executable,str(HERE/"BGXAI059_SAFE.py"),"status"],
                          capture_output=True,text=True,timeout=8)
        self.assertEqual(cp.returncode,2) # no EET in this Linux test environment
        self.assertIn("BGXAI059 STOP",cp.stdout)
        self.assertNotIn("urllib",cp.stdout)

    def test_install_cli_requires_optin_without_download(self):
        cp=subprocess.run([sys.executable,str(HERE/"BGXAI059_SAFE.py"),"install"],
                          capture_output=True,text=True,timeout=8)
        self.assertEqual(cp.returncode,2)
        self.assertIn("EXPLICIT_--yes_AND_--confirm_BGXAI_059_EXPERIMENTAL_REQUIRED",cp.stdout)

    def test_install_yes_without_exact_confirmation_is_blocked(self):
        cp=subprocess.run([sys.executable,str(HERE/"BGXAI059_SAFE.py"),"install","--yes"],
                          capture_output=True,text=True,timeout=8)
        self.assertEqual(cp.returncode,2)
        self.assertIn("EXPLICIT_--yes_AND_--confirm_BGXAI_059_EXPERIMENTAL_REQUIRED",cp.stdout)

    def test_preexisting_remote_host_cannot_be_overridden(self):
        self.assertIn('raw.githubusercontent.com/jeleZa112/nwn-xanos-updates/'+installer.COMMIT,installer.RAW_URL)
        self.assertNotIn('refs/heads/',installer.RAW_URL)

if __name__=='__main__':unittest.main(verbosity=2)