-- BGXAI 066S: real BCS REQUESTS for low-resource caster emergency responses.
-- SOURCE ONLY: this module is inert until the verified new BCS receiver is
-- installed separately. No direct Spell/Attack/ClearActions or hook registration.
-- Real spell availability and action queue are rechecked BY BCS, not inferred
-- from class alone. Applies exclusively after a confirmed EEex weapon hit.
BGX66Caster = BGX66Caster or {}
local S=BGX66Caster
S.version='0.3.33-066S-CASTER-EMERGENCY-SOURCE-ONLY'
S.enabled=true
S.healPrepared=0
S.wardPrepared=0
S.errors=0
S.rejected={}
S.last=nil
S.reservations={}
S.victims={}
local EXPIRE=300
local LEASE=45
local MAX_TIME=2147483346
local HEALER={[3]=true,[8]=true,[11]=true,[14]=true,[15]=true,[16]=true,[17]=true,[18]=true}
local ARCANE={[1]=true,[5]=true,[7]=true,[10]=true,[13]=true,[14]=true,[17]=true,[19]=true}
local function integer(v) return type(v)=='number' and v==math.floor(v) and v>=0 and v<=2147483647 end
local function number(v) return type(v)=='number' and v==v and v>=0 and v<100000000 end
local function safe(f,...) local ok,v=pcall(f,...); if ok then return v end;return nil end
local function reason(why)
 S.rejected[why]=(S.rejected[why] or 0)+1
 S.last={status='NO_WRITE',reason=why}
 return false,why
end
local function get(o,k) return safe(function()return o:getLocalInt(k)end) end
local function apply(o, key, fields, slot)
 local ok=pcall(function()
  o:setLocalInt(key,0)
  for _,x in ipairs(fields) do o:setLocalInt(x[1],x[2]) end
  o:setLocalInt(key,slot) -- last write commits the request
 end)
 if not ok then pcall(function()o:setLocalInt(key,0)end) end
 return ok
end
local function pct(o)
 local hp=safe(function()return o.m_baseStats.m_hitPoints end)
 local mh=safe(function()return o.m_derivedStats.m_nMaxHitPoints end)
 if not number(hp) or not number(mh) or hp==0 or mh==0 or hp>mh then return nil end
 return 100*hp/mh
