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


def blob_sha(path):
    raw = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def check_source_provenance(root, registry):
    """Fail closed on stale provenance, missing predecessor, or copied R41 internals.

    This is source integrity + reuse evidence, NOT semantic proof that code is new.
    """
    failures = []
    receipts = registry.get("source_provenance_receipts", [])
    if not isinstance(receipts, list):
        return ["source_provenance_receipts must be a list"]
    by_path = {}
    for entry in receipts:
        if not isinstance(entry, dict):
            failures.append("source provenance receipt is not an object")
            continue
        rel = entry.get("source_path")
        if not isinstance(rel, str) or not rel.startswith("BGXAI/BUILD/") or ".." in Path(rel).parts:
            failures.append("invalid source provenance path: " + repr(rel))
            continue
        if rel in by_path:
            failures.append("duplicate source provenance receipt for " + rel)
            continue
        by_path[rel] = entry
        if not entry.get("already_implemented") or not isinstance(entry.get("exclusive_delta"), str) or len(entry["exclusive_delta"].strip()) < 50:
            failures.append(rel + " lacks meaningful predecessor overlap or exclusive delta")
        if not entry.get("evidence"):
            failures.append(rel + " lacks evidence link")
        refs = entry.get("predecessor_sources")
        if not isinstance(refs, list) or not refs:
            failures.append(rel + " has no predecessor_sources")
            continue
        for parent in refs:
            if not isinstance(parent, dict):
                failures.append(rel + " has invalid predecessor")
                continue
            parent_path = parent.get("path", "")
            if not isinstance(parent_path, str) or ".." in Path(parent_path).parts or not parent_path.startswith("BGXAI/BUILD/"):
                failures.append(rel + " has invalid predecessor path")
                continue
            p = root / parent_path
            if not p.is_file():
                failures.append(rel + " prior source missing: " + parent_path)
                continue
            if blob_sha(p) != parent.get("git_blob_sha"):
                failures.append(rel + " prior source changed without reviewed delta: " + parent_path)
        source = root / rel
        if entry.get("status") == "PLANNED_SOURCE_ONLY":
            if source.exists():
                failures.append(rel + " is still marked PLANNED after code was written")
            continue
        if not source.is_file():
            failures.append(rel + " registered source is missing")
            continue
        if blob_sha(source) != entry.get("source_git_blob_sha"):
            failures.append(rel + " changed without an updated reviewed provenance receipt")
        for embedded in entry.get("embedded_sources", []):
            if not isinstance(embedded, str) or ".." in Path(embedded).parts or not embedded.startswith("BGXAI/BUILD/"):
                failures.append(rel + " invalid embedded predecessor")
                continue
            original = root / embedded
            if not original.is_file() or original.read_bytes() not in source.read_bytes():
                failures.append(rel + " no longer embeds unchanged source: " + embedded)

    target = root / "BGXAI/BUILD/R39_STAGED_XEQUIP_SOURCEONLY_20261127"
    candidates = []
    for p in target.glob("*.lua"):
        if p.name.startswith("test_"):
            continue
        if "BGXW3ARM" in p.read_text(encoding="utf-8"):
            candidates.append(p)
    if not candidates:
        failures.append("BGXAI R39 actor-arm source is missing")
    for p in candidates:
        rel = p.relative_to(root).as_posix()
        if rel not in by_path:
            failures.append(rel + " has no predecessor receipt (HOLD_NEW_SOURCE)")
    exact_v3 = root / "BGXAI/BUILD/WEAPON_XEQUIP_LOCAL_ARM_SOURCEONLY_V3_20261127/BGXAI_XEQUIP_LOCAL_ARM_SOURCE_V3.py"
    if not exact_v3.is_file() or not all(token in exact_v3.read_text(encoding="utf-8")
                                              for token in ("BGXW3ARM", "BGXW3TAG", "BGXW3TRY", "XEquipItem(")):
        failures.append("BGXAI V3 original one-shot actor LOCALS are not verified")
    return failures


