"""Onefile 175/176 regression + new R38 staged sub-menu; no user game touched."""
import importlib.util
import inspect
import json
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT=Path.cwd()
PRE=ROOT/'BGXAI/BUILD/WEAPON_XEQUIP_ONEFILE_175_RO_20261126'
def load(name,p):
    s=importlib.util.spec_from_file_location(name,str(p));m=importlib.util.module_from_spec(s)
    s.loader.exec_module(m);return m
legacy=load('r38old',PRE/'BGXAI_XEQUIP_ONEFILE_175_RO_V1.py')
stage=load('r38stage',PRE/'BGXAI_XEQUIP_ONEFILE_176_R38_STAGE_ONLY.py')
PIN='a'*40
class Response:
    def __init__(self,data,expected):self.data=data;self.expected=expected
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def read(self,n):
        assert n==self.expected+1,(n,self.expected)
        return self.data[:n]
class Host:
    def __init__(self,fail_first=False,tamper=None):
        self.calls=[];self.fail_first=fail_first;self.tamper=tamper
    def __call__(self,req,timeout=0):
        url=req.full_url
        idx=url.index('/BGXAI/')+1
        path=url[idx:]
        self.calls.append(path)
        if self.fail_first and len(self.calls)==1:raise OSError('mock raw host down')
        expected=(stage.SOURCES.get(path) or stage.V3_SOURCES.get(path) or stage.R38_SOURCES.get(path))
        if expected is None:raise AssertionError(path)
        raw=Path(path).read_bytes()
        if self.tamper==path:raw+=b'X'
        return Response(raw,expected[0])

