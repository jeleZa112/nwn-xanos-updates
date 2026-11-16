#!/usr/bin/env python3
"""Offline source-only manifest, old-080 append proof, Lua regression test runner."""
import hashlib, json, re, shutil, subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
BASE=HERE/'BGXAI080_EPS_FIRST_COORDINATOR.lua'
CAND=HERE/'BGXAI080_EPS_FIRST_COORDINATOR_MULTI_THREAT_SOURCE_ONLY.lua'
MAN=HERE/'SHA256_MULTI_THREAT_SOURCE_ONLY.json'

def check():
    manifest=json.loads(MAN.read_text(encoding='utf-8'))
    assert manifest['status']=='SOURCE_ONLY_NOT_INSTALLED'
    names=set(manifest['files'])
    actual={p.name for p in HERE.iterdir() if p.is_file() and p.name!='SHA256_MULTI_THREAT_SOURCE_ONLY.json'}
    assert names==actual,(names-actual,actual-names)
    for name,expected in manifest['files'].items():
        assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==expected,name
    base=BASE.read_bytes()
    altered=CAND.read_bytes()
    assert altered.startswith(base[:-len(b'return M\n')]),'OLD_080_CHANGED'
    assert altered.endswith(b'return M\n'),'NO_FINAL_RETURN'
    delta=altered[len(base)-len(b'return M\n'):-len(b'return M\n')]
    assert delta.startswith(b'-- BGXAI EPS-FIRST MULTI-THREAT extension'), 'WRONG_NEW_MODULE'
    assert delta.count(b'function M.reviewMultipleThreats(')==1
    assert b'function M.review(' not in delta,'OLD_REVIEW_REDEFINED'
    for action in (rb'\bClearActions\s*\(',rb'\bSpell\s*\(',rb'\bAttack\s*\(',rb'\bUseItem\s*\(',rb'\bProtectObject\s*\('):
        assert re.search(action,delta) is None,action
    exe=shutil.which('texlua')
    if not exe: raise RuntimeError('texlua missing; tests NOT executed')
    for script,label in [('syntax_check.lua','LUA_SYNTAX_OK'),('test_080.lua','BGXAI080_EPS_FIRST_COORDINATOR_TESTS_PASS 82'),('test_080_candidate.lua','BGXAI080_EPS_FIRST_COORDINATOR_TESTS_PASS 82'),('test_multi_threat.lua','BGXAI_MULTI_THREAT_TESTS_PASS 143')]:
        proc=subprocess.run([exe,script],cwd=HERE,capture_output=True,text=True,timeout=20)
        assert proc.returncode==0,(script,proc.stdout,proc.stderr)
        assert label in proc.stdout,(script,proc.stdout)
        print(proc.stdout.strip())
    print('BGXAI_MULTI_THREAT_RELEASE: SHA %d/%d, OLD_080_APPEND_ONLY, NO_ENGINE_CALLS PASS' % (len(names),len(names)))

if __name__=='__main__':check()
