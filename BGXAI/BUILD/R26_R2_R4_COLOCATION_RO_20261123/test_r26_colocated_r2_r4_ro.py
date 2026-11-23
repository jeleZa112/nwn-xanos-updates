"""R26 synthetic negative/positive contract tests; zero native / game access."""
import json
import unittest
import sys
from pathlib import Path
# Reuse R25 in its canonical GitHub BUILD folder; local offline fallback only.
root = Path(__file__).resolve().parent.parent
reused = root / "R25_CAPTURE_SEGMENT_SOURCE_ONLY_20261123"
sys.path.insert(0, str(reused if reused.exists() else root))
from BGXAI_R26_COLOCATED_R2_R4_RO import inspect, SCHEMA


def event(source, kind, seq=1):
    if source == 'BGXW2':
        e = dict(schema='BGXAI_WEAPON_SLOTS_RAW_R2', type=kind)
        if kind == 'SESSION': e['readOnly'] = True
        elif kind == 'READY': e['hookRegistered'] = True
        else:
            e.update(seq=seq, partyIndex=2, actor=111, actionRaw=3,
                     selectedWeaponRaw=12, selectedAbilityRaw=0,
                     status='RAW_FIXED_SLOTS_OBSERVED_IDENTITY_UNKNOWN',
                     itemIdentityVerified=False, perSlotAPRVerified=False,
                     manualOrderOriginVerified=False, epsQueueVerified=False,
                     switchAuthorized=False)
        return e
    e = dict(schema='BGXAI_WEAPON_ACTIVE_R4',type=kind)
    if kind == 'SESSION':e['readOnly'] = True
    elif kind == 'READY':e['hookRegistered'] = True
    else:
        e.update(seq=seq, partyIndex=2, actor=111, actionRaw=3,
                 selectedWeaponRaw=12, selectedAbilityRaw=0,
                 presentCount=68, missingCount=0,
                 status='RAW_CURRENT_SELECTED_STATS_OBSERVED_NOT_COMPLETE_EFFECTS',
                 statsRaw={'m_nNumberOfAttacks':2},
                 allBuffsObserved=False, allEffectsObserved=False,
                 alternateSlotAPRVerified=False, manualOrderProven=False,
                 epsQueueProven=False, weaponSwitchAuthorized=False,
                 dispatchAuthorized=False)
    return e


def fixture(n=2):
    records=[('BGXW2',event('BGXW2','SESSION')),('BGXW2',event('BGXW2','READY')),
             ('BGXW4',event('BGXW4','SESSION')),('BGXW4',event('BGXW4','READY'))]
    for seq in range(1,n+1):
        records.extend([('BGXW2',event('BGXW2','SLOTS',seq)),
                        ('BGXW4',event('BGXW4','ACTIVE',seq))])
    return records


def serialize(records, mirrors=True):
    lines=[]
    for source,e in records:
        payload=json.dumps(e,separators=(',',':'))
        lines.append(f'INFO: LUA: [{source}] {payload}')
        if mirrors and source=='BGXW2':
            lines.append(f'INFO: LPRINT: [{source}] {payload}')
    return ('\n'.join(lines)+'\n').encode()


