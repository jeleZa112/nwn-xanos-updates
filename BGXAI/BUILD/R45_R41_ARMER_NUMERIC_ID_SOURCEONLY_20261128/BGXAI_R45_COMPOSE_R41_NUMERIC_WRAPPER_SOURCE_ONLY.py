#!/usr/bin/env python3
"""BGXAI R45 source-only risk reduction for the ALREADY-WRITTEN R39/R41 armer.

First real user R44 captured CLASS=BDDEFAI via numeric m_id. This module
reuses (does not edit) the ORIGINAL R39 explicit-hotkey arm and R41 lifecycle
wrapper. Both contain direct Lua sprite-wrapper comparisons, which can falsely
deny the same actor even when EEex's numeric m_id matches.

Creates an ALTERNATIVE inactive R41 source: no new listener registration,
no auto-arm, no BAF installation, no game writes, no orders, no new updater.
Before any live equip, separate required port proofs and user approval remain.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ORIGIN=HERE.parent/"R39_STAGED_XEQUIP_SOURCEONLY_20261127"
AR=ORIGIN/"M_BGXW3_EXPLICIT_USER_ARM_SOURCE_ONLY.lua"
R41=ORIGIN/"M_BGXW3_R41_LINK_SOURCE_ONLY.lua"
AR_BLOB="dab140035652bcf66b7f150ad72b0ec5f9ae1453"
R41_BLOB="8d64a67b013c6c42352835c5a51706d5075522a4"
SCHEMA="BGXAI_R45_R39_R41_NUMERIC_ACTOR_WRAPPER_SOURCE_ONLY_V1"
STATUS="SOURCE_ONLY_NO_INSTALL"

class Hold(ValueError):
    pass

def blob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def verified(path:Path,expected:str)->bytes:
    if path.is_symlink() or not path.is_file():
        raise Hold("HOLD_ORIGINAL_SOURCE_NOT_REGULAR:"+path.name)
    raw=path.read_bytes()
    if blob(raw)!=expected:
        raise Hold("HOLD_PINNED_ORIGINAL_SOURCE_DRIFT:"+path.name)
    return raw

def repl_exact(raw:bytes,old:bytes,new:bytes,label:str)->bytes:
    if raw.count(old)!=1 or raw.count(new)!=0:
        raise Hold("HOLD_UNIQUE_PATCH_ANCHOR:"+label)
    return raw.replace(old,new,1)

ID_FUNCTION=b"""local function sameNumericActor(sprite,id)
 if sprite==nil or not validInt(id,1,2147483647) then return false end
 local ok,n=pcall(function() return sprite.m_id end)
 return ok and validInt(n,1,2147483647) and n==id
end
"""

def patch_armer(ar:bytes)->bytes:
    if blob(ar)!=AR_BLOB:
        raise Hold("HOLD_AR_SOURCE_BLOB")
    out=repl_exact(ar,
        b"local function ret(status)\n",
        ID_FUNCTION+b"local function ret(status)\n","AR_NUMERIC_ACTOR_HELPER")
    out=repl_exact(out,
        b"    state.volatileSprite~=aiBase then return false end",
        b"    not sameNumericActor(state.volatileSprite,state.volatileActorId) or\n"
        b"    not sameNumericActor(aiBase,state.volatileActorId) then return false end",
        "AR_SAVED_WRAPPER")
    out=repl_exact(out,
        b" if not ok or portraitSprite~=aiBase then return false end",
        b" if not ok or not sameNumericActor(portraitSprite,state.volatileActorId) then return false end",
        "AR_PORTRAIT_WRAPPER")
    out=repl_exact(out,
        b" if postEpoch~=epoch or not ok2 or postPortrait~=aiBase or",
        b" if postEpoch~=epoch or not ok2 or\n"
        b"    not sameNumericActor(postPortrait,state.volatileActorId) or",
        "AR_POST_PORTRAIT_WRAPPER")
    if b"~=aiBase" in out:
        raise Hold("HOLD_REMAINING_AR_POINTER_EQ")
    return out

R41_ID_FUNCTION=b"""local function sameLoadedActorId(a,b)
 if a==nil or b==nil then return false end
 local oka,ida=pcall(function() return a.m_id end)
 local okb,idb=pcall(function() return b.m_id end)
 return oka and okb and type(ida)=='number' and type(idb)=='number' and
        ida==ida and idb==idb and ida%1==0 and idb%1==0 and
        ida>=1 and idb>=1 and ida<=2147483647 and idb<=2147483647 and ida==idb
end
"""

def patch_r41(r41:bytes,ar:bytes,corrected:bytes)->bytes:
    if blob(r41)!=R41_BLOB:
        raise Hold("HOLD_R41_SOURCE_BLOB")
    out=repl_exact(r41,ar,corrected,"R41_ONE_EMBEDDED_R39_AR")
    out=repl_exact(out,
        b"local function goodResetStatus(s)\n",
        R41_ID_FUNCTION+b"local function goodResetStatus(s)\n",
        "R41_ID_HELPER")
    out=repl_exact(out,
        b"  return current~=nil and current==verifiedLoadedSprite",
        b"  return sameLoadedActorId(current,verifiedLoadedSprite)",
        "R41_LOADED_EPOCH_ACTOR")
    out=repl_exact(out,
        b"   if sprite~=nil and sprite==current and goodResetStatus(s.status) then",
        b"   if sameLoadedActorId(sprite,current) and goodResetStatus(s.status) then",
        "R41_LOAD_CALLBACK_ACTOR")
    return out

def compose()->bytes:
    ar=verified(AR,AR_BLOB)
    old=verified(R41,R41_BLOB)
    new=patch_r41(old,ar,patch_armer(ar))
    for marker in (b"return M\n",b"EXPLICIT_GESTURE_ARMED_ONCE_BAF_WILL_RECHECK",
                   b"BGXW3_EEexSessionGate",b"HOLD_SESSION_RESET_ORDER_UNPROVEN",
                   b"HOLD_RUNTIME_PROOFS_OR_PORTS_MISSING",
                   b"PENDING_ARM_CLEARED_ON_SPRITE_LOAD"):
        if new.count(marker)!=old.count(marker):
            raise Hold("HOLD_R45_SEMANTIC_OR_GLOBAL_MARKER_CHANGED")
    for marker in (b"XEquipItem(",b"SetGlobal(",b"ActionOverride(",
                   b"EEex_Action_AddSpriteStartedActionListener(",
                   b"EEex_GameState_AddDestroyedListener("):
        if new.count(marker)!=old.count(marker):
            raise Hold("HOLD_R45_ACTION_OR_LISTENER_BOUNDARY_CHANGED")
    if b"return M" not in new:
        raise Hold("HOLD_R45_NO_SOURCE_MODULE")
    return new

def main():
    raw=compose()
    print(json.dumps({"schema":SCHEMA,"status":STATUS,
      "r41OriginalGitBlob":R41_BLOB,
      "r39OriginalArmerGitBlob":AR_BLOB,
      "alternativeSourceBytes":len(raw),
      "alternativeSourceSHA256":hashlib.sha256(raw).hexdigest(),
      "r39AndR41NumericActorGuards":True,
      "sameOriginalR40AndOneHotkey":True,
      "gameModified":False,"installed":False,"ordersSent":0,
      "dispatchAuthorized":False,"armAuthorized":False,
      "next":"REQUIRES_SEPARATE_SAFETY_PORT_PROOFS_BCS_EXECUTION_AND_TYPED_APPROVAL_BEFORE_FIRST_LIVE_XEQUIP"},indent=2))

if __name__=="__main__":
    main()
