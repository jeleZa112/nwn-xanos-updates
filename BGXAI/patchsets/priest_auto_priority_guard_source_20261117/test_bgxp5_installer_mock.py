#!/usr/bin/env python3
"""Guarded BGXP5 mock install and rollback; NEVER start WeiDU or change EET."""
from __future__ import annotations
import hashlib,json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch

import BGXP5_INSTALL as I
import BGXP5_BCS_PREFLIGHT_READ_ONLY as N


def create(root:Path,rel:str,data:bytes):
    path=root/rel
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(data)
    return path


def chunk(tag:bytes=b"BASE")->bytes:
    return b"CR\nCO\nTR\nRS\nRE\nRS\n"+tag+b"\nCR\n"


class BGXP5GuardedMock(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/"BG_EET_FOXX_NEW"
        self.root.mkdir()
        self.pre_blocks=[chunk(b"BASE") for _ in range(1154)]+[chunk(b"COMBAT") for _ in range(4)]
        self.old=b"SC\n"+b"".join(self.pre_blocks)+b"SC\n"
        self.new=b"SC\n"+chunk(b"HEAL")*12+b"".join(self.pre_blocks[:-4])+chunk(b"SAFE")*4+b"SC\n"
        self.base_log=b"~BGXP3\\SETUP-BGXP3.TP2~ #0 #0 // existing\n"
        create(self.root,I.BCS_PATH,self.old)
        create(self.root,I.LUA_PATH,b"Lua preserved")
        create(self.root,"WeiDU.log",self.base_log)
        create(self.root,I.WEIDU_PATH,b"MZ"+b"x"*130000)
        for rel in ("chitin.key","weidu.conf","lang/ru_RU/dialog.tlk","lang/ru_RU/dialogf.tlk"):
            create(self.root,rel,b"existing")
        self.pin_bcs=N.BCS_PIN
        self.pin_lua=N.LUA_PIN
        N.BCS_PIN=hashlib.sha256(self.old).hexdigest()
        N.LUA_PIN=hashlib.sha256(b"Lua preserved").hexdigest()
        self.addCleanup(lambda: setattr(N,"BCS_PIN",self.pin_bcs))
        self.addCleanup(lambda: setattr(N,"LUA_PIN",self.pin_lua))
        create(self.root,"BGXP3/STAGED_PROOF.json",json.dumps(
            {"new_bcs_sha256":N.BCS_PIN,"lua_sha256":N.LUA_PIN}).encode())
        self.oldhome=os.environ.get("USERPROFILE")
        os.environ["USERPROFILE"]=str(Path(self.tmp.name)/"HOME")
        self.addCleanup(self.restore_home)
        self.events=[]

    def restore_home(self):
        if self.oldhome is None:os.environ.pop("USERPROFILE",None)
        else:os.environ["USERPROFILE"]=self.oldhome

    def native_candidate(self,root):
        return self.new,{"candidate_bcs_sha256":hashlib.sha256(self.new).hexdigest(),
                         "old_blocks_preserved_exact":1154}

    def fake_wei(self,root,uninstall=False):
        self.events.append("ROLLBACK" if uninstall else "INSTALL")
        if uninstall:
            create(root,I.BCS_PATH,(root/I.RESTORE_COPY).read_bytes())
            create(root,"WeiDU.log",self.base_log)
        else:
            create(root,I.BCS_PATH,(root/I.STAGED).read_bytes())
            create(root,"WeiDU.log",self.base_log+b"~BGXP5\\SETUP-BGXP5.TP2~ #0 #0 // mock\n")
        return "FAKE_SUCCESS"

    def test_source_integrity(self):
        self.assertEqual(I.sources()["schema"],1)

    def test_readonly_baseline(self):
        old=self.old
        state=I.base(self.root)
        self.assertEqual(state["state"],"BGXP3_INSTALLED_VERIFIED")
        self.assertEqual((self.root/I.BCS_PATH).read_bytes(),old)

    def test_native_preflight_mock_readonly(self):
        with patch.object(I,"native_candidate",side_effect=self.native_candidate):
            result=I.preflight(self.root)
        self.assertFalse(result["game_modified"])
        self.assertFalse((self.root/"BGXP5").exists())
        self.assertEqual(result["patch"]["old_blocks_preserved_exact"],1154)

    def test_synthetic_install_and_rollback(self):
        with patch.object(I,"running_guard"),\
             patch.object(I,"native_candidate",side_effect=self.native_candidate),\
             patch.object(I,"wei",side_effect=self.fake_wei):
            installed=I.install(self.root)
            self.assertEqual(installed["status"],"BGXP5_INSTALLED_VERIFIED")
            self.assertEqual((self.root/I.BCS_PATH).read_bytes(),self.new)
            self.assertTrue((Path(installed["backup"])/"PROOF.json").exists())
            rollback=I.rollback(self.root)
            self.assertEqual(rollback["status"],"BGXP5_RETURNED_TO_BGXP3_VERIFIED")
            self.assertEqual((self.root/I.BCS_PATH).read_bytes(),self.old)
            self.assertEqual(self.events,["INSTALL","ROLLBACK"])

    def test_refuse_other_last_weidu(self):
        create(self.root,"WeiDU.log",b"~OTHER\\SETUP-OTHER.TP2~ #0 #0\n")
        with self.assertRaisesRegex(I.Stop,"BGXP3_MUST_BE_LAST"):
            I.base(self.root)

    def test_refuse_tampered_bcs(self):
        create(self.root,I.BCS_PATH,self.old+b"X")
        with self.assertRaisesRegex(I.Stop,"LIVE_BGXP3_BCS_OR_LUA_SHA_MISMATCH"):
            I.base(self.root)

    def test_refuse_tampered_lua(self):
        create(self.root,I.LUA_PATH,b"corrupt")
        with self.assertRaisesRegex(I.Stop,"LIVE_BGXP3_BCS_OR_LUA_SHA_MISMATCH"):
            I.base(self.root)

    def test_refuse_existing_staging(self):
        (self.root/"BGXP5").mkdir()
        with self.assertRaisesRegex(I.Stop,"STAGING_COLLISION"):
            I.base(self.root)

    def test_refuse_without_typed_approval(self):
        self.assertEqual(I.main(["install","--game-root",str(self.root)]),2)
        self.assertEqual(I.main(["install","--yes","--confirm","WRONG",
                                 "--game-root",str(self.root)]),2)

    def test_refuse_wrong_root_even_approved(self):
        self.assertEqual(I.main(["install","--yes","--confirm",I.INSTALL_TOKEN,
                                 "--game-root",str(self.root)]),2)

    def test_rollback_only_if_last(self):
        with self.assertRaisesRegex(I.Stop,"BGXP5_NOT_LAST_WEIDU"):
            I.installed(self.root)


if __name__=="__main__":
    unittest.main(verbosity=2)
