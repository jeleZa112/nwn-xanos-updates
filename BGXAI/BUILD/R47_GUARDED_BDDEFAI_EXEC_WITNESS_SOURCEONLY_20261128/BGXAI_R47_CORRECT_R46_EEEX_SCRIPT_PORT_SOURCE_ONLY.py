#!/usr/bin/env python3
"""R47 source-only smallest edit: R46 BCS witness uses existing R44-proven API.

Exact original R46 source remains immutable and its native 223-byte always-
false BAF compilation already passed on user EET. Only change R46 witness Lua
from an unverified sprite.getScriptLevelResRef method to the global
EEex_AIBase_GetScriptLevelResRef(actor,4), which the installed R44 uses.

No script install, WeiDU invocation, orders, ARM, inventory action or CMD.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
R46_SOURCE=HERE.parent/"R46_BDDEFAI_EXEC_WITNESS_SOURCEONLY_20261128/BGXAI_R46_INERT_BDDEFAI_WITNESS_SOURCE_ONLY.py"
R46_SOURCE_BLOB="4630b4ab59e45d8fac8ba92068bafa588438415d"
R46_ORIGINAL_LUA_SIZE=2222
R46_ORIGINAL_LUA_SHA="6f6f090c57ad2d3a5dca54ad474c5bb475bb16502c7d0af6ce3ab6fafad396c4"
R46_BAF_SIZE=223
R46_BAF_SHA="af9c78d00dd24806c694e7ee1d6fe882a65b8a9fd71acc90654f60188932a0d9"
SCHEMA="BGXAI_R47_R46_WITNESS_EEEX_VERIFIED_CLASS_API_SOURCE_ONLY_V1"
EXPECTED_LUA_SHA=""  # Filled only after Windows+Ubuntu CI computes exact bytes.

class Hold(ValueError):
    pass

def blob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def original():
    if R46_SOURCE.is_symlink() or not R46_SOURCE.is_file():
        raise Hold("HOLD_ORIGINAL_R46_SOURCE_MISSING_OR_REPARSE")
    data=R46_SOURCE.read_bytes()
    if blob(data)!=R46_SOURCE_BLOB:
        raise Hold("HOLD_PINNED_R46_SOURCE_DRIFT")
    spec=importlib.util.spec_from_file_location("bgxai_verified_r46_inert",R46_SOURCE)
    if spec is None or spec.loader is None:
        raise Hold("HOLD_IMPORT_R46_SOURCE")
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    original=m.compose()
    if len(original["R46_WITNESS_BAF"])!=R46_BAF_SIZE or sha(original["R46_WITNESS_BAF"])!=R46_BAF_SHA:
        raise Hold("HOLD_R46_NATIVE_PROVEN_BAF_DRIFT")
    old=original["R46_WITNESS_LUA"]
    if len(old)!=R46_ORIGINAL_LUA_SIZE or sha(old)!=R46_ORIGINAL_LUA_SHA:
        raise Hold("HOLD_R46_ORIGINAL_LUA_DRIFT")
    return original

def source_only():
    previous=original()
    old=previous["R46_WITNESS_LUA"]
    wrong=b" local getScript=field(actor,'getScriptLevelResRef')\n local assigned=safe(getScript,actor,4)\n"
    correct=(b" local getScript=rawget(_G,'EEex_AIBase_GetScriptLevelResRef')\n"
             b" local assigned=safe(getScript,actor,4)\n")
    if old.count(wrong)!=1 or old.count(correct):
        raise Hold("HOLD_R47_SCRIPT_API_UNIQUE_ANCHOR")
    updated=old.replace(wrong,correct,1)
    if updated.replace(correct,wrong,1)!=old:
        raise Hold("HOLD_R47_NOT_SINGLE_EXACT_CHANGE")
    for marker in (b"return false\n",b"pcall(witness)",b"local seen=false",
                   b"rawget(_G,'EEex_LuaTrigger_Object')",
                   b"field(portrait,'m_id')~=actorID",
                   b"field(stats,'m_nKit')~=16384",
                   b"assigned:upper()~='BDDEFAI'",
                   b"ordersSent=0",b"armAuthorized=false"):
        if updated.count(marker)!=old.count(marker):
            raise Hold("HOLD_R47_SAFETY_MARKER_CHANGED")
    for banned in (b"XEquipItem(",b"SetGlobal(",b"ClearActions(",
                   b"EEex_Action_AddSpriteStartedActionListener(",
                   b"ActionOverride(",b"SelectWeaponAbility("):
        if banned in updated:
            raise Hold("HOLD_R47_ACTION_TOKEN")
    if EXPECTED_LUA_SHA and sha(updated)!=EXPECTED_LUA_SHA:
        raise Hold("HOLD_R47_NEW_LUA_SHA")
    return {"BAF":previous["R46_WITNESS_BAF"],
            "LUA":updated}

def main():
    code=source_only()
    print(json.dumps({"schema":SCHEMA,"status":"R47_CORRECTED_WITNESS_SOURCE_ONLY_NO_INSTALL",
        "originalR46BafUnchangedSha256":sha(code["BAF"]),
        "correctedLuaSha256":sha(code["LUA"]),
        "correctedLuaBytes":len(code["LUA"]),
        "reuseLiveVerifiedEEexGlobalScriptAPI":True,
        "previousNativeBAFCompileProvenByUser":True,
        "R47LuaInstalled":False,"BCSModified":False,"ordersSent":0,
        "armAuthorized":False,"dispatchAuthorized":False},indent=2))
if __name__=="__main__":
    main()
