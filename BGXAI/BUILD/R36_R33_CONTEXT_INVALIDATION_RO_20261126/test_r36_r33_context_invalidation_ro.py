#!/usr/bin/env python3
"""R36 fail-closed tests. Fixtures mirror observed R33 *shape*, not private actor IDs."""
import copy
import importlib.util
from pathlib import Path
import unittest

p=Path(__file__).resolve().parent/"BGXAI_R36_R33_CONTEXT_INVALIDATION_RO.py"
spec=importlib.util.spec_from_file_location("bgxai_r36",p)
r36=importlib.util.module_from_spec(spec);spec.loader.exec_module(r36)

def slot(slot,ref=None,amount=None):
    return {"slot":slot,"resrefRaw":ref,
            "useCount1Raw":amount if ref is not None else None,
            "useCount2Raw":1 if ref is not None else None,
            "useCount3Raw":1 if ref is not None else None}

def event(seq,arrows=20,action=23):
    return {
        "schema":r36.R33_SCHEMA,"type":"R27_SINGLE_CALLBACK",
        "status":r36.R33_EVENT_STATUS,"seq":seq,
        "actor":123456,"partyIndex":2,"actionRaw":action,
        "selectedWeaponRaw":12,"selectedAbilityRaw":0,"selectedAprKeyRaw":2,
        "quickWeaponsRaw":[slot(35,"SW1H04",0),slot(36,"BOW05",0),
                           slot(37),slot(38,"STAF01",0)],
        "quiversRaw":[slot(11),slot(12,"AROW01",arrows),slot(13),slot(14)],
        "offhandRaw":[slot(9,"SHLD03A",0)],
        "rawInventoryDoubleReadConsistent":True,
        "selectedDerivedStatsDoubleReadConsistent":True,
        "queueSnapshotStable":True,"queuedActionsRaw":0,
        "actionContextSnapshotStable":True,
        "actionSourceStable":False,"actionSourceRaw":None,
        "actionSourceReadStatus":"ACTION_SOURCE_POINTER_UNAVAILABLE",
        "actionSourceSemantics":"UNCLASSIFIED_CAI_ACTION_M_SOURCE",
        "actionOriginVerified":False,"manualEpsQueueVerified":False,
        "r4Status":r36.R4_STATUS,
        "selectedStatsRaw":{"m_nNumberOfAttacks":2,"m_nTHAC0":20,
            "m_nSTR":15,"m_nSTRExtra":0,"m_bImprovedHaste":0,
            "m_nHitBonus":0},
        "levelsAndKitRaw":{"level1":1,"level2":1,"level3":1,"kitRaw":16384},
        "proficiencyStat89to134Raw":[0,2]+[0]*44,
        "sameLuaListenerInvocation":True,"alternativeAPRVerified":False,
        "launcherAmmoPairVerified":False,"completeActiveEffectsVerified":False,
        "epsManualQueueVerified":False,"ordersSent":0,"localsWritten":0,
        "dispatchAuthorized":False,"weaponSwitchAuthorized":False,
        "readOnly":True,
    }

def eight_events():
    return [event(i,20 if i<=6 else 19,3 if i==6 else 23)
            for i in range(1,9)]

