#!/usr/bin/env python3
"""Read-only guard: fail when canonical project resume diverges from checked-in source.
Never accesses user saves, game files, private archives, or update installers.
"""
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]

def marker(doc, key):
    hits = re.findall(r"(?m)^<!-- RESUME_GUARD_" + re.escape(key) + r"=(\S+) -->$", doc)
    if len(hits) != 1:
        raise ValueError(f"{key}: expected one value, got {len(hits)}")
    return hits[0]

def check():
    errors = []
    try:
        rel = json.loads((ROOT / "bg-eet-ru/onefile/release.json").read_text(encoding="utf-8"))
        doc = (ROOT / "bg-eet-ru/CURRENT/00_RESUME_CURRENT.md").read_text(encoding="utf-8")
        if marker(doc, "BG_EET_RU_RELEASE_VERSION") != str(rel["version"]):
            errors.append("BG_EET_RU current VERSION is stale vs release.json")
        if marker(doc, "BG_EET_RU_RELEASE_SHA256") != str(rel["sha256"]):
            errors.append("BG_EET_RU current SHA is stale vs release.json")
    except (OSError, ValueError, KeyError) as exc:
        errors.append("BG_EET_RU resume cannot be verified: " + str(exc))
    try:
        doc = (ROOT / "BGXAI/CURRENT/00_RESUME_CURRENT.md").read_text(encoding="utf-8")
        raw = (ROOT / "BGXAI/BUILD/R39_STAGED_XEQUIP_SOURCEONLY_20261127/BGXAI_R39_JAGAN_STAF01_SOURCE_ONLY.baf").read_bytes()
        if marker(doc, "BGXAI_R39_BAF_BYTES") != str(len(raw)):
            errors.append("BGXAI R39 BAF size differs from current resume")
        if marker(doc, "BGXAI_R39_BAF_SHA256") != hashlib.sha256(raw).hexdigest():
            errors.append("BGXAI R39 BAF SHA differs from current resume")
    except (OSError, ValueError) as exc:
        errors.append("BGXAI resume cannot be verified: " + str(exc))
    # PREDECESSOR-GATE (BGXAI R39 armer): exact existing feature ancestry, not a
    # proof of absence of duplication. FAIL if agent drops V3 attribution in new code.
    try:
        v3 = (ROOT / "BGXAI/BUILD/WEAPON_XEQUIP_LOCAL_ARM_SOURCEONLY_V3_20261127/BGXAI_XEQUIP_LOCAL_ARM_SOURCE_V3.py").read_text(encoding="utf-8")
        capsule = (ROOT / "BGXAI/CURRENT/00_RESUME_CURRENT.md").read_text(encoding="utf-8")
        registry = json.loads((ROOT / "GLOBAL_PROJECT_RULES/KNOWN_ERROR_GATES_V1.json").read_text(encoding="utf-8"))
        if not all(token in v3 for token in ('BGXW3ARM', 'BGXW3TAG', 'BGXW3TRY', 'XEquipItem(')):
            errors.append("BGXAI prior V3 actor-local one-shot implementation unavailable or changed")
        if "ПОДТВЕРЖДЁННЫЙ ПОВТОР V3" not in capsule:
            errors.append("BGXAI canonical resume omits confirmed overlap with V3")
        expected_id = "BGXAI_R39_V3_PRIOR_WORK_GATE_BYPASS_20261128"
        if not any(x.get("error_id") == expected_id for x in registry.get("project_error_register", [])):
            errors.append("BGXAI prior-work violation not logged in global known error register")
        arm_dir = ROOT / "BGXAI/BUILD/R39_STAGED_XEQUIP_SOURCEONLY_20261127"
        candidates = [p for p in arm_dir.glob("*.lua") if not p.name.startswith("test_") and "BGXW3ARM" in p.read_text(encoding="utf-8")]
        if not candidates:
            errors.append("BGXAI guarded R39 armer missing")
        for p in candidates:
            source = p.read_text(encoding="utf-8")
            head = "\n".join(source.splitlines()[:20])
            if not all(s in head for s in (
                "PRIOR_WORK_REUSE: BGXAI/BUILD/WEAPON_XEQUIP_LOCAL_ARM_SOURCEONLY_V3_20261127/",
                "PRIOR_WORK_EXISTING:",
                "PRIOR_WORK_DELTA_ONLY:",
                "PRIOR_WORK_STATUS:",
                "PRIOR_WORK_NO_REIMPLEMENT:"
            )):
                errors.append(p.name + " missing verified V3 provenance and delta-only receipt")
    except (OSError, ValueError, UnicodeError) as exc:
        errors.append("BGXAI prior-work gate unavailable: " + str(exc))
    routes = {
        "BGXAI/README_RU.md": "CURRENT/00_RESUME_CURRENT.md",
        "BGXAI/CURRENT/00_CURRENT_STATUS.md": "00_RESUME_CURRENT.md",
        "BGXAI/CURRENT/00_AUTO_CONTINUE_READ_FIRST.md": "00_RESUME_CURRENT.md",
        "bg-eet-ru/README.md": "CURRENT/00_RESUME_CURRENT.md",
    }
    for path, target in routes.items():
        try:
            if target not in (ROOT / path).read_text(encoding="utf-8"):
                errors.append(path + " does not route to canonical " + target)
        except OSError as exc:
            errors.append(path + " missing: " + str(exc))
    return errors

if __name__ == "__main__":
    problems = check()
    if problems:
        for problem in problems:
            print("RESUME DRIFT: " + problem, file=sys.stderr)
        sys.exit(1)
    print("RESUME PASS: BGXAI source and BG_EET_RU release match canonical resume.")
