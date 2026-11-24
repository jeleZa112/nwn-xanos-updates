"""V129 pinned control-flow checks. Synthetic fixture has no game executable."""
import unittest
import conditional_hit_message_v129 as m

def synthetic():
    code=bytearray(b"\x90"*(m.FUNC_END-m.FUNC_BASE))
    for rva,hex_bytes in m.SITES.values():
        data=bytes.fromhex(hex_bytes)
        code[rva-m.FUNC_BASE:rva-m.FUNC_BASE+len(data)]=data
    return bytes(code)

class ConditionalDispatch(unittest.TestCase):
    def test_pinned_machine_path_proves_addmessage_not_universal(self):
        proof=m.evaluate_function(synthetic(),require_sha=False)
        self.assertEqual(proof["status"],"PINNED_SOURCE_PROVES_CONDITIONAL_MESSAGE_DISPATCH")
        self.assertFalse(proof["message_callsite_is_universal_event_source"])
        self.assertTrue(proof["message_callsite_not_called_in_some_code_paths"])
        self.assertEqual([x["compare_constant"] for x in proof["conditional_paths"]],
                         ["0x182","0x502"])
        self.assertEqual(proof["checks_passed"],len(m.SITES)+5)
        self.assertFalse(proof["new_hook_installed"])
        self.assertEqual(proof["game_files_written"],0)
        self.assertFalse(proof["engineering_decision"]["native_install_allowed"])

    def test_real_only_requires_exact_private_function_hash(self):
        with self.assertRaisesRegex(ValueError,"PINNED_SHA"):
            m.evaluate_function(synthetic())

    def test_every_instruction_anchor_mutation_is_rejected(self):
        original=synthetic()
        for label,(rva,hexcode) in m.SITES.items():
            with self.subTest(label=label):
                bad=bytearray(original)
                bad[rva-m.FUNC_BASE]^=1
                with self.assertRaisesRegex(ValueError,"INSTRUCTION_DRIFT"):
                    m.evaluate_function(bytes(bad),require_sha=False)

    def test_explicit_branch_target_guards(self):
        orig=synthetic()
        self.assertEqual(m.branch_target(m.fragment(orig,0x39E699,6),0x39E699),0x39E7A0)
        self.assertEqual(m.branch_target(m.fragment(orig,0x39E6A4,6),0x39E6A4),0x39E7A0)
        self.assertEqual(m.branch_target(m.fragment(orig,0x39E7B3,6),0x39E7B3),m.BYPASS)
        self.assertEqual(m.branch_target(m.fragment(orig,0x39E6B2,5),0x39E6B2),0x39E7A7)
        self.assertEqual(m.branch_target(m.fragment(orig,m.CALLSITE,5),m.CALLSITE),m.CALL_TARGET)
        with self.assertRaisesRegex(ValueError,"NOT_A_PINNED"):
            m.branch_target(b"\x90\x90\x90\x90\x90",m.CALLSITE)

    def test_no_attack_outcome_is_invented_from_absent_message(self):
        report=m.evaluate_function(synthetic(),require_sha=False)
        self.assertEqual(report["attack_coverage_in_actual_game"],"NOT_MEASURED")
        self.assertEqual(report["game_meaning_of_0x182_0x502"],"UNKNOWN")
        self.assertEqual(report["engineering_decision"]["on_missing_message"],
                         "DO_NOT_CLASSIFY_AS_MISS_OR_ASSIGN_WEAPON")
        self.assertEqual(report["engineering_decision"]["ui_join"],
                         "REQUIRE_INDEPENDENT_EVENT_TO_DISPLAY_ROW_PROOF")

if __name__=="__main__":
    unittest.main()
