#!/usr/bin/env python3
"""Pure synthetic regression tests; optionally real-log replay via env variable."""
from __future__ import annotations
import json
from pathlib import Path
import unittest
import BGXAI_R38_RUNTIME_GATE_V1 as gate


def fake_rows():
    out = []
    for i, t in enumerate(gate.PREFIXES[:3]):
        out.append(t + json.dumps({"schema": gate.SCHEMAS[i], "type": "SESSION"}) + "\n")
    for seq, party, actor, action, q in [(1, 2, 222, 23, 0), (2, 1, 111, 30, 2),
                                         (3, 1, 111, 23, 0), (4, 1, 111, 23, 0)]:
        for i, tag in enumerate(gate.PREFIXES):
            record = {
                "schema":gate.SCHEMAS[i], "type":gate.TYPES[i],
                "seq":seq, "partyIndex":party, "readOnly":True,
                "ordersSent":0, "dispatchAuthorized":False,
            }
            if i == 0:
                record.update(actor=actor,actionRaw=action,queuedActionsRaw=q,
                              actionOriginVerified=False,manualEpsQueueVerified=False)
            if i == 3:
                record.update(status=gate.MATCH if party == 1 else gate.OTHER,
                              armAuthorized=False,localsWritten=0,
                              safeActionBoundaryVerified=False)
            out.append(tag + json.dumps(record) + "\n")
    return out


def mutate(lines, seq, stream, **fields):
    rows = list(lines)
    for i, line in enumerate(rows):
        if gate.PREFIXES[stream] not in line:
            continue
        record=json.loads(line.split(gate.PREFIXES[stream],1)[1])
        if record.get("seq") == seq:
            record.update(fields)
            rows[i]=gate.PREFIXES[stream] + json.dumps(record) + "\n"
            return rows
    raise AssertionError('missing fixture target')


class GateTests(unittest.TestCase):
    def test_realistic_synthetic_pass_to_hold_idle(self):
        r=gate.audit_lines(fake_rows())
        self.assertEqual(r['status'],'HOLD_SAFE_IDLE_AND_SESSION_AUTHENTICATION_NOT_PROVEN')
        self.assertEqual(r['jaganMatchingEvents'],3)
        self.assertEqual(r['otherActorFilteredEvents'],1)
        self.assertEqual(r['moveToPointObservedInJaganEvents'],2)
        self.assertEqual(r['nonemptyQueueObservedInJaganEvents'],1)
        self.assertIs(r['sameRuntimeActorAcrossJaganEvents'],True)
        for k in ('safeActionBoundaryVerified','savedGAMSessionIdentityVerified',
                  'armAuthorized','dispatchAuthorized','manualEpsActionOriginVerified'):
            self.assertIs(r[k],False)
        self.assertIs(r['ordersSent'],0)
        self.assertNotIn('111',json.dumps(r))
        self.assertNotIn('222',json.dumps(r))

    def assert_hold(self, lines, reason=None):
        r=gate.audit_lines(lines)
        self.assertEqual(r['status'],'HOLD_UNTRUSTED_R38_CAPTURE')
        if reason:self.assertEqual(r['reason'],reason)
        self.assertFalse(r['armAuthorized'])
        self.assertFalse(r['dispatchAuthorized'])
        self.assertEqual(r['ordersSent'],0)

    def test_jagan_actor_changes(self):
        self.assert_hold(mutate(fake_rows(),3,0,actor=991),'HOLD_ACTOR_CHANGED_OR_COLLIDED')

    def test_jagan_actor_collision(self):
        self.assert_hold(mutate(fake_rows(),1,0,actor=111),'HOLD_ACTOR_CHANGED_OR_COLLIDED')

    def test_mismatched_party_by_stream(self):
        self.assert_hold(mutate(fake_rows(),2,1,partyIndex=2),'HOLD_PARTY_MISMATCH_PER_EVENT')

    def test_other_actor_claims_match(self):
        self.assert_hold(mutate(fake_rows(),1,3,status=gate.MATCH),
                         'HOLD_JAGAN_STATUS_FOR_WRONG_PARTY')

    def test_jagan_unmatched(self):
        self.assert_hold(mutate(fake_rows(),2,3,status=gate.OTHER),'HOLD_EXPECTED_JAGAN_REJECTED')

    def test_silently_removed_event(self):
        x=[v for v in fake_rows() if '"seq": 4' not in v or '[BGXID]' not in v]
        self.assert_hold(x,'HOLD_FOUR_STREAM_SEQ_MISMATCH')

    def test_duplicate_event(self):
        x=fake_rows();x.append(x[-1]);self.assert_hold(x,'HOLD_DUPLICATE_SEQ')

    def test_global_arming_marker_rejected(self):
        self.assert_hold(mutate(fake_rows(),2,3,armAuthorized=True),
                         'HOLD_IDENTITY_RECORD_NOT_PASSIVE')

    def test_locals_write_rejected(self):
        self.assert_hold(mutate(fake_rows(),2,3,localsWritten=1),
                         'HOLD_IDENTITY_RECORD_NOT_PASSIVE')

    def test_fake_session(self):
        self.assert_hold(fake_rows()+[gate.PREFIXES[0]+json.dumps({
                         'schema':gate.SCHEMAS[0],'type':'SESSION'})+'\n'],
                         'HOLD_SESSION_MARKERS_UNEXPECTED')

    def test_unknown_action_does_not_authorize(self):
        r=gate.audit_lines(mutate(fake_rows(),3,0,actionRaw=999))
        self.assertFalse(r['safeActionBoundaryVerified'])
        self.assertFalse(r['armAuthorized'])

    def test_zero_queue_does_not_authorize(self):
        lines=fake_rows()
        for n in (2,3,4):lines=mutate(lines,n,0,queuedActionsRaw=0)
        r=gate.audit_lines(lines)
        self.assertFalse(r['zeroQueueIsIdleProof'])
        self.assertFalse(r['armAuthorized'])

    def test_invalid_queue_hold(self):
        self.assert_hold(mutate(fake_rows(),3,0,queuedActionsRaw='0'),
                         'HOLD_QUEUE_RAW_UNREADABLE')

    def test_missing_session(self):
        x=fake_rows()[1:]
        self.assert_hold(x,'HOLD_SESSION_MARKERS_UNEXPECTED')

    def test_malicious_json_string(self):
        x=fake_rows();x.append(gate.PREFIXES[2]+'not-json\n')
        self.assert_hold(x,'HOLD_INVALID_R38_JSON')

    def test_no_matches(self):
        x=[v for v in fake_rows() if '"seq": 2' not in v and
           '"seq": 3' not in v and '"seq": 4' not in v]
        self.assert_hold(x,'HOLD_NO_REAL_JAGAN_MATCH')


if __name__ == '__main__':unittest.main()