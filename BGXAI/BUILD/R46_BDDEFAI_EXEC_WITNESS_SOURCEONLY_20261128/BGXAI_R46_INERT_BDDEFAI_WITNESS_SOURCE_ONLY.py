#!/usr/bin/env python3
"""BGXAI R46: SOURCE-ONLY inert BCS-execution witness for assigned BDDEFAI.

This does not install, write EET, run WeiDU, register a listener, or arm
equipment. A future guarded last-only WeiDU #158 could EXTEND_TOP a compiled
BAF whose one Lua trigger ALWAYS RETURNS FALSE. It therefore cannot execute
the RESPONSE or interfere with an attack round. It proves BCS *evaluation*
only; no manual/EPS origin, effects, XEquip, or permission to arm is claimed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
R39=HERE.parent/"R39_STAGED_XEQUIP_SOURCEONLY_20261127"
R39_BAF=R39/"BGXAI_R39_JAGAN_STAF01_EEEX_SESSION_SOURCE_ONLY.baf"
R39_BAF_BLOB="3d2816b2ba459b1d212f79bce74d925033691303"
SCHEMA="BGXAI_R46_BDDEFAI_EXEC_WITNESS_SOURCE_ONLY_V1"
FUNC="BGXAI_R46_BDDEFAI_Witness"
BAF=(r'''// BGXAI R46 SOURCE ONLY, NOT INSTALLED; inert BCS-execution witness.
IF
  InParty(Myself)
  InPartySlot(Myself,1)
  EEex_LuaTrigger("pcall(BGXAI_R46_BDDEFAI_Witness); return false")
THEN
  RESPONSE #100
    Continue()
END
''').encode("ascii")
TP2=(r'''BACKUP ~BGXR46/backup~
AUTHOR ~BGXAI R46 inert BCS witness source only~
BEGIN ~BGXR46 BDDEFAI read-only evaluation witness (NO EQUIP/ARM)~
COPY ~BGXR46/staged/M_BGXR46_WITNESS.lua~ ~override/M_BGXR46_WITNESS.lua~
EXTEND_TOP ~BDDEFAI.BCS~ ~BGXR46/staged/BGX_R46_WITNESS.baf~
''').encode("ascii")
LUA=(r'''-- BGXAI R46 passive BCS evaluation witness; no actions, no LOCALS,
-- no hotkey, no action listeners, and no equipment modification.
local M={schema='BGXAI_R46_BDDEFAI_EXEC_WITNESS_RO_V1',
         readOnly=true,ordersSent=0,registered=false}
local seen=false
local NAME='BGXAI_R46_BDDEFAI_Witness'
local function integer(x)
 return type(x)=='number' and x==x and x%1==0 and
        x>=1 and x<=2147483647
end
local function field(a,k)
 if a==nil then return nil end
 local ok,x=pcall(function()return a[k] end)
 return ok and x or nil
end
local function safe(f,...)
 if type(f)~='function' then return nil end
 local ok,x=pcall(f,...)
 return ok and x or nil
end
local function witness()
 if seen then return end
 local actor=rawget(_G,'EEex_LuaTrigger_Object')
 if actor==nil then return end
 local actorID=field(actor,'m_id')
 if not integer(actorID) then return end
 local portrait=safe(rawget(_G,'EEex_Sprite_GetInPortrait'),1)
 local portraitID=safe(rawget(_G,'EEex_Sprite_GetInPortraitID'),1)
 if not integer(portraitID) or portrait==nil or
    field(portrait,'m_id')~=actorID or portraitID~=actorID then return end
 if field(field(actor,'m_typeAI'),'m_Class')~=3 then return end
 local stats=safe(field(actor,'getActiveStats'),actor)
 if not stats or field(stats,'m_nKit')~=16384 then return end
 local getScript=field(actor,'getScriptLevelResRef')
 local assigned=safe(getScript,actor,4)
 if type(assigned)~='string' or assigned:upper()~='BDDEFAI' then return end
 seen=true
 print('[BGXBEX] R46_BDDEFAI_CLASS_TRIGGER_EVALUATED_JAGAN_READONLY'
       ..' scrlev=4 class=BDDEFAI partyIndex=1'
       ..' witnessBlockEvaluated=true actionOriginVerified=false'
       ..' ordersSent=0 armAuthorized=false')
end
local function bridge()
 -- Even if witness errors, its BAF trigger MUST always evaluate FALSE.
 pcall(witness)
 return false
end
-- Explicit namespace collision fail closed: do not overwrite unknown globals.
if rawget(_G,NAME)==nil then
 rawset(_G,NAME,bridge)
 M.registered=true
end
function M.inspect()
 return {schema=M.schema,readOnly=true,globalBridgeRegistered=M.registered,
         witnessOnce=seen,ordersSent=0,armAuthorized=false,
         actualBCSActionExecutionVerified=false}
end
return M
''').encode("ascii")

def git_blob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def verified_prior()->bytes:
    if R39_BAF.is_symlink() or not R39_BAF.is_file():
        raise ValueError("HOLD_ORIGINAL_R39_BAF_NOT_REGULAR")
    raw=R39_BAF.read_bytes()
    if git_blob(raw)!=R39_BAF_BLOB:
        raise ValueError("HOLD_R39_BAF_SOURCE_GIT_BLOB_DRIFT")
    if raw.count(b'XEquipItem("STAF01"')!=1 or raw.count(b'EEex_LuaTrigger(')!=2:
        raise ValueError("HOLD_R39_BAF_PREVIOUS_NATIVE_CONTRACT")
    return raw

def compose()->dict[str,bytes]:
    orig=verified_prior()
    if (BAF.count(b"EEex_LuaTrigger(")!=1
        or BAF.count(b"Continue()")!=1
        or BAF.count(b"XEquipItem(")!=0
        or BAF.count(b"SetGlobal(")!=0
        or BAF.count(b"IF\n")!=1):
        raise ValueError("HOLD_INERT_BAF_POLICY")
    for danger in (b"XEquipItem(",b"SetGlobal(",b"SelectWeaponAbility(",
                   b"ActionOverride(",b"EEex_Action_AddSpriteStartedActionListener("):
        if danger in BAF or danger in LUA or danger in TP2:
            raise ValueError("HOLD_WITNESS_ISSUES_GAME_ORDER")
    if not re.search(rb"local function bridge\(\)\s*--[^\n]*\n\s*pcall\(witness\)\s*return false\s*end",LUA):
        raise ValueError("HOLD_WITNESS_MUST_ALWAYS_RETURN_FALSE")
    if LUA.count(b"print('[BGXBEX]")!=1:
        raise ValueError("HOLD_WITNESS_SINGLE_LOG_SITE")
    if TP2.count(b"EXTEND_TOP ~BDDEFAI.BCS~")!=1:
        raise ValueError("HOLD_BCS_TARGET_NOT_EXACT")
    if b"BGXAI_R39_JAGAN_STAF01" in TP2 or orig in BAF:
        raise ValueError("HOLD_MUST_NOT_INSTALL_TRANSFER_BAF")
    return {"R46_WITNESS_BAF":BAF,
            "R46_WITNESS_LUA":LUA,
            "R46_WEIDU_BLUEPRINT_SOURCE_ONLY":TP2}

def main():
    source=compose()
    print(json.dumps({"schema":SCHEMA,"status":"R46_SOURCE_ONLY_NOT_INSTALLED",
      "sourceComponents":{
        key:{"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}
        for key,raw in source.items()},
      "nextIfGuarded":"EXACT_LAST157_NATIVE_COMPILE_AND_PREVIOUS_BDDEFAI_BCS_HASH_REQUIRED",
      "sourceR39BafReusedNotInstalled":True,
      "newActionStartListeners":0,
      "gameModified":False,"installed":False,"armAuthorized":False,
      "dispatchAuthorized":False,"ordersSent":0,
      "actualBcsWitnessBlockEvaluatedLive":False,
      "liveXEquipItemPerformed":False},indent=2))

if __name__=="__main__":
    main()
