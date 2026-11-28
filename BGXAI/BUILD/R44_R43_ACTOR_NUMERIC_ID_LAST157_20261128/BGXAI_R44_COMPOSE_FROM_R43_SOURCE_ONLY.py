#!/usr/bin/env python3
"""BGXAI R44 source-only: replace ONLY R39 sprite-wrapper comparison in R43.

R43 is already installed on user EET, WeiDU last #156. This produces an
ALTERNATIVE single-listener diagnostic Lua for a separately guarded #157
successor. This script NEVER writes game files, issues an action, or deploys.
Immutable R42/R43 original + immutable R39 source are not modified.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
R43_DIR=REPO/"BGXAI/BUILD/R42_R38_CLASS_BCS_SINGLE_LISTENER_20261128"
R39_DIR=REPO/"BGXAI/BUILD/R39_STAGED_XEQUIP_SOURCEONLY_20261127"
R43_SOURCE=R43_DIR/"BGXAI_R42_CLASS_HOLD_REASON_SOURCE_ONLY.py"
R39_SOURCE=R39_DIR/"BGXAI_R39_ACTOR_ID_GUARD_SOURCE_ONLY.py"
R43_SOURCE_BLOB="2436a29f72f296fdba3ca00b075992f80fea6973"
R39_SOURCE_BLOB="c53ab70223ac697d70ace7a510e657a5b5efa3c6" # verified as tool source on first CI
R43_CANDIDATE_SHA256="8abdc5b1d2088d8c8e2f53b6e4502de5dd0b05225fc6fcca52ebe165253e7ce6"
R39_OLD_BLOB="52bd8751581aa9f9d9ac09559f11a856e81ba1da"
R39_NEW_SHA256="c7b72d75c9d5500907e63ff7eb09c37ec8981a048235b72db266a9d19f0e322a"
R39_NEW_SIZE=13533
R43_SIZE=95965
R44_SIZE=96410
SCHEMA="BGXAI_R44_SINGLE_LISTENER_NUMERIC_ACTOR_ID_SOURCE_ONLY_V1"
STATUS="R44_SOURCE_COMPOSED_NO_INSTALL"

class Hold(ValueError):
    pass

def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()

def blob(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def load(path:Path,pinned_blob:str,name:str):
    if path.is_symlink() or not path.is_file() or blob(path.read_bytes())!=pinned_blob:
        raise Hold("HOLD_PINNED_SOURCE_BLOB:"+name)
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:
        raise Hold("HOLD_SOURCE_MODULE_IMPORT:"+name)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod

def components():
    r43=load(R43_SOURCE,R43_SOURCE_BLOB,"bgxai_r44_verified_r43")
    r39=load(R39_SOURCE,R39_SOURCE_BLOB,"bgxai_r44_verified_r39")
    orig=r43.compose()
    if len(orig)!=R43_SIZE or sha(orig)!=R43_CANDIDATE_SHA256:
        raise Hold("HOLD_R43_LIVE_PREDECESSOR_CANDIDATE_SHA")
    old=r39.verified_original()
    new=r39.compose()
    if blob(old)!=R39_OLD_BLOB or len(new)!=R39_NEW_SIZE or sha(new)!=R39_NEW_SHA256:
        raise Hold("HOLD_R39_EXACT_SOURCE_DIFF")
    return orig,old,new

def patch(original:bytes,old_r39:bytes,corrected_r39:bytes)->bytes:
    if len(original)!=R43_SIZE or sha(original)!=R43_CANDIDATE_SHA256:
        raise Hold("HOLD_R43_CANDIDATE_NOT_PINNED")
    if len(corrected_r39)!=R39_NEW_SIZE or sha(corrected_r39)!=R39_NEW_SHA256:
        raise Hold("HOLD_R39_NEW_SOURCE_NOT_PINNED")
    if original.count(old_r39)!=1 or original.count(corrected_r39)!=0:
        raise Hold("HOLD_R39_EMBEDDED_SOURCE_NOT_EXACTLY_ONCE")
    for marker in (b"[BGXBCS]",b"R27.r42Once=true",
                   b"EEex_Action_AddSpriteStartedActionListener,pilot.listener",
                   b"probeInstalledScriptAssignments()"):
        if original.count(marker)<1:
            raise Hold("HOLD_R43_LISTENER_OR_PROBE_MISSING")
    candidate=original.replace(old_r39,corrected_r39,1)
    if len(candidate)!=R44_SIZE:
        raise Hold("HOLD_R44_CANDIDATE_BYTES_DRIFT")
    if candidate.replace(corrected_r39,old_r39,1)!=original:
        raise Hold("HOLD_R44_NOT_EXACTLY_ONE_SOURCE_REPLACE")
    for marker in (b"[BGXBCS]",b"[BGXR27]",b"[BGXR37]",b"[BGXINV3]",
                   b"[BGXID]",b"R27.r42Once=true",
                   b"EEex_Action_AddSpriteStartedActionListener,pilot.listener",
                   b"probeInstalledScriptAssignments()",
                   b'"actualBcsExecutionVerified":false',
                   b'"dispatchAuthorized":false',
                   b'"armAuthorized":false',b'"ordersSent":0',b'"localsWritten":0'):
        if candidate.count(marker)!=original.count(marker):
            raise Hold("HOLD_R44_EXISTING_LISTENER_OR_SAFETY_MARKER_CHANGED")
    for bad in (b"XEquipItem(",b"SetGlobal(",b"ActionOverride(",
                b"ClearActions(",b"SelectWeaponAbility(",
                b"EEex_Action_AddSpriteStartedActionListener("):
        if candidate.count(bad)!=original.count(bad):
            raise Hold("HOLD_R44_GAMEPLAY_ACTION_OR_LISTENER_CHANGED")
    return candidate

def compose()->bytes:
    return patch(*components())

def main():
    raw=compose()
    print(json.dumps({"schema":SCHEMA,"status":STATUS,
       "r43OriginalSHA256":R43_CANDIDATE_SHA256,
       "r44CandidateBytes":len(raw),"r44CandidateSHA256":sha(raw),
       "oneExistingListenerPreserved":True,
       "patchTouchesOnlyEmbeddedR39":True,"installed":False,
       "gameModified":False,"ordersSent":0,"localsWritten":0,
       "dispatchAuthorized":False,"armAuthorized":False,
       "actualBcsExecutionVerified":False,"manualEpsActionOriginVerified":False,
       "classScriptResrefAtLiveJaganVerified":False,
       "next":"SOURCE_ONLY_TEST_AND_SEPARATE_GUARDED_LAST_ONLY_APPROVAL"},indent=2))

if __name__=="__main__":
    main()
