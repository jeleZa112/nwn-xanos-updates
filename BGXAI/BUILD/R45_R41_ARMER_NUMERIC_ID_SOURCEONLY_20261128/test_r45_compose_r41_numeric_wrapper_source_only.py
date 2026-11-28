"""R45 exact source provenance / safety regression: NO game/WeiDU/ARM."""
from __future__ import annotations
import hashlib
import importlib.util
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('r45_numeric_id',HERE/'BGXAI_R45_COMPOSE_R41_NUMERIC_WRAPPER_SOURCE_ONLY.py')
P=importlib.util.module_from_spec(s);s.loader.exec_module(P)

class ExactSourceOnly(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.arm=P.verified(P.AR,P.AR_BLOB)
        cls.original=P.verified(P.R41,P.R41_BLOB)
        cls.newArmer=P.patch_armer(cls.arm)
        cls.new=P.compose()

    def test_existing_original_r39_r41_git_blobs_exact(self):
        self.assertEqual(P.blob(self.arm),P.AR_BLOB)
        self.assertEqual(P.blob(self.original),P.R41_BLOB)

    def test_embedded_armer_exists_exactly_once(self):
        self.assertEqual(self.original.count(self.arm),1)
        self.assertEqual(self.new.count(self.newArmer),1)
        self.assertEqual(self.new.count(self.arm),0)

    def test_numeric_id_guards_replace_old_pointer_comparisons(self):
        for old in (b'state.volatileSprite~=aiBase',b'portraitSprite~=aiBase',
                    b'postPortrait~=aiBase',b'current==verifiedLoadedSprite',
                    b'sprite==current'):
            self.assertNotIn(old,self.new)
            self.assertIn(old,self.original)
        for marker in (b"sameNumericActor(aiBase,state.volatileActorId)",
                       b"sameNumericActor(state.volatileSprite,state.volatileActorId)",
                       b"sameNumericActor(portraitSprite,state.volatileActorId)",
                       b"sameNumericActor(postPortrait,state.volatileActorId)",
                       b"sameLoadedActorId(sprite,current)",
                       b"sameLoadedActorId(current,verifiedLoadedSprite)"):
            self.assertIn(marker,self.new)

    def test_still_requires_exact_hotkey_and_installer_approval(self):
        for marker in (b'Ctrl+Alt+Shift+F12',
                       b"INSTALL_BGXAI_R39_EXPLICIT_GESTURE_WITH_R40_LIVE_GUARD",
                       b"BGXAI_R41_GUARDED_TYPED_INSTALL_APPROVED",
                       b"ACTIVATE_BGXAI_R40_SESSION_RESET_GUARD",
                       b"HOLD_RUNTIME_PROOFS_OR_PORTS_MISSING",
                       b"HOLD_SESSION_RESET_ORDER_UNPROVEN",
                       b"HOLD_STALE_ARM_FOUND_DISARMED_NO_REARM"):
            self.assertIn(marker,self.new)

    def test_no_new_commands_or_action_listener(self):
        for marker in (b"XEquipItem(",b"ActionOverride(",b"SetGlobal(",
                       b"EEex_Action_AddSpriteStartedActionListener(",
                       b"ClearActions(",b"SelectWeaponAbility("):
            self.assertEqual(self.new.count(marker),self.original.count(marker))
        self.assertEqual(self.new.count(b"return M\n"),self.original.count(b"return M\n"))
        self.assertEqual(self.new.count(b"BGXW3_EEexSessionGate"),self.original.count(b"BGXW3_EEexSessionGate"))

    def test_not_installed_or_game_writer(self):
        src=(HERE/"BGXAI_R45_COMPOSE_R41_NUMERIC_WRAPPER_SOURCE_ONLY.py").read_text()
        for unsafe in ("subprocess.", "os.system(", "write_bytes(",
                       "setup-BGX", "InfinityLoader.exe"):
            self.assertNotIn(unsafe,src)

    def test_refuses_unexpected_previous_armer(self):
        with self.assertRaisesRegex(ValueError,"HOLD_AR_SOURCE_BLOB"):
            P.patch_armer(self.arm+b"\n")

    def test_refuses_unexpected_previous_r41(self):
        with self.assertRaisesRegex(ValueError,"HOLD_R41_SOURCE_BLOB"):
            P.patch_r41(self.original+b"\n",self.arm,self.newArmer)

    def test_reproducible_exact_candidate(self):
        self.assertEqual(self.new,P.compose())
        self.assertNotEqual(hashlib.sha256(self.new).digest(),
                            hashlib.sha256(self.original).digest())

    def test_R40_unchanged_in_alternative(self):
        before=self.original.split(b"local Armer=(function()\n",1)[0]
        after=self.new.split(b"local Armer=(function()\n",1)[0]
        self.assertEqual(before,after)

if __name__=="__main__":
    unittest.main()
