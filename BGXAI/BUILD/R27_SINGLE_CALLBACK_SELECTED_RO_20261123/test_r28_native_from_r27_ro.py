import hashlib
from pathlib import Path
import json
import tempfile
import unittest
from unittest import mock
import BGXAI_R28_NATIVE_FROM_R27_RO as r

REAL=Path('/mnt/data/BGXAI_R27_CONSOLE_20261123T163105828183Z.log')

class TestR28(unittest.TestCase):
    def test_real_user_log(self):
        if not REAL.is_file(): self.skipTest('only when local real user file available')
        got=r.capture_extract(REAL.read_bytes())
        self.assertEqual(got['r27ConfirmedCallbacks'],24)
        self.assertEqual(got['r27SessionMarkers'],1)
        self.assertEqual(got['actorCount'],1)
        self.assertEqual(got['observedRawItemResrefs'],['AROW01','BOW05','STAF01','SW1H04'])
        self.assertEqual(got['samplesSelectedOnly'][22]['selectedSlotRaw'],35)
    def fake_log(self,names=('SW1H04','AROW01'),changes=None):
        rows=[{'schema':r.R27_SCHEMA,'type':'SESSION'}]
        x={'schema':r.R27_SCHEMA,'type':'R27_SINGLE_CALLBACK',
           'seq':1,'actor':10,'partyIndex':2,'actionRaw':23,
           'selectedWeaponRaw':35,'selectedAbilityRaw':0,'selectedAprKeyRaw':7,
           'status':'CURRENT_SELECTED_SAME_CALLBACK_SOURCE_CANDIDATE',
           'sameLuaListenerInvocation':True,'ordersSent':0,'localsWritten':0,
           'dispatchAuthorized':False,'weaponSwitchAuthorized':False,'readOnly':True,
           'quickWeaponsRaw':[{'slot':35+i,'resrefRaw':names[0] if i==0 else None} for i in range(4)],
           'quiversRaw':[{'slot':11+i,'resrefRaw':names[1] if i==0 else None} for i in range(4)]}
        if changes: x.update(changes)
        rows.append(x)
        return b'\n'.join((b'INFO: LUA: [BGXR27] '+json.dumps(e,separators=(',',':')).encode()) for e in rows)
    def test_positive(self):
        z=r.capture_extract(self.fake_log())
        self.assertEqual(z['observedRawItemResrefs'],['AROW01','SW1H04'])
        self.assertEqual(z['samplesSelectedOnly'][0]['selectedAprKeyRaw'],7)
    def test_missing_session(self):
        raw=self.fake_log().split(b'\n')[1]
        with self.assertRaisesRegex(r.StopReadOnly,'SESSION'):r.capture_extract(raw)
    def test_duplicate_session(self):
        raw=self.fake_log();start=raw.split(b'\n')[0]
        with self.assertRaisesRegex(r.StopReadOnly,'SESSION_AMBIGUOUS'):r.capture_extract(start+b'\n'+raw)
    def test_unknown_origin_denies_dispatch(self):
        with self.assertRaisesRegex(r.StopReadOnly,'NOT_SAFE'):r.capture_extract(self.fake_log(changes={'dispatchAuthorized':True}))
    def test_wrong_seq_fails(self):
        with self.assertRaisesRegex(r.StopReadOnly,'NONCONTIGUOUS'):r.capture_extract(self.fake_log(changes={'seq':2}))
    def test_bad_resref_fails(self):
        with self.assertRaisesRegex(r.StopReadOnly,'RESREF_INVALID'):r.capture_extract(self.fake_log(names=('../NO','AROW01')))
    def test_missing_items_fails(self):
        with self.assertRaisesRegex(r.StopReadOnly,'ITEM_SET_UNAVAILABLE'):r.capture_extract(self.fake_log(names=(None,None)))
    def test_source_pin(self):
        p=Path(r.__file__).parent/r.R3_NAME
        if not p.is_file(): self.skipTest('source artifact outside package')
        self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),r.R3_SHA256)
        self.assertTrue(hasattr(r.source_r3(p.parent),'NativeSource'))
    def test_positive_native_mock_and_report(self):
        class NativeMock:
            class NativeSource:
                def __init__(self,root):pass
            def audit(self,source,names,ctx):
                assert names==['AROW01','SW1H04']
                assert ctx['sampleCount']==1
                return {'status':'ITM_NATIVE_ALL_ITEMS_RAW_READ','items':{'SW1H04':{},'AROW01':{}},'missingItemsOrLinkedSpells':[]}
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);(p/'BGXAI_R27_CONSOLE_TEST.log').write_bytes(self.fake_log())
            x=r.native_audit(p,{'status':'R27_PASSIVE_INSTALLED_AWAITING_RUNTIME_TEST'},lambda:None,p,NativeMock())
            self.assertEqual(x['status'],'R28_NATIVE_ITEMS_RAW_READ_AWAITING_REVIEW')
            self.assertEqual(x['itemsRead'],2)
            self.assertFalse(x['weaponSwitchAuthorized'])
            d=json.loads(Path(x['reportFile']).read_text())
            self.assertFalse(d['effectiveAlternateAPRVerified'])
            self.assertFalse(d['manualAndEPSQueueVerified'])
    def test_not_installed(self):
        with self.assertRaisesRegex(r.StopReadOnly,'NOT_INSTALLED'):
            r.native_audit(Path('/bad'),{'status':'R27_NOT_INSTALLED'},lambda:None)

if __name__=='__main__':unittest.main()
