#!/usr/bin/env python3
"""Strict BCS 066S preservation + native BAF compiled fallback at the END of EPS script.
No game writes. A failed structural, action, or SHA check forbids installation.
"""
from __future__ import annotations
from pathlib import Path
import hashlib,re,shutil,subprocess,tempfile
BASE=Path(__file__).resolve().parent
BCS_PIN='fb435d82e6c3e0ebea1d6a9532753921bd5411d70ac0677dc1fd8ec483380476'
BCS_BLOCKS=1088
ADDED=42
START=re.compile(rb'(?:^|\n)(CR\nCO\n)')
ACT=re.compile(rb'(?:^|\n)(?:\d+)?AC\n(-?\d+)OB\n')
def sha(x):return hashlib.sha256(x).hexdigest()
def chunks(raw:bytes, expected:int)->list[bytes]:
    if not raw.startswith(b'SC\n') or not raw.endswith(b'CR\nSC\n'):
        raise ValueError('INVALID_BCS_CONTAINER')
    starts=[m.start(1) for m in START.finditer(raw)]
    if len(starts)!=expected or starts[0]!=3:
        raise ValueError('BCS_BLOCK_COUNT_MISMATCH:'+str(len(starts)))
    out=[raw[a:b] for a,b in zip(starts,starts[1:]+[len(raw)])]
    if any(not b.startswith(b'CR\nCO\n') or b.count(b'\nRS\n')<2 for b in out):
        raise ValueError('BCS_BLOCK_NOT_VALID')
    if any(not b.endswith(b'CR\n') for b in out[:-1]):
        raise ValueError('BCS_BLOCK_TRAILER_ERROR')
    if b'SC\n'+b''.join(out)!=raw: raise ValueError('BCS_NOT_LOSSLESS')
    return out

def verify_fragment(raw:bytes)->list[bytes]:
    b=chunks(raw,ADDED)
    actions=[[int(i) for i in ACT.findall(block)] for block in b]
    # Every new block has exactly a timer and either a real spell or a controlled approach.
    if any(a not in ([115,31],[115,22]) for a in actions):
        raise ValueError('FRAGMENT_ACTION_NOT_ALLOWED:'+str(actions))
    if sum(a==[115,31] for a in actions)!=24 or sum(a==[115,22] for a in actions)!=18:
        raise ValueError('FRAGMENT_SPELL_MOVE_ACTION_COUNTS_MISMATCH')
    for block in b:
        if b'BGXR_ROLE' not in block or b'BGX38_GUARD' not in block or b'BGXR_' not in block:
            raise ValueError('FRAGMENT_ROLE_F_GATE_MISSING')
    return b

def splice(original:bytes,compiled:bytes)->tuple[bytes,dict]:
    if sha(original)!=BCS_PIN: raise ValueError('UNTRUSTED_LIVE_BCS_SHA')
    before=chunks(original,BCS_BLOCKS)
    additions=verify_fragment(compiled)
    out=original[:-3]+compiled[3:]
    after=chunks(out,BCS_BLOCKS+ADDED)
    if after[:BCS_BLOCKS-1]!=before[:BCS_BLOCKS-1] or after[BCS_BLOCKS-1]+b'SC\n'!=before[-1]:
        raise ValueError('ANY_OLD_EPS_OR_066S_BLOCK_CHANGED')
    if after[BCS_BLOCKS:]!=additions:
        raise ValueError('APPENDED_BLOCK_MISMATCH')
    if out==original:raise ValueError('NO_CHANGE')
    return out,{'old_sha256':sha(original),'new_sha256':sha(out), 'old_blocks_preserved':BCS_BLOCKS,
       'appended_blocks':ADDED,'total_blocks':len(after),'only_appended_to_end':True}

def compile_fragment(game:Path,weidu:Path,tlk:Path,baf:Path)->bytes:
    game=game.resolve(strict=True)
    if weidu.resolve(strict=True).parent!=game:raise ValueError('WEIDU_NOT_FROM_GAME_ROOT')
    if game not in tlk.resolve(strict=True).parents:raise ValueError('TLK_NOT_FROM_GAME')
    with tempfile.TemporaryDirectory(prefix='BGXPR_REAL_IDS_READ_ONLY_') as t:
        tmp=Path(t);exe=tmp/'weidu.exe';shutil.copy2(weidu,exe)
        if sha(exe.read_bytes())!=sha(weidu.read_bytes()):raise ValueError('WEIDU_COPY_MISMATCH')
        (tmp/'out').mkdir()
        (tmp/'BGXPR.baf').write_bytes(baf.read_bytes())
        cmd=[str(exe),'--no-auto-tp2','--no-exit-pause','--noautoupdate',
             '--game',str(game),'--tlkin',str(tlk),'--script-style','BG2',
             '--out',str(tmp/'out'),str(tmp/'BGXPR.baf')]
        p=subprocess.run(cmd,cwd=tmp,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
           text=True,encoding='utf-8',errors='replace',timeout=90,check=False)
        lines=(p.stdout or '')+'\n'+(p.stderr or '')
        if p.returncode or re.search(r'(?im)^\s*(?:FATAL ERROR:|ERROR:)',lines):
            raise ValueError('GAME_IDS_BAF_COMPILATION_FAILED:'+lines[-1600:])
        found=[f for f in (tmp/'out').rglob('*') if f.is_file() and f.suffix.lower()=='.bcs' and f.stem.upper()=='BGXPR']
        if len(found)!=1:raise ValueError('BCS_COMPILE_OUTPUT_NOT_UNIQUE:'+repr([str(f) for f in found]))
        result=found[0].read_bytes()
        verify_fragment(result)
        return result
