"""Regression for BGXAI menu176 HOLD KeyError,KeyError observed in real onefile."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import re
import unittest
from unittest.mock import patch

BASE=Path("BGXAI/BUILD/WEAPON_XEQUIP_ONEFILE_175_RO_20261126")
def load(path):
    spec=importlib.util.spec_from_file_location("bgxai176_hotfix_stage",str(path))
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod
m=load(BASE/"BGXAI_XEQUIP_ONEFILE_175_RO_DUALMODE_STAGE_176.py")
COMMIT="a"*40

class Response:
    def __init__(self,data,expected):
        self.data=data;self.expected=expected
    def __enter__(self):return self
    def __exit__(self,exc_type,exc,tb):return False
    def read(self,requested):
        # Limits must be read from the matching V3 or legacy allowlist.
        assert requested == self.expected+1,(requested,self.expected)
        return self.data[:requested]

class MockHost:
    def __init__(self,fail_first=False,tamper=None):
        self.calls=[]
        self.fail_first=fail_first
        self.tamper=tamper
    def __call__(self,request,timeout=None):
        url=request.full_url
        match=re.search(r"(BGXAI/[-_A-Za-z0-9./]+)$",url)
        if not match:raise AssertionError("Unexpected path: "+url)
        path=match.group(1)
        self.calls.append((path,url))
        if self.fail_first and len(self.calls)==1:
            raise OSError("SIMULATED_PRIMARY_HOST_FAILURE")
        src=(m.SOURCES.get(path) or m.V3_SOURCES.get(path))
        if src is None:raise AssertionError("Unpinned input "+path)
        raw=Path(path).read_bytes()
        if path==self.tamper:raw=raw+b"X"
        return Response(raw,src[0])

class Tests(unittest.TestCase):
    def test_pins_match_git_checkout(self):
        for path,(length,digest) in list(m.SOURCES.items())+list(m.V3_SOURCES.items()):
            raw=Path(path).read_bytes()
            self.assertEqual(len(raw),length,path)
            self.assertEqual(m.digest(raw),digest,path)
    def test_native_v3_wrapper_download_no_keyerror(self):
        for path in (m.V3_WRAPPER,m.V3_EVIDENCE):
            host=MockHost()
            with patch.object(m.urllib.request,"urlopen",side_effect=host):
                raw=m.fetch_pinned(COMMIT,path)
            self.assertEqual(raw,Path(path).read_bytes())
            self.assertEqual(len(host.calls),1)
    def test_backend_shared_in_both_source_allowlists(self):
        self.assertIn(m.BACKEND,m.SOURCES)
        self.assertIn(m.BACKEND,m.V3_SOURCES)
        host=MockHost()
        with patch.object(m.urllib.request,"urlopen",side_effect=host):
            self.assertEqual(m.fetch_pinned(COMMIT,m.BACKEND),Path(m.BACKEND).read_bytes())
    def test_old_175_sources_still_download(self):
        for path in m.SOURCES:
            with self.subTest(path=path):
                host=MockHost()
                with patch.object(m.urllib.request,"urlopen",side_effect=host):
                    raw=m.fetch_pinned(COMMIT,path)
                self.assertEqual(raw,Path(path).read_bytes())
    def test_v3_primary_host_failure_falls_back_to_cdn(self):
        host=MockHost(fail_first=True)
        with patch.object(m.urllib.request,"urlopen",side_effect=host):
            got=m.fetch_pinned(COMMIT,m.V3_WRAPPER)
        self.assertEqual(got,Path(m.V3_WRAPPER).read_bytes())
        self.assertEqual(len(host.calls),2)
        self.assertIn("cdn.jsdelivr.net",host.calls[1][1])
    def test_v3_tamper_fails_closed_both_hosts(self):
        host=MockHost(tamper=m.V3_EVIDENCE)
        with patch.object(m.urllib.request,"urlopen",side_effect=host):
            with self.assertRaises(m.Hold) as err:
                m.fetch_pinned(COMMIT,m.V3_EVIDENCE)
        self.assertIn("HOLD_PINNED_DOWNLOAD_OR_HASH_FAILURE",str(err.exception))
        self.assertEqual(len(host.calls),2)
    def test_v3_rejects_nonallowlisted_url(self):
        host=MockHost()
        with patch.object(m.urllib.request,"urlopen",side_effect=host):
            with self.assertRaises(m.Hold):
                m.fetch_pinned(COMMIT,"BGXAI/override/DPLAYER.BCS")
        self.assertEqual(host.calls,[])
    def test_v3_full_real_python_sourceonly_pipeline(self):
        host=MockHost()
        with patch.object(m.urllib.request,"urlopen",side_effect=host):
            out=m.prepare_v3(Path("/nonexistent/NoUserEET"),COMMIT,False)
        self.assertEqual(out["status"],"V3_EXACT_SOURCE_PIN_PASS_NOT_NATIVE")
        self.assertEqual(set(out["sourcePins"]),set(m.V3_SOURCES))
        self.assertEqual(out["innerReport"]["bafSha256"],m.V3_BAF_SHA256)
        self.assertEqual(out["innerReport"]["bafBytes"],762)
        self.assertFalse(out["gameplayFeatureInstalled"])
        self.assertFalse(out["gameplayLiveVerified"])
        self.assertFalse(out["gameplayMoveAuthorized"])
        self.assertEqual(out["ordersSent"],0)
        self.assertEqual(len(host.calls),len(m.V3_SOURCES))
    def test_legacy_175_full_real_python_sourceonly_pipeline(self):
        host=MockHost()
        with patch.object(m.urllib.request,"urlopen",side_effect=host):
            out=m.prepare(Path("/nonexistent/NoUserEET"),COMMIT,False)
        self.assertEqual(out["status"],"INERT_SOURCE_PIN_VERIFIED_NO_NATIVE")
        self.assertEqual(set(out["sourcePins"]),set(m.SOURCES))
        self.assertFalse(out["gameplayFeatureInstalled"])
        self.assertEqual(len(host.calls),len(m.SOURCES))
    def test_176_hold_reports_correct_schema_and_zero_orders(self):
        with patch.object(m,"prepare_v3",side_effect=m.Hold("TEST_NO_NATIVE")):
            b=io.StringIO()
            with contextlib.redirect_stdout(b):
                exitcode=m.main(["--v3","--commit",COMMIT,"--game","/nonexistent/NoUserEET"])
        result=json.loads(b.getvalue())
        self.assertEqual(exitcode,3)
        self.assertEqual(result["schema"],"BGXAI_XEQUIP_ONEFILE_176_V3_READONLY_V1")
        self.assertEqual(result["status"],"HOLD_XEQUIP176_V3")
        self.assertEqual(result["ordersSent"],0)
        self.assertEqual(result["newGameFilesWrittenByThisRunner"],0)
    def test_175_hold_schema_still_old(self):
        with patch.object(m,"prepare",side_effect=m.Hold("TEST_NO_NATIVE")):
            b=io.StringIO()
            with contextlib.redirect_stdout(b):
                exitcode=m.main(["--commit",COMMIT,"--game","/nonexistent/NoUserEET"])
        result=json.loads(b.getvalue())
        self.assertEqual(exitcode,3)
        self.assertEqual(result["schema"],m.SCHEMA)
        self.assertEqual(result["status"],"HOLD_XEQUIP175")
        self.assertEqual(result["ordersSent"],0)

if __name__=="__main__":unittest.main(verbosity=2)
