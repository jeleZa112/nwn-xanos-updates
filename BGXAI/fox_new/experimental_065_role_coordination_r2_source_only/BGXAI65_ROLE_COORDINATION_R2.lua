-- BGXAI 065-R2 SOURCE ONLY: defensive role allocation, pure/read-only.
-- Execute only in isolated Lua tests. Does not install, hook, move, attack, cast, or write LOCALS.
-- Requires unchanged BGX65Policy baseline for confirmed threat classification.
BGX65RoleR2 = BGX65RoleR2 or {}
local R = BGX65RoleR2
R.version = '0.3.31-065-R2-ROLE-SOURCE-ONLY'
R.dispatchEnabled = false
R.isInstalled = false

local function integer(x)
  return type(x)=='number' and x==x and x==math.floor(x) and x>=0 and x<=2147483647
end
local function finite(x)
  return type(x)=='number' and x==x and x>-100000000 and x<100000000
end
local function sameArea(eq,a,b)
  if type(eq)~='function' or a==nil or b==nil then return false end
  local ok,res=pcall(eq,a,b)
  return ok and res==true
end
local function danger(m)
  if type(m)~='table' or not finite(m.hp) or not finite(m.maxhp) or m.maxhp<=0 or m.hp<=0 then return true end
  return m.hp<=3 or m.hp/m.maxhp<=0.20
end
local function healthyFrontline(m)
  if danger(m) then return false end
  return m.hp/m.maxhp>0.50
end
local function role(m)
  local base=BGX65Policy
  if type(base)=='table' and type(base.classRole)=='function' then
    return base.classRole(m.classID)
  end
  return 'unknown'
end
local function canBeGuard(m)
  return type(m)=='table' and integer(m.id) and integer(m.slot) and m.slot>0 and m.slot<=5
    and m.guard==1 and m.modal==0 and finite(m.x) and finite(m.y) and m.area~=nil
end
local function byDistance(a,b)
  if a.distance~=b.distance then return a.distance<b.distance end
  return a.slot<b.slot
end
local function distance(a,b)
  local dx,dy=a.x-b.x,a.y-b.y
  return dx*dx+dy*dy
end
local function supportKind(r)
  if r=='arcane' then return 'control_candidate_unverified_spells' end
  if r=='healer' then return 'healing_or_protection_candidate_unverified_spells' end
  if r=='arcane_healer' then return 'healing_or_control_candidate_unverified_spells' end
  return nil
end
local function supportScore(m, urgency)
  local r=role(m)
  local wounded=urgency.hpPercent~=nil and urgency.hpPercent<=50
  if wounded and (r=='healer' or r=='arcane_healer') then return 0 end
  if r=='arcane' or r=='arcane_healer' then return 1 end
  return 2
end

-- No attacker/target invention: P.plan rejects unknown victim, party attacker,
-- and any unverified pre-hit intent. Its priorityOrder is only a proposed order.
function R.plan(party, signals, areaEqual)
  local out={version=R.version,mode='ADVISORY_ONLY',ordersSent=0,
    priorityOrder={},frontlineAssignments={},supportAssignments={},
    reserves={},uncovered={},rejections={},meta={}}
  if type(BGX65Policy)~='table' or type(BGX65Policy.plan)~='function'
    or type(party)~='table' or type(signals)~='table' then
    out.rejections.bad_input=1
    return out
  end
  local base=BGX65Policy.plan(party,signals,areaEqual)
  out.priorityOrder=base.priorityOrder or {}
  out.rejections=base.rejections or {}
  out.meta.baseAssignmentsIgnored=#(base.assignments or {})
  local byid,slotSeen={},{}
  for _,m in ipairs(party) do
    if type(m)=='table' and integer(m.id) and integer(m.slot) and m.slot<=5 and
      not byid[m.id] and not slotSeen[m.slot] then
      byid[m.id]=m;slotSeen[m.slot]=true
    end
  end
  local threatened={}
  for _,urgent in ipairs(out.priorityOrder) do threatened[urgent.victimID]=true end
  local frontlines,supporters={},{}
  for _,m in pairs(byid) do
    if canBeGuard(m) and not threatened[m.id] then
      local r=role(m)
      if r=='tank' and healthyFrontline(m) then
        frontlines[#frontlines+1]=m
      elseif supportKind(r) and not danger(m) then
        supporters[#supporters+1]=m
      else
        out.reserves[#out.reserves+1]={guardianID=m.id,slot=m.slot,
          reason=danger(m) and 'low_or_unreadable_hp' or 'role_not_safe_for_auto_melee'}
      end
    end
  end
  local allocatedFront={}
  for _,urgent in ipairs(out.priorityOrder) do
    local victim=byid[urgent.victimID]
    local options={}
    if victim and finite(victim.x) and finite(victim.y) then
      for _,m in ipairs(frontlines) do
        if not allocatedFront[m.id] and m.id~=urgent.attackerID and
          sameArea(areaEqual,m.area,victim.area) then
          options[#options+1]={m=m,slot=m.slot,distance=distance(m,victim)}
        end
      end
    end
    table.sort(options,byDistance)
    if #options>0 then
      local m=options[1].m
      allocatedFront[m.id]=true
      out.frontlineAssignments[#out.frontlineAssignments+1]={guardianID=m.id,
        guardianSlot=m.slot,victimID=urgent.victimID,victimSlot=urgent.victimSlot,
        attackerID=urgent.attackerID,urgency=urgent.tier,
        role='frontline_candidate_unverified_weapon',ordersSent=0}
    else
      out.uncovered[#out.uncovered+1]={victimID=urgent.victimID,
        type='frontline',reason='no_healthy_same_area_F_tank'}
    end
  end
  -- First one passive supporter per threatened ally (urgent first), then extras.
  -- Does not imply an actual spell, usable projectile, or safe EPS action is available.
  local usedSupport,coverage={},{}
  local function offer(urgent)
    local victim=byid[urgent.victimID]
    if not victim or not finite(victim.x) or not finite(victim.y) then return false end
    local options={}
    for _,m in ipairs(supporters) do
      if not usedSupport[m.id] and m.id~=urgent.attackerID and
        sameArea(areaEqual,m.area,victim.area) then
        options[#options+1]={m=m,slot=m.slot,distance=distance(m,victim),rank=supportScore(m,urgent)}
      end
    end
    table.sort(options,function(a,b)
      if a.rank~=b.rank then return a.rank<b.rank end
      return byDistance(a,b)
    end)
    if #options==0 then return false end
    local m=options[1].m
    usedSupport[m.id]=true
    coverage[urgent.victimID]=(coverage[urgent.victimID] or 0)+1
    out.supportAssignments[#out.supportAssignments+1]={guardianID=m.id,
      guardianSlot=m.slot,victimID=urgent.victimID,victimSlot=urgent.victimSlot,
      suggestedRole=supportKind(role(m)),roleOnly=true,spellVerified=false,ordersSent=0}
    return true
  end
  for _,urgent in ipairs(out.priorityOrder) do offer(urgent) end
  -- Multiple casters may advise about the sole remaining threat, but never cast.
  if #out.priorityOrder==1 then
    while offer(out.priorityOrder[1]) do end
  end
  for _,urgent in ipairs(out.priorityOrder) do
    if not coverage[urgent.victimID] then
      out.uncovered[#out.uncovered+1]={victimID=urgent.victimID,
        type='support',reason='no_ready_same_area_support_candidate'}
    end
  end
  table.sort(out.reserves,function(a,b)return a.slot<b.slot end)
  return out
end
return R