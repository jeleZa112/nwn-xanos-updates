"""Fail-closed standalone test suite. Synthetic fixtures != native game validation."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from BGXAI_WEAPON_SELECTED_EVIDENCE_BRIDGE_RO_V1 import analyze_text, analyze_file

F = {'m_nArmorClass': 10, 'm_nACCrushingMod': 0, 'm_nACMissileMod': 0,
     'm_nACPiercingMod': 0, 'm_nACSlashingMod': 0, 'm_nResistCrushing': 0,
     'm_nResistPiercing': 0, 'm_nResistSlashing': 0, 'm_nResistMissile': 0}


def make(source_apr=7, slot=35, target=135137293, status='TARGET_RAW_DEFENSE_FIELDS_CANDIDATE_ONLY'):
    r13 = {'type': 'DEFENSE', 'seq': 1, 'partyIndex': 2, 'sourceActor': 139266124,
           'targetActor': target, 'selectedSlot': slot, 'rawActionId': 3,
           'status': status, 'fields': F.copy(), 'weaponSwitchAuthorized': False,
           'exactHitChanceProven': False, 'allProtectionsObserved': False}
    r4 = {'type': 'ACTIVE', 'seq': 42, 'partyIndex': 2, 'actor': 139266124,
          'selectedWeaponRaw': slot, 'actionRaw': 3,
          'statsRaw': {'m_nNumberOfAttacks': source_apr}}
    r1 = {'type': 'ACTION', 'sequence': 42, 'partyIndex': 2,
          'actor': 139266124, 'selectedWeaponRaw': slot, 'action': 3,
          'aprRaw': source_apr, 'weaponSwitchAuthorized': False}
    r2 = {'type': 'SLOTS', 'seq': 42, 'partyIndex': 2,
          'actor': 139266124, 'selectedWeaponRaw': slot, 'actionRaw': 3,
          'itemIdentityVerified': False, 'perSlotAPRVerified': False,
          'quickWeapons': [{'index': 35, 'resrefRaw': 'SW1H04'}],
          'quivers': [{'index': 12, 'resrefRaw': 'AROW01'}]}
    return r13, r4, r1, r2


def render(events):
    lines = ['INFO: LUA: [BGXTD13] {"type":"SESSION"}',
             'INFO: LUA: [BGXTD13] {"type":"READY","hookRegistered":true}']
    for group, obj in events:
        lines.append('INFO: LUA: [' + group + '] ' + json.dumps(obj))
    return '\n'.join(lines) + '\n'


class BridgeTests(unittest.TestCase):
    def fixture(self, **kwargs):
        events = make(**kwargs)
        return [('BGXTD13', events[0]), ('BGXW2', events[3]),
                ('BGXW4', events[1]), ('BGXWP', events[2])]

    def test_ammo_slot_and_source_apr(self):
        out = analyze_text(render(self.fixture(slot=12, source_apr=2)))
        self.assertEqual(out['status'], 'CURRENT_SELECTED_EVIDENCE_CAPTURED_RO')
        o = out['observations'][0]
        self.assertEqual(o['sourceAprValue'], '2')
        self.assertEqual(o['sourceItemRefRaw'], 'AROW01')
        self.assertFalse(o['dispatchAuthorized'])
        self.assertFalse(o['itemIdentityVerified'])

    def test_sword_raw_7_is_one_and_half_not_seven(self):
        out = analyze_text(render(self.fixture(slot=35, source_apr=7)))
        self.assertEqual(out['status'], 'CURRENT_SELECTED_EVIDENCE_CAPTURED_RO')
        self.assertEqual(out['observations'][0]['sourceAprValue'], '3/2')
        self.assertEqual(out['observations'][0]['sourceItemRefRaw'], 'SW1H04')
        self.assertFalse(out['alternateSlotAprVerified'])

    def test_fist_slot_is_not_item_resource(self):
        out = analyze_text(render(self.fixture(slot=10)))
        self.assertEqual(out['status'], 'CURRENT_SELECTED_EVIDENCE_CAPTURED_RO')
        self.assertIsNone(out['observations'][0]['sourceItemRefRaw'])

    def test_no_session_is_hold(self):
        s=render(self.fixture()).splitlines()
        out=analyze_text('\n'.join(s[2:]))
        self.assertEqual(out['status'], 'HOLD_INCOMPLETE_EVIDENCE')
        self.assertEqual(out['observations'][0]['reason'], 'R13_IDENTITY_OR_SESSION_INVALID')

    def test_missing_r1_is_hold(self):
        out=analyze_text(render(self.fixture()[:-1]))
        self.assertEqual(out['observations'][0]['reason'], 'R1_R2_R4_PAIRING_NOT_UNIQUE_OR_MISSING')

    def test_duplicate_r4_is_hold(self):
        items=self.fixture()
        out=analyze_text(render([*items, items[2]]))
        self.assertEqual(out['observations'][0]['reason'], 'R1_R2_R4_PAIRING_NOT_UNIQUE_OR_MISSING')

    def test_raw_apr_unknown_is_hold(self):
        out=analyze_text(render(self.fixture(source_apr=11)))
        self.assertEqual(out['observations'][0]['reason'], 'UNKNOWN_CURRENT_APR_KEY')

    def test_apr_conflicting_observers_hold(self):
        events=self.fixture()
        events[-1][1]['aprRaw']=2
        out=analyze_text(render(events))
        self.assertEqual(out['observations'][0]['reason'], 'R1_R2_R4_EVIDENCE_CONFLICT')

    def test_null_defense_field_hold(self):
        events=self.fixture()
        events[0][1]['fields']['m_nResistMissile']=None
        out=analyze_text(render(events))
        self.assertEqual(out['observations'][0]['reason'], 'R13_TARGET_FIELDS_MISSING_OR_INVALID')

    def test_r13_hold_never_counted_as_pass(self):
        out=analyze_text(render(self.fixture(status='HOLD')))
        self.assertEqual(out['observations'][0]['reason'], 'R13_TARGET_DEFENSE_NOT_FULLY_READ')

    def test_forbidden_claim_in_source_hold(self):
        events=self.fixture()
        events[0][1]['weaponSwitchAuthorized']=True
        out=analyze_text(render(events))
        self.assertEqual(out['observations'][0]['reason'], 'R13_PROVENANCE_FLAGS_UNEXPECTED')

    def test_null_r4_stats_hold_not_crash(self):
        events=self.fixture();events[2][1]['statsRaw']=None
        out=analyze_text(render(events))
        self.assertEqual(out['observations'][0]['reason'], 'R1_R2_R4_EVIDENCE_CONFLICT')

    def test_malformed_source_event_hold(self):
        s=render(self.fixture())+'INFO: LUA: [BGXWP] {garbage}\n'
        out=analyze_text(s)
        self.assertEqual(out['status'], 'HOLD_MALFORMED_SOURCE_EVENTS')

    def test_duplicate_lprint_never_double_counted(self):
        s=render(self.fixture())
        s+='INFO: LPRINT: [BGXTD13] '+json.dumps(self.fixture()[0][1])+'\n'
        out=analyze_text(s)
        self.assertEqual(out['r13DefenseCount'],1)

    def test_real_file_is_read_only(self):
        text=render(self.fixture())
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'console.log'; p.write_text(text,encoding='utf-8')
            before=p.read_bytes();out=analyze_file(p)
            self.assertEqual(out['status'],'CURRENT_SELECTED_EVIDENCE_CAPTURED_RO')
            self.assertEqual(p.read_bytes(),before)
            self.assertFalse(out['gameModified'])

    def test_nonexistent_input_rejected(self):
        with self.assertRaises(ValueError):
            analyze_file(Path('/a/path/that/is/not/a/file.txt'))

    def test_real_user_console_four_valid_events(self):
        # Test needs the user file only when present; synthetic tests are portable.
        p=Path('/mnt/data/BGXAI_R13_2_CONSOLE_20261123T064924087770Z.log')
        if not p.is_file(): self.skipTest('Real conversation attachment not on CI runner')
        result=analyze_file(p)
        self.assertEqual(result['status'],'CURRENT_SELECTED_EVIDENCE_CAPTURED_RO')
        self.assertEqual(result['r13DefenseCount'],4)
        self.assertEqual([x['sourceAprValue'] for x in result['observations']],['2','2','2','3/2'])
        self.assertEqual([x['selectedSlot'] for x in result['observations']], [12,12,12,35])
        self.assertTrue(all(x['dispatchAuthorized'] is False for x in result['observations']))


if __name__=='__main__': unittest.main()
