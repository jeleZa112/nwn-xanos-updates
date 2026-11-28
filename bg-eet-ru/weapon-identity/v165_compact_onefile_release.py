# -*- coding: utf-8 -*-
"""Build-only, never an installer. Reversible zlib compaction of V68 literal.

Only from EXACT V164 SHA. Publishes no game changes. Output must pass
existing --selftest and contract tests on both Windows and Linux.
"""
from __future__ import annotations
import ast
import base64
import hashlib
import json
from pathlib import Path
import re
import zlib

ROOT=Path(__file__).resolve().parents[2]
CMD=ROOT/'bg-eet-ru/onefile/BG_EET_RU_UPDATE.cmd'
RELEASE=ROOT/'bg-eet-ru/onefile/release.json'
V165=ROOT/'bg-eet-ru/weapon-identity/V165_ONE_ITEM_DUAL_PILOT.py'
V164_SHA='80db1808d3748f03c10c090345c40afcd17881bacac80d68ad9d88f0e1f1f90e'
V165_SOURCE_SHA='d882c235ee4c2f57d02d5fc3afd614dead1bc918cbd45077a22bea3baf715dea'
V165_SOURCE_COMMIT='8864c9cbd711297e07ba95f0cf118c61a12f0fdb'


def sha(raw):return hashlib.sha256(raw).hexdigest()


