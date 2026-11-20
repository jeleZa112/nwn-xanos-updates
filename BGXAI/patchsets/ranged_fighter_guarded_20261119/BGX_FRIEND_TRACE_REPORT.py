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
def _audit_trace(root:Path):
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


def startup_diagnostics(root:Path):
    """Read-only, bounded EEex Lua configuration and startup log evidence."""
    import os
    ini=root/"InfinityLoader.ini"
    result={"status":"EEEX_STARTUP_DIAG_READONLY",
            "ini_path":str(ini),
            "ini_present":False,
            "lua_patch_mode":"UNKNOWN",
            "lua_io_available":"UNKNOWN",
            "log_file_setting":"UNKNOWN",
            "observer_override_present":False,
            "observer_override_sha256":None,
            "startup_logs":[],"startup_errors":[],"game_modified":False}
    if not ini.is_symlink() and ini.is_file():
        try:
            data=ini.read_bytes()[:262144].decode("utf-8-sig","replace")
            result["ini_present"]=True
            for line in data.splitlines():
                if line.lstrip().startswith(("#",";")):continue
                item=re.match(r"\s*(LuaPatchMode|LogFile)\s*=\s*(.*?)\s*(?:[;#].*)?$",line,re.I)
                if not item:continue
                key=item.group(1).lower();value=item.group(2).strip()
                if key=="luapatchmode":result["lua_patch_mode"]=value[:120]
                elif key=="logfile":result["log_file_setting"]=value[:120]
            mode=result["lua_patch_mode"].upper()
            if mode in ("INTERNAL","USE_INTERNAL","NONE","OFF"):
                result["lua_io_available"]="LIKELY_UNAVAILABLE_IN_INTERNAL_LUA"
            elif ("LUAJIT" in mode or "EXTERNAL" in mode):
                result["lua_io_available"]="POSSIBLE_NEEDS_RUNTIME_VERIFICATION"
        except OSError as exc:
            result["startup_errors"].append("INFINITYLOADER_INI_READ_ERROR:"+str(exc)[:120])
    observer=root/"override"/"M_BXFR.lua"
    if not observer.is_symlink() and observer.is_file():
        try:
            info=observer.stat()
            if info.st_size<=1_000_000:
                result["observer_override_present"]=True
                result["observer_override_sha256"]=hashlib.sha256(observer.read_bytes()).hexdigest()
        except OSError:
            pass
    possible=[
        root/"InfinityLoader.txt",root/"InfinityLoader.log",
        root/"EEex.log",root/"Baldur.err",root/"InfinityLoader_Crash.log",
        root/"override"/LOG_NAME,root/"override"/"EEex.log"]
    # Only a trusted plain filename from the INI may add one local log path.
    filename=result["log_file_setting"]
    if filename!="UNKNOWN" and re.fullmatch(r"[A-Za-z0-9_. -]{1,90}",filename):
        possible.append(root/filename)
    dedup=set()
    for candidate in possible:
        key=str(candidate).lower()
        if key in dedup:continue
        dedup.add(key)
        if candidate.is_symlink() or not candidate.is_file():continue
        try:
            st=candidate.stat()
            if st.st_size>150_000_000:continue
            with candidate.open("rb") as stream:
                start=max(0,st.st_size-1_500_000)
                stream.seek(start)
                payload=stream.read(1_500_000).decode("utf-8","replace")
            evidence=[]
            for line in payload.splitlines():
                if re.search(r"(?i)M_BXFR|BGXFTRACE|LuaPatchMode|LuaJIT|(?:^|[^a-z])io\.open|lua.*(?:error|failed|missing|disabled)|(?:error|failed).*lua",line):
                    evidence.append(line.strip()[:230])
            result["startup_logs"].append({"path":str(candidate),"bytes":st.st_size,
                "modified_utc":datetime.datetime.fromtimestamp(st.st_mtime,datetime.timezone.utc).isoformat(),
                "relevant_lines":evidence[-22:]})
        except (OSError,UnicodeError) as exc:
            result["startup_errors"].append("STARTUP_LOG_SCAN_ERROR:"+str(exc)[:160])
    if not result["observer_override_present"]:
        result["hypothesis"]="OBSERVER_OVERRIDE_NOT_FOUND"
    elif result["lua_io_available"]=="LIKELY_UNAVAILABLE_IN_INTERNAL_LUA":
        result["hypothesis"]="NO_LUA_IO_POSSIBLE; VERIFY_EEEX_LUAJIT_COMPONENT"
    elif not result["startup_logs"]:
        result["hypothesis"]="NO_USABLE_STARTUP_LOG; RUNTIME_HOOK_AND_CWD_UNKNOWN"
    else:
        result["hypothesis"]="STARTUP_LOG_EVIDENCE_AVAILABLE; INSPECT_MATCHED_LINES"
    return result


def audit(root:Path):
    result=_audit_trace(root)
    result["startup_diagnostics"]=startup_diagnostics(root)
    return result
