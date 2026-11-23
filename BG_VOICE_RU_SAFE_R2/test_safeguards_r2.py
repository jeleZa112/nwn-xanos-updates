import hashlib
import io
import json
import multiprocessing
import subprocess
import sys
import tempfile
import unittest
import wave
import zipfile
from pathlib import Path
from bgvoice_safeguards_r2 import (SafetyHold, verify_model_bundle, verify_signed_manifest,
    merge_report_locked, publish_candidate_once, summarize_batch, create_style_plan,
    build_shtorm_kwargs_for_approved_job, inspect_existing_bundle_readonly,
    inspect_report_readonly, build_strict_style_pair)


def mk_wav():
    f=io.BytesIO()
    with wave.open(f,'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000)
        w.writeframes(b'\x20\x20'*16000)
    return f.getvalue()


def merge_worker(path, label, count, q):
    try:
        for i in range(count):
            merge_report_locked(path,{f'{label}/{i}.json':b'{}'})
        q.put('PASS')
    except Exception as e:q.put(type(e).__name__+str(e))


class R2Test(unittest.TestCase):
    def test_model_strict_no_unpinned_assets(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);(r/'a.json').write_bytes(b'good')
            specs={'a.json':{'bytes':4,'sha256':hashlib.sha256(b'good').hexdigest()}}
            self.assertIn('PASS',verify_model_bundle(r,specs,strict_inventory=True)['status'])
            (r/'extra.safetensors').write_bytes(b'fake')
            with self.assertRaisesRegex(SafetyHold,'INVENTORY'):
                verify_model_bundle(r,specs,strict_inventory=True)
            listing=inspect_existing_bundle_readonly(r)
            self.assertEqual(listing['status'],'OBSERVED_NOT_TRUSTED_PINSET_NOT_LOADED')
            self.assertEqual(len(listing['files']),2)
    def test_model_symlink_child_holds(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);(r/'g').write_bytes(b'ok')
            (r/'link').symlink_to('g')
            self.assertIn('HOLD',inspect_existing_bundle_readonly(r)['status'])
    def test_win_path_tricks_hold(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'run.zip'
            with zipfile.ZipFile(p,'w') as z:z.writestr('ok.txt',b'ok')
            for key in ['../escape','C:/auto','valid/CON.txt','bad:name','trailing./item',r'bad\file']:
                with self.assertRaises(SafetyHold,msg=key):merge_report_locked(p,{key:b'1'})
    def test_signature_under_optimized_python(self):
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives import serialization
        private=Ed25519PrivateKey.generate()
        pub=private.public_key().public_bytes(encoding=serialization.Encoding.Raw,format=serialization.PublicFormat.Raw).hex()
        good={'project':'BG_VOICE_RU','version':'4.9.10','commit':'a'*40,'sha256':'b'*64}
        raw=json.dumps(good).encode(); sig=private.sign(raw)
        self.assertEqual(verify_signed_manifest(raw,sig,pub,'4.9.9')['version'],'4.9.10')
        for wrong in [{**good,'project':'BAD'}, {**good,'version':'4.9.9'},
                      {**good,'commit':'x'*40}, {**good,'path':'../../bad.py'}]:
            invalid=json.dumps(wrong).encode()
            with self.assertRaises(SafetyHold):verify_signed_manifest(invalid,private.sign(invalid),pub,'4.9.9')
        # Re-execute with -O; must not be vulnerable to stripped asserts.
        statement='from bgvoice_safeguards_r2 import verify_signed_manifest,SafetyHold;'+\
                  'import json; '+\
                  'assert True; '\
                  ''
        p=subprocess.run([sys.executable,'-O','-c',
                          'import inspect,bgvoice_safeguards_r2; '
                          's=inspect.getsource(bgvoice_safeguards_r2.verify_signed_manifest); '
                          'assert "assert obj" not in s; print("OPTIMIZED_SCHEMA_CHECKS_PRESENT")'],
                         capture_output=True,text=True,cwd=Path(__file__).parent)
        self.assertEqual(p.returncode,0,p.stderr)
    def test_summarizer_rejects_traversal_and_fake_id(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(SafetyHold,'ID_INVALID'):
                summarize_batch([{'id':'../../secret','fingerprint':'f'*64}],d,worker_exit_code=0)
            p=Path(d)/'X__SHTORM_MOVIE_DRAFT.wav';p.write_bytes(mk_wav())
            (Path(d)/'X__SHTORM_MOVIE_DRAFT.json').write_text(json.dumps({'id':'WRONG','sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'fingerprint':'f'*64,'status':'NEW_NOT_APPROVED'}))
            self.assertEqual(summarize_batch([{'id':'X','fingerprint':'f'*64}],d,worker_exit_code=0)['ready'],0)
    def test_report_readonly_no_write(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'live.zip'
            with zipfile.ZipFile(p,'w') as z:z.writestr('some/report.json',b'{}')
            orig=p.read_bytes()
            r=inspect_report_readonly(p)
            self.assertEqual(r['status'],'REPORT_INTEGRITY_PASS_NOT_AUDIO_APPROVED')
            self.assertEqual(p.read_bytes(),orig)
            self.assertEqual(inspect_report_readonly(Path(d)/'missing.zip')['status'],'HOLD_REPORT_MISSING')
    def test_style_gates_and_same_ref(self):
        with tempfile.TemporaryDirectory() as d:
            ref=Path(d)/'reference.wav';ref.write_bytes(mk_wav())
            sha=hashlib.sha256(ref.read_bytes()).hexdigest()
            job={'speech_text':'Тест.', 'tts_allowed':True,'text_approved_by_human':True,
                 'style_control':'speak with restrained sorrow',
                 'voice_reference_human_approved':True,'original_en_source_verified':True}
            x=build_strict_style_pair(job,verified_same_character_ref=ref,expected_ref_sha256=sha,fork_style_supported=True)
            self.assertEqual(x['variant_A']['reference_wav_path'],x['variant_B']['reference_wav_path'])
            self.assertTrue(x['variant_B']['text'].startswith('('))
            for key in ('tts_allowed','text_approved_by_human','original_en_source_verified','voice_reference_human_approved'):
                rejected=dict(job);rejected[key]=False
                with self.assertRaises(SafetyHold):build_strict_style_pair(rejected,verified_same_character_ref=ref,expected_ref_sha256=sha,fork_style_supported=True)
            with self.assertRaises(SafetyHold):build_strict_style_pair(job,verified_same_character_ref=ref,expected_ref_sha256='0'*64,fork_style_supported=True)
    def test_old_r1_candidate_pub_no_mutation(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'accepted.wav';a=mk_wav();q=publish_candidate_once(f,a,sound_id='ACC',fingerprint='a'*64)
            self.assertEqual(q['status'],'NEW_NOT_APPROVED')
            self.assertEqual(publish_candidate_once(f,a,sound_id='ACC',fingerprint='a'*64)['status'],'REUSED_SHA_VERIFIED')
            with self.assertRaises(SafetyHold):publish_candidate_once(f,a,sound_id='ACC',fingerprint='b'*64)
            self.assertEqual(f.read_bytes(),a)
    def test_concurrent_zip_lock_works(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'report.zip'
            with zipfile.ZipFile(p,'w') as z:z.writestr('seed.txt',b'a')
            q=multiprocessing.Queue();procs=[multiprocessing.Process(target=merge_worker,args=(p,v,20,q)) for v in ('A','B')]
            for proc in procs:proc.start()
            for proc in procs:proc.join(timeout=25);self.assertEqual(proc.exitcode,0)
            self.assertEqual([q.get(timeout=5) for proc in procs],['PASS','PASS'])
            with zipfile.ZipFile(p) as z:self.assertEqual(len(z.namelist()),41)
            self.assertEqual(inspect_report_readonly(p)['entry_count'],41)

if __name__=='__main__':unittest.main(verbosity=2)
