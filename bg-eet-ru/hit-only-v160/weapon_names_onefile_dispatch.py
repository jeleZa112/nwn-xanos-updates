# -*- coding: utf-8 -*-
"""V162 backend imported ONLY by the existing SHA-pinned BG_EET_RU_UPDATE.cmd.

This is not a user-facing script or second updater. All downloaded Python
sources are immutable Git-ref + SHA256 checked before their first execution.
No writes to game except delegated typed batch.run('install'/'rollback').
"""
from __future__ import annotations
import hashlib
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import urllib.request

COMMIT = '26a3a792af22257edf85da0877f306199d15ea43'
BASE = 'https://raw.githubusercontent.com/jeleZa112/nwn-xanos-updates/' + COMMIT + '/'
# Set exact sha256 values only after byte-identical CI (never a moving ref).
SOURCES = {
    'batch': ('bg-eet-ru/hit-only-v160/weapon_names_batch_source.py', '79ac47a9b1189502722eaf699238b67f930a0a6b4fdd05ebdb42fb567e930288'),
    'bridge': ('bg-eet-ru/weapon-identity/BG_EET_RU_ITEM_NAMES_FROM_BGXAI_R3_RO.py', 'd0f13bb8e865da671a345bf68a0f6ee59cb52ca1d56e357d4731f5a3f4ff2634'),
    'r3': ('BGXAI/BUILD/R27_SINGLE_CALLBACK_SELECTED_RO_20261123/BGXAI_WEAPON_NATIVE_ITM_R3_RO.py', 'ed87a7a6618826c6d3901d2579a39bf280fcaeb09cd18b7b6ee159b9ebfcc74a'),
    'v111': ('bg-eet-ru/weapon-identity/V111_ITEM_NAMES_READONLY_SOURCE_ONLY.py', 'bb9e9d39ed9c5d06c90930c8f3974cc22e5594e1c41e1024ce11c7c8e05600c0'),
    'v160': ('bg-eet-ru/hit-only-v160/v160_guarded.py', 'ccf02f4892bf0ed434ac97a1f0bb7d7da2a9abdde8fafe7a64b422386e82b2de'),
}
MAX_SOURCE_BYTES = 100_000

class SourceHold(RuntimeError):
    pass

def _sha(b):
    return hashlib.sha256(b).hexdigest()

def _external_root(game: Path, workdir: Path) -> Path:
    if game.is_symlink() or workdir.is_symlink() or not game.is_dir() or not workdir.is_dir() or not (game / 'chitin.key').is_file():
        raise SourceHold('GAME_OR_WORKDIR_UNSAFE')
    g = game.resolve(strict=True)
    w = workdir.resolve(strict=True)
    if g == w or g in w.parents or w in g.parents:
        raise SourceHold('EXTERNAL_CACHE_MUST_NOT_BE_IN_GAME')
    cache = workdir / '.BG_EET_RU_AUTOFIX_CACHE'
    if cache.is_symlink() or cache.exists() and not cache.is_dir():
        raise SourceHold('CACHE_UNSAFE')
    cache.mkdir(parents=True, exist_ok=True)
    return cache

def _pinned_source(root: Path, key: str, offline: bool) -> Path:
    relative, expected = SOURCES[key]
    if len(expected) != 64 or any(c not in '0123456789abcdef' for c in expected):
        raise SourceHold('SOURCE_SHA_NOT_PINNED')
    path = root / relative
    parent = root
    for part in Path(relative).parts[:-1]:
        parent = parent / part
        if parent.is_symlink() or parent.exists() and not parent.is_dir():
            raise SourceHold('CACHE_PARENT_UNSAFE')
    parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink() or path.exists() and not path.is_file():
        raise SourceHold('CACHE_FILE_UNSAFE')
    if path.is_file():
        if path.stat().st_size <= MAX_SOURCE_BYTES and _sha(path.read_bytes()) == expected:
            return path
        raise SourceHold('CACHE_SOURCE_DRIFT_REQUIRES_REVIEW')
    if offline:
        raise SourceHold('PINNED_CACHE_MISSING_OFFLINE:' + key)
    req = urllib.request.Request(BASE + relative, headers={'User-Agent':'BG-EET-RU-ONEFILE-V162'})
    with urllib.request.urlopen(req, timeout=9) as response:
        raw = response.read(MAX_SOURCE_BYTES + 1)
    if not raw or len(raw) > MAX_SOURCE_BYTES or _sha(raw) != expected:
        raise SourceHold('REMOTE_SOURCE_SHA_MISMATCH:' + key)
    with tempfile.NamedTemporaryFile(dir=parent, prefix='.v162_', delete=False) as f:
        stage = Path(f.name)
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())
    try:
        if _sha(stage.read_bytes()) != expected or path.exists() or path.is_symlink():
            raise SourceHold('CACHE_STAGE_CHANGED')
        os.replace(stage,path)
    finally:
        if stage.exists():stage.unlink()
    return path

