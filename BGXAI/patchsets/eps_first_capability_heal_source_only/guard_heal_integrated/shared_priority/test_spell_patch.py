"""Native Lua / full-source regression of a *candidate* 066S capability patch.
No game installation and no claim of actual live EEex validation.
"""
from __future__ import annotations
import hashlib, pathlib, unittest, sys, re
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from lua65_harness import run_case
from native_066_fixture import PREAMBLE
import test_066s_caster_native as historical

LEGACY=HERE/'M_BX43_066S_CASTER_CANDIDATE.lua'
PATCH=HERE/'M_BX43_066S_CAPABILITY_CANDIDATE.lua'
BAF=HERE/'BGX66_CASTER_RECEIVER_SOURCE_ONLY.baf'

class SpellCapability(unittest.TestCase):
    def call(self,script,assertions,extra=''):
        # Fixture state before module load; capability provider after its init.
        marker='BGX66Caster.capabilityVerifier='
        if marker in extra:
            at=extra.index(marker)
            before=extra[:at]; after=extra[at:]
        else:
            before=extra; after=''
        run_case(PREAMBLE+before,after+'\n'+assertions,PATCH)
    def test_legacy_shaman_no_new_actions_by_default(self):
        self.call('','''assert(hit(v2)==false)
assert(BGX66Caster.healPrepared==0 and #actions==0 and #writes==0)''',
        'g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=21;v2.m_baseStats.m_hitPoints=2;')
    def test_spell_verified_shaman_allowed_instead_of_class_gate(self):
        self.call('','''assert(hit(v2)==false)
assert(BGX66Caster.healPrepared==1 and g2.locals.BGX66_S_HEAL_SLOT==3)
assert(#actions==0 and BGX66Caster.wardPrepared==0)''',
        "g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=21;v2.m_baseStats.m_hitPoints=2;"+
        "BGX66Caster.capabilityVerifier=function(o,spell) return o.m_id==105 and spell=='CLERIC_CURE_LIGHT_WOUNDS' end;")
    def test_modified_kit_without_class_hint_uses_real_spell(self):
        self.call('','''assert(hit(v2)==false)
assert(BGX66Caster.healPrepared==1 and g2.locals.BGX66_S_HEAL_SLOT==3)''',
        "g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=200;v2.m_baseStats.m_hitPoints=2;"+
        "BGX66Caster.capabilityVerifier=function(o,spell) return o.m_id==105 and spell=='CLERIC_CURE_LIGHT_WOUNDS' end;")
    def test_false_proof_blocks_legacy_healer(self):
        self.call('','''assert(hit(v2)==false)
assert(BGX66Caster.healPrepared==0 and #writes==0)''',
        "g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=3;v2.m_baseStats.m_hitPoints=2;"+
        "BGX66Caster.capabilityVerifier=function() return false end;")
    def test_invalid_proof_not_true(self):
        for value in ('nil','1','"yes"','{}'):
            with self.subTest(value=value):
                self.call('','''assert(hit(v2)==false)
assert(BGX66Caster.healPrepared==0 and #writes==0)''',
                "g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=3;v2.m_baseStats.m_hitPoints=2;"+
                f"BGX66Caster.capabilityVerifier=function() return {value} end;")
    def test_provider_error_never_dispatches(self):
        self.call('','''assert(hit(v2)==false)
assert(BGX66Caster.healPrepared==0 and #writes==0 and #actions==0)''',
        "g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=3;v2.m_baseStats.m_hitPoints=2;"+
        "BGX66Caster.capabilityVerifier=function() error('bad EEex') end;")
    def test_custom_spell_shield_role_without_class_assumption(self):
        self.call('','''assert(hit(v1)==false)
assert(BGX66Caster.wardPrepared==1 and v1.locals.BGX66_S_WARD==1 and #actions==0)''',
        "v1.m_typeAI.m_Class=4;v1.locals.BGX38_GUARD=1;v1.m_baseStats.m_hitPoints=2;"+
        "BGX66Caster.capabilityVerifier=function(o,spell) return o.m_id==102 and spell=='WIZARD_SHIELD' end;")
    def test_unavailable_spell_rejects_nearest_candidate_and_next_eligible(self):
        self.call('','''assert(hit(v2)==false)
assert(BGX66Caster.healPrepared==1 and g2.locals.BGX66_S_HEAL_SLOT==3)
assert(g1.locals.BGX66_S_HEAL_SLOT==nil)''',
        "g1.m_typeAI.m_Class=3;g2.m_typeAI.m_Class=3;v2.m_baseStats.m_hitPoints=2;"+
        "BGX66Caster.capabilityVerifier=function(o,spell) return o.m_id==105 and spell=='CLERIC_CURE_LIGHT_WOUNDS' end;")
    def test_f_guard_off_and_area_restriction_intact(self):
        self.call('','''assert(hit(v2)==false)
assert(BGX66Caster.healPrepared==0 and #actions==0)''',
        "g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=21;v2.m_baseStats.m_hitPoints=2;g1.locals.BGX38_GUARD=0;g2.locals.BGX38_GUARD=0;"+
        "BGX66Caster.capabilityVerifier=function() return true end;")

if __name__=='__main__':
    # Historical native tests are imported and run separately in runner.py
    unittest.main()