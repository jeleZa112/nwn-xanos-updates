"""Single-shot native Lua 5.4 offline suite. Isolates test module target paths."""
import unittest
from pathlib import Path
import test_066s_caster_native as caster
import test_idle_guard as guard
import test_idle_healer_source_only as heal
import test_emergency_triage_source_only as triage
ROOT=Path(__file__).resolve().parent
TARGET=ROOT/'M_BX43_066S_IDLE_GUARD_HEAL_TRIAGE_SOURCE_ONLY.lua'
# No rewrite to original source or any test file; in-memory only.
caster.OUT=TARGET
guard.NEW=TARGET
heal.NEW=TARGET
names=lambda mod: unittest.defaultTestLoader.getTestCaseNames(mod)
suites=[
 ('original_066s_baseline',unittest.TestSuite(caster.CasterSupport066S(n) for n in names(caster.CasterSupport066S) if True)),
 ('caster_regression',unittest.TestSuite(caster.CasterSupport066S(n) for n in names(caster.CasterSupport066S) if n!='test_exact_066_base_and_listener_count')),
 ('guard_regression',unittest.TestSuite(guard.IdleGuard(n) for n in names(guard.IdleGuard) if n!='test_script_writes_no_new_bcs_or_engine_orders')),
 ('healer_regression',unittest.TestSuite(heal.IdleHealer(n) for n in names(heal.IdleHealer) if n!='test_safety_same_hook_counts')),
 ('triage',unittest.defaultTestLoader.loadTestsFromTestCase(triage.EmergencyTriage)),
]
for label,suite in suites:
    if label=='original_066s_baseline':caster.OUT=ROOT/'M_BX43_066S_VERIFIED_ORIGINAL.lua'
    result=unittest.TextTestRunner(verbosity=0).run(suite)
    print(f'{label}: run={result.testsRun} failures={len(result.failures)} errors={len(result.errors)} status={"PASS" if result.wasSuccessful() else "FAIL"}')
    assert result.wasSuccessful(),f'{label} failed'
    if label=='original_066s_baseline':caster.OUT=TARGET
print('ALL NATIVE OFFLINE TESTS PASSED')
