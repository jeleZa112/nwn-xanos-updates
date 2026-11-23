local function check(flag, msg) if not flag then error(msg, 2) end end
local calls = 0
local log = {}
local function got(key) for _,s in ipairs(log) do if s:find(key,1,true) then return s end end return nil end
Infinity_Log = function(s) log[#log+1]=s end
-- In-game io/os unavailable; make test prove console fallback.
io=nil;os=nil
EEex_Action_AddSpriteStartedActionListener=function(f) calls=calls+1; listener=f end
EEex_Sprite_GetInPortraitID=function(p) if p==2 then return 123 end return -1 end
EEex_GameObject_Get=function(id)
 -- Return new Lua object wrapper on each Get: rawequal fails, actual id is stable.
 if id~=456 then return nil end
 return {m_id=456,isSprite=function() return true end}
end
local fields={'m_nArmorClass','m_nACCrushingMod','m_nACMissileMod','m_nACPiercingMod','m_nACSlashingMod','m_nResistCrushing','m_nResistPiercing','m_nResistSlashing','m_nResistMissile'}
EEex_Sprite_GetActiveStats=function(t)
 local s={}; for _,k in ipairs(fields) do s[k]=0 end
 s.m_nArmorClass=-4;s.m_nResistMissile=15;return s
end
local base={m_id=123,m_equipment={m_selectedWeapon=10,m_selectedWeaponAbility=0,m_items={get=function(_,slot) if slot==10 then error('FIST_SLOT_SHOULD_NOT_BE_DEREF') end if slot==12 or slot==35 then return {resref='AROW01'} end end}}}
local action={m_actionID=3,m_acteeID={m_Instance=456}}
local function fire(slot) base.m_equipment.m_selectedWeapon=slot;listener(base,action) end
local modulefile='R15_M_BGXD13.lua'
local loadassert=assert(loadfile(modulefile))
loadassert()
check(calls==1,'singleton listener')
check(got('"type":"READY"')~=nil,'READY')
fire(10)
check(got('"slotClass":"FIST"')~=nil,'FIST classification')
check(got('"status":"TARGET_RAW_DEFENSE_FIELDS_CANDIDATE_ONLY"')~=nil,'fist read must succeed candidate')
check(got('"m_nResistMissile":15')~=nil,'missile resist')
check(got('"sourceActor":123')~=nil,'observed source id')
fire(12)
check(got('"slotClass":"AMMO"')~=nil,'ammo classification')
fire(35)
check(got('"slotClass":"WEAPON"')~=nil,'weapon classification')
EEex_GameObject_Get=function() return nil end
fire(12)
check(got('"reason":"TARGET_NOT_A_SPRITE"')~=nil,'HOLD reason')
check(got('"status":"HOLD"')~=nil,'HOLD status')
check(got('"targetActor":456')~=nil,'raw target survives HOLD')
local current=BGXTargetDefenseR13
loadassert()
check(calls==1 and BGXTargetDefenseR13==current,'duplicate listener blocked')
check(#log==6,'2 startup + 4 actions should make six logs; actual '..#log)
check(BGXTargetDefenseR13.ordersSent==0,'no orders')
print('R15_RUNTIME_TEST_PASS 6 checks groups')
