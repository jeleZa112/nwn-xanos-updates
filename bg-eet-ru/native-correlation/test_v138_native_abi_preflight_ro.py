"""Adversarial COFF and pinned-real-archive tests for V138, no game changes."""
from __future__ import annotations
import os,struct,unittest
from pathlib import Path
import v138_native_abi_preflight_ro as M

DIR=Path(__file__).resolve().parent
WIN=DIR/'v138_native_attempt_ledger_win64.obj'
USER=DIR/'v138_pinned_user_capture.zip'

class ProofTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not WIN.is_file():raise unittest.SkipTest('Win64 COFF compile first')
        cls.data=WIN.read_bytes()

    def section(self,name):
        data=self.data
        n=struct.unpack_from('<H',data,2)[0]
        for i in range(n):
            off=20+i*40
            if struct.unpack_from('<8s',data,off)[0].rstrip(b'\0')==name.encode():
                x=struct.unpack_from('<8sLLLLLLHHL',data,off)
                return off,x
        self.fail('COFF section not found: '+name)

    def denied(self,data,reason=None):
        with self.assertRaises(M.Hold) as cm:
            M.audit_coff(bytes(data))
        if reason:self.assertIn(reason,str(cm.exception))
    def test_valid_win64_coff_two_function_tables(self):
        r=M.audit_coff(self.data)
        self.assertTrue(r['win64_compiler_emitted_pdata_xdata'])
        self.assertEqual(r['unwind_entries_count'],2)
        self.assertFalse(r['actual_runtime_registration_verified'])
        self.assertFalse(r['native_hook_or_injection_performed'])
    def test_zero_input_denied(self):self.denied(b'', 'TRUNCATED')
    def test_mixed_architecture_denied(self):
        b=bytearray(self.data);struct.pack_into('<H',b,0,0x14c)
        self.denied(b,'NOT_AMD64')
    def test_missing_unwind_pdata_denied(self):
        b=bytearray(self.data);off,_=self.section('.pdata');b[off:off+8]=b'.qdata\0\0'
        self.denied(b,'SECTION_MISSING')
    def test_missing_unwind_xdata_denied(self):
        b=bytearray(self.data);off,_=self.section('.xdata');b[off:off+8]=b'.qdata\0\0'
        self.denied(b,'SECTION_MISSING')
    def test_missing_entry_relocation_denied(self):
        b=bytearray(self.data);off,x=self.section('.pdata');struct.pack_into('<H',b,off+32,2)
        self.denied(b,'RELOCATION_COUNT')
    def test_bad_relocation_kind_denied(self):
        b=bytearray(self.data);off,x=self.section('.pdata');struct.pack_into('<H',b,x[5]+8,4)
        self.denied(b,'RELOCATION_INVALID')
    def test_relocation_symbol_mismatch_denied(self):
        b=bytearray(self.data);off,x=self.section('.pdata');struct.pack_into('<L',b,x[5]+10+4,99)
        self.denied(b,'RELOCATION_SYMBOL_INVALID')
    def test_unwind_table_outside_raw_denied(self):
        b=bytearray(self.data);off,x=self.section('.pdata');struct.pack_into('<L',b,off+20,999999999)
        self.denied(b,'SECTION_DATA_OUT_OF_BOUNDS')
    def test_unwind_record_missing_version_denied(self):
        b=bytearray(self.data);off,x=self.section('.xdata');b[x[4]]=0
        self.denied(b,'XDATA_HEADER_INVALID')
    def test_empty_unwind_code_count_denied(self):
        b=bytearray(self.data);off,x=self.section('.xdata');b[x[4]+2]=0
        self.denied(b,'XDATA_HEADER_INVALID')
    def test_bad_xdata_pointer_denied(self):
        b=bytearray(self.data);off,x=self.section('.xdata');struct.pack_into('<L',b,off+20,0)
        self.denied(b,'SECTION_DATA_OUT_OF_BOUNDS')
    def test_relocated_function_bounds_denied(self):
        b=bytearray(self.data);off,x=self.section('.pdata');struct.pack_into('<L',b,x[4]+4,1)
        self.denied(b,'PDATA_ENTRY_INVALID')
    def test_truncated_pdata_length_denied(self):
        b=bytearray(self.data);off,x=self.section('.pdata');struct.pack_into('<L',b,off+16,11)
        self.denied(b,'INVALID_LENGTH')
    def test_truncated_coff_file_denied(self):self.denied(self.data[:40])
    def test_user_v136_real_archive_exact_if_provided(self):
        if not USER.is_file():self.skipTest('No project user archive mounted in CI (expected)')
        result=M.audit_user_archive(USER.read_bytes())
        self.assertTrue(result['message_bypass_verified'])
        self.assertFalse(result['renderer_direct_token_available'])
        self.assertFalse(result['native_live_owner_verified'])
    def test_user_archive_checksum_mismatch_fails_closed(self):
        self.assertRaisesRegex(M.Hold,'PIN_DRIFT',M.audit_user_archive,b'not-a-user-zip')
    def test_pinned_user_archive_never_rewritten(self):
        s=Path(M.__file__).read_text(encoding='utf8')
        for forbidden in ('WriteProcessMemory(', 'CreateRemoteThread(', 'VirtualProtectEx(',
                          'SetThreadContext(', 'EEex_JITAt(', 'EEex_HookAfterCall('):
            self.assertNotIn(forbidden,s)

if __name__=='__main__':unittest.main(verbosity=2)
