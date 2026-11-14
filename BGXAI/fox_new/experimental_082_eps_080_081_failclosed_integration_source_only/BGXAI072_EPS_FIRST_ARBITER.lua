-- BGXAI072 EPS-FIRST arbitration contract, SOURCE ONLY, NOT INSTALLED.
-- Pure Lua: no EEex calls, hooks, BCS commands, attacks or mutation.
-- All inputs are untrusted until separately verified; every output is advisory.
local M={version='0.3.39-072-EPS-FIRST-ARBITER-SOURCE-ONLY',enabled=false}
local function integer(x)
 return type(x)=='number' and x==math.floor(x) and x>0 and x<2147483647
end
local function denied(reason)
 return {state='HOLD',reason=reason,allow_engine_action=false,
         confirmed_target_id=nil,engine_orders_sent=0,script_changes=0}
end
function M.review(role,threat,eps,proposed,config)
 -- Explicit operator-mode opt-in is not an installation or game command.
 if type(config)~='table' or config.opt_in~=true or config.smart_guard~=true then
  return denied('OPT_IN_OFF')
 end
 if type(role)~='table' or role.status~='ADVISORY_ONLY' or
    role.possible_interceptor~=true or role.orders_sent~=0 or
    role.guard_toggle~=1 then return denied('ROLE_UNVERIFIED_OR_F_OFF') end
 if type(threat)~='table' or threat.verified~=true or
    threat.source~='EEEX_EXPLICIT_ATTACK_ACTION' or
    threat.hostile~=true or threat.victim_is_party~=true or
    threat.attacker_is_party~=false or threat.same_area~=true or
    threat.attack_in_progress~=true or
    not integer(threat.attacker_id) or not integer(threat.victim_id) or
    threat.attacker_id==threat.victim_id then return denied('REAL_ATTACKER_NOT_PROVED') end
 if type(eps)~='table' or eps.verified~=true then return denied('EPS_STATE_UNKNOWN') end
 if eps.manual_command~=false then return denied('MANUAL_COMMAND_FIRST') end
 if eps.heal_pending~=false or eps.ally_in_critical_danger~=false then
  return denied('LIFE_SAVING_HEAL_FIRST') end
 if eps.casting~=false then return denied('SPELL_IN_PROGRESS') end
 if eps.singing~=false then return denied('BARD_SONG_IN_PROGRESS') end
 if eps.detecting_traps~=false then return denied('TRAP_DETECTION_IN_PROGRESS') end
 if eps.queue_empty~=true or eps.idle~=true then return denied('EPS_ACTION_QUEUE_BUSY_OR_UNKNOWN') end
 -- 067 currently uses NearestEnemyOf(PlayerN) and cannot prove identity.
 -- Never upgrade a nearest-enemy guess into a confirmed hit attacker.
 if type(proposed)~='table' or proposed.verified~=true or
    proposed.target_source~='EXACT_RESOLVED_ATTACKER_ID' or
    not integer(proposed.target_id) or proposed.target_id~=threat.attacker_id then
  return denied('BCS_TARGET_NOT_EXACT_ATTACKER') end
 return {state='CANDIDATE_REVIEW_ONLY',reason='NO_ENGINE_DISPATCH_IMPLEMENTED',
         allow_engine_action=false,confirmed_target_id=threat.attacker_id,
         engine_orders_sent=0,script_changes=0}
end
return M
