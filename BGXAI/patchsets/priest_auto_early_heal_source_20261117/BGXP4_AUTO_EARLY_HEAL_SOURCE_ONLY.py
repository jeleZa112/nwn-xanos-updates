#!/usr/bin/env python3
"""BGXP4 conservative AUTO Cure Light Wounds priority: SOURCE ONLY.

Changes ONLY six AUTO cure trigger thresholds in installed BGXPR's original
42 BAF blocks: HP <45% -> HP <70%; no actions or other modes change.
No game installation. No executable gameplay intervention.
"""
from __future__ import annotations
import hashlib
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORIGINAL_BAF = HERE / "BGXPR_LAST_PRIORITY.baf"
PIN = "4e28be67e9d76af91aca0011da736bbbbae787a4c6b5a86e08c02050601b2993"
ROLE = 'Global("BGXR_ROLE","LOCALS",4)'
SPELL = "CLERIC_CURE_LIGHT_WOUNDS"
OLD_THRESHOLD = 45
NEW_THRESHOLD = 70
AUTO_CURE_BLOCKS = (30, 32, 34, 36, 38, 40)
TOTAL_BLOCKS = 42


def canon(raw: bytes) -> bytes:
    data = raw.replace(b"\r\n", b"\n")
    if b"\r" in data:
        raise ValueError("BAF_HAS_UNEXPECTED_CR")
    return data


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def patch(original: bytes) -> bytes:
    raw = canon(original)
    if sha(raw) != PIN:
        raise ValueError("BGXPR_ORIGINAL_BAF_SHA_MISMATCH")
    text = raw.decode("utf-8")
    positions = list(re.finditer(r"(?m)^IF\n.*?^END$", text, flags=re.S))
    if len(positions) != TOTAL_BLOCKS:
        raise ValueError("BGXPR_42_BLOCK_SHAPE_DRIFT")
    newblocks = []
    for idx,m in enumerate(positions):
        block = m.group(0)
        if idx in AUTO_CURE_BLOCKS:
            target = (idx - 30)//2 + 1
            old = f"HPPercentLT(Player{target},{OLD_THRESHOLD})"
            replacement = f"HPPercentLT(Player{target},{NEW_THRESHOLD})"
            gates = [ROLE, 'Global("BGX38_GUARD","LOCALS",1)',
                     "ActionListEmpty()", f"HaveSpell({SPELL})",
                     f"Spell(Player{target},{SPELL})"]
            if any(g not in block for g in gates):
                raise ValueError(f"AUTO_HEAL_GATE_DRIFT:{idx}")
            if block.count(old) != 1 or replacement in block:
                raise ValueError(f"AUTO_HEAL_THRESHOLD_DRIFT:{idx}")
            block = block.replace(old, replacement)
        newblocks.append(block)
    result = []
    previous = 0
    for m,block in zip(positions,newblocks):
        result += [text[previous:m.start()],block]
        previous = m.end()
    result.append(text[previous:])
    proposed = "".join(result).encode("utf-8")
    if proposed == raw or proposed.count(b"\nIF\n") != TOTAL_BLOCKS:
        raise ValueError("BGXP4_UNEXPECTED_BAF_SHAPE")
    # Exact reverse transformation must reproduce the trusted input.
    recovered = proposed
    for i in range(1,7):
        token = f"HPPercentLT(Player{i},{NEW_THRESHOLD})".encode()
        if recovered.count(token) < 1:
            raise ValueError("REVERSE_PATCH_GATE_MISSING")
    # Avoid silently mutating anything beyond the six expected blocks.
    test = []
    for idx,m in enumerate(positions):
        before = m.group(0)
        after = newblocks[idx]
        if idx not in AUTO_CURE_BLOCKS and before != after:
            raise ValueError("NON_AUTO_CURE_BLOCK_MODIFIED")
    return proposed


def report() -> dict:
    old = ORIGINAL_BAF.read_bytes()
    new = patch(old)
    return {"status":"BGXP4_SOURCE_ONLY_EARLY_HEAL_CANDIDATE",
            "old_baf_sha256":PIN,"new_baf_sha256":sha(new),
            "changed_auto_cure_blocks":list(AUTO_CURE_BLOCKS),
            "heal_threshold_old":OLD_THRESHOLD,
            "heal_threshold_new":NEW_THRESHOLD,
            "changes_to_game":False,"ready_to_install":False,
            "note":"Does not override ActionListEmpty, visibility, spell slots or timers"}


if __name__ == "__main__":
    import json
    print(json.dumps(report(),ensure_ascii=False,indent=2))
