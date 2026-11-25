"""R33: official SHA-pinned WeiDU 251 native TP2 syntax, no EET installation.

Reuses the verified official release ZIP SHA + exact binary selection routines
from the previously passed R31 smoke. No native install/uninstall anywhere.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import zipfile

HERE = Path(__file__).resolve().parent
R31_CHECKER = HERE.parent / "R31_R27V3_PASSIVE_SOURCE_20261125" / "R31_NATIVE_TP2_PARSE_RO.py"
R33_GUARD = HERE / "R33_GUARDED_SOURCE_ONLY.py"
R33_GUARD_SHA = "0815d173b276c0f990eb3ab66ac6f8f614a9a0f0f59fc301f94f5f8c890be653"


def imported(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    cli = argparse.ArgumentParser()
    cli.add_argument("--release", type=Path, required=True)
    cli.add_argument("--platform", choices=("linux", "windows"), required=True)
    a = cli.parse_args()
    if hashlib.sha256(R33_GUARD.read_bytes()).hexdigest() != R33_GUARD_SHA:
        raise ValueError("R33_GUARD_SHA_DRIFT")
    old = imported(R31_CHECKER, "r31_native_parse_ro")
    old.verify_release(a.release, a.platform)
    r33 = imported(R33_GUARD, "r33_guard_native_parse_ro")
    text = r33.TP2_TEXT
    if (not text.startswith("BACKUP ~BGXR33/backup~\n") or
        "BEGIN ~BGXR33 passive R27V3 prof snapshot only~\n" not in text or
        text.count("COPY ~BGXR33/staged/M_BGXR27.lua~ ~override/M_BGXR27.lua~") != 1):
        raise ValueError("R33_TP2_CONTRACT_CHANGED")
    with tempfile.TemporaryDirectory(prefix="BGXAI_R33_NATIVE_TP2_") as td:
        root = Path(td)
        tp2 = root / r33.TP2
        tp2.parent.mkdir(parents=True)
        tp2.write_bytes(text.encode("ascii"))
        with zipfile.ZipFile(a.release) as archive:
            member, exe_data = old.choose_binary(archive, a.platform)
        exe = root / ("weidu.exe" if a.platform == "windows" else "weidu")
        exe.write_bytes(exe_data)
        if a.platform == "linux":
            exe.chmod(0o700)
        cmd = [str(exe), "--nogame", "--parse-check", "TP2", str(tp2)]
        out = subprocess.run(cmd, cwd=root, capture_output=True, text=True,
                             stdin=subprocess.DEVNULL, timeout=40, check=False, errors="replace")
        if out.returncode:
            raise ValueError("R33_WEIDU_NATIVE_TP2_PARSE_FAILED:" + (out.stdout+out.stderr)[-900:])
        if tp2.read_bytes() != text.encode("ascii"):
            raise ValueError("R33_PARSER_MUTATED_INPUT")
        if (root / "WeiDU.log").exists() or (root / "override").exists():
            raise ValueError("R33_PARSER_WROTE_GAME_FILES")
        print("PASS R33 REAL_WEIDU_251_TP2_PARSE",a.platform,
              "tp2Sha="+hashlib.sha256(tp2.read_bytes()).hexdigest(),
              "binaryFrom="+member,"gameModified=false")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
