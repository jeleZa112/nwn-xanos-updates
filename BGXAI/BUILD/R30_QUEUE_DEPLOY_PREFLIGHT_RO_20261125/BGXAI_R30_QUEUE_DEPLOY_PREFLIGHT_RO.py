#!/usr/bin/env python3
"""BGXAI R30 passive observer replacement feasibility: READ ONLY, fail closed.

This is NOT a WeiDU installer, status switcher, bootstrap, or a source of
approval. Its purpose is to avoid replaying the original R27 WeiDU-last
assumption before staging an eventually typed-authorized upgrade.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys

SCHEMA = 'BGXAI_R30_PASSIVE_QUEUE_READONLY_PREFLIGHT_V1'
OLD_R27_SHA = 'e5eb400c56ffb1bc23344a0cf30dcc724d8d18fc2752fabd1c2c63cdcca73735'
SOURCE_CANDIDATE_SHA = '7ca77abeb94363c75cc58986db4427d9f93edba25e09764be35008c2f0e0600b'
# Snapshot anchored in user's 24 Nov existing preflight. These are provenance
# gates, not instructions to modify or restore either source.
EEEX_ACTION_SHA = '7a64c157418f503e914c4fb3083c97f017e70c9787024fcac779f162c86f20da'
EEEX_SPRITE_SHA = '4813ae620f0b472903848018d66488805db7ba2012e065019f4ea5f2a6afab28'
EPS_CORE_SHA = '1da3e226645367aa4cc8ba3ff8c1f14627df5ccd3c3e0852941c256b5301e776'

# Regex deliberately accepts path variations but validates actual WeiDU
# component 0, not a substring of a different component name.
R27 = re.compile(r'^~(?:[^~]*/)?BGXR27/SETUP-BGXR27[.]TP2~\s+#0\s+#0(?:\s|$)', re.I)
R30 = re.compile(r'^~(?:[^~]*/)?BGXQ30/SETUP-BGXQ30[.]TP2~\s+#0\s+#0(?:\s|$)', re.I)
FORBIDDEN = (b'ClearActions(', b'SelectWeaponAbility(', b'ActionOverride(',
             b'SetGlobal(', b'Stop(', b'Attack(', b'getAbility(',
             b'getLauncher(', b'EEex_Action_AddSpriteStartedActionListener(',
             b'EEex_Action_QueueScriptFileResponseOnAIBase(',
             b'EEex_Resource_Demand(', b'io.open(', b'os.execute(')

class Hold(ValueError):
    pass


def safe(root: Path, rel: str) -> Path:
    if not rel or rel.startswith(('/', '\\')):
        raise Hold('INVALID_RELATIVE_PATH')
    path = root
    for bit in rel.replace('\\', '/').split('/'):
        if bit in ('', '.', '..'):
            raise Hold('INVALID_PATH_COMPONENT')
        path = path / bit
        # Windows junction is a reparse point too, not just an NTFS symlink.
        is_junction = getattr(path, 'is_junction', None)
        if path.is_symlink() or (is_junction and is_junction()):
            raise Hold('REPARSE_POINT_DENIED:' + rel)
    return path


def blob(root: Path, rel: str, maximum: int = 4_000_000) -> tuple[str, bytes]:
    p = safe(root, rel)
    if not p.is_file() or p.stat().st_size > maximum:
        raise Hold('SOURCE_MISSING_OR_OVERSIZE:' + rel)
    raw = p.read_bytes()
    return hashlib.sha256(raw).hexdigest(), raw


def entries(raw: bytes) -> list[str]:
    # WeiDU log ordering is material; never sort or truncate the installed list.
    if len(raw) > 4_000_000:
        raise Hold('WEIDU_LOG_OVERSIZE')
    lines = raw.decode('utf-8-sig', errors='replace').splitlines()
    out = []
    for line in lines:
        if not line.lstrip().startswith('~'):
            continue
        normalized = line.strip().replace('\\', '/')
        if not re.match(r'^~[^~]+~\s+#\d+\s+#\d+(?:\s|$)', normalized):
            raise Hold('WEIDU_MALFORMED_COMPONENT')
        out.append(normalized)
    if not out:
        raise Hold('WEIDU_NO_INSTALLED_COMPONENTS')
    return out


def inspect(root: Path, candidate: Path | None = None) -> dict:
    """Only read data and return bounded metadata; never create any file."""
    state = {'schema': SCHEMA, 'status': 'HOLD_NOT_READY_FOR_INSTALL',
             'readOnly': True, 'gameModified': False, 'installationPerformed': False,
             'ordersSent': 0, 'dispatchAuthorized': False,
             'manualEpsOriginVerified': False, 'alternateEffectiveAPRVerified': False,
             'queueBindingLiveVerified': False, 'typedInstallApproved': False}
    try:
        if not root.is_dir() or root.is_symlink():
            raise Hold('GAME_ROOT_MISSING_OR_LINK')
        log_sha, log_raw = blob(root, 'WeiDU.log')
        rows = entries(log_raw)
        old = [i for i, line in enumerate(rows) if R27.match(line)]
        if len(old) != 1:
            raise Hold('R27_COMPONENT_MISSING_OR_AMBIGUOUS')
        if any(R30.match(line) for line in rows):
            raise Hold('R30_COMPONENT_ALREADY_IN_HISTORY')
        state.update(weiduLogSha256=log_sha,
                     weiduComponentCount=len(rows),
                     r27ComponentPosition=old[0] + 1,
                     r27IsLast=old[0] == len(rows) - 1,
                     weiduLastComponent=rows[-1][:240])
        current_sha, current = blob(root, 'override/M_BGXR27.lua', 128_000)
        state['installedR27LuaSha256'] = current_sha
        if current_sha != OLD_R27_SHA:
            raise Hold('INSTALLED_R27_RESOURCE_NOT_HISTORICAL_EXACT')
        if not current.endswith(b'P.initialized=start()\n'):
            raise Hold('INSTALLED_R27_BOOTSTRAP_MISSING')
        expected = {
            'EEex/copy/EEex_scripts/EEex_Action.lua': EEEX_ACTION_SHA,
            'EEex/copy/EEex_scripts/EEex_Sprite.lua': EEEX_SPRITE_SHA,
            'enhanced-powergaming-scripts/lib/core_base.tph': EPS_CORE_SHA,
        }
        for name, required in expected.items():
            actual, _ = blob(root, name)
            if actual != required:
                raise Hold('ENGINE_OR_EPS_SOURCE_DRIFT:' + name)
        state['pinnedInstalledSourcesMatched'] = len(expected)
        # A source-only candidate is not a directly installable active Lua.
        if candidate is None:
            raise Hold('CANDIDATE_PATH_REQUIRED_FOR_SOURCE_CHECK')
        if candidate is not None:
            if candidate.is_symlink() or not candidate.is_file():
                raise Hold('CANDIDATE_MISSING_OR_LINK')
            if candidate.stat().st_size > 128_000:
                raise Hold('CANDIDATE_OVERSIZE')
            raw = candidate.read_bytes()
            state['candidateSha256'] = hashlib.sha256(raw).hexdigest()
            if state['candidateSha256'] != SOURCE_CANDIDATE_SHA:
                raise Hold('CANDIDATE_SHA_DRIFT')
            if any(fragment in raw for fragment in FORBIDDEN):
                raise Hold('CANDIDATE_CONTAINS_ENGINE_ACTION_OR_HOOK')
            if not raw.endswith(b'return R27\n'):
                raise Hold('CANDIDATE_EXPORT_MISSING')
            state['candidateSourceVerified'] = True
        # Re-read all game metadata to prevent silently accepting changed bytes.
        if blob(root, 'WeiDU.log')[0] != log_sha or \
           blob(root, 'override/M_BGXR27.lua', 128_000)[0] != current_sha:
            raise Hold('GAME_BASELINE_CHANGED_DURING_READ')
        state['status'] = 'SOURCE_AND_HISTORY_READ_ONLY_PASS_INSTALL_STILL_UNAUTHORIZED'
    except (Hold, OSError, UnicodeError, ValueError) as exc:
        state['status'] = 'HOLD_NOT_READY_FOR_INSTALL'
        state['reason'] = str(exc)[:200]
    return state


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--game', type=Path, required=True)
    parser.add_argument('--candidate', type=Path)
    args = parser.parse_args()
    result = inspect(args.game, args.candidate)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result['status'].startswith('SOURCE_AND_HISTORY_READ_ONLY_PASS') else 2

if __name__ == '__main__':
    sys.exit(main())
