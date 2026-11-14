-- 073 SOURCE ONLY. Passive cross-module evaluation; no engine command pathway.
local R=dofile('BGXAI069_ROLE_OBSERVER.lua')
local E=dofile('BGXAI070_EEEX_FACTS_READONLY.lua')
local K=dofile('BGXAI071_KIT_HINTS_READONLY.lua')
local A=dofile('BGXAI072_EPS_FIRST_ARBITER.lua')
local M={version='BGXAI-073-SOURCE-ONLY',orders_sent=0}
function M.inspect(sprite, threat, eps, proposal, config)
 local snap=E.snapshot(sprite)
 local kit=K.hint(snap)
 local role=R.inspect(sprite,E.facts_for_069(snap))
 local arbitration=A.review(role,threat,eps,proposal,config)
 return {snapshot=snap,kit_hint=kit,role=role,arbitration=arbitration,
         engine_orders_sent=0,game_changes=0,diagnostic_only=true}
end
return M
