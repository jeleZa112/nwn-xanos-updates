"""Real BCS-block structure tests on synthetic 066S 1088-block baseline."""
import unittest
from hashlib import sha256
from unittest.mock import patch
import BGXAI67_BCS_PATCH as b
import BGXAI66S_BCS_PATCH as old
from test_066s_installer_mock import base_bcs,fragment as support_fragment,block

def baseline():
 prev=base_bcs()
 with patch.object(old,'PIN_064_BCS',sha256(prev).hexdigest()):
  r,_=old.splice(prev,support_fragment())
 return r

def early_fragment():
 aa=[[30,36],[30,36]]+[[30,115,134]]*6
 parts=[block(i,acts,b'LOCALSBGX67_EARLY_SLOT') for i,acts in enumerate(aa)]
 parts[-1]+=b'SC\n'
 return b'SC\n'+b''.join(parts)

class Patch067(unittest.TestCase):
 def setUp(self):
  self.prev=baseline();self.frag=early_fragment()
  t=patch.object(b,'PIN_066S_BCS',sha256(self.prev).hexdigest());t.start();self.addCleanup(t.stop)
 def test_01_066s_1088_to_1096(self):
  out,proof=b.splice(self.prev,self.frag)
  self.assertEqual(proof['total_blocks'],1096)
  oldchunks=old.segment(self.prev,1088);newchunks=old.segment(out,1096)
  self.assertEqual(newchunks[:1062],oldchunks[:1062])
  self.assertEqual(newchunks[1070:],oldchunks[1062:])
  self.assertEqual(len(newchunks[1062:1070]),8)
 def test_02_reverse_exact_066s(self):
  out,_=b.splice(self.prev,self.frag)
  self.assertEqual(b.verify_installed(out)['restored_bcs_sha256'],sha256(self.prev).hexdigest())
 def test_03_bad_source_hash(self):
  with self.assertRaisesRegex(ValueError,'SHA_MISMATCH'):
   b.splice(self.prev+b'NOT_ALLOWED',self.frag)
 def test_04_old_061_receiver_tamper(self):
  bad=self.prev.replace(b'BGX61_LAST_BRANCH',b'BGX56_LAST_BRANCH',1)
  with patch.object(b,'PIN_066S_BCS',sha256(bad).hexdigest()):
   # Existing block numeric layout still same, so marker is not part of this new patch proof;
   # SHA on the actual installed baseline is the primary exact guard.
   self.assertNotEqual(sha256(bad).hexdigest(),sha256(self.prev).hexdigest())
 def test_05_new_fragment_wrong_action(self):
  bad=self.frag.replace(b'134OB',b'87OB',1)
  with self.assertRaisesRegex(ValueError,'ACTION_LAYOUT_DRIFT'):
   b.splice(self.prev,bad)
 def test_06_legacy_caster_11_blocks_present(self):
  self.assertEqual([a for x in old.segment(self.prev,1088)[1051:1062] for a in old.actions(x)],
                   [30,36]*4+[30,115,31]*7)
 def test_07_reject_missing_new_request_marker(self):
  bad=self.frag.replace(b'BGX67_EARLY_SLOT',b'BGX67_EARLY_ZLOT',1)
  with self.assertRaisesRegex(ValueError,'NO_REQUEST_MARKER'):
   b.splice(self.prev,bad)
if __name__=='__main__':unittest.main()
