"""Native Lua RED-before-GREEN checks: outstanding healing/ward actions.
The actual EET and its installed EPS 18.4 / BGXAI 066S are never touched.
"""
import unittest
from pathlib import Path
from lua65_harness import run_case
from native_066_fixture import PREAMBLE
R = Path(__file__).resolve().parent
SCRIPT = R/'M_BX43_066S_CAPABILITY_CANDIDATE.lua'

def check(setup, assertions):
    run_case(PREAMBLE+setup.replace('BGX66Team.capabilitySourceVerified=true;',''),
        '\nBGX66Team.capabilitySourceVerified=true;\n'+assertions,SCRIPT)

class OutstandingCasterRequests(unittest.TestCase):
    def test_pending_ward_prevents_new_heal(self):
        check('''g1.m_typeAI.m_Class=1; g2.m_typeAI.m_Class=3;
v2.m_baseStats.m_hitPoints=2;
BGX66Team.capabilitySourceVerified=true;
g2.locals.BGX66_S_WARD=1;''','''hit(v2)
assert(BGX66Caster.healPrepared==0)
assert(g2.locals.BGX66_S_HEAL_SLOT==nil and #writes==0 and #actions==0)''')

    def test_pending_heal_prevents_new_ward(self):
        check('''g1.m_typeAI.m_Class=1; g2.m_typeAI.m_Class=1;
v2.m_typeAI.m_Class=1; v2.locals.BGX38_GUARD=1;
v2.m_baseStats.m_hitPoints=2;
BGX66Team.capabilitySourceVerified=true;
v2.locals.BGX66_S_HEAL_SLOT=3;''','''hit(v2)
assert(BGX66Caster.wardPrepared==0)
assert(v2.locals.BGX66_S_WARD==nil and #writes==0 and #actions==0)''')

    def test_unknown_ward_status_fails_closed_for_heal(self):
        check('''g1.m_typeAI.m_Class=1; g2.m_typeAI.m_Class=3;
v2.m_baseStats.m_hitPoints=2;
BGX66Team.capabilitySourceVerified=true;
local previous=g2.getLocalInt
function g2:getLocalInt(k)
 if k=='BGX66_S_WARD' then error('no EEex local') end
 return previous(self,k)
end''','''hit(v2)
assert(BGX66Caster.healPrepared==0)
assert(g2.locals.BGX66_S_HEAL_SLOT==nil and #writes==0 and #actions==0)''')

    def test_unknown_heal_status_fails_closed_for_ward(self):
        check('''g1.m_typeAI.m_Class=1; g2.m_typeAI.m_Class=1;
v2.m_typeAI.m_Class=1; v2.locals.BGX38_GUARD=1;
v2.m_baseStats.m_hitPoints=2;
BGX66Team.capabilitySourceVerified=true;
local previous=v2.getLocalInt
function v2:getLocalInt(k)
 if k=='BGX66_S_HEAL_SLOT' then error('no EEex local') end
 return previous(self,k)
end''','''hit(v2)
assert(BGX66Caster.wardPrepared==0)
assert(v2.locals.BGX66_S_WARD==nil and #writes==0 and #actions==0)''')

if __name__=='__main__': unittest.main()
