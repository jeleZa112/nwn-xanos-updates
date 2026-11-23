"""Offline source and drift regression tests; no EEex or game installation."""
import copy
import json
import unittest
from pathlib import Path
from BGXAI_R22_NATIVE_OWNER_AUDIT_RO import inspect, SCHEMA, UPSTREAM_BLOBS

HERE=Path(__file__).resolve().parent
EVIDENCE=json.loads((HERE/'R22_UPSTREAM_EXCERPTS_VERIFIED_20261123.json').read_text(encoding='utf-8'))
FRAG=EVIDENCE['fragments']
SIZES=EVIDENCE['documentedSizes']
PINS={k:v['gitBlobSha1'] for k,v in EVIDENCE['provenance'].items()}

def run(frag=None,sizes=None,pins=None):
    return inspect(FRAG if frag is None else frag,
                   SIZES if sizes is None else sizes,
                   PINS if pins is None else pins)

class OwnershipAuditTests(unittest.TestCase):
    def test_01_baseline_status(self): self.assertEqual(run()['status'],'SOURCE_CHAIN_MATCHED_LIFETIME_HOLD')
    def test_02_exact_checks(self): self.assertTrue(all(run()['sourceChecks'].values()))
    def test_03_source_only(self): self.assertTrue(run()['sourceOnly'])
    def test_04_read_only(self): self.assertTrue(run()['readOnly'])
    def test_05_zero_orders(self): self.assertEqual(run()['ordersSent'],0)
    def test_06_no_install(self): self.assertFalse(run()['installAuthorized'])
    def test_07_no_dispatch(self): self.assertFalse(run()['dispatchAuthorized'])
    def test_08_no_switch(self): self.assertFalse(run()['weaponSwitchAuthorized'])
    def test_09_no_getability(self): self.assertFalse(run()['safeToCallGetAbility'])
    def test_10_no_launcher(self): self.assertFalse(run()['safeToCallGetLauncher'])
    def test_11_no_listener(self): self.assertFalse(run()['safeToRegisterListener'])
    def test_12_no_pointer_field_read(self): self.assertFalse(run()['safeToReadNativeAbilityFields'])
    def test_13_no_runtime_abi(self): self.assertFalse(run()['nativeDllAbiRuntimeVerified'])
    def test_14_no_lifetime(self): self.assertFalse(run()['actualDemandReleaseLifetimeProven'])
    def test_15_no_alt_apr(self): self.assertFalse(run()['alternateSlotAPRVerified'])
    def test_16_no_eps_queue(self): self.assertFalse(run()['manualEpsActionQueueVerified'])
    def test_17_correct_offset(self): self.assertEqual(run()['staticAbilityStrideMismatchBytesAtIndex1'],58)
    def test_18_verified_pins(self): self.assertEqual(PINS,UPSTREAM_BLOBS)
    def test_19_wrong_header_stride_detected(self):
        f=copy.deepcopy(FRAG);f['resource']=f['resource'].replace('Item_Header_st.sizeof','Item_ability_st.sizeof')
        x=run(f);self.assertFalse(x['allSourceChecksPass']);self.assertIsNone(x['staticAbilityStrideMismatchBytesAtIndex1'])
    def test_20_missing_demand_detected(self):
        f=copy.deepcopy(FRAG);f['cpp']=f['cpp'].replace('curWeaponIn->Demand();','')
        self.assertFalse(run(f)['sourceChecks']['cppDemandsBeforeNativeGetAbility'])
    def test_21_no_cpp_callback_push_detected(self):
        f=copy.deepcopy(FRAG);f['cpp']=f['cpp'].replace('pWeaponAbility, "Item_ability_st"','nullptr, "Item_ability_st"')
        self.assertFalse(run(f)['sourceChecks']['cppPushesEngineAbilityToLuaCallback'])
    def test_22_no_context_detected(self):
        f=copy.deepcopy(FRAG);f['sprite']=f['sprite'].replace('["weaponAbility"] = weaponAbility','["weaponAbility"] = nil')
        self.assertFalse(run(f)['sourceChecks']['luaHitHookExposesAbilityWithinContext'])
    def test_23_damage_block_detected(self):
        f=copy.deepcopy(FRAG);f['sprite']=f['sprite'].replace('return true','return false')
        self.assertFalse(run(f)['sourceChecks']['luaHitHookCanCancelDamage'])
    def test_24_try_ignore_result_detected(self):
        f=copy.deepcopy(FRAG);f['utility']=f['utility'].replace('return select(2, table.unpack(result))','return false')
        self.assertFalse(run(f)['sourceChecks']['utilityReturnsSuccessfulListenerResult'])
    def test_25_patch_semantics_detected(self):
        f=copy.deepcopy(FRAG);f['sprite_patch']=f['sprite_patch'].replace('Block base weapon damage','Protect base weapon damage')
        self.assertFalse(run(f)['sourceChecks']['patchDocumentsFalseNoChangeTrueBlocks'])
    def test_26_wrong_pin_rejected(self):
        p=dict(PINS);p['cpp']='0'*40
        self.assertFalse(run(pins=p)['allSourceChecksPass'])
    def test_27_bool_size_rejected(self):
        s=dict(SIZES);s['Item_Header_st']=True
        self.assertFalse(run(sizes=s)['sourceChecks']['x64SizesHeader114Ability56'])
    def test_28_wrong_size_rejected(self):
        s=dict(SIZES);s['Item_ability_st']=57
        self.assertFalse(run(sizes=s)['allSourceChecksPass'])
    def test_29_missing_source_rejected(self):
        f=dict(FRAG);f.pop('cpp')
        self.assertFalse(run(f)['allSourceChecksPass'])
    def test_30_no_input_rejected(self):
        self.assertFalse(inspect({}, {}, {})['allSourceChecksPass'])
    def test_31_fail_closed_cannot_grant_access(self):
        for f in (None, {}, {'bad':'bad'}):
            x=run(f) if f is not None else run()
            self.assertFalse(x['weaponSwitchAuthorized'])
    def test_32_preserve_inputs(self):
        f,s,p=copy.deepcopy(FRAG),copy.deepcopy(SIZES),copy.deepcopy(PINS)
        run(f,s,p)
        self.assertEqual(f,FRAG);self.assertEqual(s,SIZES);self.assertEqual(p,PINS)
    def test_33_no_actual_engine_call(self):
        src=(HERE/'BGXAI_R22_NATIVE_OWNER_AUDIT_RO.py').read_text(encoding='utf-8')
        for symbol in ('EEex_UDToPtr(', 'CItem::Demand(', 'sprite:getLauncher(', 'item:getAbility(',
                       'EEex_Sprite_AddBlockWeaponHitListener(', 'os.system(', 'subprocess.'):
            self.assertNotIn(symbol,src)
    def test_34_no_unearned_confidence(self):
        x=run()
        self.assertFalse(x['callbackPointerLifetimeVerified'])
        self.assertTrue(x['callbackCanAlterCombat'])
        self.assertFalse(x['callbackCouldBeUsedForPreAttackRanking'])
    def test_35_provenance_urls_present(self):
        self.assertEqual(set(EVIDENCE['provenance']),set(UPSTREAM_BLOBS))
        self.assertTrue(all(x['url'].startswith('https://github.com/') for x in EVIDENCE['provenance'].values()))
    def test_36_result_schema(self): self.assertEqual(run()['schema'],SCHEMA)
    def test_37_no_error_raises_on_bad_types(self):
        for a,b,c in ((None,None,None),(42,3,9),('hello',[],0),({'cpp':3},{},{})):
            x=inspect(a,b,c);self.assertFalse(x['allSourceChecksPass']);self.assertFalse(x['weaponSwitchAuthorized'])
    def test_38_cpp_check_specific_to_cur_weapon(self):
        f=copy.deepcopy(FRAG);f['cpp']=f['cpp'].replace('curWeaponIn->Demand();','otherItem->Demand();')
        self.assertFalse(run(f)['cppDemandOrderObserved'])
    def test_39_no_effects_claim(self):self.assertFalse(run()['fullActiveEffectsVerified'])
    def test_40_next_step(self):self.assertEqual(run()['nextAction'],'KEEP_CURRENT_WEAPON_NO_DISPATCH')

if __name__=='__main__':unittest.main()