def preflight_target(root, registry, proposed_source):
    """Run before edits: require reviewed predecessor, existing source or a planned new delta."""
    path = Path(proposed_source)
    if path.is_absolute() or ".." in path.parts or path.as_posix().startswith("./"):
        return ["PREWORK HOLD: target must be a repo-relative path"]
    matches = [x for x in registry.get("source_provenance_receipts", [])
               if isinstance(x, dict) and x.get("source_path") == path.as_posix()]
    if len(matches) != 1:
        return ["PREWORK HOLD: no single scoped predecessor receipt: " + path.as_posix()]
    r = matches[0]
    if not r.get("predecessor_sources") or not r.get("already_implemented") or not r.get("exclusive_delta"):
        return ["PREWORK HOLD: predecessor, overlap and exclusive delta not documented"]
    for parent in r["predecessor_sources"]:
        parent_path = parent.get("path", "")
        if not isinstance(parent_path, str) or ".." in Path(parent_path).parts or not parent_path.startswith("BGXAI/BUILD/"):
            return ["PREWORK HOLD: invalid predecessor path"]
        p = root / parent_path
        if not p.is_file():
            return ["PREWORK HOLD: missing existing source " + parent_path]
        if blob_sha(p) != parent.get("git_blob_sha"):
            return ["PREWORK HOLD: predecessor changed since review " + parent_path]
    source = root / path
    if not source.is_file() and r.get("status") != "PLANNED_SOURCE_ONLY":
        return ["PREWORK HOLD: source missing and no prospective plan recorded"]
    if source.is_file() and blob_sha(source) != r.get("source_git_blob_sha"):
        return ["PREWORK HOLD: source changed before preflight"]
    if source.is_file() and r.get("status") == "PLANNED_SOURCE_ONLY":
        return ["PREWORK HOLD: code exists but receipt still PLANNED"]
    return []


