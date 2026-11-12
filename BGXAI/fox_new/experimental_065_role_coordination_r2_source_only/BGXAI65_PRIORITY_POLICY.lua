-- BGXAI 065 SOURCE ONLY / PASSIVE POLICY. Never modifies game objects or issues AI orders.
-- Priority is meaningful when MULTIPLE allies are threatened; on a single hit the
-- BGXAI 064 baseline still protects the actual hit victim.
-- Class integers: BGEE CLASS.IDS; sprite fields use EEex x64 names.
BGX65Policy = BGX65Policy or {}
local P = BGX65Policy
P.version = '0.3.31-065-PRIORITY-OBSERVER-SOURCE-ONLY'
P.isInstalled = false
P.dispatchEnabled = false
P.observed = P.observed or {}
P.lastPlan = nil
P.observationCount = 0
P.errors = 0
local MAX_THREATS = 12
local TICK_WINDOW = 45 -- only for observations, never engine timers
local ARCANE = {[1]=true,[5]=true,[7]=true,[10]=true,[13]=true,[14]=true,[17]=true,[19]=true}
local HEALER = {[3]=true,[8]=true,[11]=true,[14]=true,[15]=true,[16]=true,[17]=true,[18]=true}
local TANK = {[2]=true,[6]=true,[12]=true,[20]=true}
local function validid(x) return type(x)=='number' and x==math.floor(x) and x>=0 and x<=2147483647 end
local function number(x) return type(x)=='number' and x==x and x>-1e9 and x<1e9 end
local function safe(fn) local ok,res=pcall(fn); if ok then return res end; return nil end
local function validArea(equal, a,b)
  if type(equal)~='function' or a==nil or b==nil then return false end
  return safe(function() return equal(a,b) end)==true
end
function P.classRole(classID)
  if type(classID)~='number' or classID~=math.floor(classID) then return 'unknown' end
  if HEALER[classID] and ARCANE[classID] then return 'arcane_healer' end
  if HEALER[classID] then return 'healer' end
  if ARCANE[classID] then return 'arcane' end
  if TANK[classID] then return 'tank' end
  if classID==4 or classID==9 then return 'rogue' end
  return 'other'
end
function P.urgency(member)
  if type(member)~='table' then return nil end
  local hp,maxhp=member.hp,member.maxhp
  if hp~=nil and (not number(hp) or hp<0) then return nil end
  if maxhp~=nil and (not number(maxhp) or maxhp<=0) then maxhp=nil end
  if number(hp) and hp==0 then return nil end -- incapacitated or dead: do not queue attack escort
  local pct = number(hp) and number(maxhp) and math.min(100,math.floor(100*hp/maxhp)) or nil
  local role=P.classRole(member.classID)
  local tier,reason
  if (number(hp) and hp<=3) or (pct~=nil and pct<=20) then tier,reason=1,'lethal_risk'
  elseif role=='arcane' or role=='arcane_healer' or role=='healer' then tier,reason=2,'spellcaster_or_healer_under_threat'
  elseif pct~=nil and pct<=50 then tier,reason=3,'wounded'
  elseif role=='tank' then tier,reason=5,'durable_frontliner'
  else tier,reason=4,'other_ally' end
  return {tier=tier,reason=reason,role=role,hpPercent=pct}
end
-- snapshot is PURE READ of existing EEex sprites; all optional values fail closed.
function P.partySnapshot()
  if type(EEex_Sprite_GetInPortraitID)~='function' or type(EEex_GameObject_Get)~='function' then return {} end
  local out, seen={},{}
  for slot=0,5 do
    local id=safe(function() return EEex_Sprite_GetInPortraitID(slot) end)
    if validid(id) and not seen[id] then
      seen[id]=true
      local obj=safe(function() return EEex_GameObject_Get(id) end)
      if obj and safe(function() return obj.m_id end)==id then
        out[#out+1]={id=id,slot=slot,area=safe(function()return obj.m_pArea end),
          x=safe(function()return obj.m_pos.x end),y=safe(function()return obj.m_pos.y end),
          classID=safe(function()return obj.m_typeAI.m_Class end),
          hp=safe(function()return obj.m_baseStats.m_hitPoints end),
          maxhp=safe(function()return obj.m_derivedStats.m_nMaxHitPoints end),
          guard=safe(function()return obj:getLocalInt('BGX38_GUARD')end),
          modal=safe(function()return obj.m_nModalState end)}
      end
    end
  end
  return out
end
local function before(a,b)
  if a.tier~=b.tier then return a.tier<b.tier end
  if a.signal~=b.signal then return a.signal=='confirmed_hit' end
  local ah,bh=a.hpPercent or 101,b.hpPercent or 101
  if ah~=bh then return ah<bh end
  if a.tick~=b.tick then return a.tick<b.tick end
  if a.victimSlot~=b.victimSlot then return a.victimSlot<b.victimSlot end
  return a.victimID<b.victimID
