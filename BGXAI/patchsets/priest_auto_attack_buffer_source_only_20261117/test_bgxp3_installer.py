#!/usr/bin/env python3
"""Isolated BGXP3 install/rollback simulation; never runs WeiDU or writes live EET."""
from __future__ import annotations
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import BGXP3_INSTALL as I
import BGXP3_BCS_PREFLIGHT_SOURCE_ONLY as Q
import BGXP2_BCS_PATCH as P

def block(actions, marker=b"45"):
    raw=b"CR\nCO\nTR\nRS\nRE\nRS\nBGXR_ROLE BGX38_GUARD BGX66_S_HEAL_SLOT "+marker+b"\n"
    for a in actions:
        raw+=b"AC\n"+str(a).encode()+b"OB\nx\n"
    return raw+b"CR\n"

def put(root,name,data):
    dst=root/name;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(data)
    return dst

class TestGuardedBGXP3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        a=[[115,31]]*24+[[115,31],[115,105],[115,31],[115,105]]
        cls.old=b"SC\n"+b"".join(block(x) for x in a)+b"SC\n"
        cls.new=b"SC\n"+b"".join(block(x,b"60" if i==27 else b"45") for i,x in enumerate(a))+b"SC\n"
        cls.live=b"SC\n"+block([115,31])*1130+cls.old[3:]
        cls.changed,cls.delta=Q.assemble(cls.live,cls.old,cls.new,hashlib.sha256(cls.live).hexdigest())

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/"BG_EET_FOXX_NEW"
        self.root.mkdir()
        self.base_log=b"~BGXP2\\SETUP-BGXP2.TP2~ #0 #0 // verified old\n"
        put(self.root,"WeiDU.log",self.base_log)
        put(self.root,I.BCS,self.live)
        put(self.root,I.LUA,b"LUA_unchanged")
        put(self.root,I.WEIDU,b"MZ"+b"X"*120000)
        put(self.root,"chitin.key",b"CHITIN")
        put(self.root,"weidu.conf",b"language=ru_ru\n")
        put(self.root,"lang/ru_RU/dialog.tlk",b"mock language")
        put(self.root,"lang/ru_RU/dialogf.tlk",b"mock female language")
        put(self.root,"BGXP2/STAGED_PROOF.json",json.dumps({
            "new_bcs_sha256":hashlib.sha256(self.live).hexdigest(),
            "lua_sha256":hashlib.sha256(b"LUA_unchanged").hexdigest()
        }).encode())
        self.h1=patch.object(Q,"LIVE_BCS_SHA",hashlib.sha256(self.live).hexdigest())
        self.h2=patch.object(Q,"LIVE_LUA_SHA",hashlib.sha256(b"LUA_unchanged").hexdigest())
        self.h1.start();self.h2.start()
        self.addCleanup(self.h1.stop);self.addCleanup(self.h2.stop)
        self.oldhome=os.environ.get("USERPROFILE")
        os.environ["USERPROFILE"]=str(Path(self.tmp.name)/"home")
        self.addCleanup(self.restore_home)
        self.calls=[]

    def restore_home(self):
        if self.oldhome is None: os.environ.pop("USERPROFILE",None)
        else: os.environ["USERPROFILE"]=self.oldhome

    def fake_compile(self,game,weidu,tlk,baf):
        raw=baf.read_bytes()
        expected=I.BUFFER.candidate(I.BUFFER.SOURCE.read_bytes())
        if raw.replace(b"\r\n",b"\n")==I.BUFFER.SOURCE.read_bytes().replace(b"\r\n",b"\n"):
            return self.old
        self.assertEqual(raw,expected)
        return self.new

    def fake_native(self,root):
        return {**self.delta,"game_modified":False,"candidate_baf_sha256":"mock",
                "compiled_fragment_sha256":"mock"}

    def fake_weidu(self,root,uninstall=False):
        self.calls.append("rollback" if uninstall else "install")
        if uninstall:
            put(root,I.BCS,(root/I.OLD).read_bytes())
            put(root,"WeiDU.log",self.base_log)
        else:
            put(root,I.BCS,(root/I.STAGED).read_bytes())
            put(root,"WeiDU.log",self.base_log+b"~BGXP3\\SETUP-BGXP3.TP2~ #0 #0 // mock\n")
        return "MOCK_WEIDU_OK"

    def test_01_release_sources_sha_gates(self):
        self.assertTrue(I.sources())

    def test_02_preflight_read_only_baseline(self):
        original=(self.root/I.BCS).read_bytes()
        with patch.object(Q,"preflight",side_effect=self.fake_native):
            report=I.preflight(self.root)
        self.assertFalse(report["authorized_to_install"])
        self.assertEqual(report["patch"]["preserved_blocks_exact"],1157)
        self.assertEqual((self.root/I.BCS).read_bytes(),original)
        self.assertFalse((self.root/"BGXP3").exists())

    def test_03_full_synthetic_weiDU_install_rollback(self):
        with patch.object(Q,"preflight",side_effect=self.fake_native), \
             patch.object(P,"compile_fragment",side_effect=self.fake_compile), \
             patch.object(I,"guard_processes"), \
             patch.object(I,"weidu",side_effect=self.fake_weidu):
            outcome=I.install(self.root)
            self.assertEqual(outcome["status"],"BGXP3_INSTALLED_VERIFIED")
            self.assertEqual(outcome["after"]["preserved_blocks"],1157)
            self.assertEqual((self.root/I.BCS).read_bytes(),self.changed)
            self.assertTrue((Path(outcome["backup"])/"PROOF.json").exists())
            rollback=I.rollback(self.root)
            self.assertEqual(rollback["status"],"BGXP3_ROLLED_BACK_TO_BGXP2")
            self.assertEqual((self.root/I.BCS).read_bytes(),self.live)
            self.assertEqual(self.calls,["install","rollback"])

    def test_04_tamper_prevented_before_stage(self):
        put(self.root,I.BCS,b"TAMPER")
        with self.assertRaisesRegex(I.Stop,"EXISTING_BGXP2_BCS_CHANGED"):
            I.base(self.root)
        self.assertFalse((self.root/"BGXP3").exists())

    def test_05_unapproved_install_never_runs(self):
        with patch.object(I,"install",side_effect=AssertionError("unsafe call")):
            self.assertEqual(I.main(["install","--game-root",str(self.root)]),2)
            self.assertEqual(I.main(["install","--yes","--confirm","WRONG",
                                     "--game-root",str(self.root)]),2)

    def test_06_rollback_requires_exact_last_component(self):
        with self.assertRaisesRegex(I.Stop,"BGXP3_NOT_LAST_WEIDU"):
            I.installed(self.root)

if __name__=="__main__": unittest.main(verbosity=2)
