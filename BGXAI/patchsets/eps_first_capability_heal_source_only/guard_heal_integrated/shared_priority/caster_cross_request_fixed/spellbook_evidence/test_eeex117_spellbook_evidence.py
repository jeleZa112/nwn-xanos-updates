"""Native Lua 5.4 source-only tests for genuine EEex 1.1.7 spellbook READ API.
No EEex runtime/game write proof. Raw memorized entry != castable in game.
"""
from pathlib import Path
import unittest, re, csv, hashlib
from lua65_harness import run_case
from native_066_fixture import PREAMBLE
R=Path(__file__).resolve().parent
NEW=R/'M_BX43_066S_EEEX_BOOK_EVIDENCE_CANDIDATE.lua'
OLD=R/'M_BX43_066S_CAPABILITY_CANDIDATE.lua'
MOD=R/'BGX66_EEEX117_SPELLBOOK_EVIDENCE.lua'

# Mocks only the actual documented EEex 1.1.7 list iteration and structures.
NATIVE='''
local function book(records)
 return {getReference=function(self,index)
  assert(index==0,'spell level must be 0 for 1st-level spell')
  return records
 end}
end
local function spell(res,flags)
 return {m_spellId={get=function(self)return res end},m_flags=flags}
end
function EEex_Utility_IterateCPtrList(list,func)
 for _,rec in ipairs(list) do if func(rec) then return end end
end
'''

def run(assertions,setup='',native=True):
    run_case(PREAMBLE+(NATIVE if native else '')+setup,assertions,NEW)

