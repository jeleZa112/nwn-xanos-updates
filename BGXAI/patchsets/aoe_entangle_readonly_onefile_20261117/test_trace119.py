#!/usr/bin/env python3
"""Read-only BCS source-trace tests: mocks only, never need EET installation."""
from __future__ import annotations
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import zipfile

import BGXAI_AOE_AUDIT as A
import BGX119_TRACE as T

class Trace(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.work=Path(self.tmp.name)
        self.game=self.work/"game"
        (self.game/"override").mkdir(parents=True)
        self.out=self.work/"report"
        self.old_game=A.GAME
        A.GAME=self.game
        self.addCleanup(lambda:setattr(A,"GAME",self.old_game))

    def test_override_takes_precedence_over_biff(self):
        (self.game/"override"/"JAHEIRA_.BCS").write_bytes(b"SC\nCR\nSC\n")
        with mock.patch.object(T,"run",side_effect=AssertionError("BIF extract must not run")):
            raw,origin,path=T.read_script(self.game,self.work/"weidu.exe",self.work,"JAHEIRA_")
        self.assertEqual(origin,"override")
        self.assertEqual(raw,b"SC\nCR\nSC\n")

    def test_biff_extract_is_read_only_and_in_temp(self):
        calls=[]
        def fake_run(cmd,cwd):
            calls.append(cmd)
            out=Path(cmd[cmd.index("--out")+1])
            (out/"PRIEST1.BCS").write_bytes(b"SC\nCR\nSC\n")
            return 0,"OK"
        with mock.patch.object(T,"run",side_effect=fake_run):
            raw,origin,_=T.read_script(self.game,self.work/"weidu.exe",self.work,"PRIEST1")
        self.assertEqual(origin,"chitin_biff")
        self.assertEqual(raw,b"SC\nCR\nSC\n")
        self.assertEqual(len(calls),1)
        self.assertIn("--biff-get",calls[0])
        self.assertNotIn("--make-biff",calls[0])
        self.assertNotIn("--install",calls[0])

    def test_spell_classifier_detects_real_casts(self):
        code="""IF
  HaveSpell(CLERIC_ENTANGLE)
THEN
  RESPONSE #100
    Spell(LastSeenBy(Myself),CLERIC_ENTANGLE)
END
IF
  True()
THEN
  RESPONSE #100
    Spell(LastSeenBy(Myself),CLERIC_CURE_LIGHT_WOUNDS)
END
"""
        lines=T.SPELL.findall(code)
        self.assertEqual(len(lines),1)
        self.assertIn("CLERIC_ENTANGLE",lines[0])
        self.assertEqual(len(T.RESPONSE.findall(code)),2)

    def test_report_contains_five_slots_and_isolated_output(self):
        before=[]
        class DummyCtx:
            def __init__(self,b):self.b=b
        def fake_read(game,exe,td,stem):
            if stem=="PRIEST1":return b"SC\nCR\nSC\n","chitin_biff","OK"
            return None,"not_found_in_chitin","NO_RESOURCE"
        def fake_decompile(exe,game,td,stem,raw):
            return 'IF\n  True()\nTHEN\n  RESPONSE #100\n    Spell(NearestEnemyOf(Myself),CLERIC_ENTANGLE)\nEND\n',"LOG"
        with mock.patch.object(A,"checked",return_value=(b"SC\nCR\nSC\n",b"MZ"+b"1"*1000,b"some lua","BGXP5")),\
            mock.patch.object(T,"read_script",side_effect=fake_read),\
            mock.patch.object(T,"decompile",side_effect=fake_decompile),\
            mock.patch.object(T,"gam_snapshot",return_value={"status":"SAVE_SLOT_NOT_FOUND"}):
            result=T.extract(self.game,self.out)
        self.assertEqual(result["status"],"BGX119_READONLY_PASS")
        self.assertEqual(result["found_scripts"],1)
        self.assertEqual(len(result["scripts"]),5)
        self.assertTrue(result["game_modified"] is False)
        dest=Path(result["zip_path"])
        with zipfile.ZipFile(dest) as archive:
            self.assertIn("PRIEST1.BAF",archive.namelist())
            self.assertIn("PRIEST1.BCS",archive.namelist())
            self.assertEqual(json.loads(archive.read("REPORT.json"))["found_scripts"],1)
        self.assertFalse(list((self.game/"override").iterdir()))

    def test_no_writes_inside_game_ever(self):
        with mock.patch.object(A,"checked",return_value=(b"SC\nCR\nSC\n",b"MZ"+b"1"*1000,b"some lua","BGXP5")):
            with self.assertRaisesRegex(ValueError,"REPORT_INSIDE_GAME_BLOCKED"):
                T.extract(self.game,self.game/"override"/"OUTPUT")

if __name__=="__main__":
    unittest.main(verbosity=2)
