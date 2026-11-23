import hashlib
import io
import multiprocessing
import os
from pathlib import Path
import shutil
import tempfile
import unittest
import zipfile

from bgvoice_safeguards_r2 import SafetyHold
from bgvoice_report_bridge_r3 import (
    merge_report_transaction, movie_merge_main_report, v70_replace_atomic,
    verify_compatible_core_contract)


def _writer(report, prefix, q):
    try:
        for idx in range(8):
            merge_report_transaction(report, {f'{prefix}/{idx}.json': b'{"ok":true}'})
        q.put('PASS')
    except Exception as exc:
        q.put(type(exc).__name__ + ':' + str(exc))


class BridgeTests(unittest.TestCase):
    def test_exact_movie_remove_and_idempotence(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'SEND_TO_CHATGPT_BG_VOICE_RU.zip'
            with zipfile.ZipFile(p,'w') as z:
                z.writestr('SEED.txt', b'immutable')
                z.writestr('VIDEO/RU10_HUMAN_DECISIONS/UNREVIEWED_3.csv',b'old')
            x = movie_merge_main_report({'VIDEO/RU10_HUMAN_DECISIONS/STATUS.json':b'new'},root=d,remove_names=('VIDEO/RU10_HUMAN_DECISIONS/UNREVIEWED_3.csv',))
            self.assertEqual(x,'MAIN_REPORT_UPDATED_ATOMIC_R3')
            h = hashlib.sha256(p.read_bytes()).hexdigest()
            y = movie_merge_main_report({'VIDEO/RU10_HUMAN_DECISIONS/STATUS.json':b'new'},root=d,remove_names=('VIDEO/RU10_HUMAN_DECISIONS/UNREVIEWED_3.csv',))
            self.assertEqual(y,'MAIN_REPORT_UNCHANGED_R3')
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),h)
            with zipfile.ZipFile(p) as z:
                self.assertEqual(z.read('SEED.txt'),b'immutable')
                self.assertNotIn('VIDEO/RU10_HUMAN_DECISIONS/UNREVIEWED_3.csv',z.namelist())

    def test_v70_prefix_replaces_legacy_rows_only(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'SEND_TO_CHATGPT_BG_VOICE_RU.zip'
            with zipfile.ZipFile(p,'w') as z:
                z.writestr('V70/PRODUCTION/obsolete.json',b'old')
                z.writestr('VIDEO/PILOT/LOCKED_APPROVED.wav',b'voice-kept')
            self.assertEqual(v70_replace_atomic(p, {'V70/PRODUCTION/STATUS.json':b'new'},result_prefix='V70/PRODUCTION/'), 'MERGED')
            with zipfile.ZipFile(p) as z:
                self.assertNotIn('V70/PRODUCTION/obsolete.json',z.namelist())
                self.assertEqual(z.read('VIDEO/PILOT/LOCKED_APPROVED.wav'),b'voice-kept')
            before = p.read_bytes()
            self.assertEqual(v70_replace_atomic(p, {'V70/PRODUCTION/STATUS.json':b'new'},result_prefix='V70/PRODUCTION/'), 'UNCHANGED')
            self.assertEqual(p.read_bytes(),before)

    def test_invalid_input_preserves_original(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'SEND_TO_CHATGPT_BG_VOICE_RU.zip'
            with zipfile.ZipFile(p,'w') as z:z.writestr('SEED.txt',b'x')
            raw = p.read_bytes()
            for bad in ({'../escape':b'danger'},{'evil:stream':b'danger'},{'okay':'not bytes'}):
                with self.assertRaises(SafetyHold):merge_report_transaction(p,bad)
            with self.assertRaises(SafetyHold):merge_report_transaction(p,{},remove_prefixes=('../../',))
            self.assertEqual(p.read_bytes(),raw)

    def test_contract_rejects_unverified_movie(self):
        self.assertEqual(verify_compatible_core_contract('1.11.0','1.2.0',literary_gate_present=True)['live_integration'],False)
        for args in [('1.10.0','1.2.0',True),('1.11.0','1.3.0',True),('1.11.0','1.2.0',False)]:
            with self.assertRaises(SafetyHold):verify_compatible_core_contract(args[0],args[1],literary_gate_present=args[2])

    def test_cooperating_processes_serialized(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'SEND_TO_CHATGPT_BG_VOICE_RU.zip'
            with zipfile.ZipFile(p,'w') as z:z.writestr('seed',b'1')
            q=multiprocessing.Queue()
            processes=[multiprocessing.Process(target=_writer,args=(p,c,q)) for c in ('Movie','V70')]
            for proc in processes:proc.start()
            for proc in processes:proc.join(30);self.assertEqual(proc.exitcode,0)
            self.assertEqual(sorted([q.get(timeout=3) for _ in processes]),['PASS','PASS'])
            with zipfile.ZipFile(p) as z:self.assertEqual(len(z.namelist()),17)

    def test_real_windows_archive_on_copy(self):
        source=Path('/mnt/data/bgvoice_r2_work/input/SOURCE_WINDOWS_VIDEO_REPORT_20261123.zip')
        if not source.is_file():self.skipTest('historical archive not present')
        with tempfile.TemporaryDirectory() as d:
            copy=Path(d)/'SEND_TO_CHATGPT_BG_VOICE_RU.zip'
            shutil.copy2(source,copy)
            sha=hashlib.sha256(source.read_bytes()).hexdigest()
            self.assertEqual(sha,'9ea9089666061a3b29a9d8fb9a1bb0822958438af28e45acc2faee12fb447b19')
            # Add a namespaced read-only status; content of every existing ZIP member unchanged.
            update=merge_report_transaction(copy,{'VIDEO/SAFETY_R3/READONLY_TEST_STATUS.json':b'{"test":true,"tts_allowed":false}'})
            self.assertEqual(update['status'],'MERGED')
            with zipfile.ZipFile(source,'r') as before, zipfile.ZipFile(copy,'r') as after:
                for name in before.namelist():self.assertEqual(before.read(name),after.read(name),name)
                self.assertEqual(len(after.namelist()),82)
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),sha)

if __name__=='__main__':unittest.main(verbosity=2)
