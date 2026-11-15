"""Release-integrity and optional read-only Windows EET baseline preflight.
No game modification, installation, activation or rollback is performed.
"""
from pathlib import Path
import argparse, hashlib, json, difflib
BASE=Path(__file__).resolve().parent
ORIGINAL='50640902ec4c25a2c85e5088d7231678b54445a847b41743c476974236d1d70f'
CANDIDATE='2bf43c6ce4d607c13ce1aaf5a6af34810e0d4e81e2272c7a37dce384b6413e1a'
BCS='fb435d82e6c3e0ebea1d6a9532753921bd5411d70ac0677dc1fd8ec483380476'

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def check():
    manifest=json.loads((BASE/'manifest_sha256.json').read_text(encoding='utf-8'))
    for name,expected in manifest['files'].items():
        p=BASE/name
        assert p.is_file() and digest(p)==expected, f'CORRUPT_FILE: {name}'
    assert digest(BASE/'M_BX43_066S_VERIFIED_ORIGINAL.lua')==ORIGINAL
    assert digest(BASE/'M_BX43_066S_IDLE_GUARD_CANDIDATE.lua')==CANDIDATE
    a=(BASE/'M_BX43_066S_VERIFIED_ORIGINAL.lua').read_text(encoding='utf-8')
    b=(BASE/'M_BX43_066S_IDLE_GUARD_CANDIDATE.lua').read_text(encoding='utf-8')
    generated=''.join(difflib.unified_diff(a.splitlines(keepends=True),b.splitlines(keepends=True),fromfile='066S_live_exact',tofile='066S_idle_guard_candidate'))
    assert generated==(BASE/'066S_idle_guard_minimal.diff').read_text(encoding='utf-8'), 'DIFF_MISMATCH'
    hunks=[x for x in difflib.SequenceMatcher(a=a.splitlines(),b=b.splitlines()).get_opcodes() if x[0]!='equal']
    assert len(hunks)==2, f'NOT_MINIMAL_DIFF {hunks}'
    assert a.count('EEex_Sprite_AddBlockWeaponHitListener, P.onWeaponHit')==b.count('EEex_Sprite_AddBlockWeaponHitListener, P.onWeaponHit')==1
    assert a.count('EEex_Action_AddSpriteStartedActionListener, P.onStarted')==b.count('EEex_Action_AddSpriteStartedActionListener, P.onStarted')==1
    assert a.count('function S.onHit(hit)')==b.count('function S.onHit(hit)')==1
    assert a.count('function P.onWeaponHit(context)')==b.count('function P.onWeaponHit(context)')==1
    for forbidden in ('ClearActions(', 'ActionOverride(', 'Attack(', 'Spell('):
        assert b.count(forbidden)==a.count(forbidden), 'NEW_ENGINE_ACTION: '+forbidden
    print(f'RELEASE_VERIFIED {len(manifest["files"])} SHA256, EXACT_TWO_REGION_DIFF, ALL_HOOKS_IDENTICAL, NO_NEW_ENGINE_ACTIONS')

def live_readonly(root):
    lua=Path(root)/'override'/'M_BX43.lua'
    bcs=Path(root)/'override'/'BDDEFAI.BCS'
    for p,expected in ((lua,ORIGINAL),(bcs,BCS)):
        assert p.is_file(),f'NOT_FOUND: {p}'
        actual=digest(p)
        assert actual==expected,f'BASELINE_MISMATCH: {p.name} expected={expected} actual={actual}'
    print('LIVE_BASELINE_PINNED_READ_ONLY: 066S Lua+BCS exact; NO_WRITE')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--game-root',help='Optional Windows root: read-only SHA preflight, never modifies game')
    args=p.parse_args()
    check()
    if args.game_root: live_readonly(args.game_root)
