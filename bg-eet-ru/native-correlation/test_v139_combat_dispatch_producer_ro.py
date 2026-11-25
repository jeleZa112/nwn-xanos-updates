"""V139 hostile tests with synthetic PE and sparse machine instructions only.

No user ZIP, real executable, game process, hooking, or game changes in CI.
"""
from __future__ import annotations
import hashlib
import os
import random
import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import v139_combat_dispatch_producer_ro as M


def synthetic_pe():
    b=bytearray(0x1800)
    b[:2]=b'MZ'
    struct.pack_into('<I',b,0x3c,0x80)
    b[0x80:0x84]=b'PE\0\0'
    struct.pack_into('<H',b,0x84,0x8664)
    struct.pack_into('<H',b,0x86,2)
    struct.pack_into('<H',b,0x94,0xF0)
    opt=0x98
    struct.pack_into('<H',b,opt,0x20B)
    struct.pack_into('<I',b,opt+108,16)
    struct.pack_into('<II',b,opt+112+3*8,0x3000,12)
    sec=opt+0xF0
    b[sec:sec+8]=b'.text\0\0\0'
    struct.pack_into('<IIII',b,sec+8,0x1000,0x1000,0x1000,0x400)
    struct.pack_into('<I',b,sec+36,0x60000020)
    p=sec+40
    b[p:p+8]=b'.pdata\0\0'
    struct.pack_into('<IIII',b,p+8,0x200,0x3000,0x200,0x1400)
    struct.pack_into('<I',b,p+36,0x40000040)
    struct.pack_into('<III',b,0x1400,0x1100,0x1400,0x3100)
    for i in range(0x300):b[0x500+i]=(i*17+9)&255
    b[0x1500:0x1504]=b'\x01\x00\x00\x00'
    return bytes(b)


def synthetic_source(start,end,specs):
    code=bytearray(end-start)
    for i,(call,arg,hexbytes,*_) in enumerate(specs):
        payload=bytes.fromhex(hexbytes)
        code[arg-start:arg-start+len(payload)]=payload
        disp=M.TARGET_RVA-call-5
        struct.pack_into('<Bi',code,call-start,0xE8,disp)
    return bytes(code)


