#!/usr/bin/env python3
"""BGXAI 118 mock six-party test save: only Jaheira race 8 bytes may change."""
from __future__ import annotations
import json
from pathlib import Path
from unittest import mock
import hashlib
import struct
import tempfile
import unittest

import BGXAI_AOE_AUDIT as A
import BGXAI_TEST6_SAFE_COPY as S


def fixture() -> bytes:
    raw=bytearray(20000)
    raw[:8]=b"GAMEV2.0"
    struct.pack_into("<I",raw,0x20,0xB4)
    struct.pack_into("<I",raw,0x24,6)
    for i,name in enumerate(S.SLOT_NAMES):
        slot=0xB4+S.ENTRY_SIZE*i
        cre=0x2000+i*0x350
        struct.pack_into("<I",raw,slot+4,cre)
        struct.pack_into("<I",raw,slot+8,0x300)
        raw[slot+0xC0:slot+0xE0]=name.encode().ljust(32,b"\0")
        raw[cre:cre+8]=b"CRE V1.0"
        raw[cre+0x250:cre+0x258]=b"BDDEFAI\0"
        raw[cre+0x258:cre+0x260]=b"None\0\0\0\0"
        if i==5:
            raw[cre+0x248:cre+0x250]=b"JAHEIRA_"
            raw[cre+0x258:cre+0x260]=b"PRIEST1\0"
    return bytes(raw)


class SafeSave(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name)
        self.root=self.base/"game"
        self.root.mkdir()
        self.saveroot=self.base/"save"
        self.saveroot.mkdir()
        self.src=self.saveroot/S.SOURCE_SLOT
        self.src.mkdir()
        (self.src/"BALDUR.gam").write_bytes(fixture())
        (self.src/"BALDUR.SAV").write_bytes(b"unchanged area save")
        (self.src/"BALDUR.bmp").write_bytes(b"image")
        self.original_sha=A.digest((self.src/"BALDUR.gam").read_bytes())
        self.oldgame=A.GAME
        A.GAME=self.root
        self.addCleanup(lambda:setattr(A,"GAME",self.oldgame))

    def test_exactly_eight_bytes_changed(self):
        original=fixture()
        new,proof=S.alter_gam(original)
        self.assertEqual(len(original),len(new))
        diff=[i for i,(a,b) in enumerate(zip(original,new)) if a!=b]
        self.assertTrue(all(0 <= i-proof["modified_offset"] < 8 for i in diff))
        self.assertEqual(new[proof["modified_offset"]:proof["modified_offset"]+8],b"None\0\0\0\0")
        self.assertEqual(original[proof["modified_offset"]:proof["modified_offset"]+8],b"PRIEST1\0")
        self.assertEqual(proof["modified_bytes"],8)

    def test_main_copy_exact_preserves_source_and_other_files(self):
        with mock.patch.object(A,"checked",return_value=(b"",b"",b"","BGXP5")),\
             mock.patch.object(S,"guard_no_running_game",return_value=None),\
             mock.patch.object(S.os,"name","nt"):
            result=S.new_copy(self.root,self.saveroot,S.TOKEN,True)
        dst=self.saveroot/S.TARGET_SLOT
        self.assertEqual(result["status"],"BGXAI_TEST6_NO_PRIEST1_COPY_VERIFIED")
        self.assertEqual(A.digest((self.src/"BALDUR.gam").read_bytes()),self.original_sha)
        self.assertEqual(A.digest((dst/"BALDUR.gam").read_bytes()),result["new_gam_sha256"])
        self.assertEqual((dst/"BALDUR.SAV").read_bytes(),(self.src/"BALDUR.SAV").read_bytes())
        self.assertFalse(result["game_modified"])
        self.assertTrue(result["only_new_test_save_created"])
        with self.assertRaisesRegex(ValueError,"ALREADY_EXISTS"):
            with mock.patch.object(A,"checked",return_value=None),\
                 mock.patch.object(S,"guard_no_running_game",return_value=None),\
                 mock.patch.object(S.os,"name","nt"):
                S.new_copy(self.root,self.saveroot,S.TOKEN,True)

    def test_refuses_without_exact_approval(self):
        with self.assertRaisesRegex(ValueError,"EXPLICIT_TEST_SAVE_COPY_APPROVAL_REQUIRED"):
            S.new_copy(self.root,self.saveroot,"",False)
        with self.assertRaisesRegex(ValueError,"EXPLICIT_TEST_SAVE_COPY_APPROVAL_REQUIRED"):
            S.new_copy(self.root,self.saveroot,"NO",True)
        self.assertFalse((self.saveroot/S.TARGET_SLOT).exists())

    def test_wrong_party_or_missing_priest1_aborts(self):
        data=bytearray(fixture())
        data[0xB4+5*S.ENTRY_SIZE+0xC0:0xB4+5*S.ENTRY_SIZE+0xC0+7]=b"NOTJAH!"
        with self.assertRaisesRegex(ValueError,"WRONG_TEST_PARTY"):
            S.alter_gam(data)
        raw=bytearray(fixture())
        pos=0x2000+5*0x350+0x258
        raw[pos:pos+8]=b"None\0\0\0\0"
        with self.assertRaisesRegex(ValueError,"NOT_PRIEST1"):
            S.alter_gam(raw)

    def test_wrong_class_script_aborts(self):
        raw=bytearray(fixture())
        pos=0x2000+5*0x350+0x250
        raw[pos:pos+8]=b"OTHER\0\0\0"
        with self.assertRaisesRegex(ValueError,"BGXP5_CLASS_SCRIPT_REQUIRED"):
            S.alter_gam(raw)

    def test_refuses_non_test_directory_files(self):
        (self.src/"SETUP.EXE").write_bytes(b"unsafe")
        with self.assertRaisesRegex(ValueError,"UNEXPECTED_FILE"):
            S.files(self.src)

    def test_cannot_modify_main_game_or_save_without_copy(self):
        source=Path(S.__file__).read_text("utf-8")
        for forbidden in ("--force-install","--force-uninstall","WeiDU.exe --install"):
            self.assertNotIn(forbidden,source)
        self.assertIn("TARGET_TEST_SAVE_ALREADY_EXISTS_NO_OVERWRITE",source)
        self.assertIn("EXPLICIT_TEST_SAVE_COPY_APPROVAL_REQUIRED",source)


if __name__=="__main__":
    unittest.main(verbosity=2)
