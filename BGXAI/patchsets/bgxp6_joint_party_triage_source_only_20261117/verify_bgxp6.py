#!/usr/bin/env python3
"""BGXP6 source-only manifest gate: exact prior advisors, no install/game actions."""
import hashlib
import pathlib
import re

HERE=pathlib.Path(__file__).resolve().parent
REPO=HERE.parents[2]
SOURCES=(
    ("BGXAI080_EPS_FIRST_COORDINATOR_MULTI_THREAT_SOURCE_ONLY.lua",
     "BGXAI/patchsets/eps_first_multi_threat_guard_source_only/BGXAI080_EPS_FIRST_COORDINATOR_MULTI_THREAT_SOURCE_ONLY.lua",
     "f9c39f3190a005da77eb6dea4720dc93e44d5d8e"),
    ("BGXAI072_EPS_FIRST_ARBITER.lua",
     "BGXAI/fox_new/experimental_080_eps_first_buff_preserving_coordinator_source_only/BGXAI072_EPS_FIRST_ARBITER.lua",
     "23e5f992c572dc12b96c7e303cb7916957cd7e5a")
)
def gitblob_sha(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\x00"+raw).hexdigest()

for name,original,expected_git_blob in SOURCES:
    raw=(HERE/name).read_bytes()
    baseline=(REPO/original).read_bytes()
    assert raw==baseline, f"HISTORIC_ADVISORY_DRIFT:{name}"
    assert gitblob_sha(raw)==expected_git_blob, f"PINNED_ADVISORY_BLOB_DRIFT:{name}"

candidate=(HERE/"BGXP6_JOINT_TRIAGE.lua").read_text("utf-8")
assert "function M.plan(" in candidate
assert "return M" in candidate
assert "engine_dispatch=false" in candidate
for forbidden in (
    r"\bAttack\s*\(",r"\bAttackOneRound\s*\(",r"\bAttackReevaluate\s*\(",
    r"\bSpell\s*\(",r"\bClearActions\s*\(",r"\bForceSpell\s*\(",
    r"\bActionOverride\s*\(",r"\bMoveToObject\s*\(",
    r"\bsetLocalInt\s*\(",r"\bSetGlobal\s*\(",r"\bWriteFile\s*\("
):
    assert not re.search(forbidden,candidate), f"GAME_ACTION_DETECTED:{forbidden}"
assert candidate.count("HOLD_NO_ENGINE_DISPATCH") >= 2
assert "deepCopy" in candidate and "ACTOR_SNAPSHOT_NOT_SAFE_TO_CLONE" in candidate
assert not (HERE/"setup-BGXP6.tp2").exists()
assert not (HERE/"BGXP6_INSTALL.py").exists()
assert not (HERE/"M_BX43.lua").exists()
print("BGXP6_SOURCE_ONLY_VERIFIED: two original advisors byte-exact; no engine install or actions")
