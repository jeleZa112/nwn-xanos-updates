import unittest
from class_action_contract import validate

def member(slot=2,id=100):
    result={'slot':slot,'id':id,'guard_f':1,'modal':0,'class_id':2,
            'current_action_id':0}
    result.update({k:'unknown' for k in (
        'equipped_weapon','can_melee','can_cast','manual_order_absent',
        'action_queue_idle','stealth_absent','consciousness','role')})
    return result

def env(party=None):
    return {'schema':2,'mode':'READ_ONLY','origin':'BGXAI_062E_SOURCE_ONLY',
            'binding':'X64_EEEX_SOURCE_DOCUMENTED_RUNTIME_UNVERIFIED',
            'status':'PARTIAL_OBSERVATIONS_ONLY','party':party if party is not None else [member()]}

class ClassActionTest(unittest.TestCase):
    def test_one(self):
        r=validate(env());self.assertEqual(r.members[0].class_id,2)
        self.assertFalse(r.members[0].intercept_authorized)
    def test_unknown_allowed(self):
        r=member();r['class_id']='unknown';r['current_action_id']='unknown'
        self.assertFalse(validate(env([r])).members[0].intercept_authorized)
    def test_class_not_role(self):
        r=member();r['role']='frontline'
        with self.assertRaisesRegex(ValueError,'UNPROVEN'):validate(env([r]))
    def test_action_zero_not_manual_clear(self):
        r=member();r['action_queue_idle']=True
        with self.assertRaisesRegex(ValueError,'UNPROVEN'):validate(env([r]))
    def test_weapon_not_inferred(self):
        r=member();r['equipped_weapon']='SW1H01'
        with self.assertRaisesRegex(ValueError,'UNPROVEN'):validate(env([r]))
    def test_melee_not_inferred(self):
        r=member();r['can_melee']=True
        with self.assertRaisesRegex(ValueError,'UNPROVEN'):validate(env([r]))
    def test_no_api_empty(self):
        p=env([]);p['status']='API_UNAVAILABLE';self.assertEqual(validate(p).members,())
    def test_no_api_nonempty(self):
        p=env();p['status']='API_UNAVAILABLE'
        with self.assertRaises(ValueError):validate(p)
    def test_duplicate_slot(self):
        with self.assertRaises(ValueError):validate(env([member(),member(id=200)]))
    def test_duplicate_id(self):
        with self.assertRaises(ValueError):validate(env([member(),member(slot=3)]))
    def test_bad_class(self):
        p=env();p['party'][0]['class_id']=256
        with self.assertRaises(ValueError):validate(p)
    def test_bad_action(self):
        p=env();p['party'][0]['current_action_id']=-1
        with self.assertRaises(ValueError):validate(p)
    def test_boolean_class(self):
        p=env();p['party'][0]['class_id']=True
        with self.assertRaises(ValueError):validate(p)
    def test_boolean_action(self):
        p=env();p['party'][0]['current_action_id']=False
        with self.assertRaises(ValueError):validate(p)
    def test_boolean_guard(self):
        p=env();p['party'][0]['guard_f']=True
        with self.assertRaises(ValueError):validate(p)
    def test_bad_provenance(self):
        p=env();p['binding']='RUNTIME_VERIFIED'
        with self.assertRaises(ValueError):validate(p)
    def test_bad_schema(self):
        p=env();p['schema']=True
        with self.assertRaises(ValueError):validate(p)
    def test_missing_proven_fields(self):
        p=env();p['party'][0].pop('role')
        with self.assertRaises(ValueError):validate(p)
    def test_max_party(self):
        p=env([member(i,100+i) for i in range(1,7)])
        self.assertEqual(len(validate(p).members),6)
    def test_over_max_party(self):
        p=env([member(i,100+i) for i in range(1,8)])
        with self.assertRaises(ValueError):validate(p)
    def test_id_zero(self):
        p=env([member(id=0)])
        self.assertEqual(validate(p).members[0].id,0)

if __name__=='__main__':unittest.main()
