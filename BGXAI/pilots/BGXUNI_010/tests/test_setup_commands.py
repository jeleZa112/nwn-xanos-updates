"""Regression checks after actual user WeiDU 25100 rejected --tp2 on 2026-11-03.
These tests do not substitute for Windows/WeiDU execution.
"""
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=(ROOT/'BGXUNI_SETUP.cmd').read_text(encoding='utf-8')
TP2=(ROOT/'BGXUNI/setup-BGXUNI.tp2').read_text(encoding='utf-8')
EXEC='\n'.join(x.strip() for x in SCRIPT.splitlines() if x.strip() and not x.strip().lower().startswith('rem '))

class TestWeiDU251Setup(unittest.TestCase):
    def test_no_unsupported_tp2_argument(self):
        self.assertNotIn(' --tp2 ', EXEC)
    def test_valid_supported_cli_commands(self):
        self.assertIn('"setup-BGXUNI.exe" --yes', EXEC)
        self.assertIn('"setup-BGXUNI.exe" --reinstall', EXEC)
        self.assertIn('"setup-BGXUNI.exe" --uninstall', EXEC)
        self.assertNotIn('--uninstall --yes', EXEC)
    def test_stages_tp2_from_existing_user_folder(self):
        self.assertIn('if exist "setup-BGXUNI.tp2" (', EXEC)
        self.assertIn('fc /b "setup-BGXUNI.tp2" "BGXUNI\\setup-BGXUNI.tp2"', EXEC)
        self.assertIn('copy /b "BGXUNI\\setup-BGXUNI.tp2" "setup-BGXUNI.tp2"', EXEC)
    def test_never_overwrites_unrelated_existing_tp2(self):
        self.assertIn('STOP: root setup-BGXUNI.tp2 differs', EXEC)
        self.assertIn('exit /b 11', EXEC)
    def test_checks_unique_script_before_user_can_select_it(self):
        self.assertIn('if not exist "scripts\\BGXUN1.BS"', EXEC)
    def test_never_mutates_old_ai(self):
        for term in ('BDDEFAI.BCS','BGXGRP.BS','BGXTANK.BS','BGXAI_UPDATE.cmd','BGXAI_LIVE.cmd'):
            self.assertNotIn('copy /b /y "'+term, EXEC)
            self.assertNotIn('del "'+term, EXEC)
    def test_tp2_compiles_one_unique_baf(self):
        self.assertIn('COMPILE ~BGXUNI/BGXUN1.BAF~', TP2)
        self.assertIn('COPY ~override/BGXUN1.BCS~ ~scripts/BGXUN1.BS~', TP2)
        self.assertNotRegex(TP2, r'(?i)BDDEFAI|BGXGRP|BGXTANK')

if __name__=='__main__':unittest.main(verbosity=2)