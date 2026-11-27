"""V158 upgrade contract: no changes in legacy source, only status v158 route.

This test never reads or modifies user game files; no WeiDU invocation.
"""
from __future__ import annotations
import hashlib
import pathlib
import re
import base64
import zlib
import unittest

R=pathlib.Path(__file__).resolve().parents[1]
OLD=R/'bulk-v157'/'v157_combined.py'
NEW=R/'bulk-v158'/'v158_combined.py'
SRC=R/'bulk-v158'/'v158_banter_live_ro.py'
UPDATER=R/'onefile'/'BG_EET_RU_UPDATE.cmd'
RELEASE=R/'onefile'/'release.json'
OLD_SHA='96fb55e299f5986413504115a169572380749e67b9bbe0cd3038866d29e1bc83'
NEW_SHA='413764adb10af5cc7719bec7840e8a771d96e14181ed5152ff9ffb433d42432a'
SRC_SHA='e690295ed4b6fa7a29c17b8fd40f319c58713fb96f983b89ca56d8f9cf32ffea'
UPDATER_SHA='388e5eb48228637ec398351273804373ee08d35ecade18021a7e5d559afee866'


def lf(b:bytes)->bytes:return b.replace(b'\r\n',b'\n')
def sh(b:bytes)->str:return hashlib.sha256(b).hexdigest()

class V158Contract(unittest.TestCase):
 def test_source_pins(self):
  a,b,s=map(lambda p:lf(p.read_bytes()),(OLD,NEW,SRC))
  self.assertEqual(sh(a),OLD_SHA);self.assertEqual(sh(b),NEW_SHA);self.assertEqual(sh(s),SRC_SHA)
  self.assertTrue(b.startswith(a))
 def test_zlib_embedding_verifies_original(self):
  text=lf(NEW.read_bytes()).decode('utf-8')
  m=re.search(r"^_V158_RO_Z='([A-Za-z0-9+/=]+)'$",text,re.M)
  self.assertIsNotNone(m)
  self.assertEqual(zlib.decompress(base64.b64decode(m.group(1))),lf(SRC.read_bytes()))
 def test_legacy_dispatch_unchanged(self):
  ns={'__name__':'bg_eet_ru_v158_test'}
  exec(compile(lf(NEW.read_bytes()),'<v158>', 'exec'),ns)
  old=ns['_V157_RUN_UNCHANGED']
  try:
   ns['_V157_RUN_UNCHANGED']=lambda *args,**kwargs:{'status':'LEGACY_VERIFIED','params':args[0]}
   for mode in ('preflight','status','install','rollback','capture','bulk_preflight','bulk_install','bulk_rollback'):
    r=ns['run'](mode,'Z:/missing','Z:/external',allow_non_windows_test=True)
    self.assertEqual(r,{'status':'LEGACY_VERIFIED','params':mode})
   r=ns['run']('bulk_status','Z:/missing','Z:/external')
   self.assertEqual(r['schema'],'BG_EET_RU_V158_ONE_BATCH_CURRENT_PROVENANCE')
   self.assertEqual(r['v157_status']['status'],'LEGACY_VERIFIED')
   self.assertEqual(r['status'],'V158_READONLY_SOURCE_HOLD')
   self.assertEqual(r['game_files_written'],0)
   self.assertFalse(r['install_allowed'])
  finally:ns['_V157_RUN_UNCHANGED']=old
 def test_one_updater_manifest_size_and_reports(self):
  import json
  data=UPDATER.read_bytes()
  # Python -x code is UTF-8 encoded and LF normalized by Git checkout on Linux/Windows.
  norm=lf(data)
  self.assertLessEqual(len(norm),750000)
  self.assertEqual(sh(norm),UPDATER_SHA)
  self.assertIn(b'SELF_VERSION = 158',norm)
  for key in (b'73_V153_GUARDED_OBSERVER.json',b'74_V154_CONSOLE_CAPTURE_RO.json',
              b'75_V157_BULK_ONE_BATCH.json',b'76_V158_BANTER_LIVE_RO.json'):
   self.assertIn(key,norm)
  m=json.loads(RELEASE.read_text(encoding='utf-8'))
  self.assertEqual(m['version'],158);self.assertEqual(m['sha256'],UPDATER_SHA)
  self.assertFalse(m.get('default_game_writes_allowed'))

if __name__=='__main__':unittest.main(verbosity=2)
