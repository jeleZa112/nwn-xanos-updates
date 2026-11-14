import io,unittest,zipfile,tempfile
from pathlib import Path
from audit_cre_071 import cre_head, scan, CORE_KIT_HINTS

def example(class_id=11,kit=0x40110000,flags=0,levels=(9,0,0)):
 import struct
 b=bytearray(0x2d4)
 b[0:8]=b'CRE V1.0'
 struct.pack_into('<I',b,0x10,flags)
 b[0x273]=class_id
 struct.pack_into('<I',b,0x244,kit)
 b[0x234:0x237]=bytes(levels)
 return bytes(b)

class Tests(unittest.TestCase):
 def test_shapeshifter_cre_vs_ids(self):
  x=cre_head(example())
  self.assertEqual(x['class_id'],11)
  self.assertEqual(x['kit_cre_raw'],0x40110000)
  self.assertEqual(x['kit_name_hint'],'SHAPESHIFTER')
  self.assertNotIn(0x4011,CORE_KIT_HINTS)
 def test_original_class_fighter_flag(self):
  x=cre_head(example(7,0,flags=1<<3,levels=(7,10,0)))
  self.assertEqual(x['old_class_hint'],'FIGHTER')
  self.assertTrue(x['has_dual_original_flag_hint'])
 def test_other_original_class_bits(self):
  for bit in range(3,9):
   self.assertTrue(cre_head(example(flags=1<<bit))['old_class_hint'])
 def test_unknown_old_class_ambiguous(self):
  x=cre_head(example(flags=(1<<3)|(1<<4)))
  self.assertIsNone(x['old_class_hint'])
  self.assertFalse(x['has_dual_original_flag_hint'])
 def test_unrelated_flags_not_dual(self):
  self.assertIsNone(cre_head(example(flags=0x400000))['old_class_hint'])
 def test_level_does_not_prove_dual_active(self):
  self.assertNotIn('old_active',cre_head(example(flags=1<<3,levels=(7,10,0))))
 def test_reject_short_and_wrong_version(self):
  self.assertIsNone(cre_head(b'CRE V1.0'))
  self.assertIsNone(cre_head(b'CRE V9.0'+b'\x00'*1000))
 def test_class_255_does_not_fail_parser_but_not_supported(self):
  self.assertEqual(cre_head(example(class_id=255))['class_id'],255)
 def test_no_intervention_in_archive(self):
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'private.zip'
   with zipfile.ZipFile(path,'w') as z:
    z.writestr('first.cre',example())
    z.writestr('second.cre',example(7,0,1<<3,(7,10,0)))
    z.writestr('third.cre',example(255,0))
    z.writestr('bad.cre',b'BAD!')
   before=path.read_bytes(); r=scan(path); after=path.read_bytes()
   self.assertEqual(before,after)
   self.assertEqual(r['stats']['cre_entries'],4)
   self.assertEqual(r['stats']['shapeshifter_raw'],1)
   self.assertEqual(r['stats']['single_original_class_bit_hint'],1)
   self.assertEqual(r['stats']['noncore_or_modded_class'],1)
   self.assertEqual(r['stats']['bad_header_or_unsupported_cre'],1)
   self.assertEqual(r['no_names_or_cre_bytes_exported'],True)

if __name__=='__main__':unittest.main()
