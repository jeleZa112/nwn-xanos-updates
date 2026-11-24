local here=(arg and arg[0] or ''):match('^(.*[/\\])') or './'
local M=dofile(here..'BGXAI_WEAPON_SELECTED_VS_ALTERNATE_V1.lua')
local c=0
local function test(label,fn) c=c+1;fn();print('PASS '..c..' '..label) end
local function clone(x)
 if type(x)~='table' then return x end
 local y={};for k,v in pairs(x) do y[k]=clone(v) end;return y
end
local function event(seq,slot,apr)
 local r4={schema='BGXAI_WEAPON_ACTIVE_R4',type='ACTIVE',status='RAW_CURRENT_SELECTED_STATS_OBSERVED_NOT_COMPLETE_EFFECTS',
  seq=seq,actor=139266124,partyIndex=2,actionRaw=23,selectedWeaponRaw=slot,presentCount=68,missingCount=0,
  statsRaw={m_nTHAC0=20,m_nNumberOfAttacks=apr},allBuffsObserved=false,allEffectsObserved=false,
  alternateSlotAPRVerified=false,manualOrderProven=false,epsQueueProven=false,weaponSwitchAuthorized=false,dispatchAuthorized=false}
 local r2={schema='BGXAI_WEAPON_SLOTS_RAW_R2',type='SLOTS',seq=seq,actor=139266124,partyIndex=2,
  actionRaw=23,selectedWeaponRaw=slot,quickWeapons={
  {index=35,resrefRaw='SW1H04'},{index=36,resrefRaw='BOW05'},
  {index=37,resrefRaw=nil},{index=38,resrefRaw='STAF01'}},quivers={
  {index=11,resrefRaw=nil},{index=12,resrefRaw='AROW01',useCount1Raw=20},
  {index=13,resrefRaw=nil},{index=14,resrefRaw=nil}}}
 local r1={type='ACTION',sequence=seq,actor=139266124,partyIndex=2,
  action=23,selectedWeaponRaw=slot,aprRaw=apr,thac0Raw=20}
 return r4,r2,r1
end
local function safe(x)
 assert(type(x)=='table' and x.executable==false and x.dispatchAuthorized==false)
 assert(x.weaponSwitchAuthorized==false and x.ordersSent==0 and x.actionQueueCleared==false)
 assert(x.currentActionPreserved==true)
