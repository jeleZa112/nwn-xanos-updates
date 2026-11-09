-- Executes active bridge algorithm against sandboxed objects, never game.
local HITS=0
local function verify(cond,msg) HITS=HITS+1; if not cond then error('TEST FAIL: '..msg) end end
local party={101,102,103,104,105,106}
local sprites={}
local function sprite(id,x,y)
 local t={m_id=id,m_pos={x=x,y=y},m_nModalState=0,locals={}}
 function t:getLocalInt(k) return self.locals[k] or 0 end
 function t:setLocalInt(k,v) self.locals[k]=v end
 sprites[id]=t
 return t
end
for i=1,6 do sprite(100+i,10*i,0) end
sprites[102].locals.BGX38_GUARD=1
sprites[104].locals.BGX38_GUARD=1
sprites[101].locals.BGX38_GUARD=1 -- Player1 never a team guardian
EEex_Sprite_GetInPortraitID=function(i) return party[i+1] or -1 end
EEex_GameObject_Get=function(i) return sprites[i] end
EEex_EngineGlobal_CBaldurChitin={m_pObjectGame={m_worldTime={m_gameTime=1000}}}
BGX43Probe=nil
EEex_Action_AddSpriteStartedActionListener=function() end
EEex_Sprite_AddBlockWeaponHitListener=function() end
-- Loads exact in-game module shape with disabled 052 bridge.
dofile('/mnt/data/BGXAI_052_ACTIVE_BRIDGE_SOURCE_ONLY/M_BX43_052_PREVIEW.lua')
local B=BGX52Bridge
local good={event='PASSIVE_GUARD_ADVISORY_ON_CONFIRMED_HIT',confirmation='ENGINE_WEAPON_HIT_CONTEXT', protected_id=103,attacker_id=777,source_event_sequence=1}
local x,reason=B.prepare(good)
verify(x==false and reason=='disabled','disabled by default')
verify(sprites[102].locals.BGX52_REQ_SLOT==nil and sprites[104].locals.BGX52_REQ_SLOT==nil,'no writes while disabled')
B.enabled=true
x,reason=B.prepare(good)
verify(x==true and reason=='prepared','accept confirmed hit')
verify(sprites[102].locals.BGX52_REQ_SLOT==3,'closest guardian is Player2')
verify(sprites[102].locals.BGX52_EXPIRE==1090,'absolute expiry 90 ticks')
verify(sprites[102].locals.BGX52_LAST_TICK==1000,'game time stored')
verify(sprites[104].locals.BGX52_REQ_SLOT==nil,'one request only')
verify(B.last.orders_sent==false,'no engine action sent')
x,reason=B.prepare(good)
verify(x==false and reason=='duplicate_same_tick_or_clock_rewound','repeat event rejected at same tick')
local bad={event='PASSIVE_GUARD_ADVISORY_ON_CONFIRMED_HIT',confirmation='MISSING',protected_id=103,attacker_id=777,source_event_sequence=2}
x,reason=B.prepare(bad)
verify(x==false and reason=='unconfirmed_hit','reject unconfirmed')
local saved=sprites[102].locals.BGX38_GUARD
sprites[102].locals.BGX38_GUARD=0
local newer={event='PASSIVE_GUARD_ADVISORY_ON_CONFIRMED_HIT',confirmation='ENGINE_WEAPON_HIT_CONTEXT', protected_id=103,attacker_id=777,source_event_sequence=2}
x,reason=B.prepare(newer)
verify(x==true and sprites[104].locals.BGX52_REQ_SLOT==3,'F OFF drops earlier guardian')
sprites[102].locals.BGX38_GUARD=saved
sprites[102].m_nModalState=1
newer.source_event_sequence=3
x,reason=B.prepare(newer)
verify(x==false and reason=='duplicate_same_tick_or_clock_rewound','new hit same tick safely rejected')
EEex_EngineGlobal_CBaldurChitin.m_pObjectGame.m_worldTime.m_gameTime=1001
x,reason=B.prepare(newer)
verify(x==true and sprites[104].locals.BGX52_LAST_TICK==1001,'BATTLESONG excludes guardian')
sprites[102].m_nModalState=0
sprites[102].locals.BGX38_GUARD=0
sprites[104].locals.BGX38_GUARD=0
newer.source_event_sequence=4
x,reason=B.prepare(newer)
verify(x==false and reason=='no_guardian_with_f_mode','no F guardian => fail closed')
sprites[102].locals.BGX38_GUARD=1
newer.source_event_sequence=4
newer.protected_id=8888
x,reason=B.prepare(newer)
verify(x==false and reason=='victim_not_in_party','unknown victim rejected')
newer.protected_id=103
EEex_EngineGlobal_CBaldurChitin.m_pObjectGame.m_worldTime.m_gameTime=-1
x,reason=B.prepare(newer)
verify(x==false and reason=='clock_invalid','negative clock rejected')
EEex_EngineGlobal_CBaldurChitin.m_pObjectGame.m_worldTime.m_gameTime=2147483647
x,reason=B.prepare(newer)
verify(x==false and reason=='clock_invalid','clock overflow rejected')
EEex_EngineGlobal_CBaldurChitin.m_pObjectGame.m_worldTime.m_gameTime=1002
sprites[102].locals.BGX52_LAST_TICK=1000
x,reason=B.prepare(newer)
verify(x==true and sprites[102].locals.BGX52_EXPIRE==1092,'active clock writes matching TTL')
local old=sprites[102].setLocalInt
sprites[102].setLocalInt=function(self,k,v)
  if k=='BGX52_LAST_TICK' then error('mock write failure') end
  self.locals[k]=v
