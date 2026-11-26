-- Lua 5.3+ synthetic-contract tests; no game is touched.
local function load_file(p)
 local f=assert(loadfile(p))
 return f()
end
local M=load_file('BGXAI/BUILD/WEAPON_INVENTORY_PREP_V1_20261126/BGXAI_WEAPON_INVENTORY_PREP_RO_V1.lua')
local count=0
local function eq(actual,expected)
 assert(actual==expected,'expected '..tostring(expected)..', got '..tostring(actual))
end
local function verify_no_orders(v)
 eq(v.ordersSent,0);eq(v.dispatchAuthorized,false);eq(v.weaponSwitchAuthorized,false)
 eq(v.executable,false);eq(v.readOnly,true)
 count=count+1
end
local function fixture()
 local inventory={status='RAW_BACKPACK_CAPTURED_IDENTITY_NOT_PROVEN',actorId=123,slots={}}
 for i=15,34 do inventory.slots[i]={slot=i,status='EMPTY'} end
 inventory.slots[17]={slot=17,status='PRESENT_RAW',resref='SW1H04',flagsRaw=1,
    useCount1Raw=0,useCount2Raw=0,useCount3Raw=0}
 local quick={}
 for i=35,38 do quick[i]={slot=i,status='EMPTY'} end
 quick[35]={slot=35,status='OCCUPIED',resref='BOW05'}
 local scene={actorId=123,tick=100,targetResref='GIBBER',snapshotId='snap1',
    itemModelProvenance='V3_V4_V5',protectionEvidenceVerified=true,
    currentWeaponScoreVerified=true,currentWeaponScore=3,
    weaponSlotCapacity=4,selectedWeaponStillSame=true,
    currentEquipmentFingerprintStable=true}
 local candidates={{sourceSlot=17,resref='SW1H04',snapshotId='snap1',
    modelProvenance='V3_V4_V5',predictedUtility=9,
    usabilityVerified=true,identifiedVerified=true,notCursedVerified=true,
    notQuestItemVerified=true,offhandCompatibilityVerified=true,
    ammoAndLauncherVerified=true,protectionsAccountedVerified=true}}
 return inventory,quick,scene,candidates
end
local function test(name,fn)
 local ok,err=pcall(fn)
 if not ok then error(name..': '..tostring(err),0) end
 print('PASS '..name)
