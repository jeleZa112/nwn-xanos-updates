"""BGXAI R38 28 source/adversarial tests: never touch user's game."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[2] if Path(__file__).resolve().parents[2].name=='BGXAI' else Path.cwd()
# In GitHub this test lives next to the guarded tool; local allows direct file execution.
FOLDER=Path(__file__).resolve().parent
STAGE=FOLDER/'BGXAI_R38_GUARDED_FROM_R37.py'
if not STAGE.is_file():
    STAGE=ROOT/'BGXAI/BUILD/R38_GUARDED_FROM_R37_20261127/BGXAI_R38_GUARDED_FROM_R37.py'
spec=importlib.util.spec_from_file_location('r38_guard',str(STAGE))
G=importlib.util.module_from_spec(spec);spec.loader.exec_module(G)
LIVE=Path('C:/Games/BG_EET_FOXX_NEW')
SRC=Path('BGXAI/BUILD/R37_XEQUIP_IDENTITY_SINGLE_LISTENER_SOURCEONLY_20261127/M_BGXR27_R37_INV3_IDENTITY_SOURCE_ONLY.lua')
OLD=Path('BGXAI/BUILD/R37_R33_R36_SINGLE_LISTENER_RO_20261126/R37_GUARDED_SOURCE_ONLY.py')

class FakeOld:
    SOURCE_SHA=G.OLD_SHA
    NATIVE_SHA=G.WEIDU_SHA
    BASELINE_SHA={}
    WATCHED=('WeiDU.log',G.OVERRIDE)
    def protected_root(self,root,live):self.calls.append('root')
    def __init__(self):self.calls=[];self.components=153;self.active=G.OLD_SHA
    def history(self,root):self.calls.append('history');return (['r%d'%i for i in range(self.components)],'a'*64)
    def last_r37_history(self,rows):return len(rows)==153
    def safe(self,root,rel):return root/rel
    def sha(self,p):return G.WEIDU_SHA if p.name=='setup-enhanced-powergaming-scripts.exe' else self.active
    def installed_proof(self,root):self.calls.append('proof');return {'status':'R37_PASSIVE_INSTALLED_AWAITING_RUNTIME'}
    def verify_snapshot(self,root,expected):self.calls.append('verify')
    def verify_processes(self):self.calls.append('process')

class Unit(unittest.TestCase):
    def test_01_tool_schema_is_r38(self):self.assertIn('R38',G.SCHEMA)
    def test_02_source_sha_is_real_sha(self):self.assertEqual(len(G.SOURCE_SHA),64)
    def test_03_source_size_pin(self):self.assertEqual(G.SOURCE_BYTES,78927)
    def test_04_r37_sha_separate(self):self.assertNotEqual(G.SOURCE_SHA,G.OLD_SHA)
    def test_05_token_not_empty(self):self.assertTrue(G.INSTALL_TOKEN.startswith('INSTALL_BGXAI_R38_'))
    def test_06_rollback_token_not_install(self):self.assertTrue(G.ROLLBACK_TOKEN.startswith('ROLLBACK_BGXAI_R38_'))
    def test_07_install_without_approval_no_write(self):
        x=FakeOld()
        with self.assertRaises(G.Hold):G.install(x,LIVE,SRC,'WRONG')
        self.assertEqual(x.calls,[])
    def test_08_rollback_without_approval_no_write(self):
        x=FakeOld()
        with self.assertRaises(G.Hold):G.rollback(x,LIVE,'WRONG')
        self.assertEqual(x.calls,[])
    def test_09_invalid_candidate_never_passes(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'candidate.lua';p.write_bytes(b'fake')
            with self.assertRaises(G.Hold):G.candidate_bytes(p)
    def test_10_source_only_does_not_send_orders(self):
        s=STAGE.read_text()
        self.assertNotIn('XEquipItem(',s)
        self.assertNotIn('SetGlobal(',s)
        self.assertNotIn('ClearActions(',s)
    def test_11_tp2_exact_one_override_copy(self):
        s=G.TP2_TEXT
        self.assertEqual(s.count('COPY ~'),1)
        self.assertIn('override/M_BGXR27.lua',s)
        self.assertIn('BACKUP ~BGXR38/backup~',s)
    def test_12_status_preinstall_r37_untouched(self):
        with tempfile.TemporaryDirectory() as d:
            old=FakeOld();obj=G.status(old,Path(d))
        self.assertEqual(obj['status'],'R38_NOT_INSTALLED_R37_PRESENT_LAST')
        self.assertFalse(obj['installed']);self.assertFalse(obj['armAuthorized'])
    def test_13_status_unknown_weidu_hold(self):
        with tempfile.TemporaryDirectory() as d:
            old=FakeOld();old.components=155;obj=G.status(old,Path(d))
        self.assertEqual(obj['status'],'R38_HOLD_UNKNOWN_WEIDU_OR_LUA')
    def test_14_status_old_r37_sha_changed_hold(self):
        with tempfile.TemporaryDirectory() as d:
            old=FakeOld();old.active='e'*64;obj=G.status(old,Path(d))
        self.assertEqual(obj['status'],'R38_HOLD_UNKNOWN_WEIDU_OR_LUA')
    def test_15_preflight_rejects_wrong_last_weidu(self):
        with tempfile.TemporaryDirectory() as d:
            old=FakeOld();old.components=154
            with mock.patch.object(G,'check_processes'):
                with self.assertRaisesRegex(G.Hold,'HOLD_R37_MUST_BE_LAST_153'):
                    G.preflight(old,Path(d),SRC)
    def test_16_preflight_rejects_changed_live_lua(self):
        with tempfile.TemporaryDirectory() as d:
            old=FakeOld();old.active='a'*64
            with mock.patch.object(G,'check_processes'):
                with self.assertRaisesRegex(G.Hold,'HOLD_R37_LIVE_MODULE_SHA_DRIFT'):
                    G.preflight(old,Path(d),SRC)
    def test_17_preflight_rejects_staging_collision(self):
        with tempfile.TemporaryDirectory() as d:
            old=FakeOld();(Path(d)/'BGXR38').mkdir()
            with mock.patch.object(G,'check_processes'):
                with self.assertRaisesRegex(G.Hold,'HOLD_R38_STAGING_COLLISION'):
                    G.preflight(old,Path(d),SRC)
    def test_18_preflight_rejects_bad_compiler(self):
        with tempfile.TemporaryDirectory() as d:
            class NoWeiDU(FakeOld):
                def sha(self,p):return '0'*64 if p.name=='setup-enhanced-powergaming-scripts.exe' else super().sha(p)
            old=NoWeiDU();(Path(d)/'setup-enhanced-powergaming-scripts.exe').write_bytes(b'FAKE')
            with mock.patch.object(G,'check_processes'):
                with self.assertRaisesRegex(G.Hold,'HOLD_NATIVE_WEIDU_BINARY_CHANGED'):
                    G.preflight(old,Path(d),SRC)
    def test_19_last_r38_not_weidu154(self):
        with tempfile.TemporaryDirectory() as d:
            old=FakeOld();old.components=153
            with self.assertRaisesRegex(G.Hold,'HOLD_R38_NOT_WEIDU_LAST_154'):
                G.last_r38(old,Path(d))
    def test_20_installed_proof_missing(self):
        with tempfile.TemporaryDirectory() as d:
            old=FakeOld()
            with self.assertRaisesRegex(G.Hold,'HOLD_R38_PROOF_MISSING'):
                G.installed_proof(old,Path(d))
    def test_21_weidu_unavailable_safe_hold(self):
        with tempfile.TemporaryDirectory() as d:
            old=FakeOld()
            with self.assertRaises(G.Hold):G.run_weidu(old,Path(d))
    def test_22_r38_parser_four_advisory_lines(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'mock.log'
            types=('R27_SINGLE_CALLBACK','ADVISORY_CONTEXT','BACKPACK16_ADVISORY','IDENTITY_ADVISORY')
            lines=[]
            for i in range(3):
                lines.append(G.STATUS_PREFIXES[i].decode()+json.dumps(dict(schema=G.EXPECTED_SCHEMA[i],type='SESSION')))
            for i in range(4):
                obj=dict(schema=G.EXPECTED_SCHEMA[i],type=types[i],seq=1,partyIndex=1,
                    readOnly=True,dispatchAuthorized=False,ordersSent=0,
                    status='RUNTIME_JAGAN_INVENTORY_MATCH_READONLY_NO_ARM' if i==3 else 'SAMPLE')
                if i==1:obj.update(weaponSwitchAuthorized=False,safeActionBoundaryVerified=False)
                if i==2:obj.update(inventoryMoveAuthorized=False,safeActionBoundaryVerified=False)
                if i==3:obj.update(armAuthorized=False,safeActionBoundaryVerified=False,localsWritten=0)
                lines.append(G.STATUS_PREFIXES[i].decode()+json.dumps(obj))
            p.write_text('\n'.join(lines)+'\n')
            obj=G.parse_console(p,0)
            self.assertEqual(obj['status'],'R38_RUNTIME_IDENTITY_OBSERVATIONS_READY_FOR_REVIEW')
            self.assertTrue(obj['alignedFourEvents']);self.assertTrue(obj['jaganExactItemMatchObserved'])
            self.assertFalse(obj['runtimeActorIdentityVerified']);self.assertEqual(obj['ordersSent'],0)
    def test_23_r38_parser_rejects_arming(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'mock.log'
            s=dict(schema=G.EXPECTED_SCHEMA[3],type='IDENTITY_ADVISORY',seq=1,partyIndex=1,
                 readOnly=True,dispatchAuthorized=False,ordersSent=0,
                 status='RUNTIME_JAGAN_INVENTORY_MATCH_READONLY_NO_ARM',armAuthorized=True,
                 safeActionBoundaryVerified=False,localsWritten=0)
            p.write_text(G.STATUS_PREFIXES[3].decode()+json.dumps(s)+'\n')
            self.assertGreater(G.parse_console(p,0)['malformedRows'],0)
    def test_24_r38_parser_rejects_duplicate_seq(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'mock.log';s=dict(schema=G.EXPECTED_SCHEMA[3],type='IDENTITY_ADVISORY',
                 seq=1,partyIndex=1,readOnly=True,dispatchAuthorized=False,ordersSent=0,
                 armAuthorized=False,safeActionBoundaryVerified=False,localsWritten=0,status='HOLD')
            line=G.STATUS_PREFIXES[3].decode()+json.dumps(s)
            p.write_text(line+'\n'+line+'\n')
            self.assertEqual(G.parse_console(p,0)['malformedRows'],1)
    def test_25_r38_parser_rejects_nonzero_exit(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'mock.log';p.write_bytes(b'')
            self.assertEqual(G.parse_console(p,1)['status'],'R38_RUNTIME_HOLD_MANUAL_REVIEW')
    def test_26_r38_parser_rejects_malformed(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'mock.log';p.write_bytes(b'[BGXID] not-json\n')
            self.assertGreater(G.parse_console(p,0)['malformedRows'],0)
    def test_27_parser_ignores_untagged_text(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'mock.log';p.write_bytes(b'unrelated game log line\n')
            self.assertEqual(G.parse_console(p,0)['malformedRows'],0)
    def test_28_failed_menu_not_auto_install(self):
        s=STAGE.read_text()
        self.assertNotIn('install(old,a.game,a.candidate,INSTALL_TOKEN)',s)
        self.assertIn('token=input(',s)
    def test_29_rollback_checks_external_provenance(self):
        s=STAGE.read_text()
        self.assertIn('PRE_BGXR38_',s)
        self.assertIn('HOLD_R38_EXTERNAL_BACKUP_PROVENANCE',s)
    def test_30_reports_advice_not_safe_boundaries(self):
        s=STAGE.read_text()
        self.assertIn('safeActionBoundaryVerified=False',s)
        self.assertIn('manualEpsOriginVerified=False',s)

if __name__=='__main__':unittest.main(verbosity=2)