"""No-game tests for 80KB onefile menu171 and exact 1-170 preservation."""
import hashlib
import importlib.util
from pathlib import Path
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("r31_onefile",ROOT/"build_r31_onefile_menu_source_only.py")
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class OnefileSourceOnly(unittest.TestCase):
    def test_original_pin_and_exact_size(self):
        src=m.BACKEND.read_bytes()
        if b"'171' {" not in src:
            self.assertEqual(len(src),79979)
            self.assertEqual(m.digest(src),m.ORIGINAL_SHA)
        self.assertEqual(m.digest(m.LUA.read_bytes()),m.LUA_SHA)
        self.assertIn(b"INSTALL_BGXAI_R31_PASSIVE_V3_AFTER_R29",m.GUARD.read_bytes())

    def test_menu171_built_without_touching_current_backend(self):
        before=m.BACKEND.read_bytes()
        out=m.build()
        self.assertLessEqual(len(out),80000)
        self.assertIn(b"R31_GUARDED_SOURCE_ONLY.py",out)
        self.assertIn(b"M_BGXR27_R31_SOURCE_ONLY.lua",out)
        self.assertIn(m.digest(m.GUARD.read_bytes()).encode(),out)
        self.assertIn(m.LUA_SHA.encode(),out)
        self.assertIn(b"171 R31 V3",out)
        self.assertIn(b"'171' {",out)
        self.assertEqual(m.dispatches(out.decode()),[str(n) for n in range(1,172)])
        self.assertIn(b"Set-Alias wh Write-Host -Scope Script",out)
        self.assertIn(b"'170' {RunR30ReadOnly;break}",out)
        self.assertEqual(m.BACKEND.read_bytes(),before)

    def test_staged_backend_bytes_exactly_equal_deterministic_builder(self):
        staged=ROOT/"BGXAI_SYNC_R31_MENU171_SOURCE_ONLY.ps1"
        expected=m.build()
        self.assertEqual(staged.read_bytes(),expected,
                         "staged source must be identical to approved deterministic builder")
        self.assertEqual(len(expected),79941)
        self.assertEqual(m.digest(expected),"c998ff6607ee3915b9cbb3c9b31955f715bee425b5ed882e04e1af1d515ed4aa")

    def test_idempotent_on_proposed_backend(self):
        built=m.build()
        self.assertEqual(m.produce(built,m.GUARD.read_bytes(),m.LUA.read_bytes()),built)

    def test_old_baseline_tamper_and_r31_source_change_fail_closed(self):
        original=m.BACKEND.read_bytes()
        if b"'171' {" not in original:
            with self.assertRaisesRegex(m.Hold,"BASELINE_BACKEND_SHA_DRIFT"):
                m.produce(original+b" ",m.GUARD.read_bytes(),m.LUA.read_bytes())
        with self.assertRaisesRegex(m.Hold,"R31_LUA_SOURCE_PIN_DRIFT"):
            m.produce(original,m.GUARD.read_bytes(),m.LUA.read_bytes()+b"X")

    def test_new_menu_guards_and_scope(self):
        text=m.build().decode("utf-8")
        index=text.index("'171' {")
        handler=text[index:].split("\n",1)[0]
        self.assertIn("ANR $zcd",handler)
        self.assertIn("[guid]::NewGuid()",handler)
        self.assertIn("R31 PIN STOP",handler)
        self.assertIn("R31 STAGE SHA",handler)
        self.assertIn("R31 BAD CHOICE",handler)
        for mode in ("preflight","install","status","rollback","capture"):
            self.assertIn("'"+mode+"'",handler)
        self.assertIn("Remove-Item -LiteralPath $f,$c",handler)
        self.assertIn("BGXAI/BUILD",text)
        self.assertEqual(text.count("'171' {"),1)

if __name__=="__main__":unittest.main()
