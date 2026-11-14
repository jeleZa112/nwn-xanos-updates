-- Mock EEex objects; synthetic scenarios, no game installation.
local M=dofile('BGXAI073_CROSS_MODULE_AUDIT.lua')
local tests=0
local function check(x,m) assert(x,m); tests=tests+1 end
local function npc(class,kit,guard,hp,poly)
 return {m_typeAI={m_Class=class},m_baseStats={m_hitPoints=hp or 90},
  m_derivedStats={m_nMaxHitPoints=100,m_nKit=kit or 0,m_nLevel1=7,
   m_nLevel2=6,m_nLevel3=0,m_bPolymorphed=poly or 0},m_nModalState=0,
  getLocalInt=function(_,k) return k=='BGX38_GUARD' and guard or nil end}
end
local threat={verified=true,source='EEEX_EXPLICIT_ATTACK_ACTION',hostile=true,
 victim_is_party=true,attacker_is_party=false,same_area=true,
 attack_in_progress=true,attacker_id=312,victim_id=313}
local eps={verified=true,manual_command=false,heal_pending=false,
 ally_in_critical_danger=false,casting=false,singing=false,
 detecting_traps=false,queue_empty=true,idle=true}
local proposal={verified=true,target_source='EXACT_RESOLVED_ATTACKER_ID',target_id=312}
local config={opt_in=true,smart_guard=true}
local cases={
 {2,0,1,90,0,'FIGHTER'},
 {8,0,1,90,0,'FIGHTER_CLERIC'},
 {16,0,1,90,0,'FIGHTER_DRUID'},
 {11,0x40110000,1,90,1,'DRUID'},
 {21,0,1,90,0,'SHAMAN'},
 {1,0,1,90,0,'MAGE'},
 {5,0,1,90,0,'BARD'},
 {7,0,1,90,0,'FIGHTER_MAGE'},
 {2,0,0,90,0,'FIGHTER'},
 {2,0,1,5,0,'FIGHTER'},
 {2,0,1,90,1,'FIGHTER'},
 {11,0x4011,1,90,1,'DRUID'},
 {11,0x40110000,1,90,0,'DRUID'},
 {11,0xDEADBEEF,1,90,1,'DRUID'},
 {0,0,1,90,0,'UNKNOWN'},
}
for i,c in ipairs(cases) do
 local s=npc(c[1],c[2],c[3],c[4],c[5])
 local r=M.inspect(s,threat,eps,proposal,config)
 check(r.role.class_name==c[6],'class mismatch '..i)
 check(r.role.possible_interceptor==false,'unverified actions should hold '..i)
 check(r.arbitration.state=='HOLD','no dispatch without EPS evidence '..i)
 check(r.arbitration.allow_engine_action==false,'never execute '..i)
 check(r.engine_orders_sent==0 and r.game_changes==0,'never write '..i)
 check(r.snapshot.action_queue_verified==false,'queue unresolved '..i)
 check(r.snapshot.dual_verified==false,'dual unresolved '..i)
 check(r.kit_hint.kit_verified==false,'kit unresolved '..i)
 check(r.diagnostic_only==true,'diagnostic '..i)
end
local sh=M.inspect(npc(11,0x40110000,1,90,1),threat,eps,proposal,config)
check(sh.kit_hint.kit_name_hint=='SHAPESHIFTER','shapeshifter hint from CRE raw')
check(sh.role.kit_name=='UNKNOWN','hint not upgraded to proof')
check(sh.role.shape_melee_confirmed==false,'polymorph not verified werewolf')
local token=M.inspect(npc(11,0x4011,1,90,1),threat,eps,proposal,config)
check(token.kit_hint.reason=='KIT_IDS_TOKEN_NOT_CRE_RAW','KIT IDS vs CRE raw')
local dual=M.inspect(npc(1,0,1,90,0),threat,eps,proposal,config)
check(dual.role.dual_state=='UNKNOWN','levels do not certify dual status')
for _,s in ipairs({nil,{}, {m_typeAI={},m_baseStats={},m_derivedStats={}}}) do
 local r=M.inspect(s,threat,eps,proposal,config)
 check(r.engine_orders_sent==0 and r.arbitration.allow_engine_action==false,'missing sprite safe')
end
-- Even a maliciously forged model recommendation cannot be sent as a game action.
local adversarial={status='ADVISORY_ONLY',possible_interceptor=true,orders_sent=0,guard_toggle=1}
local a=dofile('BGXAI072_EPS_FIRST_ARBITER.lua').review(adversarial,threat,eps,proposal,config)
check(a.state=='CANDIDATE_REVIEW_ONLY','synthetic role can reach advisory')
check(a.allow_engine_action==false and a.engine_orders_sent==0,'advisory never dispatches')
print('BGXAI073_CROSS_MODULE_LUA_PASS '..tests)
