-- BGXAI 067: pre-impact guard on an enemy's RESOLVED, actual attack action.
-- Zero new EEex listeners. Never calls Spell, Attack, ProtectObject or ClearActions.
-- This is intentionally NOT a proactive enemy scan and not a guaranteed block.
BGX67Early = BGX67Early or {}
local G=BGX67Early
G.version='0.3.35-067-EARLY-RESOLVED-ATTACK-SOURCE-ONLY'
G.enabled=true
G.attempts,G.prepared,G.errors=0,0,0
G.rejected={}
G.last=nil
G.reserved={}
G.victims={}
local CLASS_FRONT={[2]=true,[6]=true,[12]=true}
local CLASS_MELEE_SUPPORT={[3]=true,[8]=true,[11]=true} -- cleric/druid/shaman only, never arcane/bard
local ALLOWED_ACTION={[3]=true,[98]=true,[105]=true,[134]=true}
local TTL=90  -- 6 seconds; only for attack-start, distinct from weapon-hit 20s
local LEASE=45
local MAX_TICK=2147483346
local function safe(fn) local ok,v=pcall(fn);if ok then return v end;return nil end
local function int(n)return type(n)=='number' and n==math.floor(n) and n>=0 and n<=2147483647 end
local function finite(n)return type(n)=='number' and n==n and n>-100000000 and n<100000000 end
local function reject(why)
 G.rejected[why]=(G.rejected[why] or 0)+1
 G.last={status='NO_WRITE',reason=why}
 return false,why
end
local function read(o,key)return safe(function()return o:getLocalInt(key)end)end
local function pct(o)
 local h=safe(function()return o.m_baseStats.m_hitPoints end)
 local m=safe(function()return o.m_derivedStats.m_nMaxHitPoints end)
 if not finite(h) or not finite(m) or h<=0 or m<=0 or h>m then return nil end
 return h/m*100
end
local function reserve(o,slot,now)
 local success=pcall(function()
  o:setLocalInt('BGX67_EARLY_SLOT',0)
  o:setLocalInt('BGX67_EARLY_EXPIRE',now+TTL)
  o:setLocalInt('BGX67_EARLY_LAST',now)
  o:setLocalInt('BGX67_EARLY_SENT',1)
  o:setLocalInt('BGX67_EARLY_SLOT',slot)
 end)
 if not success then pcall(function()o:setLocalInt('BGX67_EARLY_SLOT',0)end) end
 return success
