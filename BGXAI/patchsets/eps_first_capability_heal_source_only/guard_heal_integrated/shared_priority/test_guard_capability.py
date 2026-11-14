"""Regression tests for a DISABLED-BY-DEFAULT guard capability gate in existing 066S Lua.
All cases are mock EEex: nothing here proves actual player-command provenance.
"""
from pathlib import Path
import hashlib
import unittest
from lua65_harness import run_case
from native_066_fixture import PREAMBLE

R=Path(__file__).resolve().parent
LEGACY=R/'M_BX43_066S_CASTER_CANDIDATE.lua'
PREVIOUS=R/'M_BX43_066S_HEAL_PATCH_PREVIOUS.lua'
CANDIDATE=R/'M_BX43_066S_CAPABILITY_CANDIDATE.lua'
BAF=R/'BGX66_CASTER_RECEIVER_SOURCE_ONLY.baf'

PROOF_FIELDS_TRUE = ('verified','effective_melee_now','weapon_effective_vs_attacker',
    'active_class_and_kit_verified','transformation_safe_verified',
    'action_idle_verified','eps_queue_empty_verified',
    'manual_order_absent_verified','target_attacker_identity_verified')
PROOF_FIELDS_FALSE = ('heal_reservation','spell_casting','bard_singing','detecting_traps')
ALL_FIELDS=PROOF_FIELDS_TRUE+PROOF_FIELDS_FALSE

# Tokens are deliberately synthetic in the model, NOT current evidence from EEex.
PROOF='{'+','.join([f'{k}=true' for k in PROOF_FIELDS_TRUE]+[f'{k}=false' for k in PROOF_FIELDS_FALSE])+'}'


def call(assertions,setup='',candidate=CANDIDATE):
    # Party fixture state is set before the Lua module loads; runtime
    # injection of the gated provider occurs only AFTER BGX66Team exists.
    marker='BGX66Team.'
    if marker in setup:
        pos=setup.index(marker)
        pre,post=setup[:pos],setup[pos:]
    else:
        pre,post=setup,''
    run_case(PREAMBLE + '''\nfunction bindProof(o,a,v,s,p)\n if type(p)=='table' then p.actor_id=o.m_id;p.attacker_id=a;p.victim_id=v;p.source_event_sequence=s end\n return p\nend\n''' + pre,post+'\n'+assertions,candidate)


def enabled_setup(class_id=8,proof=PROOF,chosen=105):
    return f'''g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class={class_id};
BGX66Team.capabilitySourceVerified=true;
BGX66Team.capabilityVerifier=function(o,a,v,s) if o.m_id=={chosen} then return bindProof(o,a,v,s,{proof}) else return nil end end;
'''

