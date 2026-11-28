"""R46 compiles in TEMP via R39/V3 backend, never installs BCS/game files."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('r46_existing_native',HERE/'BGXAI_R46_NATIVE_COMPILE_RO_REUSE_R39.py')
N=importlib.util.module_from_spec(sp);sp.loader.exec_module(N)

class FakeV3:
    def __init__(self): self.closed=0;self.compiled=0
    def close_game_proof(self):self.closed+=1
    def pinned_compiler(self,game):
        return game/'setup-enhanced-powergaming-scripts.exe'

class FakeBackend:
    class Hold(ValueError): pass
    TEMP_SOURCE_NAME="RANGED7.baf"
    def source_check(self,p,g):return None
    def __init__(self):
        self.resultStatus="NATIVE_WEIDU_COMPILED_TEMP_ONLY"
        self.watched=False
        self.fail=False
        self.lastSource=None
    def checked_file(self,p,required=False):return Path(p).read_bytes()
    def compile_readonly(self,game,source,compiler):
        self.lastSource=Path(source)
        if self.fail:raise ValueError("MOCK_NATIVE_FAILED")
        item=self.source_check(source,game)
        assert item["sha256"]==N.EXPECTED_BAF_SHA
        assert item["blocks"]==1 and item["actionCount"]==1
        assert self.TEMP_SOURCE_NAME=="BGXR46.baf"
        assert not self.lastSource.is_relative_to(Path(game))
        return {"status":self.resultStatus,
          "nativeSymbolsAcceptedByCompiler":self.resultStatus=="NATIVE_WEIDU_COMPILED_TEMP_ONLY",
          "watchedFilesChanged":self.watched,"temporaryOutputRemoved":True,
          "compiledSha256":"a"*64}

class NativeSourceOnly(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r46,cls.r39,cls.realV3,cls.realBackend,cls.baf=N.load_all()

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.game=Path(self.temp.name)/"game"
        self.game.mkdir()
        (self.game/"chitin.key").write_bytes(b"UNCHANGED_FIXTURE")
        self.v3=FakeV3();self.backend=FakeBackend()

    def native(self,baf=None):
        return N.native_ro(self.game,r39=self.r39,v3=self.v3,
                           backend=self.backend,baf=self.baf if baf is None else baf)

    def test_exact_preexisting_R39_V3_native_backend_integrity(self):
        self.assertEqual(N.blob(N.R39_HELPER.read_bytes()),N.EXPECTED[N.R39_HELPER.name])
        self.assertEqual(N.blob(N.V3_HELPER.read_bytes()),N.EXPECTED[N.V3_HELPER.name])
        self.assertEqual(N.blob(N.BACKEND.read_bytes()),N.EXPECTED[N.BACKEND.name])

    def test_R46_source_exact_223_bytes_known_SHA(self):
        self.assertEqual(len(self.baf),223)
        self.assertEqual(N.sha(self.baf),N.EXPECTED_BAF_SHA)

    def test_no_real_game_execution_on_module_import(self):
        self.assertFalse((self.game/"BGXR46").exists())
        self.assertEqual((self.game/"chitin.key").read_bytes(),b"UNCHANGED_FIXTURE")

    def test_mock_native_compiles_only_in_TEMP(self):
        expected=self.backend.source_check
        name=self.backend.TEMP_SOURCE_NAME
        result=self.native()
        self.assertEqual(result["status"],"R46_NATIVE_BAF_TEMP_PASS_NO_INSTALL")
        self.assertEqual(result["ordersSent"],0)
        self.assertFalse(result["gameModified"])
        self.assertFalse(result["installed"])
        self.assertEqual(self.v3.closed,1)
        self.assertEqual(self.backend.source_check.__func__,expected.__func__)
        self.assertEqual(self.backend.TEMP_SOURCE_NAME,name)
        self.assertFalse(self.backend.lastSource.exists())
        self.assertEqual((self.game/"chitin.key").read_bytes(),b"UNCHANGED_FIXTURE")

    def test_mock_native_unknown_ids_refuses_positive(self):
        self.backend.resultStatus="WEIDU_COMPILE_FAILED_OR_UNRESOLVED_IDS"
        out=self.native()
        self.assertEqual(out["status"],"HOLD_R46_NATIVE_BAF")
        self.assertTrue(out["noAutoRetry"])

    def test_mock_watched_game_file_change_refuses(self):
        self.backend.watched=True
        out=self.native()
        self.assertEqual(out["status"],"HOLD_R46_NATIVE_BAF")
        self.assertTrue(out["noAutoRetry"])

    def test_missing_game_directory_no_native(self):
        with self.assertRaisesRegex(ValueError,"HOLD_R46_GAME_ROOT_UNSAFE"):
            N.native_ro(self.game/"missing",r39=self.r39,
                        v3=self.v3,backend=self.backend,baf=self.baf)

    def test_modified_baf_refuses(self):
        with self.assertRaisesRegex(ValueError,"HOLD_R46_STAGED_BAF_SHA"):
            self.native(baf=self.baf+b"\n")

    def test_native_exception_restores_backend_guards(self):
        self.backend.fail=True
        old=self.backend.source_check
        name=self.backend.TEMP_SOURCE_NAME
        with self.assertRaisesRegex(ValueError,"MOCK_NATIVE_FAILED"):
            self.native()
        self.assertEqual(self.backend.source_check.__func__,old.__func__)
        self.assertEqual(self.backend.TEMP_SOURCE_NAME,name)

    def test_source_disallows_new_updater_and_installer(self):
        src=(HERE/"BGXAI_R46_NATIVE_COMPILE_RO_REUSE_R39.py").read_text()
        self.assertIn("TEMP",src)
        self.assertNotIn("BGXAI_UPDATE2.cmd",src)
        self.assertNotIn("XEquipItem(",src)
        self.assertNotIn("--force-install",src)
        self.assertNotIn("WeiDU.log",src) # deliberately do not touch log

if __name__=="__main__":
    unittest.main()
