# -*- coding: utf-8 -*-
"""Internal V163 onefile dispatcher for a cumulative SECOND names batch.

SOURCE ONLY until an exact SHA-pinned revision of the ONE existing
BG_EET_RU_UPDATE.cmd imports this module.  No standalone CLI and no automatic
writes to the game. Existing V162 first64 data, old dispatch, and rollback
remain immutable. Uses verified V162 bundle rather than reimplementing R3/V111.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import sys
import tempfile
import types
import urllib.request

SCHEMA = 'BG_EET_RU_CUMULATIVE_ONEFILE_DISPATCH_V163'
BASE_REF = 'ca6fa6bbc29f74ebe2884de39eb0e970813a1d3a'
BASE_SHA = 'b46a01274479fbe3c7e83cf847ef299ba41d12f4a1f051ac26cf7495b7e2ab00'
BASE_REL = 'bg-eet-ru/hit-only-v160/weapon_names_onefile_dispatch.py'
BASE_CACHE = 'V162_WEAPON_NAMES_DISPATCH.py'
SECOND_REF = 'b447162812c3cc0461052034834f3d27bee8875f'
SECOND_REL = 'bg-eet-ru/hit-only-v160/weapon_names_cumulative_source.py'
# Exact SHA256 of SECOND_REL from immutable SECOND_REF, verified by release CI.
SECOND_SHA = '0f1afca5e805a1803f4bde2614dd9ce95dd95e2110e44f067e2bca34bcb4ee15'
MAX_SOURCE = 50_000
HEX = set('0123456789abcdef')


class SourceHold(RuntimeError):
    pass


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _url(ref: str, rel: str) -> str:
    return 'https://raw.githubusercontent.com/jeleZa112/nwn-xanos-updates/'+ref+'/'+rel


def _pinned(root: Path, rel: str, name: str, url: str, sha: str,
            offline: bool) -> tuple[Path, bytes]:
    """External cache: never execute a file other than its just-checked bytes."""
    if len(sha) != 64 or set(sha) - HEX:
        raise SourceHold('UNPINNED_SOURCE')
    if Path(rel).is_absolute() or '\\' in rel or ':' in rel or '..' in Path(rel).parts:
        raise SourceHold('CACHE_REL_UNSAFE')
    target = root / rel
    if target.is_symlink() or (target.exists() and not target.is_file()):
        raise SourceHold('CACHE_TARGET_UNSAFE:'+name)
    parent = root
    for part in Path(rel).parts[:-1]:
        if part in ('..', '.', ''):
            raise SourceHold('CACHE_REL_UNSAFE')
        parent = parent / part
        if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
            raise SourceHold('CACHE_PARENT_UNSAFE:'+name)
    parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if not 0 < target.stat().st_size <= MAX_SOURCE:
            raise SourceHold('CACHED_SOURCE_SIZE_HOLD:'+name)
        content = target.read_bytes()
        if _sha(content) != sha:
            raise SourceHold('EXISTING_CACHE_SHA_DRIFT:'+name)
        return target, content
    if offline:
        raise SourceHold('OFFLINE_CACHE_MISSING:'+name)
    req = urllib.request.Request(url, headers={'User-Agent':'BG-EET-RU-ONEFILE-V163'})
    with urllib.request.urlopen(req,timeout=9) as remote:
        content = remote.read(MAX_SOURCE+1)
    if not 0 < len(content) <= MAX_SOURCE or _sha(content) != sha:
        raise SourceHold('PINNED_DOWNLOAD_SHA_HOLD:'+name)
    with tempfile.NamedTemporaryFile(dir=parent, prefix='.v163_', delete=False) as f:
        staging = Path(f.name)
        f.write(content)
        f.flush()
        os.fsync(f.fileno())
    try:
        if _sha(staging.read_bytes()) != sha or target.exists() or target.is_symlink():
            raise SourceHold('SOURCE_CHANGED_BEFORE_COMMIT:'+name)
        os.replace(staging,target)
    finally:
        if staging.exists():staging.unlink()
    return target,content


def _module(path: Path, raw: bytes, name: str):
    module = types.ModuleType(name)
    exec(compile(raw,str(path),'exec'),module.__dict__)
    return module


def _load(root: Path, offline: bool):
    p, raw = _pinned(root,BASE_CACHE,'V162_ORIGINAL_BUNDLE',
                      _url(BASE_REF,BASE_REL),BASE_SHA,offline)
    base = _module(p,raw,'v163_verified_v162_backend')
    p, raw = _pinned(root,SECOND_REL,'CUMULATIVE_SOURCE',
                     _url(SECOND_REF,SECOND_REL),SECOND_SHA,offline)
    cumulative = _module(p,raw,'v163_verified_cumulative')
    return base,cumulative


def run(game,workdir,mode='status',offline=False):
    """Only called by onefile CMD's single menu. Never a standalone runner."""
    game = Path(game)
    workdir = Path(workdir)
    try:
        if mode not in ('status','preflight','install','rollback'):
            raise SourceHold('INVALID_CUMULATIVE_MODE')
        if mode in ('install','rollback') and sys.platform != 'win32':
            raise SourceHold('GAME_WRITES_REQUIRE_WINDOWS')
        # Import stable V162 backend strictly from pinned immutable source.
        # It validates cache is external to game and rejects symlinks.
        if game.is_symlink() or workdir.is_symlink() or not (game/'chitin.key').is_file():
            raise SourceHold('GAME_PATH_UNSAFE')
        if not workdir.is_dir():
            raise SourceHold('EXTERNAL_WORKDIR_MISSING')
        g = game.resolve(strict=True)
        w = workdir.resolve(strict=True)
        if g == w or g in w.parents or w in g.parents:
            raise SourceHold('GAME_WORKDIR_OVERLAP')
        cache = workdir / '.BG_EET_RU_AUTOFIX_CACHE'
        if cache.is_symlink() or cache.exists() and not cache.is_dir():
            raise SourceHold('CACHE_UNSAFE')
        cache.mkdir(parents=True,exist_ok=True)
        base,cumulative = _load(cache,offline)
        batch = base._module(base._pinned_source(cache,'batch',offline),'batch')
        if mode == 'status':
            return cumulative.run('status',game,workdir,batch)
        if mode == 'rollback':
            typed = input('Type '+cumulative.APPROVE_ROLLBACK+' to restore first 64 (Enter cancels): ').strip()
            return cumulative.run('rollback',game,workdir,batch,typed=typed)
        catalog,resolver = base._readonly_catalog(cache,game,cumulative.HISTORICAL_SECOND_SEEDS_64,offline)
        if mode == 'preflight':
            return cumulative.run('preflight',game,workdir,batch,catalog,resolver)
        prior = cumulative.run('preflight',game,workdir,batch,catalog,resolver)
        if prior.get('status') != 'CUMULATIVE_PREFLIGHT_PASS':
            return prior
        typed = input('Type '+cumulative.APPROVE_INSTALL+' to add current-game names (Enter cancels): ').strip()
        return cumulative.run('install',game,workdir,batch,catalog,resolver,typed=typed)
    except Exception as exc:
        return {'schema':SCHEMA,'status':'CUMULATIVE_SAFE_STOP',
                'reason':type(exc).__name__+': '+str(exc)[:155],
                'gameFilesWritten':0 if mode not in ('install','rollback') else 'UNKNOWN_AFTER_EXCEPTION'}


if __name__ == '__main__':
    raise SystemExit('INTERNAL SOURCE: use existing BG_EET_RU_UPDATE.cmd only')