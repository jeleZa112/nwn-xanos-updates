#!/usr/bin/env python3
"""BGXAI read-only static EEex compatibility check V2. Not an installer.

Only checks code present in this exact EET and hashes source files. It never
claims that APIs are available at runtime or that weapons may be switched.
No game writes, no hooks, no WeiDU, no changes to BGXAI_UPDATE.cmd.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re

GAME = Path(r'C:\Games\BG_EET_FOXX_NEW')
LIMIT = 2_000_000
CALLS = {
    'bootstrap': ('override/M___EEex.lua', ()),
    'attack_info': ('EEex_scripts/B3AttackInfo.lua', (
        r'EEex\.GetWeaponHitChance\s*\(',
        r'EEex\.IsImmuneToWeapon\s*\(',
        r'sourceSpriteEquipment\.m_selectedWeapon\b',
        r'sourceSpriteEquipment\.m_selectedWeaponAbility\b',
    )),
    'action': ('EEex_scripts/EEex_Action.lua', (
        r'function\s+EEex_Action_AddSpriteStartedActionListener\s*\(',
        r'function\s+EEex_Action_LuaHook_OnAfterSpriteStartedAction\s*\(',
        r'sprite\.m_curAction\b',
    )),
    'r1': ('override/M_BGXWP.lua', ()),
    'r2': ('override/M_BGXW2.lua', ()),
    'r4': ('override/M_BGXW4.lua', ()),
}
# Lua lexical masking: strip quotes and comments, preserving source-code tokens
# and newline boundaries. Not a full Lua parser and never proves execution.
_LONG_OPEN = re.compile(r'\[(=*)\[')

def code_only(src: str) -> str:
    result=[];i=0;n=len(src)
    def mask(s: str) -> str:
        return ''.join('\n' if c=='\n' else ' ' for c in s)
    def long_end(pos: int):
        m=_LONG_OPEN.match(src,pos)
        if not m:return None
        end_token=']'+m.group(1)+']'
        at=src.find(end_token,m.end())
        return n if at<0 else at+len(end_token)
    while i<n:
        if src.startswith('--',i):
            j=long_end(i+2)
            if j is None:
                at=src.find('\n',i)
                j=n if at<0 else at
            result.append(mask(src[i:j]));i=j
        elif src[i] in ('"',"'"):
            quote=src[i];j=i+1
            while j<n:
                if src[j]=='\\':j=min(n,j+2)
                elif src[j]==quote:
                    j+=1;break
                else:j+=1
            result.append(mask(src[i:j]));i=j
        elif src[i]=='[' and (j:=long_end(i)) is not None:
            result.append(mask(src[i:j]));i=j
        else:
            result.append(src[i]);i+=1
    return ''.join(result)

def alias(path: Path) -> bool:
    if path.is_symlink():return True
    checker=getattr(path,'is_junction',None)
    return bool(checker and checker())

def read_script(root: Path, rel: str):
    meta={'relative':rel,'sha256':None,'bytes':None,'exists':False}
    p=root
    for part in Path(rel).parts:
        if part in ('','..','.') or Path(part).is_absolute():
            meta['error']='PATH_NOT_CANONICAL';return meta,None
        p=p/part
        if alias(p):
            meta['error']='REPARSE_POINT_STOP';return meta,None
    if not p.is_file():
        meta['error']='FILE_MISSING';return meta,None
    try:
        st=p.stat()
        if st.st_size<=0 or st.st_size>LIMIT:
            meta['error']='SCRIPT_SIZE_INVALID';return meta,None
        with p.open('rb') as handle:
            before=os.fstat(handle.fileno())
            if before.st_size!=st.st_size:
                meta['error']='SOURCE_RACED';return meta,None
            data=handle.read(LIMIT+1)
            after=os.fstat(handle.fileno())
        if len(data)!=before.st_size or after.st_size!=before.st_size or after.st_mtime_ns!=before.st_mtime_ns:
            meta['error']='SOURCE_RACED';return meta,None
        meta.update({'exists':True,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
        if b'\x00' in data:
            meta['error']='SCRIPT_BINARY_DATA_STOP';return meta,None
        try:
            return meta, data.decode('utf-8-sig','strict')
        except UnicodeError:
            meta['error']='SCRIPT_ENCODING_UNVERIFIED';return meta,None
    except (OSError,ValueError):
        meta['error']='SCRIPT_READ_FAILED';return meta,None

def scan(root: Path):
    report={'schema':'BGXAI_EEEX_R11_STATIC_COMPAT_RO_V2',
        'status':'HOLD','gameModified':False,'readOnly':True,
        'runtimeApiAuthenticated':False,'liveHookSafetyProven':False,
        'nativeEvidenceAuthenticated':False,'manualEPSBoundaryProven':False,
        'alternateSlotAPRVerified':False,'weaponSwitchAuthorized':False,
        'installAuthorized':False,'scripts':{}}
    if not root.is_dir() or alias(root):
        report['status']='HOLD_ROOT_UNAVAILABLE_OR_REPARSE';return report
    key=root/'chitin.key'
    if not key.is_file() or alias(key):
        report['status']='HOLD_CHITIN_UNVERIFIED';return report
    good=True
    for name,(relative,patterns) in CALLS.items():
        meta,src=read_script(root,relative)
        if src is None:good=False
        else:
            active=code_only(src)
            absent=[index for index,pattern in enumerate(patterns) if not re.search(pattern,active)]
            meta['expectedStaticCallsitesPresent']=not absent
            meta['missingCallsiteIndices']=absent
            if absent:good=False
        report['scripts'][name]=meta
    report['status']='STATIC_CALLSITES_FOUND_RUNTIME_NOT_PROVEN' if good else 'HOLD_STATIC_COMPAT_INCOMPLETE'
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game',default=str(GAME))
    args=p.parse_args()
    # Only exact installed game path is accepted when launched, never test fixture paths.
    if os.name!='nt' or os.path.normcase(os.path.abspath(args.game))!=os.path.normcase(os.path.abspath(str(GAME))):
        print(json.dumps({'status':'HOLD_EXPECTED_WINDOWS_GAME_ONLY','gameModified':False,'weaponSwitchAuthorized':False}))
        return 2
    out=scan(Path(args.game))
    print(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True))
    return 0 if out['status']=='STATIC_CALLSITES_FOUND_RUNTIME_NOT_PROVEN' else 3

if __name__=='__main__':raise SystemExit(main())
