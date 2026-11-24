"""Independent adversarial SOURCE tests; no game or native hook execution."""
import unittest, zipfile, tempfile, sys, json, shutil, os
from pathlib import Path
from pilot_static_gates import verify, SITES, BASE, FUNC, PINNED_ARCHIVE

BASE_DIR=Path(__file__).resolve().parent
ARCHIVE=Path(os.environ.get('BG_EET_RU_V120_ZIP', '/mnt/data/SEND_TO_CHATGPT_BG_EET_RU(20261124-031007).zip'))
LUA=BASE_DIR/'BG_EET_RU_HIT_PILOT_DRAFT.lua'

class TestPilot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with zipfile.ZipFile(ARCHIVE) as z:
            cls.data={i.filename:z.read(i.filename) for i in z.infolist()}
    def test_original_passes_and_is_source_only(self):
        r=verify(ARCHIVE,LUA)
        self.assertEqual(r['status'],'SOURCE_PASS_RUNTIME_HOLD')
        self.assertEqual(r['passed'],r['total'])
        self.assertFalse(r['gameplay_tested'])
        self.assertFalse(r['native_hooks_installed'])
    def test_all_evidence_slots_mutated_fail(self):
        for key,(rva,hexb) in SITES.items():
            with self.subTest(key=key),tempfile.TemporaryDirectory() as t:
                data=self.data.copy();b=bytearray(data[FUNC]);b[rva-BASE] ^= 1;data[FUNC]=bytes(b)
                path=Path(t)/'tampered.zip'
                with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as z:
                    for k,v in data.items():z.writestr(k,v)
                x=verify(path,LUA)
                self.assertEqual(x['status'],'SOURCE_INVALID_HOLD')
                self.assertFalse(x['checks']['byte_'+key])
    def test_different_lua_sources_fail(self):
        snippets=[b'authorized_install = false',b'runtime_abi_verified = false',
                  b'atomic_three_hook_install_verified = false',b'capture=first-0x1E',
                  b'P.active[frame]={weapon=ref:upper()',
                  b"return false,'RUNTIME_HOOK_IMPLEMENTATION_NOT_VERIFIED'",
                  b'P.active[frame]=nil;P.blocked[frame]=nil',b'max_active = 128',b'max_samples = 64']
        for pattern in snippets:
            with self.subTest(pattern=pattern),tempfile.TemporaryDirectory() as t:
                src=Path(t)/'bad.lua';src.write_bytes(LUA.read_bytes().replace(pattern,pattern.replace(b'false',b'true') if b'false' in pattern else b'BROKEN'))
                x=verify(ARCHIVE,src)
                self.assertEqual(x['status'],'SOURCE_INVALID_HOLD')
    def test_old_unsafe_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            src=Path(t)/'unsafe.lua';src.write_bytes(LUA.read_bytes().replace(b'capture=first-0x1E',b'capture=first-0x11'))
            r=verify(ARCHIVE,src)
            self.assertEqual(r['status'],'SOURCE_INVALID_HOLD')
            self.assertFalse(r['checks']['never_use_old_site_for_capture'])
    def test_unapproved_jit_is_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            src=Path(t)/'unsafe.lua';src.write_bytes(LUA.read_bytes()+b'\nEEex_JITAt(0x0,{})\n')
            r=verify(ARCHIVE,src)
            self.assertFalse(r['checks']['no_runtime_hook_calls'])
    def test_zip_extra_entry_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            path=Path(t)/'extra.zip';shutil.copy2(ARCHIVE,path)
            with zipfile.ZipFile(path,'a') as z:z.writestr('SNEAK','unexpected')
            r=verify(path,LUA)
            self.assertEqual(r['status'],'SOURCE_INVALID_HOLD')
            self.assertFalse(r['checks']['exact_v120_archive'])
    def test_not_deployed(self):
        self.assertNotIn(b'EEex_HookBeforeCallWithLabels(',LUA.read_bytes())
        self.assertNotIn(b'EEex_HookBeforeRestoreWithLabels(',LUA.read_bytes())

if __name__=='__main__':unittest.main(verbosity=2)