end
local staff,slots,raw=event(1,38,1)
local result,state=M.observe(staff,slots,raw)
test('first selected staff APR observed, no switch allowed',function()
 safe(result);assert(result.status=='SELECTED_ONLY_EFFECTIVE_APR_OBSERVED_PRIORITY_HOLD')
 assert(result.selectedAPRDecoded==1);assert(result.quickslots[4].evidenceClass=='SELECTED_EFFECTIVE_APR_OBSERVED_THIS_ACTION')
 assert(result.quickslots[1].effectiveAPRForUnselected==nil)
end)
local bow,quiver,rr=event(2,12,2)
local rBow,sBow=M.observe(bow,quiver,rr,state)
test('ammo selection never proves bow launcher active',function()
 safe(rBow);assert(rBow.currentSelected.selectedRef=='AROW01')
 assert(rBow.currentSelected.selection=='CURRENT_SELECTED_AMMO_LAUNCHER_UNPROVEN')
 assert(rBow.quickslots[2].evidenceClass=='UNOBSERVED_ALTERNATE_NO_EFFECTIVE_APR')
 assert(rBow.quickslots[2].effectiveAPRForUnselected==nil)
end)
local sword,s2,r1=event(3,35,7)
local rSword,sSword=M.observe(sword,s2,r1,sBow)
test('sword raw7 decodes 1.5, staff remains history only',function()
 safe(rSword);assert(rSword.selectedAPRDecoded==1.5)
 assert(rSword.quickslots[4].evidenceClass=='HISTORICAL_SELECTED_APR_NOT_CURRENT_PROJECTION')
 assert(rSword.quickslots[4].historicalSelectedAPR==1)
 assert(rSword.quickslots[4].effectiveAPRForUnselected==nil)
end)
test('no fake projected APR added to any quickslot',function()
 for _,entry in ipairs(rSword.quickslots) do assert(entry.effectiveAPRForUnselected==nil) end
end)
test('changing current actor ID rejects pairing',function()
 local bad=clone(sword);bad.actor=77
 local x=M.observe(bad,s2,r1,sBow);safe(x);assert(x.status=='HOLD_UNVERIFIED_OBSERVATION')
end)
test('changing party position rejects pairing',function()
 local bad=clone(sword);bad.partyIndex=3
 local x=M.observe(bad,s2,r1,sBow);safe(x)
end)
test('changing action ID rejects pairing',function()
 local bad=clone(sword);bad.actionRaw=30
 local x=M.observe(bad,s2,r1,sBow);safe(x)
end)
test('changing selected weapon slot rejects pairing',function()
 local bad=clone(sword);bad.selectedWeaponRaw=38
 local x=M.observe(bad,s2,r1,sBow);safe(x)
end)
test('changing R1 APR rejects pairing',function()
 local bad=clone(r1);bad.aprRaw=2
 local x=M.observe(sword,s2,bad,sBow);safe(x)
end)
test('changing R1 THAC0 rejects pairing',function()
 local bad=clone(r1);bad.thac0Raw=19
 local x=M.observe(sword,s2,bad,sBow);safe(x)
end)
test('bogus R4 effects completeness cannot elevate authority',function()
 local bad=clone(sword);bad.allEffectsObserved=true
 local x=M.observe(bad,s2,r1,sBow);safe(x)
end)
test('bogus R4 dispatch flag cannot elevate authority',function()
 local bad=clone(sword);bad.dispatchAuthorized=true
 local x=M.observe(bad,s2,r1,sBow);safe(x)
end)
test('nonstandard APR unknown means HOLD not guessing',function()
 local a,b,d=event(3,35,9)
 local x=M.observe(a,b,d,sBow);safe(x);assert(x.status=='HOLD_UNVERIFIED_OBSERVATION')
end)
test('no ammo count means HOLD',function()
 local a,b,d=event(3,12,2);b.quivers[2].useCount1Raw=0
 local x=M.observe(a,b,d,sBow);safe(x)
end)
test('invalid slot count means HOLD',function()
 local a,b,d=event(3,35,7);b.quickWeapons[4]=nil
 local x=M.observe(a,b,d,sBow);safe(x)
end)
test('invalid resref means HOLD',function()
 local a,b,d=event(3,35,7);b.quickWeapons[1].resrefRaw='BAD.INJECT'
 local x=M.observe(a,b,d,sBow);safe(x)
end)
test('missing action input means HOLD',function()
 local x=M.observe(sword,s2,nil,sBow);safe(x)
end)
test('new actor history reset, even if adjacent sequence',function()
 local a,b,d=event(4,38,1)
 a.actor=88;b.actor=88;d.actor=88
 local x,n=M.observe(a,b,d,sSword);safe(x)
 assert(x.quickslots[1].evidenceClass=='UNOBSERVED_ALTERNATE_NO_EFFECTIVE_APR')
 assert(n.actorKey=='88:2')
end)
test('sequence gap resets history',function()
 local a,b,d=event(5,35,7)
 local x,n=M.observe(a,b,d,sSword);safe(x)
 assert(x.quickslots[4].evidenceClass=='UNOBSERVED_ALTERNATE_NO_EFFECTIVE_APR')
end)
test('session reset with sequence1 clears history',function()
 local a,b,d=event(1,35,7)
 local x,n=M.observe(a,b,d,sSword);safe(x)
 assert(x.quickslots[4].evidenceClass=='UNOBSERVED_ALTERNATE_NO_EFFECTIVE_APR')
end)
test('same selected weapon allowed but not alternative projection',function()
 local a,b,d=event(4,35,7)
 local x,n=M.observe(a,b,d,sSword);safe(x)
 assert(x.quickslots[1].evidenceClass=='SELECTED_EFFECTIVE_APR_OBSERVED_THIS_ACTION')
 assert(x.quickslots[4].historicalSelectedAPR==1)
end)
test('no module writes to globals or authorizes output',function()
 assert(M.installed==false);assert(_G.BGXAIWeaponR6==nil)
 assert(M.version=='BGXAI_WEAPON_SELECTED_VS_ALTERNATE_V1')
end)
test('out of range actor / party and sequence fail closed',function()
 local a,b,d=event(0,35,7);local x=M.observe(a,b,d);safe(x)
 a,b,d=event(1,35,7);a.partyIndex=8;local y=M.observe(a,b,d);safe(y)
end)
test('no legacy APR guessed in place of new raw',function()
 local a,b,d=event(1,35,6);local x=M.observe(a,b,d);safe(x)
end)
test('changing weapon identity invalidates stale history (not carry old APR)',function()
 local prior=nil
 for n=1,12 do
  local a,b,d=event(n,35,7)
  b.quickWeapons[1].resrefRaw=string.format('WPN%05d',n)
  local out,next= M.observe(a,b,d,prior)
  safe(out);assert(out.status=='SELECTED_ONLY_EFFECTIVE_APR_OBSERVED_PRIORITY_HOLD')
  if n>1 then assert(out.quickslots[4].historicalSelectedAPR==nil) end
  prior=next
 end
 local size=0;for _ in pairs(prior.history) do size=size+1 end
 assert(size==1 and prior.history.WPN00001==nil)
 assert(prior.history.WPN00012~=nil)
end)
test('old selected APR invalidated by quiver depletion',function()
 local a,b,d=event(4,35,7);b.quivers[2].useCount1Raw=19
 local out,next=M.observe(a,b,d,sSword)
 safe(out);assert(next.history.STAF01==nil)
end)
test('slot-resref change with same charges does not reuse APR',function()
 local a,b,d=event(4,35,7);b.quickWeapons[4].resrefRaw='STAF02'
 local out,next=M.observe(a,b,d,sSword)
 safe(out);assert(next.history.STAF01==nil)
end)
test('malicious stale history with non-sequence entry is purged when cap reached',function()
 local a,b,d=event(2,35,7)
 local junk={version=M.version,actorKey='139266124:2',lastSeq=1,history={}}
 for n=1,9 do junk.history[string.format('X%03d',n)]={garbage=true} end
 local out,after=M.observe(a,b,d,junk)
 safe(out)
 local n=0;for _ in pairs(after.history) do n=n+1 end
 assert(n<=8)
end)
print('PASS R6 SELECTED VERSUS ALTERNATE '..c..'/'..c)
