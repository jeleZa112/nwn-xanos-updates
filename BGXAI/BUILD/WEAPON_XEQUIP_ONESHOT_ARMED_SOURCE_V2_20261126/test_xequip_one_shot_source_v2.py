import importlib.util,json,unittest
from pathlib import Path
P=Path("BGXAI/BUILD/WEAPON_XEQUIP_ONESHOT_ARMED_SOURCE_V2_20261126/BGXAI_XEQUIP_ONE_SHOT_SOURCE_V2.py")
spec=importlib.util.spec_from_file_location("once",P)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def d(**kw):
 x={"schema":m.SCHEMA,"actorId":1248,"partyIndex":2,
    "sourceSlot":18,"targetSlot":36,"resref":"SW1H04",
    "weaponSlotCapacity":4,"sourceSnapshotSha256":"a"*64,
    "snapshotSession":"SESSION_TEST_20261126"}
 x.update(kw)
 return x
class Pilot(unittest.TestCase):
 def test_exact_one_shot(self):
  x=m.render(d())
  self.assertIn('Global("BGXW2ARM","GLOBAL",1)',x)
  self.assertIn('Global("BGXW2TRY","LOCALS",0)',x)
  self.assertIn('SetGlobal("BGXW2ARM","GLOBAL",2)',x)
  self.assertIn('SetGlobal("BGXW2TRY","LOCALS",1)',x)
  self.assertIn('CheckItemSlot(Myself,"SW1H04",SLOT_MISC3)',x)
  self.assertIn('!HasItemSlot(Myself,SLOT_WEAPON1)',x)
  self.assertIn('XEquipItem("SW1H04",Myself,SLOT_WEAPON1,EQUIP)',x)
  self.assertEqual(x.count('XEquipItem('),1)
 def test_never_arm_itself(self):
  x=m.render(d());self.assertNotIn('SetGlobal("BGXW2ARM","GLOBAL",1)',x)
 def test_no_attack_disruption_commands(self):
  x=m.render(d())
  for v in ("Stop(","ClearActions(","FillSlot(","Attack(",
            "CreateItem(","SelectWeaponAbility("):
   self.assertNotIn(v,x)
 def test_outside_combat_and_idle(self):
  s=m.render(d())
  self.assertIn("CombatCounter(0)",s)
  self.assertIn("ActionListEmpty()",s)
  self.assertIn("!StateCheck(Myself,STATE_HELPLESS)",s)
 def test_correct_slot_mapping_16(self):
  for n in range(18,34):
   self.assertIn(f"SLOT_MISC{n-15})",m.render(d(sourceSlot=n)))
  for n in range(35,39):
   self.assertIn(f"SLOT_WEAPON{n-35},EQUIP)",m.render(d(targetSlot=n)))
 def test_all_wrong_source_slots_rejected(self):
  for n in (0,14,15,16,17,34,35,39,True,"18",None):
   with self.subTest(n=n),self.assertRaises(m.Hold):m.render(d(sourceSlot=n))
 def test_class_allowed_quickslot_only(self):
  for n in (34,39,100,False):
   with self.subTest(n=n),self.assertRaises(m.Hold):m.render(d(targetSlot=n))
  for n in (37,38):
   with self.subTest(n=n),self.assertRaises(m.Hold):
    m.render(d(targetSlot=n,weaponSlotCapacity=2))
 def test_resref_injection_and_lowercase(self):
  for n in ("sw1h04",'SW1H04")\nDestroyItem(',"A/B","A\n","",None,"ÁBC", "ABCDEFGHI"):
   with self.subTest(n=n),self.assertRaises(m.Hold):m.render(d(resref=n))
 def test_no_pc_and_bad_npc(self):
  for n in (0,6,-1,True,2.0):
   with self.subTest(n=n),self.assertRaises(m.Hold):m.render(d(partyIndex=n))
 def test_no_fake_verified_flag(self):
  with self.assertRaises(m.Hold):m.render(d(manualEpsOriginVerified=True))
 def test_digest_not_proof_of_snapshot(self):
  a=m.audit(d())
  self.assertFalse(a["inputSnapshotProvenanceAuthenticated"])
  self.assertFalse(a["gameInventoryUniqueVerified"])
  self.assertFalse(a["userInstallAuthorizationReceived"])
  self.assertFalse(a["installed"])
  self.assertEqual(a["ordersSent"],0)
 def test_bad_hash_and_bad_session(self):
  for value in ("z"*64,"A"*64,"a"*63,"",None):
   with self.subTest(value=value),self.assertRaises(m.Hold):
    m.render(d(sourceSnapshotSha256=value))
  for value in ("",None,"../other","a"):
   with self.subTest(value=value),self.assertRaises(m.Hold):
    m.render(d(snapshotSession=value))
 def test_no_source_mutation(self):
  x=d()
  p=dict(x);m.render(x);self.assertEqual(x,p)
 def test_single_block_one_response(self):
  x=m.render(d())
  self.assertEqual(x.count("IF\n"),1)
  self.assertEqual(x.count("THEN\n"),1)
  self.assertEqual(x.count("RESPONSE #100"),1)
  self.assertEqual(x.count("END\n"),1)
 def test_one_shot_markers_before_action(self):
  x=m.render(d())
  self.assertLess(x.index('SetGlobal("BGXW2ARM","GLOBAL",2)'),x.index("XEquipItem("))
  self.assertLess(x.index('SetGlobal("BGXW2TRY","LOCALS",1)'),x.index("XEquipItem("))
if __name__=="__main__":unittest.main(verbosity=2)
