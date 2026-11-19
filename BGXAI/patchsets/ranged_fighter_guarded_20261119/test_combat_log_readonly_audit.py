#!/usr/bin/env python3
"""Tests require no BG game or EEex; exercise actual BGX71 monitor line grammar."""
import os,sys,tempfile,unittest
from pathlib import Path
from unittest import mock
sys.path.insert(0,str(Path(__file__).parent))
import BGX_COMBAT_LOG_READONLY_AUDIT as A
def rec(seq,tag,id,slot,action,target):
 return (f"[BGX71] ACTION_{seq} actor={tag} id={id} slot={slot} action={action} "
  f"pos=(2,3) dest=(4,5) target={target}\n")
def runlog(data):
 with tempfile.TemporaryDirectory() as d:
  p=Path(d)/"BGXAI_COMBAT.log"
  p.write_bytes(data.encode("utf-8"))
  original=p.read_bytes()
  report=A.report(Path(d))
  assert p.read_bytes()==original
  return report
class CombatLogAudit(unittest.TestCase):
 def test_party_attack_observed_with_exact_roster_membership(self):
  data="[BGX71] ROSTER epoch=1 size=2\n"+rec(1,"A1",101,1,0,-1)+rec(2,"A2",102,2,0,-1)+rec(3,"A1",101,1,3,102)
  r=runlog(data)
  self.assertEqual(r["status"],"COMBAT_LOG_SCANNED")
  self.assertEqual(r["observed_party_attack_starts"][0]["status"],"PARTY_TO_PARTY_ATTACK_ACTION_STARTED_OBSERVED")
  self.assertEqual(r["observed_party_attack_starts"][0]["target_slot"],2)
  self.assertEqual(r["observed_party_attack_starts"][0]["action_origin"],"UNKNOWN")
  self.assertFalse(r["proof_of_absence"])
 def test_no_roster_does_not_call_it_party_attack(self):
  r=runlog(rec(1,"A1",101,1,3,102)+rec(2,"A2",102,2,0,-1))
  self.assertEqual(r["status"],"BGX71_ROSTER_NOT_OBSERVED_TARGET_MEMBERSHIP_UNVERIFIED")
  self.assertEqual(r["observed_party_attack_starts"],[])
 def test_old_epoch_must_not_be_reused(self):
  data="[BGX71] ROSTER epoch=1 size=2\n"+rec(1,"A1",101,1,0,-1)+rec(2,"A2",102,2,0,-1)
  data+="[BGX71] ROSTER epoch=2 size=1\n"+rec(3,"A1",101,1,3,102)
  r=runlog(data)
  self.assertEqual(r["observed_party_attack_starts"],[])
  self.assertEqual(r["distinct_observed_party_slots"],1)
 def test_no_target_cannot_assert_identity(self):
  r=runlog("[BGX71] ROSTER epoch=1 size=2\n"+rec(1,"A1",101,1,3,-1)+rec(2,"A2",102,2,0,-1))
  self.assertEqual(r["observed_party_attack_starts"],[])
 def test_nonparty_target_cannot_assert_party_attack(self):
  r=runlog("[BGX71] ROSTER epoch=1 size=2\n"+rec(1,"A1",101,1,3,999)+rec(2,"A2",102,2,0,-1))
  self.assertEqual(r["observed_party_attack_starts"],[])
 def test_legacy_without_target_cannot_prove(self):
  r=runlog("[BGXAI] ACTION_4 name=Khalid id=101 action=3\n")
  self.assertEqual(r["status"],"NO_BGX71_TARGET_BEARING_EVENTS")
  self.assertEqual(r["legacy_actions_without_known_target_id"],1)
 def test_missing_log_is_nonfatal(self):
  with tempfile.TemporaryDirectory() as d:
   r=A.report(Path(d))
   self.assertEqual(r["status"],"NO_EXISTING_COMBAT_LOG")
 def test_never_mutates_game(self):
  source=Path(A.__file__).read_text()
  self.assertNotIn("--force-install",source)
  self.assertNotIn("write_bytes(",source)
  self.assertNotIn("unlink(",source)
  self.assertNotIn("ClearActions",source)
  self.assertIn("action_origin\":\"UNKNOWN",source)
if __name__=="__main__":unittest.main()