class GuardCapability(unittest.TestCase):
    def test_legacy_sha_and_baf_same(self):
        self.assertEqual(hashlib.sha256(LEGACY.read_bytes()).hexdigest(),
            '50640902ec4c25a2c85e5088d7231678b54445a847b41743c476974236d1d70f')
        self.assertEqual(hashlib.sha256(BAF.read_bytes()).hexdigest(),
            'c678a70a08dbcff7584e0f2703aa8bed5ae5945856287666016ee47c9d6f69ae')

    def test_existing_heal_patch_and_guard_diff_only(self):
        import difflib
        old=PREVIOUS.read_text();new=CANDIDATE.read_text()
        # Exact reverse patch proves no unrelated code changed beyond the five
        # cross-channel arbitration regions; V2 already proved spell/guard diff.
        from arbiter_exact_diff import verify_exact_revert
        self.assertTrue(verify_exact_revert(R))
        self.assertNotIn('ClearActions(',new)
        self.assertEqual(new.count('EEex_Action_AddSpriteStartedActionListener, P.onStarted'),1)
        self.assertEqual(new.count('EEex_Sprite_AddBlockWeaponHitListener, P.onWeaponHit'),1)
        self.assertEqual(new.count('BGX52Bridge.prepare=T.prepare'),1)
        self.assertEqual(new.count('S.capabilityVerifier = nil'),1)
        self.assertEqual(new.count('T.capabilitySourceVerified = false'),1)
        self.assertEqual(new.count('T.capabilityVerifier = nil'),1)

    def test_default_disabled_previous_guard_behavior_all_class_ids(self):
        # This covers every CLASS.IDS 1..21; includes kit, dual/multi examples as IDs.
        for cls in range(1,22):
            with self.subTest(cls=cls):
                approved=cls in (2,6,12)
                setup=f'g2.m_typeAI.m_Class={cls};g1.m_typeAI.m_Class=1;'
                if approved:
                    expected="assert(BGX66Team.prepared==1 and g2.locals.BGX52_REQ_SLOT==3)"
                else:
                    expected="assert(BGX66Team.prepared==0 and g2.locals.BGX52_REQ_SLOT==0)"
                call('hit(v2);'+expected+";assert(#actions==0)",setup)

    def test_legacy_ignores_unverified_provider(self):
        setup="g1.m_typeAI.m_Class=2; BGX66Team.capabilityVerifier=function() error('called') end;"
        call('hit(v2); assert(BGX66Team.prepared==1 and g1.locals.BGX52_REQ_SLOT==3)',setup)

    def test_enabled_current_capability_not_base_class(self):
        for cls in (7,8,9,10,11,13,14,15,16,17,18,20,21,200):
            with self.subTest(cls=cls):
                call('hit(v2); assert(BGX66Team.prepared==1 and g2.locals.BGX52_REQ_SLOT==3 and #actions==0)',
                     enabled_setup(cls))

    def test_verified_but_fighter_without_usable_weapon_is_rejected(self):
        setup=enabled_setup(2,proof='nil')
        call('hit(v2); assert(BGX66Team.prepared==0 and g2.locals.BGX52_REQ_SLOT==0)',setup)

    def test_missing_false_wrong_type_or_thrown_proof_rejected(self):
        for value in ('false','nil','1','"yes"','{}','true',
                      "setmetatable({},{__index=function() error('unsafe field') end})"):
            with self.subTest(value=value):
                call('hit(v2); assert(BGX66Team.prepared==0 and #writes==0 and #actions==0)',
                     enabled_setup(21,proof=value))
        call("hit(v2); assert(BGX66Team.prepared==0 and #writes==0)",
             'g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=21;'
             'BGX66Team.capabilitySourceVerified=true;'
             "BGX66Team.capabilityVerifier=function() error('observer broken') end;")

    def test_one_false_required_true_field_blocks(self):
        for field in PROOF_FIELDS_TRUE:
            with self.subTest(field=field):
                setup=enabled_setup(21)+f"local p={PROOF};p.{field}=false;BGX66Team.capabilityVerifier=function(o,a,v,s) return bindProof(o,a,v,s,p) end;"
                call("hit(v2); assert(BGX66Team.prepared==0 and #writes==0)",setup)
        for field in PROOF_FIELDS_FALSE:
            with self.subTest(field=field):
                setup=enabled_setup(21)+f"local p={PROOF};p.{field}=true;BGX66Team.capabilityVerifier=function(o,a,v,s) return bindProof(o,a,v,s,p) end;"
                call("hit(v2); assert(BGX66Team.prepared==0 and #writes==0)",setup)

    def test_missing_field_cannot_be_inferred_by_class_or_metatable(self):
        for field in ALL_FIELDS:
            with self.subTest(field=field):
                setup=enabled_setup(21)+f"local p={PROOF};p.{field}=nil;BGX66Team.capabilityVerifier=function(o,a,v,s) return bindProof(o,a,v,s,p) end;"
                call("hit(v2); assert(BGX66Team.prepared==0 and #writes==0)",setup)

    def test_f_off_modal_area_hp_guards_preserved(self):
        for change in ('g2.locals.BGX38_GUARD=0','g2.m_nModalState=1',
                       'g2.m_pArea=b','g2.m_baseStats.m_hitPoints=2',
                       'g2.m_baseStats.m_hitPoints=15'):
            with self.subTest(change=change):
                setup=enabled_setup(21)+change+';'
                call("hit(v2); assert(BGX66Team.prepared==0 and #writes==0)",setup)

    def test_second_defender_when_first_busy(self):
        # g1 is nearer to v2 but has pending EPS action: g2 must be selected.
        setup=f'''g1.m_typeAI.m_Class=8;g2.m_typeAI.m_Class=21;
BGX66Team.capabilitySourceVerified=true;
BGX66Team.capabilityVerifier=function(o,a,v,s)
 local p={PROOF}
 if o.m_id==104 then p.eps_queue_empty_verified=false end
 return bindProof(o,a,v,s,p)
end;'''
        call("hit(v2); assert(BGX66Team.prepared==1 and g1.locals.BGX52_REQ_SLOT==0 and g2.locals.BGX52_REQ_SLOT==3)",setup)

    def test_closer_verified_frontliner_wins(self):
        setup=f'''g1.m_typeAI.m_Class=8;g2.m_typeAI.m_Class=21;
BGX66Team.capabilitySourceVerified=true;
BGX66Team.capabilityVerifier=function(o,a,v,s) return bindProof(o,a,v,s,{PROOF}) end;'''
        call("hit(v2); assert(BGX66Team.prepared==1 and g1.locals.BGX52_REQ_SLOT==3 and g2.locals.BGX52_REQ_SLOT==0)",setup)

    def test_reserve_healer_prevents_guard_then_heal_same_actor(self):
        setup=enabled_setup(3,proof=PROOF.replace('heal_reservation=false','heal_reservation=true'))+'v2.m_baseStats.m_hitPoints=2;'
        call("hit(v2); assert(BGX66Team.prepared==0 and BGX66Caster.healPrepared==1 and g2.locals.BGX66_S_HEAL_SLOT==3)\nassert(g2.locals.BGX52_REQ_SLOT==0 and #actions==0)",setup)

    def test_no_intercept_when_player_fired_manual_order(self):
        setup=enabled_setup(2,proof=PROOF.replace('manual_order_absent_verified=true','manual_order_absent_verified=false'))
        call("hit(v2); assert(BGX66Team.prepared==0 and #writes==0)",setup)

    def test_no_passing_proof_when_runtime_source_not_approved(self):
        # Merely injecting a correct-looking proof is not enough to change the old behavior.
        setup=f'''g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=21;
BGX66Team.capabilitySourceVerified=false;
BGX66Team.capabilityVerifier=function(o,a,v,s) return bindProof(o,a,v,s,{PROOF}) end;'''
        call("hit(v2); assert(BGX66Team.prepared==0 and #writes==0)",setup)

    def test_wrong_actor_or_attacker_or_hit_sequence_proof_is_refused(self):
        cases=("p.actor_id=104", "p.attacker_id=1001", "p.victim_id=102", "p.source_event_sequence=888")
        for tamper in cases:
            with self.subTest(tamper=tamper):
                setup=enabled_setup(8)+f"BGX66Team.capabilityVerifier=function(o,a,v,s) if o.m_id~=105 then return nil end; local p=bindProof(o,a,v,s,{PROOF});{tamper};return p end;"
                call("hit(v2); assert(BGX66Team.prepared==0 and #writes==0 and #actions==0)",setup)

    def test_correct_actor_and_hit_ids_are_forwarded_to_observer(self):
        setup=f'''g1.m_typeAI.m_Class=1;g2.m_typeAI.m_Class=8;
BGX66Team.capabilitySourceVerified=true;
BGX66Team.capabilityVerifier=function(o,a,v,s)
 assert(o.m_id==105 and a==999 and v==103 and s==1)
 return bindProof(o,a,v,s,{PROOF})
end;'''
        call("hit(v2); assert(BGX66Team.prepared==1 and g2.locals.BGX52_REQ_SLOT==3)",setup)

    def test_guard_and_caster_independent_enable_and_no_lua_actions(self):
        # In simulation, a proven shaman can protect and another caster can heal;
        # real-game arbitration would still require a separately proven observer.
        setup=f'''g1.m_typeAI.m_Class=21;g2.m_typeAI.m_Class=3;v2.m_baseStats.m_hitPoints=2;
BGX66Team.capabilitySourceVerified=true;
BGX66Team.capabilityVerifier=function(o,a,v,s) if o.m_id==104 then return bindProof(o,a,v,s,{PROOF}) end end;'''
        call("hit(v2); assert(BGX66Team.prepared==1 and BGX66Caster.healPrepared==1)\nassert(g1.locals.BGX52_REQ_SLOT==3 and g2.locals.BGX66_S_HEAL_SLOT==3 and #actions==0)",setup)


    def test_emergency_heal_has_priority_over_same_actors_guard_request(self):
        # Prove a real cross-channel conflict: eligible Fighter/Cleric can
        # receive guard and heal requests from the SAME confirmed hit. Fix
        # must reserve the emergency healer BEFORE optional guard arbitration.
        setup=enabled_setup(8)+"v2.m_baseStats.m_hitPoints=2;"
        call("""hit(v2)
assert(BGX66Caster.healPrepared==1 and BGX66Team.prepared==0)
assert(g2.locals.BGX66_S_HEAL_SLOT==3 and g2.locals.BGX52_REQ_SLOT==0)
assert(#actions==0)""",setup)

    def test_emergency_healer_and_different_guard_are_both_selected(self):
        # Nearest g1 can heal, g2 is the independent frontline responder.
        setup=f'''g1.m_typeAI.m_Class=8;g2.m_typeAI.m_Class=6;
v2.m_baseStats.m_hitPoints=2;
BGX66Team.capabilitySourceVerified=true;
BGX66Team.capabilityVerifier=function(o,a,v,s)
 return bindProof(o,a,v,s,{PROOF})
end;'''
        call("""hit(v2)
assert(BGX66Caster.healPrepared==1 and BGX66Team.prepared==1)
assert(g1.locals.BGX66_S_HEAL_SLOT==3 and g1.locals.BGX52_REQ_SLOT==0)
assert(g2.locals.BGX52_REQ_SLOT==3 and g2.locals.BGX66_S_HEAL_SLOT==nil)
assert(#actions==0)""",setup)

    def test_outstanding_caster_bcs_request_blocks_guard_even_after_lease(self):
        setup=enabled_setup(8)+"g2.locals.BGX66_S_HEAL_SLOT=3;"
        call("""hit(v2)
assert(BGX66Team.prepared==0 and g2.locals.BGX52_REQ_SLOT==0)
assert(#actions==0)""",setup)

    def test_outstanding_guard_bcs_request_blocks_healer_even_after_lease(self):
        setup=enabled_setup(8)+"v2.m_baseStats.m_hitPoints=2;g2.locals.BGX52_REQ_SLOT=3;"
        call("""hit(v2)
assert(BGX66Caster.healPrepared==0 and g2.locals.BGX66_S_HEAL_SLOT==nil)
assert(#actions==0)""",setup)

    def test_unreadable_request_state_must_fail_closed_when_capability_enabled(self):
        setup=enabled_setup(8)+"""local old=g2.getLocalInt
function g2:getLocalInt(k)
 if k=='BGX66_S_HEAL_SLOT' or k=='BGX66_S_WARD' then error('read denied') end
 return old(self,k)
end;"""
        call("""hit(v2)
assert(BGX66Team.prepared==0 and g2.locals.BGX52_REQ_SLOT==0)
assert(#actions==0)""",setup)

if __name__=='__main__':unittest.main()