end
newer.source_event_sequence=5
EEex_EngineGlobal_CBaldurChitin.m_pObjectGame.m_worldTime.m_gameTime=1003
x,reason=B.prepare(newer)
verify(x==false and reason=='write_failure','write failure detected')
verify(sprites[102].locals.BGX52_REQ_SLOT==0,'failure revokes request')
sprites[102].setLocalInt=old
-- Strict separation: no source-level commands exist in a bridge sender.
local f=assert(io.open('/mnt/data/BGXAI_052_ACTIVE_BRIDGE_SOURCE_ONLY/BGX52_bridge_preview.lua','rb'))
local src=f:read('*a');f:close()
verify(not src:find('ClearActions%(') and not src:find('ActionOverride%('),'no interrupt commands')
print('BGXAI 052 LUA MOCK TESTS: '..HITS..' PASSED')
-- Real 049 callback shape integration: confirmed hit creates advisory and calls 052.
sprites[102].locals.BGX52_LAST_TICK=0
sprites[102].locals.BGX52_HAS_SENT=0
sprites[102].locals.BGX52_REQ_SLOT=0
sprites[102].locals.BGX38_GUARD=1
sprites[102].m_nModalState=0
sprites[104].locals.BGX38_GUARD=0
EEex_EngineGlobal_CBaldurChitin.m_pObjectGame.m_worldTime.m_gameTime=1200
local attacker=sprite(777,25,0)
local hitResult=BGX43Probe.onWeaponHit({attackingSprite=attacker,targetSprite=sprites[103]})
verify(hitResult==false,'weapon-hit handler must never block damage')
verify(BGX43Probe.weaponHitCalls==1 and BGX43Probe.guardSignalCount==1,'049 hit->signal chain intact')
verify(BGX43Probe.guardSignalErrors==0 and BGX43Probe.weaponHitErrors==0,'049->052 callback no errors')
verify(B.prepared>=1 and sprites[102].locals.BGX52_REQ_SLOT==3,'confirmed callback triggers one local request')
verify(sprites[102].locals.BGX52_EXPIRE==1290,'callback expiry 6 game seconds')
verify(BGX43Probe.guardDispatchEnabled==false,'049 runtime dispatch remains disabled')
print('BGXAI 052 END-TO-END MOCK TESTS: '..HITS..' PASSED')

-- Save/load regression: 049 Lua sequence resets to 1, but clock advances.
-- Persistent dedup must be based on game time, NOT local sequence.
local old_time=sprites[102].locals.BGX52_LAST_TICK
sprites[102].locals.BGX52_REQ_SLOT=0
EEex_EngineGlobal_CBaldurChitin.m_pObjectGame.m_worldTime.m_gameTime=old_time+25
local saved=BGX52Bridge.prepare({event='PASSIVE_GUARD_ADVISORY_ON_CONFIRMED_HIT', confirmation='ENGINE_WEAPON_HIT_CONTEXT',protected_id=103,attacker_id=777,source_event_sequence=1})
verify(saved==true,'first new hit after reloading Lua sequence succeeds')
-- Reject party member as attacker (defense-in-depth even though 049 already filters).
local blocked,why=BGX52Bridge.prepare({event='PASSIVE_GUARD_ADVISORY_ON_CONFIRMED_HIT', confirmation='ENGINE_WEAPON_HIT_CONTEXT',protected_id=103,attacker_id=101,source_event_sequence=2})
verify(blocked==false and why=='party_actor','party actor cannot become attacker')
print('BGXAI 052 SAVE/RELOAD + ORIGIN CHECKS: '..HITS..' PASSED')
