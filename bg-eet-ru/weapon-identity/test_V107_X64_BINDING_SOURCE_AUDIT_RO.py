import importlib.util
import pathlib
import unittest

MODULE = pathlib.Path(__file__).with_name('V107_X64_BINDING_SOURCE_AUDIT_RO.py')
spec = importlib.util.spec_from_file_location('audit', MODULE)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

DOC = '''.. _CItem:\nCItem\n| **Offset** | **Size (Total: 168)** | **Type** | **Field** |\n| 0x24 | 4 | unsigned int | m_flags |\n1 IDENTIFIED\n'''
GOOD = '''static int tolua_get_CItem_m_flags(lua_State *L) { return 1; }\nvoid foo(lua_State* L) {\n tolua_beginmodule(L, "CItem");\n tolua_variable(L, "m_flags", tolua_get_CItem_m_flags, nullptr);\n tolua_endmodule(L);\n}\n'''

class SourceProofTests(unittest.TestCase):
    def test_upstream_pin_format(self):
        for repo, commit, path, sha, size in audit.UPSTREAM:
            self.assertEqual(len(commit), 40)
            self.assertEqual(len(sha), 40)
            self.assertGreater(size, 0)
        self.assertEqual(audit._git_blob_sha(b'hello'), 'b6fc4c620b67d95f953a5c1c1230aaab5db5a1b0')

    def test_static_binding_pass_is_not_game_pass(self):
        v = audit.analyze(GOOD, DOC)
        self.assertEqual(v['status'], 'UPSTREAM_SOURCE_PASS_USER_ABI_HOLD')
        self.assertTrue(v['sourceOnlyPass'])
        self.assertFalse(v['allowGameInstallation'])
        self.assertFalse(v['userCallbackWeaponFlagsLiveVerified'])
        self.assertEqual(v['newEngineHooks'], 0)

    def test_x86_offset_false_positive_holds(self):
        self.assertFalse(audit.analyze(GOOD, DOC.replace('0x24','0x1C'))['sourceOnlyPass'])
        self.assertFalse(audit.analyze(GOOD, DOC.replace('1 IDENTIFIED','2 IDENTIFIED'))['sourceOnlyPass'])

    def test_wrong_struct_holds(self):
        self.assertRaises(ValueError, audit.analyze, GOOD, DOC.replace('.. _CItem:', '.. _CGameSprite:'))

    def test_registered_variable_must_be_inside_citem(self):
        fake = GOOD.replace('"CItem"', '"CSpell"')
        self.assertFalse(audit.analyze(fake, DOC)['sourceOnlyPass'])
        self.assertFalse(audit.analyze(GOOD.replace('"m_flags"','"m_other"'),DOC)['sourceOnlyPass'])

    def test_getter_required(self):
        self.assertFalse(audit.analyze(GOOD.replace('tolua_get_CItem_m_flags','tolua_get_CItem_other'),DOC)['sourceOnlyPass'])

    def test_pinned_release_binary_provenance_is_not_game_pass(self):
        content = b'official-synthetic-dll'
        size, gitsha = len(content), audit._git_blob_sha(content)
        actual = __import__('hashlib').sha256(content).hexdigest()
        good = audit.compare_pinned_binary(content, size, gitsha, actual)
        self.assertTrue(good['pinnedSourceBytesVerified'])
        self.assertTrue(good['installedSha256MatchesOfficial'])
        wrong_hash = audit.compare_pinned_binary(content, size, gitsha, '0' * 64)
        self.assertFalse(wrong_hash['installedSha256MatchesOfficial'])
        wrong_source = audit.compare_pinned_binary(content + b'!', size, gitsha, actual)
        self.assertFalse(wrong_source['pinnedSourceBytesVerified'])
        self.assertFalse(wrong_source['installedSha256MatchesOfficial'])

    def test_official_release_v120_size_sha1_pins(self):
        self.assertEqual(len(audit.RELEASE_V120_COMMIT), 40)
        names = [entry[0] for entry in audit.RELEASE_V120_BINARIES]
        self.assertEqual(names, ['EEex.dll', 'LuaBindings.dll'])
        self.assertEqual([entry[2] for entry in audit.RELEASE_V120_BINARIES],
                         [1282048, 6432256])
        for name, path, size, gitsha in audit.RELEASE_V120_BINARIES:
            self.assertTrue(path.endswith('/' + name))
            self.assertEqual(len(gitsha), 40)


if __name__ == '__main__': unittest.main()