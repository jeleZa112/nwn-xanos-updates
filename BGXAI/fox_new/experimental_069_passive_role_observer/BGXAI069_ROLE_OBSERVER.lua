-- BGXAI 069 -- PASSIVE ROLE OBSERVER, SOURCE ONLY, NOT INSTALLED.
-- No hooks, timers, action dispatch, changes to EPS/BCS, local variable writes,
-- or changes to live game. EEex facts not independently proven remain UNKNOWN.
-- Never automatically use this module's recommendations as orders.
local R = { version = '0.3.36-069-PASSIVE-ROLE-OBSERVER-SOURCE-ONLY' }

-- BG(2)EE CLASS.IDS. Game's actual IDS is authoritative, especially with mods.
local DATA = {
 [1]={'MAGE',               {arcane=true}},
 [2]={'FIGHTER',            {martial=true}},
 [3]={'CLERIC',             {divine=true,healer=true}},
 [4]={'THIEF',              {thief=true}},
 [5]={'BARD',               {bard_song=true,arcane=true}},
 [6]={'PALADIN',            {martial=true,divine_limited=true}},
 [7]={'FIGHTER_MAGE',       {martial=true,arcane=true}},
 [8]={'FIGHTER_CLERIC',     {martial=true,divine=true,healer=true}},
 [9]={'FIGHTER_THIEF',      {martial=true,thief=true}},
[10]={'FIGHTER_MAGE_THIEF', {martial=true,arcane=true,thief=true}},
[11]={'DRUID',              {divine=true,healer=true,shapeshift_possible=true}},
[12]={'RANGER',             {martial=true,divine_limited=true}},
[13]={'MAGE_THIEF',         {arcane=true,thief=true}},
[14]={'CLERIC_MAGE',        {divine=true,healer=true,arcane=true}},
[15]={'CLERIC_THIEF',       {divine=true,healer=true,thief=true}},
[16]={'FIGHTER_DRUID',      {martial=true,divine=true,healer=true,shapeshift_possible=true}},
[17]={'FIGHTER_MAGE_CLERIC',{martial=true,arcane=true,divine=true,healer=true}},
[18]={'CLERIC_RANGER',      {martial=true,divine=true,healer=true}},
[19]={'SORCERER',           {arcane=true}},
[20]={'MONK',               {skirmisher=true}},
[21]={'SHAMAN',             {divine=true,healer=true,spirits=true}},
}

local function safe(f)
 local ok, v = pcall(f)
 if ok then return v end
 return nil
end
local function int(x)
 return type(x)=='number' and x==math.floor(x) and x>=0 and x<2147483647
end
local function finite(x)
 return type(x)=='number' and x==x and x>-100000000 and x<100000000
end
local function flags(id)
 local item = DATA[id]
 local c = {}
 if item then for k,v in pairs(item[2]) do c[k]=v end end
 return item and item[1] or 'UNKNOWN', c
end

function R.inspect(sprite, facts)
 facts=type(facts)=='table' and facts or {}
 local cls=safe(function() return sprite.m_typeAI.m_Class end)
 if not int(cls) or not DATA[cls] then cls=nil end
 local name, caps=flags(cls)
 local hp=safe(function() return sprite.m_baseStats.m_hitPoints end)
 local maximum=safe(function() return sprite.m_derivedStats.m_nMaxHitPoints end)
 local hp_pct=nil
 if finite(hp) and finite(maximum) and maximum>0 and hp>=0 and hp<=maximum then
  hp_pct=hp/maximum*100
 end
 local f=safe(function() return sprite:getLocalInt('BGX38_GUARD') end)
 if f~=0 and f~=1 then f=nil end

 -- No unverified guesses about m_kit, active Shapechange, or dual-level
 -- restoration: only an explicit, already-validated adapter may provide facts.
 local kit='UNKNOWN'
 if type(facts.kit)=='table' and facts.kit.verified==true
    and type(facts.kit.name)=='string' and #facts.kit.name>0 then kit=facts.kit.name end
 local dual=facts.dual
 local dual_state='UNKNOWN'
 if type(dual)=='table' and dual.verified==true
    and int(dual.old_class_id) and DATA[dual.old_class_id]
    and type(dual.old_active)=='boolean' then
  dual_state=dual.old_active and 'OLD_ACTIVE' or 'OLD_LOCKED'
 elseif type(dual)=='table' then dual_state='UNVERIFIED' end

 -- Potential capabilities from verified restored former class only. The
 -- current CLASS.IDS may describe just the new Mage/Cleric after dualing.
 local old_caps={}
 if dual_state=='OLD_ACTIVE' then
  local former_name
  former_name,old_caps=flags(dual.old_class_id)
 end
 local martial=caps.martial==true or old_caps.martial==true
 local healer=caps.healer==true or old_caps.healer==true
 if dual_state=='OLD_LOCKED' then
  -- If current martial class is separately proven active, do not mistakenly
  -- ban Mage->Fighter; otherwise fail closed for both kinds of dual.
  martial = caps.martial==true and dual.current_martial_verified==true
  healer = caps.healer==true and dual.current_heal_verified==true
 elseif dual_state=='UNVERIFIED' then
  martial = false
  healer = false
 end

 local shape_ok=false
 if name=='DRUID' and kit=='SHAPESHIFTER' and type(facts.form)=='table'
    and facts.form.verified==true and facts.form.melee_verified==true
    and (facts.form.name=='WEREWOLF' or facts.form.name=='GREATER_WEREWOLF') then
  shape_ok=true
 end

 local out={
   version=R.version, status='ADVISORY_ONLY', class_id=cls, class_name=name,
   capabilities=caps, kit_name=kit, dual_state=dual_state,
   hp_percent=hp_pct, guard_toggle=f, martial_capable=martial,
   healer_capable=healer, shape_melee_confirmed=shape_ok,
   possible_interceptor=false, possible_healer=false,
   reason='NOT_EVALUATED', orders_sent=0, hook_registered=false,
 }
 local heal=facts.healing
 out.possible_healer=healer and type(heal)=='table' and heal.verified==true
   and heal.usable_now==true or false
 local action=facts.actions
 local combat=facts.combat
 if cls==nil then out.reason='UNKNOWN_CLASS'; return out end
 if f~=1 then out.reason='GUARD_DISABLED_OR_UNKNOWN'; return out end
 if hp_pct==nil or hp_pct<=60 then out.reason='HP_NOT_CONFIRMED_SAFE'; return out end
 if not (martial or shape_ok) then out.reason='NO_VERIFIED_MELEE_ROLE'; return out end
 if type(action)~='table' or action.verified~=true then
   out.reason='ACTIONS_UNVERIFIED';return out end
 if action.manual~=false or action.casting~=false or action.singing~=false
    or action.traps~=false then out.reason='EPS_OR_MANUAL_PRIORITY';return out end
 if action.heal_pending~=false then out.reason='HEAL_FIRST_OR_UNKNOWN';return out end
 if action.idle~=true then out.reason='NOT_IDLE';return out end
 if type(combat)~='table' or combat.verified~=true then
   out.reason='COMBAT_UNVERIFIED';return out end
 if combat.same_area~=true or combat.can_act~=true or combat.melee~=true
    or combat.survivability~=true then
   out.reason='COMBAT_NOT_VERIFIED_SAFE'; return out end
 out.possible_interceptor=true
 out.reason='POTENTIAL_ONLY_NO_ENGINE_ORDER'
 return out
end

function R.class_name(id)
 if not int(id) then return 'UNKNOWN' end
 return flags(id)
end

return R
