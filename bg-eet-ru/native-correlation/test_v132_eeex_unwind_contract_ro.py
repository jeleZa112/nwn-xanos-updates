"""V132 synthetic PE64/unwind/EEex source tests; never operate on actual game."""
from pathlib import Path
from tempfile import TemporaryDirectory
import struct
import unittest

import v132_eeex_unwind_contract_ro as m
from test_pe_unwind_entry_gate_v130 import fixture

def fake_exe():
    raw=bytearray(fixture())
    coff=0x84;opt=coff+20;section=opt+0xF0
    # Move fixture .xdata to the exact user's unwind RVA 0x639100.
    at=section+2*40
    struct.pack_into("<I",raw,at+12,0x639000)
    struct.pack_into("<III",raw,0x2400,m.HIT_START,m.HIT_END,m.UNWIND_RVA)
    x=0x2700
    raw[x:x+4]=bytes([1,31,10,0])
    code=[(31,0x34),(27,0x00),(31,0xF2),
          (21,0xF0),(19,0xE0),(17,0xD0),(15,0xC0),
          (13,0x70),(12,0x60),(11,0x50)]
    for i,(pos,op) in enumerate(code):
        raw[x+4+i*2:x+6+i*2]=bytes([pos,op])
    return bytes(raw)

def source(good=True):
    marks=list(m.ASSEMBLY_MARKERS.values())
    if not good:marks.remove("EEex_RtlAddFunctionTable(")
    return ("\n".join(marks)+"\n"+"-- SOURCE ONLY FIXTURE\n"*280).encode("utf8")

class Tests(unittest.TestCase):
    def test_exact_private_unwind_slots_decode_save_rbx_27_x8(self):
        r=m.pe_unwind_raw(fake_exe(),require_pin=False)
        self.assertEqual(r["status"],"RAW_WIN64_SAVE_RBX_OFFSET_AND_POST_PROLOG_STATIC_PASS")
        self.assertEqual(r["raw_save_rbx_encoded_scaled_offset"],27)
        self.assertEqual(r["raw_save_rbx_stack_offset_bytes"],216)
        self.assertTrue(r["raw_rbx_offset_exact_216_verified"])
        self.assertEqual(r["alloc_stack_bytes"],128)
        self.assertEqual(r["push_nonvolatile_count"],7)
        self.assertEqual(r["unwind_code_slot_count"],10)
        self.assertEqual(r["unwind_record_count"],9)
        self.assertFalse(r.get("native_hook_install_allowed",False))

    def test_user_exe_sha_mandatory(self):
        with self.assertRaisesRegex(m.Hold,"BALDUR_EXE_SHA_DRIFT_HOLD"):
            m.pe_unwind_raw(fake_exe())

    def test_unwind_rbx_offset_drift_blocks(self):
        b=bytearray(fake_exe());b[0x2700+6]=25
        with self.assertRaisesRegex(m.Hold,"RAW_SAVE_OFFSET"):
            m.pe_unwind_raw(bytes(b),require_pin=False)

    def test_unwind_wrong_register_blocks(self):
        b=bytearray(fake_exe());b[0x2700+5]=0x44
        with self.assertRaisesRegex(m.Hold,"RBX_SAVE_ALLOC_PUSHES"):
            m.pe_unwind_raw(bytes(b),require_pin=False)

    def test_unwind_count_truncation_blocks(self):
        b=bytearray(fake_exe());b[0x2700+2]=9
        with self.assertRaises(m.Hold):
            m.pe_unwind_raw(bytes(b),require_pin=False)

    def test_no_ambiguous_function_records(self):
        b=bytearray(fake_exe())
        opt=0x84+20
        struct.pack_into("<I",b,opt+0x70+3*8+4,24)
        struct.pack_into("<III",b,0x240c,m.HIT_START,m.HIT_END,m.UNWIND_RVA)
        with self.assertRaisesRegex(m.Hold,"FUNCTION_COUNT"):
            m.pe_unwind_raw(bytes(b),require_pin=False)

    def test_installed_eeex_source_markers_no_runtime_claim(self):
        r=m.source_audit(source())
        self.assertTrue(r["all_required_symbols_present"])
        self.assertEqual(r["status"],"INSTALLED_SOURCE_JIT_UNWIND_PRIMITIVES_PRESENT_RUNTIME_HOLD")
        self.assertFalse(r["installed_eeex_runtime_loaded_verified"])
        self.assertFalse(r["rtl_lookup_runtime_owner_verified"])
        self.assertFalse(r["jit_unwind_registration_runtime_verified"])

    def test_missing_eeex_function_table_disables_gate(self):
        r=m.source_audit(source(False))
        self.assertFalse(r["all_required_symbols_present"])
        self.assertEqual(r["status"],"INSTALLED_SOURCE_MISSING_REQUIRED_API_HOLD")
        self.assertEqual(r["symbol_counts"]["register_jit_function_table"],0)

    def test_no_disk_writes_and_no_game_dependency(self):
        with TemporaryDirectory(prefix="BGV132_FIXTURE_") as tmp:
            game=Path(tmp)
            (game/"Baldur.exe").write_bytes(fake_exe())
            script=game/m.ASM_PATH
            script.parent.mkdir()
            script.write_bytes(source())
            patch=game/m.PATCH_PATH
            patch.write_bytes(b"not a match")
            db=game/m.DB_PATH
            db.write_bytes(m.FIRSTCALL_LABEL.encode("ascii")+b"\0")
            before={str(p.relative_to(game)):m.sha(p.read_bytes()) for p in game.rglob("*") if p.is_file()}
            result=m.audit_game(game)
            after={str(p.relative_to(game)):m.sha(p.read_bytes()) for p in game.rglob("*") if p.is_file()}
            self.assertEqual(before,after)
            self.assertEqual(result["game_files_written"],0)
            self.assertFalse(result["native_hook_install_allowed"])
            self.assertFalse(result["eeex_existing_firstcall_owner_verified"])
            self.assertEqual(result["status"],"STATIC_SOURCE_OR_RAW_XDATA_HOLD")
            # Failure is from exact private EXE SHA; no synthetic fixture is
            # misrepresented as an installed game PASS.
            self.assertIn("BALDUR_EXE_SHA_DRIFT_HOLD",result["unwind"]["reason"])
            self.assertTrue(result["firstcall_label_present_in_db"])

    def test_empty_source_and_missing_files_safe_hold(self):
        with TemporaryDirectory() as d:
            res=m.audit_game(Path(d))
            self.assertEqual(res["status"],"STATIC_SOURCE_OR_RAW_XDATA_HOLD")
            self.assertEqual(res["game_files_written"],0)
            self.assertIn("HOLD",res["unwind"]["status"])
            self.assertFalse(res["native_hook_install_allowed"])

if __name__=="__main__":
    unittest.main()
