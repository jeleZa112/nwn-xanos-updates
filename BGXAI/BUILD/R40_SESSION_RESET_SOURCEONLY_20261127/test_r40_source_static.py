#!/usr/bin/env python3
"""Static source-only guards. Dynamic Lua-mock tests run in GitHub CI."""
from pathlib import Path
import unittest

P=Path(__file__).with_name('M_BGXW3_SESSION_RESET_V1.lua')
S=P.read_text(encoding='utf-8')

class SourceGuards(unittest.TestCase):
 def test_no_action_start_listener(self):
  self.assertNotIn('EEex_Action_AddSpriteStartedActionListener',S)
 def test_no_item_transfer(self):self.assertNotIn('XEquipItem(',S)
 def test_no_auto_arming(self):
  self.assertNotIn('BGXW3ARM",0,1',S)
  self.assertNotIn("KEYS[1],1",S)
  self.assertNotIn('setLocalInt(sprite,"BGXW3ARM",1)',S)
 def test_actor_local_exact_six_names(self):
  for n in ('BGXW3ARM','BGXW3TAG','BGXW3TRY','BGXW3QST','BGXW3QTM','BGXW3MAX'):
   self.assertIn("'"+n+"'",S)
 def test_session_destroyed_hook(self):
  self.assertIn('EEex_GameState_AddDestroyedListener',S)
  self.assertIn('state.epoch=state.epoch+1',S)
 def test_sprite_loaded_hook(self):
  self.assertIn('EEex_Sprite_AddLoadedListener',S)
  self.assertIn('M.resetIfPending(sprite,ports)',S)
 def test_official_local_api(self):
  self.assertIn('EEex_Sprite_GetLocalInt',S)
  self.assertIn('EEex_Sprite_SetLocalInt',S)
 def test_arm_cleared_first(self):
  self.assertLess(S.index('safeClear(ports.getLocal,ports.setLocal,sprite,KEYS[1])'),
                  S.index('for i=2,#KEYS do'))
 def test_exact_typed_registration_gate(self):
  self.assertIn('ACTIVATE_BGXAI_R40_SESSION_RESET_GUARD',S)
  self.assertIn('HOLD_NO_EXACT_INSTALL_APPROVAL',S)
 def test_pre_game_registration_guard(self):
  self.assertIn('ports.preGameStartupVerified~=true',S)
 def test_incomplete_registration_inert(self):
  self.assertIn('local enabled=false',S)
  self.assertIn('if enabled then',S)
 def test_unverified_api_fails_closed(self):
  self.assertIn('HOLD_REQUIRED_EEEX_APIS_MISSING',S)
 def test_no_top_level_registration_call(self):
  self.assertNotIn('M.registerWithInstalledEEex(',S.split('return M')[-1])

if __name__=='__main__':unittest.main()
