from __future__ import annotations
import pathlib, unittest, importlib.util, json, hashlib, tempfile
P=pathlib.Path(__file__).parent
spec=importlib.util.spec_from_file_location('BGXAI085_BCS_GATE_AUDIT',P/'BGXAI085_BCS_GATE_AUDIT.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
BASE='''IF
  InParty(Myself)
  Global("BGX38_GUARD","LOCALS",1)
  Global("BGX52_REQ_SLOT","LOCALS",2)
  GlobalTimerNotExpired("BGX52_EXPIRE","LOCALS")
  ActionListEmpty()
  ModalState(NONE)
  HaveSpell(CLERIC_CURE_LIGHT_WOUNDS)
THEN
  RESPONSE #100
    SetGlobal("BGX52_REQ_SLOT","LOCALS",0)
    Spell(Player2,CLERIC_CURE_LIGHT_WOUNDS)
END
'''
class SourcePolicy(unittest.TestCase):
 def test_01_good_spell(self):
  r=m.audit(BASE); self.assertEqual(r['status'],'BAF_STATIC_GATE_PASS');self.assertEqual(r['dispatch_rules'],1)
 def test_02_never_authorized(self):
  r=m.audit(BASE);self.assertFalse(r['engine_dispatch_authorized']);self.assertFalse(r['live_verified']);self.assertFalse(r['eps_buff_priority_verified'])
 def test_03_missing_queue(self):
  r=m.audit(BASE.replace('ActionListEmpty()',''));self.assertIn(1,r['fail_blocks'])
 def test_04_negated_queue(self):
  r=m.audit(BASE.replace('ActionListEmpty()','!ActionListEmpty()'));self.assertIn('MISSING_NATIVE_QUEUE',r['rules'][0]['findings'])
 def test_05_guard_off(self):
  r=m.audit(BASE.replace('"LOCALS",1)','"LOCALS",0',1));self.assertIn('MISSING_F_GUARD_ON',r['rules'][0]['findings'])
 def test_06_modal_missing(self):
  r=m.audit(BASE.replace('ModalState(NONE)',''));self.assertIn('MISSING_MODAL_NONE',r['rules'][0]['findings'])
 def test_07_have_spell(self):
  r=m.audit(BASE.replace('HaveSpell(CLERIC_CURE_LIGHT_WOUNDS)',''));self.assertIn('MISSING_HAVE_SPELL',r['rules'][0]['findings'])
 def test_08_protect_object_not_housekeeping(self):
  r=m.audit(BASE.replace('Spell(Player2,CLERIC_CURE_LIGHT_WOUNDS)','ProtectObject(Player2,6)'));self.assertEqual(r['dispatch_rules'],1);self.assertEqual(r['rules'][0]['action_names'],['ProtectObject'])
 def test_09_attack_one_round_unknown(self):
  r=m.audit(BASE.replace('Spell(Player2,CLERIC_CURE_LIGHT_WOUNDS)','AttackOneRound(Player2)'))
  self.assertIn('REVIEW_UNKNOWN_ENGINE_ACTION_AttackOneRound',r['rules'][0]['findings'])
 def test_10_cleanup(self):
  s='''// cleanup
IF
  InParty(Myself)
THEN
  RESPONSE #100
    SetGlobal("X","LOCALS",0)
    Continue()
END'''
  r=m.audit(s);self.assertEqual(r['housekeeping_rules'],1);self.assertEqual(r['status'],'BAF_STATIC_GATE_PASS')
 def test_11_comments_do_not_count(self):
  r=m.audit(BASE.replace('ActionListEmpty()','// ActionListEmpty()'))
  self.assertIn('MISSING_NATIVE_QUEUE',r['rules'][0]['findings'])
 def test_12_no_expire(self):
  r=m.audit(BASE.replace('GlobalTimerNotExpired("BGX52_EXPIRE","LOCALS")',''))
  self.assertIn('MISSING_REQUEST_TTL',r['rules'][0]['findings'])
 def test_13_no_request(self):
  r=m.audit(BASE.replace('Global("BGX52_REQ_SLOT","LOCALS",2)',''))
  self.assertIn('MISSING_ON_HIT_REQUEST',r['rules'][0]['findings'])
 def test_14_malformed(self):
  with self.assertRaises(ValueError):m.audit(BASE[:-5])
 def test_15_trailing_command(self):
  with self.assertRaises(ValueError):m.audit(BASE+'IllegalLine')
 def test_16_empty(self):
  with self.assertRaises(ValueError):m.audit('')
 def test_17_multiple(self):
  r=m.audit(BASE+BASE.replace('Spell(Player2,CLERIC_CURE_LIGHT_WOUNDS)','AttackReevaluate(LastAttackerOf(Player2),30)'))
  self.assertEqual(r['dispatch_rules'],2)
 def test_18_readonly_cli(self):
  with tempfile.TemporaryDirectory() as td:
   f=pathlib.Path(td)/'t.baf';f.write_text(BASE,encoding='utf-8')
   before=hashlib.sha256(f.read_bytes()).hexdigest()
   self.assertEqual(m.main([str(f)]),0)
   self.assertEqual(before,hashlib.sha256(f.read_bytes()).hexdigest())
 def test_19_evidence(self):
  e=json.loads((P/'evidence_085.json').read_text('utf-8'))
  self.assertEqual(e['audited_sources'][0]['dispatch_rules'],18)
  self.assertEqual(e['audited_sources'][1]['dispatch_rules'],7)
  self.assertEqual(e['audited_sources'][2]['dispatch_rules'],6)
 def test_20_manifest(self):
  for f,sha in json.loads((P/'manifest_sha256.json').read_text('utf-8'))['files'].items():
   self.assertEqual(hashlib.sha256((P/f).read_bytes()).hexdigest(),sha)
if __name__=='__main__':unittest.main()