end
-- signals require exact victimID + attackerID; confirmed pre-hit intent also requires verifiedTarget=true.
-- There is NO action dispatch, even when a plan is returned.
function P.plan(party,signals,areaEqual)
  local ret={schema=1,version=P.version,mode='ADVISORY_ONLY',ordersSent=0,
    priorityOrder={},assignments={},supportCandidates={},rejections={},unassigned={}}
  if type(party)~='table' or type(signals)~='table' then ret.rejections.bad_input=1;return ret end
  local byid, partySlots={},{}
  for _,member in ipairs(party) do
    if type(member)=='table' and validid(member.id) and not byid[member.id]
      and type(member.slot)=='number' and member.slot==math.floor(member.slot)
      and member.slot>=0 and member.slot<=5 then byid[member.id]=member;partySlots[#partySlots+1]=member end
  end
  local candidates, seen={},{}
  for _,sig in ipairs(signals) do
    local reason
    if type(sig)~='table' or not validid(sig.victimID) or not validid(sig.attackerID) then reason='invalid_identity'
    elseif not byid[sig.victimID] then reason='victim_not_in_party'
    elseif byid[sig.attackerID] then reason='party_attacker'
    elseif sig.signal~='confirmed_hit' and sig.signal~='verified_attack_intent' then reason='unverified_signal'
    elseif sig.signal=='verified_attack_intent' and sig.verifiedTarget~=true then reason='target_not_verified'
    else
      local key=tostring(sig.victimID) -- protect a victim once per scheduling window
      if seen[key] then
        -- A real confirmed hit supersedes an intent within a planning window.
        if seen[key].signal=='verified_attack_intent' and sig.signal=='confirmed_hit' then
          seen[key].signal='confirmed_hit'
          seen[key].attackerID=sig.attackerID
          seen[key].tick=number(sig.tick) and sig.tick>=0 and sig.tick or seen[key].tick
        end
        reason='duplicate_victim'
      else
        local member=byid[sig.victimID];local priority=P.urgency(member)
        if not priority then reason='victim_incapacitated_or_unreadable'
        else
          local tick=number(sig.tick) and sig.tick>=0 and sig.tick or 0
          local v={victimID=sig.victimID,attackerID=sig.attackerID,
            victimSlot=member.slot,signal=sig.signal,tick=tick,
            tier=priority.tier,reason=priority.reason,role=priority.role,
            hpPercent=priority.hpPercent}
          candidates[#candidates+1]=v;seen[key]=v
        end
      end
    end
    if reason then ret.rejections[reason]=(ret.rejections[reason] or 0)+1 end
  end
  table.sort(candidates,before)
  local allocated={}
  for _,urgent in ipairs(candidates) do
    ret.priorityOrder[#ret.priorityOrder+1]=urgent
    local victim=byid[urgent.victimID]
    local options={}
    if number(victim.x) and number(victim.y) then
      for _,m in ipairs(partySlots) do
        if m.slot>0 and m.id~=urgent.victimID and m.id~=urgent.attackerID and
          m.guard==1 and m.modal==0 and not allocated[m.id] and
          number(m.x) and number(m.y) and validArea(areaEqual,m.area,victim.area) then
          local dx,dy=m.x-victim.x,m.y-victim.y
          options[#options+1]={id=m.id,slot=m.slot,dist=dx*dx+dy*dy,role=P.classRole(m.classID)}
        end
      end
    end
    table.sort(options,function(a,b) if a.dist~=b.dist then return a.dist<b.dist end return a.slot<b.slot end)
    if #options>0 then
      local primary=options[1];allocated[primary.id]=true
      ret.assignments[#ret.assignments+1]={victimID=urgent.victimID,
        attackerID=urgent.attackerID,guardianID=primary.id,urgency=urgent.tier,
        signal=urgent.signal,advisoryOnly=true}
    else
      ret.unassigned[#ret.unassigned+1]={victimID=urgent.victimID,reason='no_available_same_area_F_guardian'}
    end
  end
  -- Extra unassigned F guardians remain independent EPS actors; do NOT issue
  -- heal/spell/attack commands, only report possible support roles.
  for _,m in ipairs(partySlots) do
    if m.slot>0 and m.guard==1 and m.modal==0 and not allocated[m.id] then
      ret.supportCandidates[#ret.supportCandidates+1]={guardianID=m.id,
        suggestedRole=(function()local r=P.classRole(m.classID)
          if r=='healer' or r=='arcane_healer' then return 'healing_candidate'
          elseif r=='arcane' then return 'control_candidate' end
          return 'reserve_guardian' end)(),ordersSent=0}
    end
  end
  return ret
end
-- Read-only observation adapter for a FUTURE separately approved hook.
function P.observeHit(event,now,sourceSignal)
  P.observationCount=P.observationCount+1
  if type(event)~='table' then return nil,'bad_event' end
  if not number(now) or now<0 then return nil,'clock_unavailable' end
  local signal=sourceSignal or 'confirmed_hit'
  if signal~='confirmed_hit' and signal~='verified_attack_intent' then return nil,'unverified_signal' end
  if signal=='verified_attack_intent' and event.verifiedTarget~=true then return nil,'target_not_verified' end
  local kept={}
  for _,old in ipairs(P.observed) do
    if old.tick<=now and now-old.tick<=TICK_WINDOW then kept[#kept+1]=old end
  end
  kept[#kept+1]={victimID=event.target_id or event.protected_id,attackerID=event.actor_id or event.attacker_id,
      signal=signal,verifiedTarget=event.verifiedTarget==true,tick=now}
  while #kept>MAX_THREATS do table.remove(kept,1) end
  P.observed=kept
  local party=P.partySnapshot()
  local result=P.plan(party,kept,EEex_UDEqual)
  P.lastPlan={mode=result.mode,ordersSent=0,
    firstVictimID=result.priorityOrder[1] and result.priorityOrder[1].victimID or nil,
    highestUrgency=result.priorityOrder[1] and result.priorityOrder[1].tier or nil,
    assignedCount=#result.assignments,observedCount=#kept,
    rejected=result.rejections}
  return result
end
-- This remains ONLY a passive planning hint. Until an authoritative EEex
-- enemy-target resolver is validated in this particular EET installation,
-- no active hook may call observeIntent or dispatch a pre-hit attack.
function P.observeIntent(event,now)
  if type(event)~='table' or event.verifiedTarget~=true then return nil,'target_not_verified' end
  if not validid(event.target_id) or not validid(event.actor_id) then return nil,'invalid_identity' end
  return P.observeHit(event,now,'verified_attack_intent')
end
return P
