"""Regression: R33 menu172 must be permitted by the exact pinned source guard.

Never accesses user game or network. Test against the precise immutable Git
commit used by BGXAI_UPDATE.cmd, not a newer unpinned branch.
"""
from pathlib import Path
import hashlib
import json
import re
import subprocess

BASE = Path(__file__).resolve().parents[3]
pin = json.loads((BASE / "BGXAI/fox_new/BOOTSTRAP_PIN.json").read_text())
src = (BASE / pin["script_path"]).read_bytes()
assert pin["script_size"] == len(src) == 79920
assert hashlib.sha256(src).hexdigest() == pin["script_sha256"] == (
    "7e3c3cc69ce865ff197a5238564757a2c01df71950f56018590f5fa2c38b2417")
assert subprocess.check_output(
    ["git", "show", pin["commit"] + ":" + pin["script_path"]], cwd=BASE) == src
raw = src.decode("ascii")
match = re.search(
    r"function Get-PinnedBytes\(\[string\]\$zrp\) \{\s*"
    r"if\(\$zrp -notmatch '([^']+)' -or \$zrp.Contains\('\.\.'\)\)", raw)
assert match, "Get-PinnedBytes guard missing or safety rules altered"
allow = re.compile(match.group(1))
folder = "BGXAI/BUILD/R33_R31_REUSE_PROF_SNAPSHOT_RO_20261125/"
files = {
    "R33_GUARDED_SOURCE_ONLY.py": "0815d173b276c0f990eb3ab66ac6f8f614a9a0f0f59fc301f94f5f8c890be653",
    "M_BGXR27_R33_SOURCE_ONLY.lua": "1420ef723df1090d56f8f6590fd82e5c69107ba97a39b2ca2ba73f93e0e77069",
}
for name, wanted in files.items():
    p = folder + name
    assert allow.fullmatch(p), "User-reproduced STOP: exact R33 path blocked: " + p
    assert not (".." in p)
    actual = subprocess.check_output(["git", "show", pin["commit"] + ":" + p], cwd=BASE)
    assert hashlib.sha256(actual).hexdigest() == wanted
for forbidden in [
    "BGXAI/BUILD/R33_UNLISTED/R33_GUARDED_SOURCE_ONLY.py",
    "BGXAI/CURRENT/00_CURRENT_STATUS.md",
    "BGXAI/BUILD/R33_R31_REUSE_PROF_SNAPSHOT_RO_20261125/../../secret.py",
]:
    assert not allow.fullmatch(forbidden) or ".." in forbidden
assert "'172' {" in raw
assert len(src) <= 80000
print("PASS R33 PINNED_SOURCE_ALLOWLIST_TEST, exact guard+Lua, unknown dirs denied, traversal denied, game unchanged")
