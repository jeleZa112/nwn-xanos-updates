"""Adversarial route preflight: no game writes, run as part of one-pass suite."""
from __future__ import annotations
import hashlib, tempfile, unittest, sys, zipfile, os
from pathlib import Path
from patchpoint_contract import (
    get_function, route_verify, target_rel32, Hold, ROUTES, CAPTURE,
    MESSAGE, NORMAL_EXIT, UPSTREAM_FIRSTCALL, BASE,
)
ARCHIVE=Path(os.environ.get('BG_EET_RU_V120_ZIP', '/mnt/data/SEND_TO_CHATGPT_BG_EET_RU(20261124-031007).zip'))
class PatchpointTests(unittest.TestCase):
    def test_original_routes_reconstruct_all_callees(self):
        report=route_verify(ARCHIVE)
        self.assertEqual(report['status'],'STATIC_ROUTE_PASS_LIVE_ABI_HOLD')
        self.assertEqual(report['callees'],{
            hex(UPSTREAM_FIRSTCALL):'0x3fcd70',hex(MESSAGE):'0x204c60',hex(NORMAL_EXIT):'0x3fce00'})
        self.assertEqual(report['passed'],18)
    def test_nonnative_unsafe_api_rejected(self):
        self.assertEqual(ROUTES['capture'][2],'EEex_HookBeforeRestoreWithLabels')
        for name in ('message','normal_exit'):
            self.assertEqual(ROUTES[name][2],'EEex_HookBeforeCallWithLabels')
            self.assertNotEqual(ROUTES[name][3],'fixed_sub_rsp')
    def test_broken_rel32_opcode_rejected(self):
        b=bytearray(get_function(ARCHIVE))
        for name in ('message','normal_exit'):
            test=bytearray(b)
            test[ROUTES[name][0]-BASE]=0x90
            with self.subTest(site=name),self.assertRaises(Hold):
                target_rel32(test,ROUTES[name][0])
    def test_call_displacements_decode_full_signed_32bit(self):
        b=get_function(ARCHIVE)
        self.assertLess(target_rel32(b,MESSAGE),MESSAGE)
        self.assertGreater(target_rel32(b,NORMAL_EXIT),NORMAL_EXIT)
        self.assertGreater(target_rel32(b,UPSTREAM_FIRSTCALL),UPSTREAM_FIRSTCALL)
    def test_unpinned_archive_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            changed=Path(td)/'untrusted.zip'
            changed.write_bytes(ARCHIVE.read_bytes()+b'altered')
            with self.assertRaisesRegex(Hold,'V120_WHOLE_ZIP_SHA_DRIFT'):
                route_verify(changed)
    def test_symbolic_instruction_compiler_is_not_runtime_install(self):
        r=route_verify(ARCHIVE)
        self.assertFalse(r['runtime_patched'])
        self.assertFalse(r['gameplay_verified'])
if __name__=='__main__':unittest.main(verbosity=2)
