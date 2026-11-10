#!/usr/bin/env python3
"""BGXAI 056: verify exact bytes of every pinned distributable, offline/read-only.

Validates both release manifest.json and installer SOURCE_MANIFEST.json. Run
from any directory; no network, game files, or installation is accessed.
"""
from __future__ import annotations
import hashlib
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[2]  # repo/BGXAI/fox_new/experimental_056_active_guard -> repo
UPDATER = REPO / "BGXAI" / "BGXAI_SYNC.ps1"
EXPECTED_NAMES = (
    "BGX56/M_BX43.lua", "BGX56/BGX56_RECEIVER.baf", "BGX56/setup-BGX56.tp2",
    "BGXAI56_BUILDER.py", "BGXAI56_INSTALL.py", "README_RU.md",
    "tests/test_056.py", "tests/test_lua_056.py", "ci_weidu_056.py",
    "ids/trigger.ids", "ids/action.ids", "ids/object.ids", "ids/modal.ids",
    "SOURCE_MANIFEST.json",
)

def main() -> int:
    outer = json.loads((HERE / "manifest.json").read_text(encoding="utf-8"))
    inner = json.loads((HERE / "SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
    assert outer["status"] == "EXPERIMENTAL_OPTIN_INSTALL_GATED"
    assert inner["status"] == "OPT_IN_ACTIVE_056_TWO_OVERRIDE_FILES"
    assert outer["version"] == inner["version"]
    entries = outer["files"]
    all_names = [entry["dest"] for entry in entries]
    assert len(all_names) == len(set(all_names)), "Duplicate path in release manifest"
    assert set(all_names) == set(EXPECTED_NAMES), "Unexpected/missing release files"
    assert set(inner["files"]) == set(EXPECTED_NAMES) - {"SOURCE_MANIFEST.json"}, "Inner manifest scope mismatch"
    for entry in entries:
        dest, source = entry["dest"], entry["source"]
        assert source == "BGXAI/fox_new/experimental_056_active_guard/" + dest, f"Source path mismatch: {dest}"
        path = HERE / dest
        assert path.is_file() and not path.is_symlink(), f"Missing or symlink: {dest}"
        data = path.read_bytes()
        actual_size = len(data)
        actual_sha = hashlib.sha256(data).hexdigest()
        assert actual_size == entry["size"], f"SIZE ERROR {dest}: {actual_size} != {entry['size']}"
        assert actual_sha == entry["sha256"], f"SHA256 ERROR {dest}: {actual_sha} != {entry['sha256']}"
        if dest in inner["files"]:
            assert inner["files"][dest] == {"size": actual_size, "sha256": actual_sha}, f"Inner manifest error: {dest}"
        print(f"VERIFIED {dest}: {actual_size} bytes {actual_sha}")
    script = UPDATER.read_text(encoding="utf-8")
    match = re.search(r"\$release056=@\{(.*?)\n\}", script, flags=re.S)
    assert match is not None, "Updater lacks release056"
    named = re.search(r"names=@\((.*?)\)", match.group(1), flags=re.S)
    assert named is not None, "Updater missing release names"
    named_files = re.findall(r"'([^']+)'", named.group(1))
    assert set(named_files) == set(EXPECTED_NAMES), "Updater name set does not match pinned manifest"
    assert 'experimental_056_active_guard/manifest.json' in match.group(1)
    assert 'experimental_056_active_guard/' in match.group(1)
    for option in range(55, 60):
        assert f"'{option}' {{" in script, f"Missing updater option {option}"
    print(f"BGXAI_056_MANIFEST_ALL_PASS files={len(entries)} with GitHub sync path and source manifest")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("BGXAI_056_MANIFEST_FAIL:", str(exc), file=sys.stderr)
        sys.exit(1)