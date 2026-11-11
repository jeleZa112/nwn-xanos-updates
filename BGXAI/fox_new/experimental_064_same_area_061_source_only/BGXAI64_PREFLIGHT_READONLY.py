"""Read-only candidate preflight for integration into existing BGXAI_UPDATE.cmd.

No CLI or game installer supplied. This module checks real live disk state only
when called by the pinned existing updater in a future guarded release.
Never modifies the game, WeiDU.log, or BGX61 stage.
"""
from __future__ import annotations
import re
import stat
from pathlib import Path
from BGXAI64_PATCH import build_candidate,digest,PIN_061,PIN_064

BCS_SHA='db0fcba4678b00defa2ed7887b57c0d4207effc064891aeb9a0d7dcc1a1a6b0b'
LAST061=re.compile(r'^~(?:[^~]*[/\\])?BGX61[/\\]SETUP-BGX61\.TP2~(?=\s|$)',re.IGNORECASE)
WATCH=('WeiDU.log','chitin.key','override/BDDEFAI.BCS','override/M_BX43.lua',
       'BGX61/staged/BDDEFAI.BCS','BGX61/staged/M_BX43.lua')

class Stop(ValueError):pass

def is_reparse(path:Path)->bool:
    if path.is_symlink(): return True
    try: return bool(path.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)
    except (FileNotFoundError,AttributeError): return False

def safe_read(root:Path,relative:str)->bytes:
    if not relative or relative.startswith(('/', '\\')) or ':' in relative or '\\' in relative or '..' in Path(relative).parts:
        raise Stop('UNSAFE_PATH')
    p=root/relative
    if any(is_reparse(q) for q in (p,*p.parents)):
        raise Stop('SYMLINK_BLOCKED:'+relative)
    if not p.is_file(): raise Stop('MISSING_FILE:'+relative)
    return p.read_bytes()

def check(root:Path, *,bcs_pin=BCS_SHA,lua_pin=PIN_061,candidate_pin=PIN_064):
    """Return proof or raise. Default pins are the only production contract."""
    root=Path(root)
    if not root.is_dir() or is_reparse(root): raise Stop('INVALID_GAME_ROOT')
    original={rel:safe_read(root,rel) for rel in WATCH}
    # No game filesystem writes anywhere, even after a failed assertion.
    entries=[s.strip() for s in original['WeiDU.log'].decode('utf-8-sig',errors='replace').splitlines()
             if s.lstrip().startswith('~')]
    if not entries or not LAST061.search(entries[-1]): raise Stop('LAST_WEIDU_NOT_061')
    if digest(original['override/BDDEFAI.BCS'])!=bcs_pin:raise Stop('INSTALLED_BCS_MISMATCH')
    if digest(original['override/M_BX43.lua'])!=lua_pin:raise Stop('INSTALLED_LUA_MISMATCH')
    if original['BGX61/staged/BDDEFAI.BCS']!=original['override/BDDEFAI.BCS']:
        raise Stop('061_BCS_STAGE_MISMATCH')
    if original['BGX61/staged/M_BX43.lua']!=original['override/M_BX43.lua']:
        raise Stop('061_LUA_STAGE_MISMATCH')
    result,proof=build_candidate(original['override/M_BX43.lua'],
                   baseline_sha=lua_pin,candidate_sha=candidate_pin)
    for rel,raw in original.items():
        if safe_read(root,rel)!=raw: raise Stop('LIVE_FILE_CHANGED_DURING_CHECK:'+rel)
    return {'status':'064_SOURCE_ONLY_PREFLIGHT_PASS','last_weidu':entries[-1],
            'game_bcs_sha':bcs_pin,'game_lua_sha':lua_pin,
            'candidate_lua_sha':digest(result), 'patch_proof':proof,
            'installed_game_changed':False,'eeex_runtime_area_api':'NOT_CHECKED',
            'authorized_to_install':False}
