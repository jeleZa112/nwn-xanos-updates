"""One-time, targeted tests for actual user incident: Enter -> unwanted V3 + network timeout."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SRC=Path("BGXAI/BUILD/R38_GUARDED_FROM_R37_20261127/BGXAI_ONEFILE176_NET_AND_DEFAULT_HOTFIX_STAGE.py")
spec=importlib.util.spec_from_file_location("bgxai176_hotfix",SRC)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
PIN="a"*40
class Response:
 def __init__(self,data):self.data=data
 def __enter__(self):return self
 def __exit__(self,*args):return False
 def read(self,n):return self.data[:n]
class Tests(unittest.TestCase):
 def test_enter_exits_without_running_completed_v3(self):
  with patch.object(m.sys.stdin,"isatty",return_value=True),patch("builtins.input",return_value=""):
   self.assertEqual(m.ask_r38_mode(True),"cancel")
  with patch.object(m.sys.stdin,"isatty",return_value=True),patch("builtins.input",return_value="0"):
   self.assertEqual(m.ask_r38_mode(True),"cancel")
 def test_main_empty_never_downloads_or_compiles(self):
  with patch.object(m.sys.stdin,"isatty",return_value=True),patch("builtins.input",return_value=""),patch.object(m,"prepare_v3",side_effect=AssertionError("unexpected completed test")),patch.object(m,"run_r38",side_effect=AssertionError("unexpected R38")):
   self.assertEqual(m.main(["--v3","--commit",PIN,"--game","/fake"]),0)
 def test_1_only_explicitly_triggers_v3(self):
  with patch.object(m.sys.stdin,"isatty",return_value=True),patch("builtins.input",return_value="1"):
   self.assertIsNone(m.ask_r38_mode(True))
 def test_4_only_explicitly_routes_install(self):
  with patch.object(m.sys.stdin,"isatty",return_value=True),patch("builtins.input",return_value="4"):
   self.assertEqual(m.ask_r38_mode(True),"install")
 def test_r38_cache_first_download_then_offline(self):
  path=m.R38_LUA
  raw=Path(path).read_bytes()
  calls=[]
  def fetch(commit,name):
   calls.append(name)
   return raw
  with tempfile.TemporaryDirectory() as td:
   cache=Path(td)
   self.assertEqual(m.fetch_r38_cached(PIN,path,Path("/fake"),cache,fetch),raw)
   def fail(*args):raise AssertionError("MUST_REUSE_VERIFIED_CACHE")
   self.assertEqual(m.fetch_r38_cached(PIN,path,Path("/fake"),cache,fail),raw)
   self.assertEqual(calls,[path])
   cached=list(cache.glob("*.bin"))
   self.assertEqual(len(cached),1)
   self.assertEqual(cached[0].read_bytes(),raw)
 def test_tampered_cache_cannot_be_used_offline(self):
  path=m.R38_PY;raw=Path(path).read_bytes()
  with tempfile.TemporaryDirectory() as td:
   cache=Path(td)
   self.assertEqual(m.fetch_r38_cached(PIN,path,Path("/fake"),cache,lambda a,b:raw),raw)
   saved=next(cache.glob("*.bin"));saved.write_bytes(raw+b"X")
   def no_network(a,b):raise m.Hold("NETWORK_UNAVAILABLE")
   with self.assertRaisesRegex(m.Hold,"NETWORK_UNAVAILABLE"):
    m.fetch_r38_cached(PIN,path,Path("/fake"),cache,no_network)
 def test_tampered_cache_replaced_only_by_verified_download(self):
  path=m.R38_PY;raw=Path(path).read_bytes()
  with tempfile.TemporaryDirectory() as td:
   cache=Path(td)
   m.fetch_r38_cached(PIN,path,Path("/fake"),cache,lambda a,b:raw)
   f=next(cache.glob("*.bin"));f.write_bytes(b"malicious")
   self.assertEqual(m.fetch_r38_cached(PIN,path,Path("/fake"),cache,lambda a,b:raw),raw)
   self.assertEqual(f.read_bytes(),raw)
 def test_nonallowlisted_cache_source_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   with self.assertRaises(m.Hold):
    m.fetch_r38_cached(PIN,"BGXAI/override/DPLAYER.BCS",Path("/fake"),Path(td),lambda a,b: b"x")
 def test_third_independent_raw_hostname_after_two_failures(self):
  path=m.R38_PY;raw=Path(path).read_bytes();urls=[]
  def network(req,timeout=None):
   urls.append(req.full_url)
   if len(urls)<3:raise OSError("blocked network")
   return Response(raw)
  with patch.object(m.urllib.request,"urlopen",side_effect=network):
   self.assertEqual(m.fetch_pinned(PIN,path),raw)
  self.assertEqual(len(urls),3)
  self.assertIn("raw.githubusercontent.com",urls[0])
  self.assertIn("cdn.jsdelivr.net",urls[1])
  self.assertIn("fastly.jsdelivr.net",urls[2])
 def test_unverified_web_result_never_cached(self):
  path=m.R38_PY
  with tempfile.TemporaryDirectory() as td:
   cache=Path(td)
   with self.assertRaises(m.Hold):
    m.fetch_r38_cached(PIN,path,Path("/fake"),cache,lambda a,b:b"wrong")
   self.assertEqual(list(cache.iterdir()),[])
 def test_noninteractive_v3_backward_compatibility(self):
  with patch.object(m.sys.stdin,"isatty",return_value=False):
   self.assertIsNone(m.ask_r38_mode(True))
 def test_source_has_no_game_mutation_api(self):
  code=SRC.read_text()
  for token in ("XEquipItem(","ClearActions(","FillSlot(","SetGlobal("):
   self.assertNotIn(token,code)
if __name__=="__main__":unittest.main(verbosity=2)
