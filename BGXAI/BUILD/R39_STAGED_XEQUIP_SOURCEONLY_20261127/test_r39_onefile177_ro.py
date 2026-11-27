"""Onefile177 strictly source-only mock regression. NO Windows game I/O."""
from pathlib import Path
import hashlib
import json
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch
import BGXAI_R39_ONEFILE177_RO as p


class Onefile177(unittest.TestCase):
    def test_exact_published_baf_pin(self):
        x=Path(__file__).with_name('BGXAI_R39_JAGAN_STAF01_SOURCE_ONLY.baf').read_bytes()
        self.assertEqual(len(x),p.SOURCES[p.B][0])
        self.assertEqual(p.digest(x),p.SOURCES[p.B][1])

    def test_no_extra_executables_or_installers(self):
        s=Path(p.__file__).read_text('utf-8')
        for forbidden in ('--force-install','--force-uninstall', 'SetGlobal("BGXW3ARM",',
                          'ClearActions(', 'setup-BGXR39.exe','WeiDU.log'):
            self.assertNotIn(forbidden,s)
        self.assertIn('TemporaryDirectory(',s)
        self.assertIn('subprocess.DEVNULL',s)

    def test_bad_commit_denied(self):
        for x in ('', 'main', 'a'*39, 'z'*40, 4, None):
            with self.subTest(x=x),self.assertRaises(p.Hold):p.check_pin(x)

    def test_invalid_fetch_source_denied(self):
        with self.assertRaises(p.Hold):p.verify('other',b'')
        with self.assertRaises(p.Hold):p.fetch('a'*40,'does/not/exist')

    def test_sha_mismatch_denied(self):
        with self.assertRaisesRegex(p.Hold,'HOLD_SOURCE_SHA_DRIFT'):
            p.verify(p.B,b'a'*p.SOURCES[p.B][0])

    def fixtures(self):
        raws={x:x.encode('ascii') for x in p.SOURCES}
        hashes={x:(len(raw),p.digest(raw)) for x,raw in raws.items()}
        return raws, hashes

    def success_response(self):
        return {'status':'R39_NATIVE_EET_TEMP_COMPILE_PASS_NO_INSTALL',
                'nativeWeiDUCompileVerified':True,
                'sourceSha256':p.SOURCES[p.B][1],
                'sourceBytes':p.SOURCES[p.B][0],
                'watchedFilesChanged':False,
                'temporaryOutputRemoved':True,
                'installed':False, 'ordersSent':0,
                'dispatchAuthorized':False, 'armAuthorized':False,
                'itemHeaderCheck':{'staticItemClassKitHeaderAllowed':True,
                                   'engineCanEquipVerified':False}}

    def with_fake(self, inner=None, returncode=0):
        raws,hashes=self.fixtures()
        # Verify staging and cancellation using a deterministic fake native runner.
        def runfake(cmd,**kwargs):
            self.assertIn('--native-readonly',cmd)
            self.assertEqual(cmd.count('--native-readonly'),1)
            self.assertEqual(len([s for s in cmd if s=='--game']),1)
            self.assertIs(kwargs['stdin'],p.subprocess.DEVNULL)
            self.assertIs(kwargs['capture_output'],True)
            content=self.success_response() if inner is None else inner
            return SimpleNamespace(returncode=returncode,stdout=json.dumps(content))
        with tempfile.TemporaryDirectory() as d:
            game=Path(d)/'game';game.mkdir()
            with patch.dict(p.SOURCES,hashes,clear=True):
                return p.run(game,'a'*40,fetcher=lambda _commit,x:raws[x],runner=runfake,require_windows=False)

    def test_good_exact_mock_never_authorizes_gameplay(self):
        out=self.with_fake()
        self.assertEqual(out['status'],'R39_EXACT_NATIVE_AND_ITEM_HEADER_PASS_NO_INSTALL')
        for f in ('gameModified','installed','dispatchAuthorized','armAuthorized','engineCanEquipVerified','realGameplayTransferVerified'):
            self.assertIs(out[f],False,f)
        self.assertEqual(out['ordersSent'],0)

    def test_reject_inner_missing_item_header(self):
        inner=self.success_response();del inner['itemHeaderCheck']
        self.assertEqual(self.with_fake(inner)['status'],'HOLD_R39_NATIVE_OR_STATIC_ITEM_USABILITY')

    def test_reject_inner_claims_engine_can_equip(self):
        inner=self.success_response();inner['itemHeaderCheck']['engineCanEquipVerified']=True
        self.assertEqual(self.with_fake(inner)['status'],'HOLD_R39_NATIVE_OR_STATIC_ITEM_USABILITY')

    def test_reject_inner_claims_installed(self):
        inner=self.success_response();inner['installed']=True
        self.assertEqual(self.with_fake(inner)['status'],'HOLD_R39_NATIVE_OR_STATIC_ITEM_USABILITY')

    def test_reject_inner_claims_actions(self):
        for k,v in (('ordersSent',1),('dispatchAuthorized',True),('armAuthorized',True)):
            inner=self.success_response();inner[k]=v
            with self.subTest(k=k):
                self.assertEqual(self.with_fake(inner)['status'],'HOLD_R39_NATIVE_OR_STATIC_ITEM_USABILITY')

    def test_reject_inner_sha_drift(self):
        inner=self.success_response();inner['sourceSha256']='0'*64
        self.assertEqual(self.with_fake(inner)['status'],'HOLD_R39_NATIVE_OR_STATIC_ITEM_USABILITY')

    def test_reject_inner_unsafe_engine_temporary(self):
        for k,v in (('watchedFilesChanged',True),('temporaryOutputRemoved',False)):
            inner=self.success_response();inner[k]=v
            self.assertEqual(self.with_fake(inner)['status'],'HOLD_R39_NATIVE_OR_STATIC_ITEM_USABILITY')

    def test_reject_nonzero_native_process(self):
        inner=self.success_response()
        self.assertEqual(self.with_fake(inner,returncode=3)['status'],'HOLD_R39_NATIVE_OR_STATIC_ITEM_USABILITY')

    def test_source_has_only_immutable_allowlist(self):
        for path,(size,sha) in p.SOURCES.items():
            self.assertTrue(path.startswith('BGXAI/'))
            self.assertGreater(size,1)
            self.assertEqual(len(sha),64)
            self.assertNotIn('..',path)
        self.assertEqual(len(p.SOURCES),4)

if __name__=='__main__':unittest.main()
