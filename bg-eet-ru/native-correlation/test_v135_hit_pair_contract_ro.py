"""V135 independent source-only regression; optional private ZIP is never uploaded to GitHub."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import v135_hit_pair_contract_ro as v

class V135SourceOnly(unittest.TestCase):
    def test_exact_entry_stays_outside_31_byte_prolog(self):
        self.assertEqual(v.ENTRY-v.BASE,31)
        self.assertEqual(v.EXPECTED['after_prolog_rcx_rdx_preserved'],(0x39DA6F,'4c8bf2488bd9'))
    def test_entry_register_transfer_is_not_riprelative(self):
        self.assertEqual(bytes.fromhex(v.EXPECTED['after_prolog_rcx_rdx_preserved'][1]),
                         bytes.fromhex('4c8bf2488bd9'))
        self.assertEqual(v.EXPECTED['source_item_from_r8'][1],'4d8bf8')
        self.assertEqual(v.EXPECTED['source_ability_from_r9d'][1],'418bf1')
    def test_exact_exit_before_epilog(self):
        self.assertEqual(v.EXIT_PRE_EPILOG + 8,v.OUTPUT_RAW)
        self.assertEqual(v.OUTPUT_RAW + 4,0x39E9A7)
        self.assertEqual(v.EXPECTED['pre_epilog_exit_anchor_abi_unverified'][1],
                         '488b9c24d8000000')
        self.assertEqual(v.EXPECTED['raw_return_from_r14b'][1],'410fb6c6')
        self.assertEqual(v.EXPECTED['stack_restore_after_return_transfer'][1],
                         '4881c480000000')
    def test_bypass_skips_addmessage(self):
        rva,code=v.EXPECTED['possible_message_bypass']
        b=bytes.fromhex(code)
        target=rva+len(b)+int.from_bytes(b[2:],'little',signed=True)
        self.assertEqual(target,0x39E855)
        self.assertLess(v.EXPECTED['conditional_message_call'][0],target)
    def test_result_producer_is_not_trusted_as_semantics(self):
        self.assertEqual(v.EXPECTED['native_result_setge'],(0x39E546,'0f9dc0'))
        self.assertEqual(v.EXPECTED['native_result_store'],(0x39E549,'894540'))
        self.assertEqual(v.EXPECTED['r14d_from_stack_result'],(0x39E66F,'448b7540'))
        self.assertEqual(v.EXPECTED['r14d_from_r12d_other_path'],(0x39E717,'458bf4'))
    def test_sha_is_from_real_private_hit(self):
        self.assertEqual(len(v.HIT_SHA),64)
        self.assertEqual(len(v.ZIP_SHA),64)
    def test_reject_non_bytes(self):
        for x in (None,[],memoryview(b'x'),bytearray(v.END-v.BASE)):
            with self.assertRaisesRegex(v.Hold,'HIT_ORIGINAL_FUNCTION_LENGTH_HOLD'):
                v.exact_original_hit(x)
    def test_reject_empty_and_wrong_length(self):
        for size in (0,1,v.END-v.BASE-1,v.END-v.BASE+1):
            with self.assertRaisesRegex(v.Hold,'HIT_ORIGINAL_FUNCTION_LENGTH_HOLD'):
                v.exact_original_hit(bytes(size))
    def test_reject_forged_function_of_right_length(self):
        with self.assertRaisesRegex(v.Hold,'HIT_ORIGINAL_FUNCTION_SHA_HOLD'):
            v.exact_original_hit(bytes(v.END-v.BASE))
    def test_no_modifying_functions_in_source(self):
        src=(HERE/'v135_hit_pair_contract_ro.py').read_text('utf8')
        for m in ('WriteProcessMemory(', 'VirtualProtect(', 'OpenProcess(',
                  'EEex_JITAt(', 'EEex_HookBefore(', 'CreateRemoteThread('):
            self.assertNotIn(m,src)
    def test_lua_never_uses_game_hacks_or_guesses(self):
        src=(HERE/'BG_EET_RU_V135_PURE_LUA_ATTEMPT_BRIDGE.lua').read_text('utf8')
        for m in ('EEex_Hook', 'EEex_JIT', 'CItem::', 'WriteProcessMemory',
                  'raw_return == 0 then outcome', 'raw_return == 1 then outcome',
                  'HIT_MISS_CONFIRMED'):
            self.assertNotIn(m,src)
        self.assertIn("top.outcome = 'UNVERIFIED'",src)
        self.assertIn('OUT_OF_ORDER_EXIT_STACK_INVALIDATED',src)
    def test_no_implicit_game_promotion(self):
        for prop in ('native_hook_safe_or_installed','runtime_callback_abi_verified',
                     'return_0_is_miss_proven','return_1_is_hit_proven'):
            self.assertIn(prop,(HERE/'v135_hit_pair_contract_ro.py').read_text('utf8'))
    def test_private_zip_or_skip(self):
        archive=Path(os.environ.get('BG_EET_RU_PRIVATE_ZIP',''))
        if not archive.is_file() or archive.is_dir():
            self.skipTest('private user ZIP unavailable on public CI')
        report=v.audit_zip(archive)
        self.assertEqual(report['status'],'V135_SOURCE_PAIR_MODEL_READY_NATIVE_LIVE_HOLD')
        self.assertEqual(report['native_contract']['instruction_anchors_checked'],len(v.EXPECTED))
        self.assertFalse(report['native_contract']['return_0_is_miss_proven'])
        self.assertFalse(report['native_contract']['return_1_is_hit_proven'])
        self.assertFalse(report['runtime_pairing_installed'])
        self.assertEqual(report['game_files_written'],0)
    def test_private_real_byte_mutations_always_fail_closed(self):
        archive=Path(os.environ.get('BG_EET_RU_PRIVATE_ZIP',''))
        if not archive.is_file() or archive.is_dir():
            self.skipTest('private user ZIP unavailable on public CI')
        import zipfile
        with zipfile.ZipFile(archive) as z:
            src=z.read(v.HIT_NAME)
        anchors=list(v.EXPECTED.values())
        for rva,hexstr in anchors:
            for i in range(len(bytes.fromhex(hexstr))):
                mod=bytearray(src);mod[rva-v.BASE+i]^=1
                with self.assertRaisesRegex(v.Hold,'HIT_ORIGINAL_FUNCTION_SHA_HOLD'):
                    v.exact_original_hit(bytes(mod))
    def test_corrupt_private_zip_never_falls_back(self):
        archive=Path(os.environ.get('BG_EET_RU_PRIVATE_ZIP',''))
        if not archive.is_file() or archive.is_dir():
            self.skipTest('private user ZIP unavailable on public CI')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'fake.zip';p.write_bytes(archive.read_bytes()[:-1]+b'?')
            with self.assertRaisesRegex(v.Hold,'EXACT_USER_V133_ARCHIVE_PIN_HOLD'):
                v.audit_zip(p)

if __name__=='__main__':unittest.main(verbosity=2)
