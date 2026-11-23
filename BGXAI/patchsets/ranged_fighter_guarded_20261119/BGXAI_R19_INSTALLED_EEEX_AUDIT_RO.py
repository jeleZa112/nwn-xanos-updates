#!/usr/bin/env python3
"""BGXAI R19 — read-only *static* installed EEex v1.1.7 API provenance.

Never reads a game object or CItem pointer, calls a game API, alters a file,
starts a process, executes Lua, attaches a hook or authorizes switching. Main
entrypoint is deliberately Windows / known-game only; unit tests use fixtures.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import stat
from pathlib import Path
from typing import Any

GAME = Path(r'C:\Games\BG_EET_FOXX_NEW')
MAX_BYTES = 2_000_000
# Git blob SHA-1 values taken from the official Bubb13/EEex **v1.1.7** tag.
# These are NOT claimed to be hashes of the user's installed EEex.
UPSTREAM = {
    'resource': ('EEex_scripts/EEex_Resource.lua', '5ecd3c2f9e9bcc6cbd317653fc057a06d956916b'),
    'sprite': ('EEex_scripts/EEex_Sprite.lua', 'b2d8d930c47785737bd30dad08e9f35a9d859578'),
    'action': ('EEex_scripts/EEex_Action.lua', 'e7543274ed066b5abe3c58262105212f208d1595'),
}
# Required code tokens must occur in executable code, not Lua comments/strings.
PATTERNS = {
 'resource': (
    r'function\s+EEex_Resource_GetItemAbility\s*\(\s*itemHeader\s*,\s*abilityIndex\s*\)',
    r'itemHeader\.abilityCount\s*<=\s*abilityIndex',
    r'function\s+EEex_Resource_GetCItemAbility\s*\(\s*item\s*,\s*abilityIndex\s*\)',
    r'item\.pRes\.pHeader\s*:\s*getAbility\s*\(\s*abilityIndex\s*\)',
    r'CItem\.getAbility\s*=\s*EEex_Resource_GetCItemAbility',
 ),
 'sprite': (
    r'function\s+EEex_Sprite_GetLauncher\s*\(\s*sprite\s*,\s*curAbility\s*\)',
    r'sprite\s*:\s*GetLauncher\s*\(\s*curAbility\s*,\s*launcherSlot\s*\)',
    r'CGameSprite\.getLauncher\s*=\s*EEex_Sprite_GetLauncher',
    r'function\s+EEex_Sprite_GetActiveStats\s*\(\s*sprite\s*\)',
    r'CGameSprite\.getActiveStats\s*=\s*EEex_Sprite_GetActiveStats',
 ),
 'action': (
    r'function\s+EEex_Action_AddSpriteStartedActionListener\s*\(\s*func\s*\)',
    r'table\.insert\s*\(\s*EEex_Action_Private_SpriteStartedActionListeners\s*,\s*func\s*\)',
    r'function\s+EEex_Action_LuaHook_OnAfterSpriteStartedAction\s*\(\s*sprite\s*\)',
    r'EEex_Utility_TryIgnore\s*\(\s*listener\s*,\s*sprite\s*,\s*action\s*\)',
 ),
}


def _sha1_git_blob(raw: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(raw)).encode('ascii') + b'\0' + raw).hexdigest()


def _path_alias(p: Path) -> bool:
    if p.is_symlink():
        return True
    attrs = getattr(p.stat(follow_symlinks=False), 'st_file_attributes', 0)
    return bool(attrs & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400))


def _safe_read(root: Path, relative: str) -> tuple[dict[str, Any], str | None]:
    meta: dict[str, Any] = {'path': relative, 'present': False, 'sha256': None,
                            'gitBlobSha1Raw': None, 'gitBlobSha1LF': None,
                            'exactUpstreamByteMatch': False, 'canonicalLFUpstreamMatch': False}
    if not isinstance(relative, str) or not re.fullmatch(r'[A-Za-z0-9_./-]{1,120}', relative):
        meta['error'] = 'INVALID_RELATIVE_PATH';return meta,None
    parts = relative.split('/')
    if any(x in ('','.','..') for x in parts):
        meta['error'] = 'INVALID_RELATIVE_PATH';return meta,None
    p = root
    try:
        for part in parts:
            p=p/part
            if _path_alias(p):
                meta['error']='REPARSE_COMPONENT_REJECTED';return meta,None
        if not p.is_file():
            meta['error']='FILE_MISSING';return meta,None
        first = p.stat()
        if not 1 <= first.st_size <= MAX_BYTES:
            meta['error']='SIZE_REJECTED';return meta,None
        with p.open('rb') as f:
            before = os.fstat(f.fileno())
            data = f.read(MAX_BYTES + 1)
            after = os.fstat(f.fileno())
        last = p.stat()
        if (len(data)!=first.st_size or before.st_size!=first.st_size or
            after.st_size!=before.st_size or first.st_mtime_ns!=after.st_mtime_ns or
            after.st_mtime_ns!=last.st_mtime_ns or last.st_size!=first.st_size):
            meta['error']='READ_RACE_OR_SIZE_CHANGED';return meta,None
        if b'\x00' in data:
            meta['error']='BINARY_SOURCE_REJECTED';return meta,None
        try: source=data.decode('utf-8-sig','strict')
        except UnicodeError:
            meta['error']='INVALID_UTF8';return meta,None
        meta.update(present=True, bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),
                    gitBlobSha1Raw=_sha1_git_blob(data),
                    gitBlobSha1LF=_sha1_git_blob(data.replace(b'\r\n',b'\n').lstrip(b'\xef\xbb\xbf')))
        return meta,source
    except (OSError,ValueError):
        meta['error']='READ_ERROR';return meta,None


def _code_only(src: str) -> str:
    """Mask Lua strings and comments, including long bracket variants."""
    n=len(src); out=[];i=0
    def mask(text: str) -> str:
        return ''.join('\n' if c=='\n' else ' ' for c in text)
    def long_end(pos: int) -> int | None:
        m=re.match(r'\[(=*)\[',src[pos:])
        if not m:return None
        close=']'+m.group(1)+']'
        end=src.find(close,pos+m.end())
        return n if end<0 else end+len(close)
    while i<n:
        if src.startswith('--',i):
            long=long_end(i+2)
            if long is None:
                end=src.find('\n',i)
                long=n if end<0 else end
            out.append(mask(src[i:long]));i=long
        elif src[i] in ('"',"'"):
            ch=src[i];j=i+1
            while j<n:
                if src[j]=='\\':j=min(n,j+2)
                elif src[j]==ch:j+=1;break
                else:j+=1
            out.append(mask(src[i:j]));i=j
        elif src[i]=='[' and (end:=long_end(i)) is not None:
            out.append(mask(src[i:end]));i=end
        else:
            out.append(src[i]);i+=1
    return ''.join(out)


def check_contract(key: str, source: str) -> dict[str, Any]:
    if key not in PATTERNS or not isinstance(source,str):
        return {'allCallsitesPresent':False,'missingPatternIds':list(range(1,20))}
    code=_code_only(source)
    missing=[i+1 for i,pattern in enumerate(PATTERNS[key]) if not re.search(pattern,code)]
    return {'allCallsitesPresent':not missing,'missingPatternIds':missing}


def _read_bootstrap(root: Path) -> dict[str, Any]:
    meta,_=_safe_read(root,'override/M___EEex.lua')
    return {'present':meta.get('present',False),'sha256':meta.get('sha256'),
            'error':meta.get('error')}


def audit(root: Path, *, fixture: bool = False) -> dict[str, Any]:
    # A static audit is NEVER a health/safety proof of native pointer derefs.
    result: dict[str,Any] = {
        'schema':'BGXAI_R19_INSTALLED_EEEX_STATIC_AUDIT_RO_V1',
        'status':'HOLD', 'readOnly':True,'gameModified':False,
        'sourceTag':'v1.1.7','sourceRepository':'Bubb13/EEex',
        'fixtureMode':bool(fixture), 'installedGameFilesInspected':False,
        'allRequiredLuaScriptsPresent':False,'allStaticMethodCallsitesPresent':False,
        'allInstalledFilesExactUpstream':False,'allInstalledFilesCanonicalLFUpstream':False,
        'apiPresentAtRuntimeVerified':False,'nativeResourceLifetimeVerified':False,
        'nativeAbilityPointerSafe':False,'nativeLauncherReturnSafe':False,
        'safeToCallGetAbility':False,'safeToCallGetLauncher':False,
        'safeToRegisterListener':False,'nativeActionEventIdVerified':False,
        'fullActiveEffectsFingerprintVerified':False,'alternateSlotAPRVerified':False,
        'weaponSwitchAuthorized':False,'dispatchAuthorized':False,'installAuthorized':False,
        'gameplayActionsSent':0,'blockers':[], 'scripts':{},
    }
    try:
        if not root.is_dir() or _path_alias(root):
            result['status']='HOLD_ROOT_UNAVAILABLE_OR_REPARSE';return result
        if not fixture:
            if os.name!='nt' or os.path.normcase(os.path.abspath(root)) != os.path.normcase(os.path.abspath(GAME)):
                result['status']='HOLD_EXACT_WINDOWS_GAME_ONLY';return result
        key=root/'chitin.key'
        if not key.is_file() or _path_alias(key):
            result['status']='HOLD_GAME_KEY_MISSING';return result
        result['installedGameFilesInspected']=not fixture
    except (OSError, ValueError):
        result['status']='HOLD_ROOT_PATH_UNREADABLE';return result
    bs=_read_bootstrap(root)
    result['bootstrap']=bs
    all_present=bs['present'] is True
    all_static=True
    exact=True
    canon=True
    for key,(rel,sha) in UPSTREAM.items():
        meta,source=_safe_read(root,rel)
        meta['upstreamTagGitBlobSha1']=sha
        if source is None:
            all_present=False;all_static=False;exact=False;canon=False
            meta.update(allCallsitesPresent=False,missingPatternIds=[])
        else:
            meta['exactUpstreamByteMatch']=meta['gitBlobSha1Raw']==sha
            meta['canonicalLFUpstreamMatch']=meta['gitBlobSha1LF']==sha
            contract=check_contract(key,source)
            meta.update(contract)
            all_static=all_static and contract['allCallsitesPresent']
            exact=exact and meta['exactUpstreamByteMatch']
            canon=canon and meta['canonicalLFUpstreamMatch']
        result['scripts'][key]=meta
    result['allRequiredLuaScriptsPresent']=all_present
    result['allStaticMethodCallsitesPresent']=all_present and all_static
    result['allInstalledFilesExactUpstream']=all_present and exact
    result['allInstalledFilesCanonicalLFUpstream']=all_present and canon
    if not all_present:
        result['status']='HOLD_INSTALLED_EEEX_SOURCE_MISSING_OR_UNREADABLE'
    elif not all_static:
        result['status']='HOLD_INSTALLED_EEEX_STATIC_CALLSITES_MISSING'
    elif exact:
        result['status']='UPSTREAM_V117_EXACT_BYTES_STATIC_ONLY'
    elif canon:
        result['status']='UPSTREAM_V117_LF_EQUIVALENT_STATIC_ONLY'
    else:
        result['status']='LOCAL_EEEX_VARIANT_CALLSITES_PRESENT_STATIC_ONLY'
    result['blockers']=[
        'NO_LIVE_POINTER_LIFETIME_PROOF',
        'CITEM_GETABILITY_UNGUARDED_PRES_HEADER_DEREFERENCE',
        'GETLAUNCHER_REQUIRES_VALID_NATIVE_ABILITY_HANDLE',
        'STATIC_API_PRESENCE_DOES_NOT_ESTABLISH_RUNTIME_SAFETY',
        'ACTIVE_EFFECTS_AND_ACTION_QUEUE_UNVERIFIED',
    ]
    return result


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game',default=str(GAME))
    args=parser.parse_args()
    try: report=audit(Path(args.game),fixture=False)
    except Exception as ex:
        report={'schema':'BGXAI_R19_INSTALLED_EEEX_STATIC_AUDIT_RO_V1','status':'HOLD_AUDIT_EXCEPTION',
                'errorType':type(ex).__name__,'gameModified':False,
                'weaponSwitchAuthorized':False,'dispatchAuthorized':False}
    print(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2))
    # This tool is a read-only diagnostic; a HOLD is a supported outcome.
    # Never return success as installation authorization.
    return 0 if report['status'].endswith('_STATIC_ONLY') else 2

if __name__=='__main__':raise SystemExit(main())
