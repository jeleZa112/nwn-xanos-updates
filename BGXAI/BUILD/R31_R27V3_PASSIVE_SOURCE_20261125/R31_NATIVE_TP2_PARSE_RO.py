"""BGXAI R31: exact real WeiDU v251 TP2 parser, no game modification.

Run only with official SHA256-verified WeiDU release zip. This module writes
the TP2 *only* to a disposable temporary directory and invokes --nogame
--parse-check TP2, never force-install/uninstall.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
from pathlib import Path
import os
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent
GUARD = ROOT / "R31_GUARDED_SOURCE_ONLY.py"
GUARD_SHA = "0ac97a702c4ac5919549a5a54cf9ef6a01a8fbd582273fc556fe9c82a60950ee"
OFFICIAL_ZIP = {
    "linux": "3e1a34ec5d6e934b1d4a34541a1312d0170b120c6efe903a732415acde3bd3c0",
    "windows": "a54c6198d6ebed8139793fcacb225500d563657c23fc775b840383f9750493d8",
}

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def verify_release(zip_path: Path, platform: str) -> None:
    if not zip_path.is_file() or zip_path.stat().st_size > 15_000_000:
        raise ValueError("OFFICIAL_ARCHIVE_MISSING_OR_OVERSIZE")
    if digest(zip_path.read_bytes()) != OFFICIAL_ZIP[platform]:
        raise ValueError("OFFICIAL_WEIDU_251_SHA_MISMATCH")

def choose_binary(archive: zipfile.ZipFile, platform: str) -> tuple[str, bytes]:
    suffix = ".exe" if platform == "windows" else ""
    candidates = []
    for member in archive.infolist():
        name = member.filename.replace("\\", "/")
        if member.is_dir() or name.startswith("/") or any(
            segment in (".", "..", "") for segment in name.split("/")
        ):
            continue
        leaf = name.split("/")[-1].lower()
        if leaf == "weidu" + suffix or leaf == "setup-weidu" + suffix:
            if member.file_size > 16_000_000 or member.file_size < 100_000:
                raise ValueError("WEIDU_BINARY_SIZE_INVALID")
            candidates.append(member)
    if not candidates:
        raise ValueError("WEIDU_BINARY_NOT_IN_VERIFIED_ZIP")
    # Choose exact named root-most binary; no arbitrary extracted scripts.
    candidates.sort(key=lambda m: (m.filename.count("/"), len(m.filename)))
    member = candidates[0]
    raw = archive.read(member)
    if platform == "windows" and raw[:2] != b"MZ":
        raise ValueError("WEIDU_WINDOWS_PE_INVALID")
    if platform == "linux" and raw[:4] != b"\\x7fELF":
        raise ValueError("WEIDU_LINUX_ELF_INVALID")
    return member.filename, raw

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--release", type=Path, required=True)
    p.add_argument("--platform", choices=("linux", "windows"), required=True)
    a = p.parse_args()
    verify_release(a.release, a.platform)
    if digest(GUARD.read_bytes()) != GUARD_SHA:
        raise ValueError("R31_GUARD_SOURCE_CHANGED")
    spec = importlib.util.spec_from_file_location("bgxai_r31_guard", GUARD)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    tp2_text = mod.TP2_TEXT
    if not (tp2_text.startswith("BACKUP ~BGXR31/backup~\\n")
            and "BEGIN ~BGXR31 passive R27V3 observer only~" in tp2_text
            and tp2_text.count("COPY ~BGXR31/staged/M_BGXR27.lua~ ~override/M_BGXR27.lua~") == 1):
        raise ValueError("R31_TP2_CONTRACT_CHANGED")
    with tempfile.TemporaryDirectory(prefix="bgxai_r31_weidu_parse_") as td:
        root = Path(td)
        tp2 = root / "BGXR31" / "setup-BGXR31.tp2"
        tp2.parent.mkdir(parents=True)
        tp2.write_bytes(tp2_text.encode("ascii"))
        with zipfile.ZipFile(a.release) as archive:
            member,raw = choose_binary(archive,a.platform)
        binary = root / ("weidu.exe" if a.platform == "windows" else "weidu")
        binary.write_bytes(raw)
        if a.platform == "linux":
            binary.chmod(0o700)
        command = [str(binary), "--nogame", "--parse-check", "TP2", str(tp2)]
        completed = subprocess.run(
            command, cwd=root, capture_output=True, text=True, timeout=40,
            stdin=subprocess.DEVNULL, errors="replace", check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                "R31_NATIVE_WEIDU_PARSE_FAILED exit=" + str(completed.returncode)
                + "\\n" + (completed.stdout+completed.stderr)[-2000:]
            )
        if not tp2.read_bytes() == tp2_text.encode("ascii"):
            raise RuntimeError("TP2_MUTATED")
        if (root / "WeiDU.log").exists() or (root / "override").exists():
            raise RuntimeError("PARSER_WROTE_FAKE_GAME")
        print("R31_NATIVE_WEIDU_251_TP2_PARSE_PASS",a.platform,
              "guardSHA="+GUARD_SHA,"tp2SHA="+digest(tp2.read_bytes()),
              "binaryFrom="+member,"gameModified=false")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
