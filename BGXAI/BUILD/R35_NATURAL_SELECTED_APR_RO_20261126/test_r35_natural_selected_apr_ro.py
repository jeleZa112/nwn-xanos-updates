"""R35 no-game tests: synthetic structure with separately evidenced real facts."""
import copy
import importlib.util
import pathlib
import unittest

HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("bgxai_r35",HERE/"BGXAI_R35_NATURAL_SELECTED_APR_RO.py")
r35=importlib.util.module_from_spec(spec)
spec.loader.exec_module(r35)

SHA={"AROW01":"52209dceddf99fec75e20a694b42906fa3f9ea74c6cacad5d62d33eff22f9d91",
     "BOW05":"0bfc6680b759239052dcd1882a1d2f354e7bc840e535f0b9499a5c7a3c07d797",
     "STAF01":"c472bdf3a561144392249d45df67ae3b4e07d0faf5d30469177c318bc6857fd3",
     "SW1H04":"73e3de6a07afc42f50d63b74c3235c1f9efdd773e280c501b481e876647eda88",
     "SHLD03A":"f24085edd8bf24f79b9b09302bb719f5203d9fa175dbf352f94253ff2a48b7f1"}
PROF={"AROW01":0,"BOW05":105,"STAF01":102,"SW1H04":90,"SHLD03A":0}
ORIGIN={"AROW01":"CURRENT_GAME_BIFF","BOW05":"CURRENT_GAME_BIFF",
        "STAF01":"CURRENT_GAME_OVERRIDE","SW1H04":"CURRENT_GAME_OVERRIDE","SHLD03A":"CURRENT_GAME_BIFF"}

def fixture():
    events=[]
    for seq in range(1,25):
        slot,apr=(12,2) if seq<=22 else (35,7)
        events.append({"sequence":seq,"actorRaw":123456,"actionRaw":23,
                       "selectedSlotRaw":slot,"selectedAprKeyRaw":apr,
                       "selectedAbilityRaw":0})
    r28={"schema":r35.R28_SCHEMA,"status":"R28_NATIVE_ITEMS_RAW_READ_AWAITING_REVIEW",
         "gameModified":False,"dispatchAuthorized":False,"weaponSwitchAuthorized":False,
         "captureSha256":r35.R27_SHA,
         "liveR27Evidence":{"sourceSha256":r35.R27_SHA,"r27SessionMarkers":1,
            "r27ConfirmedCallbacks":24,"actorCount":1,"samplesSelectedOnly":events},
         "nativeAudit":{"schema":"BGXAI_WEAPON_NATIVE_ITM_R3_READONLY",
            "status":"ITM_NATIVE_ALL_ITEMS_RAW_READ","sourceKind":"CURRENT_GAME",
            "items":{ref:{"item":{"proficiencyIdRaw":PROF[ref]},
                       "provenance":{"sha256":SHA[ref],"origin":ORIGIN[ref]}}
                     for ref in ("AROW01","BOW05","STAF01","SW1H04")}}}
    r34={"schema":r35.R34_SCHEMA,
         "status":"HISTORICAL_R33_PROFILE_CURRENT_ITM_JOINED_RO_NO_SWITCH",
         "gameModified":False,"readOnly":True,"ordersSent":0,"dispatchAuthorized":False,
         "weaponSwitchAuthorized":False,"liveGamePinVerified":True,"historicalProfileOnly":True,
         "sessionTemporalAlignmentVerified":False,"sameBytesAsUserUploadedLogVerified":False,
         "nativeResourceCount":5,"r33EventCount":8,
         "historicalReferenceLogSha256":r35.R33_LOG_SHA,
         "resourceItems":[{"resref":ref,"resourceSha256":SHA[ref],
             "sourceOrigin":ORIGIN[ref],"proficiencyStatIdRaw":PROF[ref],
             "proficiencyLowThreeBitsObserved":{"BOW05":0,"STAF01":0,"SW1H04":2}.get(ref)}
             for ref in ("AROW01","BOW05","SHLD03A","STAF01","SW1H04")]}
    return r28,r34