def _module(path: Path, key: str):
    raw=path.read_bytes()
    if _sha(raw) != SOURCES[key][1]:
        raise SourceHold('PIN_CHANGED_BEFORE_IMPORT:' + key)
    spec=importlib.util.spec_from_file_location('bg_eet_ru_v162_checked_'+key,path)
    if spec is None or spec.loader is None:
        raise SourceHold('MODULE_IMPORT_UNAVAILABLE')
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def _readonly_catalog(root,game,keys,offline):
    from pathlib import Path
    bridge = _module(_pinned_source(root,'bridge',offline),'bridge')
    # bridge loads these two exact upstream modules using Git blob pins.
    _pinned_source(root,'r3',offline)
    _pinned_source(root,'v111',offline)
    catalog = bridge.build_catalog(root,game,keys)
    r3 = bridge.verified_module(root,bridge.R3_REL,bridge.R3_BLOB_SHA)
    return catalog, r3.NativeSource(game)

def run(game,workdir,mode='status',offline=False):
    """One-file caller owns ZIP reporting, update lock and menu dispatch."""
    from pathlib import Path
    game=Path(game);workdir=Path(workdir)
    try:
        cache=_external_root(game,workdir)
        batch=_module(_pinned_source(cache,'batch',offline),'batch')
        if mode not in ('status','preflight','install','rollback'):
            raise SourceHold('INVALID_BATCH_MODE')
        if mode in ('install','rollback') and sys.platform != 'win32':
            raise SourceHold('GAME_WRITES_REQUIRE_WINDOWS')
        if mode in ('status','rollback'):
            if mode == 'status':return batch.run('status',game,workdir)
            typed=input('Type '+batch.APPROVE_ROLLBACK+' to restore V160 (Enter cancels): ').strip()
            return batch.run('rollback',game,workdir,typed=typed)
        v160=_module(_pinned_source(cache,'v160',offline),'v160')
        catalog,resolver=_readonly_catalog(cache,game,batch.HISTORICAL_WEAPON_SEEDS_64,offline)
        if mode == 'preflight':
            return batch.run('preflight',game,workdir,catalog,resolver,v160.GAME_PINS)
        check=batch.run('preflight',game,workdir,catalog,resolver,v160.GAME_PINS)
        if check.get('status')!='BATCH_PREFLIGHT_PASS':return check
        typed=input('Type '+batch.APPROVE_INSTALL+' to add verified names (Enter cancels): ').strip()
        return batch.run('install',game,workdir,catalog,resolver,v160.GAME_PINS,typed=typed)
    except (SourceHold,OSError,ValueError,TypeError,KeyError,EOFError,ImportError) as exc:
        return {'schema':'BG_EET_RU_WEAPON_NAMES_BATCH_DISPATCH_V162',
                'status':'BATCH_SAFE_STOP','reason':type(exc).__name__+': '+str(exc)[:155],
                'gameFilesWritten':0 if mode in ('status','preflight') else 'UNKNOWN_AFTER_EXCEPTION'}

if __name__ == '__main__':
    raise SystemExit('INTERNAL MODULE ONLY; use the existing BG_EET_RU_UPDATE.cmd')