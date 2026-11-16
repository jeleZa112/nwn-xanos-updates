#!/usr/bin/env python3
"""BGXP5 conservative AUTO early Cure and explicit no-friendly-target source proposal.

No game access and no installation. BGXP3 remains the current installed baseline.
"""
from __future__ import annotations
import hashlib
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PR_SOURCE=ROOT/"BGXPR_LAST_PRIORITY.baf"
COMBAT_SOURCE=ROOT/"BGXP2_LAST_PRIORITY.baf"
PR_SHA="4e28be67e9d76af91aca0011da736bbbbae787a4c6b5a86e08c02050601b2993"
COMBAT_SHA="a93dd1d46bf55ff7a5d53f15b0b55c1fc2ad10e39a4a23ae90ece62bfd76df2d"
BGXP3_BUF_SHA="c3d41f9d046203e8acbb2e8ff3896183b10a12e58eaef743d67eeab77213f378"
CURE_PRIORITY_THRESHOLD=(35,70)
MAX_HEAL_TARGET_DISTANCE=18
COMBAT_INDICES=(24,25,26,27)
AUTO_ATTACK_INDEX=27


def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()


def canonical(data:bytes)->bytes:
    raw=data.replace(b"\r\n",b"\n")
    if b"\r" in raw:
        raise ValueError("STRAY_CR_IN_SOURCE")
    return raw


def sections(raw:bytes,expected:int)->list[str]:
    txt=canonical(raw).decode("utf-8")
    chunks=re.findall(r"(?m)^IF\n[\s\S]*?^END$",txt)
    if len(chunks)!=expected:
        raise ValueError("SOURCE_BAF_BLOCK_COUNT_DRIFT")
    return chunks


def guarded_combat_baf(raw:bytes)->bytes:
    src=canonical(raw)
    if sha(src)!=COMBAT_SHA:
        raise ValueError("BGXP2_BAF_SHA_DRIFT")
    blocks=sections(src,28)
    for i in COMBAT_INDICES:
        b=blocks[i]
        if b.count("See(NearestEnemyOf(Myself))")!=1:
            raise ValueError("COMBAT_TARGET_GATE_CHANGED")
        if "Global(\"BGX38_GUARD\",\"LOCALS\",1)" not in b or "ActionListEmpty()" not in b:
            raise ValueError("COMBAT_MANUAL_GUARD_MISSING")
        if "!InParty(NearestEnemyOf(Myself))" in b:
            raise ValueError("FRIENDLY_FILTER_ALREADY_EXISTS")
        b=b.replace("See(NearestEnemyOf(Myself))",
                    "!InParty(NearestEnemyOf(Myself))\n  See(NearestEnemyOf(Myself))",1)
        if i==AUTO_ATTACK_INDEX:
            for n in range(1,7):
                old=f"!HPPercentLT(Player{n},45)"
                if b.count(old)!=1:
                    raise ValueError("AUTO_ATTACK_THRESHOLD_DRIFT")
                b=b.replace(old,f"!HPPercentLT(Player{n},60)",1)
        blocks[i]=b
    # Build without any textual changes outside the four expected IF blocks.
    source=src.decode("utf-8")
    spans=list(re.finditer(r"(?m)^IF\n[\s\S]*?^END$",source))
    out=[]; last=0
    for i,m in enumerate(spans):
        out.extend([source[last:m.start()],blocks[i]])
        last=m.end()
    out.append(source[last:])
    result="".join(out).encode("utf-8")
    if len(sections(result,28))!=28:
        raise ValueError("COMBAT_RESULT_INVALID")
    return result


def expected_bgxp3_baf(raw:bytes)->bytes:
    source=canonical(raw)
    if sha(source)!=COMBAT_SHA:
        raise ValueError("BGXP2_BAF_SHA_DRIFT")
    t=source.decode("utf-8")
    blocks=sections(source,28)
    b=blocks[-1]
    for n in range(1,7):
        old=f"!HPPercentLT(Player{n},45)"
        if b.count(old)!=1:raise ValueError("BGXP3_AUTO_ATTACK_INPUT_DRIFT")
        b=b.replace(old,f"!HPPercentLT(Player{n},60)",1)
    spans=list(re.finditer(r"(?m)^IF\n[\s\S]*?^END$",t))
    m=spans[-1]
    result=(t[:m.start()]+b+t[m.end():]).encode()
    if sha(result)!=BGXP3_BUF_SHA:raise ValueError("BGXP3_BAF_SOURCE_MISMATCH")
    return result


def priority_auto_cure_baf()->bytes:
    lines=[]
    for threshold in CURE_PRIORITY_THRESHOLD:
        for slot in range(1,7):
            idx=slot-1
            lines.append(f"""// BGXP5 source only: AUTO safety-first cure slot {slot} below {threshold}%
IF
  InParty(Myself)
  !InPartySlot(Myself,{idx})
  Global("BGX38_GUARD","LOCALS",1)
  Global("BGXR_ROLE","LOCALS",4)
  Global("BGX66_S_HEAL_SLOT","LOCALS",0)
  !GlobalTimerNotExpired("BGX66_S_HEAL_COOLDOWN","LOCALS")
  !GlobalTimerNotExpired("BGXR_HEAL_CD","LOCALS")
  ActionListEmpty()
  ModalState(NONE)
  HaveSpell(CLERIC_CURE_LIGHT_WOUNDS)
  InParty(Player{slot})
  InPartySlot(Player{slot},{idx})
  InMyArea(Player{slot})
  See(Player{slot})
  HPGT(Player{slot},0)
  Range(Player{slot},{MAX_HEAL_TARGET_DISTANCE})
  HPPercentLT(Player{slot},{threshold})
THEN
  RESPONSE #100
    SetGlobalTimer("BGXR_HEAL_CD","LOCALS",12)
    Spell(Player{slot},CLERIC_CURE_LIGHT_WOUNDS)
END
""")
    out=("\n".join(lines)).encode("utf-8")
    blocks=sections(out,12)
    assert len(blocks)==12
    for b in blocks:
        if "ActionListEmpty()" not in b or "Spell(Player" not in b:
            raise ValueError("PRIORITY_HEAL_ACTION_DRIFT")
    return out


def report()->dict:
    old=canonical(COMBAT_SOURCE.read_bytes())
    pr=canonical(PR_SOURCE.read_bytes())
    if sha(pr)!=PR_SHA:raise ValueError("BGXPR_BAF_SHA_DRIFT")
    combat=guarded_combat_baf(old)
    priority=priority_auto_cure_baf()
    return {"status":"BGXP5_SOURCE_ONLY_NO_INSTALL",
            "friendly_protection_combat_blocks":list(COMBAT_INDICES),
            "emergency_auto_heal_blocks":12,
            "heal_hp_thresholds":list(CURE_PRIORITY_THRESHOLD),
            "max_visible_heal_range":MAX_HEAL_TARGET_DISTANCE,
            "priority_baf_sha256":sha(priority),
            "combat_baf_sha256":sha(combat),
            "current_bgxp3_baf_sha256":sha(expected_bgxp3_baf(old)),
            "game_modified":False,"installable":False,
            "manual_actions_preserved":True,
            "limitations":"Cannot interrupt currently active action or fix LOS/timer/role flags"}


if __name__=="__main__":
    import json
    print(json.dumps(report(),ensure_ascii=False,indent=2))
