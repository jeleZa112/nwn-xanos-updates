-- Offline native Lua mocks for BGXAI R4. No EEex/game dependency.
local folder=(arg and arg[0] or ''):match('^(.*[/\\])') or './'
local R=dofile(folder..'BGXAI_WEAPON_ACTIVE_R4_READONLY.lua')
local n=0
local function test(name,fn) fn();n=n+1;print('PASS '..name) end
local function equal(a,b)assert(a==b,tostring(a)..' ~= '..tostring(b))end
local function mock()
 local stats={m_nNumberOfAttacks=2,m_nTHAC0=17,m_nLevel1=3,m_nLevel2=0,m_nLevel3=0,
  m_nKit=0,m_nSTR=15,m_nSTRExtra=0,m_nDEX=16,m_nDamageBonus=0,
  m_nMeleeTHAC0Bonus=0,m_nMeleeDamageBonus=0,m_nMissileTHAC0Bonus=0,
  m_nMissileDamageBonus=0,m_nHitBonus=0,m_bImprovedHaste=0,m_nLuck=0,
  m_nLevelDrain=0,m_THAC0BonusRight=0,m_THAC0BonusLeft=0,m_DamageBonusRight=0,
  m_DamageBonusLeft=0,m_nProficiencyLongSword=1,m_nProficiencyShortBow=2,
  m_nProficiencyQuarterStaff=0,m_nProficiencySwordAndShield=0,
  m_nProficiency2Handed=0,m_nProficiencySingleWeapon=0,m_nProficiency2Weapon=0}
 local s={m_id=139135050,m_equipment={m_selectedWeapon=12,m_selectedWeaponAbility=0}}
 return s,{m_actionID=30},stats
end
local function snapshot() local s,a,stats=mock();return R.observe(s,a,2,function() return stats end) end
test('actor high-bit-friendly 31-bit raw index',function() local v=snapshot();equal(v.actorId,139135050);equal(v.partyIndex,2)end)
test('selected ammo ID stays selected index, not launcher proof',function()local v=snapshot();equal(v.selectedWeaponRaw,12);equal(v.selectedOnly,true);equal(v.alternateSlotAPRVerified,false)end)
test('selected APR2 decoded as 2, not added twice',function()local v=R.classifyObservedEvidence(snapshot());equal(v.selectedAPRIfStandard,2);equal(v.projectionToOtherSlotsAllowed,false)end)
test('encoded APR7 decoded as one point five',function()local s,a,stats=mock();stats.m_nNumberOfAttacks=7;local v=R.classifyObservedEvidence(R.observe(s,a,2,function()return stats end));equal(v.selectedAPRIfStandard,1.5)end)
test('raw kit levels and 3 weapon proficiency fields available',function()local v=snapshot();equal(v.fields.m_nLevel1,3);equal(v.fields.m_nProficiencyLongSword,1);equal(v.fields.m_nProficiencyShortBow,2);equal(v.fields.m_nProficiencyQuarterStaff,0)end)
test('no completeness permission from raw stats',function()local v=snapshot();equal(v.allBuffsObserved,false);equal(v.manualOrderProven,false);equal(v.epsQueueProven,false);equal(v.dispatchAuthorized,false)end)
test('missing EEex API fails closed',function()local s,a=mock();local v=R.observe(s,a,2,false);equal(v.status,'HOLD_ACTIVE_STATS_API_MISSING')end)
test('stats pointer error fails closed',function()local s,a=mock();local v=R.observe(s,a,2,function()error('TEST')end);equal(v.status,'HOLD_ACTIVE_STATS_ACCESS_FAILED')end)
test('missing current APR fails closed, false not zero',function()local s,a,stats=mock();stats.m_nNumberOfAttacks=nil;local v=R.observe(s,a,2,function()return stats end);equal(v.status,'HOLD_APR_OR_SELECTED_SLOT_MISSING');equal(v.fields.m_nNumberOfAttacks,false)end)
test('zero APR is a real observed zero not absence',function()local s,a,stats=mock();stats.m_nNumberOfAttacks=0;local v=R.observe(s,a,2,function()return stats end);equal(v.fields.m_nNumberOfAttacks,0);equal(R.classifyObservedEvidence(v).selectedAPRIfStandard,0)end)
test('known haste key invalidates advice without action',function()local a=snapshot();local b=snapshot();b.fields.m_bImprovedHaste=1;local c=R.compare(a,b);equal(c.changeCount,1);equal(c.status,'INVALIDATE_CACHED_WEAPON_ADVICE_KEEP_ACTION');equal(c.dispatchAuthorized,false)end)
test('strength buff invalidates cached proposal',function()local a=snapshot();local b=snapshot();b.fields.m_nSTR=19;equal(R.compare(a,b).changeCount,1)end)
test('proficiency change invalidates cached proposal',function()local a=snapshot();local b=snapshot();b.fields.m_nProficiencyShortBow=3;equal(R.compare(a,b).changeCount,1)end)
test('raw item selection changes invalidate proposal',function()local a=snapshot();local b=snapshot();b.selectedWeaponRaw=35;equal(R.compare(a,b).changedFields[1],'SELECTION_CHANGED')end)
test('unchanged samples do not certify all buffs',function()local c=R.compare(snapshot(),snapshot());equal(c.status,'RAW_SELECTED_STATS_UNCHANGED_NOT_PROOF_OF_ALL_EFFECTS');equal(c.allEffectsObserved,false)end)
test('wrong actor cannot be compared',function()local a=snapshot();local b=snapshot();b.actorId=321;equal(R.compare(a,b).status,'HOLD_UNCOMPARABLE_SNAPSHOTS')end)
test('out-of-range field dropped not clamped to false value 0',function()local s,a,stats=mock();stats.m_nNumberOfAttacks=10000;local v=R.observe(s,a,2,function()return stats end);equal(v.fields.m_nNumberOfAttacks,10000);equal(R.classifyObservedEvidence(v).status,'HOLD_APR_ENCODING_UNKNOWN')end)
test('bad selected weapon holds rather than ranking',function()local s,a,stats=mock();s.m_equipment=nil;local v=R.observe(s,a,2,function()return stats end);equal(v.status,'HOLD_APR_OR_SELECTED_SLOT_MISSING')end)
test('missing class level remains missing only',function()local s,a,stats=mock();stats.m_nLevel1=nil;local v=R.observe(s,a,2,function()return stats end);equal(v.fields.m_nLevel1,false);equal(v.allBuffsObserved,false)end)
test('no game mutation on snapshots',function()local s,a,stats=mock();R.observe(s,a,2,function()return stats end);equal(s.m_equipment.m_selectedWeapon,12);equal(a.m_actionID,30);equal(stats.m_nNumberOfAttacks,2)end)
print('BGXAI_R4_CORE_OFFLINE_PASS '..n..'/'..n)
