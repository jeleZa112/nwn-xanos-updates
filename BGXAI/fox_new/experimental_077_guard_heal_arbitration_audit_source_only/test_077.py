"""Unit and regression tests. Synthetic data are not real EEex/gameplay outcomes."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from audit_077 import INPUTS, AuditError, analyze, baf_blocks, lua_class_ids, read_exact

HERE=Path(__file__).parent

def block(body): return 'IF\n'+body+'\nTHEN\n RESPONSE #100\n  Continue()\nEND\n'

def fixture():
    guard = ''.join(block('InParty(Myself)') for _ in range(2))
    guard += ''.join(block('ActionListEmpty()\nAttackReevaluate(LastAttackerOf(Player1),30)') for _ in range(6))
    guard += ''.join(block('ActionListEmpty()\nMoveToObject(Player1)') for _ in range(6))
    guard += ''.join(block('ActionListEmpty()\nProtectObject(Player1,6)') for _ in range(6))
    cast = ''.join(block('InParty(Myself)') for _ in range(4))
    cast += ''.join(block('ActionListEmpty()\nHaveSpell(CLERIC_CURE_LIGHT_WOUNDS)\nRange(Player1,10)\nSpell(Player1,CLERIC_CURE_LIGHT_WOUNDS)') for _ in range(6))
    cast += block('ActionListEmpty()\nHaveSpell(WIZARD_SHIELD)\nSpell(Myself,WIZARD_SHIELD)')
    lua = """local FRONTLINE = {[2]=true,[6]=true,[12]=true}
    BGX52Bridge.prepare=T.prepare
    if guardOK and guardRecord then
      pcall(BGX52Bridge.prepare, guardRecord)
    end
    local basePrepare=BGX52Bridge.prepare
    BGX52Bridge.prepare=function(hit)
      local ok,why=basePrepare(hit)
      S.onHit(hit)
      return ok,why
    end
    """
    lua = lua.replace('    local basePrepare=', 'local basePrepare=').replace('    BGX52Bridge.prepare=function', 'BGX52Bridge.prepare=function').replace('    end\n', 'end\n')
    support = """local HEALER={[3]=true,[8]=true,[11]=true,[14]=true,[15]=true,[16]=true,[17]=true,[18]=true}
    local ARCANE={[1]=true,[5]=true,[7]=true,[10]=true,[13]=true,[14]=true,[17]=true,[19]=true}
    if HEALER[cls] and get(o,'BGX66_S_HEAL_SLOT')==0 then
       local dist=(ox-vx)^2+(oy-vy)^2
       if not healer or dist<rank then healer=m end
    end
    if healer and ward and healer.id==ward.id then ward=nil end
    """
    return {'BGX61_RECEIVER.baf':guard,
            'BGX66_CASTER_RECEIVER_SOURCE_ONLY.baf':cast,
            'M_BX43_066S_CASTER_CANDIDATE.lua':lua,
            'BGX66_CASTER_SUPPORT.lua':support}

class Audit077(unittest.TestCase):
    def setUp(self):
        self.data=fixture()
    def runaudit(self):return analyze(self.data)
    def test_valid_sample(self): self.assertEqual(self.runaudit()['status'],'SOURCE_ONLY_BGXAI_077_AUDIT_CONFIRMED')
    def test_guard20(self):self.assertEqual(self.runaudit()['baf']['061_blocks'],20)
    def test_061_18_queued(self):self.assertEqual(self.runaudit()['baf']['061_action_list_empty'],18)
    def test_066_7_queued(self):self.assertEqual(self.runaudit()['baf']['066s_action_list_empty'],7)
    def test_guard_action_split(self):
        a=self.runaudit()['baf']
        self.assertEqual([a['attack_reevaluate'],a['move_to_ally'],a['protect_ally']],[6,6,6])
    def test_roles_disjoint(self):self.assertEqual(self.runaudit()['roles']['frontline_healer_id_overlap'],[])
    def test_shaman_absent(self):self.assertFalse(self.runaudit()['roles']['shaman_21_in_healer'])
    def test_guard_table_exact(self):self.assertEqual(self.runaudit()['roles']['frontline_ids'],[2,6,12])
    def test_healer_table_exact(self):self.assertEqual(self.runaudit()['roles']['healer_ids'],[3,8,11,14,15,16,17,18])
    def test_arcane_table_exact(self):self.assertEqual(self.runaudit()['roles']['arcane_ids'],[1,5,7,10,13,14,17,19])
    def test_bad_061_count_rejected(self):
        self.data['BGX61_RECEIVER.baf']=self.data['BGX61_RECEIVER.baf'][:-len(block('ActionListEmpty()\nProtectObject(Player1,6)'))]
        with self.assertRaises(AuditError): self.runaudit()
    def test_queue_guard_rejected(self):
        self.data['BGX61_RECEIVER.baf']=self.data['BGX61_RECEIVER.baf'].replace('ActionListEmpty()','',1)
        with self.assertRaisesRegex(AuditError,'QUEUE_GATE'):self.runaudit()
    def test_queue_heal_rejected(self):
        self.data['BGX66_CASTER_RECEIVER_SOURCE_ONLY.baf']=self.data['BGX66_CASTER_RECEIVER_SOURCE_ONLY.baf'].replace('ActionListEmpty()','',1)
        with self.assertRaisesRegex(AuditError,'QUEUE_GATE'):self.runaudit()
    def test_spell_gate_rejected(self):
        self.data['BGX66_CASTER_RECEIVER_SOURCE_ONLY.baf']=self.data['BGX66_CASTER_RECEIVER_SOURCE_ONLY.baf'].replace('HaveSpell(CLERIC_CURE_LIGHT_WOUNDS)','',1)
        with self.assertRaisesRegex(AuditError,'SPELL_GATE'):self.runaudit()
    def test_range_gate_rejected(self):
        self.data['BGX66_CASTER_RECEIVER_SOURCE_ONLY.baf']=self.data['BGX66_CASTER_RECEIVER_SOURCE_ONLY.baf'].replace('Range(Player1,10)','',1)
        with self.assertRaisesRegex(AuditError,'RANGE_GATE'):self.runaudit()
    def test_shaman_table_change_requires_reaudit(self):
        self.data['BGX66_CASTER_SUPPORT.lua']=self.data['BGX66_CASTER_SUPPORT.lua'].replace('[18]=true}', '[18]=true,[21]=true}')
        with self.assertRaisesRegex(AuditError,'HEALER_DRIFT'):self.runaudit()
    def test_frontline_change_requires_reaudit(self):
        self.data['M_BX43_066S_CASTER_CANDIDATE.lua']=self.data['M_BX43_066S_CASTER_CANDIDATE.lua'].replace('[12]=true}', '[12]=true,[8]=true}')
        with self.assertRaisesRegex(AuditError,'FRONTLINE_DRIFT'):self.runaudit()
    def test_callback_reverse_rejected(self):
        self.data['M_BX43_066S_CASTER_CANDIDATE.lua']=self.data['M_BX43_066S_CASTER_CANDIDATE.lua'].replace('local ok,why=basePrepare(hit)\n      S.onHit(hit)', 'S.onHit(hit)\n      local ok,why=basePrepare(hit)')
        with self.assertRaisesRegex(AuditError,'WRAPPER_ORDER'):self.runaudit()
    def test_duplicate_role_ids_rejected(self):
        with self.assertRaisesRegex(AuditError,'MALFORMED_CLASS_TABLE'):
            lua_class_ids('local HEALER={[8]=true,[8]=true}', 'HEALER')
    def test_missing_variable_rejected(self):
        with self.assertRaisesRegex(AuditError,'MISSING_CLASS_TABLE'):
            lua_class_ids('local FRONTLINE={}', 'HEALER')
    def test_empty_baf_rejected(self):
        with self.assertRaisesRegex(AuditError,'BAF_BLOCK_PARSE_INCOMPLETE'):
            baf_blocks('')
    def test_published_report(self):
        data=json.loads((HERE/'audit_results_077.json').read_text())
        self.assertEqual(data['baf']['066s_heal_blocks'],6)
        self.assertTrue(data['event_path']['weapon_hit_dispatch_first_calls_frontline_then_support'])
    def test_input_pins_full(self):
        self.assertEqual(set(INPUTS),set(fixture()))
    def test_read_exact_sha_denial(self):
        with tempfile.TemporaryDirectory() as d:
            for k in INPUTS: (Path(d)/k).write_bytes(b'not original')
            with self.assertRaisesRegex(AuditError,'SOURCE_SHA_MISMATCH'):read_exact(Path(d))
    def test_mutation_does_not_affect_fixture(self):
        baseline=fixture(); self.runaudit(); self.assertEqual(baseline,self.data)
    @unittest.skipUnless(os.getenv('BGXAI077_SOURCE_DIR'), 'Original private source fixture optional')
    def test_original_read_only_source(self):
        r=analyze(read_exact(Path(os.environ['BGXAI077_SOURCE_DIR'])))
        self.assertEqual(r['status'],'SOURCE_ONLY_BGXAI_077_AUDIT_CONFIRMED')

if __name__=='__main__':unittest.main()
