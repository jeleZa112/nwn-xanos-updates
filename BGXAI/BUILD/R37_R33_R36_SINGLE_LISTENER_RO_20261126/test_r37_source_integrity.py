"""R37 source-only integrity: one installed R33 listener, no second observer."""
from pathlib import Path
import hashlib
import re
import subprocess
import unittest

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent/"R33_R31_REUSE_PROF_SNAPSHOT_RO_20261125"/"M_BGXR27_R33_SOURCE_ONLY.lua"
R36=ROOT.parent/"R36_R33_CONTEXT_INVALIDATION_RO_20261126"/"BGXAI_R36_R33_ADVICE_INVALIDATION.lua"
CAND=ROOT/"M_BGXR27_R37_SOURCE_ONLY.lua"
EXPECTED_BASE_SHA="1420ef723df1090d56f8f6590fd82e5c69107ba97a39b2ca2ba73f93e0e77069"
EXPECTED_R36_BLOB="f7d4e11a219cd254a52a0f53f18582c9415223af"

class R37(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=BASE.read_bytes()
        cls.r36=R36.read_bytes()
        cls.cand=CAND.read_bytes()
        cls.text=cls.cand.decode("utf-8")

    def test_frozen_sources(self):
        self.assertEqual(len(self.base),49438)
        self.assertEqual(hashlib.sha256(self.base).hexdigest(),EXPECTED_BASE_SHA)
        self.assertEqual(len(self.r36),8299)
        blob=subprocess.check_output(["git","hash-object",str(R36)],text=True).strip()
        self.assertEqual(blob,EXPECTED_R36_BLOB)

    def test_only_one_real_eeex_registration(self):
        self.assertEqual(self.text.count("EEex_Action_AddSpriteStartedActionListener,pilot.listener"),1)
        self.assertEqual(self.text.count("function R27.makeListener(deps)"),1)
        self.assertEqual(self.text.count("function R27.prepareConsolePilot(ports)"),1)
        self.assertEqual(self.text.count("local R27 = (function()"),1)
        self.assertEqual(self.text.count("BGXAI_R27_ObserverPilot.registered==true"),1)

    def test_embedded_r36_is_byte_exact(self):
        self.assertEqual(self.text.count(self.r36.decode("utf-8")),1)
        self.assertIn("local R36_CORE = (function()\n",self.text)
        self.assertIn("end)()\nlocal R27 = (function()",self.text)

    def test_did_not_add_second_stats_reader(self):
        base=self.base.decode("utf-8")
        self.assertEqual(self.text.count("getStats(sprite)"),base.count("getStats(sprite)"))
        self.assertEqual(self.text.count("EEex_Sprite_GetActiveStats"),
                         base.count("EEex_Sprite_GetActiveStats"))
        self.assertEqual(self.text.count("EEex_ReadLString"),
                         base.count("EEex_ReadLString"))
        self.assertEqual(self.text.count("R4_CORE.observeStableDerived"),
                         base.count("R4_CORE.observeStableDerived"))
        self.assertEqual(self.text.count("R2_CORE.observe_sprite"),
                         base.count("R2_CORE.observe_sprite"))

    def test_no_game_action_in_source(self):
        for forbidden in ("SelectWeaponAbility(","ClearActions(","Attack(",
                          "Stop(","SetGlobal(","ActionOverride(",
                          "io.open(","os.execute("):
            self.assertNotIn(forbidden,self.text)
        self.assertIn("dispatchAuthorized=false",self.text)
        self.assertIn("weaponSwitchAuthorized=false",self.text)
        self.assertIn('"actionOrigin":"UNKNOWN"',self.text)

    def test_original_r33_json_schema_unchanged(self):
        self.assertEqual(self.text.count("function R27.toConsoleJson(sample)"),1)
        self.assertEqual(self.text.count("BGXAI_R27_SINGLE_CALLBACK_SELECTED_RO_V1"),
                         self.base.decode("utf-8").count("BGXAI_R27_SINGLE_CALLBACK_SELECTED_RO_V1")+1)
        self.assertIn("R37_R33_CAPTURE_HOLD_NO_DISPATCH",self.text)
        self.assertIn("RAW_FIELDS_EQUAL_NOT_EFFECT_OR_EPS_PROOF",self.text)

    def test_r37_output_bounded_and_no_raw_actor(self):
        part=self.text.split("function R27.toR37AdviceJson(sample)",1)[1].split("end\n-- Makes a passive",1)[0]
        self.assertNotIn("sample.actor",part)
        self.assertNotIn("m_source",part)
        self.assertIn("jnum(sample.collectorOrdinal,1,64)",part)
        self.assertIn('"safeActionBoundaryVerified":false',part)

    def test_pinned_onefile_not_rewritten(self):
        root=ROOT.parents[1]
        pin=(root/"fox_new"/"BOOTSTRAP_PIN.json")
        import json
        obj=json.loads(pin.read_text("utf-8"))
        actual=(root/"BGXAI_SYNC.ps1").read_bytes()
        self.assertEqual(hashlib.sha256(actual).hexdigest(),obj["script_sha256"])
        self.assertEqual(len(actual),obj["script_size"])

if __name__=="__main__":
    unittest.main()
