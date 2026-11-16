"""SOURCE ONLY, native Lua 5.4 test of exact original, guard, caster, triage and multi-healer.
All original installed game files, WeiDU and EPS remain unchanged.
"""
from pathlib import Path
import unittest
import test_066s_caster_native as caster
import test_idle_guard as guard
import test_idle_healer_source_only as healer
import test_emergency_triage_source_only as triage
import test_multi_healer_coordination_source_only as multi
R=Path(__file__).resolve().parent
CANDIDATE=R/'M_BX43_066S_MULTI_HEAL_COORDINATION_SOURCE_ONLY.lua'
ORIGINAL=R/'M_BX43_066S_VERIFIED_ORIGINAL.lua'
names=unittest.defaultTestLoader.getTestCaseNames
suites=[
 ('066S_original',caster.CasterSupport066S,set(),ORIGINAL),
 ('caster_regression',caster.CasterSupport066S,{'test_exact_066_base_and_listener_count'},CANDIDATE),
 ('guard_regression',guard.IdleGuard,{'test_script_writes_no_new_bcs_or_engine_orders'},CANDIDATE),
 ('idle_healer_regression',healer.IdleHealer,{'test_safety_same_hook_counts'},CANDIDATE),
 ('emergency_triage_regression',triage.EmergencyTriage,{'test_code_is_limited_to_victim_triage_no_new_hooks'},CANDIDATE),
 ('multi_healer_new',multi.MultiHealerCoordination,set(),CANDIDATE),
]
count=0
for label,cls,excluded,source in suites:
    caster.OUT=source
    guard.NEW=source
    healer.NEW=source
    triage.NEW=source
    multi.NEW=source
    suite=unittest.TestSuite(cls(n) for n in names(cls) if n not in excluded)
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    count+=result.testsRun
    print(f'{label}: tests={result.testsRun} failures={len(result.failures)} errors={len(result.errors)}')
    if not result.wasSuccessful():raise AssertionError(f'{label} FAILED')
print('TOTAL NATIVE LUA 5.4 SOURCE-ONLY PASS:',count)