class R35(unittest.TestCase):
    def setUp(self):
        self.a,self.b=fixture()

    def assert_hold(self,part):
        r=r35.witness(self.a,self.b)
        self.assertEqual(r["status"],"R35_HOLD")
        self.assertIn(part,r["reason"])
        self.assertFalse(r["dispatchAuthorized"])
        self.assertFalse(r["weaponSwitchAuthorized"])

    def test_real_shape_22_ammo_2_sword_passive_apr(self):
        x=r35.witness(self.a,self.b)
        self.assertEqual(x["status"],"R35_HISTORIC_TWO_NATURALLY_SELECTED_APR_WITNESSES_NO_SWITCH")
        self.assertEqual(x["actualR27SelectedEvents"],24)
        self.assertEqual(x["currentNativeITMShaMatchCount"],4)
        a,b=x["observationsBySelectedSlot"]
        self.assertEqual((a["selectedSlotRaw"],a["eventCount"]),(12,22))
        self.assertEqual((b["selectedSlotRaw"],b["eventCount"]),(35,2))
        self.assertEqual(a["observedSelectedApr"],[
            {"engineAprKeyRaw":2,"aprIfStandardDecoder":2,"observations":22}])
        self.assertEqual(b["observedSelectedApr"],[
            {"engineAprKeyRaw":7,"aprIfStandardDecoder":1.5,"observations":2}])
        for flag in ("otherSlotEffectiveAPRVerified","perSlotTHAC0Verified",
                     "sameBuffContextVerified","ammoLauncherEngineBindingVerified",
                     "manualAndEPSOriginVerified","dispatchAuthorized",
                     "weaponSwitchAuthorized","gameplayPriorityExecutable"):
            self.assertIs(x[flag],False)

    def test_r28_sha_mismatch_fails_closed(self):
        self.a["captureSha256"]="0"*64
        self.assert_hold("R27_ARCHIVED_CAPTURE_UNVERIFIED")

    def test_r34_historical_8_events_missing(self):
        self.b["r33EventCount"]=7
        self.assert_hold("R34_HISTORICAL")

    def test_r34_different_item_bytes(self):
        self.b["resourceItems"][1]["resourceSha256"]="0"*64
        self.assert_hold("R28_R34_NATIVE_ITEM_CHANGED_OR_UNVERIFIED_BOW05")

    def test_r34_changed_proficiency_group(self):
        self.b["resourceItems"][1]["proficiencyStatIdRaw"]=104
        self.assert_hold("R28_R34_NATIVE_ITEM_CHANGED_OR_UNVERIFIED_BOW05")

    def test_r27_actor_drift(self):
        self.a["liveR27Evidence"]["samplesSelectedOnly"][-1]["actorRaw"]=654321
        self.assert_hold("R27_ACTOR_CHANGED")

    def test_r27_missing_natural_melee_observation(self):
        for x in self.a["liveR27Evidence"]["samplesSelectedOnly"]:
            x["selectedSlotRaw"]=12
            x["selectedAprKeyRaw"]=2
        self.assert_hold("BOTH_NATURALLY_SELECTED_SLOTS_NOT_OBSERVED")

    def test_altered_raw_apr_not_repeated_as_current_counterfactual(self):
        self.a["liveR27Evidence"]["samplesSelectedOnly"][5]["selectedAprKeyRaw"]=6
        x=r35.witness(self.a,self.b)
        self.assertEqual(x["status"],"R35_HISTORIC_TWO_NATURALLY_SELECTED_APR_WITNESSES_NO_SWITCH")
        self.assertEqual(x["observationsBySelectedSlot"][0]["observedSelectedApr"],
          [{"engineAprKeyRaw":2,"aprIfStandardDecoder":2,"observations":21},
           {"engineAprKeyRaw":6,"aprIfStandardDecoder":0.5,"observations":1}])
        self.assertFalse(x["sameBuffContextVerified"])

    def test_no_thac0_guess_while_missing(self):
        x=r35.witness(self.a,self.b)
        self.assertNotIn("finalTHAC0",str(x))
        self.assertFalse(x["perSlotTHAC0Verified"])

    def test_malformed_event_fails_closed(self):
        self.a["liveR27Evidence"]["samplesSelectedOnly"][2]["selectedAprKeyRaw"]=16
        self.assert_hold("R27_SELECTED_EVENT_SHAPE_OR_ORDER")

    def test_do_not_accept_r34_with_game_writes(self):
        self.b["ordersSent"]=1
        self.assert_hold("ORDERS_SENT_NOT_ZERO")

    def test_misleading_current_pips_are_historical_only(self):
        x=r35.witness(self.a,self.b)
        self.assertEqual(x["historicalShortBowPips"],0)
        self.assertNotIn("liveShortBowPips",x)
        self.assertFalse(x["activeClassAndKitVerified"])

    def test_arbitrary_input_hold_not_crash(self):
        x=r35.witness({"schema":"bad"},None)
        self.assertEqual(x["status"],"R35_HOLD")
        self.assertFalse(x["gameModified"])

if __name__=="__main__":
    unittest.main()
