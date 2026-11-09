import ctypes, ctypes.util, hashlib, json, tempfile, unittest, importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

P = Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('install044',P/'BGXAI44_INSTALL.py')
M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)

class InstallerTests(unittest.TestCase):
    def test_manifest_safe(self):
        self.assertEqual(M.verify_source(P)['version'],'0.3.16-044-DIAG')
    def test_path_traversal_blocked(self):
        for bad in ('../file','a/../file','C:/foo','a\\foo','/tmp/test'):
            with self.assertRaises(RuntimeError): M.safe(P,bad)
    def test_release_has_no_game_action_calls(self):
        lua=(P/M.OWN_LUA).read_text()
        for call in ('ClearActions(', 'QueueResponse(', 'ActionOverride(', 'SetGlobal(', 'os.execute(', 'io.open('):
            self.assertNotIn(call,lua)
    def prepare(self,root):
        files={
          'chitin.key':b'K'*2000,'override/BDDEFAI.BCS':b'BCS'*5000,
          'override/M_BGX43Probe.lua':b'prior43', 'override/M___EEex.lua':b'eeex123456789',
          'InfinityLoader.exe':b'MZ'+b'I'*12000, M.BASE_WEIDU:b'MZ'+b'Z'*120000,
          'WeiDU.log':b'~setup-enhanced-powergaming-scripts.tp2~ #0 #1\n~BGX42/SETUP-BGX42.TP2~ #0 #0\n~BGX43/SETUP-BGX43.TP2~ #0 #0\n',
          'lang/ru_RU/dialog.tlk':b'TLK'*700,
        }
        for path,blob in files.items():
            p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(blob)
        M.BCS_SHA=M.digest(root/M.BCS);M.LUA43_SHA=M.digest(root/M.LUA43)
    def test_install_uninstall_mock_weidu(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'game';root.mkdir()
            self.prepare(root)
            backups=Path(tmp)/'external'
            before={key:M.digest(root/key) for key in ['chitin.key',M.BCS,M.LUA43,M.EEEX]}
            def runner(args,**kw):
                if '--force-install' in args:
                    (root/M.OVERRIDE_LUA).write_bytes((root/M.OWN_LUA).read_bytes())
                    with (root/'WeiDU.log').open('a') as f:f.write('~BGX44/SETUP-BGX44.TP2~ #0 #0\n')
                elif '--force-uninstall' in args:
                    (root/M.OVERRIDE_LUA).unlink()
                    lines=(root/'WeiDU.log').read_text().splitlines()
                    (root/'WeiDU.log').write_text('\n'.join(lines[:-1])+'\n')
                return SimpleNamespace(returncode=0,stdout='WeiDU simulated',stderr='')
            r=M.install(root,P,runner=runner,guard=lambda:None,backup_dir=backups,exact_path=False)
            self.assertEqual(r['status'],'INSTALLED_READONLY_044',r)
            self.assertTrue(all(r['checks'].values()))
            self.assertEqual(M.verified_install_backup(root,base=backups),Path(r['backup']))
            for k,v in before.items():self.assertEqual(M.digest(root/k),v,k)
            u=M.uninstall(root,P,runner=runner,guard=lambda:None,backup_dir=backups,exact_path=False)
            self.assertEqual(u['status'],'UNINSTALLED_044',u)
            self.assertTrue(all(u['checks'].values()))
            for k,v in before.items():self.assertEqual(M.digest(root/k),v,k)
    def test_modified_source_fails_before_install(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'game';root.mkdir();self.prepare(root)
            # Fake package manifest mismatch: must halt before staging files
            pk=Path(tmp)/'package';pk.mkdir()
            (pk/'SOURCE_MANIFEST.json').write_text((P/'SOURCE_MANIFEST.json').read_text())
            (pk/'BGXAI44_INSTALL.py').write_text('tampered')
            with self.assertRaises(RuntimeError):M.install(root,pk,guard=lambda:None,exact_path=False)
            self.assertFalse((root/'BGX44').exists())
            self.assertFalse((root/M.OVERRIDE_LUA).exists())

class LuaTests(unittest.TestCase):
    def test_callback_action134_and_hotkey(self):
        lib=ctypes.CDLL(ctypes.util.find_library('lua5.4'))
        lib.luaL_newstate.restype=ctypes.c_void_p
        lib.luaL_openlibs.argtypes=[ctypes.c_void_p]
        lib.luaL_loadstring.argtypes=[ctypes.c_void_p,ctypes.c_char_p];lib.luaL_loadstring.restype=ctypes.c_int
        lib.lua_pcallk.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_longlong,ctypes.c_void_p];lib.lua_pcallk.restype=ctypes.c_int
        lib.lua_tolstring.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.POINTER(ctypes.c_size_t)];lib.lua_tolstring.restype=ctypes.c_char_p
        lib.lua_close.argtypes=[ctypes.c_void_p]
        L=lib.luaL_newstate();lib.luaL_openlibs(L)
        def run(s):
            r=lib.luaL_loadstring(L,s.encode())
            if r==0:r=lib.lua_pcallk(L,0,-1,0,0,None)
            if r!=0:raise AssertionError('Lua runtime: '+str(lib.lua_tolstring(L,-1,None)))
        try:
            run('''
messages={}
EEex_Action_AddSpriteStartedActionListener=function(f) actionHook=f end
EEex_Key_AddPressedListener=function(f) keyHook=f end
EEex_Sprite_GetInPortraitID=function(i) return i==0 and 10 or -1 end
EEex_Key_IsDown=function(key) return key==0x400000E0 or key==0x400000E2 end
Infinity_DisplayString=function(s) table.insert(messages,s) end
''')
            run((P/M.OWN_LUA).read_text())
            run('''
assert(BGX44Diag.actionRegistered and BGX44Diag.keyRegistered)
assert(actionHook~=nil and keyHook~=nil)
actionHook({m_id=99},{m_actionID=134,m_acteeID={m_Instance=10}})
actionHook({m_id=99},{m_actionID=3,m_acteeID={m_Instance=10}})
actionHook({m_id=99},{m_actionID=105,m_acteeID={m_Instance=12}})
actionHook({m_id=99},{m_actionID=999,m_acteeID={m_Instance=10}})
assert(BGX44Diag.started==4)
assert(BGX44Diag.attacks==3)
assert(BGX44Diag.attacks134==1)
assert(BGX44Diag.partyAttacks==2)
assert(keyHook(0x40000044,false)==false)
assert(#messages==2)
assert(string.find(messages[2],'id134=1',1,true)~=nil)
assert(string.find(messages[1],'043 loaded=false',1,true)~=nil)
''')
        finally:lib.lua_close(L)

if __name__=='__main__':unittest.main(verbosity=2)
