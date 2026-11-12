#!/usr/bin/env python3
"""Proven 066S BCS -> 067 prehit BCS, preserving ALL installed legacy BCS blocks."""
from __future__ import annotations
from pathlib import Path
import hashlib,re,shutil,subprocess,tempfile
import BGXAI66S_BCS_PATCH as old

PIN_066S_BCS='fb435d82e6c3e0ebea1d6a9532753921bd5411d70ac0677dc1fd8ec483380476'
PIN_066S_BLOCKS=1088
PIN_FRAGMENT_BAF='84f40ae45efc25af6a94d88d0c28e77fc5d2b0fdda5fd92bad8bb3af603548cf'
PIN_FRAGMENT_BLOCKS=8
SPLICE_AT=old.SPLICE_AT+old.PIN_FRAGMENT_BLOCKS # after existing 20 guard and 11 heal/shield blocks
EXPECTED=[30,36]*2+[30,115,134]*6
sha=lambda x:hashlib.sha256(x).hexdigest()

def before(raw):
 if sha(raw)!=PIN_066S_BCS:raise ValueError('066S_LIVE_BCS_SHA_MISMATCH')
 parts=old.segment(raw,PIN_066S_BLOCKS)
 original=parts[old.OLD_RECEIVER_START:old.SPLICE_AT]
 if [old.actions(b) for b in original]!=old.EXISTING_061_ACTIONS:
  raise ValueError('066S_061_GUARD_RECEIVER_DRIFT')
 # 066S existing 11 blocks must be exactly its original 7 healing and cleanup actions.
 aid=[a for x in parts[old.SPLICE_AT:old.SPLICE_AT+11] for a in old.actions(x)]
 if aid!=[30,36]*4+[30,115,31]*7:raise ValueError('066S_HEAL_RECEIVER_DRIFT')
 return parts

def fragment(raw):
 parts=old.segment(raw,PIN_FRAGMENT_BLOCKS)
 actions=[n for b in parts for n in old.actions(b)]
 if actions!=EXPECTED:raise ValueError('067_PREHIT_ACTION_LAYOUT_DRIFT:'+str(actions))
 if any(b'BGX67_EARLY_SLOT' not in b for b in parts):
  raise ValueError('067_PREHIT_NO_REQUEST_MARKER')
 return parts

def splice(original,compiled):
 prev=before(original);ins=list(fragment(compiled))
 if not ins[-1].endswith(b'CR\nSC\n'):raise ValueError('067_FRAGMENT_FOOTER_MISSING')
 ins[-1]=ins[-1][:-3]
 merged=b'SC\n'+b''.join(prev[:SPLICE_AT]+ins+prev[SPLICE_AT:])
 total=old.segment(merged,PIN_066S_BLOCKS+PIN_FRAGMENT_BLOCKS)
 if total[:SPLICE_AT]!=prev[:SPLICE_AT] or total[SPLICE_AT+PIN_FRAGMENT_BLOCKS:]!=prev[SPLICE_AT:]:
  raise AssertionError('ORIGINAL_066S_BCS_BLOCK_DRIFT')
 if total[SPLICE_AT:SPLICE_AT+PIN_FRAGMENT_BLOCKS]!=ins:raise AssertionError('INSERTION_MISMATCH')
 return merged,dict(status='BCS_067_PATCH_VERIFIED',old_blocks=1088,new_blocks=8,total_blocks=1096,
  existing_bcs_byte_exact=True,insert_before_old_block=SPLICE_AT+1,source_sha256=sha(original),
  compiled_sha256=sha(compiled),final_sha256=sha(merged))

def verify_installed(candidate):
 parts=old.segment(candidate,PIN_066S_BLOCKS+PIN_FRAGMENT_BLOCKS)
 ins=list(parts[SPLICE_AT:SPLICE_AT+PIN_FRAGMENT_BLOCKS]);ins[-1]+=b'SC\n'
 fragment(b'SC\n'+b''.join(ins))
 restored=b'SC\n'+b''.join(parts[:SPLICE_AT]+parts[SPLICE_AT+PIN_FRAGMENT_BLOCKS:])
 before(restored)
 return dict(restored_bcs_sha256=sha(restored),old_blocks=PIN_066S_BLOCKS,new_blocks=PIN_FRAGMENT_BLOCKS)

def compile_real_game(game:Path,baf:Path,weidu:Path,tlk:Path,*,runner=subprocess.run):
 game=game.resolve(strict=True);baf=baf.resolve(strict=True)
 if sha(baf.read_bytes())!=PIN_FRAGMENT_BAF:raise ValueError('067_BAF_SHA_MISMATCH')
 if weidu.resolve(strict=True).parent!=game:raise ValueError('WEIDU_NOT_GAME_ROOT')
 if game not in tlk.resolve(strict=True).parents:raise ValueError('TLK_NOT_FROM_GAME')
 with tempfile.TemporaryDirectory(prefix='BGXAI67_READONLY_COMPILE_') as t:
  temp=Path(t);tool=temp/'weidu.exe';shutil.copy2(weidu,tool)
  if sha(tool.read_bytes())!=sha(weidu.read_bytes()):raise ValueError('WEIDU_TEMP_COPY_SHA_DRIFT')
  src=temp/'BX67CHCK.baf';src.write_bytes(baf.read_bytes());out=temp/'out';out.mkdir()
  cmd=[str(tool),'--no-auto-tp2','--no-exit-pause','--noautoupdate','--game',str(game),
       '--tlkin',str(tlk),'--script-style','BG2','--out',str(out),str(src)]
  proc=runner(cmd,cwd=str(temp),stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
       stderr=subprocess.PIPE,timeout=40,check=False,text=True,encoding='utf-8',errors='replace')
  msg=(proc.stdout or '')+'\n'+(proc.stderr or '')
  if proc.returncode!=0 or re.search(r'(?im)^\s*(?:FATAL ERROR:|ERROR:)',msg):
   raise ValueError('REAL_EET_IDS_WEIDU_COMPILE_FAILED:'+msg[-1500:])
  found=list(out.rglob('BX67CHCK.bcs'))
  if len(found)!=1:raise ValueError('REAL_IDS_COMPILE_OUTPUT_MISSING_OR_AMBIGUOUS')
  data=found[0].read_bytes();fragment(data);return data
