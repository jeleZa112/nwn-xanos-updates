"""V157 one-release invariants; no live game, no user writes."""
import base64, hashlib, importlib.util, pathlib, zlib, unittest
ROOT=pathlib.Path(__file__).resolve().parent
P=ROOT/'v157_combined.py'
B=ROOT/'v157_bulk_guarded.py'
BASE_SHA='db636cad123194092b248ca4d073ab448c16c9801bb7879ce0c5d68b0eafb1c4'
PIN_SHA='96fb55e299f5986413504115a169572380749e67b9bbe0cd3038866d29e1bc83'

def sha(x):return hashlib.sha256(x).hexdigest()
class V157Combined(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  spec=importlib.util.spec_from_file_location('v157_combined',P)
  cls.m=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.m)
 def test_exact_published_module(self):self.assertEqual(sha(P.read_bytes().replace(b'\r\n',b'\n')),PIN_SHA)
 def test_v154_prefix_unchanged(self):
  data=P.read_bytes().replace(b'\r\n',b'\n');prefix=data.split(b'# V157 additive, one-CMD-only bulk editorial entry.')[0]
  self.assertEqual(sha(prefix[:-1]),BASE_SHA)
 def test_bundled_v157_matches_separate_authoritative_source(self):
  dec=zlib.decompress(base64.b64decode(self.m._V157_BLOB))
  self.assertEqual(dec,B.read_bytes().replace(b'\r\n',b'\n'))
 def test_v154_legacy_invalid_mode_unchanged(self):
  self.assertEqual(self.m.run('invalid',ROOT,ROOT.parent)['status'],'V153_BAD_ACTION_HOLD')
 def test_v157_preflight_game_missing_safe_stop(self):
  result=self.m.run('bulk_preflight',ROOT,ROOT.parent)
  self.assertEqual(result['status'],'V157_SAFE_STOP');self.assertEqual(result['game_files_written'],0)
 def test_v154_console_parser_preserved(self):
  data=b'INFO: LPRINT: BG_EET_RU_V150_RAW\t2\t1\t101\ttext\n'
  r=self.m._v154_parse_console(data)
  self.assertIn('raw_sample_count_capped',r)
if __name__=='__main__':unittest.main(verbosity=2)
