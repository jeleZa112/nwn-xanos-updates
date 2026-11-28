import importlib.util,struct,unittest
from pathlib import Path
P=Path("BGXAI/BUILD/WEAPON_SAVE_GAM_INVENTORY_RO_V1_20261126/BGXAI_GAM_INVENTORY_RO_V1.py")
spec=importlib.util.spec_from_file_location("ro",P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def make_cre(items=None):
 cre=bytearray(0x400)
 cre[:8]=b"CRE V1.0"
 slot_off=0x300;item_off=0x350
 struct.pack_into("<I",cre,0x2b8,slot_off)
 struct.pack_into("<I",cre,0x2bc,item_off)
 struct.pack_into("<I",cre,0x2c0,3)
 for i in range(40):struct.pack_into("<H",cre,slot_off+i*2,0xffff)
 struct.pack_into("<H",cre,slot_off+21*2,0)
 struct.pack_into("<H",cre,slot_off+9*2,1)
 struct.pack_into("<H",cre,slot_off+2*2,2)
 struct.pack_into("<H",cre,slot_off+38*2,1)
 struct.pack_into("<H",cre,slot_off+39*2,0)
 for i,rr in enumerate(("SW1H04","BOW05","SHLD03A")):
  o=item_off+i*20
  cre[o:o+8]=rr.encode().ljust(8,b"\0")
  struct.pack_into("<HHHI",cre,o+10,5+i,6+i,7+i,1+i)
 return bytes(cre)
def make_gam(cre=None,version=b"GAMEV2.0",npcidx=1):
 cre=cre or make_cre()
 header=bytearray(0xa4)
 header[:8]=version
 struct.pack_into("<I",header,0x20,0xa4)
 struct.pack_into("<I",header,0x24,1)
 npc=bytearray(0x160)
 struct.pack_into("<H",npc,2,npcidx)
 struct.pack_into("<I",npc,4,0xa4+0x160)
 struct.pack_into("<I",npc,8,len(cre))
 npc[0xc0:0xc6]=b"Khalid"
 return bytes(header)+bytes(npc)+cre
class TestGam(unittest.TestCase):
 def test_real_mapping_backpack_not_cre_index(self):
  out=m.parse(make_gam());a=out["partyMembers"][0]
  self.assertEqual(a["partyIndex"],1)
  self.assertEqual(a["sourceSlots18to33"][0]["resref"],"SW1H04")
  self.assertEqual(a["quickWeaponSlots35to38"][0]["resref"],"BOW05")
  self.assertEqual(a["topLevelSlots"][9]["resref"],"SHLD03A")
 def test_moded_resref_charset_aligns_exactly_with_existing_r3(self):
  # EET items can use mod namespaces, e.g. C#GRTOO0. The original
  # R3 RESREF allowlist already accepts ASCII letters/digits/_/#/-.
  self.assertEqual(m.checkedres(b'C#GRTOO0'),'C#GRTOO0')
  self.assertEqual(m.checkedres(b'C-ITEM01'),'C-ITEM01')
  self.assertEqual(m.checkedres(b'sw1h04\0\0'),'SW1H04')
  c=bytearray(make_cre())
  c[0x350:0x358]=b'C#GRTOO0'
  c[0x350+20:0x350+28]=b'C-ITEM01'
  parsed=m.parse(make_gam(bytes(c)))
  slots=parsed['partyMembers'][0]['topLevelSlots']
  self.assertEqual(slots[18]['resref'],'C#GRTOO0')
  self.assertEqual(slots[35]['resref'],'C-ITEM01')
  self.assertFalse(parsed['dispatchAuthorized'])
  self.assertEqual(parsed['ordersSent'],0)

 def test_resref_dangerous_bytes_still_fail_closed(self):
  for bad in (b'X/BAD\0\0\0',b'../TEST\0',b'X\\TEST\0',
              b'X;DROP\0\0',b'X\x01BAD\0\0\0',b'X\xffTEST\0\0',
              b'X BAD\0\0\0'):
   with self.subTest(raw=bad),self.assertRaisesRegex(m.Hold,'HOLD_INVALID_RESREF_BYTES'):
    m.checkedres(bad)

 def test_free_slots_reported(self):
  x=m.parse(make_gam())["partyMembers"][0]
  self.assertEqual(x["freeQuickSlotCandidates"],[36,37,38])
 def test_flags_charges_preserved(self):
  x=m.parse(make_gam())["partyMembers"][0]["sourceSlots18to33"][0]
  self.assertEqual((x["useCount1Raw"],x["useCount2Raw"],
                    x["useCount3Raw"],x["flagsRaw"]),(5,6,7,1))
 def test_untrusted_live_fields_false(self):
  x=m.parse(make_gam())
  for field in ("userGameRuntimeItemPresentVerified","saveMatchesCurrentlyLoadedSessionVerified",
    "classKitWeaponSlotCapacityVerified","partyActorEngineIdVerified","currentItemUniqueAcrossContainersVerified"):
   self.assertIs(x[field],False)
  self.assertEqual(x["ordersSent"],0)
 def test_reject_invalid_gam(self):
  with self.assertRaises(m.Hold):m.parse(b"BAD")
 def test_reject_gam_v21_unproven_layout(self):
  with self.assertRaises(m.Hold):m.parse(make_gam(version=b"GAMEV2.1"))
 def test_reject_short_npc(self):
  with self.assertRaises(m.Hold):m.parse(make_gam()[:-100])
 def test_reject_duplicate_cre_item_reference(self):
  c=bytearray(make_cre())
  struct.pack_into("<H",c,0x300+22*2,0)
  with self.assertRaises(m.Hold):m.parse(make_gam(bytes(c)))
 def test_reject_bad_item_index(self):
  c=bytearray(make_cre())
  struct.pack_into("<H",c,0x300+21*2,9)
  with self.assertRaises(m.Hold):m.parse(make_gam(bytes(c)))
 def test_reject_cre_version(self):
  c=bytearray(make_cre());c[:8]=b"CRE V1.2"
  with self.assertRaises(m.Hold):m.parse(make_gam(bytes(c)))
 def test_reject_bad_party_order(self):
  with self.assertRaises(m.Hold):m.parse(make_gam(npcidx=6))
 def test_reject_item_table_unreferenced(self):
  c=bytearray(make_cre());struct.pack_into("<H",c,0x300+2*2,0xffff)
  with self.assertRaises(m.Hold):m.parse(make_gam(bytes(c)))
 def test_reject_wrong_count(self):
  g=bytearray(make_gam());struct.pack_into("<I",g,0x24,100)
  with self.assertRaises(m.Hold):m.parse(bytes(g))
 def test_bounded_50mb(self):
  with self.assertRaises(m.Hold):m.parse(b"GAMEV2.0"+b"0"*(50_000_001))
 def test_same_raw_input_deterministic_hash(self):
  x=make_gam()
  self.assertEqual(m.parse(x)["gamSha256"],m.parse(x)["gamSha256"])
if __name__=="__main__":unittest.main(verbosity=2)
