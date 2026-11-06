"""Isolated fake-game tests: never invokes WeiDU or touches user's real EET."""
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

base=types.ModuleType('weidu_isolated_test_032')
base.MIN_EXTRA_BYTES=100
base.digest=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
base.junction_or_link=lambda p:Path(p).is_symlink()
base.capture_critical=lambda p:{'chitin.key':base.digest(Path(p)/'chitin.key')}
old=types.ModuleType('recover_isolated_clone_033')
old.hardlink_check=lambda a,b: (_ for _ in ()).throw(ValueError('HARDLINK')) if os.stat(a).st_ino==os.stat(b).st_ino and os.stat(a).st_dev==os.stat(b).st_dev else None

def copy_one_exclusive(src,dst,n):
    if Path(dst).exists():raise ValueError('File already exists')
    Path(dst).parent.mkdir(parents=True,exist_ok=True)
    with open(dst,'xb') as f:f.write(Path(src).read_bytes())
    if base.digest(src)!=base.digest(dst):raise ValueError('copy integrity')
old.copy_one_exclusive=copy_one_exclusive
old.resume=lambda *a,**kw:{'status':'PASS_ISOLATED_INSTALL_AND_ROLLBACK'}
sys.modules['weidu_isolated_test_032']=base
sys.modules['recover_isolated_clone_033']=old
source_path=Path(__file__).parent/'reconcile_existing_clone_034.py'
spec=importlib.util.spec_from_file_location('bgx34',source_path)
mod=importlib.util.module_from_spec(spec)
sys.modules['bgx34']=mod
spec.loader.exec_module(mod)

