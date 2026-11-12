"""Native Lua 5.4 test of R2 source-only defensive role advisories."""
import unittest
from pathlib import Path
from lua65_harness import run_case

ROOT = Path(__file__).resolve().parent
R2 = ROOT / 'BGXAI65_ROLE_COORDINATION_R2.lua'
BASELINE = (ROOT / 'BGXAI65_PRIORITY_POLICY.lua').read_text(encoding='utf-8')
SETUP = "local BGX65Policy=(function()\n" + BASELINE + "\nend)()\n"
PARTY = r'''
local area={}
local party={
{id=100,slot=0,classID=2,hp=14,maxhp=14,x=2930,y=591,guard=0,modal=0,area=area},
{id=101,slot=1,classID=1,hp=14,maxhp=14,x=3176,y=546,guard=1,modal=0,area=area},
{id=102,slot=2,classID=5,hp=6,maxhp=6,x=3192,y=582,guard=0,modal=0,area=area},
{id=103,slot=3,classID=3,hp=8,maxhp=8,x=3092,y=561,guard=1,modal=0,area=area},
}
local function eq(x,y) return x==y end
local function hit(v,a) return {victimID=v,attackerID=a or 999,signal='confirmed_hit',tick=1} end
local function intent(v,t) return {victimID=v,attackerID=999,signal='verified_attack_intent',verifiedTarget=t,tick=1} end
'''
# Definition stage: BGX65Policy is loaded before the R2 source within a fresh VM.

def case(s, assertions):
    run_case(SETUP + PARTY + s, assertions, R2)

