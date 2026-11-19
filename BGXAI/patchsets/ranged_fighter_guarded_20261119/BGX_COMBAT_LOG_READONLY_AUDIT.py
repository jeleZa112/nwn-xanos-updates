#!/usr/bin/env python3
"""Read-only BGXAI_COMBAT.log action-start evidence parser.

Only observed BGX71 ACTION entries with concrete actor/target entity IDs can
establish an observed action-start pair; NEVER infer manual/EPS/BGXAI origin.
The log may be absent, old, or contain only legacy lines without target IDs.
"""
from __future__ import annotations
import datetime
import hashlib
import os
from pathlib import Path
import re

LOG_MAX=8_388_608
RECENT_ACTIONS=160
RE_BGX71=re.compile(
 r"\[BGX71\]\s+ACTION_(\d+)\s+actor=(A\d+)\s+id=(-?\d+)\s+slot=([1-6])\s+"
 r"action=(-?\d+)\s+pos=\((-?\d+),(-?\d+)\)\s+dest=\((-?\d+),(-?\d+)\)\s+target=(-?\d+)")
RE_ROSTER=re.compile(r"\[BGX71\]\s+ROSTER\s+epoch=(\d+)\s+size=([1-6])\b")
RE_LEGACY=re.compile(r"\[BGXAI\]\s+ACTION_(\d+)\s+name=(.*?)\s+id=(\S+)\s+action=(-?\d+)\b")
ATTACK_FAMILY={3,94,98,105,134}
def report(root):
    p=root/"BGXAI_COMBAT.log"
    if p.is_symlink():
        return {"status":"LOG_SYMLINK_BLOCKED","game_modified":False}
    if not p.is_file():
        return {"status":"NO_EXISTING_COMBAT_LOG","runtime_action_origin":"UNKNOWN",
                "game_modified":False}
    try:
        stat=p.stat()
        start=max(0,stat.st_size-LOG_MAX)
        with p.open("rb") as f:
            if start:f.seek(start)
            chunk=f.read(LOG_MAX)
        # A leading truncated line would be invalid; do not parse it.
        if start:
            first=chunk.find(b"\n")
            chunk=chunk[first+1:] if first>=0 else b""
        payload=chunk.decode("utf-8","replace")
    except OSError as e:
        return {"status":"COMBAT_LOG_READ_STOP","reason":str(e)[:300],
                "runtime_action_origin":"UNKNOWN","game_modified":False}
    epochs=0
    slot_to_entity={}
    events=[]
    legacy=0
    total=0
    for line in payload.splitlines():
        r=RE_ROSTER.search(line)
        if r:
            epochs+=1
            slot_to_entity={}
            events=[]
        m=RE_BGX71.search(line)
        if m:
            total+=1
            seq,label,actor,slot,action,target=(int(m.group(1)),m.group(2),
                     int(m.group(3)),int(m.group(4)),int(m.group(5)),
                     int(m.group(10)))
            if actor>=0:
                slot_to_entity[slot]=actor
            events.append({"sequence":seq,"actor_label":label,"actor_id":actor,
                           "actor_slot":slot,"action_id":action,"target_id":target,
                           "script_origin":"UNKNOWN"})
            if len(events)>RECENT_ACTIONS:events.pop(0)
        elif RE_LEGACY.search(line):
            legacy+=1
    party_ids={v:k for k,v in slot_to_entity.items() if v>=0}
    observed=[]
    for ev in events:
        dest=ev["target_id"]
        if (ev["action_id"] in ATTACK_FAMILY and ev["actor_id"] in party_ids
            and dest in party_ids and dest!=ev["actor_id"]):
            observed.append({"sequence":ev["sequence"],"actor_id":ev["actor_id"],
                "actor_slot":party_ids[ev["actor_id"]],"target_id":dest,
                "target_slot":party_ids[dest],"action_id":ev["action_id"],
                "status":"PARTY_TO_PARTY_ATTACK_ACTION_STARTED_OBSERVED",
                "action_origin":"UNKNOWN"})
    for ev in events:
        if ev["target_id"] in party_ids:
            ev["target_slot_if_observed"]=party_ids[ev["target_id"]]
    result={"status":"COMBAT_LOG_SCANNED","log_sha256_observed_tail":hashlib.sha256(chunk).hexdigest(),
            "log_bytes":stat.st_size,
            "log_modified_utc":datetime.datetime.fromtimestamp(stat.st_mtime,
                tz=datetime.timezone.utc).isoformat(),
            "tail_truncated":start>0,
            "bgx71_roster_events":epochs,
            "bgx71_actions_in_tail":total,
            "legacy_actions_without_known_target_id":legacy,
            "distinct_observed_party_slots":len(slot_to_entity),
            "observed_party_attack_starts":observed[-25:],
            "last_action_starts":events[-50:],
            "runtime_action_origin":"UNKNOWN",
            "source_coverage":"BGX71_ACTIONS_ONLY_NOT_ALL_ENGINE_ACTIONS",
            "proof_of_absence":False,
            "game_modified":False}
    if not total:
        result["status"]="NO_BGX71_TARGET_BEARING_EVENTS"
    elif not epochs:
        result["status"]="BGX71_ROSTER_NOT_OBSERVED_TARGET_MEMBERSHIP_UNVERIFIED"
        result["observed_party_attack_starts"]=[]
    return result
