#!/usr/bin/env python3
"""BGXAI 059 READ ONLY preflight. Does not install/backup/edit any file.

Can be run from a separate development folder with --game-root and --source.
Any mismatch stops; the game is never modified. No network or subprocess.
"""
from __future__ import annotations
import argparse, hashlib, pathlib, re, stat, sys

EXPECTED_SOURCE_BLOB='0ce2b256f2b0d5ab9246b61e15c8b11d194cdea9'
EXPECTED_BCS_SHA256='054c1c8e99b4d8ef8fb541287844d46cb81faa4c320f59c3f39f82f8bf0ab87c'
EXPECTED_LUA_SHA256='35e450b6600f0fc65d47e535126a52e0303c360033307fa920776faec3f581ab'
LAST_RE=re.compile(r'^~(?:[^~]*[/\\])?BGX56[/\\]SETUP-BGX56\.TP2~(?=\s|$)',re.I)

class Blocked(RuntimeError): pass

def checked(root:pathlib.Path,relative:str)->pathlib.Path:
    if '/' == relative[:1] or '\\' in relative or ':' in relative or '..' in pathlib.PurePosixPath(relative).parts:
        raise Blocked('UNSAFE_RELATIVE_PATH')
    p=root/relative
    for x in (p, *p.parents):
        if x.is_symlink(): raise Blocked('SYMLINK_BLOCKED:'+str(x))
        if x==root: break
    if not p.is_file(): raise Blocked('MISSING:'+relative)
    return p

def digest(path:pathlib.Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(512*1024),b''):h.update(chunk)
    return h.hexdigest()

def git_blob(path:pathlib.Path)->str:
    raw=path.read_bytes()
    return hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest()

def read_last_weidu(path:pathlib.Path)->str:
    lines=path.read_text(encoding='utf-8-sig',errors='replace').splitlines()
    mod_entries=[x.strip() for x in lines if x.strip().startswith('~')]
    return mod_entries[-1] if mod_entries else ''

def check_game(root:pathlib.Path, bcs_pin=EXPECTED_BCS_SHA256, lua_pin=EXPECTED_LUA_SHA256)->dict:
    root=root.expanduser().absolute()
    if root.is_symlink() or not root.is_dir():raise Blocked('GAME_ROOT_MISSING_OR_SYMLINK')
    checked(root,'chitin.key')
    last=read_last_weidu(checked(root,'WeiDU.log'))
    if not LAST_RE.search(last):raise Blocked('NOT_LAST_056:'+last[:125])
    checks={'override/BDDEFAI.BCS':bcs_pin,'override/M_BX43.lua':lua_pin}
    for rel,expected in checks.items():
        if digest(checked(root,rel))!=expected:raise Blocked('INSTALLED_056_DRIFT:'+rel)
    return {'installed_056_last':True,'installed_bcs_sha':bcs_pin,'installed_lua_sha':lua_pin}

def check_source(path:pathlib.Path, blob_pin=EXPECTED_SOURCE_BLOB)->dict:
    path=path.expanduser().absolute()
    if path.is_symlink() or not path.is_file():raise Blocked('SOURCE_MISSING_OR_SYMLINK')
    if git_blob(path)!=blob_pin:raise Blocked('SOURCE_BLOB_MISMATCH')
    txt=path.read_text(encoding='utf-8')
    required=['P.version = "0.3.25-059-GUARD-VISIBILITY-SOURCE"',
              'BGX59Eligibility.choose(victim, options)',
              'EEex_UDEqual(guardArea,victimArea)',
              'guardian, "[ANYONE]", E.maxVisualDistancePixels',
              'if not best then return reject(selectionReason) end']
    if any(x not in txt for x in required):raise Blocked('SOURCE_MISSING_ELIGIBILITY_GATE')
    if txt.count('function P.onWeaponHit(')!=1 or txt.count('function B.prepare(')!=1:
        raise Blocked('LISTENER_OR_BRIDGE_COUNT_CHANGED')
    for line in txt.splitlines():
        action=line.split('--',1)[0]
        if any(token in action for token in ('ClearActions(', 'ActionOverride(', 'ReallyForceSpell(', 'SpellNoDec(')):
            raise Blocked('DANGEROUS_ACTION_IN_SOURCE')
    return {'source_git_blob':blob_pin,'source_bytes':path.stat().st_size,'source_sha256':digest(path)}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--game-root',type=pathlib.Path,required=True)
    ap.add_argument('--source',type=pathlib.Path,required=True)
    a=ap.parse_args()
    try:
        source=check_source(a.source)
        game=check_game(a.game_root)
    except (OSError,UnicodeError,Blocked) as e:
        print('BGXAI059 READ-ONLY: REVIEW/BLOCKED:',str(e));return 2
    print('BGXAI059 READ-ONLY: SOURCE_AND_056_BASELINE_VERIFIED')
    for k,v in {**source,**game}.items(): print(k,v)
    print('NO FILES CHANGED. NO INSTALL ACTION AVAILABLE.');return 0

if __name__=='__main__':sys.exit(main())