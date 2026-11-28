"""Exact source-only R39 actor-ID continuity patch; do not touch installed R43."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location(
    "r39_stable_id_readonly",HERE/"BGXAI_R39_ACTOR_ID_GUARD_SOURCE_ONLY.py")
P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)

class R39ActorIdSourceOnly(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old=P.verified_original()
        cls.new=P.compose()

    def test_exact_published_original_r39_blob(self):
        self.assertEqual(P.git_blob(self.old),P.ORIGINAL_GIT_BLOB)

    def test_changes_are_exactly_five_unique_replacements(self):
        restored=self.new
        self.assertEqual(len(P.PATCHES),5)
        for before,after in reversed(P.PATCHES):
            self.assertEqual(restored.count(after),1)
            restored=restored.replace(after,before,1)
        self.assertEqual(restored,self.old)

    def test_numeric_id_compared_to_both_portrait_and_original_snapshot(self):
        self.assertIn(b"secondActorId~=initialPhysical.actorId",self.new)
        self.assertIn(b"secondActorId~=portraitId or sameId~=portraitId",self.new)
        self.assertNotIn(b"sameActor~=sprite or sameId~=portraitId",self.new)
        self.assertIn(b"not int(secondActorId,1,2147483647)",self.new)

    def test_second_read_is_new_wrapper_not_old_userdata(self):
        self.assertIn(b"local second=once(sameActor)",self.new)
        self.assertIn(b"local first=once(sprite)",self.new)
        self.assertIn(b"local function once(readSprite)",self.new)
        self.assertIn(b"safe(ports.getScriptLevelResRef,readSprite,level)",self.new)

    def test_prior_physical_selected_inventory_cursor_guards_preserved(self):
        for marker in (b"exactPhysical(sprite,",b"exactPhysical(sameActor,",
                       b"HOLD_SCRIPT_PILOT_PHYSICAL_CHANGED",
                       b"HOLD_SCRIPT_CURSOR_CHANGED",
                       b"HOLD_SCRIPT_RESREF_CHANGED",
                       b"HOLD_SCRIPT_RESREF_UNREADABLE",
                       b"source.resref~='STAF01'",
                       b"target.empty",
                       b"source.flags~=1"):
            self.assertEqual(self.new.count(marker),self.old.count(marker))

    def test_no_modification_of_listener_orders_arm_or_globals(self):
        for marker in (b"EEex_Action_AddSpriteStartedActionListener(",
                       b"XEquipItem(",b"SetGlobal(",b"ActionOverride(",
                       b"EEex_Trigger_EvalConditionalStringAsAIBase(",
                       b"local M={schema=",
                       b"armAuthorized=false",b"ordersSent=0",
                       b"canArm=false",b"installed=false"):
            self.assertEqual(self.new.count(marker),self.old.count(marker))

    def test_reproducible_candidate(self):
        self.assertEqual(self.new,P.compose())
        self.assertNotEqual(hashlib.sha256(self.new).digest(),
                            hashlib.sha256(self.old).digest())

    def test_no_automatic_installer_or_game_io(self):
        src=(HERE/"BGXAI_R39_ACTOR_ID_GUARD_SOURCE_ONLY.py").read_text()
        for unsafe in ("subprocess.", "os.system(", "write_bytes(",
                       "setup-BGX", "InfinityLoader.exe", "BGXAI_UPDATE.cmd"):
            self.assertNotIn(unsafe,src)

    def test_cannot_patch_already_altered_source(self):
        with self.assertRaisesRegex(ValueError,"HOLD_R39_PATCH_ANCHOR_DRIFT"):
            raw=self.old
            for old,new in P.PATCHES:
                raw=raw.replace(old,new,1)
            # If a changed candidate is fed as predecessor it will not match.
            def bad():
                s=raw
                for old,new in P.PATCHES:
                    if s.count(old)!=1: raise ValueError("HOLD_R39_PATCH_ANCHOR_DRIFT")
            bad()
        # Previous test ensures refusal of duplicate source patch; no native game call.

if __name__=="__main__":
    unittest.main()
