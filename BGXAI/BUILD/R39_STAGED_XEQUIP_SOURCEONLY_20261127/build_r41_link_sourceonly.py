#!/usr/bin/env python3
"""SOURCE-ONLY R41: embed *unchanged* R39 armer and R40 reset in one Lua M_ file.
Never writes EET files or authorizes/executes a game action.
"""
from pathlib import Path
import hashlib

ROOT=Path(__file__).resolve().parent
R40=ROOT/'M_BGXW3_SESSION_RESET_V1.lua'
ARM=ROOT/'M_BGXW3_EXPLICIT_USER_ARM_SOURCE_ONLY.lua'
OUTPUT=ROOT/'M_BGXW3_R41_LINK_SOURCE_ONLY.lua'
SHA={
 R40.name:'04eb22f926ac47a51eee832f83bb2b6f692f56393e7119e73b7c0335066cb0de',
 ARM.name:'c9333f6dd90cb9f36be3b43aaae778f4c90bcfc90a0e52c296a06b35c50924de',
}
# Pinned hashes above must be refreshed from independently fetched source evidence.
# An unknown/mismatched origin must never be embedded as an approved game module.
def checked(p):
 b=p.read_bytes()
 if len(b)!={'M_BGXW3_SESSION_RESET_V1.lua':4632,
                 'M_BGXW3_EXPLICIT_USER_ARM_SOURCE_ONLY.lua':11427}[p.name]:
  raise ValueError('HOLD_PRIOR_SOURCE_LENGTH:'+p.name)
 if hashlib.sha256(b).hexdigest()!=SHA[p.name]:
  raise ValueError('HOLD_PRIOR_SOURCE_SHA:'+p.name)
 return b.decode('ascii')

# A source-only module with no side effects on load.  The runtime-facing bridge
# is intentionally installed/armed nowhere; all ports require installer proof.
BRIDGE=r'''
local M={schema='BGXAI_R41_SOURCE_ONLY_LINK_R39_R40_V1',sourceOnly=true,
         registered=false,installed=false,ordersSent=0,dispatchAuthorized=false,
         last='SOURCE_ONLY_UNREGISTERED'}
local R40_APPROVAL='ACTIVATE_BGXAI_R40_SESSION_RESET_GUARD'
local R39_APPROVAL='INSTALL_BGXAI_R39_EXPLICIT_GESTURE_WITH_R40_LIVE_GUARD'
local started=false
local function ret(s)
 M.last=s
 return {schema=M.schema,status=s,sourceOnly=true,installed=false,
  armAuthorized=false,dispatchAuthorized=false,ordersSent=0,
  r40Registered=Reset.registered,
  r39Registered=Armer.registered,globalGateBound=started}
end
-- Pre-game install proof is an external, separately authenticated fact.
-- A boolean inserted by this file would not be evidence.
function M.prepare(ports,installerApproval)
 if installerApproval~='BGXAI_R41_GUARDED_TYPED_INSTALL_APPROVED' then
  return ret('HOLD_TYPED_INSTALL_APPROVAL_REQUIRED') end
 if started then return ret('HOLD_ALREADY_STARTED') end
 if rawget(_G,'BGXW3_EEexSessionGate')~=nil then
  return ret('HOLD_GLOBAL_GATE_COLLISION') end
 if type(ports)~='table' or ports.preGameStartupVerified~=true or
    ports.runtimeItemUsabilityVerified~=true or
    ports.runtimeEffectsVerified~=true or
    ports.scriptOwnerVerified~=true or
    ports.manualEpsSafetyVerified~=true or
    type(ports.capture)~='function' or
    type(ports.getPortraitSprite)~='function' or
    type(ports.getLocal)~='function' or
    type(ports.setLocal)~='function' or
    type(ports.addDestroyed)~='function' or
    type(ports.addLoaded)~='function' or
    type(ports.addPressed)~='function' or
    type(ports.keyFromName)~='function' or
    type(ports.isDown)~='function' then
  return ret('HOLD_RUNTIME_PROOFS_OR_PORTS_MISSING') end
 -- R40 lifecycle callbacks must be installed BEFORE a key can ARM an actor.
 local rr=Reset.register({preGameStartupVerified=ports.preGameStartupVerified,
  addDestroyed=ports.addDestroyed,addLoaded=ports.addLoaded,
  getLocal=ports.getLocal,setLocal=ports.setLocal},R40_APPROVAL)
 if rr.status~='RESET_ONLY_LIFECYCLE_HOOKS_REGISTERED_NO_ARM' then
  return ret('HOLD_R40_REGISTER_FAILED') end
 local lastEpoch=Reset.getStatus().sessionEpoch
 local function getEpoch()
  local state=Reset.getStatus()
  if state.status=='NOT_REGISTERED' or type(state.sessionEpoch)~='number' then
   return nil end
  return state.sessionEpoch
 end
 local function proveLifecycle()
  local state=Reset.getStatus()
  return type(state.sessionEpoch)=='number' and state.sessionEpoch>=lastEpoch and
   ports.preGameStartupVerified==true and
   Reset.registered==true
 end
 local ar=Armer.prepare({addPressed=ports.addPressed,
  keyFromName=ports.keyFromName,isDown=ports.isDown,
  getPortraitSprite=ports.getPortraitSprite,
  capture=ports.capture,getLocal=ports.getLocal,setLocal=ports.setLocal,
  proveLifecycle=proveLifecycle,getEpoch=getEpoch,onResult=ports.onResult},R39_APPROVAL)
 if ar.status~='REGISTERED_GESTURE_ONLY_NO_ARM' then
  return ret('HOLD_R39_REGISTER_FAILED_R40_ONLY') end
 local gated=Armer.makeLuaTrigger()
 if type(gated)~='function' then return ret('HOLD_TRIGGER_INVALID_R40_ONLY') end
 local function guarded()
  if not started then return false end
  local ok,allowed=pcall(gated)
  return ok and allowed==true
 end
 -- Final single global write; all prerequisite registrations already succeeded.
 -- No self-ARM, no script start, no engine command in this module.
 if rawget(_G,'BGXW3_EEexSessionGate')~=nil then
  return ret('HOLD_GLOBAL_GATE_CHANGED_R40_ONLY') end
 rawset(_G,'BGXW3_EEexSessionGate',guarded)
 started=true
 M.registered=true
 return ret('R41_BRIDGE_BOUND_GESTURE_ONLY_NO_ARM')
end
function M.getStatus()return ret(M.last)end
function M.getEmbeddedStatus()
 return {r39=Armer.getStatus(),r40=Reset.getStatus(),globalGateBound=started}
end
-- No registration and no global function published at import time.
return M
'''

def render():
 r40=checked(R40)
 arm=checked(ARM)
 return ("-- BGXAI R41 source-only, not installed. Do NOT copy into EET without typed guard.\n"
         "-- Two original immutable modules embedded, not reimplemented.\n"
         "local Reset=(function()\n"+r40+"\nend)()\n"
         "local Armer=(function()\n"+arm+"\nend)()\n"+BRIDGE)

if __name__=='__main__':
 OUTPUT.write_text(render(),encoding='ascii',newline='')
 print('GENERATED',OUTPUT.name,OUTPUT.stat().st_size,hashlib.sha256(OUTPUT.read_bytes()).hexdigest())