class RoleR2Tests(unittest.TestCase):
    def test_live_snapshot_two_f_casters_not_melee(self):
        case('', r'''
local q=BGX65RoleR2.plan(party,{hit(102)},eq)
assert(q.mode=='ADVISORY_ONLY' and q.ordersSent==0)
assert(#q.frontlineAssignments==0 and #q.supportAssignments==2)
assert(q.supportAssignments[1].guardianID==101)
assert(q.supportAssignments[2].guardianID==103)
assert(q.supportAssignments[1].spellVerified==false)
''')

    def test_two_threats_split_casters_no_melee(self):
        case('', r'''
local q=BGX65RoleR2.plan(party,{hit(100),hit(102)},eq)
assert(#q.frontlineAssignments==0 and #q.supportAssignments==2)
assert(q.supportAssignments[1].victimID==102)
assert(q.supportAssignments[2].victimID==100)
assert(q.supportAssignments[1].guardianID~=q.supportAssignments[2].guardianID)
''')

    def test_full_health_f_tank_can_be_frontline_candidate(self):
        case('party[1].guard=1', r'''
local q=BGX65RoleR2.plan(party,{hit(102)},eq)
assert(#q.frontlineAssignments==0) -- P0 is player slot, not a guardian
party[2].classID=2
local z=BGX65RoleR2.plan(party,{hit(102)},eq)
assert(#z.frontlineAssignments==1 and z.frontlineAssignments[1].guardianID==101)
assert(#z.supportAssignments==1 and z.supportAssignments[1].guardianID==103)
''')

    def test_low_hp_frontliner_not_used(self):
        case('party[2].classID=2;party[2].hp=3', r'''
local q=BGX65RoleR2.plan(party,{hit(102)},eq)
assert(#q.frontlineAssignments==0)
assert(q.reserves[1].guardianID==101)
''')

    def test_half_hp_frontliner_not_used(self):
        case('party[2].classID=2;party[2].hp=7', r'''
local q=BGX65RoleR2.plan(party,{hit(102)},eq)
assert(#q.frontlineAssignments==0)
''')

    def test_mage_cannot_be_made_frontline_by_proximity(self):
        case('party[2].x=3191;party[2].y=582', r'''
local q=BGX65RoleR2.plan(party,{hit(102)},eq)
assert(#q.frontlineAssignments==0 and #q.supportAssignments==2)
''')

    def test_f_off_cannot_support(self):
        case('party[2].guard=0', r'''
local q=BGX65RoleR2.plan(party,{hit(102)},eq)
assert(#q.supportAssignments==1 and q.supportAssignments[1].guardianID==103)
''')

    def test_casting_modal_cannot_support(self):
        case('party[2].modal=3', r'''
local q=BGX65RoleR2.plan(party,{hit(102)},eq)
assert(#q.supportAssignments==1 and q.supportAssignments[1].guardianID==103)
''')

    def test_threatened_mage_cannot_support_other_victim(self):
        case('', r'''
local q=BGX65RoleR2.plan(party,{hit(101),hit(102)},eq)
assert(#q.supportAssignments==1 and q.supportAssignments[1].guardianID==103)
''')

    def test_party_attacker_rejected(self):
        case('', r'''
local q=BGX65RoleR2.plan(party,{{victimID=102,attackerID=100,signal='confirmed_hit'}},eq)
assert(#q.priorityOrder==0 and #q.supportAssignments==0 and q.rejections.party_attacker==1)
''')

    def test_unverified_pre_hit_rejected(self):
        case('', r'''
local q=BGX65RoleR2.plan(party,{intent(102,false)},eq)
assert(#q.priorityOrder==0 and #q.supportAssignments==0 and q.ordersSent==0)
''')

    def test_verified_pre_hit_still_passive(self):
        case('', r'''
local q=BGX65RoleR2.plan(party,{intent(102,true)},eq)
assert(#q.priorityOrder==1 and #q.supportAssignments==2)
assert(q.ordersSent==0 and q.supportAssignments[1].spellVerified==false)
''')

    def test_areas_must_match(self):
        case('party[2].area={};party[4].area={}', r'''
local q=BGX65RoleR2.plan(party,{hit(102)},eq)
assert(#q.frontlineAssignments==0 and #q.supportAssignments==0)
''')

    def test_missing_area_comparator_fails_closed(self):
        case('', r'''
local q=BGX65RoleR2.plan(party,{hit(102)},nil)
assert(#q.frontlineAssignments==0 and #q.supportAssignments==0)
''')

    def test_throwing_area_comparator_fails_closed(self):
        case('', r'''
local q=BGX65RoleR2.plan(party,{hit(102)},function()error('bad EEex')end)
assert(#q.frontlineAssignments==0 and #q.supportAssignments==0)
''')

    def test_duplicate_victim_one_threat(self):
        case('', r'''
local q=BGX65RoleR2.plan(party,{hit(102,999),hit(102,998)},eq)
assert(#q.priorityOrder==1 and q.rejections.duplicate_victim==1)
assert(#q.supportAssignments==2 and #q.frontlineAssignments==0)
''')

    def test_dead_supporter_excluded(self):
        case('party[2].hp=0', r'''
local q=BGX65RoleR2.plan(party,{hit(102)},eq)
assert(#q.supportAssignments==1 and q.supportAssignments[1].guardianID==103)
''')

    def test_missing_hp_supporter_excluded(self):
        case('party[2].maxhp=nil', r'''
local q=BGX65RoleR2.plan(party,{hit(102)},eq)
assert(#q.supportAssignments==1 and q.supportAssignments[1].guardianID==103)
''')

    def test_no_disallowed_engine_methods_or_writes(self):
        text = R2.read_text(encoding='utf-8')
        for s in ('setLocalInt(', 'ClearActions(', 'Attack(', 'Spell(', 'ForceSpell(', 'MoveToObject(',
                  'C:SetGlobal(', 'CreateCreature(', 'SetGlobal(', 'EEex_Hook', 'require(', 'io.', 'os.'):
            self.assertNotIn(s, text)
        self.assertIn('R.dispatchEnabled = false', text)
        self.assertIn('R.isInstalled = false', text)

if __name__ == '__main__':
    unittest.main()