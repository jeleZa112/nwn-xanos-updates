"""R44 alternative single-listener diagnostic source: offline deterministic tests."""
from __future__ import annotations

import hashlib
import importlib.util
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('r44_compose_source_only',HERE/"BGXAI_R44_COMPOSE_FROM_R43_SOURCE_ONLY.py")
C=importlib.util.module_from_spec(s)
s.loader.exec_module(C)

class R44Composition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r43,cls.r39_old,cls.r39_new=C.components()
        cls.r44=C.compose()

    def test_exact_published_predecessor_bytes_and_sha(self):
        self.assertEqual(len(self.r43),95965)
        self.assertEqual(hashlib.sha256(self.r43).hexdigest(),C.R43_CANDIDATE_SHA256)

    def test_same_exact_original_r39_once(self):
        self.assertEqual(self.r43.count(self.r39_old),1)
        self.assertEqual(self.r44.count(self.r39_new),1)
        self.assertEqual(self.r44.count(self.r39_old),0)

    def test_only_one_patch_in_single_old_listener(self):
        self.assertEqual(self.r44.replace(self.r39_new,self.r39_old,1),self.r43)
        self.assertEqual(len(self.r44),C.R44_SIZE)

    def test_no_new_listener_no_arm_and_no_commands(self):
        for marker in (b"EEex_Action_AddSpriteStartedActionListener,pilot.listener",
                       b"R27.r42Once=true",b"[BGXBCS]",b"[BGXR27]",b"[BGXR37]",
                       b"[BGXINV3]",b"[BGXID]",b'"ordersSent":0',
                       b'"localsWritten":0',b'"armAuthorized":false',
                       b'"dispatchAuthorized":false'):
            self.assertEqual(self.r44.count(marker),self.r43.count(marker))
        for marker in (b"XEquipItem(",b"ActionOverride(",b"SetGlobal(",
                       b"ClearActions(",b"SelectWeaponAbility(",
                       b"EEex_Action_AddSpriteStartedActionListener("):
            self.assertEqual(self.r44.count(marker),self.r43.count(marker))

    def test_num_id_guard_and_second_7_resrefs_present(self):
        self.assertIn(b"secondActorId~=initialPhysical.actorId",self.r44)
        self.assertIn(b"local second=once(sameActor)",self.r44)
        self.assertIn(b"HOLD_SCRIPT_RESREF_CHANGED",self.r44)

    def test_reject_corrupted_base(self):
        wrong=bytearray(self.r43)
        wrong[0]^=1
        with self.assertRaisesRegex(ValueError,"HOLD_R43_CANDIDATE_NOT_PINNED"):
            C.patch(bytes(wrong),self.r39_old,self.r39_new)

    def test_reject_corrupted_new_bridge(self):
        wrong=bytearray(self.r39_new)
        wrong[0]^=1
        with self.assertRaisesRegex(ValueError,"HOLD_R39_NEW_SOURCE_NOT_PINNED"):
            C.patch(self.r43,self.r39_old,bytes(wrong))

    def test_reject_missing_embedded_predecessor(self):
        with self.assertRaisesRegex(ValueError,"HOLD_R39_EMBEDDED_SOURCE_NOT_EXACTLY_ONCE"):
            C.patch(self.r43,b"NOT_AN_EMBEDDED_R39",self.r39_new)

    def test_reproducibility(self):
        self.assertEqual(self.r44,C.compose())

    def test_reuse_not_new_updater(self):
        source=Path(C.__file__).read_text()
        self.assertNotIn("subprocess.",source)
        self.assertNotIn("write_bytes(",source)
        self.assertNotIn("WeiDU.exe",source)
        self.assertNotIn("InfinityLoader.exe",source)

if __name__=="__main__":
    unittest.main()
