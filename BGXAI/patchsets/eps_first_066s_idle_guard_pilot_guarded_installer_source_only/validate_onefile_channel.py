#!/usr/bin/env python3
"""Offline CI gate for the existing pinned one-file BGXAI updater.
Reads Git objects; never executes the updater or touches a user's game.
"""
from __future__ import annotations
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = "BGXAI/BGXAI_SYNC.ps1"
CMD = "BGXAI_UPDATE.cmd"
PIN = "BGXAI/fox_new/BOOTSTRAP_PIN.json"
MANIFEST = "BGXAI/patchsets/eps_first_066s_idle_guard_pilot_guarded_installer_source_only/manifest_updater.json"
RELEASE_DIR = MANIFEST.rsplit("/", 1)[0] + "/"
OLD_PINNED = "b238eec6c929d0c908d61c09353bf26a41c461f9"
OLD_SHA = "f7452cb7757e6bac074655cabd0c17dac701c07660707ce2496deda433bc5a48"
NEW_SHA = "bc4b176aaed83852e597cef8b2cc168b9732fbfa31bbb79ca6442b854351a466"
NEW_SCRIPT_COMMIT = "9ad7249c768bc4770e5adb5b8582d8c0184e32b7"

def git_bytes(rev: str, path: str) -> bytes:
    proc = subprocess.run(["git", "show", f"{rev}:{path}"], cwd=ROOT,
                          capture_output=True, check=False)
    if proc.returncode:
        raise AssertionError(f"Cannot read pinned Git object {rev}:{path}: {proc.stderr[-200:]!r}")
    return proc.stdout

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def menu(content: bytes) -> list[str]:
    return [line.strip() for line in content.decode("utf-8-sig").splitlines()
            if re.match(r"^\s*Write-Host ' (?:\d{1,2}) - ", line)]

def choices(content: bytes) -> list[str]:
    return [line.strip() for line in content.decode("utf-8-sig").splitlines()
            if re.match(r"^\s*'\d{1,2}' \{", line)]

def check() -> None:
    old = git_bytes(OLD_PINNED, SCRIPT)
    assert len(old) == 70582 and sha(old) == OLD_SHA, "old pinned updater drift"
    new = git_bytes("HEAD", SCRIPT)
    assert len(new) == 74220 and sha(new) == NEW_SHA, "new updater hash/size drift"
    pinned = json.loads(git_bytes("HEAD", PIN))
    assert pinned["schema"] == 1 and pinned["channel"] == "bgxai-fox-new-onefile"
    assert pinned["commit"] == NEW_SCRIPT_COMMIT
    assert pinned["script_sha256"] == NEW_SHA
    assert pinned["script_size"] == 74220 and pinned["script_path"] == SCRIPT
    assert git_bytes(pinned["commit"], SCRIPT) == new, "current file differs from pinned script"
    assert git_bytes("HEAD", CMD) == git_bytes(OLD_PINNED, CMD), "BGXAI_UPDATE.cmd changed"

    m_old, m_new = menu(old), menu(new)
    c_old, c_new = choices(old), choices(new)
    assert len(m_old) == 92 and len(m_new) == 97, "menu count mismatch"
    assert m_new[:91] == m_old[:91] and m_new[-1] == m_old[-1], "legacy menu modified"
    assert len(c_old) == 91 and len(c_new) == 96, "option dispatch count mismatch"
    assert c_new[:91] == c_old, "legacy dispatch modified"
    for number in range(92, 97):
        assert any(re.search(rf"Write-Host ' {number} - ", ln) for ln in m_new)
        assert any(re.match(rf"'{number}' \{{", ln) for ln in c_new)
    text = new.decode("utf-8-sig")
    assert "INSTALL_BGXAI_IDLE_GUARD" in text and "ROLLBACK_BGXAI_IDLE_GUARD" in text
    assert "'--yes' '--confirm' $token" in text
    assert "function VerifyIdleGuardSource" in text
    assert "function CheckIdleGuardReadOnly" in text
    assert "function RunIdleGuardGuarded" in text
    assert "SyncRelease $releaseIdle" in text
    assert "AssertNotReparse $file" in text

    pat = re.search(r"\$remotePath -notmatch '([^']+)'", text)
    assert pat, "remote allowlist missing"
    allow = re.compile(pat.group(1), re.IGNORECASE)
    assert allow.fullmatch(MANIFEST)
    assert allow.fullmatch(RELEASE_DIR + "README_RU.md")
    assert allow.fullmatch("BGXAI/fox_new/experimental_067_early_guard_guarded/manifest_updater.json")
    assert not allow.fullmatch("BGXAI/evil/a.ps1")
    assert "-or $remotePath.Contains('..')" in text

    raw_manifest = git_bytes("HEAD", MANIFEST)
    assert sha(raw_manifest) == "eef8f8fcb45f9783563e2e6120c71a2731932460537d89ae1d4261e01cf330a1"
    spec = json.loads(raw_manifest)
    assert spec["schema"] == 1 and spec["channel"] == "bgxai-fox-new-safe-source"
    assert spec["version"] == "0.3.36-066S-IDLE-GUARD-PILOT"
    assert len(spec["files"]) == 19
    seen = set()
    for f in spec["files"]:
        dest, source = f["dest"], f["source"]
        assert source == RELEASE_DIR + dest and dest not in seen
        assert re.fullmatch(r"[A-Za-z0-9_.-]+", dest) and ".." not in dest
        seen.add(dest)
        data = git_bytes(pinned["commit"], source)
        assert len(data) == f["size"] and sha(data) == f["sha256"], f"source mismatch: {source}"
        assert f"'{dest}'" in text, f"release name missing: {dest}"
    print("BGXAI_ONEFILE_CHANNEL_PASS: old 1-91 preserved, new 92-96, pin SHA/size, 19/19 sources, game unchanged")

if __name__ == "__main__":
    check()
