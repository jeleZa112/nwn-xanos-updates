"""Structural offline verification for 061 BCS 20-rule receiver and 060 baseline preservation."""
import unittest, pathlib, sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import BGXAI61_BUILDER as b
from generate_baf import generate

def block(ids,label,final=False):
    acts=b''.join(b'AC\n'+str(x).encode()+b'OB\nOB\nAC\n' for x in ids)
    return b'CR\nCO\n'+label+b'\nCO\nRS\nRP\n100\n'+acts+b'RS\nCR\n'+(b'SC\n' if final else b'')

def base():
    parts=[]
    for i in range(1071):
        if 1031<=i<1045:
            acts=b.OLD_ACTIONS[i-1031];label=b'LOCALSBGX52_REQ_SLOT\nBGX60_LAST_BRANCH\n'+str(i).encode()
        else:
            acts=[42] if i<1031 else [105]
            label=b'LOCALSBGX38_GUARD\n'+str(i).encode()
        parts.append(block(acts,label,final=i==1070))
    return b'SC\n'+b''.join(parts)

def candidate():
    return b'SC\n'+b''.join(block(actions,b'LOCALSBGX52_REQ_SLOT\nBGX61_LAST_BRANCH\n'+str(i).encode(),final=i==19) for i,actions in enumerate(b.NEW_ACTIONS))

class Tests(unittest.TestCase):
    def test_twenty_rules_six_paths_each_and_cleanup(self):
        src=generate()
        self.assertEqual(src.count('\nIF\n'),20)
        self.assertEqual(src.count('AttackReevaluate('),6)
        self.assertEqual(src.count('MoveToObject('),6)
        self.assertEqual(src.count('ProtectObject('),6)
        self.assertEqual(src.count('InMyArea('),18)
        self.assertEqual(src.count('ActionListEmpty()'),18)
        self.assertEqual(src.count('ModalState(NONE)'),18)
    def test_correct_fixed_slot_targets(self):
        src=generate()
        for slot in range(1,7):
            self.assertEqual(src.count('Global("BGX52_REQ_SLOT","LOCALS",'+str(slot)+')'),3)
            self.assertIn('MoveToObject(Player'+str(slot)+')',src)
            self.assertIn('AttackReevaluate(LastAttackerOf(Player'+str(slot)+'),30)',src)
            self.assertIn('ProtectObject(Player'+str(slot)+',6)',src)
    def test_approach_not_only_close(self):
        src=generate();start=src.index('// P3: approach');end=src.index('END',start)
        approach=src[start:end]
        self.assertIn('!Range(Player3,10)',approach)
        self.assertIn('Range(Player3,40)',approach)
        self.assertIn('InMyArea(Player3)',approach)
        self.assertNotIn('See(Player3)',approach)
        self.assertIn('MoveToObject(Player3)',approach)
        self.assertNotIn('SetGlobal("BGX52_REQ_SLOT","LOCALS",0)',approach)
        self.assertIn('SetGlobalTimer("BGX52_EXPIRE","LOCALS",20)',approach)
        self.assertIn('SetGlobalTimer("BGX52_COOLDOWN","LOCALS",2)',approach)
    def test_manual_commands_and_eps_not_interrupted(self):
        s=generate()
        for forbidden in ['ClearActions(', 'ActionOverride(', 'ReallyForceSpell(', 'Spell(', 'MoveToObjectNoInterrupt(', 'MoveToObjectFollow(']:
            self.assertNotIn(forbidden,s)
        self.assertEqual(s.count('Global("BGX38_GUARD","LOCALS",1)'),18)
    def test_action_sequence_exact(self):
        self.assertEqual(b.NEW_ACTIONS,[[30,36],[30,36]]+[[30,115,30,30,134]]*6+[[115,115,30,30,22]]*6+[[30,115,30,30,87]]*6)
    def test_splice_only_receiver_changed(self):
        old=base();new,proof=b.splice(old,candidate(),old_pin=b.sha(old))
        self.assertEqual(proof['final_blocks'],1077)
        self.assertTrue(proof['eps_unchanged'])
        old_blocks=b.split(old,1071);new_blocks=b.split(new,1077)
        self.assertEqual(old_blocks[:1031],new_blocks[:1031])
        self.assertEqual(old_blocks[1045:],new_blocks[1051:])
        self.assertEqual([b.actions(x) for x in new_blocks[1031:1051]],b.NEW_ACTIONS)
    def test_reject_bad_baseline_sha(self):
        with self.assertRaisesRegex(ValueError,'SHA_MISMATCH'):b.splice(base(),candidate())
    def test_reject_060_rule_perturbation(self):
        original=base().replace(b'LOCALSBGX52_REQ_SLOT',b'LOCALSCORRUPT_REQ_SLOT',1)
        with self.assertRaisesRegex(ValueError,'NO_Q_MARKER'):b.splice(original,candidate(),old_pin=b.sha(original))
    def test_reject_malicious_action_in_fragment(self):
        wrong=candidate().replace(b'AC\n22OB\n',b'AC\n3OB\n',1)
        with self.assertRaisesRegex(ValueError,'ACTIONS_CHANGED'):b.splice(base(),wrong,old_pin=b.sha(base()))
    def test_reject_bad_footer(self):
        with self.assertRaisesRegex(ValueError,'FOOTER_INVALID'):b.splice(base(),candidate()[:-3],old_pin=b.sha(base()))
    def test_no_implicit_install_in_builder(self):
        s=pathlib.Path(b.__file__).read_text()
        for bad in ['--force-install','--force-uninstall','def install(','os.replace(']:self.assertNotIn(bad,s)

if __name__=='__main__':unittest.main(verbosity=2)
