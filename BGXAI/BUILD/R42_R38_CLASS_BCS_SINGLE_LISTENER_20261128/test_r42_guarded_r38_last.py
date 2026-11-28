"""R42 guarded 154->155 WeiDU tests; fake EET filesystem only, no game process."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
spec=importlib.util.spec_from_file_location('r42_guarded_module', HERE/'BGXAI_R42_GUARDED_FROM_R38.py')
G=importlib.util.module_from_spec(spec);spec.loader.exec_module(G)
srcspec=importlib.util.spec_from_file_location('r42_builder_module', HERE/'BGXAI_R42_REUSE_R38_CLASS_BCS_RO.py')
B=importlib.util.module_from_spec(srcspec);srcspec.loader.exec_module(B)
CANDIDATE=B.compose(B.verified(B.R38,B.R38_BYTES,B.R38_BLOB),
                    B.verified(B.R39,B.R39_BYTES,B.R39_BLOB))
R37_PATH=REPO/'BGXAI/BUILD/R37_R33_R36_SINGLE_LISTENER_RO_20261126/R37_GUARDED_SOURCE_ONLY.py'
R38_PATH=REPO/'BGXAI/BUILD/R38_GUARDED_FROM_R37_20261127/BGXAI_R38_GUARDED_FROM_R37.py'
R38_ROWS=["~DUMMY.TP2~ #0 #0"]*153+["~BGXR38/setup-BGXR38.tp2~ #0 #0"]
R42_ROW="~BGXR42/setup-BGXR42.tp2~ #0 #0"

def sha(blob):
    return hashlib.sha256(blob).hexdigest()

class FakeOld:
    def __init__(self,game):
        self.BASELINE_SHA={'chitin.key':sha(b'fixture'),'override/BDDEFAI.BCS':sha(b'known')}
        self.SOURCE_SHA=G.R38_SHA
        self.NATIVE_SHA=G.WEIDU_SHA
    def safe(self,root,rel):
        p=Path(root)
        for part in rel.split('/'):
            if part in ('','.','..'):raise ValueError('bad path')
            p=p/part
            if p.is_symlink():raise ValueError('symlink path')
        return p
    def protected_root(self,root,live=True):
        if not Path(root).is_dir():raise G.Hold('HOLD_ROOT')
    def history(self,root):
        raw=self.safe(root,'WeiDU.log').read_bytes()
        rows=raw.decode('utf-8').splitlines()
        return rows,sha(raw)
    def last_r37_history(self,rows):
        return len(rows)==153
    def sha(self,file):
        return sha(Path(file).read_bytes())
    def verify_snapshot(self,root,expected):
        for p,v in expected.items():
            if self.sha(self.safe(root,p))!=v:
                raise G.Hold('HOLD_FILE_DRIFT:'+p)

class FakeR38:
    SOURCE_SHA=G.R38_SHA
    WEIDU_SHA=G.WEIDU_SHA
    PROOF='BGXR38/PROOF.json'
    LAST=re.compile(r'^~BGXR38/setup-BGXR38[.]tp2~ #0 #0$',re.I)
    @staticmethod
    def check_processes(old):
        return None
    def last_r38(self,old,root):
        rows,log=old.history(root)
        if len(rows)!=154 or not self.LAST.match(rows[-1]):
            raise G.Hold('HOLD_NOT_R38_LAST')
        if old.sha(old.safe(root,G.OVERRIDE))!=G.R38_SHA:
            raise G.Hold('HOLD_NOT_R38_ACTIVE')
        return rows,log
    def installed_proof(self,old,root):
        return json.loads(old.safe(root,self.PROOF).read_text(encoding='utf-8'))
    def snapshot(self,old,root):
        return {p:old.sha(old.safe(root,p)) for p in (
            'WeiDU.log',G.OVERRIDE,'chitin.key','override/BDDEFAI.BCS',
            'BGXR37/PROOF.json')}

class T(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base=Path(self.tmp.name)
        self.game=base/'game'
        self.game.mkdir()
        self.home=base/'home'
        self.home.mkdir()
        self.old=FakeOld(self.game)
        self.r38=FakeR38()
        self._file('WeiDU.log',('\n'.join(R38_ROWS)+'\n').encode())
        self._file(G.OVERRIDE,(REPO/B.R38).read_bytes())
        self._file('chitin.key',b'fixture')
        self._file('override/BDDEFAI.BCS',b'known')
        self._file('BGXR37/PROOF.json',b'{"installed":true}')
        self._file('BGXR38/PROOF.json',b'{"installed":true,"source":"R38"}')
        self._file('setup-enhanced-powergaming-scripts.exe',b'fake-native')
        self.candidate=base/'candidate.lua'
        self.candidate.write_bytes(CANDIDATE)
        self._contexts=[
            patch.object(G,'WEIDU_SHA',sha(b'fake-native')),
            patch.object(G,'check_processes',return_value=None),
            patch.dict(os.environ,{'USERPROFILE':str(self.home)}),
        ]
        for c in self._contexts:
            c.start();self.addCleanup(c.stop)

    def _file(self,path,contents):
        dst=self.game/path
        dst.parent.mkdir(parents=True,exist_ok=True)
        dst.write_bytes(contents)
    def fake_weidu(self,old,root,uninstall=False):
        if uninstall:
            self._file(G.OVERRIDE,(REPO/B.R38).read_bytes())
            self._file('WeiDU.log',('\n'.join(R38_ROWS)+'\n').encode())
        else:
            self._file(G.OVERRIDE,self.candidate.read_bytes())
            self._file('WeiDU.log',('\n'.join(R38_ROWS+[R42_ROW])+'\n').encode())

    def test_01_existing_r38_r37_helper_pins(self):
        self.assertEqual(len(R38_PATH.read_bytes()),G.R38_TOOL_LEN)
        self.assertEqual(sha(R38_PATH.read_bytes()),G.R38_TOOL_SHA)
        self.assertEqual(len(R37_PATH.read_bytes()),G.R37_TOOL_LEN)
        self.assertEqual(sha(R37_PATH.read_bytes()),G.R37_TOOL_SHA)
        # setUp pins the fake native bytes for sandbox install tests; restore
        # the genuine production SHA for independent helper-contract validation.
        with patch.object(G,'WEIDU_SHA','0d17e26e3f3ef5b36796eb0ee8ae73cb851d8b62c9702c2e224da2945caafb75'):
            r38,old=G.load(R38_PATH,R37_PATH)
            self.assertEqual(r38.SOURCE_SHA,G.R38_SHA)
            self.assertEqual(old.NATIVE_SHA,G.WEIDU_SHA)

    def test_02_real_composer_bytes_and_sha(self):
        self.assertEqual(len(CANDIDATE),G.CANDIDATE_BYTES)
        self.assertEqual(sha(CANDIDATE),G.CANDIDATE_SHA)
        self.assertEqual(G.candidate_bytes(self.candidate),CANDIDATE)

    def test_03_default_read_only_status_r38(self):
        v=G.status(self.r38,self.old,self.game)
        self.assertEqual(v['status'],'R42_NOT_INSTALLED_R38_LAST')
        self.assertFalse(v['gameModified'])

    def test_04_preflight_154_exact_no_install(self):
        v=G.preflight(self.r38,self.old,self.game,self.candidate)
        self.assertEqual(v['status'],'R42_PREFLIGHT_PASS_NO_INSTALL')
        self.assertEqual(v['weiduComponents'],154)
        self.assertEqual(v['baselineSnapshot'][G.OVERRIDE],G.R38_SHA)
        self.assertIn(self.r38.PROOF,v['baselineSnapshot'])
        self.assertFalse((self.game/G.DIR).exists())

    def test_05_install_token_required_before_write(self):
        with self.assertRaisesRegex(G.Hold,'HOLD_EXACT_R42_INSTALL_TOKEN_REQUIRED'):
            G.install(self.r38,self.old,self.game,self.candidate,'')
        self.assertFalse((self.game/G.DIR).exists())

    def test_06_rollback_token_required_before_write(self):
        with self.assertRaisesRegex(G.Hold,'HOLD_EXACT_R42_ROLLBACK_TOKEN_REQUIRED'):
            G.rollback(self.r38,self.old,self.game,'')
        self.assertFalse((self.game/G.DIR).exists())

    def test_07_modified_r42_candidate_rejected(self):
        bad=bytearray(CANDIDATE);bad[44]^=1
        self.candidate.write_bytes(bad)
        with self.assertRaisesRegex(G.Hold,'HOLD_R42_CANDIDATE_SHA_OR_LISTENER'):
            G.preflight(self.r38,self.old,self.game,self.candidate)

    def test_08_candidate_missing_rejected(self):
        self.candidate.unlink()
        with self.assertRaisesRegex(G.Hold,'HOLD_R42_CANDIDATE_SIZE_OR_PATH'):
            G.preflight(self.r38,self.old,self.game,self.candidate)

    def test_09_r38_weidu_not_last_holds(self):
        self._file('WeiDU.log',('\n'.join(R38_ROWS+[R42_ROW])+'\n').encode())
        with self.assertRaises(G.Hold):
            G.preflight(self.r38,self.old,self.game,self.candidate)

    def test_10_live_r38_sha_drift_holds(self):
        self._file(G.OVERRIDE,b'stale')
        with self.assertRaises(G.Hold):
            G.preflight(self.r38,self.old,self.game,self.candidate)

    def test_11_existing_r42_stage_holds(self):
        (self.game/G.DIR).mkdir()
        with self.assertRaisesRegex(G.Hold,'HOLD_R42_EXISTING_STAGING'):
            G.preflight(self.r38,self.old,self.game,self.candidate)

    def test_12_modified_unrelated_bcs_holds(self):
        self._file('override/BDDEFAI.BCS',b'wrong')
        with self.assertRaisesRegex(G.Hold,'HOLD_R38_BASELINE_CHANGED'):
            G.preflight(self.r38,self.old,self.game,self.candidate)

    def test_13_staged_native_weidu_binary_holds(self):
        self._file('setup-enhanced-powergaming-scripts.exe',b'drift')
        with self.assertRaisesRegex(G.Hold,'HOLD_R42_NATIVE_WEIDU_CHANGED'):
            G.preflight(self.r38,self.old,self.game,self.candidate)

    def test_14_backup_copies_all_sha_verified(self):
        v=G.preflight(self.r38,self.old,self.game,self.candidate)
        dst=G.external_backup(self.old,self.game,v['baselineSnapshot'])
        self.assertTrue(dst.name.startswith('PRE_BGXR42_'))
        self.assertEqual(json.loads((dst/'SHA256.json').read_text()),v['baselineSnapshot'])
        self.old.verify_snapshot(dst,v['baselineSnapshot'])

    def test_15_install_155_last_and_exact_rollback_154(self):
        with patch.object(G,'native_weidu',side_effect=self.fake_weidu):
            output=G.install(self.r38,self.old,self.game,self.candidate,G.INSTALL_TOKEN)
            self.assertEqual(output['status'],'R42_READONLY_INSTALLED_AWAITING_LIVE_CLASS')
            self.assertTrue(output['installationPerformed'])
            self.assertEqual(G.status(self.r38,self.old,self.game)['status'],'R42_PRESENT_LAST_READONLY')
            self.assertEqual(self.old.sha(self.game/G.OVERRIDE),G.CANDIDATE_SHA)
            self.assertEqual(self.old.history(self.game)[0][-1],R42_ROW)
            self.assertEqual(self.old.sha(self.game/'override/BDDEFAI.BCS'),self.old.BASELINE_SHA['override/BDDEFAI.BCS'])
            r=G.rollback(self.r38,self.old,self.game,G.ROLLBACK_TOKEN)
            self.assertEqual(r['status'],'R42_ROLLBACK_RESTORED_R38_LAST')
            self.assertEqual(G.status(self.r38,self.old,self.game)['status'],'R42_NOT_INSTALLED_R38_LAST')
            self.assertEqual(self.old.sha(self.game/G.OVERRIDE),G.R38_SHA)

    def _install(self):
        with patch.object(G,'native_weidu',side_effect=self.fake_weidu):
            return G.install(self.r38,self.old,self.game,self.candidate,G.INSTALL_TOKEN)

    def test_16_rollback_refuses_weiDU_component_added_after_r42(self):
        self._install()
        self._file('WeiDU.log',('\n'.join(R38_ROWS+[R42_ROW,'~AFTER.tp2~ #0 #0'])+'\n').encode())
        with self.assertRaisesRegex(G.Hold,'HOLD_R42_NOT_WEIDU_LAST_155'):
            G.rollback(self.r38,self.old,self.game,G.ROLLBACK_TOKEN)

    def test_17_rollback_refuses_unrelated_bcs_change(self):
        self._install()
        self._file('override/BDDEFAI.BCS',b'changed!')
        with self.assertRaisesRegex(G.Hold,'HOLD_R42_UNRELATED_RESOURCE_DRIFT'):
            G.rollback(self.r38,self.old,self.game,G.ROLLBACK_TOKEN)

    def test_18_rollback_refuses_backup_manifest_drift(self):
        output=self._install()
        folder=Path(output['externalBackup'])
        f=folder/'SHA256.json'
        obj=json.loads(f.read_text());obj[G.OVERRIDE]='z'*64
        f.write_text(json.dumps(obj))
        with self.assertRaisesRegex(G.Hold,'HOLD_R42_BACKUP_MANIFEST_MISMATCH'):
            G.rollback(self.r38,self.old,self.game,G.ROLLBACK_TOKEN)

    def test_19_rollback_refuses_invalid_backup_location(self):
        self._install()
        f=self.game/G.PROOF;obj=json.loads(f.read_text())
        obj['externalBackup']=str(self.game)
        f.write_text(json.dumps(obj))
        with self.assertRaisesRegex(G.Hold,'HOLD_R42_EXTERNAL_BACKUP_PROVENANCE'):
            G.rollback(self.r38,self.old,self.game,G.ROLLBACK_TOKEN)

    def test_20_rollback_refuses_modified_active_r42(self):
        self._install()
        self._file(G.OVERRIDE,b'drift')
        with self.assertRaisesRegex(G.Hold,'HOLD_R42_ACTIVE_LUA_SHA_DRIFT'):
            G.rollback(self.r38,self.old,self.game,G.ROLLBACK_TOKEN)

    def test_21_failed_weidu_leaves_pending_for_manual_review_no_auto_retry(self):
        def fail(*args,**kwargs):raise G.Hold('HOLD_WEIDU_FAILURE')
        with patch.object(G,'native_weidu',side_effect=fail):
            with self.assertRaisesRegex(G.Hold,'HOLD_WEIDU_FAILURE'):
                G.install(self.r38,self.old,self.game,self.candidate,G.INSTALL_TOKEN)
        self.assertTrue((self.game/G.PROOF).exists())
        self.assertEqual(json.loads((self.game/G.PROOF).read_text())['status'],'R42_PENDING_WEIDU')
        self.assertEqual(self.old.history(self.game)[0][-1],R38_ROWS[-1])

    def test_22_no_second_listener_or_equipment_command(self):
        self.assertEqual(CANDIDATE.count(G.ONE_LISTENER),1)
        self.assertEqual(CANDIDATE.count(b'[BGXBCS]'),1)
        for raw in (b'XEquipItem(',b'SetGlobal(',b'ClearActions(',b'ActionOverride('):
            # Real R38+R39 source may contain only text/comments; no new
            # issuance by the R42 caller, verified in original composer.
            self.assertNotIn(raw,G.TP2_TEXT.encode())

    def test_23_no_automatic_install_from_main_default(self):
        self.assertIn("default='status'",(HERE/'BGXAI_R42_GUARDED_FROM_R38.py').read_text())
        self.assertIn("input('Type '+INSTALL_TOKEN", (HERE/'BGXAI_R42_GUARDED_FROM_R38.py').read_text())

    def test_24_weidu_rollback_command_is_only_force_uninstall(self):
        self.assertIn("'--force-uninstall' if uninstall else '--force-install'", (HERE/'BGXAI_R42_GUARDED_FROM_R38.py').read_text())

if __name__=='__main__':unittest.main()
