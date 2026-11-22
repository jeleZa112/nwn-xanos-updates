from __future__ import annotations
import importlib.util
import tempfile
from pathlib import Path
import unittest

PATH=Path(__file__).with_name('BGXAI_EEEX_R11_STATIC_COMPAT_RO.py')
spec=importlib.util.spec_from_file_location('bgx_compat',PATH)
module=importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        (self.root/'chitin.key').write_bytes(b'KEY')
        for name,(rel,pat) in module.CHECKS.items():
            p=self.root/rel;p.parent.mkdir(parents=True,exist_ok=True)
            if name=='attack_info':
                s='EEex.GetWeaponHitChance(x)\nEEex.IsImmuneToWeapon(x)\nsourceSpriteEquipment.m_selectedWeapon\nsourceSpriteEquipment.m_selectedWeaponAbility\n'
            elif name=='action':
                s='function EEex_Action_AddSpriteStartedActionListener(func) end\nfunction EEex_Action_LuaHook_OnAfterSpriteStartedAction(sprite) end\nsprite.m_curAction\n'
            else: s='-- static fixture\n'
            p.write_text(s,encoding='utf-8')
    def tearDown(self): self.tmp.cleanup()
    def test_all_static_callsites_readonly(self):
        before={name:(self.root/rel).read_bytes() for name,(rel,_) in module.CHECKS.items()}
        r=module.scan(self.root)
        self.assertEqual(r['status'],'STATIC_CALLSITES_FOUND_RUNTIME_NOT_PROVEN')
        self.assertFalse(r['gameModified'])
        self.assertFalse(r['runtimeApiAuthenticated'])
        self.assertFalse(r['weaponSwitchAuthorized'])
        for name,(rel,_) in module.CHECKS.items():
            self.assertEqual((self.root/rel).read_bytes(),before[name])
    def test_missing_script_blocks(self):
        (self.root/'EEex_scripts/B3AttackInfo.lua').unlink()
        self.assertEqual(module.scan(self.root)['status'],'HOLD_STATIC_COMPAT_INCOMPLETE')
    def test_missing_api_callsite_blocks(self):
        (self.root/'EEex_scripts/B3AttackInfo.lua').write_text('-- no API calls',encoding='utf-8')
        self.assertEqual(module.scan(self.root)['status'],'HOLD_STATIC_COMPAT_INCOMPLETE')
    def test_missing_action_listener_blocks(self):
        (self.root/'EEex_scripts/EEex_Action.lua').write_text('-- no listener',encoding='utf-8')
        self.assertEqual(module.scan(self.root)['status'],'HOLD_STATIC_COMPAT_INCOMPLETE')
    def test_missing_r1_r2_r4_blocks(self):
        for name in ('r1','r2','r4'):
            rel=module.CHECKS[name][0]
            p=self.root/rel;old=p.read_bytes();p.unlink()
            self.assertEqual(module.scan(self.root)['status'],'HOLD_STATIC_COMPAT_INCOMPLETE')
            p.write_bytes(old)
    def test_symlink_blocks(self):
        p=self.root/'override/M_BGXWP.lua';p.unlink()
        try:p.symlink_to(self.root/'chitin.key')
        except OSError:self.skipTest('symlinks unavailable')
        a=module.scan(self.root)
        self.assertEqual(a['status'],'HOLD_STATIC_COMPAT_INCOMPLETE')
        self.assertEqual(a['scripts']['r1']['error'],'SYMLINK_PATH_STOP')
    def test_comment_only_api_callsite_does_not_pass(self):
        p=self.root/'EEex_scripts/B3AttackInfo.lua'
        p.write_text('-- EEex.GetWeaponHitChance(x)\n-- EEex.IsImmuneToWeapon(x)\n'
                     '-- sourceSpriteEquipment.m_selectedWeapon\n'
                     '-- sourceSpriteEquipment.m_selectedWeaponAbility\n',encoding='utf-8')
        self.assertEqual(module.scan(self.root)['status'],'HOLD_STATIC_COMPAT_INCOMPLETE')
    def test_block_commented_callsite_does_not_pass(self):
        p=self.root/'EEex_scripts/EEex_Action.lua'
        p.write_text('--[[function EEex_Action_AddSpriteStartedActionListener(func) end\n'
                     'function EEex_Action_LuaHook_OnAfterSpriteStartedAction(sprite) end\n'
                     'sprite.m_curAction]]\n',encoding='utf-8')
        self.assertEqual(module.scan(self.root)['status'],'HOLD_STATIC_COMPAT_INCOMPLETE')
    def test_game_root_missing(self):
        a=module.scan(self.root/'missing')
        self.assertEqual(a['status'],'HOLD_GAME_ROOT_UNAVAILABLE')
    def test_chitin_missing(self):
        (self.root/'chitin.key').unlink()
        a=module.scan(self.root)
        self.assertEqual(a['status'],'HOLD_GAME_ROOT_UNVERIFIED')
    def test_game_modified_never_true_on_hold(self):
        (self.root/'EEex_scripts/EEex_Action.lua').unlink()
        a=module.scan(self.root)
        self.assertFalse(a['gameModified'])
        self.assertFalse(a['runtimeApiAuthenticated'])
        self.assertFalse(a['installAuthorized'])
    def test_install_protection_not_derived_from_callsites(self):
        a=module.scan(self.root)
        self.assertFalse(a['liveHookSafetyProven'])
        self.assertFalse(a['manualEPSBoundaryProven'])
        self.assertFalse(a['alternateSlotEffectiveAPRVerified'])
        self.assertFalse(a['actionSourceProven'])
    def test_metadata_has_hash_and_no_absolute_paths(self):
        a=module.scan(self.root)
        x=a['scripts']['attack_info']
        self.assertEqual(len(x['sha256']),64)
        self.assertFalse(x['relative'].startswith('/'))

if __name__=='__main__':unittest.main(verbosity=2)
