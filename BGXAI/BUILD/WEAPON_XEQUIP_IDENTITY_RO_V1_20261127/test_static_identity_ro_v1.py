import pathlib,re,unittest
ROOT=pathlib.Path(__file__).resolve().parent
SRC=ROOT/'BGXAI_XEQUIP_IDENTITY_RO_V1.lua'
class Static(unittest.TestCase):
 def test_no_game_mutation_api(self):
  src=SRC.read_text(encoding='utf-8')
  # Remove comments before checking actual calls.
  code='\n'.join(l.split('--',1)[0] for l in src.splitlines())
  for pat in [r'\bXEquipItem\s*\(',r'\bSetGlobal\s*\(',r'\bActionOverride\s*\(',r'\bClearActions\s*\(',r'\bStop\s*\(',r'\bFillSlot\s*\(',r'\bEEex_Action_AddSpriteStartedActionListener\s*\(',r'\bEEex_.*[Ww]rite']:
   self.assertNotRegex(code,pat)
 def test_no_arm_or_true_proof(self):
  src=SRC.read_text(encoding='utf-8')
  self.assertIn('armAuthorized=false',src)
  self.assertIn('sessionMatchesSavedGamVerified=false',src)
  self.assertIn('safeActionBoundaryVerified=false',src)
 def test_exact_canonical_candidate_and_full_scan(self):
  src=SRC.read_text(encoding='utf-8')
  self.assertIn('portraitIndex=1,classRaw=3,sourceSlot=20,targetSlot=35',src)
  self.assertIn("resref='STAF01',flagsRaw=1,charges={0,0,0}",src)
  self.assertIn('for slot=0,38 do',src)
  self.assertIn('if slot~=10',src)
 def test_no_private_save_committed(self):
  self.assertFalse(any(p.suffix.lower()=='.gam' for p in ROOT.iterdir()))
 def test_no_unauthorized_install_code(self):
  src=SRC.read_text(encoding='utf-8')
  self.assertNotIn('Weidu',src)
  self.assertNotIn('WeiDU(',src)
if __name__=='__main__':unittest.main(verbosity=2)