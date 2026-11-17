#!/usr/bin/env python3
"""Tests for one-file BGXAI AoE audit. No live game, writes only tmp fixtures."""
from __future__ import annotations
from pathlib import Path
from unittest import mock
import hashlib, json, tempfile, unittest, zipfile
import BGXAI_AOE_AUDIT as A

SAMPLE = """IF
  True()
THEN
  RESPONSE #100
    Spell(NearestEnemyOf(Myself),CLERIC_ENTANGLE)
END

IF
  True()
THEN
  RESPONSE #100
    Spell(Player1,CLERIC_CURE_LIGHT_WOUNDS)
END

IF
  True()
THEN
  RESPONSE #100
    Spell(NearestEnemyOf(Myself),WIZARD_FIREBALL)
END
"""

class Audit(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name)
        self.game=self.base/"game"
        self.game.mkdir()
        self.bcs=b"SC\n"+b"x"*5000
        self.lua=b"local x = 1"+b" "*200
        self.weidu=b"MZ"+b"x"*100000
        for rel,raw in (
            ("override/BDDEFAI.BCS",self.bcs),
            ("override/M_BX43.lua",self.lua),
            ("WeiDU.log",b"~BGXP5\SETUP-BGXP5.TP2~ #0 #0 // ok\n"),
            ("setup-enhanced-powergaming-scripts.exe",self.weidu),
            ("lang/ru_RU/dialog.tlk",b"TLK"+b"x"*200)
        ):
            target=self.game/rel
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(raw)
        self.oldpins=A.BCS_PIN,A.LUA_PIN,A.GAME
        A.BCS_PIN=A.digest(self.bcs)
        A.LUA_PIN=A.digest(self.lua)
        A.GAME=self.game
        self.addCleanup(self.restore)
    def restore(self):
        A.BCS_PIN,A.LUA_PIN,A.GAME=self.oldpins

    def test_entangle_and_fireball_found_heal_excluded(self):
        r=A.classify(SAMPLE)
        self.assertEqual(r["baf_block_count"],3)
        self.assertEqual(r["entangle_block_count"],1)
        self.assertEqual(len(r["aoe_blocks"]),2)
        self.assertEqual([x["index_zero_based"] for x in r["aoe_blocks"]],[0,2])

    def test_untrusted_missing_or_drift_aborts(self):
        self.assertEqual(A.checked(self.game)[-1].count("BGXP5"),2)
        (self.game/"override/BDDEFAI.BCS").write_bytes(b"modified"*800)
        with self.assertRaisesRegex(ValueError,"BGXP5_LIVE_SHA_MISMATCH"):
            A.checked(self.game)

    def test_invalid_weidu_order_aborts(self):
        (self.game/"WeiDU.log").write_text("~BGXP6\SETUP-BGXP6.TP2~ #0 #0 // other\n")
        with self.assertRaisesRegex(ValueError,"BGXP5_NOT_LAST_WEIDU"):
            A.checked(self.game)

    def test_full_report_writes_only_outside_game(self):
        before={str(f.relative_to(self.game)): A.digest(f.read_bytes()) for f in self.game.rglob("*") if f.is_file()}
        extra= "IF\n  True()\nTHEN\n  RESPONSE #100\n    NoAction()\nEND\n"
        text=SAMPLE+extra*(A.COUNT-3)
        with mock.patch.object(A,"decompile",return_value=(text,"WEIDU_LOG")):
            report=A.audit(self.game,self.base/"reports")
        self.assertEqual(report["status"],"BGXAI_AOE_READONLY_PASS")
        self.assertEqual(report["total_blocks"],1170)
        self.assertEqual(report["entangle_keyword_hits"],1)
        self.assertFalse(report["game_modified"])
        z=Path(report["zip"])
        self.assertTrue(z.is_file())
        with zipfile.ZipFile(z) as archive:
            self.assertEqual(len(A.find_blocks(archive.read("BDDEFAI_DECOMPILED_READONLY.BAF").decode())),1170)
            self.assertIn("AOE_BLOCKS.json",archive.namelist())
        self.assertEqual(before,{str(f.relative_to(self.game)):A.digest(f.read_bytes()) for f in self.game.rglob("*") if f.is_file()})

    def test_reject_report_inside_game(self):
        with mock.patch.object(A,"decompile",return_value=(SAMPLE+"IF\n True()\nTHEN\n RESPONSE #100\n NoAction()\nEND\n"*(A.COUNT-3),"LOG")):
            with self.assertRaisesRegex(ValueError,"OUTPUT_MUST_BE_OUTSIDE_GAME"):
                A.audit(self.game,self.game/"override"/"REPORTS")

    def test_no_mutation_commands_in_auditor(self):
        source=(Path(__file__).with_name("BGXAI_AOE_AUDIT.py")).read_text()
        for phrase in ["--force-install","--force-uninstall","setup-BGXP6.tp2",
                       "COPY ~","override/BDDEFAI.BCS~"]:
            self.assertNotIn(phrase,source)

if __name__=="__main__":
    unittest.main(verbosity=2)