class R26Contract(unittest.TestCase):
    def assert_hold(self, data, reason=None):
        v=inspect(data)
        self.assertEqual(v['status'],'HOLD_CROSS_OBSERVER_AUTHENTICATION')
        if reason:self.assertEqual(v['reason'],reason)
        for k in ['gameActionsAuthorized','dispatchAuthorized','weaponSwitchAuthorized','nativeEventAuthenticated']:
            self.assertIs(v[k],False)
        self.assertEqual(v['ordersSent'],0)

    def test_valid_two(self):
        v=inspect(serialize(fixture()))
        self.assertEqual(v['schema'],SCHEMA)
        self.assertEqual(v['pairedCount'],2)
        self.assertEqual(v['selectedAprSummary'],{'slot_12_rawAPR_2':2})
        self.assertEqual(v['actionRawCounts'],{'3':2})
        self.assertEqual(v['r25MirrorPairsRemoved'],4)
        for k in ['nativeEventAuthenticated','fullEffectsVerified','alternativeAPRVerified','launcherAmmoPairVerified','manualEpsQueueVerified','safeSessionIdentityVerified','dispatchAuthorized','weaponSwitchAuthorized']:
            self.assertIs(v[k],False)
    def test_valid_one(self):self.assertEqual(inspect(serialize(fixture(1)))['pairedCount'],1)
    def test_valid_without_mirrors(self):self.assertEqual(inspect(serialize(fixture(),False))['pairedCount'],2)
    def test_slot_mismatch(self):
        f=fixture();f[5][1]['selectedWeaponRaw']=35
        self.assert_hold(serialize(f),'CORRELATED_ACTION_SCALAR_MISMATCH')
    def test_ability_mismatch(self):
        f=fixture();f[5][1]['selectedAbilityRaw']=1
        self.assert_hold(serialize(f),'CORRELATED_ACTION_SCALAR_MISMATCH')
    def test_action_mismatch(self):
        f=fixture();f[5][1]['actionRaw']=23
        self.assert_hold(serialize(f),'CORRELATED_ACTION_SCALAR_MISMATCH')
    def test_actor_mismatch(self):
        f=fixture();f[5][1]['actor']=222
        self.assert_hold(serialize(f))
    def test_party_mismatch(self):
        f=fixture();f[5][1]['partyIndex']=1
        self.assert_hold(serialize(f),'CORRELATED_ACTION_SCALAR_MISMATCH')
    def test_sequence_mismatch(self):
        f=fixture();f[5][1]['seq']=10
        self.assert_hold(serialize(f),'CORRELATED_ACTION_SCALAR_MISMATCH')
    def test_reordered_events(self):
        f=fixture();f[4],f[5]=f[5],f[4]
        self.assert_hold(serialize(f),'R2_R4_NOT_ADJACENT_IN_TAGGED_LUA_STREAM')
    def test_missing_r4(self):self.assert_hold(serialize(fixture()[:-1]),'DIFFERENT_OBSERVER_EVENT_COUNTS')
    def test_missing_r2(self):
        f=fixture();f.pop(4)
        self.assert_hold(serialize(f),'DIFFERENT_OBSERVER_EVENT_COUNTS')
    def test_second_session(self):
        f=fixture(1);f+=fixture(1)
        self.assert_hold(serialize(f),'NOT_EXACTLY_ONE_R2_AND_ONE_R4_CAPTURE_SEGMENT')
    def test_selected_apr_invalid(self):
        f=fixture();f[5][1]['statsRaw']['m_nNumberOfAttacks']=22
        self.assert_hold(serialize(f),'SELECTED_APR_RAW_UNTRUSTED')
    def test_selected_apr_bool_not_int(self):
        f=fixture();f[5][1]['statsRaw']['m_nNumberOfAttacks']=True
        self.assert_hold(serialize(f),'SELECTED_APR_RAW_UNTRUSTED')
    def test_r2_optimistic_identity(self):
        f=fixture();f[4][1]['itemIdentityVerified']=True
        self.assert_hold(serialize(f),'FALSIFIED_RUNTIME_AUTHORIZATION_OR_INCOMPLETE_EFFECT_FLAGS')
    def test_r4_optimistic_eps(self):
        f=fixture();f[5][1]['epsQueueProven']=True
        self.assert_hold(serialize(f),'FALSIFIED_RUNTIME_AUTHORIZATION_OR_INCOMPLETE_EFFECT_FLAGS')
    def test_r4_optimistic_dispatch(self):
        f=fixture();f[5][1]['dispatchAuthorized']=True
        self.assert_hold(serialize(f))
    def test_r4_optimistic_effects(self):
        f=fixture();f[5][1]['allBuffsObserved']=True
        self.assert_hold(serialize(f),'FALSIFIED_RUNTIME_AUTHORIZATION_OR_INCOMPLETE_EFFECT_FLAGS')
    def test_dangling_mirror(self):
        x=serialize(fixture())
        x+=x.splitlines()[-1]+b'\n'
        self.assert_hold(x)
    def test_harmful_mirror_drift(self):
        x=serialize(fixture()).replace(b'INFO: LPRINT: [BGXW2]',b'INFO: LPRINT: [BGXW4]',1)
        self.assert_hold(x)
    def test_missing_ready(self):
        f=fixture();f.pop(1)
        self.assert_hold(serialize(f))
    def test_multiple_actor_same_seq(self):
        f=fixture();f[6][1]['actor']=222;f[7][1]['actor']=222
        self.assert_hold(serialize(f),'R25_CAPTURE_VALIDATION_FAILED')
    def test_non_string_bytes(self):self.assert_hold('text')
    def test_oversize(self):self.assert_hold(b'a'*(2_000_001))
    def test_no_data(self):self.assert_hold(b'')
    def test_malicious_apr_plus(self):
        f=fixture();f[5][1]['statsRaw']['m_nNumberOfAttacks']=7
        v=inspect(serialize(f))
        self.assertEqual(v['selectedAprSummary'],{'slot_12_rawAPR_2':1,'slot_12_rawAPR_7':1})
        self.assertIs(v['alternativeAPRVerified'],False)
    def test_unrecognized_status(self):
        f=fixture();f[4][1]['status']='ALL_VERIFIED'
        self.assert_hold(serialize(f),'SOURCE_OBSERVER_STATUS_UNRECOGNIZED')

if __name__=='__main__':unittest.main()
