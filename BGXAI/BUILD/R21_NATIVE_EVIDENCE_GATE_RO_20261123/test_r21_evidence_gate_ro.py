"""R21 synthetic no-game tests and R20-format fail-closed regressions."""
import copy
import unittest
from BGXAI_R21_EVIDENCE_GATE_RO import evaluate, APR_KEYS, SOURCE_BLOBS


def good_report():
    return {
        "schema": "BGXAI_R19_INSTALLED_EEEX_STATIC_AUDIT_RO_V1",
        "status": "UPSTREAM_V117_LF_EQUIVALENT_STATIC_ONLY",
        "sourceTag": "v1.1.7", "sourceRepository": "Bubb13/EEex",
        "readOnly": True, "installedGameFilesInspected": True,
        "allRequiredLuaScriptsPresent": True,
        "allStaticMethodCallsitesPresent": True,
        "allInstalledFilesCanonicalLFUpstream": True,
        "apiPresentAtRuntimeVerified": False,
        "nativeAbilityPointerSafe": False, "nativeLauncherReturnSafe": False,
        "nativeResourceLifetimeVerified": False, "safeToCallGetAbility": False,
        "safeToCallGetLauncher": False, "safeToRegisterListener": False,
        "alternateSlotAPRVerified": False, "fullActiveEffectsFingerprintVerified": False,
        "weaponSwitchAuthorized": False, "dispatchAuthorized": False,
        "installAuthorized": False, "gameModified": False,
        "scripts": {
            name: {"present": True, "allCallsitesPresent": True,
                   "canonicalLFUpstreamMatch": True, "gitBlobSha1LF": sha,
                   "upstreamTagGitBlobSha1": sha}
            for name, sha in SOURCE_BLOBS.items()
        },
    }


def snapshot(slot=12, apr=2, resref="AROW01"):
    return {"actor": 123, "target": 456, "selectedSlot": slot,
            "selectedResref": resref, "selectedAprKeyRaw": apr,
            "nativeEventAuthenticated": False,
            "alternateSlotAPRVerified": False, "manualEpsQueueVerified": False}


