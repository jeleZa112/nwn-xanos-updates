"""Standalone Python 3.10+ source-only unit tests, no EET installation."""
import unittest
from fractions import Fraction
from apr_key_decoder_ro import decode_source_apr_key, compare_source_keys_only


class AprDecoderReadOnlyTests(unittest.TestCase):
    def test_documented_mapping(self):
        expected = [0, 1, 2, 3, 4, 5, .5, 1.5, 2.5, 3.5, 4.5]
        for raw, value in enumerate(expected):
            with self.subTest(key=raw):
                d = decode_source_apr_key(raw)
                self.assertEqual(d.source_value, Fraction(str(value)))
                self.assertEqual(d.state, 'SOURCE_KEY_DECODED_RO')
                self.assertFalse(d.effective_apr_verified)
                self.assertFalse(d.per_slot_apr_verified)
                self.assertFalse(d.weapon_switch_authorized)

    def test_real_live_range_and_melee_values(self):
        ranged, melee = decode_source_apr_key(2), decode_source_apr_key(7)
        self.assertEqual(ranged.source_value, Fraction(2))
        self.assertEqual(melee.source_value, Fraction(3, 2))
        self.assertGreater(7, 2)
        self.assertLess(melee.source_value, ranged.source_value)

    def test_invalid_keys_hold(self):
        for raw in (True, False, '7', 7.0, 7.5, -1, 11, 255, None, [], {}):
            with self.subTest(key=raw):
                d = decode_source_apr_key(raw)
                self.assertEqual(d.state, 'HOLD')
                self.assertIsNone(d.source_value)
                self.assertFalse(d.weapon_switch_authorized)

    def test_non_ranking_output(self):
        out = compare_source_keys_only(2, 7)
        self.assertEqual(out['state'], 'SOURCE_KEYS_BOTH_DECODED_RO')
        self.assertTrue(out['raw_numeric_comparison_forbidden'])
        self.assertTrue(out['does_not_rank_weapons'])
        self.assertFalse(out['weapon_switch_authorized'])

    def test_unknown_never_comparable(self):
        self.assertEqual(compare_source_keys_only(11, 2)['state'], 'HOLD')
        self.assertEqual(compare_source_keys_only(2, None)['state'], 'HOLD')


if __name__ == '__main__':
    unittest.main()