end
test('fails_closed_on_missing_inputs',function()
 verify_no_orders(M.plan(nil,nil,nil,nil))
end)
test('observes_20_backpack_slots',function()
 local entries={}
 function entries:get(slot)
  if slot==16 then return {cResRef={get=function() return 'sw1h04' end},
    m_flags=1,m_useCount1=0,m_useCount2=0,m_useCount3=0} end
  return nil
 end
 local s={m_id=123,m_equipment={m_items=entries}}
 local v=M.observe(s)
 eq(v.status,'RAW_BACKPACK_CAPTURED_IDENTITY_NOT_PROVEN')
 eq(v.presentCount,1);eq(v.emptyCount,19)
 eq(v.slots[16].resref,'SW1H04');eq(v.slots[34].status,'EMPTY')
 verify_no_orders(v)
end)
test('observes_fail_closed_when_citem_incomplete',function()
 local e={}
 function e:get(slot) if slot==16 then return {m_flags=0} end end
 local v=M.observe({m_id=123,m_equipment={m_items=e}})
 eq(v.status,'HOLD_BACKPACK_SLOT_UNREADABLE')
 verify_no_orders(v)
end)
test('valid_free_quickslot_candidate_advice_only',function()
 local a,b,c,d=fixture()
 local v=M.plan(a,b,c,d)
 eq(v.status,'ADVISE_LOAD_BACKPACK_WEAPON_INTO_EMPTY_QUICKSLOT_RO')
 eq(v.sourceSlot,17);eq(v.toSlot,36);eq(v.candidateResref,'SW1H04')
 eq(v.itemTransferSemanticsVerified,false)
 eq(v.engineFinalAlternativeStatsVerified,false)
 verify_no_orders(v)
end)
test('all_occupied_never_overwrites',function()
 local a,b,c,d=fixture()
 for i=36,38 do b[i]={slot=i,status='OCCUPIED',resref='BOW0'..i} end
 local v=M.plan(a,b,c,d)
 eq(v.status,'HOLD_ALL_USABLE_QUICKSLOTS_OCCUPIED_NO_OVERWRITE')
 verify_no_orders(v)
end)
test('class_2_only_first_two_slots',function()
 local a,b,c,d=fixture()
 c.weaponSlotCapacity=2
 b[36]={slot=36,status='OCCUPIED',resref='SW1H01'}
 local v=M.plan(a,b,c,d)
 eq(v.status,'HOLD_ALL_USABLE_QUICKSLOTS_OCCUPIED_NO_OVERWRITE')
 verify_no_orders(v)
end)
test('insufficient_gain_keeps_equipped_weapon',function()
 local a,b,c,d=fixture()
 d[1].predictedUtility=4
 local v=M.plan(a,b,c,d)
 eq(v.status,'KEEP_CURRENT_NO_MEANINGFUL_GAIN')
 verify_no_orders(v)
end)
test('rejects_missing_effects_provenance',function()
 local a,b,c,d=fixture()
 c.protectionEvidenceVerified=false
 eq(M.plan(a,b,c,d).status,'HOLD_SCENE_OR_MODEL_NOT_PROVEN')
 verify_no_orders(M.plan(a,b,c,d))
end)
test('rejects_manual_or_snapshot_drift',function()
 local a,b,c,d=fixture()
 c.selectedWeaponStillSame=false
 eq(M.plan(a,b,c,d).status,'HOLD_EQUIPMENT_CONTEXT_DRIFT')
 verify_no_orders(M.plan(a,b,c,d))
end)
test('rejects_unidentified_weapon',function()
 local a,b,c,d=fixture()
 d[1].identifiedVerified=false
 eq(M.plan(a,b,c,d).status,'HOLD_CANDIDATE_NOT_VERIFIED')
 verify_no_orders(M.plan(a,b,c,d))
end)
test('rejects_quest_item',function()
 local a,b,c,d=fixture()
 d[1].notQuestItemVerified=false
 eq(M.plan(a,b,c,d).status,'HOLD_CANDIDATE_NOT_VERIFIED')
 verify_no_orders(M.plan(a,b,c,d))
end)
test('rejects_cursed_item',function()
 local a,b,c,d=fixture()
 d[1].notCursedVerified=false
 eq(M.plan(a,b,c,d).status,'HOLD_CANDIDATE_NOT_VERIFIED')
 verify_no_orders(M.plan(a,b,c,d))
end)
test('rejects_incompatible_offhand',function()
 local a,b,c,d=fixture()
 d[1].offhandCompatibilityVerified=false
 eq(M.plan(a,b,c,d).status,'HOLD_CANDIDATE_NOT_VERIFIED')
 verify_no_orders(M.plan(a,b,c,d))
end)
test('rejects_missing_ammo_launcher_proof',function()
 local a,b,c,d=fixture()
 d[1].ammoAndLauncherVerified=false
 eq(M.plan(a,b,c,d).status,'HOLD_CANDIDATE_NOT_VERIFIED')
 verify_no_orders(M.plan(a,b,c,d))
end)
test('rejects_duplicate_source_slot',function()
 local a,b,c,d=fixture()
 d[2]={}
 for k,v in pairs(d[1]) do d[2][k]=v end
 eq(M.plan(a,b,c,d).status,'HOLD_CANDIDATE_LIST_AMBIGUOUS')
 verify_no_orders(M.plan(a,b,c,d))
end)
test('rejects_duplicate_item_resrefs',function()
 local a,b,c,d=fixture()
 a.slots[20]={slot=20,status='PRESENT_RAW',resref='SW1H04'}
 eq(M.plan(a,b,c,d).status,'HOLD_RESREF_INSTANCE_AMBIGUITY')
 verify_no_orders(M.plan(a,b,c,d))
end)
test('rejects_unknown_snapshot_source_weapon',function()
 local a,b,c,d=fixture()
 a.slots[17]={slot=17,status='PRESENT_RAW',resref='AX1H04'}
 eq(M.plan(a,b,c,d).status,'HOLD_CANDIDATE_NOT_VERIFIED')
 verify_no_orders(M.plan(a,b,c,d))
end)
test('strict_non_mutating_contract_even_when_busy_flags_claim_safe',function()
 local a,b,c,d=fixture()
 c.manualOrderActive=false
 c.epsBusy=false
 c.safeActionBoundaryVerified=true
 c.engineFinalAlternativeStatsVerified=true
 local v=M.plan(a,b,c,d)
 eq(v.executable,false);eq(v.ordersSent,0);eq(v.dispatchAuthorized,false)
 eq(v.safeActionBoundaryVerified,false)
 verify_no_orders(v)
end)
print('PASS inventory planner contract assertions: '..count)
