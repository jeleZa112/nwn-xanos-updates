#!/usr/bin/env python3
"""No-game regression tests for surgical BGX38/39 ProtectObject isolation."""
from pathlib import Path
from unittest import mock
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
import BGX_FRIENDLY_PROTECT_ISOLATION as S
import BGXRANGED_PREFLIGHT as P
def sample_bcs():
    return b"SC\n"+b"".join(
        b"CR\nCO\n"+str(i).encode()+b"\nCR\n"+(b"SC\n" if i==1173 else b"")
        for i in range(1,1174))
def sample_baf_blocks():
    arr=[dict(conditions=["True()"],actions=["RESPONSE #100","NoAction()"])
         for _ in range(1173)]
    for n in S.DISABLE:
        arr[n-1]={"conditions":['Global("BGX38_GUARD","LOCALS",1)',"ActionListEmpty()"],
                  "actions":["RESPONSE #100","ProtectObject(Player2,6)",'SetGlobalTimer("BGX39_TEAM_CD","LOCALS",2)']}
    return arr
class IsolationTests(unittest.TestCase):
    def test_exact_known_positions(self):
        self.assertEqual(S.DISABLE,tuple(range(1078,1089)))
        self.assertEqual(S.NEW_COUNT,1162)
    def test_compilation_preserves_other_blocks(self):
        original=sample_bcs();self.assertEqual(len(P.parts(original)),1173)
        with mock.patch.object(S,"parse_baf",return_value=sample_baf_blocks()):
            patched=S.candidate(original,"synthetic decompilation")
        self.assertEqual(len(P.parts(patched)),1162)
        self.assertEqual(P.parts(patched),
            [x for i,x in enumerate(P.parts(original),1) if i not in S.DISABLE])
    def test_refuses_unknown_action_inside_protect(self):
        arr=sample_baf_blocks()
        arr[1077]["actions"].append("Spell(Player2,CLERIC_CURE_LIGHT_WOUNDS)")
        with mock.patch.object(S,"parse_baf",return_value=arr):
            with self.assertRaisesRegex(ValueError,"OTHER_ACTION"):
                S.candidate(sample_bcs(),"synthetic decompilation")
    def test_refuses_missing_guard_gate(self):
        block=sample_baf_blocks()[1077]
        block["conditions"].remove('Global("BGX38_GUARD","LOCALS",1)')
        with self.assertRaisesRegex(ValueError,"NO_GUARD_GATE"):
            S.verify_protect(block,1078)
    def test_refuses_wrong_target_or_range(self):
        block=sample_baf_blocks()[1077];block["actions"][1]="ProtectObject(NearestEnemyOf(Myself),8)"
        with self.assertRaisesRegex(ValueError,"NOT_EXACT_PROTECT"):
            S.verify_protect(block,1078)
    def test_no_auto_game_write_for_status_or_preflight(self):
        import inspect
        code=inspect.getsource(S.main)
        self.assertIn("if opts.mode==\"status\"",code)
        self.assertIn('elif opts.mode=="preflight"',code)
        self.assertIn("INSTALL_NOT_AUTHORIZED",code)
        self.assertIn("ROLLBACK_NOT_AUTHORIZED",code)
    def test_no_direct_weidu_before_backup(self):
        import inspect
        s=inspect.getsource(S.install)
        self.assertLess(s.index("snap=safe_backup(root)"),s.index("wei(root)"))
    def test_weidu_error_no_retry(self):
        p=mock.Mock(returncode=1,stdout="",stderr="ERROR: forced")
        with mock.patch.object(S.subprocess,"run",return_value=p) as run:
            with self.assertRaisesRegex(ValueError,"WEIDU_STOP_MANUAL_INSPECTION"):
                S.wei(S.ROOT)
            self.assertEqual(run.call_count,1)
    def test_last_component_before_rollback(self):
        with mock.patch.object(S.V3.V2.V1,"processes"),mock.patch.object(
                S,"status",return_value={"status":"BGXSAFE_PROTECT_ISOLATION_INSTALLED_VERIFIED"}),mock.patch.object(
                S.V3,"last",return_value="~OTHER/SETUP-OTHER.TP2~ #0 #0"):
            with self.assertRaisesRegex(ValueError,"NOT_LAST_COMPONENT"):
                S.rollback(S.ROOT)
if __name__=="__main__":unittest.main()
