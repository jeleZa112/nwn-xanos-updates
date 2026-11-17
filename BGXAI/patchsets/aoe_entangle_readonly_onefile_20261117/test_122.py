"""BGXAI122: off-line tests only; never installs or writes to a real game."""
import struct
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import BGX122_PROJECTILES_READONLY as M

class TestProjectileReadOnly(unittest.TestCase):
    def ids(self):
        return ("IDS V1.0\n"+
            "\n".join(f"0x{i:04X} NAME{i:04d}" for i in range(30))+
            "\n0x003F WEB\n0x005E CLOUD\n0x00BA CLOUDKIL\n242 ENTANG2 // comment\n").encode()

    def test_ids_uses_actual_index_not_encoded_spell_plus_one(self):
        got=M.parse_projectl(self.ids())
        self.assertEqual({x:got[x] for x in (63,94,186,242)},
                         {63:"WEB",94:"CLOUD",186:"CLOUDKIL",242:"ENTANG2"})

    def test_ids_fail_closed_on_ambiguity(self):
        with self.assertRaisesRegex(ValueError,"AMBIGUOUS"):
            M.parse_projectl(self.ids()+b"0x003F WRONG\n")

    def test_ids_fail_closed_on_unknown_header_or_short_mapping(self):
        with self.assertRaises(ValueError):
            M.parse_projectl(b"not ids\n")
        with self.assertRaisesRegex(ValueError,"SHORT"):
            M.parse_projectl(b"IDS V1.0\n0x3F WEB\n")

    def test_pro_area_offsets(self):
        p=bytearray(768)
        p[:8]=b"PRO V1.0"
        struct.pack_into("<H",p,0x08,3)
        struct.pack_into("<H",p,0x200,0x0102)
        struct.pack_into("<H",p,0x204,144)
        struct.pack_into("<h",p,0x206,-160)
        struct.pack_into("<H",p,0x210,40)
        struct.pack_into("<H",p,0x214,101)
        p[0x216]=6
        struct.pack_into("<H",p,0x21a,63)
        d=M.parse_pro(bytes(p))
        self.assertTrue(d["is_area"])
        self.assertEqual(d["explosion_radius_px"],160)
        self.assertEqual(d["trigger_radius_px"],144)
        self.assertEqual(d["explosion_frequency"],40)
        self.assertEqual(d["repetitions"],6)
        self.assertEqual(d["secondary_projectile_index"],101)
        self.assertEqual(d["explosion_projectile_index"],63)
        self.assertFalse(d["geometry_safe_to_use_at_runtime"])

    def test_pro_types_and_invalid_length(self):
        p=bytearray(512);p[:8]=b"PRO V1.0"
        struct.pack_into("<H",p,8,2)
        self.assertFalse(M.parse_pro(bytes(p))["is_area"])
        with self.assertRaises(ValueError):M.parse_pro(bytes(p[:-1]))
        with self.assertRaises(ValueError):M.parse_pro(b"bad"+bytes(765))
        struct.pack_into("<H",p,8,3)
        with self.assertRaises(ValueError):M.parse_pro(bytes(p))

    def test_eff_opcode_177_refers_to_EFF_not_SPL(self):
        raw=bytearray(0x110)
        raw[:8]=b"EFF V2.0"
        struct.pack_into("<I",raw,0x10,109)   # Hold
        struct.pack_into("<I",raw,0x14,2)
        struct.pack_into("<I",raw,0x1c,101)
        struct.pack_into("<I",raw,0x20,202)
        raw[0x30:0x38]=b"SPWI215 "
        struct.pack_into("<I",raw,0x5c,3)
        struct.pack_into("<I",raw,0xa0,64)
        d=M.parse_eff(bytes(raw))
        self.assertEqual(d["opcode"],109)
        self.assertEqual(d["parameter1"],101)
        self.assertEqual(d["projectile_index"],64)
        self.assertEqual(d["resist_dispel_flags"],3)
        self.assertEqual(d["resource"],"SPWI215 ")
        with self.assertRaises(ValueError):M.parse_eff(b"SPL V1  "+bytes(500))

    def test_read_ids_prefer_override_never_write_to_game(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/"override").mkdir()
            source=root/"override"/"PROJECTL.IDS"
            source.write_bytes(self.ids())
            with mock.patch.object(M.R,"resource",side_effect=AssertionError("BIF_CALLED")):
                buf,origin=M.read_ids(root,root/"nocompiler",root)
            self.assertEqual(buf,self.ids())
            self.assertEqual(origin,"override")

    def test_live_status_checked_before_reading_game_resources(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            with mock.patch.object(M.G,"exact_game",return_value=root),\
                mock.patch.object(M.G,"installed",side_effect=M.G.Stop("BGX120_CHANGED")),\
                mock.patch.object(M.G,"require",side_effect=AssertionError("MUST_NOT_READ")):
                with self.assertRaisesRegex(M.G.Stop,"BGX120_CHANGED"):
                    M.audit(root,root.parent/"report")

    def test_no_claim_of_working_runtime_immunity_or_pathing(self):
        self.assertTrue(all(
            M.parse_pro(bytes.fromhex("50524f2056312e30")+bytes(248))[key] is False
            for key in ("is_area","radius_validated_for_cast","geometry_safe_to_use_at_runtime")
        ))

    def test_pinned_121_sources_exact(self):
        self.assertEqual(set(M.EXACT_SPELLS),
                         {"SPPR105","SPWI215","SPWI213","SPWI502"})
        self.assertEqual(M.EXPECTED_PROJECTL_INDEX,
                         {"SPPR105":242,"SPWI215":63,"SPWI213":94,"SPWI502":186})
        self.assertTrue(all(len(x)==64 for x in M.EXACT_SPELLS.values()))

if __name__=="__main__":
    unittest.main(verbosity=2)