class SpellbookEvidence(unittest.TestCase):
    def test_saved_EET_resref_map(self):
        with (R/'SPELL_POLICY_CATALOG_469.csv').open(encoding='utf-8-sig') as handle:
            rows=list(csv.DictReader(handle))
        a={r['ids_symbol']:r for r in rows}
        self.assertEqual((a['CLERIC_CURE_LIGHT_WOUNDS']['resref'],a['CLERIC_CURE_LIGHT_WOUNDS']['ids_number']),('SPPR103','1103'))
        self.assertEqual((a['WIZARD_SHIELD']['resref'],a['WIZARD_SHIELD']['ids_number']),('SPWI114','2114'))

    def test_priest_ready_vs_consumed(self):
        run('''local ev,err=BGX66SpellbookEvidence.read(g2,'CLERIC_CURE_LIGHT_WOUNDS')
assert(err==nil and ev.resref=='SPPR103' and ev.ready_count==2)
assert(ev.book_record_read==true and ev.castable_now_proven==false)
assert(ev.manual_order_origin_proven==false and ev.queue_empty_proven==false)
assert(#writes==0 and #actions==0)''',
'''g2.m_memorizedSpellsPriest=book({spell('SPPR103',1),spell('SPPR103',0),spell('SPPR103',3),spell('SPPR104',1)})''')

    def test_wizard_book_ready_and_case_normalization(self):
        run('''local ev=BGX66SpellbookEvidence.read(v1,'WIZARD_SHIELD')
assert(ev and ev.resref=='SPWI114' and ev.ready_count==1)
assert(ev.class_kit_dual_active_proven==false and #writes==0)''',
'''v1.m_memorizedSpellsMage=book({spell('spwi114',1),spell('SPWI101',1)})''')

    def test_expended_spell_yields_zero_not_unknown(self):
        run('''local ev,err=BGX66SpellbookEvidence.read(g2,'CLERIC_CURE_LIGHT_WOUNDS')
assert(err==nil and ev.ready_count==0 and ev.book_record_read==true)''',
'''g2.m_memorizedSpellsPriest=book({spell('SPPR103',0),spell('SPPR103',2)})''')

    def test_empty_valid_book_yields_zero(self):
        run('''local ev=BGX66SpellbookEvidence.read(g2,'CLERIC_CURE_LIGHT_WOUNDS')
assert(ev and ev.ready_count==0)''','g2.m_memorizedSpellsPriest=book({})')

    def test_spontaneous_shaman_unreadable_is_unknown_not_false_class(self):
        run('''local ev,err=BGX66SpellbookEvidence.read(g2,'CLERIC_CURE_LIGHT_WOUNDS')
assert(ev==nil and err=='spellbook_read_failed')''','g2.m_typeAI.m_Class=21;')

    def test_dual_class_memorization_does_not_prove_castability(self):
        run('''local ev=BGX66SpellbookEvidence.read(g2,'CLERIC_CURE_LIGHT_WOUNDS')
assert(ev and ev.ready_count==1 and ev.class_kit_dual_active_proven==false)''',
'''g2.m_typeAI.m_Class=8;g2.m_memorizedSpellsPriest=book({spell('SPPR103',1)})''')

    def test_unknown_spell_and_nil_actor_fail_closed(self):
        run('''assert(select(1,BGX66SpellbookEvidence.read(g2,'SPELL_NOT_ALLOWED'))==nil)
assert(select(1,BGX66SpellbookEvidence.read(nil,'WIZARD_SHIELD'))==nil)''')

    def test_missing_native_iterator_fail_closed(self):
        run('''local ev,err=BGX66SpellbookEvidence.read(g2,'WIZARD_SHIELD')
assert(ev==nil and err=='eeex_iterator_missing')''',native=False)

    def test_nil_level_fail_closed(self):
        run('''local ev,err=BGX66SpellbookEvidence.read(g2,'WIZARD_SHIELD')
assert(ev==nil and err=='spellbook_read_failed')''',
'''g2.m_memorizedSpellsMage={getReference=function() return nil end}''')

    def test_reader_throws_fail_closed(self):
        run('''local ev,err=BGX66SpellbookEvidence.read(g2,'WIZARD_SHIELD')
assert(ev==nil and err=='spellbook_read_failed')''',
'''g2.m_memorizedSpellsMage={getReference=function() error('pointer invalid') end}''')

    def test_malformed_record_id_raises_protected_failure(self):
        run('''local ev=BGX66SpellbookEvidence.read(g2,'CLERIC_CURE_LIGHT_WOUNDS')
assert(ev==nil and #actions==0 and #writes==0)''',
'''g2.m_memorizedSpellsPriest=book({{m_spellId={get=function()return nil end},m_flags=1}})''')

    def test_malformed_flags_raises_protected_failure(self):
        for flags in ('nil', '-1','1.5','"ready"','4294967296'):
            with self.subTest(flags=flags):
                run('''local ev=BGX66SpellbookEvidence.read(g2,'CLERIC_CURE_LIGHT_WOUNDS')
assert(ev==nil and #writes==0)''',
                'g2.m_memorizedSpellsPriest=book({spell("SPPR103",'+flags+')})')

    def test_excessive_entries_rejected(self):
        run('''local ev=BGX66SpellbookEvidence.read(g2,'CLERIC_CURE_LIGHT_WOUNDS')
assert(ev==nil and #actions==0 and #writes==0)''',
'''local big={};for i=1,4097 do big[i]=spell('SPPR103',1) end
 g2.m_memorizedSpellsPriest=book(big)''')

    def test_broken_iterator_rejected(self):
        run('''local ev=BGX66SpellbookEvidence.read(g2,'CLERIC_CURE_LIGHT_WOUNDS')
assert(ev==nil)''',
'''function EEex_Utility_IterateCPtrList() error('bridge error') end
 g2.m_memorizedSpellsPriest=book({spell('SPPR103',1)})''')

    def test_verifier_receives_real_book_evidence_but_controls_action(self):
        run('''BGX66Caster.capabilityVerifier=function(o,s,ev)
 if o.m_id~=105 or s~='CLERIC_CURE_LIGHT_WOUNDS' then return false end
 assert(ev and ev.resref=='SPPR103' and ev.ready_count==1)
 assert(ev.castable_now_proven==false)
 return true -- *synthetic* provider approval, NOT EEex live approval
end
hit(v2)
assert(BGX66Caster.healPrepared==1 and g2.locals.BGX66_S_HEAL_SLOT==3)
assert(#actions==0)''',
'''g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=21;
 v2.m_baseStats.m_hitPoints=2;
 g2.m_memorizedSpellsPriest=book({spell('SPPR103',1)})''')

    def test_provider_can_reject_even_when_memorized(self):
        run('''BGX66Caster.capabilityVerifier=function(o,s,ev)
 if o.m_id==105 and ev and ev.ready_count==1 then return false end
 return false end
hit(v2)
assert(BGX66Caster.healPrepared==0 and #writes==0 and #actions==0)''',
'''g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=21;
 v2.m_baseStats.m_hitPoints=2;
 g2.m_memorizedSpellsPriest=book({spell('SPPR103',1)})''')

    def test_strict_opt_in_rejects_missing_memorized_even_with_true_provider(self):
        run('''BGX66Caster.requireMemorizedEvidence=true
BGX66Caster.capabilityVerifier=function()return true end
hit(v2)
assert(BGX66Caster.healPrepared==0 and #writes==0 and #actions==0)''',
'''g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=21;v2.m_baseStats.m_hitPoints=2;''')

    def test_strict_opt_in_rejects_expended(self):
        run('''BGX66Caster.requireMemorizedEvidence=true
BGX66Caster.capabilityVerifier=function()return true end
hit(v2)
assert(BGX66Caster.healPrepared==0 and #writes==0)''',
'''g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=21;v2.m_baseStats.m_hitPoints=2;
 g2.m_memorizedSpellsPriest=book({spell('SPPR103',0)})''')

    def test_strict_opt_in_accepts_memorized_plus_independent_verifier(self):
        run('''BGX66Caster.requireMemorizedEvidence=true
BGX66Caster.capabilityVerifier=function(o,s,ev) return o.m_id==105 and ev~=nil and ev.ready_count==1 end
hit(v2)
assert(BGX66Caster.healPrepared==1 and #actions==0)''',
'''g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=21;v2.m_baseStats.m_hitPoints=2;
 g2.m_memorizedSpellsPriest=book({spell('SPPR103',1)})''')

    def test_legacy_no_provider_does_not_call_native_reader(self):
        run('''hit(v2)
assert(BGX66Caster.healPrepared==1 and #actions==0)''',
'''g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=3;v2.m_baseStats.m_hitPoints=2;
 function EEex_Utility_IterateCPtrList()error('should not be invoked') end''')

    def test_integrated_source_is_small_addendum_and_no_new_actions(self):
        old=OLD.read_text(); new=NEW.read_text(); snippet=MOD.read_text()
        self.assertEqual(new.count(snippet),1)
        self.assertEqual(old.count('BGX52Bridge.prepare=T.prepare'),new.count('BGX52Bridge.prepare=T.prepare'))
        self.assertEqual(old.count('EEex_Action_AddSpriteStartedActionListener, P.onStarted'),new.count('EEex_Action_AddSpriteStartedActionListener, P.onStarted'))
        self.assertEqual(old.count('EEex_Sprite_AddBlockWeaponHitListener, P.onWeaponHit'),new.count('EEex_Sprite_AddBlockWeaponHitListener, P.onWeaponHit'))
        for bad in (r'\bClearActions\s*\(',r'\bEEex_Action_Queue\w+\s*\(',r'\bSpell\s*\(',r'\bAttack\s*\(',r'\bsetLocalInt\s*\('):
            self.assertIsNone(re.search(bad,snippet),bad)
        self.assertEqual(old.count('S.capabilityVerifier = nil'),new.count('S.capabilityVerifier = nil'))
        self.assertIn('S.requireMemorizedEvidence = false',new)

if __name__=='__main__': unittest.main()
