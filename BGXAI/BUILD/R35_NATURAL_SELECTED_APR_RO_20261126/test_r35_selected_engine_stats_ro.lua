-- R35 source-only EEex selected-APR/THAC0 witness tests (synthetic sprite).
local folder=(arg and arg[0] or ''):match('^(.*[/\\])') or './'
local r35=dofile(folder..'BGXAI_R35_SELECTED_ENGINE_STATS_RO.lua')
local n=0
local function eq(x,y)
 assert(x==y,tostring(x)..' != '..tostring(y))
end
local function test(label,fn)
 fn();n=n+1;print('PASS R35 '..label)
end
local function sprite()
 return {m_id=12345,m_bAllowEffectListCall=1,
         m_equipment={m_selectedWeapon=12,m_selectedWeaponAbility=0},
         stats={m_nNumberOfAttacks=2,m_nTHAC0=20}}
end
local function reader(x)return x.stats end
local function observed(x)return r35.observe(x,reader) end
test('selected raw APR THAC0 observed double-read',function()
 local x=observed(sprite())
 eq(x.status,'SELECTED_APR_THAC0_DOUBLE_READ_STABLE_PASSIVE')
 eq(x.selectedSlotRaw,12);eq(x.selectedAPRKeyRaw,2)
 eq(x.selectedAPRIfStandardDecoder,2);eq(x.selectedTHAC0Raw,20)
 eq(x.ordersSent,0);eq(x.dispatchAuthorized,false)
 eq(x.weaponSwitchAuthorized,false);eq(x.otherSlotEffectiveAPRVerified,false)
end)
test('EEex guard nonzero other than one accepted',function()
 local x=sprite();x.m_bAllowEffectListCall=4
 eq(observed(x).status,'SELECTED_APR_THAC0_DOUBLE_READ_STABLE_PASSIVE')
end)
test('EEex temporary effects processing hold',function()
 local x=sprite();x.m_bAllowEffectListCall=0
 eq(observed(x).reason,'ACTIVE_STATS_EFFECT_LIST_IN_PROGRESS_OR_UNVERIFIED')
end)
test('missing EEex guard hold',function()
 local x=sprite();x.m_bAllowEffectListCall=nil
 eq(observed(x).status,'HOLD_SELECTED_STATS_UNVERIFIED')
end)
test('no sprite hold',function()
 eq(observed(nil).reason,'NO_SPRITE')
end)
test('missing item ability hold',function()
 local x=sprite();x.m_equipment.m_selectedWeaponAbility=nil
 eq(observed(x).reason,'SELECTED_SLOT_OR_ABILITY_UNREADABLE')
end)
test('unrecognized APR encoding hold',function()
 local x=sprite();x.stats.m_nNumberOfAttacks=11
 eq(observed(x).reason,'APR_OR_THAC0_UNREADABLE')
end)
test('missing THAC0 hold',function()
 local x=sprite();x.stats.m_nTHAC0=nil
 eq(observed(x).reason,'APR_OR_THAC0_UNREADABLE')
end)
test('stats drift between same-callback reads hold',function()
 local x=sprite();local calls=0
 local z=r35.observe(x,function(o)
   calls=calls+1
   if calls==2 then return {m_nNumberOfAttacks=7,m_nTHAC0=19} end
   return o.stats
 end)
 eq(z.reason,'SAME_CALLBACK_STATS_OR_EQUIPMENT_DRIFT')
end)
test('selected slot drift between same-callback reads hold',function()
 local x=sprite();local calls=0
 local z=r35.observe(x,function(o)
   calls=calls+1
   if calls==2 then o.m_equipment.m_selectedWeapon=35 end
   return o.stats
 end)
 eq(z.reason,'SAME_CALLBACK_STATS_OR_EQUIPMENT_DRIFT')
end)
test('effects guard drift hold',function()
 local x=sprite();local calls=0
 local z=r35.observe(x,function(o)
   calls=calls+1
   if calls==2 then o.m_bAllowEffectListCall=0 end
   return o.stats
 end)
 eq(z.reason,'SAME_CALLBACK_STATS_OR_EQUIPMENT_DRIFT')
end)
test('no stats API hold',function()
 local x=sprite()
 eq(r35.observe(x,23).reason,'EEEX_ACTIVE_STATS_API_UNAVAILABLE')
end)
test('different naturally selected slots are observations only',function()
 local a=observed(sprite())
 local b=sprite();b.m_equipment.m_selectedWeapon=35
 b.stats.m_nNumberOfAttacks=7;b.stats.m_nTHAC0=17
 local c=observed(b)
 local x=r35.compare(a,c)
 eq(x.status,'DIFFERENT_NATURALLY_SELECTED_SLOTS_RAW_WITNESSED')
 eq(x.firstSelectedAPRKeyRaw,2);eq(x.secondSelectedAPRKeyRaw,7)
 eq(x.firstSelectedTHAC0Raw,20);eq(x.secondSelectedTHAC0Raw,17)
 eq(x.matchedBuffContextVerified,false)
 eq(x.otherSlotEffectiveAPRVerified,false)
 eq(x.manualAndEPSOriginVerified,false)
 eq(x.weaponSwitchAuthorized,false)
 eq(x.ordersSent,0)
end)
test('cross actor cannot compare selected slots',function()
 local a=observed(sprite());local b=sprite()
 b.m_id=2222;b.m_equipment.m_selectedWeapon=35
 eq(r35.compare(a,observed(b)).reason,'CROSS_ACTOR')
end)
test('same selected slot cannot be called two-slot comparison',function()
 local a=observed(sprite())
 eq(r35.compare(a,a).reason,'SAME_SELECTED_SLOT')
end)
test('incomplete samples fail closed',function()
 local a=observed(sprite())
 eq(r35.compare({},a).status,'HOLD_NATURAL_SELECTED_COMPARISON')
end)
print('R35 EEex passive selected source ONLY: '..n..' tests PASS, no game switch')
