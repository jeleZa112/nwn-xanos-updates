"""Full baseline + new guard/spell patch regression, with native Lua 5.4 ctypes.
Never touches game. The capability observer is synthetic and OFF by default.
"""
from pathlib import Path
import importlib
import sys,unittest
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R))
import test_066s_caster_native as h
from lua65_harness import run_case
from native_066_fixture import PREAMBLE
import test_guard_capability as g
import test_spell_patch as s
legacy=R/'M_BX43_066S_CASTER_CANDIDATE.lua'
candidate=R/'M_BX43_066S_CAPABILITY_CANDIDATE.lua'
assert h.OUT==legacy
baseline=unittest.defaultTestLoader.loadTestsFromTestCase(h.CasterSupport066S)
run=unittest.TextTestRunner(verbosity=0).run(baseline)
if not run.wasSuccessful() or run.testsRun!=18: raise SystemExit('BASELINE_TEST_FAILURE')
h.OUT=candidate
# 17 historical behavior tests; exact old-source check replaced by diff gate.
base_reg=unittest.TestSuite([h.CasterSupport066S(name) for name in unittest.defaultTestLoader.getTestCaseNames(h.CasterSupport066S)
                            if name!='test_exact_066_base_and_listener_count'])
run=unittest.TextTestRunner(verbosity=0).run(base_reg)
if not run.wasSuccessful() or run.testsRun!=17: raise SystemExit('BASELINE_REGRESSION_FAILURE')
cs=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(g.GuardCapability),
                       unittest.defaultTestLoader.loadTestsFromTestCase(s.SpellCapability)])
run2=unittest.TextTestRunner(verbosity=0).run(cs)
if not run2.wasSuccessful(): raise SystemExit('CANDIDATE_TEST_FAILURE')
print(f'PASS: original 18, candidate unchanged behaviors 17, new guard+healer tests {run2.testsRun}; SOURCE ONLY; runtime NOT verified')
