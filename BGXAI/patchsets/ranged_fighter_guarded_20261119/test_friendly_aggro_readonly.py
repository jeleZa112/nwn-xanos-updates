#!/usr/bin/env python3
"""Non-game tests for read-only BCS friendly fire investigation."""
import pathlib,sys,unittest
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import BGX_FRIENDLY_AGGRO_AUDIT_READONLY as A

class FriendlyAudit(unittest.TestCase):
 def test_bcs_lossless_three(self):
  raw=b"SC\n"+b"CR\nCO\nA\nCR\n"+b"CR\nCO\nB\nCR\nSC\n"
  parts=A.parts(raw)
  self.assertEqual(len(parts),2)
  self.assertEqual(b"SC\n"+b"".join(parts),raw)
 def test_parse_baf(self):
  baf="IF\n  AttackedBy([ANYONE],DEFAULT)\nTHEN\n  RESPONSE #100\n    Attack(LastAttackerOf(Myself))\nEND\n"
  blocks=A.parse_baf(baf)
  self.assertEqual(len(blocks),1)
  hit=A.classify(blocks[0],1)
  self.assertIn("MEMORIZED_ATTACKER_TARGET",hit["risk"])
  self.assertIn("NO_EXPLICIT_FRIENDLY_FILTER_IN_THIS_BLOCK",hit["risk"])
 def test_guarded_last_attacker(self):
  baf="IF\n  See(LastAttackerOf(Myself))\n  !InParty(LastAttackerOf(Myself))\nTHEN\n  RESPONSE #100\n    AttackReevaluate(LastAttackerOf(Myself),30)\nEND\n"
  hit=A.classify(A.parse_baf(baf)[0],1)
  self.assertNotIn("NO_EXPLICIT_FRIENDLY_FILTER_IN_THIS_BLOCK",hit["risk"])
 def test_nearest_enemy_unfiltered(self):
  b=A.parse_baf("IF\n  See(NearestEnemyOf(Myself))\nTHEN\n  RESPONSE #100\n    AttackOneRound(NearestEnemyOf(Myself))\nEND\n")[0]
  self.assertIn("NO_EXPLICIT_FRIENDLY_FILTER_IN_THIS_BLOCK",A.classify(b,1)["risk"])
 def test_no_attack_or_last_attacker(self):
  b=A.parse_baf("IF\n  True()\nTHEN\n  RESPONSE #100\n    DisplayStringHead(Myself,1)\nEND\n")[0]
  self.assertIsNone(A.classify(b,1))
 def test_game_guard_no_write(self):
  import inspect
  src=inspect.getsource(A)
  self.assertIn("TemporaryDirectory(",src)
  self.assertIn('input_bcs.write_bytes(raw)',src)
  self.assertNotIn("weidu(root,uninstall",src)
  self.assertNotIn("--force-install",src)
  self.assertNotIn("--force-uninstall",src)
if __name__=="__main__":unittest.main()
