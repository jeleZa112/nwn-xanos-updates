import copy, hashlib, json, os, struct, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import v157_bulk_guarded as v

# Isolated synthetic game under a temporary path; no real user files are touched.
class V157(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  n=max(v.IDS)+1
  start=v.HDR+n*v.ENTRY
  table=bytearray(n*v.ENTRY);texts=bytearray()
  for c in v.MANIFEST['tlk_editorial_changes']:
   idx=c['strref'];txt=c['existing_ru_exact'].encode('utf-8');off=idx*v.ENTRY
   struct.pack_into('<H',table,off,1)
   struct.pack_into('<II',table,off+18,len(texts),len(txt));texts+=txt
  cls.fixture=b'TLK V1  '+struct.pack('<HII',0,n,start)+bytes(table)+bytes(texts)
  cls.old=copy.deepcopy(v.MANIFEST)
  v.MANIFEST['expected_source_tlk_sha256']={name:v.digest(cls.fixture) for name in v.TLKS}
 @classmethod
 def tearDownClass(cls):v.MANIFEST.clear();v.MANIFEST.update(cls.old)
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='BG_EET_RU_V157_CI_');self.addCleanup(self.tmp.cleanup)
  self.path=Path(self.tmp.name)
  self.game=self.path/'game';self.work=self.path/'docs'
  self.work.mkdir();(self.game/'lang'/'ru_RU').mkdir(parents=True)
  (self.game/'override').mkdir();(self.game/'chitin.key').write_bytes(b'K');(self.game/'WeiDU.log').write_bytes(b'STATIC_WEIDU')
  (self.game/'override'/'UI.MENU').write_bytes(b'KNOWN_UI')
  for name in v.TLKS:(self.game/'lang'/'ru_RU'/name).write_bytes(self.fixture)
 def sha(self,name):return v.file_sha(self.game/'lang'/'ru_RU'/name)
 def test_manifest_has_exact_ten_strrefs_and_20_edits(self):
  self.assertEqual(len(v.IDS),10)
  self.assertEqual(len(v.MANIFEST['tlk_editorial_changes']),10)
  self.assertEqual(v.MANIFEST['ru_banter_edited_ids'],10)
 def test_readonly_preflight_exact_match(self):
  before=[self.sha(x) for x in v.TLKS]
  r=v.run(self.game,self.work,'preflight')
  self.assertEqual(r['status'],'V157_DUAL_TLK_EXACT_PREFLIGHT_PASS')
  self.assertEqual(before,[self.sha(x) for x in v.TLKS]);self.assertEqual(r['game_files_written'],0)
  self.assertEqual(r['banter_install'],'HOLD_NO_LIVE_VISIBILITY_OR_CURRENT_DLG_BASELINE')
 def test_preflight_bad_sha_holds_without_write(self):
  p=self.game/'lang'/'ru_RU'/'dialog.tlk';p.write_bytes(self.fixture+b'X')
  r=v.run(self.game,self.work,'preflight')
  self.assertEqual(r['status'],'V157_SAFE_STOP');self.assertIn('TLK_SHA_DRIFT',r['reason'])
 def test_preflight_symlink_protected(self):
  p=self.game/'lang'/'ru_RU'/'dialog.tlk';p.unlink();p.symlink_to(self.game/'WeiDU.log')
  r=v.run(self.game,self.work,'preflight');self.assertIn('FILE_UNSAFE',r['reason'])
 def test_game_backups_must_be_external(self):
  r=v.run(self.game,self.game/'backup','preflight');self.assertIn('BACKUP_MUST_BE_EXTERNAL',r['reason'])
 def test_text_source_mismatch_fails_closed(self):
  with patch.dict(v.MANIFEST,{'tlk_editorial_changes':[dict(x) for x in v.MANIFEST['tlk_editorial_changes']]}):
   v.MANIFEST['tlk_editorial_changes'][0]['existing_ru_exact']='tamper'
   self.assertIn('EDITORIAL_CONTENT_DRIFT',v.run(self.game,self.work,'preflight')['reason'])
 def test_target_set_mismatch_holds(self):
  with patch.dict(v.MANIFEST,{'tlk_editorial_changes':[dict(x) for x in v.MANIFEST['tlk_editorial_changes']][:-1]}):
   self.assertIn('MANIFEST_SCOPE_DRIFT',v.run(self.game,self.work,'preflight')['reason'])
 def test_tlk_patch_preserves_all_original_bytes_outside_10_table_entries(self):
  out=v.prepare_tlk(self.fixture,'dialog.tlk');self.assertTrue(out.startswith(b'TLK V1  '));self.assertGreater(len(out),len(self.fixture))
  n,start=v.load_tlk(out);z=bytearray(out[:len(self.fixture)])
  for row in v.MANIFEST['tlk_editorial_changes']:
   idx=row['strref'];p=v.HDR+v.ENTRY*idx+18
   self.assertEqual(v.row_text(out,idx,n,start),row['proposed_ru_exact'].encode('utf-8'))
   z[p:p+8]=self.fixture[p:p+8]
  self.assertEqual(bytes(z),self.fixture)
 def test_install_requires_exact_typing(self):
  with patch.object(v,'no_running_game'),patch('builtins.input',return_value=''):
   r=v.run(self.game,self.work,'install')
  self.assertEqual(r['status'],'V157_SAFE_STOP');self.assertIn('TYPED_APPROVAL_REQUIRED',r['reason'])
  self.assertEqual(self.sha('dialog.tlk'),v.digest(self.fixture))
 def test_install_and_guarded_rollback(self):
  with patch.object(v,'no_running_game'),patch('builtins.input',return_value=v.INSTALL_TOKEN):
   a=v.run(self.game,self.work,'install')
  self.assertEqual(a['status'],'V157_10_TLK_INSTALLED_AWAITING_GAMEPLAY')
  s=v.read_state(self.work);self.assertEqual(s['status'],'INSTALLED')
  for name in v.TLKS:self.assertEqual(self.sha(name),s['installed_sha256'][name])
  self.assertEqual(v.run(self.game,self.work,'preflight')['status'],'HOLD_STATE_ALREADY_ACTIVE')
  with patch.object(v,'no_running_game'),patch('builtins.input',return_value=v.ROLLBACK_TOKEN):
   b=v.run(self.game,self.work,'rollback')
  self.assertEqual(b['status'],'V157_GUARDED_ROLLBACK_DONE')
  for name in v.TLKS:self.assertEqual(self.sha(name),v.digest(self.fixture))
 def test_rollback_stops_on_weidu_log_drift(self):
  with patch.object(v,'no_running_game'),patch('builtins.input',return_value=v.INSTALL_TOKEN):self.assertIn('INSTALLED',v.run(self.game,self.work,'install')['status'])
  (self.game/'WeiDU.log').write_bytes(b'DRIFT');s=v.read_state(self.work)
  with patch.object(v,'no_running_game'),patch('builtins.input',return_value=v.ROLLBACK_TOKEN):r=v.run(self.game,self.work,'rollback')
  self.assertIn('WEIDU_DRIFT',r['reason']);self.assertEqual(s['status'],'INSTALLED')
 def test_rollback_stops_on_tlk_modified_after_install(self):
  with patch.object(v,'no_running_game'),patch('builtins.input',return_value=v.INSTALL_TOKEN):self.assertIn('INSTALLED',v.run(self.game,self.work,'install')['status'])
  p=self.game/'lang'/'ru_RU'/'dialog.tlk';p.write_bytes(p.read_bytes()+b'CHANGED')
  with patch.object(v,'no_running_game'),patch('builtins.input',return_value=v.ROLLBACK_TOKEN):r=v.run(self.game,self.work,'rollback')
  self.assertIn('ROLLBACK_LAST_ONLY_SHA_DRIFT',r['reason'])
 def test_status_uninstalled(self):self.assertEqual(v.run(self.game,self.work,'status')['status'],'V157_NOT_INSTALLED')
 def test_no_game_files_created_during_preflight(self):
  b=set(p.relative_to(self.game) for p in self.game.rglob('*'))
  v.run(self.game,self.work,'preflight')
  a=set(p.relative_to(self.game) for p in self.game.rglob('*'))
  self.assertEqual(a,b)
 def test_backup_sha_persisted_after_install(self):
  with patch.object(v,'no_running_game'),patch('builtins.input',return_value=v.INSTALL_TOKEN):v.run(self.game,self.work,'install')
  state=v.read_state(self.work);backup=Path(state['backup_dir'])
  for name in v.TLKS:self.assertEqual(v.file_sha(backup/name),v.digest(self.fixture))
 def test_incomplete_state_stops(self):
  v.write_atomic_json(v.state_file(self.work),{'schema':v.SCHEMA,'status':'PREPARING'})
  self.assertEqual(v.run(self.game,self.work,'preflight')['status'],'HOLD_STATE_ALREADY_ACTIVE')
if __name__=='__main__':unittest.main(verbosity=2)
