"""Static source-only R18 release tests; no game filesystem access."""
from pathlib import Path
import json
import re
import unittest

HERE=Path(__file__).resolve().parent
OBS=HERE/'BGXAI_R18_NATIVE_LINK_PROBE_RO.lua'
ADAPTER=HERE/'BGXAI_R18_EEEX_ADAPTER_CANDIDATE.lua'
API=HERE/'R18_UPSTREAM_API_CONTRACT_V1.json'

class ReadOnlySourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.obs=OBS.read_text(encoding='utf-8')
        cls.adapter=ADAPTER.read_text(encoding='utf-8')
        cls.api=json.loads(API.read_text(encoding='utf-8'))
    def test_tag_pinned(self):
        self.assertEqual(self.api['eeexSourceTag'],'v1.1.7')
    def test_api_blob_ids(self):
        ids={x['gitBlobSha'] for x in self.api['upstreamDefinitions']}
        self.assertEqual(len(ids),3)
        self.assertTrue(all(re.fullmatch(r'[0-9a-f]{40}',s) for s in ids))
    def test_explicit_source_only_status(self):
        self.assertIn('installed = false',self.obs)
        self.assertIn('installed=false',self.adapter)
        self.assertIn('SOURCE ONLY',self.obs)
    def test_no_hook_registration(self):
        self.assertNotIn('EEex_Action_AddSpriteStartedActionListener(',self.obs)
        self.assertNotIn('EEex_Action_AddSpriteStartedActionListener(',self.adapter)
    def test_no_game_writes_or_dispatch(self):
        for source in (self.obs,self.adapter):
            for keyword in ('ClearActions(', 'SelectWeaponAbility(', 'ActionOverride(', 'XEquipItem(',
                            'SetGlobal(', 'SetGlobalTimer(', 'Attack(', 'Stop(', 'subprocess.',
                            'os.execute(', 'io.open(', 'io.write(', 'WriteFile('):
                self.assertNotIn(keyword,source,keyword)
    def test_observer_requires_injected_api(self):
        self.assertIn('function M.observe(sprite,action,api)',self.obs)
        self.assertIn("call(api,'read_event'",self.obs)
        self.assertIn("call(api,'read_launcher'",self.obs)
    def test_no_uncertified_effect_fingerprint(self):
        self.assertIn('derivedStatsFingerprintIsCompleteEffectState=false',self.obs)
        self.assertIn('fullActiveEffectsFingerprintVerified=false',self.obs)
        self.assertIn('activeBuffsComplete=false',self.obs)
    def test_no_bogus_new_event_identity(self):
        self.assertIn('nativeActionEventIdVerified=false',self.obs)
        self.assertIn('nativeLauncherAmmoPairVerified=false',self.obs)
    def test_no_false_rankability(self):
        self.assertIn('combatPriorityAuthorized=false',self.obs)
        self.assertIn('alternateSlotAPRVerified=false',self.obs)
    def test_only_trusted_source_fields(self):
        for key in ('m_nNumberOfAttacks','m_nTHAC0','m_nSTR','m_nDEX',
                    'm_nMeleeTHAC0Bonus','m_nMissileTHAC0Bonus','m_bImprovedHaste','m_nLuck'):
            self.assertIn(key,self.obs)
            self.assertIn(key,self.adapter)
    def test_launcher_method_provenance(self):
        names={x['method'] for x in self.api['upstreamDefinitions']}
        self.assertIn('CGameSprite.getLauncher',names)
        self.assertIn('CItem.getAbility',names)
        self.assertIn('CGameSprite.getActiveStats',names)
    def test_method_access_guarded(self):
        self.assertIn('pcall',self.adapter)
        self.assertIn('sprite:getLauncher(ability.handle)',self.adapter)
        self.assertIn('item:getAbility(selection.abilityIndex)',self.adapter)
    def test_no_raw_native_pointer_serialization(self):
        self.assertNotIn('EEex_UDToPtr',self.adapter)
        self.assertNotIn('EEex_PtrToUD',self.adapter)
        self.assertNotIn('GetAtOffset',self.adapter)
    def test_contract_all_gates_off(self):
        for key in ('exactInstalledEeexBytesMatched',
                    'nativeItemAbilityHandleVerifiedInUserRuntime',
                    'nativeLauncherAmmoBindingVerifiedInUserRuntime',
                    'activeEffectsEnumerated', 'completeEffectFingerprintVerified',
                    'nativeActionEventIdVerified', 'automaticRegistrationPresent',
                    'gameFileChangeAuthorized','weaponSwitchAuthorized','dispatchAuthorized'):
            self.assertIs(self.api[key],False,key)
    def test_event_revalidation(self):
        self.assertIn('ACTION_OR_TARGET_CHANGED_DURING_READ',self.obs)
        self.assertIn('SELECTED_ITEM_OR_ABILITY_CHANGED_DURING_READ',self.obs)
        self.assertIn('LAUNCHER_CHANGED_DURING_READ',self.obs)
        self.assertIn('ACTIVE_DERIVED_STATS_CHANGED_DURING_READ',self.obs)
    def test_no_other_slots_apr_projection(self):
        self.assertNotIn('getAlternateSlotAPR(',self.obs)
        self.assertIn('NO_ALTERNATE_SLOTS_APR',self.obs)
    def test_fist_does_not_query_item(self):
        self.assertIn("if kind~='FIST' then",self.obs)
        self.assertIn("if slot==10 then return {slot=slot,abilityIndex=index,resref=nil}",self.adapter)
    def test_module_no_autorun(self):
        self.assertTrue(self.obs.rstrip().endswith('return M'))
        self.assertTrue(self.adapter.rstrip().endswith('return A'))

if __name__=='__main__': unittest.main()
