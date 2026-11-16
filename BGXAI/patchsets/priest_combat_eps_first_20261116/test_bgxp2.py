#!/usr/bin/env python3
import hashlib,re,unittest
from pathlib import Path
import BGXP2_BCS_PATCH as P
ROOT=Path(__file__).parent
class TestCombatPriest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baf=(ROOT/'BGXP2_LAST_PRIORITY.baf').read_text(encoding='utf-8')
        cls.blocks=re.findall(r'(?m)^IF\n(.*?)\nEND\n',cls.baf,re.S)
    def test_00_released_28_BCS_actions(self):
        self.assertEqual(len(self.blocks),28)
        self.assertEqual(self.baf.count('    Spell('),26)
        self.assertEqual(self.baf.count('AttackOneRound('),2)
        self.assertEqual(self.baf.count('ClearActions('),0)
        self.assertEqual(self.baf.count('ForceSpell('),0)
    def test_01_f_and_idle_all(self):
        for block in self.blocks:
            self.assertIn('Global("BGX38_GUARD","LOCALS",1)',block)
            self.assertIn('Global("BGX66_S_HEAL_SLOT","LOCALS",0)',block)
            self.assertIn('ActionListEmpty()',block)
            self.assertIn('!InPartySlot(Myself,0)',block)
            self.assertIn('ModalState(NONE)',block)
            self.assertIn('Global("BGXR_ROLE","LOCALS",',block)
    def test_02_aid_only_verified_bad_states(self):
        for mode in ['SUPPORT','AUTO']:
            for suffix in ['FEAR','POISON']:
                self.assertEqual(self.baf.count('BGXP2 '+mode+' '+suffix+' slot '),6)
        for spell,state in [('CLERIC_REMOVE_FEAR','STATE_PANIC'),('CLERIC_SLOW_POISON','STATE_POISONED')]:
            self.assertEqual(self.baf.count('HaveSpell('+spell+')'),12)
            self.assertEqual(self.baf.count('StateCheck(Player1,'+state+')'),2)
    def test_03_off_and_healer_untouched(self):
        for b in self.blocks:
            self.assertNotIn('Global("BGXR_ROLE","LOCALS",0)',b)
            self.assertNotIn('Global("BGXR_ROLE","LOCALS",1)',b)
        self.assertNotIn('CLERIC_CURE_LIGHT_WOUNDS',self.baf)
        self.assertNotIn('BGXR_MOVE_CD',self.baf)
    def test_04_threat_guards(self):
        b=[x for x in self.blocks if 'AttackOneRound(' in x]
        self.assertEqual(len(b),2)
        for x in b:
            self.assertIn('See(NearestEnemyOf(Myself))',x)
            self.assertIn('Range(NearestEnemyOf(Myself),12)',x)
            self.assertIn('HPPercentGT(Myself,60)',x)
        self.assertEqual(len([x for x in b if 'Global("BGXR_ROLE","LOCALS",4)' in x]),1)
        self.assertIn('!HPPercentLT(Player6,45)',b[-1])
    def test_05_base_bcs_mock_splice_and_restore(self):
        unit=b'CR\nCO\nTR\nRS\nRE\nRS\nCR\n'
        base=b'SC\n'+unit*P.BASE_BLOCKS+b'SC\n'
        original_pin=P.BCS_PIN
        def fragment_block(a):
            raw=b'CR\nCO\nTR\nRS\nRE\nRS\nBGXR_ROLE BGX38_GUARD BGX66_S_HEAL_SLOT\n'
            for num in a:raw+=b'AC\n'+str(num).encode()+b'OB\nX\n'
            return raw+b'CR\n'
        actions=[[115,31]]*26+[[115,105],[115,105]]
        # Match generated source order: 24 cures, battle spell/attack, auto spell/attack.
        actions=[[115,31]]*25+[[115,105],[115,31],[115,105]]
        fragment=b'SC\n'+b''.join(fragment_block(a) for a in actions)+b'SC\n'
        try:
            P.BCS_PIN=hashlib.sha256(base).hexdigest()
            merged,stats=P.splice(base,fragment)
            self.assertEqual(stats['old_blocks_preserved'],1130)
            self.assertEqual(stats['appended_blocks'],28)
            chunks=P.chunks(merged,1158)
            restored=b'SC\n'+b''.join(chunks[:1129]+[chunks[1129]+b'SC\n'])
            self.assertEqual(restored,base)
            with self.assertRaisesRegex(ValueError,'UNTRUSTED_LIVE_BCS_SHA'):P.splice(base+b'X',fragment)
            bad=fragment.replace(b'AC\n105OB\n',b'AC\n3OB\n',1)
            with self.assertRaises(ValueError):P.verify_fragment(bad)
        finally:P.BCS_PIN=original_pin
    def test_06_immutable_installed_pins(self):
        self.assertEqual(P.BASE_BLOCKS,1130)
        self.assertEqual(P.ADDED,28)
        self.assertEqual(P.LUA_PIN,'74ddc016e15fae3451bafe3039b299740c9d2efae8ecfb3e86badea257fa650c')
        self.assertEqual(P.BCS_PIN,'75ffb7160f5a0dc61579f70236c0c6ac50b83974c31138094a799139188d7e13')
if __name__=='__main__':unittest.main(verbosity=2)
