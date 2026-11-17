"""BGXAI121 regression tests: resource parser, AoE risk, routing, no live mutation."""
import struct
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import BGX121_POLICY as P
import BGX121_READONLY as R

def spl_fixture()->bytes:
    b=bytearray(0x72+0x28+0x30)
    b[:8]=b"SPL V1  "
    struct.pack_into("<I",b,0x34,1)  # level
    struct.pack_into("<H",b,0x1c,2)  # priest
    struct.pack_into("<I",b,0x64,0x72)
    struct.pack_into("<H",b,0x68,1)
    struct.pack_into("<I",b,0x6a,0x9a)
    struct.pack_into("<H",b,0x72+0x10,1)
    struct.pack_into("<H",b,0x72+0xe,30)
    struct.pack_into("<H",b,0x72+0x12,4)
    struct.pack_into("<H",b,0x72+0x1e,1)
    struct.pack_into("<H",b,0x72+0x20,0)
    struct.pack_into("<H",b,0x72+0x26,86)
    struct.pack_into("<H",b,0x9a,154)
    b[0x9a+2]=2  # projectile target
    b[0x9a+0x14:0x9a+0x1c]=b"TESTRES "
    return bytes(b)

class SpellSafety(unittest.TestCase):
    def test_spl_real_offsets_and_no_guessed_radius(self):
        d=R.parse_spl(spl_fixture())
        self.assertEqual(d["spell_level"],1)
        self.assertEqual(d["spell_type"],2)
        self.assertEqual(d["abilities"][0]["projectile_encoded"],86)
        self.assertEqual(d["abilities"][0]["projectl_ids_index"],85)
        self.assertEqual(d["abilities"][0]["projectile_radius_px"],"UNKNOWN_NEEDS_EXACT_PRO")
        self.assertEqual(d["abilities"][0]["effects"][0]["opcode"],154)

    def test_reject_bad_spl_geometry(self):
        b=bytearray(spl_fixture())
        for pos,value,fmt in ((0x68,99,"<H"),(0x64,5000,"<I"),(0x6a,5000,"<I")):
            v=bytearray(b)
            struct.pack_into(fmt,v,pos,value)
            with self.assertRaises(ValueError):
                R.parse_spl(v)

    def test_override_precedence_and_no_resource_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            game=Path(tmp)
            d=game/"override"
            d.mkdir()
            f=d/"SPPR105.SPL"
            f.write_bytes(spl_fixture())
            with mock.patch.object(R.T,"run",side_effect=AssertionError("DID_RUN_WEIDU")):
                got,origin=R.resource(game,game/"missing.exe",game,"SPPR105","SPL")
            self.assertEqual(got,f.read_bytes())
            self.assertEqual(origin,"override")

    def test_near_allies_vulnerable(self):
        h=P.Hazard("SPPR105",500,500,"AREA",160,frozenset({"ENTANGLE"}))
        friends=[P.Ally("tarana",600,500,"AREA"),P.Ally("near",400,500,"AREA")]
        self.assertEqual(P.safe_aoe(h,friends,True),(False,["tarana","near"]))

    def test_excluded_ally_on_other_area(self):
        h=P.Hazard("SPPR105",500,500,"AREA",160,frozenset({"ENTANGLE"}))
        self.assertEqual(P.safe_aoe(h,[P.Ally("other",500,500,"DIFFERENT")],True),(True,[]))

    def test_summon_without_immunity_blocks(self):
        h=P.Hazard("SPPR105",100,100,"AREA",90,frozenset({"ENTANGLE"}))
        self.assertFalse(P.safe_aoe(h,[P.Ally("summoned_spirit",100,120,"AREA")],True)[0])

    def test_verified_per_effect_immunity_allows(self):
        h=P.Hazard("MIXED",100,100,"AREA",90,frozenset({"WEB","FIRE"}))
        complete=P.Ally("safe",100,100,"AREA",frozenset({"WEB","FIRE"}))
        partial=P.Ally("partial",100,100,"AREA",frozenset({"WEB"}))
        self.assertTrue(P.safe_aoe(h,[complete],True)[0])
        self.assertFalse(P.safe_aoe(h,[partial],True)[0])

    def test_unknown_effects_not_safe_even_if_other_immune(self):
        h=P.Hazard("MOD",100,100,"AREA",90,frozenset())
        self.assertFalse(P.safe_aoe(h,[P.Ally("target",100,100,"AREA",frozenset({"WEB"}))],True)[0])

    def test_unknown_radius_and_incomplete_roster_fails_closed(self):
        h=P.Hazard("MOD",100,100,"AREA",float("nan"),frozenset({"WEB"}))
        ally=P.Ally("safe",800,800,"AREA")
        self.assertFalse(P.safe_aoe(h,[ally],True)[0])
        self.assertFalse(P.safe_aoe(P.Hazard("OK",100,100,"AREA",50,frozenset({"WEB"})),[ally],False)[0])

    def test_perspective_y_ellipse(self):
        h=P.Hazard("WEB",100,100,"AREA",100,frozenset({"WEB"}))
        self.assertTrue(P.affected(P.Ally("near",100,170,"AREA"),h,padding=0))
        self.assertFalse(P.affected(P.Ally("far",100,190,"AREA"),h,padding=0))

    def test_route_crossing_even_with_safe_endpoints(self):
        h=P.Hazard("WEB",150,100,"AREA",40,frozenset({"WEB"}))
        actor=P.Ally("actor",0,100,"AREA")
        self.assertTrue(P.path_crosses((0,100),(300,100),h,actor,0))
        self.assertFalse(P.path_crosses((0,0),(300,0),h,actor,0))

    def test_distant_from_hazard_melee_permitted(self):
        h=P.Hazard("WEB",150,100,"AREA",40,frozenset({"WEB"}))
        a=P.Ally("actor",0,0,"AREA")
        self.assertEqual(P.choose_combat_action(a,(0,0),(300,0),[h],True,False),"MELEE_PERMITTED")

    def test_ranged_weapon_first_and_ranged_spell_fallback(self):
        h=P.Hazard("WEB",150,100,"AREA",40,frozenset({"WEB"}))
        a=P.Ally("actor",0,100,"AREA")
        self.assertEqual(P.choose_combat_action(a,(0,100),(300,100),[h],True,True),"RANGED_WEAPON_FROM_SAFE_POSITION")
        self.assertEqual(P.choose_combat_action(a,(0,100),(300,100),[h],False,True),"RANGED_SPELL_FROM_SAFE_POSITION")
        self.assertEqual(P.choose_combat_action(a,(0,100),(300,100),[h],False,False),"HOLD_OR_OTHER_TARGET")

    def test_urgent_healing_bypasses_policy(self):
        h=P.Hazard("WEB",150,100,"AREA",40,frozenset({"WEB"}))
        a=P.Ally("Jagan",0,100,"AREA")
        self.assertEqual(P.choose_combat_action(a,(0,100),(300,100),[h],True,True,urgent_healing=True),"DEFER_TO_BGXP5_HEAL")

    def test_safe_movement_fallback(self):
        h=P.Hazard("WEB",150,100,"AREA",40,frozenset({"WEB"}))
        a=P.Ally("actor",0,100,"AREA")
        self.assertEqual(P.choose_combat_action(a,(0,100),(300,100),[h],False,False,safe_ally_destination=(0,0)),"MOVE_TO_SAFE_POSITION")

    def test_policy_proofs(self):
        self.assertEqual(R.policy_proofs()["status"],"BGX121_POLICY_SELFTEST_PASS")

if __name__=="__main__":
    unittest.main(verbosity=2)
