"""Repository contract checks for V159; no game writes."""
from pathlib import Path
import unittest, hashlib, re, json, base64, zlib, ast
ROOT=Path(__file__).resolve().parent.parent
P=Path(__file__).resolve().parent
UPDATER=ROOT/'onefile'/'BG_EET_RU_UPDATE.cmd'
RELEASE=ROOT/'onefile'/'release.json'
OLD=ROOT/'bulk-v158'/'v158_combined.py'
COMBINED=P/'v159_combined.py'
MODULE=P/'v159_tlk_bulk_guarded.py'
MANIFEST=P/'V159_INSTALL_MANIFEST.json'

# GitHub checkout on Windows often uses CRLF, pinned immutable RAW GitHub sources are LF.
def raw(p):return p.read_bytes().replace(b'\r\n',b'\n')
def sha(b):return hashlib.sha256(b).hexdigest()
class Contract(unittest.TestCase):
 def test_01_V158_byte_prefix_preserved(self):
  old=raw(OLD);new=raw(COMBINED)
  self.assertTrue(new.startswith(old))
  self.assertEqual(sha(old),'413764adb10af5cc7719bec7840e8a771d96e14181ed5152ff9ffb433d42432a')
 def test_02_combined_SHA_and_source_Z(self):
  b=raw(COMBINED)
  self.assertEqual(sha(b),'f5e3b527d3ed66dc8a5db847effb304c7d06d0d6a91f994519203901544e6bcd')
  self.assertLess(len(b),60001)
  z=re.search(rb"_V159_BULK_Z='([^']+)'",b)
  self.assertIsNotNone(z)
  self.assertEqual(zlib.decompress(base64.b64decode(z.group(1))),raw(MODULE))
  ast.parse(b.decode('utf-8'))
 def test_03_exact_module_SHA(self):
  self.assertEqual(sha(raw(MODULE)),'4b58a3506bac76945439ac4ef98c1efb6a006bf939945662bf1bda5927a8b0f9')
 def test_04_release_matches_onefile(self):
  rel=json.loads(raw(RELEASE))
  self.assertEqual(rel['version'],159)
  self.assertEqual(rel['sha256'],sha(raw(UPDATER)))
  self.assertFalse(rel['default_game_writes_allowed'])
  self.assertFalse(rel['game_writes_allowed'])
  self.assertLessEqual(len(raw(UPDATER)),750000)
 def test_05_menu_and_report_entries(self):
  s=raw(UPDATER).decode('utf-8')
  self.assertIn("if a=='11':",s)
  self.assertIn("'batch159_' if b in ('5','6','7','8')",s)
  self.assertIn("v153_dispatch(game,('batch159_'",s)
  self.assertIn("r.read(60001)",s)
  for n in ('73_V153_GUARDED_OBSERVER.json','74_V154_CONSOLE_CAPTURE_RO.json','75_V157_BULK_ONE_BATCH.json','76_V158_BANTER_LIVE_RO.json','77_V159_BATCH.json'):
   self.assertIn(n,s)
  self.assertIn("V153_PIN='f5e3b527d3ed66dc8a5db847effb304c7d06d0d6a91f994519203901544e6bcd'",s)
 def test_06_manifest(self):
  j=json.loads(raw(MANIFEST))
  self.assertEqual(j['schema'],'BG_EET_RU_V159_CONTENT_MANIFEST_V1')
  self.assertEqual(len(j['tlk_editorial_changes']),16)
  self.assertEqual(len(set(x['strref'] for x in j['tlk_editorial_changes'])),16)
  self.assertEqual(j['expected_source_tlk_sha256']['dialog.tlk'],'8d61cd3805e450f4c09ec1c4c476e2ae5302a0cf2cb9d69f793d236389944b02')
  self.assertEqual(j['expected_source_tlk_sha256']['dialogf.tlk'],'795c07e88a6c4575201ec43cbd2ea730d045c501d48407d5c1df81f851a7e2e6')
 def test_07_status_forwarding_only(self):
  t=raw(COMBINED).decode('utf-8')
  self.assertIn("return _V158_RUN_UNCHANGED",t)
  self.assertIn("mode.startswith('batch159_')",t)
  self.assertEqual(t.count("_V158_RUN_UNCHANGED=run"),1)
if __name__=='__main__':unittest.main(verbosity=2)