end
local function execute(e)
 G.attempts=G.attempts+1
 if not G.enabled or not BGX43Probe.enabled then return reject('disabled') end
 -- Original observer already proved this record is from an actual nonparty
 -- attack action, not a hit, guess, actionless dialogue, or group attack 94.
 if type(e)~='table' or e.event~='NONPARTY_ATTACK_STARTED_ON_PARTY'
   or e.hostility~='CONFIRMED_BY_EXPLICIT_ATTACK_ACTION'
   or (e.target_source~='actee1' and e.target_source~='actee2')
   or not ALLOWED_ACTION[e.action_id] then return reject('not_explicit_resolved_attack') end
 local attacker,victim=e.actor_id,e.target_id
 if not int(attacker) or not int(victim) or attacker==victim then return reject('bad_ids') end
 if type(EEex_Sprite_GetInPortraitID)~='function' or
   type(EEex_GameObject_Get)~='function' or type(EEex_UDEqual)~='function' then return reject('eeex_missing') end
 local party,all,slot={}, {},nil
 for i=0,5 do
  local id=safe(function()return EEex_Sprite_GetInPortraitID(i)end)
  if int(id) and not party[id] then
   party[id]=i+1
   local o=safe(function()return EEex_GameObject_Get(id)end)
   if o and safe(function()return o.m_id end)==id then all[#all+1]={id=id,slot=i+1,obj=o} end
  end
 end
 if party[attacker] or not party[victim] then return reject('not_hostile_nonparty_on_party') end
 slot=party[victim]
 local v=safe(function()return EEex_GameObject_Get(victim)end)
 local enemy=safe(function()return EEex_GameObject_Get(attacker)end)
 if not v or not enemy or safe(function()return v.m_id end)~=victim
   or safe(function()return enemy.m_id end)~=attacker then return reject('identity_unresolved') end
 local now=safe(function()return EEex_EngineGlobal_CBaldurChitin.m_pObjectGame.m_worldTime.m_gameTime end)
 if not int(now) or now>MAX_TICK then return reject('time_unavailable') end
 if G.lastTick and now<G.lastTick then G.reserved={};G.victims={} end
 G.lastTick=now
 for id,t in pairs(G.reserved) do if not int(t) or t<=now then G.reserved[id]=nil end end
 for id,t in pairs(G.victims) do if not int(t) or t<=now then G.victims[id]=nil end end
 if G.victims[victim] then return reject('victim_lease') end
 local area=safe(function()return v.m_pArea end)
 local enemyArea=safe(function()return enemy.m_pArea end)
 local vx=safe(function()return v.m_pos.x end)
 local vy=safe(function()return v.m_pos.y end)
 if not area or not enemyArea or safe(function()return EEex_UDEqual(area,enemyArea)end)~=true
   or not finite(vx) or not finite(vy) then return reject('enemy_target_area_mismatch') end
 local health=pct(v)
 if not health then return reject('victim_health_unknown') end
 local best=nil
 for _,m in ipairs(all) do
  if m.slot>1 and m.id~=victim and not G.reserved[m.id] then
   local obj=m.obj
   local cls=safe(function()return obj.m_typeAI.m_Class end)
   local front=CLASS_FRONT[cls]==true
   local backup=CLASS_MELEE_SUPPORT[cls]==true
   local gh=pct(obj)
   local a=safe(function()return obj.m_pArea end)
   local x=safe(function()return obj.m_pos.x end)
   local y=safe(function()return obj.m_pos.y end)
   if (front or backup) and gh and gh>50 and read(obj,'BGX38_GUARD')==1
     and safe(function()return obj.m_nModalState end)==0
     and a and safe(function()return EEex_UDEqual(a,area)end)==true
     and finite(x) and finite(y) and read(obj,'BGX67_EARLY_SLOT')==0
     and read(obj,'BGX52_REQ_SLOT')==0
     and read(obj,'BGX66_S_HEAL_SLOT')==0
     and read(obj,'BGX66_S_WARD')==0 then
    -- A threatened critical-HP ally needs a cleric to remain free for healing.
    if front or health>=45 then
     local last=read(obj,'BGX67_EARLY_LAST')
     local sent=read(obj,'BGX67_EARLY_SENT')
     if int(last) and (sent==0 or sent==1) and (sent==0 or now>last) then
      local d=(x-vx)^2+(y-vy)^2
      local candidate={id=m.id,slot=m.slot,sprite=obj,front=front,dist=d}
      if not best or (candidate.front and not best.front) or
        (candidate.front==best.front and (candidate.dist<best.dist or
        (candidate.dist==best.dist and candidate.slot<best.slot))) then best=candidate end
     end
    end
   end
  end
 end
 if not best then return reject('no_eligible_melee_guardian') end
 if not reserve(best.sprite,slot,now) then G.errors=G.errors+1;return reject('write_failed') end
 G.reserved[best.id]=now+LEASE;G.victims[victim]=now+LEASE
 G.prepared=G.prepared+1
 G.last={status='PREHIT_BCS_REQUEST_ONLY',victim_id=victim,
     defender_id=best.id,defender_slot=best.slot,victim_slot=slot,
     frontline=best.front,expires_at=now+TTL,engine_orders_sent=0}
 return true,'prepared'
end
function G.onAttack(record)
 local ok,a,b=pcall(execute,record)
 if not ok then G.errors=G.errors+1;return reject('internal_error') end
 return a,b
end
-- Same old on-start listener already registered by P.init(), wrapped safely.
-- Require exactly a freshly appended observer attack record, not a stale ring item.
local oldOnStarted=BGX43Probe.onStarted
BGX43Probe.onStarted=function(sprite,action)
 local seq=BGX43Probe.nextSequence or 1
 oldOnStarted(sprite,action)
 if (BGX43Probe.nextSequence or 1)~=seq then
  local events=BGX43Probe.events
  G.onAttack(events[#events])
 end
end