class Tests(unittest.TestCase):
 def test_01_legacy_175_pins_unchanged(self):self.assertEqual(stage.SOURCES,legacy.SOURCES)
 def test_02_legacy_v3_pins_unchanged(self):self.assertEqual(stage.V3_SOURCES,legacy.V3_SOURCES)
 def test_03_default_175_runner_code_unchanged(self):
    for name in ('prepare','check_report','ensure_external','validate_pin','digest','write_report'):
        self.assertEqual(inspect.getsource(getattr(stage,name)),inspect.getsource(getattr(legacy,name)),name)
 def test_04_r38_source_pin_count(self):self.assertEqual(len(stage.R38_SOURCES),3)
 def test_05_r38_source_exact_sha_and_lengths(self):
    for path,(length,digest) in stage.R38_SOURCES.items():
        self.assertEqual(Path(path).stat().st_size,length,path)
        self.assertEqual(stage.digest(Path(path).read_bytes()),digest,path)
 def test_06_legacy_downloads_untouched(self):
    for path in stage.SOURCES:
        with self.subTest(path=path):
            host=Host()
            with patch.object(stage.urllib.request,'urlopen',side_effect=host):
                self.assertEqual(stage.fetch_pinned(PIN,path),Path(path).read_bytes())
 def test_07_v3_downloads_untouched(self):
    for path in stage.V3_SOURCES:
        with self.subTest(path=path):
            host=Host()
            with patch.object(stage.urllib.request,'urlopen',side_effect=host):
                self.assertEqual(stage.fetch_pinned(PIN,path),Path(path).read_bytes())
 def test_08_new_r38_downloads_all_three(self):
    for path in stage.R38_SOURCES:
        with self.subTest(path=path):
            host=Host()
            with patch.object(stage.urllib.request,'urlopen',side_effect=host):
                self.assertEqual(stage.fetch_pinned(PIN,path),Path(path).read_bytes())
                self.assertEqual(len(host.calls),1)
 def test_09_r38_cdn_fallback(self):
    host=Host(fail_first=True)
    with patch.object(stage.urllib.request,'urlopen',side_effect=host):
        self.assertEqual(stage.fetch_pinned(PIN,stage.R38_PY),Path(stage.R38_PY).read_bytes())
        self.assertEqual(len(host.calls),2)
 def test_10_r38_tampered_host_holds(self):
    host=Host(tamper=stage.R38_LUA)
    with patch.object(stage.urllib.request,'urlopen',side_effect=host):
        with self.assertRaises(stage.Hold):stage.fetch_pinned(PIN,stage.R38_LUA)
 def test_11_unknown_file_rejected_before_fetch(self):
    host=Host()
    with patch.object(stage.urllib.request,'urlopen',side_effect=host):
        with self.assertRaises(stage.Hold):stage.fetch_pinned(PIN,'BGXAI/override/DPLAYER.BCS')
    self.assertFalse(host.calls)
 def test_12_non_v3_forced_r38_rejected(self):
    with self.assertRaises(stage.Hold):stage.ask_r38_mode(False,'install')
 def test_13_cli_r38_submenu_map(self):
    for choice,mode in [('2','preflight'),('3','status'),('4','install'),('5','rollback'),('6','capture')]:
        with patch.object(stage.sys.stdin,'isatty',return_value=True),patch('builtins.input',return_value=choice):
            self.assertEqual(stage.ask_r38_mode(True),mode)
 def test_14_old_v3_default_no_new_prompt(self):
    with patch.object(stage.sys.stdin,'isatty',return_value=False):
        self.assertIsNone(stage.ask_r38_mode(True))
 def test_15_v3_enter_defaults_to_old(self):
    with patch.object(stage.sys.stdin,'isatty',return_value=True),patch('builtins.input',return_value=''):
        self.assertIsNone(stage.ask_r38_mode(True))
 def test_16_v3_cancel_does_not_dispatch(self):
    with patch.object(stage.sys.stdin,'isatty',return_value=True),patch('builtins.input',return_value='0'):
        self.assertEqual(stage.ask_r38_mode(True),'cancel')
 def test_17_invalid_subchoice_holds_not_v3(self):
    with patch.object(stage.sys.stdin,'isatty',return_value=True),patch('builtins.input',return_value='999'):
        with self.assertRaises(stage.Hold):stage.ask_r38_mode(True)
 def test_18_r38_stages_only_outside_game(self):
    host=Host();records=[]
    class Process:returncode=0
    def runner(args,**kw):
        self.assertIn('--r37-tool',args)
        self.assertIn('--candidate',args)
        self.assertIn('--mode',args)
        self.assertEqual(args[args.index('--mode')+1],'preflight')
        self.assertIsNone(kw['stdin'])
        self.assertIsNone(kw['stdout'])
        self.assertIsNone(kw['stderr'])
        self.assertFalse(kw['check'])
        records.append(args)
        return Process()
    with patch.object(stage.urllib.request,'urlopen',side_effect=host):
        self.assertEqual(stage.run_r38(Path('/nonexistent/MockGame'),PIN,'preflight',runner=runner),0)
    self.assertEqual(set(host.calls),set(stage.R38_SOURCES))
    self.assertEqual(len(records),1)
 def test_19_r38_status_never_autoinstall(self):
    s=inspect.getsource(stage.run_r38)
    self.assertIn('stdin=None',s)
    self.assertNotIn('INSTALL_BGXAI_R38',s)
 def test_20_r38_mode_not_in_allowlist(self):
    with self.assertRaises(stage.Hold):stage.run_r38(Path('/no/game'),PIN,'force-install')
 def test_21_r38_source_written_once(self):
    for name in ('R38_PY','R38_LUA','R38_R37_HELPER'):
        self.assertTrue(getattr(stage,name) in stage.R38_SOURCES)
 def test_22_r38_same_cmd(self):
    s=stage.__file__
    self.assertNotIn('BGXAI_UPDATE_NEW.cmd',Path(s).read_text())
 def test_23_no_runtime_equip(self):
    s=Path(stage.__file__).read_text()
    self.assertNotIn('XEquipItem(',s)
    self.assertNotIn('SetGlobal(',s)
 def test_24_no_elevated_native_without_game(self):
    host=Host()
    with patch.object(stage.urllib.request,'urlopen',side_effect=host):
        result=stage.prepare_v3(Path('/nonexistent/Game'),PIN,False)
    self.assertEqual(result['status'],'V3_EXACT_SOURCE_PIN_PASS_NOT_NATIVE')
 def test_25_old_175_still_inert(self):
    host=Host()
    with patch.object(stage.urllib.request,'urlopen',side_effect=host):
        result=stage.prepare(Path('/nonexistent/Game'),PIN,False)
    self.assertEqual(result['status'],'INERT_SOURCE_PIN_VERIFIED_NO_NATIVE')

if __name__=='__main__':unittest.main(verbosity=2)