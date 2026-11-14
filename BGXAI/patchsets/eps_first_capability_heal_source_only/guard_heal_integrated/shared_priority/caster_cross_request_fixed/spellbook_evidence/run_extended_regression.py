"""Run previous real-Lua mocks against NEW candidate and verify old candidate untouched."""
from pathlib import Path
import unittest
import test_066s_caster_native as historic
import test_guard_capability as guard
import test_spell_patch as spell
import test_pending_caster_cross_request as cross
import test_eeex117_spellbook_evidence as native
R=Path(__file__).resolve().parent
old=R/'M_BX43_066S_CAPABILITY_CANDIDATE.lua'
new=R/'M_BX43_066S_EEEX_BOOK_EVIDENCE_CANDIDATE.lua'

def group(cls,exclude=()):
    names=[x for x in unittest.defaultTestLoader.getTestCaseNames(cls) if x not in exclude]
    return unittest.TestSuite([cls(x) for x in names])

hist_orig=group(historic.CasterSupport066S)
r=unittest.TextTestRunner(verbosity=0).run(hist_orig)
assert r.wasSuccessful() and r.testsRun==18, 'ORIGINAL 066S BASELINE FAILED'

historic.OUT=new
hist_mod=group(historic.CasterSupport066S,('test_exact_066_base_and_listener_count',))
# Redirect mock script path, all but the intentional exact-previous-diff test.
guard.CANDIDATE=new
spell.PATCH=new
cross.SCRIPT=new
extra=unittest.TestSuite([
    hist_mod,
    group(guard.GuardCapability,('test_existing_heal_patch_and_guard_diff_only',)),
    group(spell.SpellCapability),
    group(cross.OutstandingCasterRequests),
    group(native.SpellbookEvidence)
])
r=unittest.TextTestRunner(verbosity=0).run(extra)
assert r.wasSuccessful(), 'NEW CANDIDATE REGRESSION'
assert r.testsRun==17+22+9+4+22, r.testsRun
print('PASS: ORIGINAL_066S=18, NEW_CANDIDATE=74 (17 historical+22 guard+9 spell+4 pending+22 native), MODEL ONLY')
