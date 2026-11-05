#!/usr/bin/env python3
"""Read-only audit of stock EET Advanced AI script resources from OWN game export.

No source BCS is ever embedded in the output. Works offline, requires Python only
on the developer workstation (not on the player's Windows game machine).
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from zipfile import ZipFile

REQUIRED = [
    'BDDEFAI.BCS', 'BDFTHI01.BCS', 'BDFIGH01.BCS', 'BDFMAG01.BCS',
    'BDFCLE01.BCS', 'BDAI0010.BCS', 'BDAI0020.BCS',
]
# These identifiers are independently checked against the user's ACTION.IDS
# audit in prior work. They are for metrics, not a substitute for WeiDU decompile.
KNOWN_ACTIONS = {31: 'Spell', 34: 'UseItem', 86: 'SetInterrupt',
                 105: 'AttackOneRound', 115: 'SetGlobalTimer',
                 134: 'AttackReevaluate', 355: 'RunAwayFromNoLeaveArea'}
RE_ACTION = re.compile(r'(?m)^AC\n(\d+)OB\n')
RE_OBJECT = re.compile(r'"(?:locals|LOCALS)(bd_(?:no_retreat|retreat|combat|no_combat))"')


def profile(name: str, raw: bytes) -> dict:
    if not (raw.startswith(b'SC\nCR\n') and raw.endswith(b'\nSC\n')):
        raise ValueError(f'{name} is not a serialized Infinity Engine script')
    txt = raw.decode('latin-1')
    count = Counter(map(int, RE_ACTION.findall(txt)))
    cr = txt.count('CR\n')
    if cr % 2:
        raise ValueError(f'{name} has unpaired CR markers')
    return {
        'resource': name,
        'size_bytes': len(raw),
        'sha256': hashlib.sha256(raw).hexdigest(),
        'rules': cr // 2,
        'actions': sum(count.values()),
        'meaningful_actions': {KNOWN_ACTIONS[k]:count[k] for k in KNOWN_ACTIONS if count[k]},
        'retreat_state_tokens': sorted({m.lower() for m in RE_OBJECT.findall(txt)}),
        'unknown_origin': True,
    }


def inspect_zip(path: Path) -> dict:
    with ZipFile(path) as z:
        present = set(z.namelist())
        if missing := [name for name in REQUIRED if name not in present]:
            raise ValueError(f'Missing required user-exported resources: {missing}')
        out = {name:profile(name, z.read(name)) for name in REQUIRED}
    return {
        'source_archive': path.name,
        'scripts': out,
        'safety': {
            'game_modified': False,
            'original_stock_bcs_included_in_output': False,
            'installation_tested': False,
            'stock_behavior_parity_proven': False,
            'notes': 'These are static structural facts, not a replay of the Infinity Engine.'
        }
    }


def verify_alias(stock: bytes, alias_bcs: bytes, alias_bs: bytes) -> None:
    """Future installer acceptance: EXACT compiled-stock resource equivalence."""
    if not (len(stock) > 100 and stock.startswith(b'SC\nCR\n')):
        raise AssertionError('Invalid stock resource')
    if not (stock == alias_bcs == alias_bs):
        raise AssertionError('BGXUN1 alias differs from installed BDDEFAI: FAIL CLOSED')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('zipfile', type=Path, help='User-owned EET resource export')
    parser.add_argument('--out', type=Path, default=None)
    args = parser.parse_args()
    report = inspect_zip(args.zipfile)
    content = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        args.out.write_text(content + '\n', encoding='utf-8')
    else:
        print(content)

if __name__ == '__main__':
    main()