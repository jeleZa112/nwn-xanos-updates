#!/usr/bin/env python3
"""BGXPR-installed -> BGXP2 additive BCS fallback; fails closed on any drift."""
from __future__ import annotations
from pathlib import Path
import hashlib,re,shutil,subprocess,tempfile
BASE=Path(__file__).resolve().parent
BCS_PIN='75ffb7160f5a0dc61579f70236c0c6ac50b83974c31138094a799139188d7e13'
LUA_PIN='74ddc016e15fae3451bafe3039b299740c9d2efae8ecfb3e86badea257fa650c'
BASE_BLOCKS=1130
ADDED=28
START=re.compile(rb'(?:^|\n)(CR\nCO\n)')
ACT=re.compile(rb'(?:^|\n)(?:\d+)?AC\n(-?\d+)OB\n')
def sha(x:bytes):return hashlib.sha256(x).hexdigest()
def chunks(raw:bytes,expected:int)->list[bytes]:
    if not raw.startswith(b'SC\n') or not raw.endswith(b'CR\nSC\n'):
        raise ValueError('INVALID_BCS_CONTAINER')
    starts=[m.start(1) for m in START.finditer(raw)]
    if len(starts)!=expected or not starts or starts[0]!=3:
        raise ValueError(f'BCS_BLOCK_COUNT_MISMATCH:{len(starts)} expected {expected}')
    out=[raw[a:b] for a,b in zip(starts,starts[1:]+[len(raw)])]
    if any(not chunk.startswith(b'CR\nCO\n') or chunk.count(b'\nRS\n')<2 for chunk in out):
        raise ValueError('BCS_BLOCK_MALFORMED')
    if any(not chunk.endswith(b'CR\n') for chunk in out[:-1]):
        raise ValueError('BCS_BLOCK_TRAILER_MALFORMED')
    if b'SC\n'+b''.join(out)!=raw: raise ValueError('BCS_NOT_LOSSLESS')
    return out

def verify_fragment(raw:bytes)->list[bytes]:
    blocks=chunks(raw,ADDED)
    actions=[[int(i) for i in ACT.findall(b)] for b in blocks]
    expected=[[115,31]]*24+[[115,31],[115,105],[115,31],[115,105]]
    # 24 targeted support/auto casts, 2 enemy Command spells, 2 narrow autoattacks.
    if actions!=expected:raise ValueError('UNEXPECTED_FRAGMENT_ACTIONS:'+repr(actions))
    for b in blocks:
        for gate in [b'BGXR_ROLE',b'BGX38_GUARD',b'ActionListEmpty',b'BGX66_S_HEAL_SLOT']:
            # Trigger names might be encoded as numeric IDs; LOCALS string names remain.
            if gate.startswith(b'BGX') and gate not in b:raise ValueError('MISSING_GATE:'+gate.decode())
    return blocks

def splice(original:bytes,fragment:bytes)->tuple[bytes,dict]:
    if sha(original)!=BCS_PIN:raise ValueError('UNTRUSTED_LIVE_BCS_SHA')
    before=chunks(original,BASE_BLOCKS)
    new=verify_fragment(fragment)
    merged=original[:-3]+fragment[3:]
    after=chunks(merged,BASE_BLOCKS+ADDED)
    if after[:BASE_BLOCKS-1]!=before[:BASE_BLOCKS-1] or after[BASE_BLOCKS-1]+b'SC\n'!=before[-1]:
        raise ValueError('EXISTING_EPS_BGXPR_BLOCK_CHANGED')
    if after[BASE_BLOCKS:]!=new:raise ValueError('APPENDED_BLOCKS_CHANGED')
    return merged,{'old_sha256':sha(original),'new_sha256':sha(merged),'old_blocks_preserved':BASE_BLOCKS,'appended_blocks':ADDED,'total_blocks':len(after),'only_appended_to_end':True}

def compile_fragment(game:Path,weidu:Path,tlk:Path,baf:Path)->bytes:
    game=game.resolve(strict=True)
    if weidu.resolve(strict=True).parent!=game:raise ValueError('WEIDU_OUTSIDE_GAME')
    if game not in tlk.resolve(strict=True).parents:raise ValueError('TLK_OUTSIDE_GAME')
    with tempfile.TemporaryDirectory(prefix='BGXP2_NATIVE_IDS_READ_ONLY_') as td:
        d=Path(td);exe=d/'weidu.exe';shutil.copy2(weidu,exe)
        if sha(exe.read_bytes())!=sha(weidu.read_bytes()):raise ValueError('WEIDU_COPY_CHANGED')
        (d/'out').mkdir();(d/'BGXP2.baf').write_bytes(baf.read_bytes())
        cmd=[str(exe),'--no-auto-tp2','--no-exit-pause','--noautoupdate',
             '--game',str(game),'--tlkin',str(tlk),'--script-style','BG2','--out',str(d/'out'),str(d/'BGXP2.baf')]
        p=subprocess.run(cmd,cwd=d,stdin=subprocess.DEVNULL,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=90,check=False)
        log=(p.stdout or '')+'\n'+(p.stderr or '')
        if p.returncode or re.search(r'(?im)^\s*(?:FATAL ERROR:|ERROR:)',log):
            raise ValueError('GAME_IDS_BAF_COMPILE_FAILED:'+log[-2000:])
        files=[x for x in (d/'out').rglob('*') if x.is_file() and x.suffix.lower()=='.bcs' and x.stem.upper()=='BGXP2']
        if len(files)!=1:raise ValueError('OUTPUT_BCS_NOT_UNIQUE')
        result=files[0].read_bytes();verify_fragment(result);return result
