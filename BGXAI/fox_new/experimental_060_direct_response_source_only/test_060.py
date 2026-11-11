"""Structural tests of REAL 060 byte splicer with synthetic compiled BCS fixtures.
No game files, WeiDU, Windows, or engine behavior are simulated as verified.
"""
import unittest, pathlib, sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import BGXAI60_BUILDER as b
from generate_baf import generate


def block(ids,label,final=False):
    actions=b''.join(b'AC\n'+str(i).encode()+b'OB\nOB\nAC\n' for i in ids)
    return b'CR\nCO\n'+label+b'\nCO\nRS\nRP\n100\n'+actions+b'RS\nCR\n'+(b'SC\n' if final else b'')


def base():
    arr=[]
    for i in range(1065):
        if 1031<=i<1039:
            acts=b.OLD_ACTIONS[i-1031];label=b'LOCALSBGX52_REQ_SLOT\nTRIGGER'+str(i).encode()
        else:
            acts=[42] if i<1031 else [105]
            label=b'LOCALSBGX38_GUARD\n'+str(i).encode()
        arr.append(block(acts,label,final=i==1064))
    return b'SC\n'+b''.join(arr)


def candidate():
    return b'SC\n'+b''.join(block(acts,b'LOCALSBGX52_REQ_SLOT\nBGX60_LAST_BRANCH\n'+str(i).encode(),final=i==13)
                            for i,acts in enumerate(b.NEW_ACTIONS))


class TestSafety(unittest.TestCase):
    def test_response_contains_12_guard_paths(self):
        s=generate()
        self.assertEqual(s.count('\nIF\n'),14)
        self.assertEqual(s.count('AttackReevaluate('),6)
        self.assertEqual(s.count('ProtectObject('),6)
        self.assertEqual(s.count('ActionListEmpty()'),12)
        self.assertEqual(s.count('GlobalTimerNotExpired("BGX52_EXPIRE","LOCALS")'),13)
        for forbidden in ['ClearActions(', 'ActionOverride(', 'Spell(', 'ReallyForceSpell(']:
            self.assertNotIn(forbidden,s)

    def test_reaction_paths_every_victim_slot(self):
        s=generate()
        for i in range(1,7):
            self.assertEqual(s.count('Global("BGX52_REQ_SLOT","LOCALS",'+str(i)+')'),2)
            self.assertIn('AttackReevaluate(LastAttackerOf(Player'+str(i)+'),30)',s)
            self.assertIn('ProtectObject(Player'+str(i)+',6)',s)
        self.assertEqual(s.count('SetGlobal("BGX60_LAST_BRANCH","LOCALS",1)'),6)
        self.assertEqual(s.count('SetGlobal("BGX60_LAST_BRANCH","LOCALS",2)'),6)

    def test_splice_verifies_eps_bytes_unchanged(self):
        old=base();frag=candidate();res,proof=b.splice(old,frag,old_pin=b.sha(old))
        self.assertTrue(proof['eps_unchanged'])
        self.assertEqual(proof['old_blocks'],1065)
        self.assertEqual(proof['final_blocks'],1071)
        orig=b.split(old,1065);mod=b.split(res,1071)
        self.assertEqual(orig[:1031],mod[:1031])
        self.assertEqual(orig[1039:],mod[1045:])
        self.assertEqual([b.actions(x) for x in mod[1031:1045]],b.NEW_ACTIONS)

    def test_reject_wrong_sha(self):
        with self.assertRaisesRegex(ValueError,'SHA_MISMATCH'):b.splice(base(),candidate())

    def test_reject_modified_056_receiver(self):
        raw=base().replace(b'LOCALSBGX52_REQ_SLOT',b'OTHER____REQ_SLOT',1)
        with self.assertRaisesRegex(ValueError,'NO_Q_MARKER'):
            b.splice(raw,candidate(),old_pin=b.sha(raw))

    def test_reject_wrong_compiled_actions(self):
        bad=candidate().replace(b'AC\n134OB\n',b'AC\n87OB\n',1)
        with self.assertRaisesRegex(ValueError,'ACTIONS_CHANGED'):
            b.splice(base(),bad,old_pin=b.sha(base()))

    def test_reject_removed_compiled_q(self):
        bad=candidate().replace(b'LOCALSBGX52_REQ_SLOT',b'LOCALSOTHER_____SLOT',1)
        with self.assertRaisesRegex(ValueError,'NO_Q_MARKER'):
            b.splice(base(),bad,old_pin=b.sha(base()))

    def test_reject_bad_footer(self):
        with self.assertRaisesRegex(ValueError,'FOOTER_INVALID'):
            b.splice(base(),candidate()[:-3],old_pin=b.sha(base()))

    def test_early_blocks_unchanged_before_eps(self):
        old=base();res,_=b.splice(old,candidate(),old_pin=b.sha(old))
        self.assertEqual(b.split(old,1065)[0],b.split(res,1071)[0])

    def test_no_install_function(self):
        src=pathlib.Path(b.__file__).read_text()
        for word in ['--force-install','--force-uninstall','setup-BGX60.tp2','def install(', 'os.replace(']:
            self.assertNotIn(word,src)

if __name__=='__main__':unittest.main(verbosity=2)
