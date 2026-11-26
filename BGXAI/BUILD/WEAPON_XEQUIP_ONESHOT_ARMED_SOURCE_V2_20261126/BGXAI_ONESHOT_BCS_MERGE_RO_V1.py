#!/usr/bin/env python3
"""Pure source-only merge of one WeiDU-compiled block ahead of an existing BCS.

R29 uses the same SC/CR/CO byte-preserving method. This implementation is
isolated from the game: it writes nothing, installs nothing, authorizes nothing.
"""
from __future__ import annotations
import hashlib,re

SCHEMA="BGXAI_ONESHOT_BCS_PREFIX_MERGE_SOURCE_V1"
class Hold(ValueError):pass
def sha(v:bytes)->str:return hashlib.sha256(v).hexdigest()
def ishash(x):return type(x) is str and re.fullmatch("[0-9a-f]{64}",x) is not None
def split(raw:bytes):
    if type(raw) is not bytes or len(raw)<15 or len(raw)>40_000_000 or not raw.startswith(
        b"SC\nCR\nCO\n") or not raw.endswith(b"CR\nSC\n"):
        raise Hold("HOLD_BAD_BCS_ENVELOPE")
    starts=[m.start(1) for m in re.finditer(rb"(?:^|\n)(CR\nCO\n)",raw)]
    if not starts or starts[0]!=3:raise Hold("HOLD_MISSING_FIRST_CR_CO")
    blocks=[raw[a:b] for a,b in zip(starts,starts[1:]+[len(raw)])]
    if b"SC\n"+b"".join(blocks)!=raw:
        raise Hold("HOLD_NONLOSSLESS_BCS_SPLIT")
    if not 1<=len(blocks)<=10000:raise Hold("HOLD_UNEXPECTED_BLOCK_COUNT")
    return blocks
def compose(old:bytes, pilot:bytes,oldsha:str,pilotsha:str):
    if not ishash(oldsha) or not ishash(pilotsha):
        raise Hold("HOLD_MISSING_EXACT_SOURCE_HASHES")
    if sha(old)!=oldsha or sha(pilot)!=pilotsha:
        raise Hold("HOLD_NATIVE_BCS_BYTES_DRIFT")
    blocks=split(old)
    p=split(pilot)
    if len(p)!=1:raise Hold("HOLD_PILOT_NOT_SINGLE_NATIVE_BCS_BLOCK")
    if p[0] in blocks:raise Hold("HOLD_ALREADY_INJECTED")
    # Identical algorithm to previously installed BGXAI R29:
    # pilot's final 'SC\n' removed, existing complete BCS blocks appended intact.
    result=b"SC\n"+p[0][:-3]+b"".join(blocks)
    got=split(result)
    if len(got)!=len(blocks)+1 or got[1:]!=blocks:
        raise Hold("HOLD_OLD_BCS_BLOCKS_MUTATED")
    # The prefix must preserve EVERY old original block byte-for-byte.
    if not result.endswith(b"".join(blocks)):
        raise Hold("HOLD_SOURCE_NOT_SUFFIX_IDENTICAL")
    return result
def audit(old:bytes,pilot:bytes,oldsha:str,pilotsha:str):
    data=compose(old,pilot,oldsha,pilotsha)
    n=len(split(old))
    return {"schema":SCHEMA,"status":"BINARY_SOURCE_MERGE_PROVEN_NO_GAME_IO",
      "originalSha256":oldsha,"compiledPilotSha256":pilotsha,
      "candidateSha256":sha(data),"candidateBytes":len(data),
      "oldBlocks":n,"newBlocks":n+1,"oldBlocksByteIdentical":True,
      "gameBaselineAuthenticated":False,
      "pilotCompiledAgainstUserEet":False,
      "currentWeiDUComponentLastVerified":False,
      "externalVerifiedBackupCreated":False,
      "weiduInstallPerformed":False,
      "sourceClaimSufficientForDeployment":False,
      "queuedActionPreservationVerified":False,
      "manualEpsOriginVerified":False,
      "liveGameObserved":False,
      "installed":False,"ordersSent":0,"dispatchAuthorized":False}
