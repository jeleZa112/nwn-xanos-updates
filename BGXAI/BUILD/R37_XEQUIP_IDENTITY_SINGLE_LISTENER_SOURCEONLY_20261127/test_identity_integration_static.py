import pathlib,re,unittest
ROOT=pathlib.Path(__file__).resolve().parents[3]
BASE=ROOT/'BGXAI/BUILD/R37_INVENTORY16_SINGLE_CALLBACK_SOURCEONLY_20261126/M_BGXR27_R37_INV3_SOURCE_ONLY.lua'
NEW=ROOT/'BGXAI/BUILD/R37_XEQUIP_IDENTITY_SINGLE_LISTENER_SOURCEONLY_20261127/M_BGXR27_R37_INV3_IDENTITY_SOURCE_ONLY.lua'
GATE=ROOT/'BGXAI/BUILD/WEAPON_XEQUIP_IDENTITY_RO_V1_20261127/BGXAI_XEQUIP_IDENTITY_RO_V1.lua'
NAMES=('CORE','JSON','CAPTURE','EMIT')

def block(n):
 return re.compile(rb'-- BEGIN BGXAI_IDV1_'+n.encode()+rb'\n.*?-- END BGXAI_IDV1_'+n.encode()+rb'\n', re.S)
class Static(unittest.TestCase):
 def test_paths_exist(self):
  for p in (BASE,NEW,GATE):self.assertTrue(p.is_file(),str(p))
 def test_legacy_bytes_unmodified(self):
  b=BASE.read_bytes();s=NEW.read_bytes()
  for n in NAMES:
   pat=block(n)
   self.assertEqual(len(pat.findall(s)),1,n)
   s=pat.sub(b'',s)
  self.assertEqual(s,b,'all existing R37 INV3 bytes preserved beyond marked additions')
 def test_embedded_identity_core_exact(self):
  s=NEW.read_bytes();identity=GATE.read_bytes()
  payload=block('CORE').search(s).group(0)
  self.assertIn(identity,payload,'identity source not the tested module')
 def test_one_listener_and_old_messages(self):
  a=BASE.read_text();b=NEW.read_text()
  self.assertEqual(a.count('EEex_Action_AddSpriteStartedActionListener'),b.count('EEex_Action_AddSpriteStartedActionListener'))
  for marker in ('[BGXR27]','[BGXR37]','[BGXINV3]'):
   self.assertEqual(a.count(marker),b.count(marker))
  self.assertIn("ports.emitString('[BGXID] '..idline)",b)
  self.assertIn('result.identityV1Status=',b)
 def test_no_new_action_commands(self):
  b=NEW.read_text()
  clean='\n'.join(x.split('--',1)[0] for x in b.splitlines())
  for pat in [r'\bXEquipItem\s*\(',r'\bClearActions\s*\(',r'\bFillSlot\s*\(',
              r'\bSelectWeaponAbility\s*\(',r'\bSetGlobal\s*\(',r'\bActionOverride\s*\(']:
   self.assertNotRegex(clean,pat)
  self.assertIn('"armAuthorized":false',b)
 def test_saved_game_not_in_build_tree(self):
  project=ROOT/'BGXAI/BUILD/R37_XEQUIP_IDENTITY_SINGLE_LISTENER_SOURCEONLY_20261127'
  self.assertFalse(any(f.suffix.lower()=='.gam' for f in project.rglob('*') if f.is_file()))
if __name__=='__main__':unittest.main(verbosity=2)