"""Source contract tests only; WeiDU and actual EET compilation require user game."""
import pathlib
import re
import unittest

BAF = pathlib.Path(__file__).with_name('BGXAI_WEAPON_SLOT_CONSUMER_V3.baf')


def blocks(src):
    return [(conds, actions) for conds, actions in re.findall(
        r'\bIF\n(.*?)\nTHEN\n\s+RESPONSE #100\n(.*?)\nEND\b', src,
        re.DOTALL)]


class TestWeaponConsumer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = BAF.read_text(encoding='utf-8')
        cls.blocks = blocks(cls.src)

    def test_exactly_four_slots(self):
        self.assertEqual(len(self.blocks),4)
        for i, (conds, actions) in enumerate(self.blocks):
            self.assertIn(f'Global("BGXW3_REQ","LOCALS",{i+1})',conds)
            self.assertIn(f'HasItemSlot(Myself,SLOT_WEAPON{i})',conds)
            self.assertIn(f'SelectWeaponAbility(SLOT_WEAPON{i},0)',actions)
            self.assertEqual(len(re.findall(r'SelectWeaponAbility\(',actions)),1)

    def test_all_blocks_preserve_eps_and_manual_queue(self):
        for conds,_ in self.blocks:
            for guard in (
                'InParty(Myself)', '!InPartySlot(Myself,0)',
                'Global("BGX38_GUARD","LOCALS",1)',
                'Global("BGX66_S_HEAL_SLOT","LOCALS",0)',
                'GlobalTimerNotExpired("BGXW3_LEASE","LOCALS")',
                'ActionListEmpty()', 'ModalState(NONE)',
                '!StateCheck(Myself,STATE_PANIC)',
                '!StateCheck(Myself,STATE_HELPLESS)'):
                self.assertIn(guard,conds)

    def test_enemy_filters(self):
        for conds,_ in self.blocks:
            for guard in ('See(NearestEnemyOf(Myself))',
                          '!InParty(NearestEnemyOf(Myself))',
                          '!Allegiance(NearestEnemyOf(Myself),GOODCUTOFF)'):
                self.assertIn(guard,conds)

    def test_exactly_one_switch_and_req_reset(self):
        for _, actions in self.blocks:
            steps=[line.strip() for line in actions.splitlines() if line.strip()]
            self.assertEqual(len(steps),2)
            self.assertTrue(steps[0].startswith('SelectWeaponAbility('))
            self.assertEqual(steps[1],'SetGlobal("BGXW3_REQ","LOCALS",0)')

    def test_no_attack_heal_dispel_inventory_or_action_override(self):
        for _, actions in self.blocks:
            self.assertNotRegex(actions, r'\b(Attack|Spell|Cast|UseItem|MoveTo|RunAway|FillSlot|EquipItem|ActionOverride|CreateItem|ApplySpell|StartDialog|ClearAllActions)\s*\(')

    def test_no_untrusted_producer_in_source(self):
        self.assertNotRegex(self.src,r'(?<!\w)(SetGlobalTimer|SetGlobal)\("BGXW3_LEASE"')
        self.assertEqual(len(re.findall(r'SetGlobal\("BGXW3_REQ","LOCALS",0\)',self.src)),4)

    def test_tight_unique_action_ids(self):
        slots=re.findall(r'(?m)^\s+SelectWeaponAbility\(SLOT_WEAPON([0-3]),0\)',self.src)
        self.assertEqual(slots,['0','1','2','3'])

    def test_request_is_fail_closed_when_not_raised(self):
        for i, (conds, _) in enumerate(self.blocks):
            self.assertIn(f'Global("BGXW3_REQ","LOCALS",{i+1})',conds)
            self.assertIn('GlobalTimerNotExpired',conds)

    def test_not_proven_runtime(self):
        self.assertIn('SOURCE ONLY',self.src)
        self.assertIn('NOT INSTALLED',self.src)


if __name__=='__main__':
    unittest.main()
