"""BGXAI 0.2.7: local-only, non-destructive baseline snapshot for EPS 18.4.

Copies *selected textual* files from an EPS installation into a private folder
beside the user's game, with SHA256 report. It does NOT produce an installed mod,
distribute an EPS source bundle, alter scripts, or execute installers.

CLI: python BGXAI_DEV/src/eps_local_builder_027.py
Only the approved new Foxx game root is accepted when run from CLI.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

APPROVED_GAME_ROOT = Path(r"C:\Games\BG_EET_FOXX_NEW")
REL_SOURCE = "enhanced-powergaming-scripts"
ALLOWED_EXTENSIONS = frozenset({".baf", ".ssl", ".tp2", ".tpa", ".tph", ".tra", ".2da", ".ids", ".lua", ".ini", ".txt", ".md", ".json", ".html", ".htm"})
SKIP_DIRS = frozenset({"backup", "backups", ".git", ".github", "node_modules", "__pycache__"})
MAX_FILE_BYTES = 8_000_000
MAX_TOTAL_BYTES = 120_000_000
MAX_FILES = 10_000


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _file_inventory(source: Path):
    inventory = []
    total = 0
    for folder, dirs, files in os.walk(source, followlinks=False):
        here = Path(folder)
        dirs[:] = sorted(d for d in dirs if d.lower() not in SKIP_DIRS and not (here / d).is_symlink())
        for name in sorted(files):
            original = here / name
            if original.is_symlink() or original.suffix.lower() not in ALLOWED_EXTENSIONS:
                continue
            relative = original.relative_to(source)
            if ".." in relative.parts:
                raise RuntimeError("Unsafe traversal path")
            n = original.stat().st_size
            if n < 0 or n > MAX_FILE_BYTES:
                raise RuntimeError(f"EPS source too large: {relative}")
            total += n
            if total > MAX_TOTAL_BYTES or len(inventory) >= MAX_FILES:
                raise RuntimeError("EPS source exceeds local snapshot safety limit")
            inventory.append((original, relative, n))
    return inventory


def create_local_snapshot(game_root: Path, *, expected_root: Path, stamp: str | None = None) -> dict:
    """Only writes under BGXAI_LOCAL_BUILD, never in EPS folder or game override."""
    root = Path(game_root).resolve(strict=False)
    expected = Path(expected_root).resolve(strict=False)
    if os.path.normcase(str(root)).lower() != os.path.normcase(str(expected)).lower():
        raise RuntimeError(f"Wrong game directory: {root}; expected {expected}")
    if not (root / "chitin.key").is_file():
        raise RuntimeError("chitin.key missing; only run in new Foxx EET directory")
    eps = root / REL_SOURCE
    if not eps.is_dir() or eps.is_symlink():
        raise RuntimeError("EPS source folder not found in this game installation")
    tp2 = eps / "enhanced-powergaming-scripts.tp2"
    if not tp2.is_file():
        raise RuntimeError("EPS .tp2 missing; installation may be incomplete")
    inventory = _file_inventory(eps)
    if not inventory:
        raise RuntimeError("EPS source inventory empty")
    now = stamp or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,40}", now):
        raise RuntimeError("Invalid snapshot label")
    output_parent = root / "BGXAI_LOCAL_BUILD"
    if output_parent.is_symlink():
        raise RuntimeError("Local build folder is a symlink; refusing external destination")
    destination = output_parent / ("EPS_BASELINE_" + now)
    if destination.exists():
        raise RuntimeError(f"Snapshot already exists, no overwrite: {destination}")
    destination.mkdir(parents=True, exist_ok=False)
    report = {
        "schema": 27, "status": "LOCAL_READ_ONLY_SOURCE_SNAPSHOT", "root": str(root),
        "source": str(eps), "snapshot": str(destination),
        "source_files": [], "binary_bcs_info": None,
        "game_modified": False, "eps_modified": False, "public_upload_allowed": False,
    }
    try:
        copy_root = destination / "EPS_ORIGINAL_TEXTS_PRIVATE"
        copy_root.mkdir()
        for original, relative, size in inventory:
            output = copy_root / relative
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(original, output)
            digest = sha256_file(original)
            if sha256_file(output) != digest or output.stat().st_size != size:
                raise RuntimeError(f"Copy integrity error for {relative}")
            report["source_files"].append({"path": relative.as_posix(), "bytes": size, "sha256": digest})
        override = root / "override" / "BDDEFAI.BCS"
        if override.is_file() and not override.is_symlink():
            report["binary_bcs_info"] = {"present_in_override": True,
                                          "bytes": override.stat().st_size,
                                          "sha256": sha256_file(override),
                                          "note": "Metadata only; no compiled BCS copied"}
        else:
            report["binary_bcs_info"] = {"present_in_override": False,
                                          "note": "Absence in override does not prove resource absent from game"}
        weidu = root / "WeiDU.log"
        if weidu.is_file():
            text = weidu.read_text(encoding="utf-8", errors="replace")
            matches = [line for line in text.splitlines() if "ENHANCED-POWERGAMING-SCRIPTS" in line.upper()]
            report["weidu_eps_components"] = len(matches)
            report["weidu_eps_evidence"] = [line[:250] for line in matches[:12]]
        else:
            report["weidu_eps_components"] = None
            report["weidu_eps_evidence"] = []
        report["source_file_count"] = len(inventory)
        report["source_total_bytes"] = sum(size for _, _, size in inventory)
        (destination / "LOCAL_MANIFEST.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (destination / "README_PRIVATE_RU.txt").write_text(
            "BGXAI 027 — ЛОКАЛЬНАЯ КОПИЯ исходных текстов установленного EPS.\n"
            "НЕТ установки. НЕТ изменений игры. НЕТ отправки файлов в интернет.\n"
            "Не выкладывайте каталог EPS_ORIGINAL_TEXTS_PRIVATE в публичный/приватный GitHub.\n"
            "Будущие изменения выполняются в отдельной копии и проходят проверки.\n", encoding="utf-8")
        return report
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise


if __name__ == "__main__":
    try:
        out = create_local_snapshot(APPROVED_GAME_ROOT, expected_root=APPROVED_GAME_ROOT)
        print(f"SUCCESS: private EPS baseline; {out['source_file_count']} files")
        print(out["snapshot"])
        print("Game files/BDDEFAI/EPS source unchanged. No upload performed.")
    except Exception as exc:
        print("ERROR:", str(exc))
        raise SystemExit(1)