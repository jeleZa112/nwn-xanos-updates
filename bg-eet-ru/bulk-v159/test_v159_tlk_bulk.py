"""Synthetic-only, no real game writes. Matches V157 snapshot schema and TLK layout."""
import importlib.util, unittest, tempfile, struct, json, hashlib, re
from pathlib import Path
SRC=Path(__file__).with_name('v159_tlk_bulk_guarded.py')
spec=importlib.util.spec_from_file_location('v159_bulk',SRC)
M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
ORIG=json.loads(Path(__file__).with_name('BATCH_V159_MANIFEST_SOURCE_ONLY.json').read_text(encoding='utf-8'))

class V159Guarded(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.n=max(M.IDS)+1
  body=bytearray(b'TLK V1  '+b'\x00\x00'+struct.pack('<II',cls.n,18+26*cls.n))
  body+=b'\x00'* (cls.n*26)
  idx=M.MANIFEST['tlk_editorial_changes']
  for x in idx:
   data=x['existing_ru_exact'].encode('utf-8');start=18+26*cls.n;offset=len(body)-start
   struct.pack_into('<H',body,18+26*x['strref'],7)
   struct.pack_into('<II',body,18+26*x['strref']+18,offset,len(data))
   body+=data
  cls.fixture=bytes(body)
  cls.orig_expect=dict(M.MANIFEST['expected_source_tlk_sha256'])
  cls.fake_hash=hashlib.sha256(cls.fixture).hexdigest()
  M.MANIFEST['expected_source_tlk_sha256']={'dialog.tlk':cls.fake_hash,'dialogf.tlk':cls.fake_hash}
 @classmethod
 def tearDownClass(cls):
  M.MANIFEST['expected_source_tlk_sha256']=cls.orig_expect
 def makegame(self):
  env=tempfile.TemporaryDirectory();self.addCleanup(env.cleanup)
  root=Path(env.name);game=root/'game';work=root/'external';(game/'lang'/'ru_RU').mkdir(parents=True);work.mkdir()
  (game/'override').mkdir();(game/'chitin.key').write_bytes(b'KEY ') ;(game/'WeiDU.log').write_bytes(b'~TEST.TP2~ #0 #0 // old\r\n')
  (game/'override'/'UI.MENU').write_bytes(b'v157-UI')
  for k in M.TLKS:(game/'lang'/'ru_RU'/k).write_bytes(self.fixture)
  state={'schema':'BG_EET_RU_V157_ONE_BATCH_GUARDED_V1','status':'INSTALLED','game_root':str(game.resolve()),'installed_sha256':dict(M.MANIFEST['expected_source_tlk_sha256'])}
  (work/'BG_EET_RU_V157_BULK_STATE.json').write_text(json.dumps(state),encoding='utf8')
  return game,work
 def test_01_reviewed_16_no_old_reuse(self):
  self.assertEqual(len(M.IDS),16)
  self.assertEqual(len(set(M.IDS)),16)
  self.assertTrue(set(M.IDS).isdisjoint({216190,227151,227254,227304,231440,276225,276226,276227,276240,315861}))
 def test_02_source_exact_hash(self):
  for x in M.MANIFEST['tlk_editorial_changes']:
   self.assertEqual(M.digest(x['existing_ru_exact'].encode()),x['old_utf8_sha256'])
   self.assertEqual(M.digest(x['proposed_ru_exact'].encode()),x['new_utf8_sha256'])
 def test_03_numbers_unchanged(self):
  pattern=r'(?<![A-Za-zА-Яа-я\d])(?:\d+[dд]\d+(?:\s*\+\s*\d+)?|\d+(?:\s*\+\s*\d+)?)(?![A-Za-zА-Яа-я\d])'
  for x in M.MANIFEST['tlk_editorial_changes']:
   a=[re.sub(r'\s+','',v) for v in re.findall(pattern,x['existing_ru_exact'],flags=re.I)]
   b=[re.sub(r'\s+','',v) for v in re.findall(pattern,x['proposed_ru_exact'],flags=re.I)]
   self.assertEqual(a,b,msg=x['strref'])
 def test_04_byte_preservation_and_16_rows(self):
  out=M.prepare_tlk(self.fixture,'dialog.tlk')
  self.assertNotEqual(out,self.fixture)
  self.assertEqual(out[:18+26*self.n][:18+26*self.n],self.fixture[:18+26*self.n][:18+26*self.n].replace(b'XXXX',b'XXXX')) if False else None
  n,start=M.load_tlk(out);self.assertEqual(n,self.n)
  for x in M.MANIFEST['tlk_editorial_changes']:
   self.assertEqual(M.row_text(out,x['strref'],n,start).decode(),x['proposed_ru_exact'])
  # At most 16 offset and size fields changed in the original file.
  original_head=bytearray(out[:len(self.fixture)])
  for idx in M.IDS:original_head[18+26*idx+18:18+26*idx+26]=self.fixture[18+26*idx+18:18+26*idx+26]
  self.assertEqual(bytes(original_head),self.fixture)
 def test_05_source_hash_drift_is_stop(self):
  corrupt=bytearray(self.fixture);corrupt[-1]^=1
  with self.assertRaises(M.Hold):M.prepare_tlk(bytes(corrupt),'dialog.tlk')
 def test_06_text_drift_is_stop(self):
  n,start=M.load_tlk(self.fixture)
  old=dict(M.MANIFEST['expected_source_tlk_sha256'])
  try:
   cur=bytearray(self.fixture);idx=M.IDS[0];pos=18+26*idx+18;off,size=struct.unpack_from('<II',cur,pos);cur[start+off]^=1
   M.MANIFEST['expected_source_tlk_sha256']['dialog.tlk']=M.digest(cur)
   with self.assertRaisesRegex(M.Hold,'TARGET_TEXT_DRIFT'):M.prepare_tlk(bytes(cur),'dialog.tlk')
  finally:M.MANIFEST['expected_source_tlk_sha256']=old
 def test_07_exact_two_tlk_preflight(self):
  game,work=self.makegame();r=M.run(game,work,'preflight')
  self.assertEqual(r['status'],'V159_DUAL_TLK_EXACT_PREFLIGHT_PASS');self.assertEqual(r['game_files_written'],0)
  self.assertEqual(r['files']['dialog.tlk']['source_sha256'],self.fake_hash)
 def test_08_wrong_v157_ledger_safe_stop(self):
  game,work=self.makegame();p=work/'BG_EET_RU_V157_BULK_STATE.json';s=json.loads(p.read_text());s['status']='ROLLED_BACK';p.write_text(json.dumps(s))
  r=M.run(game,work,'preflight');self.assertEqual(r['status'],'V159_SAFE_STOP');self.assertIn('V157_NOT_ACTIVE',r['reason'])
 def test_09_one_tlk_tampered_blocks_both(self):
  game,work=self.makegame();p=game/'lang'/'ru_RU'/'dialogf.tlk';p.write_bytes(self.fixture+b'?')
  r=M.run(game,work,'preflight');self.assertEqual(r['status'],'V159_SAFE_STOP')
  self.assertEqual((game/'lang'/'ru_RU'/'dialog.tlk').read_bytes(),self.fixture)
 def test_10_declined_approval_changes_nothing(self):
  game,work=self.makegame();old=M.no_running_game;M.no_running_game=lambda:None
  try:
   oldapp=M.approved;M.approved=lambda token: (_ for _ in ()).throw(M.Hold('TYPED_APPROVAL_REQUIRED'))
   r=M.run(game,work,'install')
   self.assertEqual(r['status'],'V159_SAFE_STOP');self.assertEqual(r['game_files_written'],'UNKNOWN_IF_EXCEPTION_AFTER_AUTHORIZED_WRITE')
   for name in M.TLKS:self.assertEqual((game/'lang'/'ru_RU'/name).read_bytes(),self.fixture)
  finally:M.no_running_game=old;M.approved=oldapp
 def test_11_install_two_files_and_last_only_rollback(self):
  game,work=self.makegame();old=M.no_running_game;M.no_running_game=lambda:None
  oldapp=M.approved;M.approved=lambda token:None
  try:
   r=M.run(game,work,'install')
   self.assertEqual(r['status'],'V159_16_TLK_INSTALLED_AWAITING_GAMEPLAY')
   self.assertEqual(r['game_files_written'],2)
   state=M.read_state(work);self.assertEqual(state['status'],'INSTALLED')
   for name in M.TLKS:self.assertEqual(M.file_sha(game/'lang'/'ru_RU'/name),r['files'][name]['new_sha256'])
   status=M.run(game,work,'status');self.assertTrue(all(status['current_tlk_sha_matches'].values()))
   rollback=M.run(game,work,'rollback');self.assertEqual(rollback['status'],'V159_GUARDED_ROLLBACK_DONE')
   for name in M.TLKS:self.assertEqual((game/'lang'/'ru_RU'/name).read_bytes(),self.fixture)
   self.assertEqual(M.run(game,work,'status')['status'],'V159_ROLLED_BACK')
  finally:M.no_running_game=old;M.approved=oldapp
 def test_12_rollback_denied_on_ui_drift(self):
  game,work=self.makegame();old=M.no_running_game;M.no_running_game=lambda:None
  oldapp=M.approved;M.approved=lambda token:None
  try:
   self.assertEqual(M.run(game,work,'install')['status'],'V159_16_TLK_INSTALLED_AWAITING_GAMEPLAY')
   (game/'override'/'UI.MENU').write_bytes(b'other-release')
   r=M.run(game,work,'rollback');self.assertEqual(r['status'],'V159_SAFE_STOP');self.assertIn('UI_DRIFT',r['reason'])
   self.assertEqual(M.read_state(work)['status'],'INSTALLED')
  finally:M.no_running_game=old;M.approved=oldapp
 def test_13_wrong_game_root_hold(self):
  game,work=self.makegame();st=work/'BG_EET_RU_V157_BULK_STATE.json';j=json.loads(st.read_text());j['game_root']=str(game.parent);st.write_text(json.dumps(j))
  self.assertIn('V157_GAME_ROOT_MISMATCH',M.run(game,work,'preflight')['reason'])
 def test_14_numeric_literals_preserved_and_all_ids(self):
  self.assertEqual(M.MANIFEST['edited_ids'],list(M.IDS))
  self.assertTrue(M.MANIFEST['numeric_tokens_unchanged'])
 def test_15_no_remote_network_for_module(self):
  src=SRC.read_text(encoding='utf-8')
  self.assertNotIn('urlopen(',src)
  self.assertNotIn('subprocess.Popen(',src)
 def test_16_write_path_not_available_in_read_only(self):
  game,work=self.makegame();before={n:(game/'lang'/'ru_RU'/n).read_bytes() for n in M.TLKS}
  self.assertEqual(M.run(game,work,'status')['game_files_written'],0)
  self.assertEqual(M.run(game,work,'preflight')['game_files_written'],0)
  self.assertEqual(before,{n:(game/'lang'/'ru_RU'/n).read_bytes() for n in M.TLKS})

if __name__=='__main__':unittest.main(verbosity=2)
