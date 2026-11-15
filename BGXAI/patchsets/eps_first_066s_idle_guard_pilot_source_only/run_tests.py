import unittest
from pathlib import Path
import test_066s_caster_native as historic
import test_idle_guard as fresh
from lua65_harness import run_case
from native_066_fixture import PREAMBLE
R=Path(__file__).resolve().parent
historic.OUT=R/'M_BX43_066S_VERIFIED_ORIGINAL.lua'
old=unittest.defaultTestLoader.loadTestsFromTestCase(historic.CasterSupport066S)
r=unittest.TextTestRunner(verbosity=0).run(old)
assert r.wasSuccessful() and r.testsRun==18
historic.OUT=R/'M_BX43_066S_IDLE_GUARD_CANDIDATE.lua'
# The exact source identity test is intentionally excluded because this trial has a 2-region code change.
reg=unittest.TestSuite(historic.CasterSupport066S(n) for n in unittest.defaultTestLoader.getTestCaseNames(historic.CasterSupport066S) if n!='test_exact_066_base_and_listener_count')
r=unittest.TextTestRunner(verbosity=0).run(reg)
assert r.wasSuccessful() and r.testsRun==17
r=unittest.TextTestRunner(verbosity=0).run(unittest.defaultTestLoader.loadTestsFromTestCase(fresh.IdleGuard))
assert r.wasSuccessful() and r.testsRun==15
print('PASS ORIGINAL 18/18; MODIFIED LEGACY 17/17; NEW 15/15; MOCK LUA5.4 ONLY')
