"""Verify surgical 064 source mutation against a representative exact receiver excerpt.

Real entire-source pin is separately verified against 056+061 SHA and the
candidate file on GitHub. Test fixture is not represented as installed source.
"""
import unittest
from pathlib import Path
import BGXAI64_PATCH as p

BASE=Path(__file__).with_name('BGX64_BRIDGE_PREPARE_NATIVE.lua')

def fixture():
    candidate_receiver=BASE.read_text(encoding='utf-8')
    # B.prepare below is verbatim verified against GitHub 064 candidate fragment.
    original_receiver=candidate_receiver
    # Remove precisely the three changes that belong in B.prepare in 064.
    for a,b in reversed(p.REPLACEMENTS[1:]):
        if original_receiver.count(b)!=1:
            raise AssertionError('fixture failed reverse of anchor')
        original_receiver=original_receiver.replace(b,a,1)
    original='P.version = "0.3.22-056-ACTIVE-GUARD-OPTIN"\n'+original_receiver
    target='P.version = "0.3.29-064-061-SAME-AREA-GUARD-SOURCE"\n'+candidate_receiver
    return original.encode(),target.encode()

class SurgicalPatchTests(unittest.TestCase):
 def test_exact_reversible_four_anchor_patch(self):
    src,dst=fixture()
    out,proof=p.build_candidate(src,baseline_sha=p.digest(src),candidate_sha=p.digest(dst))
    self.assertEqual(out,dst)
    self.assertEqual(proof['changed_anchors'],4)
    self.assertTrue(proof['other_code_unchanged'])
 def test_real_061_sha_required_in_production(self):
    src,_=fixture()
    with self.assertRaisesRegex(ValueError,'SOURCE_061_SHA256_MISMATCH'):
        p.build_candidate(src)
 def test_real_064_sha_required_in_production(self):
    src,_=fixture()
    with self.assertRaisesRegex(ValueError,'CANDIDATE_064_SHA256_MISMATCH'):
        p.build_candidate(src,baseline_sha=p.digest(src))
 def test_wrong_type_rejected(self):
    with self.assertRaises(TypeError): p.build_candidate('text')
 def test_changed_anchor_blocks_patch(self):
    src,_=fixture();src=src.replace(b'local yy=safe',b'local other=safe',1)
    with self.assertRaisesRegex(ValueError,'PATCH_ANCHOR_3_DRIFT'):
        p.build_candidate(src,baseline_sha=p.digest(src),candidate_sha=None)
 def test_duplicate_anchor_blocks_patch(self):
    src,_=fixture();src+=b'\n'+p.REPLACEMENTS[1][0].encode()
    with self.assertRaisesRegex(ValueError,'PATCH_ANCHOR_2_DRIFT'):
        p.build_candidate(src,baseline_sha=p.digest(src),candidate_sha=None)
 def test_duplicate_bridge_blocks_patch(self):
    src,_=fixture();src+=b'\nfunction B.prepare(advisory) end\n'
    with self.assertRaisesRegex(ValueError,'BRIDGE_ENTRY_DRIFT'):
        p.build_candidate(src,baseline_sha=p.digest(src),candidate_sha=None)
 def test_preserves_all_request_writes(self):
    src,dst=fixture()
    out,_=p.build_candidate(src,baseline_sha=p.digest(src),candidate_sha=None)
    self.assertEqual(out.count(b'BGX52_REQ_SLOT'),src.count(b'BGX52_REQ_SLOT'))
    self.assertEqual(out.count(b'set("BGX52_REQ_SLOT",slot)'),1)
    self.assertEqual(out,dst)
 def test_malformed_or_binary_refused(self):
    with self.assertRaisesRegex(ValueError,'SOURCE_061_NOT_UTF8'):
        p.build_candidate(b'\xff',baseline_sha=p.digest(b'\xff'),candidate_sha=None)
 def test_pins_not_placeholders(self):
    self.assertEqual(len(p.PIN_061),64)
    self.assertEqual(len(p.PIN_064),64)
    self.assertNotEqual(p.PIN_061,p.PIN_064)
 def test_no_game_fs_or_weidu_modules_in_patcher(self):
    source=Path(p.__file__).read_text()
    for bad in ('subprocess','os.system','shutil','setup-BGX64.exe','--force-install','WeiDU.log','ClearActions(', 'AttackReevaluate('):
      self.assertNotIn(bad,source)

if __name__=='__main__': unittest.main()
