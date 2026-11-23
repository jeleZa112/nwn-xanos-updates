"""Isolated fixtures only; no game folder, Windows process or EEex runtime."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock
import BGXAI_R19_INSTALLED_EEEX_AUDIT_RO as m

CODE = {
'resource': '''function EEex_Resource_GetItemAbility(itemHeader, abilityIndex)
 if itemHeader.abilityCount <= abilityIndex then return end
end
function EEex_Resource_GetCItemAbility(item, abilityIndex)
 return item.pRes.pHeader:getAbility(abilityIndex)
end
CItem.getAbility = EEex_Resource_GetCItemAbility
''',
'sprite': '''function EEex_Sprite_GetLauncher(sprite, curAbility)
 return sprite:GetLauncher(curAbility, launcherSlot)
end
CGameSprite.getLauncher = EEex_Sprite_GetLauncher
function EEex_Sprite_GetActiveStats(sprite)
 return sprite.m_derivedStats
end
CGameSprite.getActiveStats = EEex_Sprite_GetActiveStats
''',
'action': '''function EEex_Action_AddSpriteStartedActionListener(func)
 table.insert(EEex_Action_Private_SpriteStartedActionListeners, func)
end
function EEex_Action_LuaHook_OnAfterSpriteStartedAction(sprite)
 EEex_Utility_TryIgnore(listener, sprite, action)
end
'''
}

class TestR19StaticRO(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory()
  self.addCleanup(self.temp.cleanup)
  self.root=Path(self.temp.name)
  (self.root/'chitin.key').write_bytes(b'KEY V1  ')
  bootstrap=self.root/'override'/'M___EEex.lua'
  bootstrap.parent.mkdir(parents=True,exist_ok=True)
  bootstrap.write_text('-- fixture bootstrap\n')
  for k,(rel,_) in m.UPSTREAM.items():
   p=self.root/rel;p.parent.mkdir(exist_ok=True,parents=True);p.write_text(CODE[k],encoding='utf-8',newline='\n')
 def audit(self):return m.audit(self.root,fixture=True)
 def alter(self,key,value):
  p=self.root/m.UPSTREAM[key][0];p.write_text(value,encoding='utf-8',newline='\n')
 def test_positive_fixture_callsite_only(self):
  out=self.audit()
  self.assertEqual(out['status'],'LOCAL_EEEX_VARIANT_CALLSITES_PRESENT_STATIC_ONLY')
  self.assertTrue(out['allStaticMethodCallsitesPresent'])
 def test_fixture_does_not_authenticate_installed_game(self):
  self.assertFalse(self.audit()['installedGameFilesInspected'])
 def test_fixture_does_not_authorize_gameplay(self):
  out=self.audit()
  for k in ('weaponSwitchAuthorized','dispatchAuthorized','installAuthorized','safeToCallGetAbility','safeToCallGetLauncher','safeToRegisterListener'):
   self.assertFalse(out[k],k)
 def test_fixture_not_runtime_verified(self):
  out=self.audit()
  for k in ('apiPresentAtRuntimeVerified','nativeResourceLifetimeVerified','nativeAbilityPointerSafe','nativeLauncherReturnSafe','nativeActionEventIdVerified'):
   self.assertFalse(out[k],k)
 def test_no_complete_effect_fingerprint(self):self.assertFalse(self.audit()['fullActiveEffectsFingerprintVerified'])
 def test_no_other_slot_apr(self):self.assertFalse(self.audit()['alternateSlotAPRVerified'])
 def test_no_game_write(self):self.assertEqual(self.audit()['gameModified'],False)
 def test_upstream_sources_pinned(self):
  self.assertEqual(m.UPSTREAM['resource'][1],'5ecd3c2f9e9bcc6cbd317653fc057a06d956916b')
  self.assertEqual(m.UPSTREAM['sprite'][1],'b2d8d930c47785737bd30dad08e9f35a9d859578')
 def test_source_tag(self):self.assertEqual(self.audit()['sourceTag'],'v1.1.7')
 def test_missing_bootstrap_hold(self):
  (self.root/'override'/'M___EEex.lua').unlink()
  self.assertEqual(self.audit()['status'],'HOLD_INSTALLED_EEEX_SOURCE_MISSING_OR_UNREADABLE')
 def test_missing_resource_hold(self):
  (self.root/m.UPSTREAM['resource'][0]).unlink()
  self.assertEqual(self.audit()['status'],'HOLD_INSTALLED_EEEX_SOURCE_MISSING_OR_UNREADABLE')
 def test_missing_sprite_hold(self):
  (self.root/m.UPSTREAM['sprite'][0]).unlink()
  self.assertFalse(self.audit()['allRequiredLuaScriptsPresent'])
 def test_missing_action_hold(self):
  (self.root/m.UPSTREAM['action'][0]).unlink()
  self.assertFalse(self.audit()['allStaticMethodCallsitesPresent'])
 def test_missing_game_key_hold(self):
  (self.root/'chitin.key').unlink()
  self.assertEqual(self.audit()['status'],'HOLD_GAME_KEY_MISSING')
 def test_unauthorized_root_hold(self):
  if m.os.name != 'nt':self.assertEqual(m.audit(self.root,fixture=False)['status'],'HOLD_EXACT_WINDOWS_GAME_ONLY')
 def test_upstream_raw_git_sha_alg(self):
  self.assertEqual(m._sha1_git_blob(b'hello\n'),hashlib.sha1(b'blob 6\0hello\n').hexdigest())
 def test_crlf_canonical_hash_changes(self):
  self.alter('sprite',CODE['sprite'].replace('\n','\r\n'))
  x=self.audit()['scripts']['sprite']
  self.assertNotEqual(x['gitBlobSha1Raw'],x['gitBlobSha1LF'])
  self.assertTrue(x['allCallsitesPresent'])
 def test_utf8_bom_supported_for_static_but_not_identical(self):
  p=self.root/m.UPSTREAM['action'][0];p.write_bytes(b'\xef\xbb\xbf'+CODE['action'].encode())
  x=self.audit()['scripts']['action'];self.assertTrue(x['allCallsitesPresent'])
  self.assertNotEqual(x['gitBlobSha1Raw'],x['gitBlobSha1LF'])
 def test_non_utf8_resource_hold(self):
  (self.root/m.UPSTREAM['resource'][0]).write_bytes(b'\xff\xfe')
  self.assertEqual(self.audit()['scripts']['resource']['error'],'INVALID_UTF8')
 def test_binary_nul_hold(self):
  (self.root/m.UPSTREAM['action'][0]).write_bytes(b'a\0b')
  self.assertEqual(self.audit()['scripts']['action']['error'],'BINARY_SOURCE_REJECTED')
 def test_oversize_hold(self):
  (self.root/m.UPSTREAM['resource'][0]).write_bytes(b'a'*(m.MAX_BYTES+1))
  self.assertEqual(self.audit()['scripts']['resource']['error'],'SIZE_REJECTED')
 def test_comments_not_interpreted_as_apis(self):
  self.alter('resource','-- '+CODE['resource'].replace('\n','\n-- '))
  self.assertFalse(self.audit()['scripts']['resource']['allCallsitesPresent'])
 def test_strings_not_interpreted_as_apis(self):
  self.alter('action','[[\n'+CODE['action']+']]')
  self.assertFalse(self.audit()['scripts']['action']['allCallsitesPresent'])
 def test_long_comment_not_interpreted(self):
  self.alter('sprite','--[=[\n'+CODE['sprite']+']=]')
  self.assertFalse(self.audit()['scripts']['sprite']['allCallsitesPresent'])
 def test_single_quote_fake_callsite(self):
  self.alter('action',"s='"+CODE['action'].replace("'","\\'").replace('\n','\\n')+"'")
  self.assertFalse(self.audit()['scripts']['action']['allCallsitesPresent'])
 def test_action_listener_must_be_bound(self):
  self.alter('action',CODE['action'].replace('table.insert(EEex_Action_Private_SpriteStartedActionListeners, func)','local noop=1'))
  self.assertEqual(self.audit()['status'],'HOLD_INSTALLED_EEEX_STATIC_CALLSITES_MISSING')
 def test_pointer_dereference_required_and_never_safe(self):
  self.alter('resource',CODE['resource'].replace('item.pRes.pHeader:getAbility(abilityIndex)','item:getAbility(abilityIndex)'))
  out=self.audit();self.assertFalse(out['allStaticMethodCallsitesPresent']);self.assertFalse(out['safeToCallGetAbility'])
 def test_launcher_method_requires_native_ability(self):
  self.alter('sprite',CODE['sprite'].replace('sprite:GetLauncher(curAbility, launcherSlot)','sprite:GetLauncher(nil,launcherSlot)'))
  self.assertFalse(self.audit()['scripts']['sprite']['allCallsitesPresent'])
 def test_effects_completeness_never_from_source(self):
  self.assertIn('ACTIVE_EFFECTS_AND_ACTION_QUEUE_UNVERIFIED',self.audit()['blockers'])
 def test_reparse_or_symlink_rejected(self):
  path=self.root/'EEex_scripts'/'EEex_Action.lua';path.unlink()
  try:path.symlink_to(self.root/'chitin.key')
  except (OSError,NotImplementedError):self.skipTest('symlinks unavailable')
  self.assertEqual(self.audit()['scripts']['action']['error'],'REPARSE_COMPONENT_REJECTED')
 def test_direct_invalid_relative_path_rejected(self):
  for bad in ('../foo.lua','/etc/passwd','a\\b','x/../r','',None):
   self.assertEqual(m._safe_read(self.root,bad)[0]['error'],'INVALID_RELATIVE_PATH')
 def test_output_is_json_serializable(self):json.dumps(self.audit())
 def test_missing_optional_attack_info_not_required(self):
  self.assertEqual(self.audit()['status'],'LOCAL_EEEX_VARIANT_CALLSITES_PRESENT_STATIC_ONLY')
 def test_scripts_are_not_marked_upstream_identical(self):
  out=self.audit()
  self.assertFalse(out['allInstalledFilesExactUpstream'])
  self.assertFalse(out['allInstalledFilesCanonicalLFUpstream'])
 def test_unknown_script_contract_fail_closed(self):
  self.assertFalse(m.check_contract('unknown','foo')['allCallsitesPresent'])
 def test_no_native_calls_in_source(self):
  source=Path(m.__file__).read_text()
  for forbidden in ('EEex_Action_AddSpriteStartedActionListener(', 'sprite:getLauncher(', 'item:getAbility(', 'subprocess.run(', 'os.system('):
   self.assertNotIn(forbidden,source)

if __name__=='__main__':unittest.main()