class Test034(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/'BG_EET_FOXX_NEW';self.root.mkdir()
        self.clone=Path(self.temp.name)/'BG_EET_FOXX_NEW__BGX32_TEST';self.clone.mkdir()
        self.local=self.root/'BGXAI_LOCAL_BUILD';self.local.mkdir()
        for a in (self.root,self.clone):
            (a/'movies').mkdir();(a/'data').mkdir()
            (a/'chitin.key').write_bytes(b'FALLOUT')
            (a/'data'/'area.dat').write_bytes(b'AREA')
        self.rel='movies/IWINTRO.WBM'
        (self.root/self.rel).write_bytes(b'GOODMOVIE')
        (self.clone/self.rel).write_bytes(b'BAD-MOVIE')
        self.missing='data/missing.dat'
        (self.root/self.missing).write_bytes(b'SOME MORE')
        self.srcs={str(p.relative_to(self.root)).replace('\\','/'):(p.relative_to(self.root),p.stat().st_size)
                   for p in self.root.rglob('*') if p.is_file() and 'BGXAI_LOCAL_BUILD' not in str(p)}
        old.sibling=lambda root:self.clone
        old.inspect=lambda root,enforce_root=True:self.info()
        self.resumed=0
    def info(self):
        existing={str(p.relative_to(self.clone)).replace('\\','/'):(p,p.stat().st_size)
                  for p in self.clone.rglob('*') if p.is_file()}
        return {'status':'INCOMPLETE_CLONE_CAN_RESUME_AFTER_PROCESS_CHECK',
                'expected_files':len(self.srcs),'present_files':len(existing),
                'missing_files':len([p for p in self.srcs if p not in existing]),
                'unexpected_files':len([p for p in existing if p not in self.srcs]),
                'size_mismatches':len([p for p in existing if p in self.srcs and self.srcs[p][1]!=existing[p][1]]),
                'details':{'sources':self.srcs,'existing':existing,
                           'missing':[p for p in self.srcs if p not in existing],
                           'extra':[p for p in existing if p not in self.srcs]}}
    def fake_resume(self,root,enforce_root=True):
        self.resumed+=1
        return {'status':'PASS_ISOLATED_INSTALL_AND_ROLLBACK'}
    def reconcile(self,**kwargs):
        return mod.reconcile(self.root,enforce_root=False,resume_fn=self.fake_resume,
                             proc_check=lambda:None,log=lambda *args:None,**kwargs)
    def mismatches(self):
        return mod.collect_mismatches(self.root,self.clone,self.info()['details'],log=lambda *a:None)
    def test_01_readonly_detects_one_movie(self):
        r=self.reconcile(inspect_only=True)
        self.assertEqual(r['status'],'MOVIE_MISMATCHES_ONLY');self.assertEqual(len(r['mismatches']),1)
    def test_02_readonly_no_mutation(self):
        h=base.digest(self.clone/self.rel); self.reconcile(inspect_only=True)
        self.assertEqual(base.digest(self.clone/self.rel),h);self.assertEqual(list(self.local.iterdir()),[])
    def test_03_preserves_bad_original_and_corrects_test_movie(self):
        m=self.mismatches()
        r=mod.repair_movies(self.root,self.clone,self.local,self.info()['details'],m,tag='20261106TEST',free_bytes=99999)
        self.assertEqual(base.digest(self.clone/self.rel),base.digest(self.root/self.rel))
        self.assertEqual((Path(r['quarantine'])/self.rel).read_bytes(),b'BAD-MOVIE')
    def test_04_no_live_mutation_after_full_resume(self):
        before=base.digest(self.root/self.rel)
        with patch('bgx34.shutil.disk_usage',return_value=types.SimpleNamespace(free=100000)):
            r=self.reconcile()
        self.assertEqual(r['status'],'PASS_ISOLATED_INSTALL_AND_ROLLBACK')
        self.assertEqual(before,base.digest(self.root/self.rel));self.assertEqual(self.resumed,1)
    def test_05_non_movie_mismatch_blocked(self):
        (self.clone/'data'/'area.dat').write_bytes(b'BRA!')
        r=self.reconcile(inspect_only=True)
        self.assertEqual(r['status'],'BLOCKED_NON_MOVIE_MISMATCH')
        with self.assertRaises(ValueError):
            mod.repair_movies(self.root,self.clone,self.local,self.info()['details'],r['mismatches'],tag='20261106TEST',free_bytes=99999)
    def test_06_extras_stop(self):
        (self.clone/'extra.txt').write_text('bad')
        with self.assertRaisesRegex(ValueError,'Unexpected'):
            self.reconcile()
    def test_07_wrong_size_stop(self):
        (self.clone/self.rel).write_bytes(b'A')
        with self.assertRaisesRegex(ValueError,'size mismatches'):
            self.reconcile()
    def test_08_low_space_before_mutation(self):
        with self.assertRaisesRegex(ValueError,'Insufficient'):
            mod.repair_movies(self.root,self.clone,self.local,self.info()['details'],self.mismatches(),tag='20261106TEST',free_bytes=0)
        self.assertEqual((self.clone/self.rel).read_bytes(),b'BAD-MOVIE')
    def test_09_source_changes_between_scan_and_write(self):
        m=self.mismatches();(self.root/self.rel).write_bytes(b'MUTATEMOV')
        with self.assertRaisesRegex(ValueError,'changed after first'):
            mod.repair_movies(self.root,self.clone,self.local,self.info()['details'],m,tag='20261106TEST',free_bytes=99999)
        self.assertEqual((self.clone/self.rel).read_bytes(),b'BAD-MOVIE')
    def test_10_unapproved_path_rejected(self):
        for rel in ('override/BDDEFAI.BCS','movies/../evil.WBM','data/good.WBM','movies/x.exe'):
            self.assertFalse(mod.safe_movie_path(rel),rel)
    def test_11_movie_path_accepts_wbm_only(self):
        self.assertTrue(mod.safe_movie_path('movies/IWINTRO.WBM'))
    def test_12_symlink_to_live_denied(self):
        (self.clone/self.rel).unlink();(self.clone/self.rel).symlink_to(self.root/self.rel)
        with self.assertRaisesRegex(ValueError,'Link|HARDLINK'):
            self.mismatches()
    def test_13_hardlink_to_live_denied(self):
        (self.clone/self.rel).unlink();os.link(self.root/self.rel,self.clone/self.rel)
        with self.assertRaisesRegex(ValueError,'HARDLINK'):
            self.mismatches()
    def test_14_existing_quarantine_denied(self):
        (self.local/'BGX34_QUARANTINE_20261106TEST').mkdir()
        with self.assertRaisesRegex(ValueError,'Quarantine'):
            mod.repair_movies(self.root,self.clone,self.local,self.info()['details'],self.mismatches(),tag='20261106TEST',free_bytes=99999)
    def test_15_process_check_blocked_no_mutation(self):
        with self.assertRaisesRegex(ValueError,'ACTIVE'):
            mod.reconcile(self.root,enforce_root=False,proc_check=lambda:(_ for _ in ()).throw(ValueError('ACTIVE')),
                          resume_fn=self.fake_resume,log=lambda *a:None)
        self.assertEqual((self.clone/self.rel).read_bytes(),b'BAD-MOVIE')
    def test_16_many_mismatches_refused(self):
        with self.assertRaisesRegex(ValueError,'More than'):
            mod.collect_mismatches(self.root,self.clone,self.info()['details'],limit=0,log=lambda *a:None)
    def test_17_no_mismatch_is_safe(self):
        shutil.copy2(self.root/self.rel,self.clone/self.rel)
        r=self.reconcile(inspect_only=True)
        self.assertEqual(r['status'],'NO_DIVERGENCE')
    def test_18_resume_failure_is_not_reported_as_success(self):
        with patch('bgx34.shutil.disk_usage',return_value=types.SimpleNamespace(free=100000)):
            r=mod.reconcile(self.root,enforce_root=False,proc_check=lambda:None,
                            resume_fn=lambda *a,**k:{'status':'REVIEW_ISOLATED_WEIDU'},log=lambda *a:None)
        self.assertEqual(r['status'],'REVIEW_ISOLATED_WEIDU')
    def test_19_no_EPS_source_files_copied(self):
        m=self.mismatches()
        r=mod.repair_movies(self.root,self.clone,self.local,self.info()['details'],m,tag='20261106TEST',free_bytes=99999)
        self.assertEqual(sorted(str(p.relative_to(Path(r['quarantine']))) for p in Path(r['quarantine']).rglob('*') if p.is_file()),[self.rel])
    def test_20_copy_error_rolls_back_to_original_clone(self):
        m=self.mismatches()
        with patch('bgx34.old.copy_one_exclusive',side_effect=ValueError('COPY FAILED')):
            with self.assertRaisesRegex(ValueError,'COPY FAILED'):
                mod.repair_movies(self.root,self.clone,self.local,self.info()['details'],m,tag='20261106TEST',free_bytes=99999)
        self.assertEqual((self.clone/self.rel).read_bytes(),b'BAD-MOVIE')

if __name__=='__main__':unittest.main(verbosity=2)