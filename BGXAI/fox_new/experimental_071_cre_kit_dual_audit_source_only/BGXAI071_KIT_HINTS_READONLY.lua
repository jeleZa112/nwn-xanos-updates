-- BGXAI 071: passive, advisory-only interpretation of CRE kit raw values.
-- SOURCE ONLY. Does not run in game, register hooks, alter locals, or issue commands.
-- A CRE raw kit (e.g. 0x40110000) is NOT the KIT.IDS trigger token (0x4011).
-- These standard mappings are merely hints pending current installed KIT.IDS /
-- KITLIST.2DA verification; modded installations may override or extend them.
local M={version='0.3.38-071-KIT-HINTS-READONLY-SOURCE-ONLY'}
local STANDARD={
 [0x40010000]={'BERSERKER',2},[0x40020000]={'WIZARD_SLAYER',2},
 [0x40030000]={'KENSAI',2},[0x40040000]={'CAVALIER',6},
 [0x40050000]={'INQUISITOR',6},[0x40060000]={'UNDEAD_HUNTER',6},
 [0x40070000]={'ARCHER',12},[0x40080000]={'STALKER',12},
 [0x40090000]={'BEASTMASTER',12},[0x400A0000]={'ASSASSIN',4},
 [0x400B0000]={'BOUNTY_HUNTER',4},[0x400C0000]={'SWASHBUCKLER',4},
 [0x400D0000]={'BLADE',5},[0x400E0000]={'JESTER',5},
 [0x400F0000]={'SKALD',5},[0x40100000]={'TOTEMIC_DRUID',11},
 [0x40110000]={'SHAPESHIFTER',11},[0x40120000]={'AVENGER',11},
 [0x40130000]={'TALOS',3},[0x40140000]={'HELM',3},
 [0x40150000]={'LATHANDER',3},[0x40200000]={'BLACKGUARD',6},
 [0x40210000]={'SHADOWDANCER',4},[0x40220000]={'DWARVEN_DEFENDER',2},
 [0x40230000]={'DRAGON_DISCIPLE',19},[0x40240000]={'DARK_MOON',20},
 [0x40250000]={'SUN_SOUL',20},
}
local function uint(x)
 return type(x)=='number' and x==x and x==math.floor(x) and x>=0 and x<=4294967295
end
function M.hint(snapshot)
 local r={version=M.version,status='ADVISORY_ONLY',
          kit_name_hint='UNKNOWN',kit_verified=false,
          form_verified=false,dual_verified=false,
          actions_verified=false,orders_sent=0,hook_registered=false,
          reason='RAW_KIT_UNKNOWN_OR_MODDED'}
 if type(snapshot)~='table' then r.reason='SNAPSHOT_UNAVAILABLE';return r end
 local kit=snapshot.kit_raw
 if not uint(kit) then r.reason='RAW_KIT_UNAVAILABLE';return r end
 if kit==0 then r.reason='NO_KIT_RAW';return r end
 if kit==0x40000000 then r.kit_name_hint='TRUECLASS';r.reason='STANDARD_HINT_ONLY';return r end
 -- Standard mage-school flags and mod kits require a separately audited table.
 if kit==0x4011 then r.reason='KIT_IDS_TOKEN_NOT_CRE_RAW';return r end
 local v=STANDARD[kit]
 if not v then return r end
 if snapshot.class_id~=v[2] then
   r.reason='CLASS_KIT_FAMILY_MISMATCH'; return r
 end
 r.kit_name_hint=v[1]
 r.reason='STANDARD_KIT_HINT_ONLY_NOT_VERIFIED'
 return r
end
function M.hint_for_069(snapshot)
 -- Never turn a raw kit hint into a verified fact used for F-guard or healing.
 local h=M.hint(snapshot)
 return {kit={verified=false,name='UNKNOWN'},
         form={verified=false,name='UNKNOWN',melee_verified=false},
         dual=nil,healing={verified=false,usable_now=false},
         actions={verified=false},combat={verified=false},
         kit_hint=h.kit_name_hint,confidence='RAW_KIT_ADVISORY'}
end
return M
