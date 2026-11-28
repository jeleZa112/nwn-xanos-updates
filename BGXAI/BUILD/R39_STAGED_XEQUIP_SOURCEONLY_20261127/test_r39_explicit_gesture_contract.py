"""Exact R39/R40/EEex integration contract for source-only gesture armer.

No game IO, no native compile, no install. This is NOT a gameplay PASS.
"""
from pathlib import Path
import hashlib
import re
import shutil
import subprocess
import unittest

HERE=Path(__file__).resolve().parent
R39=HERE/'BGXAI_R39_JAGAN_STAF01_SOURCE_ONLY.baf'
ARM=HERE/'M_BGXW3_EXPLICIT_USER_ARM_SOURCE_ONLY.lua'
RESET=HERE.parent/'R40_SESSION_RESET_SOURCEONLY_20261127'/'M_BGXW3_SESSION_RESET_V1.lua'
if not RESET.is_file():
    # Local regression layout uses only a staging folder; on GitHub Actions
    # the exact R40 source must be in sibling BUILD directory.
    RESET=HERE/'M_BGXW3_SESSION_RESET_V1.lua'

class RealContract(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
    cls.baf=R39.read_text(encoding='ascii')
    cls.arm=ARM.read_text(encoding='utf-8')
    cls.reset=RESET.read_text(encoding='utf-8')

 def test_01_preserve_exact_existing_r39_baf(self):
    self.assertEqual(len(R39.read_bytes()),2303)
    self.assertEqual(hashlib.sha256(R39.read_bytes()).hexdigest(),
        '3b84d38a9df069e3dedfdaf8de6cbf6958a7252d43490fa64b829375cf7cd03d')

 def test_02_existing_baf_witness_matches_armed_value(self):
    self.assertIn('local WITNESS=2110908191',self.arm)
    self.assertIn('Global("BGXW3TAG","LOCALS",2110908191)',self.baf)

 def test_03_same_six_variables_as_r40_reset_guard(self):
    expected=['BGXW3ARM','BGXW3TAG','BGXW3TRY','BGXW3QST','BGXW3QTM','BGXW3MAX']
    keys=re.search(r"local KEYS=\{([^}]+)\}",self.arm)
    resetkeys=re.search(r"local KEYS=\{([^}]+)\}",self.reset)
    self.assertIsNotNone(keys);self.assertIsNotNone(resetkeys)
    get=lambda m:re.findall(r"['\"](BGXW3\w+)['\"]",m.group(1))
    self.assertEqual(get(keys),expected)
    self.assertEqual(get(resetkeys),expected)

 def test_04_existing_r40_arm_first_then_other_fields(self):
    self.assertIn('safeClear(ports.getLocal,ports.setLocal,sprite,KEYS[1])',self.reset)
    self.assertIn('for i=2,#KEYS do',self.reset)

 def test_05_guarded_input_only_no_autoarm(self):
    self.assertIn('INSTALL_BGXAI_R39_EXPLICIT_GESTURE_WITH_R40_LIVE_GUARD',self.arm)
    self.assertIn("if exactInstallerApproval~=APPROVAL",self.arm)
    self.assertIn("getName('F12')",self.arm)
    for key in ('Left Ctrl','Right Ctrl','Left Alt','Right Alt','Left Shift','Right Shift'):
        self.assertIn("getName('"+key+"')",self.arm)
    self.assertNotIn('M.prepareWithInstalledEEex',self.arm)
    self.assertNotIn('M.registerWithInstalledEEex',self.arm)

 def test_06_no_extra_action_listener_and_no_engine_action(self):
    self.assertNotIn('EEex_Action_AddSpriteStartedActionListener',self.arm)
    self.assertNotIn('EEex_Action_AddSpriteStartedNextActionListener',self.arm)
    self.assertNotIn('XEquipItem(',self.arm)
    for forbidden in ('ClearActions(', 'FillSlot(', 'SelectWeaponAbility(', 'Stop('):
        self.assertNotIn(forbidden,self.arm)

 def test_07_baf_uses_one_attempt_and_no_autostart(self):
    self.assertEqual(self.baf.count('XEquipItem('),1)
    self.assertNotIn('SetGlobal("BGXW3ARM","LOCALS",1)',self.baf)
    self.assertIn('ActionListEmpty()',self.baf)
    self.assertIn('CombatCounter(0)',self.baf)

 def test_08_readback_armed_last_and_abort_on_failure(self):
    i=self.arm.index('if not setAndVerify(ports,sprite,KEYS[1],1) then')
    j=self.arm.index('for _,pair in ipairs(initial) do')
    self.assertGreater(i,j)
    self.assertIn('disarm(ports,sprite)',self.arm[i:])
    self.assertIn('state.attemptedEpoch=epoch',self.arm[j:i])

 def test_09_session_guard_required(self):
    self.assertIn('local epoch=armingAllowed(ports)',self.arm)
    self.assertIn('if not epoch then return ret',self.arm)
    self.assertIn('HOLD_SESSION_RESET_ORDER_UNPROVEN',self.arm)
    self.assertIn('HOLD_ONE_ATTEMPT_PER_SESSION',self.arm)

 def test_10_exact_selection_and_item_gates(self):
    for key in ('partyPortraitSame','selectedActorSame','itemEngineUsable',
                'itemCurrentShaVerified','activeEffectsChecked','sourceUnique',
                'targetEmpty','offhandEmpty','currentActionIdle','queueEmpty'):
        self.assertIn('x.'+key,self.arm)

 def test_11_lua_mock_when_interpreter_installed(self):
    lua=shutil.which('texlua')
    if not lua:self.skipTest('texlua not installed in this runtime')
    run=subprocess.run([lua,'test_explicit_user_arm_source.lua'],cwd=HERE,
        capture_output=True,text=True,timeout=10,check=False)
    self.assertEqual(run.returncode,0,run.stdout+'\n'+run.stderr)
    self.assertIn('PASS 33/33',run.stdout)

if __name__=='__main__':unittest.main()
