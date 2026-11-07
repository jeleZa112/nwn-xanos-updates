"""Extra source-only regression tests for BGXAI 041. No EET installation."""
import pathlib, struct, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]

class RuntimeSemantics(unittest.TestCase):
    def test_no_animated_or_force_spell(self):
        text=(ROOT/'BGX41/toggle_icon.baf').read_text()
        self.assertNotIn('ReallyForceSpellRES(',text)
        self.assertNotIn('ReallyForceSpell(',text)
        self.assertEqual(text.count('ApplySpellRES("BGX41ON",Myself)'),2)
        self.assertEqual(text.count('ApplySpellRES("BGX41OF",Myself)'),1)
    def test_f_toggle_compatible_with_040(self):
        text=(ROOT/'BGX41/toggle_icon.baf').read_text()
        self.assertEqual(text.count('HotKey(F)'),2)
        self.assertEqual(text.count('  Global("BGX38_GUARD","LOCALS",0)'),1)
        self.assertEqual(text.count('  Global("BGX38_GUARD","LOCALS",1)'),2)
        self.assertEqual(text.count('SetGlobalTimer("BGX38_KEY_CD","LOCALS",2)'),2)
        self.assertEqual(text.count('DisplayStringHead(Myself,@'),2)
    def test_on_off_effects_source_ownership(self):
        on=(ROOT/'BGX41/BGX41ON.SPL').read_bytes()
        off=(ROOT/'BGX41/BGX41OF.SPL').read_bytes()
        self.assertEqual(on[:8],b'SPL V1  ')
        self.assertEqual(off[:8],b'SPL V1  ')
        for data,ops in [(on,[321,142]),(off,[321])]:
            off_fx=struct.unpack_from('<I',data,0x6a)[0]
            n=struct.unpack_from('<H',data,0x90)[0]
            self.assertEqual([struct.unpack_from('<H',data,off_fx+48*i)[0] for i in range(n)],ops)
            first=data[off_fx:off_fx+48]
            self.assertEqual(first[0x14:0x1c].rstrip(b'\x00'),b'BGX41ON')
            self.assertEqual(first[0x08:0x0c],b'\0'*4)
            for i in range(n):
                self.assertEqual(data[off_fx+48*i+0x12:off_fx+48*i+0x14],bytes([100,0]))
        self.assertEqual(struct.unpack_from('<I',on,0xd2)[0],30000)
    def test_expected_weiDU_dynamic_patch(self):
        tp2=(ROOT/'setup-BGX41.tp2').read_text()
        self.assertIn('WRITE_LONG 0xd2 icon',tp2)
        self.assertIn('COUNT_2DA_ROWS 3 count',tp2)
        self.assertIn('READ_2DA_ENTRY (count - 1) 0 3 icon',tp2)
        self.assertNotIn('COPY ~BGXAI',tp2)
    def test_no_live_game_paths(self):
        text=(ROOT/'BGX41/toggle_icon.baf').read_text()
        self.assertNotIn('C:\\Games\\',text)
        self.assertNotIn('SetGlobal("BGX38_GUARD","GLOBAL"',text)

if __name__=='__main__':unittest.main()
