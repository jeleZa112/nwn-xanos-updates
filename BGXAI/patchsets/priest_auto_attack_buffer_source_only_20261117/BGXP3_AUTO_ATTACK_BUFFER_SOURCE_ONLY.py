#!/usr/bin/env python3
"""Read-only candidate builder for BGXP3 AUTO attack safety buffer.

Input is the exact already-released BGXP2 BAF. This module never touches EET.
No actions, Lua, EPS or BGXPR healing rules are added or changed.
"""
from __future__ import annotations
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "priest_combat_eps_first_20261116" / "BGXP2_LAST_PRIORITY.baf"
BASE_SHA256 = "a93dd1d46bf55ff7a5d53f15b0b55c1fc2ad10e39a4a23ae90ece62bfd76df2d"
AUTO_ATTACK_MARKER = "// BGXP2 AUTO guarded one-round fallback ATTACK when EPS idle"
THRESHOLD_BEFORE = 45
THRESHOLD_AFTER = 60


def candidate(original: bytes) -> bytes:
    """Adjust only AUTO AttackOneRound's six allied-HP gates.

    This is *preventive*, not interrupting: an already running AttackOneRound,
    manual command or EPS queue is left untouched. Critical healing still
    depends on existing BGXPR preconditions (ActionListEmpty etc.).
    """
    # Windows checkout may store CRLF; verify the *canonical LF release* byte hash.
    # Reject any bare CR or other mutations instead of weakening the SHA gate.
    canonical = original.replace(b"\r\n", b"\n")
    if b"\r" in canonical or hashlib.sha256(canonical).hexdigest() != BASE_SHA256:
        raise ValueError("BGXP2_BASELINE_SHA_MISMATCH")
    raw = canonical.decode("utf-8")
    if raw.count(AUTO_ATTACK_MARKER) != 1:
        raise ValueError("AUTO_ATTACK_BLOCK_NOT_UNIQUE")
    prefix, tail = raw.split(AUTO_ATTACK_MARKER, 1)
    if tail.count("\nIF\n") != 1 or tail.count("\nEND") != 1:
        raise ValueError("AUTO_ATTACK_BLOCK_SHAPE_CHANGED")
    if tail.count("AttackOneRound(NearestEnemyOf(Myself))") != 1:
        raise ValueError("AUTO_ATTACK_ACTION_MISSING")
    if 'Global("BGXR_ROLE","LOCALS",4)' not in tail or "ActionListEmpty()" not in tail:
        raise ValueError("AUTO_ATTACK_SAFETY_GATE_MISSING")
    if prefix.count("\nIF\n") != 27 or raw.count("\nIF\n") != 28:
        raise ValueError("NON_AUTO_BLOCK_COUNT_CHANGED")
    patched = tail
    for slot in range(1, 7):
        old = f"!HPPercentLT(Player{slot},{THRESHOLD_BEFORE})"
        new = f"!HPPercentLT(Player{slot},{THRESHOLD_AFTER})"
        if patched.count(old) != 1 or new in patched:
            raise ValueError(f"ALLY_HP_GATE_DRIFT:{slot}")
        patched = patched.replace(old, new, 1)
    result = (prefix + AUTO_ATTACK_MARKER + patched).encode("utf-8")
    if result == canonical or len(result) != len(canonical):
        raise ValueError("UNEXPECTED_BYTE_LENGTH")
    return result


def check() -> dict[str, object]:
    original = SOURCE.read_bytes()
    proposed = candidate(original)
    stats = {
        "status": "SOURCE_ONLY_CANDIDATE_VERIFIED",
        "game_modified": False,
        "installable": False,
        "old_sha256": BASE_SHA256,
        "candidate_sha256": hashlib.sha256(proposed).hexdigest(),
        "unchanged_first_blocks": 27,
        "changed_blocks": 1,
        "auto_attack_allied_hp_buffer_percent": THRESHOLD_AFTER,
        "note": "Does not interrupt actions or guarantee healing; live evidence needed",
    }
    return stats


if __name__ == "__main__":
    import json
    print(json.dumps(check(), indent=2, ensure_ascii=False))
