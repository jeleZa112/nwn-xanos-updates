import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('bridge',ROOT/'BGXAI_WEAPON_R3_STATIC_BRIDGE_RO.py')
bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
FIXTURE_R3=Path('/mnt/data/BGXAI_WEAPON_NATIVE_ITM_R3.json')
FIXTURE_PAIR=Path('/mnt/data/bgxai_live_pair/BGXAI_WEAPON_R1_R2_LIVE_PAIRED_20261121.json')

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r3=json.loads(FIXTURE_R3.read_text())
        cls.paired=json.loads(FIXTURE_PAIR.read_text())
    def setUp(self):
        self.r=copy.deepcopy(self.r3);self.p=copy.deepcopy(self.paired)
    def runaudit(self):return bridge.analyze(self.r,self.p)
    def bad(self):
        with self.assertRaises(bridge.EvidenceHold):self.runaudit()
    def test_native_r3_and_r1r2_live_pair_valid(self):
        a=self.runaudit()
        self.assertEqual(a['pairedActions'],10)
        self.assertEqual(a['actorId'],139135050)
        self.assertEqual(len(a['candidates']),4)
        self.assertFalse(a['dispatchAuthorized'])
        self.assertFalse(a['weaponSwitchAuthorized'])
        self.assertEqual(a['ordersSent'],0)
    def test_staff_base_and_live_apr(self):
        c=self.runaudit()['candidates'][3]
        self.assertEqual((c['item'],c['staticBaseDamageMeanWithoutStatsOrEffects'],c['sampledAPRAfterSelection']['decodedIfStandard']),('STAF01',3.5,1.0))
    def test_bow_ammo_baseline_and_apr(self):
        c=self.runaudit()['candidates'][1]
        self.assertEqual((c['item'],c['staticBaseDamageMeanWithoutStatsOrEffects'],c['sampledAPRAfterSelection']['decodedIfStandard']),('BOW05',3.5,2.0))
        self.assertEqual(c['conditionalAmmoCandidates'][0]['ammo'],'AROW01')
        self.assertEqual(c['conditionalAmmoCandidates'][0]['pairProof'],'TYPE_MATCH_ONLY_NOT_ENGINE_VERIFIED')
    def test_bow_equipped_effect_is_flat_apr_not_additive(self):
        self.assertEqual(self.runaudit()['candidates'][1]['fixedAPRByEquippedEffectRaw'],
                         [{'keyModifierRaw':2,'typeRaw':1,'timingRaw':2}])
    def test_sword_on_hit_spell_is_not_valued(self):
        a=self.runaudit()
        self.assertEqual(a['candidates'][0]['staticBaseDamageMeanWithoutStatsOrEffects'],4.5)
        self.assertEqual(a['candidates'][0]['sampledAPRAfterSelection']['decodedIfStandard'],1.5)
        self.assertEqual(a['candidates'][0]['specialHitEffectsUnvalued'][0]['resourceRaw'],'SW1H04')
        self.assertEqual(len(a['linkedSpellEffectsRaw']['SW1H04']),4)
    def test_empty_quickslot_not_rated(self):
        self.assertEqual(self.runaudit()['candidates'][2]['status'],'EMPTY')
    def test_offhand_shield_suppressed_with_twohanded(self):
        a=self.runaudit()
        self.assertEqual(a['offhandRaw']['resrefRaw'],'SHLD03A')
        self.assertTrue(a['candidates'][1]['offhandShieldMayBeSuppressed'])
        self.assertTrue(a['candidates'][3]['offhandShieldMayBeSuppressed'])
        self.assertFalse(a['candidates'][0]['offhandShieldMayBeSuppressed'])
    def test_every_score_reference_is_not_ranking(self):
        a=self.runaudit()
        self.assertFalse(a['priorityAvailable'])
        self.assertTrue(all(c['executable'] is False for c in a['candidates']))
        self.assertTrue(a['unverified'])
        self.assertEqual((a['candidates'][0]['staticBaseDamageTimesSampledAPR_NotDPS'],
                          a['candidates'][1]['staticBaseDamageTimesSampledAPR_NotDPS'],
                          a['candidates'][3]['staticBaseDamageTimesSampledAPR_NotDPS']), (6.75,7.0,3.5))
    def test_bad_status_blocks(self):
        self.r['status']='ITM_NATIVE_PARTIAL';self.bad()
    def test_not_current_build_blocks(self):
        self.r['sourceKind']='ARCHIVE_ONLY';self.bad()
    def test_report_claims_dispatch_blocks(self):
        self.r['dispatchAuthorized']=True;self.bad()
    def test_capability_flag_claim_blocks(self):
        self.r['aprPerSlotVerified']=True;self.bad()
    def test_missing_resource_blocks(self):
        self.r['missingItemsOrLinkedSpells']=['AROW01'];self.bad()
    def test_actor_mismatch_blocks(self):
        self.r['r2SnapshotSummary']['lastActor']=1;self.bad()
    def test_incomplete_pairs_blocks(self):
        self.p['pairedActions']=9;self.bad()
    def test_current_game_provenance_required(self):
        self.r['items']['BOW05']['provenance']['origin']='ARCHIVE';self.bad()
    def test_item_sha_validation(self):
        self.r['items']['BOW05']['provenance']['sha256']='unknown';self.bad()
    def test_apr_samples_different_codes_stop(self):
        self.p['selectedSnapshotsBySlotRaw']['12'][1]['aprRaw']=7;self.bad()
    def test_apr_samples_wrong_item_stop(self):
        self.p['selectedSnapshotsBySlotRaw']['12'][0]['resrefRaw']='BADITEM';self.bad()
    def test_2da_from_current_game_required(self):
        self.r['aprtables']['WSPATCK']['provenance']['origin']='ARCHIVE';self.bad()
    def test_weapons_mismatched_index_stop(self):
        self.p['gearSnapshotRaw']['quickWeapons'][1]['index']=37;self.bad()
    def test_malformed_ability_stops(self):
        self.r['items']['STAF01']['item']['abilities'][0]['diceSidesRaw']=90000;self.bad()
    def test_empty_ammo_does_not_fabricate_compatibility(self):
        self.p['gearSnapshotRaw']['quivers'][1]['resrefRaw']=None
        self.p['selectedSnapshotsBySlotRaw'].pop('12')
        self.assertEqual(self.runaudit()['candidates'][1]['conditionalAmmoCandidates'],[])
    def test_no_engine_action_functions_are_defined(self):
        for k in ('install','switch','select_weapon','execute','dispatch'):
            self.assertFalse(hasattr(bridge,k))

    def test_iron_crisis_breakage_chain_detected_as_risk_not_damage(self):
        c=self.runaudit()['candidates'][0]
        risk=c['potentialItemLossRisks'][0]
        self.assertEqual((risk['removeItemRaw'],risk['createItemRaw']),('SW1H04','MISC56_'))
        self.assertEqual(risk['triggerProbability1Raw'],1)
        self.assertFalse(risk['activationAndTargetConditionsVerified'])
        self.assertEqual(risk['numericalDamageContributionCounted'],0)
    def test_other_weapons_have_no_weapon_loss_chain(self):
        a=self.runaudit()['candidates']
        self.assertEqual(a[1]['potentialItemLossRisks'],[])
        self.assertEqual(a[3]['potentialItemLossRisks'],[])
    def test_linked_spell_missing_causes_hold(self):
        self.r['linkedSpells'].pop('SW1H04')
        self.bad()
    def test_breakage_not_assumed_when_resource_does_not_replace(self):
        e=self.r['linkedSpells']['SW1H04']['spell']['abilities'][0]['effects'][2]
        e['resourceRaw']='OTHER'
        self.assertEqual(self.runaudit()['candidates'][0]['potentialItemLossRisks'],[])

if __name__=='__main__':unittest.main(verbosity=2)
