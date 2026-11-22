import copy,hashlib,json,unittest
from pathlib import Path
from BGXAI_R10_EVIDENCE_AUDIT_RO import audit
MATRIX=Path('evidence/BGXAI_WEAPON_R4_R3_EVIDENCE_MATRIX_20261122.json')
class Audit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=MATRIX.read_bytes();cls.original=json.loads(cls.raw)
        cls.sha=hashlib.sha256(cls.raw).hexdigest()
    def go(self,fn,reason):
        d=copy.deepcopy(self.original);fn(d)
        r=audit(d,self.sha)
        self.assertEqual(r['reason'],reason);self.assertFalse(r['weaponSwitchAuthorized'])
    def test_accept_actual_evidence_but_hold(self):
        r=audit(self.original,self.sha)
        self.assertEqual(r['status'],'HOLD_REAL_R3_R4_MATRIX_INCOMPLETE_NO_NATIVE_RANKING')
        self.assertEqual(len(r['rows']),3)
        self.assertEqual({x['weaponResRef'] for x in r['rows']},{'BOW05','STAF01','SW1H04'})
        self.assertTrue(all(x['targetHitProbability'] is None for x in r['rows']))
        self.assertTrue(all(x['aprOfAlternativeAtCurrentTime'] is None for x in r['rows']))
        self.assertFalse(r['dispatchAuthorized'])
    def test_bad_schema(self):self.go(lambda d:d.update(schema='OTHER'),'MATRIX_SCHEMA_OR_STATUS')
    def test_bad_correlation(self):self.go(lambda d:d['correlation'].update(r2Events=15),'CORRELATION_MISMATCH')
    def test_missing_actor(self):self.go(lambda d:d.update(actors=[]),'ACTOR_SET_UNEXPECTED')
    def test_other_actor(self):self.go(lambda d:d['actors'][0].update(actorId=9),'ACTOR_CONTEXT_MISMATCH')
    def test_replay(self):self.go(lambda d:d['actors'][0]['selections'][0].update(sequence=16),'SELECTION_SEQUENCE_INVALID')
    def test_invalid_apr(self):self.go(lambda d:d['actors'][0]['selections'][0].update(aprDecodedIfStandard=99), 'BASE_DAMAGE_PRODUCT_MISMATCH')
    def test_illegal_native_claim(self):self.go(lambda d:d['actors'][0]['selections'][0].update(otherSlotAPRProjected=True),'FORBIDDEN_VERIFICATION_OR_ACTION_CLAIM')
    def test_loss_effect_warning(self):self.go(lambda d:d['actors'][0]['selections'][0].update(nativeItemContainsUnverifiedEquippedEffects=False),'MISSING_UNVERIFIED_EFFECT_WARNING')
    def test_launcher_claim_mismatch(self):self.go(lambda d:d['actors'][0]['selections'][0].update(ammunitionResRef='AROW02'),'AMMO_LAUNCHER_ASSOCIATION_INVALID')
    def test_change_damage(self):self.go(lambda d:d['actors'][0]['selections'][0].update(staticBaseDamageTimesSelectedAPR_NotDPS=2),'BASE_DAMAGE_PRODUCT_MISMATCH')
    def test_missing_gate(self):self.go(lambda d:d['rankingGate'].update(weaponSwitchAuthorized=True),'GATE_OR_MISSING_EVIDENCE_CHANGED')
if __name__=='__main__': unittest.main(verbosity=2)
