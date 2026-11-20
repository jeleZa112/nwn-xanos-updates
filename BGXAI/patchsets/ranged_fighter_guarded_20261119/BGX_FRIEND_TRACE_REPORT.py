#!/usr/bin/env python3
"""Read only BGXFTRACE log analyser. Never infer script/engine causality."""
from __future__ import annotations
import datetime
import hashlib
from pathlib import Path
import re

LOG_NAME="BGXAI_FRIENDLY_ACTION_TRACE.log"
LOG_CAP=4_194_304
PATTERN=re.compile(
    r"^\[BGXFTRACE\] ACTION seq=(\d+) actor=(\d+) slot=([1-6]) action=(\d+) "
    r"a1=(-?\d+) a2=(-?\d+) target=(-?\d+) target_slot=(-?\d+) "
    r"script=(-?\d+) status=(PARTY_TARGET_OBSERVED|TARGET_NOT_CONFIRMED_PARTY) origin=UNKNOWN$")
ATTACKS={3,94,98,105,134}
def audit(root:Path):
    p=root/LOG_NAME
    if p.is_symlink():return {"status":"TRACE_SYMLINK_BLOCKED","game_modified":False}
    if not p.is_file():return {"status":"TRACE_NOT_PRESENT","runtime_origin":"UNKNOWN","game_modified":False}
    try:
        stat=p.stat()
        with p.open("rb") as f:
            start=max(0,stat.st_size-LOG_CAP)
            if start:f.seek(start)
            raw=f.read(LOG_CAP)
        if start:
            i=raw.find(b"\n")
            raw=raw[i+1:] if i>=0 else b""
    except OSError as exc:
        return {"status":"TRACE_READ_ERROR","error":str(exc)[:200],"game_modified":False}
    actions=[]
    sessions=0
    ready=False
    warnings=[]
    for line in raw.decode("utf-8","replace").splitlines():
        if line.startswith("[BGXFTRACE] SESSION "):
            sessions+=1;actions=[];ready=False
        elif line.startswith("[BGXFTRACE] READY "):
            ready=True
        elif line.startswith("[BGXFTRACE] STOP "):
            warnings.append(line[:180])
        else:
            m=PATTERN.match(line)
            if not m:continue
            seq,actor,actor_slot,action,a1,a2,target,target_slot,script=(int(v) for v in m.groups()[:9])
            label=m.group(10)
            if action not in ATTACKS:continue
            valid=label=="PARTY_TARGET_OBSERVED" and 1<=target_slot<=6 and target>=0 and target!=actor
            actions.append({"sequence":seq,"actor_id":actor,"actor_slot":actor_slot,
                "action_id":action,"actee1":a1,"actee2":a2,
                "observed_target_id":target,"observed_target_slot":target_slot,
                "script_index_observed":script if script>=0 else None,
                "target_pair_observed":valid,"action_origin":"UNKNOWN"})
            if len(actions)>400:actions.pop(0)
    observed=[a for a in actions if a["target_pair_observed"]]
    return {"status":("TRACE_ACTIONS_OBSERVED" if actions else
               "TRACE_READY_NO_MATCHING_ACTIONS" if ready else "TRACE_UNVERIFIED_OR_EMPTY"),
        "last_session_ready":ready,"sessions_seen":sessions,
        "log_size":stat.st_size,
        "log_modified_utc":datetime.datetime.fromtimestamp(stat.st_mtime,datetime.timezone.utc).isoformat(),
        "tail_sha256":hashlib.sha256(raw).hexdigest(),"tail_truncated":start>0,
        "attack_action_records":len(actions),"party_target_attack_records":len(observed),
        "observed_party_target_pairs":observed[-30:],"last_attack_records":actions[-50:],
        "warnings":warnings[-5:],"runtime_origin":"UNKNOWN",
        "no_observation_means_safe":False,"game_modified":False}
