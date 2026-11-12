"""BGXAI 065 policy: execute real Lua 5.4 via shared lib; no actual EET writes."""
import unittest
from pathlib import Path
from lua65_harness import run_case

HERE=Path(__file__).resolve().parent
SOURCE=HERE/'BGXAI65_PRIORITY_POLICY.lua'
BASE=r'''
local A={} local B={}
function eq(a,b)return a==b end
local party={
  {id=101,slot=0,area=A,x=0,y=0,classID=2,hp=80,maxhp=80,guard=0,modal=0},
  {id=102,slot=1,area=A,x=10,y=0,classID=1,hp=10,maxhp=20,guard=0,modal=0},
  {id=103,slot=2,area=A,x=20,y=0,classID=3,hp=11,maxhp=20,guard=0,modal=0},
  {id=104,slot=3,area=A,x=30,y=0,classID=2,hp=60,maxhp=60,guard=1,modal=0},
  {id=105,slot=4,area=A,x=40,y=0,classID=7,hp=30,maxhp=30,guard=1,modal=0},
  {id=106,slot=5,area=A,x=50,y=0,classID=11,hp=45,maxhp=45,guard=0,modal=0},
}
local function hit(id,attacker,tick) return {victimID=id,attackerID=attacker or 999,signal='confirmed_hit',tick=tick or 10} end
local function intent(id,attacker,tick,verified) return {victimID=id,attackerID=attacker or 998,signal='verified_attack_intent',verifiedTarget=verified,tick=tick or 10} end
'''

