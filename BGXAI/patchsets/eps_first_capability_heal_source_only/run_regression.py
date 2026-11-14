"""Independent baseline vs candidate regression; FAIL on any unexpected native behavior."""
from pathlib import Path
import unittest, sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import test_066s_caster_native as h
import test_capability_patch as c

# First run historical full 18 against original unmodified 066S, including sha source test.
suite0=unittest.defaultTestLoader.loadTestsFromTestCase(h.CasterSupport066S)
h.OUT=HERE/'M_BX43_066S_CAPABILITY_CANDIDATE.lua'
# Since full-file patch is intentional, the historical exact-identity test is
# replaced by test_capability_patch.ExactDiff. The other 17 must be identical.
suite1=unittest.TestSuite()
for name in unittest.defaultTestLoader.getTestCaseNames(h.CasterSupport066S):
    if name != 'test_exact_066_base_and_listener_count':
        suite1.addTest(h.CasterSupport066S(name))
suite2=unittest.defaultTestLoader.loadTestsFromTestCase(c.ExactDiff)
suite3=unittest.defaultTestLoader.loadTestsFromTestCase(c.NativeCapability)
# Re-read original with historical exact test via an isolated module reload.
import importlib
h=importlib.reload(h)
h.OUT=HERE/'M_BX43_066S_CASTER_CANDIDATE.lua'
print('BASELINE 066S: 18 historical tests')
res0=unittest.TextTestRunner(verbosity=0).run(suite0)
assert res0.wasSuccessful() and res0.testsRun==18
h.OUT=HERE/'M_BX43_066S_CAPABILITY_CANDIDATE.lua'
print('CANDIDATE 066S: 17 historical gameplay regressions + 4 diff gates + 9 capability cases')
res=unittest.TextTestRunner(verbosity=0).run(unittest.TestSuite([suite1,suite2,suite3]))
assert res.wasSuccessful() and res.testsRun==30
print('RESULT: BASELINE 18/18, CANDIDATE 30/30, SOURCE ONLY, ENGINE ORDERS 0')