class EvidenceGateTests(unittest.TestCase):
    def test_full_static_scan_still_hold(self):
        x = evaluate(good_report())
        self.assertEqual(x["status"], "HOLD_NATIVE_POINTER_AND_ACTION_QUEUE")
        self.assertTrue(x["sourceStaticMatched"])
        self.assertEqual(x["nextAction"], "KEEP_CURRENT_WEAPON_NO_DISPATCH")

    def test_actual_report_shape_flags_are_all_false(self):
        x = evaluate(good_report(), snapshot())
        for k in ("weaponSwitchAuthorized", "dispatchAuthorized", "installAuthorized",
                  "safeToCallGetAbility", "safeToCallGetLauncher", "safeToRegisterListener",
                  "engineSuppliedAbilityRuntimeSafe", "manualEpsQueueVerified",
                  "alternateSlotAPRVerified", "completeActiveEffectsVerified"):
            self.assertIs(x[k], False, k)
        self.assertEqual(x["ordersSent"], 0)

    def test_missing_report(self):
        self.assertFalse(evaluate(None)["sourceStaticMatched"])
    def test_empty_report(self):
        self.assertFalse(evaluate({})["sourceStaticMatched"])
    def test_wrong_schema(self):
        r=good_report();r["schema"]="OTHER"
        self.assertFalse(evaluate(r)["sourceStaticMatched"])
    def test_wrong_tag(self):
        r=good_report();r["sourceTag"]="v0"
        self.assertFalse(evaluate(r)["sourceStaticMatched"])
    def test_mismatched_status(self):
        r=good_report();r["status"]="LOCAL_VARIANT"
        self.assertFalse(evaluate(r)["sourceStaticMatched"])
    def test_missing_script(self):
        r=good_report();del r["scripts"]["resource"]
        self.assertFalse(evaluate(r)["sourceStaticMatched"])
    def test_bad_source_hash(self):
        r=good_report();r["scripts"]["resource"]["gitBlobSha1LF"]="0"*40
        self.assertFalse(evaluate(r)["sourceStaticMatched"])
    def test_callsite_missing(self):
        r=good_report();r["scripts"]["sprite"]["allCallsitesPresent"]=False
        self.assertFalse(evaluate(r)["sourceStaticMatched"])
    def test_noncanonical_source(self):
        r=good_report();r["scripts"]["action"]["canonicalLFUpstreamMatch"]=False
        self.assertFalse(evaluate(r)["sourceStaticMatched"])
    def test_allowlist_never_interprets_unverified_native_as_true(self):
        for key in ("safeToCallGetAbility", "safeToCallGetLauncher", "safeToRegisterListener",
                    "installAuthorized", "dispatchAuthorized", "weaponSwitchAuthorized",
                    "nativeResourceLifetimeVerified", "apiPresentAtRuntimeVerified"):
            r=good_report();r[key]=True
            x=evaluate(r)
            self.assertFalse(x["sourceStaticMatched"],key)
            self.assertFalse(x["dispatchAuthorized"])
    def test_missing_false_is_not_false(self):
        r=good_report();del r["safeToCallGetAbility"]
        self.assertFalse(evaluate(r)["sourceStaticMatched"])
    def test_only_current_apr_decoded(self):
        self.assertEqual(evaluate(good_report(),snapshot())["selected"]["selectedAprDecoded"], 2.0)
        self.assertEqual(evaluate(good_report(),snapshot(slot=35,apr=7,resref="SW1H04"))["selected"]["selectedAprDecoded"],1.5)
        self.assertEqual(evaluate(good_report(),snapshot(slot=38,apr=6,resref="STAF01"))["selected"]["selectedAprDecoded"],0.5)
    def test_unknown_apr_rejected(self):
        self.assertFalse(evaluate(good_report(),snapshot(apr=11))["currentSelectionScalarValid"])
    def test_boolean_apr_rejected(self):
        self.assertFalse(evaluate(good_report(),snapshot(apr=True))["currentSelectionScalarValid"])
    def test_slot_gap_rejected(self):
        self.assertFalse(evaluate(good_report(),snapshot(slot=20))["currentSelectionScalarValid"])
    def test_nonuppercase_resref_rejected(self):
        self.assertFalse(evaluate(good_report(),snapshot(resref="arow01"))["currentSelectionScalarValid"])
    def test_fake_authentication_rejected(self):
        s=snapshot();s["nativeEventAuthenticated"]=True
        self.assertFalse(evaluate(good_report(),s)["currentSelectionScalarValid"])
    def test_fake_alternate_apr_rejected(self):
        s=snapshot();s["alternateSlotAPRVerified"]=True
        self.assertFalse(evaluate(good_report(),s)["currentSelectionScalarValid"])
    def test_fake_queue_proof_rejected(self):
        s=snapshot();s["manualEpsQueueVerified"]=True
        self.assertFalse(evaluate(good_report(),s)["currentSelectionScalarValid"])
    def test_same_actor_target_rejected(self):
        s=snapshot();s["target"]=s["actor"]
        self.assertFalse(evaluate(good_report(),s)["currentSelectionScalarValid"])
    def test_fist_does_not_need_resref(self):
        s=snapshot(slot=10);del s["selectedResref"]
        self.assertEqual(evaluate(good_report(),s)["selected"]["slotClass"],"FIST")
    def test_ammo_is_not_launcher(self):
        x=evaluate(good_report(),snapshot())
        self.assertEqual(x["selected"]["slotClass"],"AMMO")
        self.assertFalse(x["launcherAmmoLinkVerified"])
    def test_invalid_report_hides_valid_candidate(self):
        r=good_report();r["scripts"]["resource"]["present"]=False
        self.assertIsNone(evaluate(r,snapshot())["selected"])
    def test_size_and_hook_provenance_do_not_authorize(self):
        x=evaluate(good_report(),snapshot())
        self.assertEqual(x["itemHeaderSizeX64Documented"] - x["itemAbilitySizeX64Documented"], 58)
        self.assertTrue(x["onHitHookCanChangeCombat"])
        self.assertFalse(x["safeToRegisterListener"])
    def test_no_mutation_of_inputs(self):
        r,s=good_report(),snapshot();r0,s0=copy.deepcopy(r),copy.deepcopy(s)
        evaluate(r,s)
        self.assertEqual(r,r0);self.assertEqual(s,s0)
    def test_apr_map_one_key_per_raw(self):
        self.assertEqual(len(APR_KEYS),11)
        self.assertEqual([APR_KEYS[i] for i in range(6)],[0.,1.,2.,3.,4.,5.])

if __name__ == '__main__':
    unittest.main()
