"""Synthetic PE32+ x64 .pdata/.xdata tests. No user game bytes in CI."""
import struct
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import pe_unwind_entry_gate_v130 as g

def fixture(prologue=31,flags=0,flags_mask=0):
    # Synthetic minimal PE with exact pinned Hit() prologue+epilogue only.
    # This is NOT the actual Baldur.exe and never clears real-game ABI gates.
    buf=bytearray(0x3000)
    buf[0:2]=b"MZ"
    struct.pack_into("<I",buf,0x3c,0x80)
    buf[0x80:0x84]=b"PE\x00\x00"
    coff=0x84
    struct.pack_into("<HHIIIHH",buf,coff,0x8664,3,0,0,0,0xF0,0x22)
    opt=coff+20
    struct.pack_into("<H",buf,opt,0x20b)
    struct.pack_into("<I",buf,opt+0x6c,16)
    struct.pack_into("<II",buf,opt+0x70+3*8,0x600000,12)
    sec=opt+0xF0
    for index,(name,rva,raw,size) in enumerate([
        (b".text",0x39D000,0x400,0x2000),
        (b".pdata",0x600000,0x2400,0x200),
        (b".xdata",0x601000,0x2600,0x200)]):
        at=sec+index*40
        buf[at:at+8]=name.ljust(8,b"\0")
        struct.pack_into("<IIII",buf,at+8,size,rva,size,raw)
    def putcode(rva,data):
        i=0x400+rva-0x39D000
        buf[i:i+len(data)]=data
    putcode(g.BEGIN,g.CODE_PREFIX)
    putcode(0x39E9A7,g.EXIT_BYTES)
    putcode(g.EEEX_UPSTREAM,bytes.fromhex("e8e5f20500"))
    # .pdata RUNTIME_FUNCTION of the precise native Hit() range.
    struct.pack_into("<III",buf,0x2400,g.BEGIN,g.FUNCTION_BODY_END,0x601000)
    # 11 slots: ALLOC_SMALL 0x80, SET_FPREG, seven pushes,
    # and a SAVE_NONVOL RBX with one extra offset slot.
    slots=[
        (31,0xF2),(24,0x03),(21,0xF0),(19,0xE0),
        (17,0xD0),(15,0xC0),(13,0x70),(12,0x60),
        (11,0x50),(5,0x34),(27,0x00)]
    buf[0x2600:0x2604]=bytes([1|(flags<<3),prologue,len(slots),0x85])
    for i,(off,op) in enumerate(slots):
        buf[0x2604+i*2:0x2604+i*2+2]=bytes([off,op])
    return bytes(buf)

class Unwind(unittest.TestCase):
    def test_exact_original_code_candidate_only_after_unwind_prolog(self):
        r=g.inspect_pe(fixture(),pin_exe=False)
        self.assertEqual(r["status"],"POST_PROLOGUE_CANDIDATE_STATIC_PASS_RUNTIME_HOLD")
        self.assertTrue(r["static_candidate_gate"])
        self.assertEqual(r["prologue_length"],31)
        self.assertTrue(r["old_sub_rsp_in_prologue"])
        self.assertTrue(r["new_candidate_after_prologue"])
        self.assertEqual(r["candidate_rva"],"0x39da6f")
        self.assertEqual(r["candidate_length"],6)
        self.assertEqual(len(r["unwind_operations"]),10)
        self.assertEqual(r["unwind_frame_register"],5)
        self.assertEqual(r["unwind_frame_offset_scaled_16"],8)
        self.assertFalse(r["native_hook_install_allowed"])
        self.assertFalse(r["native_abi_xmm_verified"])
        self.assertFalse(r["eeex_existing_hook_owner_verified"])
        self.assertFalse(r["gameplay_verified"])

    def test_candidate_inside_longer_prologue_must_hold(self):
        r=g.inspect_pe(fixture(prologue=37),pin_exe=False)
        self.assertEqual(r["status"],"UNWIND_OR_PROLOGUE_PLACEMENT_HOLD")
        self.assertFalse(r["new_candidate_after_prologue"])
        self.assertFalse(r["static_candidate_gate"])

    def test_short_prologue_with_later_unwind_ops_is_corrupt(self):
        with self.assertRaisesRegex(g.Hold,"UNWIND_CODE_AFTER_PROLOGUE"):
            g.inspect_pe(fixture(prologue=20),pin_exe=False)

    def test_ehandler_unwind_flags_prevent_static_candidate_pass(self):
        r=g.inspect_pe(fixture(flags=1),pin_exe=False)
        self.assertEqual(r["status"],"UNWIND_OR_PROLOGUE_PLACEMENT_HOLD")
        self.assertTrue(r["handler_or_chain_present"])
        self.assertFalse(r["static_candidate_gate"])

    def test_actual_executable_exact_sha_is_mandatory(self):
        with self.assertRaisesRegex(g.Hold,"EXACT_GAME_EXE_SHA_MISMATCH"):
            g.inspect_pe(fixture(),pin_exe=True)

    def test_all_pinned_instr_bytes_fail_closed_if_changed(self):
        reference=fixture()
        targets=[g.BEGIN,g.BEGIN+8,g.OLD_SITE,g.PROPOSED_SITE,
                 g.UNSAFE_SITE,0x39E9A7,g.EEEX_UPSTREAM]
        for target in targets:
            with self.subTest(hex(target)):
                buf=bytearray(reference)
                buf[0x400+target-0x39D000]^=1
                with self.assertRaisesRegex(g.Hold,"DRIFT"):
                    g.inspect_pe(bytes(buf),pin_exe=False)

    def test_unwind_not_present_and_wrong_machine_rejected(self):
        b=bytearray(fixture())
        b[0x84:0x86]=b"\x4c\x01"  # i386
        with self.assertRaisesRegex(g.Hold,"AMD64"):
            g.inspect_pe(bytes(b),pin_exe=False)
        b=bytearray(fixture())
        struct.pack_into("<I",b,0x2400+4,g.BEGIN-1)
        with self.assertRaises(g.Hold):
            g.inspect_pe(bytes(b),pin_exe=False)

    def test_missing_xdata_and_bad_opcode_deny(self):
        b=bytearray(fixture())
        struct.pack_into("<I",b,0x2400+8,0x800000)
        with self.assertRaisesRegex(g.Hold,"RVA_SECTION"):
            g.inspect_pe(bytes(b),pin_exe=False)
        b=bytearray(fixture())
        b[0x2600+4+1]=0x07
        with self.assertRaisesRegex(g.Hold,"UNWIND_OPCODE_UNSUPPORTED"):
            g.inspect_pe(bytes(b),pin_exe=False)

    def test_duplicate_containing_functions_denied(self):
        b=bytearray(fixture())
        struct.pack_into("<I",b,0x84+20+0x70+3*8+4,24)
        struct.pack_into("<III",b,0x240c,g.BEGIN,g.FUNCTION_BODY_END,0x601000)
        with self.assertRaisesRegex(g.Hold,"FUNCTION_COUNT"):
            g.inspect_pe(bytes(b),pin_exe=False)

    def test_game_input_name_and_no_symlink(self):
        with TemporaryDirectory() as d:
            x=Path(d)/"Baldur.exe"
            x.write_bytes(fixture())
            with self.assertRaisesRegex(g.Hold,"EXACT_GAME_EXE_SHA_MISMATCH"):
                g.inspect_game_exe(x)
            y=Path(d)/"not-game.exe"
            y.write_bytes(fixture())
            with self.assertRaisesRegex(g.Hold,"NAME_MISMATCH"):
                g.inspect_game_exe(y)

if __name__=="__main__":
    unittest.main()
