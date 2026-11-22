import importlib.util
import tempfile
from pathlib import Path
import unittest

P=Path(__file__).with_name('BGXAI_EEEX_R11_STATIC_COMPAT_RO_V3.py')
spec=importlib.util.spec_from_file_location('scan_v3',P)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class Test(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        (self.root/'chitin.key').write_bytes(b'KEY')
        for name,(rel,_) in m.CALLS.items():
            p=self.root/rel;p.parent.mkdir(parents=True,exist_ok=True)
            if name=='attack_info':src='''EEex.GetWeaponHitChance(s,t,w,0,false)\nEEex.IsImmuneToWeapon(s,t,35,w,0)\nlocal a=sourceSpriteEquipment.m_selectedWeapon\nlocal b=sourceSpriteEquipment.m_selectedWeaponAbility\n'''
            elif name=='action':src='''function EEex_Action_AddSpriteStartedActionListener(f) end\nfunction EEex_Action_LuaHook_OnAfterSpriteStartedAction(sprite)\nreturn sprite.m_curAction end\n'''
            else:src='-- source known to be installed only after native proof\n'
            p.write_text(src,encoding='utf-8')
    def tearDown(self):self.temp.cleanup()
    def change(self,name,s):
        (self.root/m.CALLS[name][0]).write_text(s,encoding='utf-8')
    def test_full_static(self):
        r=m.scan(self.root);self.assertEqual(r['status'],'STATIC_CALLSITES_FOUND_RUNTIME_NOT_PROVEN')
        self.assertTrue(r['scripts']['r4']['exists'])
        self.assertEqual(len(r['scripts']['r4']['sha256']),64)
    def test_no_mutation(self):
        before={k:(self.root/v[0]).read_bytes() for k,v in m.CALLS.items()}
        m.scan(self.root)
        self.assertEqual(before,{k:(self.root/v[0]).read_bytes() for k,v in m.CALLS.items()})
    def test_not_native(self):
        r=m.scan(self.root)
        for k in ('gameModified','runtimeApiAuthenticated','liveHookSafetyProven','nativeEvidenceAuthenticated','manualEPSBoundaryProven','alternateSlotAPRVerified','weaponSwitchAuthorized','installAuthorized'):self.assertFalse(r[k],k)
    def test_missing_one(self):
        for name in m.CALLS:
            with self.subTest(name=name):
                p=self.root/m.CALLS[name][0];buf=p.read_bytes();p.unlink()
                expected='CORE_STATIC_PRESENT_OPTIONAL_ATTACK_INFO_ABSENT_R11_UNVERIFIED' if name=='attack_info' else 'HOLD_STATIC_COMPAT_INCOMPLETE'
                self.assertEqual(m.scan(self.root)['status'],expected)
                p.write_bytes(buf)
    def test_missing_root(self):self.assertEqual(m.scan(self.root/'missing')['status'],'HOLD_ROOT_UNAVAILABLE_OR_REPARSE')
    def test_missing_chitin(self):
        (self.root/'chitin.key').unlink();self.assertEqual(m.scan(self.root)['status'],'HOLD_CHITIN_UNVERIFIED')
    def test_comment_line(self):
        self.change('attack_info','-- EEex.GetWeaponHitChance(x)\n-- EEex.IsImmuneToWeapon(x)\n')
        self.assertEqual(m.scan(self.root)['status'],'HOLD_STATIC_COMPAT_INCOMPLETE')
    def test_comment_block(self):
        self.change('action','--[==[ function EEex_Action_AddSpriteStartedActionListener() end ]==]')
        self.assertEqual(m.scan(self.root)['status'],'HOLD_STATIC_COMPAT_INCOMPLETE')
    def test_string_spoof(self):
        self.change('attack_info','local s="EEex.GetWeaponHitChance(x)"\nlocal t=\'EEex.IsImmuneToWeapon(x)\'')
        self.assertEqual(m.scan(self.root)['status'],'HOLD_STATIC_COMPAT_INCOMPLETE')
    def test_long_string_spoof(self):
        self.change('action','local s=[====[function EEex_Action_AddSpriteStartedActionListener(x)]====]')
        self.assertEqual(m.scan(self.root)['status'],'HOLD_STATIC_COMPAT_INCOMPLETE')
    def test_block_comment_after_code(self):
        self.assertIn('f()',m.code_only('f() --[=[g()]=] h()'))
        self.assertIn('h()',m.code_only('f() --[=[g()]=] h()'))
        self.assertNotIn('g()',m.code_only('f() --[=[g()]=] h()'))
    def test_dashes_inside_string(self):
        s=m.code_only('local s="a--b"\nreal()')
        self.assertIn('real()',s)
        self.assertNotIn('a--b',s)
    def test_escaped_quote(self):
        s=m.code_only('local s="\\\" EEex.GetWeaponHitChance(x)"\n')
        self.assertNotIn('EEex.GetWeaponHitChance',s)
    def test_unterminated_comment_fail_closed(self):
        self.change('action','--[[ function EEex_Action_AddSpriteStartedActionListener()')
        self.assertEqual(m.scan(self.root)['status'],'HOLD_STATIC_COMPAT_INCOMPLETE')
    def test_empty_script(self):
        self.change('attack_info','')
        self.assertEqual(m.scan(self.root)['status'],'HOLD_STATIC_COMPAT_INCOMPLETE')
    def test_binary_script(self):
        (self.root/m.CALLS['action'][0]).write_bytes(b'hello\0world')
        self.assertEqual(m.scan(self.root)['scripts']['action']['error'],'SCRIPT_BINARY_DATA_STOP')
    def test_invalid_encoding(self):
        (self.root/m.CALLS['action'][0]).write_bytes(b'\xff\xfe\xfa')
        self.assertEqual(m.scan(self.root)['scripts']['action']['error'],'SCRIPT_ENCODING_UNVERIFIED')
    def test_symlink_script(self):
        p=self.root/m.CALLS['r4'][0];p.unlink()
        try:p.symlink_to(self.root/'chitin.key')
        except OSError:self.skipTest('symlinks disabled')
        self.assertEqual(m.scan(self.root)['scripts']['r4']['error'],'REPARSE_POINT_STOP')
    def test_symlink_parent(self):
        p=self.root/'EEex_scripts';temp=self.root/'actual';p.rename(temp)
        try:p.symlink_to(temp,target_is_directory=True)
        except OSError:self.skipTest('symlinks disabled')
        self.assertEqual(m.scan(self.root)['scripts']['action']['error'],'REPARSE_POINT_STOP')
    def test_symlink_chitin(self):
        p=self.root/'chitin.key';p.unlink();ref=self.root/'other';ref.write_bytes(b'KEY')
        try:p.symlink_to(ref)
        except OSError:self.skipTest('symlinks disabled')
        self.assertEqual(m.scan(self.root)['status'],'HOLD_CHITIN_UNVERIFIED')
    def test_path_traversal(self):
        x,txt=m.read_script(self.root,'../outside.lua');self.assertEqual(x['error'],'PATH_NOT_CANONICAL')
    def test_overlong_script(self):
        (self.root/m.CALLS['action'][0]).write_bytes(b'x'*(m.LIMIT+1))
        self.assertEqual(m.scan(self.root)['scripts']['action']['error'],'SCRIPT_SIZE_INVALID')
    def test_scan_status_never_authorizes(self):
        for name in ('attack_info','action'):
            self.change(name,'-- invalid')
            r=m.scan(self.root)
            self.assertFalse(r['installAuthorized']);self.assertFalse(r['weaponSwitchAuthorized'])
    def test_unicode_valid(self):
        p=self.root/m.CALLS['r2'][0];p.write_text('-- русский комментарий',encoding='utf-8')
        self.assertTrue(m.scan(self.root)['scripts']['r2']['exists'])
    def test_api_calls_code_with_strings(self):
        p=self.root/m.CALLS['attack_info'][0]
        p.write_text(p.read_text()+'local s="--[=[EEex.GetWeaponHitChance(x)]=]"\n')
        self.assertEqual(m.scan(self.root)['status'],'STATIC_CALLSITES_FOUND_RUNTIME_NOT_PROVEN')
    def test_missing_optional_feature_not_a_core_failure(self):
        p=self.root/m.CALLS['attack_info'][0];p.unlink()
        result=m.scan(self.root)
        self.assertEqual(result['status'],'CORE_STATIC_PRESENT_OPTIONAL_ATTACK_INFO_ABSENT_R11_UNVERIFIED')
        self.assertEqual(m.exit_code(result),0)
        self.assertTrue(result['coreStaticPresent'])
        self.assertFalse(result['attackInfoOptionalPresent'])
        self.assertFalse(result['selectedHitChanceApiStaticEvidence'])
        self.assertFalse(result['r11RuntimeEligible'])
        self.assertEqual(result['missingOptionalModules'],['attack_info'])
        self.assertEqual(result['scripts']['attack_info']['error'],'FILE_MISSING')
        self.assertIn('ATTACK_INFO_CALLSITE_NOT_INSTALLED',result['r11Blockers'])
        for x in ('installAuthorized','weaponSwitchAuthorized','runtimeApiAuthenticated','gameModified'):
            self.assertFalse(result[x])
    def test_no_api_proof_even_if_optional_feature_present(self):
        r=m.scan(self.root)
        self.assertEqual(m.exit_code(r),0)
        self.assertFalse(r['r11RuntimeEligible'])
        self.assertTrue(r['selectedHitChanceApiStaticEvidence'])
        self.assertFalse(r['runtimeApiAuthenticated'])
    def test_optional_missing_with_required_missing_fails(self):
        (self.root/m.CALLS['attack_info'][0]).unlink()
        (self.root/m.CALLS['action'][0]).unlink()
        r=m.scan(self.root)
        self.assertEqual(r['status'],'HOLD_STATIC_COMPAT_INCOMPLETE')
        self.assertEqual(m.exit_code(r),3)
    def test_optional_present_but_inconsistent_fails(self):
        self.change('attack_info','-- not genuine code')
        r=m.scan(self.root)
        self.assertEqual(r['status'],'HOLD_STATIC_COMPAT_INCOMPLETE')
        self.assertEqual(m.exit_code(r),3)
    def test_optional_symlink_cannot_be_treated_as_absence(self):
        p=self.root/m.CALLS['attack_info'][0];p.unlink()
        try:p.symlink_to(self.root/'chitin.key')
        except OSError:self.skipTest('symlinks disabled')
        r=m.scan(self.root)
        self.assertEqual(r['status'],'HOLD_STATIC_COMPAT_INCOMPLETE')
        self.assertEqual(m.exit_code(r),3)
        self.assertEqual(r['scripts']['attack_info']['error'],'REPARSE_POINT_STOP')
    def test_optional_binary_not_downgraded_to_missing(self):
        (self.root/m.CALLS['attack_info'][0]).write_bytes(b'X\x00Y')
        r=m.scan(self.root)
        self.assertEqual(r['status'],'HOLD_STATIC_COMPAT_INCOMPLETE')
        self.assertEqual(r['scripts']['attack_info']['error'],'SCRIPT_BINARY_DATA_STOP')
    def test_optional_sized_zero_is_not_missing(self):
        (self.root/m.CALLS['attack_info'][0]).write_bytes(b'')
        r=m.scan(self.root)
        self.assertEqual(r['status'],'HOLD_STATIC_COMPAT_INCOMPLETE')
        self.assertEqual(r['scripts']['attack_info']['error'],'SCRIPT_SIZE_INVALID')
    def test_optional_absent_scan_does_not_write_game(self):
        (self.root/m.CALLS['attack_info'][0]).unlink()
        before={str(p.relative_to(self.root)):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        m.scan(self.root)
        after={str(p.relative_to(self.root)):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before,after)
    def test_unknown_client_not_main(self):
        self.assertFalse(m.scan(self.root)['runtimeApiAuthenticated'])

if __name__=='__main__':unittest.main(verbosity=1)
