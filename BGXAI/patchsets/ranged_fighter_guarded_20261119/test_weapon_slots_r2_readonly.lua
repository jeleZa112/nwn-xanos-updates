local here=(arg and arg[0] or ''):match('^(.*[/\\])') or './'
local M=assert(loadfile(here..'BGXAI_WEAPON_SLOTS_R2_READONLY.lua'))()
local total=0
local function test(name,fn)
 local ok,err=pcall(fn);if not ok then error('FAILED '..name..': '..tostring(err)) end
 total=total+1;print('PASS '..name)
end
local function eq(x,y) assert(x==y,tostring(x)..' ~= '..tostring(y)) end
local function scene(opts)
 opts=opts or {}
 local read={};local calls={}
 for i=0,38 do read[i]=nil end
 read[35]={m_useCount1=3,m_flags=1,cResRef={get=function() return 'BOW05' end}};read[36]={m_useCount1=1};read[12]={m_useCount1=16,cResRef={get=function() return 'AROW01' end}};read[9]={m_useCount1=1}
 local items={get=function(self,idx)
   calls[#calls+1]=idx
   if opts.throwIndex==idx then error('unavailable') end
   return read[idx]
 end}
 local sprite={m_id=opts.id or 139135050,m_equipment={m_selectedWeapon=opts.sel or 12,m_selectedWeaponAbility=0,m_items=items}}
 return sprite,read,calls
end
test('source readonly',function()eq(M.installed,false)end)
test('live 31 bit actor id',function()local s=scene();local r=M.observe_sprite(s);eq(r.actorId,139135050)end)
test('raw fixed slots count and values',function()
 local s=scene();local r=M.observe_sprite(s);eq(#r.quickWeapons,4);eq(#r.quivers,4)
 eq(r.quickWeapons[1].index,35);eq(r.quickWeapons[4].index,38)
 eq(r.quivers[1].index,11);eq(r.quivers[4].index,14)
 eq(r.quivers[2].useCount1Raw,16);eq(r.quickWeapons[1].flagsRaw,1)
end)
test('only in-range fixed indices requested',function()
 local s,_,calls=scene();M.observe_sprite(s)
 eq(#calls,9); local seen={};for _,i in ipairs(calls) do assert(i==9 or i>=11 and i<=14 or i>=35 and i<=38);seen[i]=true end
 for _,i in ipairs({9,11,12,13,14,35,36,37,38}) do assert(seen[i]) end
end)
test('12 is ammo index and not bow identity',function()
 local s=scene();local r=M.observe_sprite(s);eq(r.selectedInventoryKind,'AMMO_QUICKSLOT');eq(r.itemIdentityVerified,false)
end)
test('35 is first weapon slot',function()local s=scene({sel=35});local r=M.observe_sprite(s);eq(r.selectedInventoryKind,'WEAPON_QUICKSLOT')end)
test('resref never guessed',function()local s=scene();local r=M.observe_sprite(s);eq(r.quickWeapons[1].itemResrefRaw,'BOW05');eq(r.quivers[2].itemResrefRaw,'AROW01');eq(r.itemIdentityVerified,false)end)
test('malformed resref rejected not guessed',function()
 local s,raw=scene();raw[35].cResRef={get=function() return 'BOW05\nEVIL' end}
 local r=M.observe_sprite(s);eq(r.quickWeapons[1].itemResrefRaw,nil);eq(r.quickWeapons[1].resrefAccess,'INVALID_RESREF')
end)
test('resref getter errors fail closed',function()
 local s,raw=scene();raw[35].cResRef={get=function() error('bad') end}
 local r=M.observe_sprite(s);eq(r.quickWeapons[1].itemResrefRaw,nil);eq(r.quickWeapons[1].resrefAccess,'RESREF_READ_ERROR')
end)
test('resref presence alone never authorizes weapon',function()
 local s=scene();local r=M.observe_sprite(s)
 eq(r.quickWeapons[1].itemResrefRaw,'BOW05');eq(r.quickWeapons[1].canEquip,false)
 eq(r.weaponSwitchAuthorized,false);eq(r.abilityVerified,false)
end)
test('empty slot no invented item',function()local s=scene();local r=M.observe_sprite(s);eq(r.quickWeapons[3].access,'NULL')end)
test('object returned does not certify identity',function()
 local s=scene();local r=M.observe_sprite(s);eq(r.quickWeapons[1].access,'OBJECT_RETURNED_UNVERIFIED');eq(r.quickWeapons[1].identityVerified,false)
end)
test('never claim ammo count from use count',function()
 local s=scene();local r=M.observe_sprite(s);eq(r.quivers[2].useCount1Raw,16);eq(r.ammoCountVerified,false)
end)
test('no per-slot APR certification',function()
 local s=scene();local r=M.observe_sprite(s);eq(r.perSlotAPRVerified,false);eq(r.weaponPriorityLive,false)
end)
test('no combat action or queue mutation',function()
 local s=scene();local before=s.m_equipment.m_selectedWeapon;local r=M.observe_sprite(s)
 eq(s.m_equipment.m_selectedWeapon,before);eq(r.ordersSent,0);eq(r.actionQueueCleared,false);eq(r.dispatchAuthorized,false)
end)
test('bad portrait refuses',function()eq(M.observe_portrait(-1).status,'HOLD_INVALID_PORTRAIT')end)
test('synthetic portrait getter reads actor',function()
 local s=scene();local r=M.observe_portrait(2,function(i)eq(i,2);return s end);eq(r.portraitIndex,2);eq(r.actorId,139135050)
end)
test('missing sprite holds',function()eq(M.observe_sprite(nil).status,'HOLD_NO_SPRITE')end)
test('missing equipment holds',function()eq(M.observe_sprite({m_id=17}).status,'HOLD_EQUIPMENT_UNAVAILABLE')end)
test('missing items holds',function()eq(M.observe_sprite({m_id=17,m_equipment={}}).status,'HOLD_ITEM_ARRAY_UNAVAILABLE')end)
test('item accessor exception isolated',function()
 local s=scene({throwIndex=35});local r=M.observe_sprite(s);eq(r.status,'HOLD_SOME_SLOTS_UNREADABLE');eq(r.quickWeapons[1].access,'READ_ERROR')
end)
test('uncertain item counts null',function()
 local s,raw=scene();raw[35].m_useCount1=-20;raw[35].m_flags='x';local r=M.observe_sprite(s)
 eq(r.quickWeapons[1].useCount1Raw,nil);eq(r.quickWeapons[1].flagsRaw,nil)
end)
test('same selected cannot prove buffs identical',function()
 local s=scene();local before=M.observe_sprite(s);local after=M.observe_sprite(s)
 eq(M.compare(before,after).status,'RAW_FINGERPRINT_SAME_NOT_PROOF_OF_BUFFS')
end)
test('change ammo invalidates advice without stopping action',function()
 local s,raw=scene();local before=M.observe_sprite(s);raw[12].m_useCount1=15;local after=M.observe_sprite(s)
 local r=M.compare(before,after);eq(r.status,'INVALIDATE_WEAPON_ADVICE_KEEP_ACTION');eq(r.currentActionPreserved,true)
end)
test('change selected slot invalidates advice',function()
 local s=scene();local before=M.observe_sprite(s);s.m_equipment.m_selectedWeapon=35
 local after=M.observe_sprite(s);local r=M.compare(before,after);eq(r.selectedChanged,true);eq(r.actionQueueCleared,false)
end)
test('cross actor comparison holds',function()
 local s=scene();local before=M.observe_sprite(s);s.m_id=2;local after=M.observe_sprite(s)
 eq(M.compare(before,after).status,'HOLD_INCOMPARABLE_ACTOR')
end)
test('incomplete comparison holds',function()
 local s=scene();local before=M.observe_sprite(s);local after=M.observe_sprite(s);after.quivers={}
 eq(M.compare(before,after).status,'HOLD_INCOMPLETE_COMPARISON')
end)
test('fist flagged not a real weapon identity',function()
 local s=scene({sel=10});local r=M.observe_sprite(s);eq(r.selectedInventoryKind,'FIST_INDEX');eq(r.weaponSwitchAuthorized,false)
end)
print('R2_READONLY_TESTS '..total..'/28 PASS; SOURCE ONLY, NO GAME CHANGES')
