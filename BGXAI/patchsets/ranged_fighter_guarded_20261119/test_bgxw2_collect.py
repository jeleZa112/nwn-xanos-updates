import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import BGXW2_OBSERVER_GUARDED as m

SESSION={'type':'SESSION','schema':m.R2_SCHEMA,'utc':'UNKNOWN','readOnly':True}
READY={'type':'READY','schema':m.R2_SCHEMA,'hookRegistered':True}
def slot(i):return {'index':i,'access':'OBJECT_RETURNED_UNVERIFIED','resrefRaw':'BOW05' if i==35 else None,
    'identityVerified':False,'usableVerified':False,'ammoVerified':False,'useCount1Raw':2}
def entry(seq=1, selected=12):
    return {'type':'SLOTS','schema':m.R2_SCHEMA,'seq':seq,'partyIndex':2,'actor':139135050,
      'selectedWeaponRaw':selected,'selectedAbilityRaw':0,'status':'RAW_FIXED_SLOTS_OBSERVED_IDENTITY_UNKNOWN',
      'quickWeapons':[slot(x) for x in [35,36,37,38]],
      'quivers':[slot(x) for x in [11,12,13,14]],
      'offhand':slot(9), 'itemIdentityVerified':False,'perSlotAPRVerified':False,
      'manualOrderOriginVerified':False,'epsQueueVerified':False,'switchAuthorized':False}

class Collector(unittest.TestCase):
 def setUp(self):
    t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup)
    self.folder=Path(t.name)
    self.log=self.folder/'BGXAI_WEAPON_CONSOLE_20261121120000Z.log'
 def put(self,*records):
    with self.log.open('w',encoding='utf-8') as f:
        for record in records:f.write('EEEX: [BGXW2] '+json.dumps(record)+'\n')
 def test_no_console(self):
    self.assertEqual(m.collect_report(self.folder)['status'],'R2_CONSOLE_CAPTURE_ABSENT')
 def test_normal_2_actions(self):
    self.put(SESSION,READY,entry(),entry(2,35))
    r=m.collect_report(self.folder);self.assertEqual(r['status'],'R2_CONSOLE_RAW_COLLECTED')
    self.assertEqual(r['actions'],2)
    stored=[json.loads(l) for l in (self.folder/m.R2_LOG).read_text().splitlines()]
    self.assertEqual(stored[-1]['selectedWeaponRaw'],35)
 def test_duplicate_console_suppressed(self):
    self.put(SESSION,READY,entry(),entry(),entry(2),entry(2))
    self.assertEqual(m.collect_report(self.folder)['actions'],2)
 def test_conflicting_seq_stop(self):
    self.put(SESSION,READY,entry(),entry(1,35))
    with self.assertRaisesRegex(ValueError,'SEQ_CONFLICT'):m.collect_report(self.folder)
 def test_unknown_flags_rejected(self):
    b=entry();b['switchAuthorized']=True;self.put(SESSION,READY,b)
    self.assertEqual(m.collect_report(self.folder)['status'],'R2_CONSOLE_INCOMPLETE_HOLD')
 def test_invalid_slot_order_rejected(self):
    b=entry();b['quickWeapons'][0]['index']=36;self.put(SESSION,READY,b)
    self.assertEqual(m.collect_report(self.folder)['status'],'R2_CONSOLE_INCOMPLETE_HOLD')
 def test_invalid_item_ref_rejected(self):
    b=entry();b['quickWeapons'][0]['resrefRaw']='bad/../';self.put(SESSION,READY,b)
    self.assertEqual(m.collect_report(self.folder)['status'],'R2_CONSOLE_INCOMPLETE_HOLD')
 def test_latest_session_only(self):
    self.put(SESSION,READY,entry(),SESSION,READY,entry(10,35))
    self.assertEqual(m.collect_report(self.folder)['actions'],1)
 def test_session_missing_is_hold(self):
    self.put(READY,entry());self.assertEqual(m.collect_report(self.folder)['status'],'R2_CONSOLE_INCOMPLETE_HOLD')
 def test_ready_missing_is_hold(self):
    self.put(SESSION,entry());self.assertEqual(m.collect_report(self.folder)['status'],'R2_CONSOLE_INCOMPLETE_HOLD')
 def test_direct_report_persist(self):
    f=self.folder/m.R2_LOG;f.write_text('\n'.join(json.dumps(x) for x in (SESSION,READY,entry()))+'\n')
    result=m.collect_report(self.folder);self.assertEqual(result['status'],'R2_DIRECT_RAW_READY')
    self.assertEqual(result['actions'],1)
 def test_direct_report_not_overwritten(self):
    f=self.folder/m.R2_LOG;f.write_text('ORIGINAL')
    self.put(SESSION,READY,entry())
    r=m.collect_report(self.folder);self.assertEqual(r['status'],'R2_DIRECT_RAW_PRESERVED')
    self.assertEqual(f.read_text(),'ORIGINAL')
 def test_symlink_raw_rejected(self):
    f=self.folder/m.R2_LOG;f.symlink_to(self.folder/'missing')
    with self.assertRaisesRegex(ValueError,'SYMLINK'):m.collect_report(self.folder)
 def test_symlink_console_ignored(self):
    self.log.symlink_to(self.folder/'missing')
    self.assertEqual(m.collect_report(self.folder)['status'],'R2_CONSOLE_CAPTURE_ABSENT')
 def test_oversize_rejected(self):
    self.log.write_bytes(b'z'*(m.MAX_CAPTURE+1))
    self.assertEqual(m.collect_report(self.folder)['status'],'R2_CONSOLE_CAPTURE_SIZE_HOLD')

if __name__=='__main__':unittest.main(verbosity=2)