def build():
    raw=CMD.read_bytes()
    rel=json.loads(RELEASE.read_text(encoding='utf-8'))
    if (sha(raw)!=V164_SHA or rel['version']!=164 or
            rel['sha256']!=V164_SHA):
        if rel['version']==165 and rel['sha256']==sha(raw) and (
            sha(V165.read_bytes())==V165_SOURCE_SHA and
            rel.get('v165_backend_sha256')==V165_SOURCE_SHA):
            print('V165_ALREADY_BUILT_PINNED')
            return
        raise RuntimeError('V165_V164_EXACT_BASELINE_HOLD')
    if sha(V165.read_bytes())!=V165_SOURCE_SHA:
        raise RuntimeError('V165_BACKEND_CHANGED_BEFORE_RELEASE')
    s=raw.decode('utf-8')
    lines=s.splitlines(keepends=True)
    locs=[i for i,l in enumerate(lines) if l.startswith('V68_COMBAT_SOURCE = "')]
    if len(locs)!=1:raise RuntimeError('UNCOMPRESSED_V68_SOURCE_ANCHOR_HOLD')
    i=locs[0]
    lhs,rhs=lines[i].rstrip('\n').split(' = ',1)
    old=ast.literal_eval(rhs)
    if type(old) is not str or len(old)<9000:
        raise RuntimeError('V68_DECOMPRESSION_BASELINE_HOLD')
    encoded=base64.b64encode(zlib.compress(old.encode('utf8'),9)).decode('ascii')
    new=f"V68_COMBAT_SOURCE = zlib.decompress(base64.b64decode('{encoded}')).decode('utf8')\n"
    if zlib.decompress(base64.b64decode(encoded)).decode('utf8')!=old:
        raise RuntimeError('V68_LOSSLESS_REPACK_HOLD')
    lines[i]=new
    s=''.join(lines)
    old_marker="V163_PIN='b24bb80860103f31688d54c9d906b44619e01bcf50be1beb645fe8aa215d7426'"
    if s.count(old_marker)!=1:raise RuntimeError('V163_FROZEN_BACKEND_MISSING')
    insert="""V165_PIN='d882c235ee4c2f57d02d5fc3afd614dead1bc918cbd45077a22bea3baf715dea'
V165_URL='https://raw.githubusercontent.com/jeleZa112/nwn-xanos-updates/8864c9cbd711297e07ba95f0cf118c61a12f0fdb/bg-eet-ru/weapon-identity/V165_ONE_ITEM_DUAL_PILOT.py'
def v165_dispatch(game,mode,offline=False):
 try:
  p=v121_cache(game)/'V165_DUAL_ONE_ITEM.py'
  if p.is_symlink():raise RuntimeError('V165_CACHE_SYMLINK')
  if not p.is_file() or sha_path(p)!=V165_PIN:
   if offline:raise RuntimeError('V165_OFFLINE_CACHE_HOLD')
   with urllib.request.urlopen(V165_URL,timeout=12) as r:data=r.read(30001)
   if digest(data)!=V165_PIN:raise RuntimeError('V165_DOWNLOAD_SHA_HOLD')
   v121_write(game,p,data)
  data=p.read_bytes()
  if digest(data)!=V165_PIN:raise RuntimeError('V165_PIN_CHANGED_BEFORE_EXEC')
  m=types.ModuleType('v165_dual');exec(compile(data,str(p),'exec'),m.__dict__)
  report=m.run_from_onefile(game,WORKDIR,mode,offline)
 except Exception as e:
  report={'status':'V165_SAFE_STOP','reason':type(e).__name__+': '+str(e)[:160],
          'gameFilesWritten':0 if mode in ('preflight','status') else 'UNKNOWN_AFTER_EXCEPTION'}
 try:v116_zip(game,WORKDIR/REPORT_NAME,report,entry='81_V165_DUAL_ONE_ITEM.json')
 except Exception as e:print('V165_ZIP_HOLD',str(e)[:120]);return 2
 print('V165:',report.get('status'),report.get('reason',''))
 return 0 if report.get('status') in ('V165_ONE_ITEM_PREFLIGHT_PASS','V165_NOT_INSTALLED',
        'V165_INSTALLED_AWAITING_GAMEPLAY','V165_ROLLED_BACK_TO_V163_123',
        'V165_ALREADY_AT_V163_BASELINE') else 2
"""
    anchor='def v133_audit(game,path,v136=False):'
    if s.count(anchor)!=1:raise RuntimeError('V165_DISPATCH_INSERT_ANCHOR_HOLD')
    s=s.replace(anchor,insert+anchor)
    menu="    if a=='13':"
    if s.count(menu)!=1:raise RuntimeError('V165_MENU_ANCHOR_HOLD')
    s=s.replace(menu,"""    if a=='14':
       try:b=input('V165 AROW01:1=status 2=check 3=install 4=undo [1]: ').strip()
       except EOFError:b=''
       return v165_dispatch(game,{'2':'preflight','3':'install','4':'rollback'}.get(b,'status'),args.offline)
"""+menu)
    oldprompt='11=bulk 12=names 13=next [1]'
    if s.count(oldprompt)!=1:raise RuntimeError('V165_MENU_TEXT_HOLD')
    s=s.replace(oldprompt,'11=bulk 12=names 13=next 14=dual [1]')
    if s.count('SELF_VERSION = 164')!=1:raise RuntimeError('V165_VERSION_ANCHOR_HOLD')
    s=s.replace('SELF_VERSION = 164','SELF_VERSION = 165')
    b=s.encode('utf8')
    if not 700000 < len(b) <= 750000:
        raise RuntimeError('V165_ONEFILE_LIMIT_HOLD:'+str(len(b)))
    if b.count(b'def v163_dispatch(')!=1 or b.count(b'def v165_dispatch(')!=1:
        raise RuntimeError('V165_DUPLICATE_OR_MISSING_DISPATCH')
    newsha=sha(b)
    # Write artifacts only when all checks pass. Published release contract
    # requires all Windows+Linux tests and exact release.json to match.
    CMD.write_bytes(b)
    rel.update(version=165,sha256=newsha,mode='V165_ONE_ITEM_AROW01_TYPED_DUAL_RU_PILOT',
               note=('One existing updater. V165 adds only menu 14 and immutable V165 '
                     'backend for AROW01 identified/unidentified Russian names using '
                     'existing V107 bit0 and V160 callback; exact V163 123-name '
                     'baseline, fresh both RU TLKs and ITM SHA, official EEex 1.2.0 '
                     'DLL SHA, external backup, typed install, last-only rollback. '
                     'Default game writes disabled. V68 historical embedded source '
                     'recompressed losslessly; unchanged bytes on decompression. '
                     'Publishing the installer is not user deployment or LIVE proof.'),
               v68_original_source_sha256=sha(old.encode('utf8')),
               v165_backend_sha256=V165_SOURCE_SHA)
    RELEASE.write_text(json.dumps(rel,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    # Historical regression contracts update ONLY the exact released version
    # and source length; never skip or relax the size/pin assertions.
    tests=[
      ROOT/'bg-eet-ru/hit-only-v160/test_v160_release_contract.py',
      ROOT/'bg-eet-ru/hit-only-v160/test_v162_onefile_release.py',
      ROOT/'bg-eet-ru/hit-only-v160/test_v163_cumulative_release_contract.py']
    for path in tests:
        data=path.read_text('utf8')
        for oldval,newval in (("release['version'], 164","release['version'], 165"),
                              ("release['version'],164","release['version'],165"),
                              ("manifest['version'],164","manifest['version'],165"),
                              ("len(blob), 749937",f"len(blob), {len(b)}"),
                              ("len(blob),749937",f"len(blob),{len(b)}"),
                              ("SELF_VERSION = 164","SELF_VERSION = 165")):
            data=data.replace(oldval,newval)
        path.write_text(data,encoding='utf8')
    print('V165_RELEASE_BUILD_PASS',len(b),newsha,'V68 source sha',rel['v68_original_source_sha256'])


if __name__=='__main__':build()
