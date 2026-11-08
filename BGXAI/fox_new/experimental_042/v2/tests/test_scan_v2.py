"""Synthetic structural checks; real installed compiled BCS NOT redistributed."""
import hashlib
import re
import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import scan_eps_bcs_v2 as m


def fake_block(trigs, acts):
    c=''.join('TR\n'+t+'\n0 0 0 0 0 0 0 0 0 0 0 0 ""OB\nTR\n' for t in trigs)
    a='RE\n100AC\n'
    for idx,act in enumerate(acts):
        if idx:a+='AC\n'
        a+=str(act)+'OB\n0 0 0 0 0 0 0 0 0 0 0 0 ""OB\nOB\n0 0 0 0 0 0 0 0 0 0 0 0 ""OB\nOB\n0 0 0 0 0 0 0 0 0 0 0 0 ""OB\n0 0 0 0 0"" "" AC\n'
    return 'CR\nCO\n'+c+'CO\nRS\n'+a+'RE\nRS\nCR\n'


class TestScanner(unittest.TestCase):
    def test_first_action_in_response(self):
        data=('SC\n'+fake_block(['16427 0 0 0 0 "" "" OB'],[3,87])+'SC\n').encode('ascii')
        parsed=m.parse(data)
        self.assertEqual(parsed[0]['action_ids'],[3,87])
        self.assertTrue(parsed[0]['action_list_empty'])
        r=m.inspect(data)
        self.assertEqual(r['attack_block_numbers'],[1]);self.assertEqual(r['protect_block_numbers'],[1])
    def test_single_first_action(self):
        data=('SC\n'+fake_block([], [31])+'SC\n').encode('ascii')
        self.assertEqual(m.parse(data)[0]['action_ids'],[31])
    def test_action_ids_count_without_duplication(self):
        data=('SC\n'+fake_block([], [86,34,86])+'SC\n').encode('ascii')
        self.assertEqual(m.inspect(data)['global_actions'],{'34':1,'86':2})
    def test_empty_script_fails(self):
        with self.assertRaises(ValueError):m.parse(b'SC\nSC\n')
    def test_lock_rejects_unknown_hash(self):
        data=('SC\n'+fake_block([], [3])+'SC\n').encode('ascii')
        with self.assertRaisesRegex(ValueError,'Wrong target BCS'):m.in_memory_preview(data)
    def test_mutating_raw_guard_string_is_not_preview(self):
        data=('SC\n'+fake_block(['16399 1 0 0 0 "LOCALSBGX38_GUARD" "" OB'], [87])+'SC\n').encode('ascii')
        with self.assertRaises(ValueError):m.in_memory_preview(data)
    def test_input_file_read_only_contract(self):
        self.assertEqual(m.GUARD_OFF_TRIGGER.count('BGX38_GUARD'),1)
        self.assertNotIn('write_bytes(',Path(m.__file__).read_text())
        self.assertNotIn('unlink(',Path(m.__file__).read_text())
    def test_explicit_attack_and_guard_ids(self):
        self.assertEqual(m.ACTION_NAMES[3],'Attack')
        self.assertEqual(m.ACTION_NAMES[87],'ProtectObject')
        self.assertEqual(m.ID_ACTION_LIST_EMPTY,16427)

if __name__=='__main__':unittest.main()
