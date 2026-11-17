"""BGXAI 120 mocked tests: no live game edits."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import BGX120_ENTANGLE_GUARD as G

ORIGINAL = """IF
  StateCheck(Myself,STATE_PANIC)
THEN
  RESPONSE #100
    RandomWalkContinuous()
END

IF
  See(NearestEnemyOf(Myself))
  HaveSpell(CLERIC_HOLD_PERSON)
  !StateCheck(NearestEnemyOf(Myself),STATE_SLEEPING)
  !StateCheck(NearestEnemyOf(Myself),STATE_HELPLESS)
THEN
  RESPONSE #100
    Spell(NearestEnemyOf(Myself),CLERIC_HOLD_PERSON)
END

IF
  See(NearestEnemyOf(Myself))
  HaveSpell(CLERIC_ENTANGLE)
  !StateCheck(NearestEnemyOf(Myself),STATE_SLEEPING)
  !StateCheck(NearestEnemyOf(Myself),STATE_HELPLESS)
THEN
  RESPONSE #100
    Spell(NearestEnemyOf(Myself),CLERIC_ENTANGLE)
END

IF
  See(NearestEnemyOf(Myself))
  HaveSpell(CLERIC_COMMAND)
  !StateCheck(NearestEnemyOf(Myself),STATE_SLEEPING)
  !StateCheck(NearestEnemyOf(Myself),STATE_HELPLESS)
THEN
  RESPONSE #100
    Spell(NearestEnemyOf(Myself),CLERIC_COMMAND)
END

IF
  See(NearestEnemyOf(Myself))
THEN
  RESPONSE #100
    Attack(NearestEnemyOf(Myself))
END

"""

class SafeGuard(unittest.TestCase):
    def test_source_fixture_is_real_users_source(self):
        self.assertEqual(len(ORIGINAL.encode()),919)
        self.assertEqual(G.sha(ORIGINAL.encode()),G.ORIGINAL_BAF_SHA)

    def test_exact_entangle_only(self):
        new=G.modify_baf(ORIGINAL)
        self.assertEqual(new.count("!InParty(Myself)"),1)
        self.assertEqual(new.replace(G.NEW_ENTANGLE,G.OLD_ENTANGLE,1),ORIGINAL)
        self.assertEqual(len(G.A.find_blocks(new)),5)
        self.assertEqual(new.count("Spell(NearestEnemyOf(Myself),CLERIC_HOLD_PERSON)"),1)
        self.assertEqual(new.count("Spell(NearestEnemyOf(Myself),CLERIC_COMMAND)"),1)
        self.assertEqual(new.count("Attack(NearestEnemyOf(Myself))"),1)

    def test_changed_or_duplicate_original_fails_closed(self):
        for s in (ORIGINAL.replace("Spell(NearestEnemyOf(Myself),CLERIC_ENTANGLE)","Attack(Myself)"),
                  ORIGINAL.replace("CLERIC_COMMAND","CLERIC_ENTANGLE"),
                  ORIGINAL.replace("See(NearestEnemyOf(Myself))","True()",1)):
            with self.assertRaises(G.Stop):
                G.modify_baf(s)

    def test_original_binary_bcs_roundtrip_blocks(self):
        # Mock the integer-coded BCS envelope, preserve 5 blocks and mutate only index 2.
        orig=b"SC\n"+b"".join(b"CR\n"+bytes([65+i])+b"\n" for i in range(5))+b"CR\nSC\n"
        diff=b"SC\n"+b"".join(b"CR\n"+bytes([65+i])+ (b"_G\n" if i==2 else b"\n") for i in range(5))+b"CR\nSC\n"
        a=G.blocks(orig); b=G.blocks(diff)
        self.assertEqual(len(a),5)
        self.assertEqual([i for i in range(5) if a[i]!=b[i]],[2])

    def test_no_unsafe_game_path(self):
        with self.assertRaises(G.Stop):
            G.require(Path("/tmp"),"../secrets",1)
        with self.assertRaises(G.Stop):
            G.require(Path("/tmp"),"override\\PRIEST1.BCS",1)

    def test_preflight_hash_doesnt_install(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            with mock.patch.object(G,"source_guard",return_value={"baseline":"OK"}),\
                 mock.patch.object(G,"candidate",return_value=(b"SC\n",{"status":"BGX120_NATIVE_PREFLIGHT_PASS"})),\
                 mock.patch.object(G,"require",return_value=Path(__file__)):
                result=G.preflight(root)
            self.assertEqual(result["status"],"BGX120_NATIVE_PREFLIGHT_PASS")
            self.assertFalse((root/"BGX120").exists())
            self.assertFalse((root/"override").exists())

    def test_no_automatic_install_without_token(self):
        with mock.patch.object(G,"exact_game",return_value=G.GAME),\
             mock.patch("builtins.input",side_effect=["3",""] ),\
             mock.patch.object(G,"install",side_effect=AssertionError("INSTALL CALLED")):
            self.assertEqual(G.main(),0)

if __name__=="__main__":
    unittest.main(verbosity=2)