end
local function process(hit)
 if not S.enabled then return reason('disabled') end
 if type(hit)~='table' or hit.event~='PASSIVE_GUARD_ADVISORY_ON_CONFIRMED_HIT'
    or hit.confirmation~='ENGINE_WEAPON_HIT_CONTEXT' then return reason('unconfirmed_hit') end
 local victimID,attackerID=hit.protected_id,hit.attacker_id
 if not integer(victimID) or not integer(attackerID) or victimID==attackerID then return reason('bad_identity') end
 if type(EEex_Sprite_GetInPortraitID)~='function' or type(EEex_GameObject_Get)~='function'
    or type(EEex_UDEqual)~='function' then return reason('eeex_missing') end
 local party,ids={},{}
 for i=0,5 do
  local id=safe(EEex_Sprite_GetInPortraitID,i)
  if integer(id) and not ids[id] then
   local o=safe(EEex_GameObject_Get,id)
   if o and safe(function()return o.m_id end)==id then
    ids[id]=true;party[#party+1]={id=id,slot=i+1,obj=o}
   end
  end
 end
 if ids[attackerID] then return reason('party_attacker') end
 local victim,slot
 for _,m in ipairs(party) do if m.id==victimID then victim=m.obj;slot=m.slot end end
 if not victim then return reason('victim_not_in_party') end
 local health=pct(victim)
 if not health then return reason('victim_health_unknown') end
 if health>=45 then return reason('not_emergency') end
 local clock=safe(function()return EEex_EngineGlobal_CBaldurChitin.m_pObjectGame.m_worldTime.m_gameTime end)
 if not integer(clock) or clock>MAX_TIME then return reason('clock_unavailable') end
 if S.lastTick and clock<S.lastTick then S.reservations={};S.victims={} end
 S.lastTick=clock
 for id,t in pairs(S.reservations) do if not integer(t) or t<=clock then S.reservations[id]=nil end end
 for id,t in pairs(S.victims) do if not integer(t) or t<=clock then S.victims[id]=nil end end
 if S.victims[victimID] then return reason('victim_lease') end
 local area=safe(function()return victim.m_pArea end)
 local vx=safe(function()return victim.m_pos.x end)
 local vy=safe(function()return victim.m_pos.y end)
 if area==nil or not number(vx) or not number(vy) then return reason('victim_location_unknown') end
 local healer,ward,rank=nil,nil,nil
 for _,m in ipairs(party) do
  if m.slot>1 and m.id~=attackerID and not S.reservations[m.id] then
   local o=m.obj
   local mode=get(o,'BGX38_GUARD')
   local modal=safe(function()return o.m_nModalState end)
   local cls=safe(function()return o.m_typeAI.m_Class end)
   local other=safe(function()return o.m_pArea end)
   local ox=safe(function()return o.m_pos.x end)
   local oy=safe(function()return o.m_pos.y end)
   local same=other~=nil and safe(function()return EEex_UDEqual(area,other)end)==true
   if mode==1 and modal==0 and same and number(ox) and number(oy) and pct(o) then
    if HEALER[cls] and get(o,'BGX66_S_HEAL_SLOT')==0 then
     local dist=(ox-vx)^2+(oy-vy)^2
     if not healer or dist<rank or (dist==rank and m.slot<healer.slot) then healer=m;rank=dist end
    end
    if m.id==victimID and ARCANE[cls] and health<=25 and get(o,'BGX66_S_WARD')==0 then ward=m end
   end
  end
 end
 local prepared={heal=false,ward=false}
 if healer then
  local o=healer.obj
  local oldTick=get(o,'BGX66_S_HEAL_LAST')
  local sent=get(o,'BGX66_S_HEAL_SENT')
  if integer(oldTick) and (sent==0 or sent==1) and (sent==0 or clock>oldTick) then
   local ok=apply(o,'BGX66_S_HEAL_SLOT',{{'BGX66_S_HEAL_EXPIRE',clock+EXPIRE},{'BGX66_S_HEAL_LAST',clock},{'BGX66_S_HEAL_SENT',1}},slot)
   if ok then
    prepared.heal=true;S.healPrepared=S.healPrepared+1;S.reservations[healer.id]=clock+LEASE
   else S.errors=S.errors+1 end
  end
 end
 -- A dual-class priest/mage is a single actor: heal first, never queue two casts.
 if healer and ward and healer.id==ward.id then ward=nil end
 if ward then
  local o=ward.obj
  local oldTick=get(o,'BGX66_S_WARD_LAST')
  local sent=get(o,'BGX66_S_WARD_SENT')
  if integer(oldTick) and (sent==0 or sent==1) and (sent==0 or clock>oldTick) then
   local ok=apply(o,'BGX66_S_WARD',{{'BGX66_S_WARD_EXPIRE',clock+EXPIRE},{'BGX66_S_WARD_LAST',clock},{'BGX66_S_WARD_SENT',1}},1)
   if ok then
    prepared.ward=true;S.wardPrepared=S.wardPrepared+1;S.reservations[ward.id]=clock+LEASE
   else S.errors=S.errors+1 end
  end
 end
 if prepared.heal or prepared.ward then
  S.victims[victimID]=clock+LEASE
  S.last={status='REQUESTS_PREPARED_BCS_ONLY',victim_id=victimID,victim_slot=slot,
    health_percent=health,healer_id=prepared.heal and healer.id or nil,
    mage_id=prepared.ward and ward.id or nil,heal=prepared.heal,ward=prepared.ward,
    spells_cast=0}
  return true,'requests_prepared'
 end
 return reason('no_eligible_support')
end
function S.onHit(hit)
 local ok,a,b=pcall(process,hit)
 if not ok then S.errors=S.errors+1;return reason('internal_error') end
 return a,b
end
-- Original 066 frontline dispatch remains first; caster requests are additive.
local basePrepare=BGX52Bridge.prepare
BGX52Bridge.prepare=function(hit)
 local ok,why=basePrepare(hit)
 S.onHit(hit)
 return ok,why
end