def self_test_provenance():
    from tempfile import TemporaryDirectory
    with TemporaryDirectory(prefix="prior_work_gate_") as d:
        root = Path(d)
        base = "BGXAI/BUILD/R39_STAGED_XEQUIP_SOURCEONLY_20261127/"
        v3 = "BGXAI/BUILD/WEAPON_XEQUIP_LOCAL_ARM_SOURCEONLY_V3_20261127/BGXAI_XEQUIP_LOCAL_ARM_SOURCE_V3.py"
        reset = "BGXAI/BUILD/R40_SESSION_RESET_SOURCEONLY_20261127/M_BGXW3_SESSION_RESET_V1.lua"
        arm = base + "M_BGXW3_EXPLICIT_USER_ARM_SOURCE_ONLY.lua"
        link = base + "M_BGXW3_R41_LINK_SOURCE_ONLY.lua"
        def write(rel, data):
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(data, encoding="utf-8")
        write(v3, "BGXW3ARM BGXW3TAG BGXW3TRY XEquipItem(")
        write(reset, "local Reset={status='SOURCE_ONLY'}")
        write(arm, "local key='BGXW3ARM' -- controlled gesture")
        write(link, "local Reset=(function()\n" + (root/reset).read_text() +
              "\nend)()\nlocal Armer=(function()\n" + (root/arm).read_text() + "\nend)()")
        def receipt(name, predecessors, embedded=None):
            return {
                "source_path": name, "source_git_blob_sha": blob_sha(root/name),
                "predecessor_sources": [
                    {"path": p, "git_blob_sha": blob_sha(root/p)} for p in predecessors],
                "already_implemented": ["V3 actor-local one-shot arm, XEquipItem and queue guards"],
                "exclusive_delta": "Only source-only integration with R40 load order, without duplicated inventory or action implementation",
                "evidence": "BGXAI/CURRENT/00_RESUME_CURRENT.md",
                "status": "RETROSPECTIVE_ACKNOWLEDGMENT_SOURCE_ONLY",
                "embedded_sources": embedded or []
            }
        policy = {"source_provenance_receipts": [
            receipt(arm,[v3]),receipt(link,[v3,arm,reset],[arm,reset])]}
        checks = 0
        def verify(condition, message):
            nonlocal checks
            checks += 1
            if not condition:
                raise AssertionError(message)
        verify(not check_source_provenance(root,policy),"untouched fixture must PASS")
        verify(not preflight_target(root,policy,arm),"existing exact armer preflight must PASS")
        verify(bool(preflight_target(root,policy,base+"NEW_ARM.lua")),"new armer lacking receipt must HOLD")
        write(arm,(root/arm).read_text()+"\n-- modified")
        verify(any("changed" in e for e in check_source_provenance(root,policy)),
               "changed armer must FAIL even if generated link unchanged")
        verify(bool(preflight_target(root,policy,arm)),"stale source before-code gate must HOLD")
        write(arm,"local key='BGXW3ARM' -- controlled gesture")
        write(v3,"BGXW3ARM BGXW3TAG BGXW3TRY -- predecessor changed")
        verify(any("prior source changed" in e for e in check_source_provenance(root,policy)),
               "changed V3 predecessor must FAIL")
        verify(bool(preflight_target(root,policy,arm)),"changed predecessor preflight must HOLD")
        write(v3,"BGXW3ARM BGXW3TAG BGXW3TRY XEquipItem(")
        write(link,"local Reset=(function() -- lost original embedded module\nend)()")
        policy["source_provenance_receipts"][1]["source_git_blob_sha"] = blob_sha(root/link)
        verify(any("no longer embeds unchanged source" in e for e in check_source_provenance(root,policy)),
               "R41 replacement must FAIL even if new link hash is recorded")
        write(link,"local Reset=(function()\n" + (root/reset).read_text() +
              "\nend)()\nlocal Armer=(function()\n" + (root/arm).read_text() + "\nend)()")
        policy["source_provenance_receipts"][1]["source_git_blob_sha"]=blob_sha(root/link)
        write(base+"UNREVIEWED.lua","BGXW3ARM is present")
        verify(any("HOLD_NEW_SOURCE" in e for e in check_source_provenance(root,policy)),
               "new actor-arm implementation without receipt must FAIL")
        (root/(base+"UNREVIEWED.lua")).unlink()
        verify(not check_source_provenance(root,policy),"restored fixture must PASS")
        planned=base+"FUTURE_ARM.lua"
        planned_receipt=receipt(arm,[v3]).copy()
        planned_receipt.update(source_path=planned,source_git_blob_sha=None,status="PLANNED_SOURCE_ONLY")
        policy["source_provenance_receipts"].append(planned_receipt)
        verify(not preflight_target(root,policy,planned),"precommitted plan may pass preflight")
        write(planned,"BGXW3ARM newly written")
        verify(bool(check_source_provenance(root,policy)),"written source still PLANNED must FAIL")
        verify(bool(preflight_target(root,policy,planned)),"planned status after writing must HOLD")
        print(f"PREWORK PROVENANCE SELFTEST PASS: {checks} positive and adversarial checks")


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
    # PREDECESSOR-GATE: provenance is bound to Git blobs, not fragile comments
    # inside generated R41 or SHA-pinned R39 Lua source.
    try:
        capsule = (ROOT / "BGXAI/CURRENT/00_RESUME_CURRENT.md").read_text(encoding="utf-8")
        registry = json.loads((ROOT / "GLOBAL_PROJECT_RULES/KNOWN_ERROR_GATES_V1.json").read_text(encoding="utf-8"))
        if "ПОДТВЕРЖДЁННЫЙ ПОВТОР V3" not in capsule:
            errors.append("BGXAI canonical resume omits confirmed overlap with V3")
        expected_id = "BGXAI_R39_V3_PRIOR_WORK_GATE_BYPASS_20261128"
        if not any(x.get("error_id") == expected_id for x in registry.get("project_error_register", [])):
            errors.append("BGXAI prior-work violation not logged in global known error register")
        errors.extend(check_source_provenance(ROOT, registry))
    except (OSError, ValueError, UnicodeError) as exc:
        errors.append("BGXAI prior-work provenance gate unavailable: " + str(exc))
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
    if len(sys.argv) == 2 and sys.argv[1] == "--self-test":
        try:
            self_test_provenance()
        except (OSError, ValueError, UnicodeError, AssertionError) as exc:
            print("PREWORK PROVENANCE SELFTEST FAIL: " + str(exc), file=sys.stderr)
            sys.exit(1)
        sys.exit(0)
    if len(sys.argv) >= 2 and sys.argv[1] == "--preflight":
        if len(sys.argv) != 3:
            print("PREWORK HOLD: usage --preflight REPO_RELATIVE_SOURCE_PATH", file=sys.stderr)
            sys.exit(2)
        try:
            reg = json.loads((ROOT / "GLOBAL_PROJECT_RULES/KNOWN_ERROR_GATES_V1.json").read_text(encoding="utf-8"))
            problems = preflight_target(ROOT, reg, sys.argv[2])
        except (OSError, ValueError, UnicodeError) as exc:
            problems = ["PREWORK HOLD: " + str(exc)]
        for problem in problems:
            print(problem, file=sys.stderr)
        if problems:
            sys.exit(2)
        print("PREWORK SOURCE RECEIPT PASS: existing source/ancestry recorded; compare actual behavior before edits.")
        sys.exit(0)
    problems = check()
    if problems:
        for problem in problems:
            print("RESUME DRIFT: " + problem, file=sys.stderr)
        sys.exit(1)
    print("RESUME PASS: current sources, predecessor receipts, and canonical resumes agree.")