class TestR36(unittest.TestCase):
    def setUp(self):
        self.events=eight_events()
    def audit(self):
        return r36.analyze_events(self.events)
    def hold(self,reason):
        out=self.audit()
        self.assertEqual(out["status"],"R36_HOLD")
        self.assertIn(reason,out["reason"])
        self.assertEqual(out["ordersSent"],0)
        self.assertFalse(out["dispatchAuthorized"])

    def test_eight_real_shaped_events_two_genuine_changes(self):
        out=self.audit()
        self.assertEqual(out["status"],
           "R36_HISTORICAL_RAW_CONTEXT_CONSISTENCY_PASS_NO_SWITCH")
        self.assertEqual(out["recordedEvents"],8)
        self.assertEqual(out["consecutiveComparisons"],7)
        self.assertEqual(out["classifications"],{
          "RAW_CONTEXT_EQUAL_BUT_NOT_EFFECT_PROOF":5,
          "AMMO_OR_EQUIPMENT_RAW_CHANGED_INVALIDATE_ADVICE":1,
          "STATS_OR_CLASS_RAW_CHANGED_INVALIDATE_ADVICE":0,
          "NATURAL_SELECTION_CHANGED_INVALIDATE_ADVICE":0,
          "ACTION_CONTEXT_CHANGED_KEEP_ACTION":1})
        ammo=out["comparisons"][5]
        self.assertEqual((ammo["fromSequence"],ammo["toSequence"]),(6,7))
        self.assertEqual(ammo["status"],
           "AMMO_OR_EQUIPMENT_RAW_CHANGED_INVALIDATE_ADVICE")
        self.assertEqual(ammo["observedEquipmentDeltas"],
          [{"slot":12,"beforeResrefRaw":"AROW01","afterResrefRaw":"AROW01",
            "beforeUseCount1Raw":20,"afterUseCount1Raw":19}])
        self.assertEqual(ammo["selectedAprRawBefore"],2)
        self.assertEqual(ammo["selectedAprRawAfter"],2)
        self.assertEqual(ammo["selectedTHAC0RawBefore"],20)
        self.assertEqual(ammo["selectedTHAC0RawAfter"],20)

    def test_unknown_manual_eps_origin_never_promoted(self):
        out=self.audit()
        for field in ("dispatchAuthorized","weaponSwitchAuthorized",
            "alternateEffectiveAPRVerified","fullActiveEffectsVerified",
            "sameBuffContextVerified","manualEpsOriginVerified",
            "safeActionBoundaryVerified","launcherAmmoBindingVerified"):
            self.assertIs(out[field],False)
        self.assertTrue(out["zeroQueueDoesNotProveFreeAction"])

    def test_action_change_does_not_emit_a_new_attack(self):
        out=self.audit()
        x=out["comparisons"][4]
        self.assertEqual(x["status"],"ACTION_CONTEXT_CHANGED_KEEP_ACTION")
        self.assertTrue(x["neverInterruptCurrentAction"])
        self.assertTrue(x["invalidateCachedRankingOnly"])
        self.assertFalse(out["actionQueueCleared"])

    def test_shield_change_invalidates_advice_without_dispatch(self):
        self.events[1]["offhandRaw"][0]["resrefRaw"]="SHLD04"
        out=self.audit()
        self.assertEqual(out["comparisons"][0]["status"],
                         "AMMO_OR_EQUIPMENT_RAW_CHANGED_INVALIDATE_ADVICE")

    def test_unused_bow_change_invalidates_advice(self):
        self.events[1]["quickWeaponsRaw"][1]["resrefRaw"]="BOW06"
        out=self.audit()
        self.assertEqual(out["comparisons"][0]["status"],
                         "AMMO_OR_EQUIPMENT_RAW_CHANGED_INVALIDATE_ADVICE")

    def test_strength_buff_shift_invalidates_advice(self):
        self.events[1]["selectedStatsRaw"]["m_nSTR"]=18
        out=self.audit()
        self.assertEqual(out["comparisons"][0]["status"],
                         "STATS_OR_CLASS_RAW_CHANGED_INVALIDATE_ADVICE")

    def test_haste_shift_invalidates_advice(self):
        self.events[1]["selectedStatsRaw"]["m_bImprovedHaste"]=1
        out=self.audit()
        self.assertEqual(out["comparisons"][0]["status"],
                         "STATS_OR_CLASS_RAW_CHANGED_INVALIDATE_ADVICE")

    def test_proficiency_shift_invalidates_advice(self):
        self.events[1]["proficiencyStat89to134Raw"][1]=3
        out=self.audit()
        self.assertEqual(out["comparisons"][0]["status"],
                         "STATS_OR_CLASS_RAW_CHANGED_INVALIDATE_ADVICE")

    def test_natural_slot_change_is_not_alternative_apr_proof(self):
        self.events[1]["selectedWeaponRaw"]=35
        out=self.audit()
        self.assertEqual(out["comparisons"][0]["status"],
                         "NATURAL_SELECTION_CHANGED_INVALIDATE_ADVICE")
        self.assertFalse(out["alternateEffectiveAPRVerified"])

    def test_same_raw_selected_stats_never_proves_full_effects(self):
        out=self.audit()
        self.assertEqual(out["comparisons"][0]["status"],
                         "RAW_CONTEXT_EQUAL_BUT_NOT_EFFECT_PROOF")
        self.assertFalse(out["sameBuffContextVerified"])
        self.assertFalse(out["fullActiveEffectsVerified"])

    def test_zero_queue_must_not_grant_dispatch(self):
        self.assertTrue(all(x["queuedActionsRaw"]==0 for x in self.events))
        out=self.audit()
        self.assertFalse(out["safeActionBoundaryVerified"])
        self.assertFalse(out["manualEpsOriginVerified"])

    def test_corrupt_sequence_rejected(self):
        self.events[2]["seq"]=12
        self.hold("R33_SEQUENCE_OR_SCALARS")

    def test_another_actor_rejected(self):
        self.events[-1]["actor"]=654321
        self.hold("ACTOR_CHANGED")

    def test_nonzero_orders_rejected(self):
        self.events[1]["ordersSent"]=1
        self.hold("R33_R4_OR_MUTATION_MISMATCH")

    def test_fake_switch_authorization_rejected(self):
        self.events[0]["weaponSwitchAuthorized"]=True
        self.hold("R33_UNSAFE_PROMOTION_weaponSwitchAuthorized")

    def test_missing_weapon_pips_rejected(self):
        self.events[1]["proficiencyStat89to134Raw"].pop()
        self.hold("R33_WPROF_INCOMPLETE")

    def test_mismatched_apr_and_selected_stats_rejected(self):
        self.events[1]["selectedStatsRaw"]["m_nNumberOfAttacks"]=7
        self.hold("R33_APR_SOURCE_DISAGREES")

    def test_malformed_empty_slot_rejected(self):
        self.events[0]["quickWeaponsRaw"][2]["useCount1Raw"]=0
        self.hold("EMPTY_SLOT_WITH_COUNTS")

    def test_missing_raw_ammo_count_rejected(self):
        self.events[0]["quiversRaw"][1]["useCount1Raw"]=None
        self.hold("OCCUPIED_SLOT_WITHOUT_RAW_COUNTS")

    def test_unknown_action_source_semantics_rejected(self):
        self.events[0]["actionSourceSemantics"]="VERIFIED_AUTOMATION"
        self.hold("R33_ACTION_SOURCE_SEMANTICS_CHANGED")

    def test_queue_unstable_rejected(self):
        self.events[1]["queueSnapshotStable"]=False
        self.hold("R33_QUEUE_RAW_UNSTABLE")

    def test_incomplete_inventory_hold(self):
        self.events[0]["quiversRaw"].pop()
        self.hold("INCOMPLETE_QUIVERSRAW")

    def test_wrong_kit_or_level_type_rejected(self):
        self.events[0]["levelsAndKitRaw"]["kitRaw"]=True
        self.hold("R33_LEVELS_KIT_UNREADABLE")

    def test_wrong_r4_contract_hold(self):
        self.events[0]["r4Status"]="RAW_TEMP_STATS"
        self.hold("R33_R4_OR_MUTATION_MISMATCH")

    def test_mismatched_sha_refuses_unknown_log(self):
        with self.assertRaisesRegex(r36.Hold,"R33_HISTORICAL_LOG_SHA_MISMATCH"):
            r36.parse_real_r33_log(b'not the authentic user console')
    def test_no_private_actor_id_in_summary(self):
        out=self.audit()
        self.assertNotIn("123456",str(out))
        self.assertNotIn("actorRaw",str(out))
    def test_no_file_or_game_writes_source(self):
        src=p.read_text(encoding="utf-8")
        for code in ("SelectWeaponAbility(", "ClearActions(", "Attack(",
                     "os.system(", "subprocess.", ".write_bytes(",
                     ".write_text(", "EEex_Action_AddSpriteStartedActionListener"):
            self.assertNotIn(code,src)

if __name__=="__main__":
    unittest.main(verbosity=2)
