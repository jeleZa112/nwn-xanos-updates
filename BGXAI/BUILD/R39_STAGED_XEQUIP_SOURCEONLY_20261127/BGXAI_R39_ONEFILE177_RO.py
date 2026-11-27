#!/usr/bin/env python3
"""Onefile menu 177 *read-only* exact R39 native preflight, not an installer.

Invoked only by the existing signed BGXAI_SYNC.ps1 from BGXAI_UPDATE.cmd.
Stages SHA-pinned source snapshots in an OUTSIDE-GAME temporary directory.
Never writes an EET override, actor LOCALS, BCS, GAM, or WeiDU component.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import urllib.request

REPO='jeleZa112/nwn-xanos-updates'
ROOT=Path(r'C:\Games\BG_EET_FOXX_NEW')
SCHEMA='BGXAI_R39_ONEFILE177_NATIVE_RO_V1'
P='BGXAI/BUILD/R39_STAGED_XEQUIP_SOURCEONLY_20261127/'
A=P+'BGXAI_R39_NATIVE_EET_COMPILE_RO_V1.py'
B=P+'BGXAI_R39_JAGAN_STAF01_SOURCE_ONLY.baf'
V='BGXAI/BUILD/WEAPON_XEQUIP_V3_NATIVE_RO_20261127/BGXAI_XEQUIP_V3_NATIVE_COMPILE_RO.py'
C='BGXAI/patchsets/ranged_fighter_guarded_20261119/BGXAI_WEAPON_NATIVE_COMPILE_PREFLIGHT_RO.py'
# Immutable specific bytes, not source branch HEAD, CI, or a filename assertion.
SOURCES={
 A:(10139,'1d5ea227f27021fbb11b503329f713b58749f4d02d25cbdd95cb77758d3748ba'),
 B:(2303,'3b84d38a9df069e3dedfdaf8de6cbf6958a7252d43490fa64b829375cf7cd03d'),
 V:(10743,'b4a0789c568879a179e21cf50391afd999861e85f832f587aceb07cf816e055e'),
 C:(9551,'27285b3d067eab2c67b075dc8654b9a0f74da0d7920b2e96339ced3e14bcd10a'),
}
class Hold(ValueError): pass

def digest(raw:bytes):return hashlib.sha256(raw).hexdigest()

def check_pin(commit:str):
    if type(commit) is not str or re.fullmatch(r'[0-9a-f]{40}',commit) is None:
        raise Hold('HOLD_IMMUTABLE_PIN_REQUIRED')
    return commit

def verify(path:str, raw:bytes):
    if path not in SOURCES or type(raw) is not bytes:
        raise Hold('HOLD_UNTRUSTED_SOURCE')
    size,sha=SOURCES[path]
    if len(raw)!=size or digest(raw)!=sha:
        raise Hold('HOLD_SOURCE_SHA_DRIFT:'+path.rsplit('/',1)[-1])
    return raw

def fetch(commit:str, path:str, opener=urllib.request.urlopen):
    check_pin(commit)
    if path not in SOURCES:raise Hold('HOLD_UNALLOWLISTED_PATH')
    errors=[]
    for base in (
        'https://raw.githubusercontent.com/'+REPO+'/'+commit+'/',
        'https://cdn.jsdelivr.net/gh/'+REPO+'@'+commit+'/',
        'https://fastly.jsdelivr.net/gh/'+REPO+'@'+commit+'/',
    ):
        try:
            request=urllib.request.Request(base+path,headers={'User-Agent':'BGXAI-Onefile177-SHA'})
            with opener(request,timeout=25) as fd:
                data=fd.read(SOURCES[path][0]+1)
            return verify(path,data)
        except (OSError,ValueError,TypeError) as error:
            errors.append(type(error).__name__)
    raise Hold('HOLD_VERIFIED_SOURCE_UNAVAILABLE:'+','.join(errors))

def protected_game(root:Path):
    if os.name!='nt' or os.path.normcase(os.path.abspath(root))!=os.path.normcase(os.path.abspath(ROOT)):
        raise Hold('HOLD_EXACT_WINDOWS_GAME_REQUIRED')
    if not root.is_dir() or root.is_symlink():
        raise Hold('HOLD_GAME_DIRECTORY_UNTRUSTED')

def run(game:Path,commit:str,fetcher=fetch,runner=subprocess.run,require_windows=True):
    check_pin(commit)
    if require_windows:protected_game(game)
    with tempfile.TemporaryDirectory(prefix='BGXAI_R39_177_NATIVE_TEMP_') as work:
        temp=Path(work).resolve(strict=True)
        realgame=game.resolve(strict=False)
        if temp==realgame or realgame in temp.parents or temp in realgame.parents:
            raise Hold('HOLD_TEMP_OVERLAPS_GAME')
        for path in SOURCES:
            raw=verify(path,fetcher(commit,path))
            target=temp.joinpath(*path.split('/'))
            if target.is_symlink() or temp not in target.parents:
                raise Hold('HOLD_STAGE_OUTSIDE_TEMP')
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(raw)
            if digest(target.read_bytes())!=SOURCES[path][1]:
                raise Hold('HOLD_STAGED_BYTES_CHANGED')
        cmd=[sys.executable,str(temp.joinpath(*A.split('/'))),
             '--native-readonly','--game',str(game),
             '--source',str(temp.joinpath(*B.split('/'))),
             '--v3-helper',str(temp.joinpath(*V.split('/'))),
             '--backend',str(temp.joinpath(*C.split('/')))]
        call=runner(cmd,cwd=str(temp),stdin=subprocess.DEVNULL,
                    capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=150,check=False)
        try:inner=json.loads(call.stdout)
        except (ValueError,TypeError):raise Hold('HOLD_R39_NATIVE_JSON_INVALID')
        safe=(call.returncode==0 and type(inner) is dict and
              inner.get('status')=='R39_NATIVE_EET_TEMP_COMPILE_PASS_NO_INSTALL' and
              inner.get('nativeWeiDUCompileVerified') is True and
              inner.get('sourceSha256')==SOURCES[B][1] and
              inner.get('sourceBytes')==SOURCES[B][0] and
              inner.get('watchedFilesChanged') is False and
              inner.get('temporaryOutputRemoved') is True and
              inner.get('installed') is False and
              inner.get('dispatchAuthorized') is False and
              inner.get('armAuthorized') is False and
              inner.get('ordersSent')==0 and
              type(inner.get('itemHeaderCheck')) is dict and
              inner['itemHeaderCheck'].get('staticItemClassKitHeaderAllowed') is True and
              inner['itemHeaderCheck'].get('engineCanEquipVerified') is False)
        return {'schema':SCHEMA,'status':'R39_EXACT_NATIVE_AND_ITEM_HEADER_PASS_NO_INSTALL' if safe else
                       'HOLD_R39_NATIVE_OR_STATIC_ITEM_USABILITY',
                'nativeWeiDUCompileVerified':bool(safe),
                'itemStaticHeaderVerified':bool(safe),
                'engineCanEquipVerified':False,
                'manualEpsActionOriginVerified':False,
                'runtimeSessionArmVerified':False,
                'realGameplayTransferVerified':False,
                'gameModified':False,'installed':False,'ordersSent':0,
                'dispatchAuthorized':False,'armAuthorized':False,
                'sourcePinCommit':commit,'bafSha256':SOURCES[B][1],
                'innerReport':inner}

def report(data):
    if os.name!='nt':return data
    home=Path(os.environ.get('USERPROFILE',''))
    if not os.environ.get('USERPROFILE'):return data
    folder=home/'Documents'/'BGXAI_LIVE_REPORTS'
    if folder.is_symlink() or (hasattr(folder,'is_junction') and folder.is_junction()):
        raise Hold('HOLD_REPORT_DIR_REPARSE')
    folder.mkdir(parents=True,exist_ok=True)
    file=folder/('BGXAI_R39_NATIVE177_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json')
    with file.open('x',encoding='utf-8') as fd:
        json.dump(data,fd,ensure_ascii=False,indent=2);fd.write('\n')
    return {**data,'reportFile':str(file)}

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game',type=Path,default=ROOT)
    parser.add_argument('--commit',required=True)
    args=parser.parse_args(argv)
    try:
        result=run(args.game,args.commit)
    except (Hold,OSError,ValueError,TypeError,subprocess.TimeoutExpired) as error:
        result={'schema':SCHEMA,'status':'HOLD_R39_ONEFILE177',
                'reason':str(error) if isinstance(error,Hold) else 'HOLD_RUNTIME_OR_IO',
                'gameModified':False,'installed':False,'ordersSent':0,
                'dispatchAuthorized':False,'armAuthorized':False}
    try:result=report(result)
    except (Hold,OSError):pass
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['status']=='R39_EXACT_NATIVE_AND_ITEM_HEADER_PASS_NO_INSTALL' else 3

if __name__=='__main__':raise SystemExit(main())
