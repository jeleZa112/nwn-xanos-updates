#!/usr/bin/env python3
"""Mock CRE/GAM fixtures only: no game or user save read or modified."""
import pathlib
import struct
import tempfile
import unittest
from unittest import mock
import BGXAI_WEAPON_SAVED_SNAPSHOT_READONLY as W

def fixture(selected=0, weapon="SW1H01", broken=False):
    cre=bytearray(0x420)
    cre[0:8]=b"CRE V1.0"
    struct.pack_into("<III",cre,0x2B8,0x300,0x360,3)
    struct.pack_into("<40H",cre,0x300,*([65535]*9+[0]+[65535]*3+[1]+[65535]*7+[2]+[65535]*16+[65535,selected,0]))
    for i,res in enumerate([weapon,"AROW01","C#MOD+1"]):
        off=0x360+20*i
        cre[off:off+8]=res.encode("ascii").ljust(8,b"\0")
        struct.pack_into("<3H",cre,off+10,12,0,0)
        struct.pack_into("<I",cre,off+16,1)
    if broken:struct.pack_into("<H",cre,0x300+9*2,500)
    return bytes(cre)

def gam(cre):
    out=bytearray(0x300+len(cre))
    out[:8]=b"GAMEV2.0"
    struct.pack_into("<II",out,0x20,0xA4,1)
    struct.pack_into("<H",out,0xA4+2,2)
    struct.pack_into("<II",out,0xA4+4,0x300,len(cre))
    out[0xA4+0xC0:0xA4+0xC0+6]=b"Khalid"
    out[0x300:]=cre
    return bytes(out)

class SavedWeaponSnapshot(unittest.TestCase):
    def test_weapon_ammo_backpack_selected(self):
        r=W.extract_cre(fixture())
        self.assertEqual(r["quickslots"][0]["resref"],"SW1H01")
        self.assertIsNone(r["quickslots"][1])
        self.assertEqual(r["quiver_slots"][0]["resref"],"AROW01")
        self.assertEqual(r["backpack_items"][0]["resref"],"C#MOD+1")
        self.assertEqual(r["selected_weapon"]["resref"],"SW1H01")
        self.assertEqual(r["selected_weapon"]["state"],"SELECTED_QUICKSLOT")
        self.assertFalse(r["live_equipment_verified"])
        self.assertFalse(r["weapon_type_verified"])
    def test_no_ability_inference_from_ammo_count(self):
        r=W.extract_cre(fixture())
        self.assertEqual(r["quiver_slots"][0]["charges"][0],12)
        self.assertFalse(r["attack_stats_verified"])
        self.assertFalse(r["enchantment_verified"])
    def test_fists_not_weapon_fallback(self):
        r=W.extract_cre(fixture(selected=1000))
        self.assertEqual(r["selected_weapon"]["state"],"FIST_SELECTED")
        self.assertIsNone(r["selected_weapon"]["resref"])
    def test_unrecognized_selected(self):
        r=W.extract_cre(fixture(selected=9))
        self.assertEqual(r["selected_weapon"]["state"],"SELECTED_SLOT_UNKNOWN")
    def test_unknown_slot_index_blocks(self):
        with self.assertRaisesRegex(ValueError,"CRE_INVALID_ITEM_SLOT_INDEX"):
            W.extract_cre(fixture(broken=True))
    def test_malformed_pointer_blocks(self):
        c=bytearray(fixture())
        struct.pack_into("<I",c,0x2B8,0xFFFFF000)
        with self.assertRaisesRegex(ValueError,"CRE_ITEM_POINTER_BOUNDS"):W.extract_cre(bytes(c))
    def test_overlap_blocks(self):
        c=bytearray(fixture())
        struct.pack_into("<I",c,0x2BC,0x302)
        with self.assertRaisesRegex(ValueError,"CRE_ITEM_SLOT_OVERLAP"):W.extract_cre(bytes(c))
    def test_unsanitized_resref_rejected(self):
        c=bytearray(fixture())
        c[0x360:0x368]=b"../../bad"
        with self.assertRaisesRegex(ValueError,"INVALID_ITEM_RESREF"):W.extract_cre(bytes(c))
    def test_unsupported_cre_rejected(self):
        with self.assertRaisesRegex(ValueError,"UNSUPPORTED_CRE"):W.extract_cre(b"CRE V2.2"+bytes(1024))
    def test_whole_saved_party_no_live_claim(self):
        r=W.inspect_gam(gam(fixture()))
        self.assertEqual(r["status"],"SAVED_WEAPON_SLOTS_SURVEY")
        self.assertEqual(r["party"][0]["name_from_saved_record"],"Khalid")
        self.assertFalse(r["runtime_verified"])
        self.assertFalse(r["game_modified"])
    def test_read_only_latest_historical_snapshot(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d)
            sf=root/"save"/"slot1"/"BALDUR.GAM"
            sf.parent.mkdir(parents=True)
            contents=gam(fixture())
            sf.write_bytes(contents)
            before=sf.read_bytes()
            with mock.patch.object(W.S,"save_roots",return_value=[root/"save"]):
                r=W.inspect_latest(root)
            self.assertEqual(r["status"],"SAVED_WEAPON_SLOTS_SURVEY")
            self.assertEqual(r["party"][0]["selected_weapon"]["resref"],"SW1H01")
            self.assertEqual(sf.read_bytes(),before)
            self.assertFalse(r["game_modified"])
    def test_wrong_gam_stop(self):
        with self.assertRaisesRegex(ValueError,"UNSUPPORTED_GAM_VERSION"):
            W.inspect_gam(b"garbage")

if __name__=="__main__":
    unittest.main(verbosity=2)
