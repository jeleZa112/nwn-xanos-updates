-- Deterministic EEex 1.1.7 mock for BGXAI 050 PREVIEW; no game required.
local assertions = 0
local function check(v, reason)
    assertions=assertions+1
    assert(v, reason.." (check "..assertions..")")
end
local roster={101,102,103,104}
local sprites={}
local function sprite(id,guard)
  return {m_id=id,guard=guard,m_pos={x=id,y=id+1},m_curAction={m_actionID=134},
    getLocalInt=function(self,name)
      if name~="BGX38_GUARD" then error('Unexpected local') end
      if self.guard=="ERROR" then error('Simulated EEex getLocalInt fault') end
      return self.guard
    end}
end
sprites[101]=sprite(101,1) -- Player1 protagonist should never be assigned under BGX42B
sprites[102]=sprite(102,1) -- Player2 guard ON
sprites[103]=sprite(103,0) -- Player3 victim
sprites[104]=sprite(104,0) -- Player4 guard OFF
local attacker=sprite(999,0)
function EEex_Sprite_GetInPortraitID(i) return roster[i+1] or -1 end
function EEex_GameObject_Get(id) return sprites[id] end
local hook, actionHook
function EEex_Action_AddSpriteStartedActionListener(fn) actionHook=fn end
function EEex_Sprite_AddBlockWeaponHitListener(fn) hook=fn end
assert(dofile(arg[1])==nil) -- Module must only register hooks and return naturally
check(type(hook)=="function","weapon hit listener registered")
check(type(actionHook)=="function","action listener preserved")
check(BGX43Probe.guardDispatchEnabled == false,"never dispatch")
check(BGX43Probe.version=="0.3.21-050-GUARD-ELIGIBILITY-PREVIEW","correct version")
check(hook({attackingSprite=attacker,targetSprite=sprites[103]})==false,"hit never suppressed")
local t=BGX43Probe.snapshot()
check(t.weapon_hit_calls==1,"call count")
check(t.guard_signal_count==1 and #t.guard_signals==1,"recorded one signal")
check(#t.events==1,"confirmed hit remains")
check(t.guard_eligibility_passes==1 and t.guard_eligibility_errors==0,"eligibility pass")
check(t.guard_dispatch_enabled==false,"never dispatch in snapshot")
local q=t.guard_signals[1]
check(q.guard_switch_state=="READ_ONLY_PER_CANDIDATE","reads per candidate")
check(#q.guard_on_candidate_ids==1 and q.guard_on_candidate_ids[1]==102,"only enabled guardian")
check(#q.guard_off_candidate_ids==1 and q.guard_off_candidate_ids[1]==104,"disabled guardian excluded")
check(#q.guard_unknown_candidate_ids==0,"no unknown in known case")
check(#q.excluded_protagonist_ids==1 and q.excluded_protagonist_ids[1]==101,"exclude Player1")
check(q.protected_id==103 and q.attacker_id==999,"correct attacker/victim")
check(q.action_command_sent==false and q.dispatch_status=="DISABLED_PASSIVE_ONLY","advisory only")
check(q.line_of_sight=="UNKNOWN" and q.ability_to_intercept=="UNKNOWN","no invented ability")
check(t.guard_local_reader_available==true,"EEex read API available")
-- Both OFF and missing/bad variable: cannot report ON.
sprites[102].guard=0; sprites[104].guard=nil
check(hook({attackingSprite=attacker,targetSprite=sprites[103]})==false,"second hit never suppressed")
local q2=BGX43Probe.snapshot().guard_signals[2]
check(#q2.guard_on_candidate_ids==0,"no active guardians when switched off")
check(#q2.guard_off_candidate_ids==1 and q2.guard_off_candidate_ids[1]==102,"off retained")
check(#q2.guard_unknown_candidate_ids==1 and q2.guard_unknown_candidate_ids[1]==104,"nil guard is unknown")
-- An EEex local lookup that errors should not synthesize an active guardian.
sprites[102].guard="ERROR"
check(hook({attackingSprite=attacker,targetSprite=sprites[103]})==false,"fault never suppresses hit")
local q3=BGX43Probe.snapshot().guard_signals[3]
check(#q3.guard_on_candidate_ids==0,"fault cannot activate")
check(#q3.guard_unknown_candidate_ids==2,"faults unknown")
check(BGX43Probe.snapshot().guard_signal_errors==0,"lookup fault is isolated")
-- Party actor: do not create an advisory.
check(hook({attackingSprite=sprites[102],targetSprite=sprites[103]})==false,"friendly swing not blocked")
check(BGX43Probe.snapshot().guard_signal_count==3,"no friendly advisory")
-- Nonparty victim: no advisory.
check(hook({attackingSprite=attacker,targetSprite=sprite(555,nil)})==false,"nonparty hit not blocked")
check(BGX43Probe.snapshot().guard_signal_count==3,"no nonparty advisory")
-- Mutating the snapshot must NOT mutate the real advisory.
local snap=BGX43Probe.snapshot()
snap.guard_signals[1].guard_on_candidate_ids[1]=777
check(BGX43Probe.snapshot().guard_signals[1].guard_on_candidate_ids[1]==102,"defensive copy")
-- Bound queue at 64; counts may continue to grow.
sprites[102].guard=1
for i=1,70 do check(hook({attackingSprite=attacker,targetSprite=sprites[103]})==false,"bounded hit callback") end
local capped=BGX43Probe.snapshot()
check(#capped.guard_signals==64,"64 guard advisory ring cap")
check(#capped.events==64,"64 confirmed event ring cap")
check(capped.guard_signal_count==73,"cumulative count")
check(capped.guard_dispatch_enabled==false,"no commands after sustained combat")
print("PASS: "..assertions.." BGXAI 050 Lua runtime checks")
