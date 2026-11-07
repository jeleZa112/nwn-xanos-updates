import unittest,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import build_assets as a

class BGXAI041(unittest.TestCase):
 def test_bam_signature(self):
  b=a.icon_bam()
  self.assertEqual(b[:8],b'BAM V1  ')
  self.assertEqual(len(b),1210)
  f,c,idx,fo,po,lo=struct.unpack_from('<HBBIII',b,8)
  self.assertEqual((f,c,idx,fo,po,lo),(1,1,0,24,40,1064))
  self.assertEqual(struct.unpack_from('<H',b,lo)[0],0)
  w,h,x,y,dat=struct.unpack_from('<HHhhI',b,fo)
  self.assertEqual((w,h,x,y),(12,12,6,6))
  self.assertTrue(dat&0x80000000)
  self.assertEqual(dat&0x7fffffff,1066)
  self.assertEqual(len(b[1066:]),144)
 def test_icon_palette_and_transparency(self):
  b=a.icon_bam()
  self.assertEqual(b[40:44],bytes((0,255,0,0)))
  self.assertGreater(b[1066:].count(0),0)
  self.assertGreater(b[1066:].count(3),0)
 def test_spells_are_isolated(self):
  a.main()
  on=(ROOT/'BGX41/BGX41ON.SPL').read_bytes()
  off=(ROOT/'BGX41/BGX41OF.SPL').read_bytes()
  for file,count in [(on,2),(off,1)]:
   self.assertEqual(file[:8],b'SPL V1  ')
   self.assertEqual(struct.unpack_from('<I',file,0x64)[0],0x72)
   self.assertEqual(struct.unpack_from('<H',file,0x68)[0],1)
   self.assertEqual(struct.unpack_from('<I',file,0x6a)[0],0x9a)
   self.assertEqual(struct.unpack_from('<H',file,0x72+0x1e)[0],count)
  self.assertEqual((struct.unpack_from('<H',on,0x9a)[0],struct.unpack_from('<H',on,0x9a+48)[0]),(321,142))
  self.assertEqual(struct.unpack_from('<I',on,0xd2)[0],30000)
  self.assertEqual(struct.unpack_from('<H',off,0x9a)[0],321)
  self.assertEqual(on[0x9a+20:0x9a+20+7],b'BGX41ON')
  self.assertEqual(off[0x9a+20:0x9a+20+7],b'BGX41ON')
 def test_baf_toggles_existing_guard(self):
  b=(ROOT/'BGX41/toggle_icon.baf').read_text()
  self.assertEqual(b.count('HotKey(F)'),2)
  self.assertEqual(b.count('SetGlobal("BGX38_GUARD","LOCALS",1)'),1)
  self.assertEqual(b.count('SetGlobal("BGX38_GUARD","LOCALS",0)'),1)
  self.assertEqual(b.count('ApplySpellRES("BGX41ON",Myself)'),2)
  self.assertEqual(b.count('ApplySpellRES("BGX41OF",Myself)'),1)
  self.assertEqual(b.count('SetGlobalTimer("BGX38_KEY_CD","LOCALS",2)'),2)
  self.assertEqual(b.count('DisplayStringHead'),2)
  self.assertEqual(b.count('\nEND\n'),3)
 def test_tp2_dynamic_icon_index(self):
  t=(ROOT/'setup-BGX41.tp2').read_text()
  self.assertIn('COUNT_2DA_ROWS 3 count',t)
  self.assertIn('READ_2DA_ENTRY (count - 1) 0 3 icon',t)
  self.assertIn('WRITE_LONG 0xd2 icon',t)
  self.assertIn('EXTEND_TOP ~BDDEFAI.BCS~',t)
  self.assertNotIn('COPY ~BDDEFAI.BCS~',t)
  self.assertEqual(t.count('APPEND ~STATDESC.2DA~'),1)
 def test_file_names_resrefs(self):
  self.assertLessEqual(len(a.ICON),8)
  self.assertLessEqual(len(a.SPELL_ON),8)
  self.assertLessEqual(len(a.SPELL_OFF),8)
  self.assertNotEqual(a.SPELL_ON,a.SPELL_OFF)

if __name__=='__main__':unittest.main()