class NativePriorityTests(unittest.TestCase):
    def test_01_class_roles_composites(self):
        run_case('',"""assert(BGX65Policy.classRole(1)=='arcane');assert(BGX65Policy.classRole(3)=='healer');
assert(BGX65Policy.classRole(14)=='arcane_healer');assert(BGX65Policy.classRole(17)=='arcane_healer')
assert(BGX65Policy.classRole(2)=='tank');assert(BGX65Policy.classRole(7)=='arcane');
assert(BGX65Policy.classRole(11)=='healer');assert(BGX65Policy.classRole(19)=='arcane')
assert(BGX65Policy.classRole(5)=='arcane');assert(BGX65Policy.classRole(nil)=='unknown')""",SOURCE)
    def test_02_critical_hp_overrides_class(self):
        run_case(BASE+"party[1].hp=3", "assert(BGX65Policy.urgency(party[1]).tier==1)",SOURCE)
    def test_03_critical_ratio_overrides_class(self):
        run_case(BASE+"party[1].hp=12;party[1].maxhp=100", "assert(BGX65Policy.urgency(party[1]).tier==1)",SOURCE)
    def test_04_spellcaster_over_wounded_rogue(self):
        run_case(BASE+"party[1].classID=4;party[1].hp=35;party[1].maxhp=80", "assert(BGX65Policy.urgency(party[1]).tier==3);assert(BGX65Policy.urgency(party[2]).tier==2)",SOURCE)
    def test_05_healthy_tank_last(self):
        run_case(BASE,"assert(BGX65Policy.urgency(party[1]).tier==5);assert(BGX65Policy.urgency(party[2]).tier==2)",SOURCE)
    def test_06_dead_or_invalid_hp_excluded(self):
        run_case(BASE,"assert(BGX65Policy.urgency({hp=0,maxhp=20,classID=1})==nil);assert(BGX65Policy.urgency({hp=-5,maxhp=20,classID=1})==nil)",SOURCE)
    def test_07_unknown_stats_neutral_no_fake_critical(self):
        run_case(BASE,"local x=BGX65Policy.urgency({hp=nil,maxhp=nil,classID=999});assert(x.tier==4 and x.hpPercent==nil)",SOURCE)
    def test_08_multithreat_critical_before_mage_before_tank(self):
        run_case(BASE+"party[3].hp=3", """local q=BGX65Policy.plan(party,{hit(101,998),hit(102,997),hit(103,996)},eq)
assert(#q.priorityOrder==3);assert(q.priorityOrder[1].victimID==103 and q.priorityOrder[1].tier==1)
assert(q.priorityOrder[2].victimID==102 and q.priorityOrder[3].victimID==101)
assert(#q.assignments==2 and #q.unassigned==1 and q.ordersSent==0)""",SOURCE)
    def test_09_one_threat_chooses_nearest_only(self):
        run_case(BASE,"""local q=BGX65Policy.plan(party,{hit(102,999)},eq)
assert(#q.assignments==1 and q.assignments[1].guardianID==104)
assert(#q.supportCandidates==1 and q.supportCandidates[1].guardianID==105)
assert(q.supportCandidates[1].suggestedRole=='control_candidate')""",SOURCE)
    def test_10_two_victims_two_distinct_defenders(self):
        run_case(BASE+"party[3].hp=2", """local q=BGX65Policy.plan(party,{hit(101,997),hit(103,996)},eq)
assert(#q.assignments==2 and q.assignments[1].guardianID~=q.assignments[2].guardianID)
assert(q.assignments[1].victimID==103 and q.assignments[2].victimID==101)""",SOURCE)
    def test_11_different_areas_fails_closed(self):
        run_case(BASE+"party[4].area=B;party[5].area=B", """local q=BGX65Policy.plan(party,{hit(102,997)},eq)
assert(#q.assignments==0 and #q.unassigned==1)""",SOURCE)
    def test_12_missing_area_comparator_fails_closed(self):
        run_case(BASE,"local q=BGX65Policy.plan(party,{hit(102,997)},nil);assert(#q.assignments==0)",SOURCE)
    def test_13_area_api_throws_fails_closed(self):
        run_case(BASE,"local q=BGX65Policy.plan(party,{hit(102,997)},function()error('bad userdata')end);assert(#q.assignments==0)",SOURCE)
    def test_14_guardian_F_off_not_used(self):
        run_case(BASE+"party[4].guard=0", "local q=BGX65Policy.plan(party,{hit(102,997)},eq);assert(q.assignments[1].guardianID==105)",SOURCE)
    def test_15_guardian_modal_not_used(self):
        run_case(BASE+"party[4].modal=3", "local q=BGX65Policy.plan(party,{hit(102,997)},eq);assert(q.assignments[1].guardianID==105)",SOURCE)
    def test_16_party_attacker_blocked(self):
        run_case(BASE,"local q=BGX65Policy.plan(party,{hit(102,101)},eq);assert(#q.assignments==0 and q.rejections.party_attacker==1)",SOURCE)
    def test_17_unknown_victim_blocked(self):
        run_case(BASE,"local q=BGX65Policy.plan(party,{hit(999,998)},eq);assert(#q.assignments==0 and q.rejections.victim_not_in_party==1)",SOURCE)
    def test_18_unverified_intent_blocked(self):
        run_case(BASE,"local q=BGX65Policy.plan(party,{intent(102,999,10,false)},eq);assert(#q.assignments==0 and q.rejections.target_not_verified==1)",SOURCE)
    def test_19_verified_intent_advisory_no_orders(self):
        run_case(BASE,"""local q=BGX65Policy.plan(party,{intent(102,999,10,true)},eq)
assert(#q.assignments==1 and q.ordersSent==0 and q.mode=='ADVISORY_ONLY')
assert(q.assignments[1].signal=='verified_attack_intent')""",SOURCE)
    def test_20_intent_superseded_by_confirmed_hit(self):
        run_case(BASE,"""local q=BGX65Policy.plan(party,{intent(102,999,10,true),hit(102,999,11)},eq)
assert(#q.priorityOrder==1 and q.priorityOrder[1].signal=='confirmed_hit')
assert(q.rejections.duplicate_victim==1)""",SOURCE)
    def test_20b_one_victim_two_attackers_not_two_guards(self):
        run_case(BASE,"""local q=BGX65Policy.plan(party,{hit(102,998,10),hit(102,997,11)},eq)
assert(#q.priorityOrder==1 and #q.assignments==1)
assert(q.rejections.duplicate_victim==1)""",SOURCE)
    def test_21_unverified_signal_fails_closed(self):
        run_case(BASE,"local q=BGX65Policy.plan(party,{{victimID=102,attackerID=998,signal='I_think_attack'}},eq);assert(#q.assignments==0)",SOURCE)
    def test_22_tie_break_slot(self):
        run_case(BASE+"party[4].x=0;party[5].x=20", "local q=BGX65Policy.plan(party,{hit(102,998)},eq);assert(q.assignments[1].guardianID==104)",SOURCE)
    def test_23_snapshot_reads_actual_fields_without_writes(self):
        run_case(BASE+r'''
local objs={}
for _,m in ipairs(party) do
 local o={m_id=m.id,m_pos={x=m.x,y=m.y},m_typeAI={m_Class=m.classID},
  m_baseStats={m_hitPoints=m.hp},m_derivedStats={m_nMaxHitPoints=m.maxhp},
  m_pArea=m.area,m_nModalState=m.modal,guard=m.guard}
 function o:getLocalInt(k) assert(k=='BGX38_GUARD');return self.guard end
 function o:setLocalInt(...)error('ILLEGAL_GAME_WRITE')end
 objs[m.id]=o
end
function EEex_Sprite_GetInPortraitID(i)return party[i+1] and party[i+1].id end
function EEex_GameObject_Get(id)return objs[id]end
''',"""local ps=BGX65Policy.partySnapshot();assert(#ps==6)
assert(ps[2].classID==1 and ps[2].hp==10 and ps[2].maxhp==20)
assert(ps[4].guard==1 and ps[4].area==party[4].area)
assert(BGX65Policy.dispatchEnabled==false and BGX65Policy.isInstalled==false)""",SOURCE)
    def test_24_snapshot_handles_missing_derivedstats(self):
        run_case(BASE+r'''
function EEex_Sprite_GetInPortraitID(i) if i==0 then return 112 end end
function EEex_GameObject_Get(id) return {m_id=id,m_typeAI={m_Class=1},
 m_baseStats={m_hitPoints=4},m_nModalState=0,m_pos={x=1,y=2},m_pArea=A,
 getLocalInt=function()return 0 end} end
''',"""local p=BGX65Policy.partySnapshot();assert(#p==1);assert(p[1].maxhp==nil)
assert(BGX65Policy.urgency(p[1]).tier==2)""",SOURCE)
    def test_25_observe_hit_snapshot_multithreat_critical_first(self):
        run_case(BASE+r'''
local objs={}
for _,m in ipairs(party) do
 local o={m_id=m.id,m_pos={x=m.x,y=m.y},m_typeAI={m_Class=m.classID},
 m_baseStats={m_hitPoints=m.hp},m_derivedStats={m_nMaxHitPoints=m.maxhp},
 m_pArea=m.area,m_nModalState=m.modal,guard=m.guard}
 function o:getLocalInt(k)return self.guard end
 function o:setLocalInt(...)error('ILLEGAL_GAME_WRITE')end
 objs[m.id]=o
end
function EEex_Sprite_GetInPortraitID(i)return party[i+1] and party[i+1].id end
function EEex_GameObject_Get(id)return objs[id]end
EEex_UDEqual=eq
objs[103].m_baseStats.m_hitPoints=2
''',"""local a=BGX65Policy.observeHit({target_id=101,actor_id=998},10)
local b=BGX65Policy.observeHit({target_id=103,actor_id=997},11)
assert(b.priorityOrder[1].victimID==103 and b.priorityOrder[1].tier==1)
assert(BGX65Policy.lastPlan.ordersSent==0 and BGX65Policy.lastPlan.firstVictimID==103)
assert(#BGX65Policy.observed==2)""",SOURCE)
    def test_26_window_expiration(self):
        run_case(BASE+r'''
function EEex_Sprite_GetInPortraitID(i)return nil end
function EEex_GameObject_Get(i)return nil end
EEex_UDEqual=eq
''',"""BGX65Policy.observeHit({target_id=101,actor_id=998},10)
BGX65Policy.observeHit({target_id=102,actor_id=997},100)
assert(#BGX65Policy.observed==1 and BGX65Policy.observed[1].victimID==102)""",SOURCE)
    def test_27_observation_failure_no_writes(self):
        run_case(BASE,"""local a,err=BGX65Policy.observeHit({target_id=101,actor_id=998},nil)
assert(a==nil and err=='clock_unavailable');assert(#BGX65Policy.observed==0)
assert(BGX65Policy.dispatchEnabled==false)""",SOURCE)
    def test_27a_unverified_proactive_observation_refused(self):
        run_case(BASE,"""local q,why=BGX65Policy.observeIntent({target_id=102,actor_id=998,verifiedTarget=false},10)
assert(q==nil and why=='target_not_verified' and #BGX65Policy.observed==0)""",SOURCE)
    def test_27b_authoritative_intent_is_advisory_only(self):
        run_case(BASE+r'''
function EEex_Sprite_GetInPortraitID(i) if party[i+1] then return party[i+1].id end end
function EEex_GameObject_Get(id)
 for _,m in ipairs(party) do if m.id==id then
 return {m_id=id,m_pos={x=m.x,y=m.y},m_pArea=m.area,m_nModalState=m.modal,
 m_typeAI={m_Class=m.classID},m_baseStats={m_hitPoints=m.hp},
 m_derivedStats={m_nMaxHitPoints=m.maxhp},getLocalInt=function()return m.guard end}
 end end
end
EEex_UDEqual=eq
''',"""local q=BGX65Policy.observeIntent({target_id=102,actor_id=999,verifiedTarget=true},100)
assert(q.ordersSent==0 and #q.assignments==1)
assert(q.priorityOrder[1].signal=='verified_attack_intent')""",SOURCE)
    def test_27c_real_hit_upgrades_same_target_intent(self):
        run_case(BASE+r'''
function EEex_Sprite_GetInPortraitID(i) if party[i+1] then return party[i+1].id end end
function EEex_GameObject_Get(id)
 for _,m in ipairs(party) do if m.id==id then
 return {m_id=id,m_pos={x=m.x,y=m.y},m_pArea=m.area,m_nModalState=m.modal,
 m_typeAI={m_Class=m.classID},m_baseStats={m_hitPoints=m.hp},
 m_derivedStats={m_nMaxHitPoints=m.maxhp},getLocalInt=function()return m.guard end}
 end end
end
EEex_UDEqual=eq
''',"""BGX65Policy.observeIntent({target_id=102,actor_id=999,verifiedTarget=true},100)
local q=BGX65Policy.observeHit({target_id=102,actor_id=998},101)
assert(#q.priorityOrder==1 and q.priorityOrder[1].signal=='confirmed_hit')
assert(q.priorityOrder[1].attackerID==998 and q.ordersSent==0)""",SOURCE)
    def test_28_no_observer_action_API_calls(self):
        run_case(BASE+r'''
function Attack(...) error('forbidden')end
function AttackReevaluate(...) error('forbidden')end
function ProtectObject(...) error('forbidden')end
function MoveToObject(...) error('forbidden')end
function ClearActions(...) error('forbidden')end
''',"""local q=BGX65Policy.plan(party,{hit(102,999)},eq)
assert(q.mode=='ADVISORY_ONLY' and q.ordersSent==0)""",SOURCE)

if __name__=='__main__':unittest.main()
