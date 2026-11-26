"""BG_EET_RU V154: public CI contract; no game or process writes."""
from __future__ import annotations
import ast, hashlib, importlib.util, json, tempfile, unittest
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[2]
MOD=ROOT/'ui-observer/v154/v154_guarded_capture.py'
ORIG=ROOT/'ui-observer/v153/v153_guarded.py'
LUA=ROOT/'ui-observer/v153/BGCL150.lua'
CMD=ROOT/'onefile/BG_EET_RU_UPDATE.cmd'
MAN=ROOT/'onefile/release.json'

def sha(x):return hashlib.sha256(x).hexdigest()
spec=importlib.util.spec_from_file_location('v154_guarded_ro',MOD)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class V154(unittest.TestCase):
 def test_source_hashes_and_release(self):
  b=CMD.read_bytes(); j=json.loads(MAN.read_text('utf8'))
  self.assertEqual(j['version'],154)
  self.assertEqual(j['sha256'],sha(b))
  self.assertLessEqual(len(b),750000)
  self.assertEqual(sha(MOD.read_bytes()),'db636cad123194092b248ca4d073ab448c16c9801bb7879ce0c5d68b0eafb1c4')
  self.assertEqual(sha(ORIG.read_bytes()),'ce54a4373a9b523877f2415cdc6503fb7d7e9824ba7c6d1a5fbaba148bd161f4')
  self.assertEqual(sha(LUA.read_bytes()),m.SIDE_SHA)
  self.assertFalse(j['game_writes_allowed'])
  self.assertFalse(j['default_game_writes_allowed'])

 def test_same_cmd_and_report_73_and_74(self):
  data=CMD.read_bytes()
  self.assertIn(b'SELF_VERSION = 154',data)
  self.assertIn(b'4=play',data)
  self.assertIn(b'10=V153',data)
  self.assertIn(b'74_V154_CONSOLE_CAPTURE_RO.json',data)
  self.assertIn(b'73_V153_GUARDED_OBSERVER.json',data)
  self.assertIn(b'if mode:return v126_dispatch(game,WORKDIR/REPORT_NAME,mode)',data)
  self.assertIn(b'if mode==\'capture\' and sha_path(game/\'override\'/\'UI.MENU\')',data)
  self.assertIn(b'if a==\'9\':return v133_audit(game,WORKDIR/REPORT_NAME,True)',data)
  self.assertIn(b"V153_PIN='db636cad123194092b248ca4d073ab448c16c9801bb7879ce0c5d68b0eafb1c4'",data)
  self.assertEqual(ast.parse(data.split(b'\n',1)[1].decode('utf8')).__class__,ast.Module)

 def test_v153_functions_preserved_except_run(self):
  orig=ast.parse(ORIG.read_text('utf8'))
  new=ast.parse(MOD.read_text('utf8'))
  a={f.name:ast.dump(f,include_attributes=False) for f in orig.body if isinstance(f,ast.FunctionDef) and f.name!='run'}
  b={f.name:ast.dump(f,include_attributes=False) for f in new.body if isinstance(f,ast.FunctionDef) and f.name!='run'}
  for name,old in a.items():self.assertEqual(b[name],old,name)
  self.assertEqual(set(b)-set(a),{'_v154_parse_console','_v154_capture'})

 def test_parser_only_claims_raw(self):
  p=m._v154_parse_console(b'BG_EET_RU_V150_RAW\t2\t5\t12\tA\nBG_EET_RU_V150_HOLD\tINVALID_TICK\t3\n')
  self.assertEqual(len(p['v150_raw_samples']),1)
  self.assertEqual(len(p['v150_hold_samples']),1)
  self.assertIn('runtime counters require explicit Lua',p['note'])
  self.assertEqual(len(m._v154_parse_console(b'BG_EET_RU_V150_RAW\tA\n'*40)['v150_raw_samples']),24)

 def test_no_game_write_when_guard_missing(self):
  with tempfile.TemporaryDirectory() as d:
   game=Path(d)/'game';work=Path(d)/'out'
   (game/'override').mkdir(parents=True);work.mkdir()
   (game/'override'/'UI.MENU').write_bytes(b'unexpected')
   with mock.patch.object(m.subprocess,'Popen',side_effect=AssertionError('must not launch')):
    r=m.run('capture',game,work,allow_non_windows_test=True)
   self.assertIn('HOLD',r['status']+' '+str(r.get('reason')))
   self.assertEqual(r['game_files_written_this_action'],0)
   self.assertEqual((game/'override'/'UI.MENU').read_bytes(),b'unexpected')

if __name__=='__main__':unittest.main(verbosity=2)
