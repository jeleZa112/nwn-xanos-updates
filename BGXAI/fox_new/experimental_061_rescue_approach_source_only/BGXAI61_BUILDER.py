#!/usr/bin/env python3
"""Compile and replace only the fourteen BGX60 receiver BCS blocks (061 source-only).

Never installs into the user's game; builder writes only to an explicitly
selected destination OUTSIDE game. Real compiler uses user's WeiDU + IDS.
"""
from __future__ import annotations
import argparse, hashlib, json, re, shutil, subprocess, tempfile
from pathlib import Path

PIN_060_BCS='038b41c529fb45bb75528722577beef7b474e1ce55e280dc5fca4d6ed9e72841'
BLOCK_COUNT_060=1071
RECEIVER_START=1031  # zero-index, after EPS F mode toggle, before old bodyguards
RECEIVER_OLD=14
RECEIVER_NEW=20
START=re.compile(rb'(?:^|\n)(CR\nCO\n)')
ACTIONS=re.compile(rb'(?:^|\n)(?:\d+)?AC\n(-?\d+)OB\n')
OLD_ACTIONS=[[30,36],[30,36]]+[[30,115,30,30,134]]*6+[[30,115,30,30,87]]*6
NEW_ACTIONS=[[30,36],[30,36]]+[[30,115,30,30,134]]*6+[[115,115,30,30,22]]*6+[[30,115,30,30,87]]*6


def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()

def split(raw:bytes,count:int)->list[bytes]:
    if not raw.startswith(b'SC\n'):raise ValueError('BCS_HEADER_INVALID')
    starts=[m.start(1) for m in START.finditer(raw)]
    if len(starts)!=count or starts[0]!=3:raise ValueError(f'BLOCK_COUNT_{len(starts)}_EXPECTED_{count}')
    blocks=[raw[a:b] for a,b in zip(starts,starts[1:]+[len(raw)])]
    if any(not b.startswith(b'CR\nCO\n') or b.count(b'\nRS\n')<2 for b in blocks):
        raise ValueError('BLOCK_STRUCTURE_INVALID')
    if any(not b.endswith(b'CR\n') for b in blocks[:-1]):
        raise ValueError('NON_FINAL_BLOCK_TRAILER_INVALID')
    if not blocks[-1].endswith(b'CR\nSC\n') or raw.count(b'\nSC\n')!=1:
        raise ValueError('BCS_FINAL_FOOTER_INVALID')
    if b'SC\n'+b''.join(blocks)!=raw:raise ValueError('LOSSLESS_SPLIT_FAILURE')
    return blocks

def actions(block:bytes):return [int(n) for n in ACTIONS.findall(block)]

def verify_original(raw:bytes,pin:str=PIN_060_BCS)->list[bytes]:
    if sha(raw)!=pin:raise ValueError('LIVE_060_SHA_MISMATCH')
    blocks=split(raw,BLOCK_COUNT_060)
    old=blocks[RECEIVER_START:RECEIVER_START+RECEIVER_OLD]
    if [actions(b) for b in old]!=OLD_ACTIONS:raise ValueError('060_RECEIVER_ACTIONS_CHANGED')
    if any(b'BGX52_REQ_SLOT' not in b for b in old):raise ValueError('060_RECEIVER_NO_Q_MARKER')
    return blocks

def verify_compiled(raw:bytes)->list[bytes]:
    b=split(raw,RECEIVER_NEW)
    if [actions(block) for block in b]!=NEW_ACTIONS:raise ValueError('061_COMPILED_ACTIONS_CHANGED')
    if any(b'BGX52_REQ_SLOT' not in x for x in b):raise ValueError('061_COMPILED_NO_Q_MARKER')
    if any(b'BGX61_LAST_BRANCH' not in x for x in b[2:]):raise ValueError('060_TRACE_MARKER_MISSING')
    return b

