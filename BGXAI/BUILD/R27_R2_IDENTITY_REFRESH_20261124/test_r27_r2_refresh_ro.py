"""R27 updated R2 source-only staging contract, synthetic, never installed."""
from __future__ import annotations
import hashlib
from pathlib import Path
import tempfile
import unittest
from build_r27_r2_refresh_ro import ROOT, HERE, OUT, FILES, HIST, build, sha


class RefreshContracts(unittest.TestCase):
    def test_exact_source_candidate(self):
        self.assertEqual((HERE/OUT).read_bytes(), build())

    def test_original_installed_r27_remains_historical(self):
        original=(ROOT/HIST/'M_BGXR27.lua').read_bytes()
        self.assertEqual(sha(original),
            'e5eb400c56ffb1bc23344a0cf30dcc724d8d18fc2752fabd1c2c63cdcca73735')
        self.assertNotIn(b'R2_CORE.compare,r2,r2later',original)
        self.assertNotEqual(sha(original),sha(build()))

    def test_updated_r2_source_and_original_r4_pinned(self):
        self.assertEqual(sha((ROOT/list(FILES)[0]).read_bytes()),list(FILES.values())[0])
        self.assertEqual(sha((ROOT/list(FILES)[1]).read_bytes()),list(FILES.values())[1])

    def test_new_code_verifies_same_callback_without_second_listener(self):
        code=build()
        self.assertEqual(code.count(b'R2_CORE.observe_sprite,sprite'),2)
        self.assertEqual(code.count(b'R2_CORE.compare,r2,r2later'),1)
        self.assertEqual(code.count(b'return R27\n'),1)
        self.assertNotIn(b'P.initialized=start()',code)
        self.assertNotIn(b'EEex_Action_AddSpriteStartedActionListener(',code)
        self.assertIn(b'rawInventoryDoubleReadConsistent=true',code)
        self.assertIn(b'offhandRaw=r2.offhand',code)
        self.assertIn(b'R4_CORE.observeStableDerived,sprite',code)
        self.assertIn(b'selectedDerivedStatsDoubleReadConsistent=true',code)
        self.assertIn(b'R4_DERIVED_STATS_NOT_STABLE',code)
        self.assertIn(b'\"r4Status\"',code)
        self.assertEqual(code.count(b'Q81_CORE.observe(sprite,action)'),2)
        self.assertIn(b'actionContextSnapshotStable=ctxStable',code)
        self.assertIn(b'actionSourceStable=srcStable',code)
        self.assertIn(b'UNCLASSIFIED_CAI_ACTION_M_SOURCE',code)
        self.assertIn(b'EEEX_READLSTRING_UNAVAILABLE',code)
        self.assertIn(b'actionOriginVerified=false',code)
        self.assertIn(b'manualEpsQueueVerified=false',code)

    def test_no_game_actions_or_unbounded_pointer_walk(self):
        code=build()
        for forbidden in (b'ClearActions(',b'Stop(',b'SelectWeaponAbility(',
            b'getAbility(',b'getLauncher(',b'SetGlobal(',b'os.execute(',
            b'io.open(',b'EEex_Resource_Demand('):
            self.assertNotIn(forbidden,code)
        self.assertIn(b'alternativeAPRVerified=false',code)
        self.assertIn(b'launcherAmmoPairVerified=false',code)
        self.assertIn(b'epsManualQueueVerified=false',code)
        self.assertIn(b'engineSessionVerified=false',code)
        context_path=ROOT/'BGXAI/fox_new/experimental_081_eeex_action_provenance_readonly_source_only/BGXAI081_ACTION_CONTEXT_READONLY_V3.lua'
        context=context_path.read_bytes()
        self.assertIn(b'pcall(reader,ptr,49)',context)
        self.assertIn(b'EEex_ReadLString',context)
        self.assertNotIn(b'EEex_ReadString(ptr)',context)
        self.assertIn(b'action_source_semantics',context)

    def test_tampered_inputs_all_denied(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for relative in FILES:
                dest=root/relative;dest.parent.mkdir(parents=True,exist_ok=True)
                dest.write_bytes((ROOT/relative).read_bytes())
            self.assertEqual(build(root),build())
            for relative in FILES:
                dest=root/relative
                original=dest.read_bytes()
                dest.write_bytes(original+b'\n-- malicious tamper\n')
                with self.subTest(relative=str(relative)):
                    with self.assertRaisesRegex(ValueError,'R27_PINNED_SOURCE_DRIFT'):
                        build(root)
                dest.write_bytes(original)

    def test_missing_inputs_denied(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError,'R27_SOURCE_FILE_MISSING_OR_LINK'):
                build(Path(temp))

    def test_queue_source_is_pinned_and_embedded_without_registration(self):
        names=[str(x) for x in FILES]
        queue=[n for n in names if n.endswith('BGXAI081_ACTION_PROVENANCE_QUEUE_V2.lua')]
        self.assertEqual(len(queue),1)
        source=build()
        self.assertEqual(source.count(b'Q81_CORE.observe(sprite)'),2)
        self.assertGreaterEqual(source.count(b'm_queuedActions'),1)
        self.assertIn(b'm_nCount',source)
        self.assertIn(b'queueSnapshotStable=qStable',source)
        self.assertIn(b'queuedActionsRaw=qCount',source)
        self.assertIn(b'actionOriginVerified=false',source)
        self.assertIn(b'manualEpsQueueVerified=false',source)
        self.assertNotIn(b'P.initialized=start()',source)
        self.assertNotIn(b'EEex_Action_AddSpriteStartedActionListener(',source)

    def test_result_not_equal_to_installable_lua(self):
        source=build()
        self.assertTrue(source.startswith(b'-- BGXAI R27 revised SOURCE ONLY:'))
        self.assertNotIn(b'P.registered=true',source)
        self.assertTrue(source.endswith(b'return R27\n'))
        self.assertLess(len(source),50000)


if __name__=='__main__':
    unittest.main()
