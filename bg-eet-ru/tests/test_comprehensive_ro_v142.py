"""BG_EET_RU V142 release integration/ZIP adversarial tests; no game files altered.

Tests the published one-file updater in isolated temp directories, not actual game.
"""
from __future__ import annotations
import hashlib,json,struct,tempfile,unittest,warnings,zipfile
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
CMD=BASE/'onefile'/'BG_EET_RU_UPDATE.cmd'
REL=BASE/'onefile'/'release.json'
NAT=BASE/'native-correlation'

def sha(b):return hashlib.sha256(b).hexdigest()

class FullRelease(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.cmd=CMD.read_bytes()
  cls.rel=json.loads(REL.read_text('utf8'))
  cls.ns={'__name__':'v142_complex_test_not_main','__file__':str(CMD)}
  exec(compile(cls.cmd.split(b'\n',1)[1],str(CMD),'exec'),cls.ns)

 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='BG_EET_RU_V142_COMPREHENSIVE_')
  self.addCleanup(self.tmp.cleanup)
  self.root=Path(self.tmp.name)
  self.game=self.root/'game';self.game.mkdir()
  self.ext=self.root/'outside';self.ext.mkdir()
  self.zip=self.ext/'SEND_TO_CHATGPT_BG_EET_RU.zip'
  with zipfile.ZipFile(self.zip,'w',zipfile.ZIP_STORED) as z:
   z.writestr('67_V136_LIVE_JIT_TARGET_RO.json','{"old":136}')
   z.writestr('68_V140_EXACT_CALLEE_RO.json','{"old":140}')
   z.writestr('00_PRESERVED.json','{"source":"original"}')

 def report(self):return {'schema':'TEST_V142','status':'SOURCE_ONLY_HOLD','native_hooks_installed':False,'game_files_written':0,'gameplay_verified':False}
 def read(self):
  with zipfile.ZipFile(self.zip) as z:
   self.assertIsNone(z.testzip())
   self.assertEqual(len(z.namelist()),len(set(z.namelist())))
   return {n:z.read(n) for n in z.namelist()}

 def test_release_exact_sha_and_bounds(self):
  self.assertIn(self.rel['version'],(142,144,146))
  self.assertFalse(self.rel['game_writes_allowed'])
  self.assertEqual(sha(self.cmd),self.rel['sha256'])
  self.assertLessEqual(len(self.cmd),750000)
  self.assertEqual(self.ns['SELF_VERSION'],self.rel['version'])

 def test_native_sources_hash_pinned_and_zip_single_menu(self):
  for v,filename in ((133,'v133_live_hit_inventory_ro.py'),(self.rel['version'],'v146_ro.py' if self.rel['version']==146 else ('v144_ro.py' if self.rel['version']==144 else 'v142_ro.py'))):
   blob=(NAT/filename).read_bytes().replace(b'\r\n',b'\n')
   self.assertEqual(sha(blob),self.ns['V'+str(v)+'_PIN'])
   self.assertIn('bg-eet-ru/native-correlation/'+filename,self.ns['V'+str(v)+'_URL'])
  self.assertIn(b"if a=='9':return v133_audit(game,WORKDIR/REPORT_NAME,True)",self.cmd)
  self.assertIn(b"70_V144_DOWNSTREAM_SOURCE_RO.json" if self.rel["version"]==144 else b"69_V142_MESSAGE_DELIVERY_RO.json",self.cmd)

 def test_same_zip_historical_preservation_and_no_duplicates(self):
  before=self.read();payload=self.report()
  self.assertTrue(self.ns['v116_zip'](self.game,self.zip,payload,'69_V142_MESSAGE_DELIVERY_RO.json'))
  after=self.read()
  self.assertEqual(set(after)-set(before),{'69_V142_MESSAGE_DELIVERY_RO.json'})
  for k,v in before.items():self.assertEqual(after[k],v)
  self.assertEqual(json.loads(after['69_V142_MESSAGE_DELIVERY_RO.json']),payload)
  self.assertEqual(list(self.game.iterdir()),[])

 def test_zip_idempotence_no_unnecessary_rewrite(self):
  self.ns['v116_zip'](self.game,self.zip,self.report(),'69_V142_MESSAGE_DELIVERY_RO.json')
  h=sha(self.zip.read_bytes())
  self.assertFalse(self.ns['v116_zip'](self.game,self.zip,self.report(),'69_V142_MESSAGE_DELIVERY_RO.json'))
  self.assertEqual(sha(self.zip.read_bytes()),h)

 def test_preexisting_v142_report_replaces_only_its_own_entry(self):
  self.ns['v116_zip'](self.game,self.zip,{'status':'PREVIOUS'},'69_V142_MESSAGE_DELIVERY_RO.json')
  self.ns['v116_zip'](self.game,self.zip,self.report(),'69_V142_MESSAGE_DELIVERY_RO.json')
  out=self.read()
  self.assertEqual(len(out),4)
  self.assertEqual(json.loads(out['69_V142_MESSAGE_DELIVERY_RO.json']),self.report())
  self.assertEqual(json.loads(out['68_V140_EXACT_CALLEE_RO.json']),{'old':140})

 def test_duplicate_member_guard_does_not_modify_zip(self):
  with warnings.catch_warnings():
   warnings.simplefilter('ignore',UserWarning)
   with zipfile.ZipFile(self.zip,'a') as z:z.writestr('00_PRESERVED.json','{"collision":true}')
  h=sha(self.zip.read_bytes())
  with self.assertRaisesRegex(ValueError,'V116_ZIP_CRC_OR_DUPLICATE'):
   self.ns['v116_zip'](self.game,self.zip,self.report(),'69_V142_MESSAGE_DELIVERY_RO.json')
  self.assertEqual(sha(self.zip.read_bytes()),h)
  self.assertEqual(list(self.game.iterdir()),[])

 def test_bad_crc_guard_does_not_modify_zip(self):
  with zipfile.ZipFile(self.zip) as z:
   i=z.getinfo('00_PRESERVED.json')
   pos=i.header_offset+30+len(i.filename.encode('utf8'))+len(i.extra)
  b=bytearray(self.zip.read_bytes());b[pos]^=0x02;self.zip.write_bytes(b)
  h=sha(self.zip.read_bytes())
  with self.assertRaises(ValueError):
   self.ns['v116_zip'](self.game,self.zip,self.report(),'69_V142_MESSAGE_DELIVERY_RO.json')
  self.assertEqual(sha(self.zip.read_bytes()),h)
  self.assertEqual(list(self.game.iterdir()),[])

 def test_report_must_be_outside_game(self):
  dest=self.game/'forbidden.zip'
  with zipfile.ZipFile(dest,'w') as z:z.writestr('00','preserved')
  h=sha(dest.read_bytes())
  with self.assertRaisesRegex(RuntimeError,'STOP:'):
   self.ns['v116_zip'](self.game,dest,self.report(),'69_V142_MESSAGE_DELIVERY_RO.json')
  self.assertEqual(sha(dest.read_bytes()),h)

 def test_v142_report_is_never_gameplay_verified(self):
  # The source-only release must not claim the native bridge/row correlation is installed.
  source=(NAT/'v142_ro.py').read_text('utf8')
  for token in ('message_queue_to_combatlog_proven',"'game_files_written':0","'native_hooks_installed':False", "'safe_to_install':False"):
   self.assertIn(token,source)
  for forbidden in ('WriteProcessMemory(', 'CreateRemoteThread(', 'VirtualProtectEx(', 'EEex_JITAt(', 'EEex_HookBefore('):
   self.assertNotIn(forbidden,source)
  self.assertFalse(self.rel['game_writes_allowed'])

if __name__=='__main__':unittest.main(verbosity=2)
