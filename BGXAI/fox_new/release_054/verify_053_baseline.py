"""BGXAI 053: READ-ONLY local EET baseline audit for a *future* 052 bridge.

NO INSTALL, no gameplay edits, no deletes, no file/log writes. Designed for
safe manual invocation after a developer review, not needed by user yet.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path
from typing import Mapping

EXPECTED = {
    "override/BDDEFAI.BCS": "8602e8853a9c0e8b1bd5733021e6dd9c9ac73e03beb6c9900ef6ebd09dacb9a0",
    "override/M_BX43.lua": "a1c09d704bf66f054a2099c6496212573d56d185a550fb874fc1a35b1c739912",
    "override/M_BX44.lua": "a7bdfba10cdb3cc26351072dac0c6f375e03b4ce3a288f0eb15db945411dd33f",
}

# Any known mod *after* BGX49 is a stop, not a hint to uninstall it.
WEIDU_LINE = re.compile(r'^\s*~([^~]+\.tp2)~', re.I)

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(262144),b''):
            h.update(chunk)
    return h.hexdigest()

def inspect(game_root:Path, expected:Mapping[str,str]=EXPECTED)->dict:
    root=Path(game_root).expanduser().resolve()
    out={"schema":1,"gate":"BGXAI-053-READ-ONLY","game_root":str(root),
         "verdict":"REVIEW_DO_NOT_INSTALL","checked":{},"issues":[],"writes_performed":False}
    if not root.is_dir():
        out['issues'].append('game_directory_not_found')
        return out
    log=root/'WeiDU.log'
    if not log.is_file() or log.is_symlink():
        out['issues'].append('weidu_log_missing_or_link')
    else:
        try:
            lines=log.read_text(encoding='utf-8-sig',errors='replace').splitlines()
            mods=[m.group(1) for line in lines if (m:=WEIDU_LINE.match(line))]
            last=mods[-1] if mods else None
            out['checked']['weidu_last']=last
            if not last or not re.search(r'(?:^|[/\\])(?:setup-)?BGX49(?:[/\\]|\.tp2|$)',last,re.I):
                out['issues'].append('BGX49_not_last_WeiDU_component')
        except (OSError,UnicodeError):
            out['issues'].append('weidu_log_unreadable')
    for rel,wanted in expected.items():
        path=root.joinpath(*Path(rel).parts)
        if not path.is_file() or path.is_symlink():
            out['checked'][rel]='missing_or_link'
            out['issues'].append('missing_'+rel)
            continue
        try:
            got=sha256_file(path)
        except OSError:
            out['issues'].append('unreadable_'+rel)
            continue
        out['checked'][rel]={"sha256":got,"match":got.lower()==wanted.lower()}
        if got.lower()!=wanted.lower():
            out['issues'].append('hash_mismatch_'+rel)
    if not (root/'chitin.key').is_file():out['issues'].append('chitin_key_missing')
    out['verdict']='BASELINE_OK_SOURCE_ONLY' if not out['issues'] else 'REVIEW_DO_NOT_INSTALL'
    return out

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game',type=Path,default=Path(r'C:\Games\BG_EET_FOXX_NEW'))
    args=parser.parse_args()
    data=inspect(args.game)
    print(json.dumps(data,ensure_ascii=False,indent=2))
    return 0 if data['verdict']=='BASELINE_OK_SOURCE_ONLY' else 2
if __name__=='__main__':raise SystemExit(main())