def splice(old_raw:bytes,new_compiled:bytes,*,old_pin=PIN_060_BCS):
    old=verify_original(old_raw,pin=old_pin)
    compiled=verify_compiled(new_compiled)
    fragment=list(compiled)
    fragment[-1]=fragment[-1][:-3] # remove compiler SC footer: old original retains it
    if not fragment[-1].endswith(b'CR\n'):raise ValueError('061_FRAGMENT_LAST_INVALID')
    result=b'SC\n'+b''.join(old[:RECEIVER_START]+fragment+old[RECEIVER_START+RECEIVER_OLD:])
    updated=split(result,BLOCK_COUNT_060-RECEIVER_OLD+RECEIVER_NEW)
    if updated[:RECEIVER_START]!=old[:RECEIVER_START] or updated[RECEIVER_START+RECEIVER_NEW:]!=old[RECEIVER_START+RECEIVER_OLD:]:
        raise ValueError('EXISTING_EPS_BCS_CHANGED')
    if updated[RECEIVER_START:RECEIVER_START+RECEIVER_NEW]!=fragment:
        raise ValueError('061_INSERT_MISMATCH')
    return result,{'source_bcs_sha':sha(old_raw),'patched_bcs_sha':sha(result),
                   'old_blocks':len(old),'removed_060_blocks':RECEIVER_OLD,
                   'inserted_061_blocks':RECEIVER_NEW,'final_blocks':len(updated),
                   'eps_unchanged':True,'old_eps_guards_unchanged':True,
                   'existing_lua_056_unchanged':False}

def compile_fragment(game:Path,baf:Path):
    """Compiles using existing game WeiDU, IDS and TLK, but only into temp dir."""
    weidu=game/'setup-enhanced-powergaming-scripts.exe'
    tlk=game/'lang/ru_RU/dialog.tlk'
    if not all(p.is_file() for p in (weidu,tlk,game/'chitin.key',baf)):
        raise ValueError('REQUIRED_GAME_SOURCE_MISSING')
    with tempfile.TemporaryDirectory(prefix='BGXAI61_COMPILE_') as t:
        tmp=Path(t);exe=tmp/'weidu.exe';shutil.copy2(weidu,exe)
        if sha(exe.read_bytes())!=sha(weidu.read_bytes()):raise ValueError('WEIDU_COPY_MISMATCH')
        source=tmp/'BX61CHCK.baf';source.write_bytes(baf.read_bytes());out=tmp/'out';out.mkdir()
        cmd=[str(exe),'--no-auto-tp2','--no-exit-pause','--noautoupdate',
             '--game',str(game),'--tlkin',str(tlk),'--script-style','BG2',
             '--out',str(out),str(source)]
        p=subprocess.run(cmd,cwd=game,capture_output=True,text=True,errors='replace',timeout=30,check=False)
        txt=(p.stdout or '')+'\n'+(p.stderr or '')
        if p.returncode!=0 or re.search(r'(?im)^\s*(FATAL ERROR:|ERROR:)',txt):
            raise ValueError('WEIDU_COMPILE_FAILED:'+txt[-800:])
        candidates=list(out.rglob('BX61CHCK.bcs'))
        if len(candidates)!=1:raise ValueError('WEIDU_OUTPUT_MISSING_OR_AMBIGUOUS')
        raw=candidates[0].read_bytes();verify_compiled(raw);return raw

def main():
    parser=argparse.ArgumentParser(description='READ ONLY for EET: compile/verify source, no game writes')
    parser.add_argument('--game-root',type=Path,required=True)
    parser.add_argument('--source-baf',type=Path,default=Path(__file__).with_name('BGX61_RECEIVER.baf'))
    parser.add_argument('--preview-out',type=Path)
    args=parser.parse_args();root=args.game_root.resolve(strict=True)
    bcs=root/'override/BDDEFAI.BCS'
    old=bcs.read_bytes();verify_original(old)
    new=compile_fragment(root,args.source_baf.resolve(strict=True))
    result,report=splice(old,new)
    if args.preview_out:
        p=args.preview_out.absolute()
        if root==p or root in p.parents or p==bcs:raise ValueError('PREVIEW_INSIDE_GAME_BLOCKED')
        if p.exists():raise ValueError('PREVIEW_EXISTS_BLOCKED')
        p.write_bytes(result)
    print(json.dumps(report,indent=2,ensure_ascii=False))
    print('No changes to game, Lua, WeiDU.log or override.')
if __name__=='__main__':main()