class PEReaderTests(unittest.TestCase):
    def extract(self,b):
        return M.extract_pdata_function(b,rva=0x1120,expected_sha=M.digest(b))

    def test_valid_amd64_pe_function_is_bounded(self):
        b=synthetic_pe();r=self.extract(b)
        self.assertEqual(r['function_begin_rva'],'0x1100')
        self.assertEqual(r['function_end_rva'],'0x1400')
        self.assertEqual(r['function_bytes'],0x300)
        self.assertEqual(len(bytes.fromhex(r['callee_source_hex'])),0x300)
        self.assertEqual(r['callee_source_sha256'],M.digest(bytes.fromhex(r['callee_source_hex'])))
        self.assertFalse(r['verified_direct_combatlog_producer'])
        self.assertFalse(r['verified_renderer_token_source'])
        self.assertFalse(r['native_hook_installed'])

    def test_exact_exe_digest_must_match(self):
        b=synthetic_pe()
        with self.assertRaisesRegex(M.Hold,'EXACT_GAME_EXE_SHA_MISMATCH'):
            M.extract_pdata_function(b,rva=0x1120)

    def test_no_mz_or_pe_signature(self):
        for offset in (0,0x80):
            b=bytearray(synthetic_pe());b[offset]^=0xff
            with self.assertRaises(M.Hold):self.extract(bytes(b))

    def test_wrong_architecture(self):
        b=bytearray(synthetic_pe());struct.pack_into('<H',b,0x84,0x14c)
        with self.assertRaisesRegex(M.Hold,'AMD64'):
            self.extract(bytes(b))

    def test_wrong_pe32_magic(self):
        b=bytearray(synthetic_pe());struct.pack_into('<H',b,0x98,0x10b)
        with self.assertRaisesRegex(M.Hold,'PE32_PLUS'):
            self.extract(bytes(b))

    def test_missing_pdata_directory(self):
        for val in (0,11,13):
            b=bytearray(synthetic_pe());struct.pack_into('<I',b,0x98+116+3*8,val)
            with self.assertRaises(M.Hold):self.extract(bytes(b))

    def test_missing_directory_count(self):
        b=bytearray(synthetic_pe());struct.pack_into('<I',b,0x98+108,3)
        with self.assertRaisesRegex(M.Hold,'EXCEPTION_DATA_DIRECTORY'):
            self.extract(bytes(b))

    def test_pdata_entry_not_covered(self):
        b=bytearray(synthetic_pe());struct.pack_into('<II',b,0x1400,0x1600,0x1700)
        with self.assertRaisesRegex(M.Hold,'ENTRY_MISSING_OR_AMBIGUOUS'):
            self.extract(bytes(b))

    def test_overlapping_pdata_entries(self):
        b=bytearray(synthetic_pe());struct.pack_into('<I',b,0x98+116+3*8,24)
        struct.pack_into('<III',b,0x140C,0x1100,0x1400,0x3100)
        with self.assertRaisesRegex(M.Hold,'ENTRY_MISSING_OR_AMBIGUOUS'):
            self.extract(bytes(b))

    def test_function_too_long(self):
        b=bytearray(synthetic_pe());struct.pack_into('<II',b,0x1400,0x1100,0x1100+M.MAX_CALLEE_BYTES+1)
        with self.assertRaisesRegex(M.Hold,'OVER_SAFETY_LIMIT'):
            self.extract(bytes(b))

    def test_nonexecutable_target(self):
        b=bytearray(synthetic_pe());struct.pack_into('<I',b,0x98+0xF0+36,0x40000040)
        with self.assertRaisesRegex(M.Hold,'SECTION_AMBIGUOUS_OR_UNAVAILABLE'):
            self.extract(bytes(b))

    def test_truncated_or_invalid_raw_section(self):
        for raw in (0x1701,0x2000,0xffffffff):
            b=bytearray(synthetic_pe());struct.pack_into('<I',b,0x98+0xF0+20,raw)
            with self.assertRaises(M.Hold):self.extract(bytes(b))

    def test_unwind_rva_outside_sections(self):
        b=bytearray(synthetic_pe());struct.pack_into('<I',b,0x1400+8,0x8000)
        with self.assertRaises(M.Hold):self.extract(bytes(b))

    def test_target_not_inside_any_function(self):
        with self.assertRaises(M.Hold):
            M.extract_pdata_function(synthetic_pe(),rva=0x1700,expected_sha=M.digest(synthetic_pe()))

    def test_small_pe_and_huge_pe_offset_rejected(self):
        for size in (0,12,127):
            with self.assertRaises(M.Hold):
                M.extract_pdata_function(bytes(size),rva=0x1120,expected_sha=M.digest(bytes(size)))
        b=bytearray(synthetic_pe());struct.pack_into('<I',b,0x3c,0xFFFFFFF0)
        with self.assertRaises(M.Hold):self.extract(bytes(b))


