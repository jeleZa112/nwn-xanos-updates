-- BGXAI 052 guarded threat-to-BCS bridge - SOURCE PROTOTYPE, NOT INSTALLED.
-- Only the matching BCS rule may execute ProtectObject. Never queues any engine action.
BGX52Bridge = BGX52Bridge or {}
local B = BGX52Bridge
B.enabled = false -- DISABLED by default; requires separately reviewed guarded installer.
B.attempts = 0
B.prepared = 0
B.rejected = {}
B.last = nil
local TTL_TICKS = 90 -- 6 seconds at standard IE game clock; must match BCS time clock.
local MAX_GAME_TIME = 2147483556 -- signed-int room for TTL
local function safe(fn,...)
    local ok,val = pcall(fn,...)
    if ok then return val end
    return nil
end
local function reject(reason)
    B.rejected[reason]=(B.rejected[reason] or 0)+1
    B.last={result="NO_WRITE",reason=reason}
    return false,reason
end
local function validInt(x)
    return type(x)=="number" and x==math.floor(x) and x>=0 and x<=2147483647
end
function B.prepare(advisory)
    B.attempts=B.attempts+1
    if not B.enabled then return reject("disabled") end
    if type(advisory)~="table" or advisory.event~="PASSIVE_GUARD_ADVISORY_ON_CONFIRMED_HIT"
       or advisory.confirmation~="ENGINE_WEAPON_HIT_CONTEXT" then
       return reject("unconfirmed_hit")
    end
    local victimID,attackerID=advisory.protected_id,advisory.attacker_id
    local sequence=advisory.source_event_sequence
    if not validInt(victimID) or not validInt(attackerID) or victimID==attackerID
       or not validInt(sequence) or sequence==0 then return reject("invalid_identity") end
    if type(EEex_Sprite_GetInPortraitID)~="function" or type(EEex_GameObject_Get)~="function" then
       return reject("api_unavailable")
    end
    local slot, victim
    for i=0,5 do
       local id=safe(EEex_Sprite_GetInPortraitID,i)
       if id==attackerID then return reject("party_actor") end
       if id==victimID then slot=i+1;victim=safe(EEex_GameObject_Get,id) end
    end
    if not slot or not victim or safe(function()return victim.m_id end)~=victimID then return reject("victim_not_in_party") end
    local now=safe(function()return EEex_EngineGlobal_CBaldurChitin.m_pObjectGame.m_worldTime.m_gameTime end)
    if not validInt(now) or now>MAX_GAME_TIME then return reject("clock_invalid") end
    local vx=safe(function()return victim.m_pos.x end)
    local vy=safe(function()return victim.m_pos.y end)
    if type(vx)~="number" or type(vy)~="number" then return reject("unknown_position") end
    local options={}
    for i=1,5 do -- Player1 is never a 042B team guardian.
       local id=safe(EEex_Sprite_GetInPortraitID,i)
       if validInt(id) and id~=victimID and id~=attackerID then
          local obj=safe(EEex_GameObject_Get,id)
          if obj and safe(function()return obj.m_id end)==id then
             local guard=safe(function()return obj:getLocalInt("BGX38_GUARD")end)
             local modal=safe(function()return obj.m_nModalState end)
             local xx=safe(function()return obj.m_pos.x end)
             local yy=safe(function()return obj.m_pos.y end)
             if guard==1 and modal==0 and type(xx)=="number" and type(yy)=="number" then
                local dx,dy=xx-vx,yy-vy
                options[#options+1]={sprite=obj,id=id,slot=i+1,dist=dx*dx+dy*dy}
             end
          end
       end
    end
    if #options==0 then return reject("no_guardian_with_f_mode") end
    table.sort(options,function(a,b)
       if a.dist==b.dist then return a.slot<b.slot end
       return a.dist<b.dist
    end)
    local best=options[1]
    -- 049 event sequence resets on reload; never persist it as dedup across saves.
    -- Persist monotonic GAME CLOCK + initialized flag instead.
    local previous=safe(function()return best.sprite:getLocalInt("BGX52_LAST_TICK")end)
    local initialized=safe(function()return best.sprite:getLocalInt("BGX52_HAS_SENT")end)
    if not validInt(previous) or (initialized~=0 and initialized~=1) then
       return reject("dedup_unreadable")
    end
    if initialized==1 and now<=previous then return reject("duplicate_same_tick_or_clock_rewound") end
    -- Write request LAST: script can never see a half-formed new request.
    -- A failure clears the request; never call Attack/ClearActions/ProtectObject from Lua.
    local function set(k,v)best.sprite:setLocalInt(k,v) end
    local ok=pcall(function()
       set("BGX52_REQ_SLOT",0)
       set("BGX52_EXPIRE",now+TTL_TICKS)
       set("BGX52_LAST_TICK",now)
       set("BGX52_HAS_SENT",1)
       set("BGX52_REQ_SLOT",slot)
    end)
    if not ok then
       pcall(set,"BGX52_REQ_SLOT",0)
       return reject("write_failure")
    end
    B.prepared=B.prepared+1
    B.last={result="PREPARED_BCS_ONLY",source_event_sequence=sequence,
            chosen_guardian=best.id,victim_id=victimID,victim_slot=slot,
            expires_at_tick=now+TTL_TICKS,orders_sent=false}
    return true,"prepared"
end
