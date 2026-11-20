#!/usr/bin/env python3
"""No EET required: installer fail-closed and live observer invariants."""
import hashlib
import inspect
from pathlib import Path
from unittest import mock
import unittest
import BGX_FRIEND_TRACE_GUARDED as M

DIR=Path(__file__).resolve().parent
class BGXFTests(unittest.TestCase):
 def test_source_is_exactly_pinned(self):
  self.assertEqual(hashlib.sha256((DIR/"M_BXFR.lua").read_bytes()).hexdigest(),M.TRACE_HASH)
  self.assertEqual(M.source_bytes(),(DIR/"M_BXFR.lua").read_bytes())
 def test_existing_five_mods_immutable(self):
  self.assertEqual(len(M.BASE),5)
  self.assertEqual(M.BASE["override/BDDEFAI.BCS"],"9bd4e5b413f60ba383fcb78859f9bfe0aab762ee8b0ec2b3f164b6c03377055e")
  self.assertEqual(M.BASE["override/M_BX43.lua"],"74ddc016e15fae3451bafe3039b299740c9d2efae8ecfb3e86badea257fa650c")
 def test_only_one_new_override_file_in_tp2(self):
  copies=[l for l in M.TP2_DATA.splitlines() if l.startswith("COPY ")]
  self.assertEqual(copies,["COPY ~BGXFTRACE/staged/M_BXFR.lua~ ~override/M_BXFR.lua~"])
  self.assertNotIn('BDDEFAI.BCS',M.TP2_DATA)
  self.assertNotIn('M_BX43.lua',M.TP2_DATA)
 def test_authorization_and_backup_before_game_write(self):
  s=inspect.getsource(M.install)
  self.assertLess(s.index("snap=backup(root)"),s.index('(root/STAGED).write_bytes(source_bytes())'))
  self.assertLess(s.index('snap=backup(root)'),s.index('weidu(root)'))
  self.assertIn('APPROVAL_INSTALL="INSTALL_BGXFTRACE_PASSIVE_OBSERVER"',(DIR/'BGX_FRIEND_TRACE_GUARDED.py').read_text())
 def test_preflight_failure_prevents_weidu(self):
  with mock.patch.object(M.V3.V2.V1,"processes"),mock.patch.object(M,"preflight",side_effect=ValueError("bad source")),mock.patch.object(M,"weidu") as runner:
   with self.assertRaisesRegex(ValueError,'bad source'):M.install(M.ROOT)
   runner.assert_not_called()
 def test_rollback_requires_guarded_last(self):
  with mock.patch.object(M.V3.V2.V1,"processes"),mock.patch.object(M,"status",return_value={"status":"BGXFTRACE_INSTALLED_VERIFIED"}),mock.patch.object(M,"last",return_value="~OTHER/SETUP.TP2~ #0 #0"):
   with self.assertRaisesRegex(ValueError,"NOT_LAST_TRACE_COMPONENT"):M.rollback(M.ROOT)
 def test_runtime_observer_has_no_game_actions(self):
  t=(DIR/'M_BXFR.lua').read_text()
  for action in ('ClearActions(', 'Attack(', 'ProtectObject(', 'Spell(', 'SetGlobal(', 'EEex_Action_Queue'):
   self.assertNotIn(action,t)
  self.assertIn('origin=UNKNOWN',t)
  self.assertIn('EEex_Action_AddSpriteStartedActionListener',t)
  self.assertIn('io.open(FILE,"w")',t)
if __name__=='__main__':unittest.main()