class DispatchTests(unittest.TestCase):
    def test_hit_dispatch_three_exact_callers_and_args(self):
        b=synthetic_source(M.HIT_RVA,M.HIT_END,M.HIT_DISPATCH)
        result=M.verify_dispatch(b,M.HIT_RVA,M.HIT_END,M.digest(b),M.HIT_DISPATCH)
        self.assertEqual([v['numeric_edx_candidate'] for v in result],[40,3,4])
        self.assertTrue(all(v['semantic_row_type_proven'] is False for v in result))

    def test_damage_dispatch_eight_exact_callers_and_args(self):
        b=synthetic_source(M.DAMAGE_RVA,M.DAMAGE_END,M.DAMAGE_DISPATCH)
        result=M.verify_dispatch(b,M.DAMAGE_RVA,M.DAMAGE_END,M.digest(b),M.DAMAGE_DISPATCH)
        self.assertEqual([v['numeric_edx_candidate'] for v in result],[83,83,82,81,64,64,1,28])

    def test_all_eleven_pinned_argument_mutations_fail(self):
        for start,end,specs in [(M.HIT_RVA,M.HIT_END,M.HIT_DISPATCH),(M.DAMAGE_RVA,M.DAMAGE_END,M.DAMAGE_DISPATCH)]:
            base=synthetic_source(start,end,specs)
            for site,arg,expected,*_ in specs:
                for off in range(len(bytes.fromhex(expected))):
                    b=bytearray(base);b[arg-start+off]^=1
                    with self.assertRaises(M.Hold):M.verify_dispatch(bytes(b),start,end,M.digest(base),specs)

    def test_all_eleven_direct_call_mutations_fail(self):
        for start,end,specs in [(M.HIT_RVA,M.HIT_END,M.HIT_DISPATCH),(M.DAMAGE_RVA,M.DAMAGE_END,M.DAMAGE_DISPATCH)]:
            base=synthetic_source(start,end,specs)
            for site,*_ in specs:
                b=bytearray(base);b[site-start+2]^=1
                with self.assertRaises(M.Hold):M.verify_dispatch(bytes(b),start,end,M.digest(base),specs)

    def test_unexpected_additional_callsite_fail(self):
        b=bytearray(synthetic_source(M.HIT_RVA,M.HIT_END,M.HIT_DISPATCH))
        site=M.HIT_RVA+0x30
        struct.pack_into('<Bi',b,site-M.HIT_RVA,0xe8,M.TARGET_RVA-site-5)
        with self.assertRaisesRegex(M.Hold,'CALLSITE_SET_DRIFT'):
            M.verify_dispatch(bytes(b),M.HIT_RVA,M.HIT_END,M.digest(bytes(b)),M.HIT_DISPATCH)

    def test_500_adversarial_random_byte_mutations_fail(self):
        rng=random.Random(13920261125)
        b=synthetic_source(M.HIT_RVA,M.HIT_END,M.HIT_DISPATCH)
        for _ in range(500):
            x=bytearray(b);off=rng.randrange(len(x));x[off]^=1<<rng.randrange(8)
            with self.assertRaises(M.Hold):M.verify_dispatch(bytes(x),M.HIT_RVA,M.HIT_END,M.digest(b),M.HIT_DISPATCH)

    def test_real_pinned_archive_if_supplied(self):
        supplied=os.environ.get('BG_EET_RU_V139_USER_ARCHIVE')
        if not supplied:
            self.skipTest('Private user ZIP is never uploaded to GitHub CI')
        report=M.run(Path(supplied))
        self.assertEqual(report['status'],'V139_PINNED_CALLSITE_PASS_DISPATCH_CALLEE_HOLD')
        self.assertEqual([r['numeric_edx_candidate'] for r in report['hit_calls']],[40,3,4])
        self.assertEqual([r['numeric_edx_candidate'] for r in report['damage_calls']],[83,83,82,81,64,64,1,28])
        self.assertEqual(report['displayed_rows'],72)
        self.assertFalse(report['call_target_to_ui_chain_verified'])
        self.assertEqual(report['game_files_written'],0)

    def test_no_runtime_write_in_source(self):
        src=Path(M.__file__).read_text('utf8')
        for danger in ('WriteProcessMemory(', 'VirtualProtect(', 'CreateRemoteThread(',
                       'EEex_JITAt(', 'EEex_HookBefore(', 'Infinity_DisplayString(',
                       'patch_exe(', 'write_bytes('):
            self.assertNotIn(danger,src)
        self.assertIn("'game_files_written':0",src)

    def test_real_private_zip_is_not_embedded_in_source(self):
        src=Path(M.__file__).read_text('utf8')
        self.assertNotIn('SEND_TO_CHATGPT_BG_EET_RU(20261125-162331).zip',src)
        self.assertFalse((Path(__file__).parent/'private_user_capture.zip').exists())


if __name__=='__main__':unittest.main(verbosity=2)
