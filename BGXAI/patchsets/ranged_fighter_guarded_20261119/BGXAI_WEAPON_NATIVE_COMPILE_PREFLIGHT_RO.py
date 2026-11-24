#!/usr/bin/env python3
"""BGXAI weapon V3: isolated, READ-ONLY compilation against actual installed EET.

Source-only. Does not install, modify IDS/BCS/WeiDU.log, or authorize dispatch.
Derived from release_054's proven temporary WeiDU pattern, not from an EPS script.
Only intended for eventual integration into the *existing* BGXAI_UPDATE.cmd.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tempfile

SOURCE_NAME = 'BGXAI_WEAPON_SLOT_CONSUMER_V3.baf'
SOURCE_SHA256 = '7d8c615894b21674be7624d6d1a61b0b42ad92f116e8cd5f9f5db1b7f7a52911'
TEMP_SOURCE_NAME = 'BGXW3CHK.baf' # <= 8-character Infinity Engine resource name
TIMEOUT_SECONDS = 25
WATCH = ('chitin.key', 'WeiDU.log', 'weidu.conf', 'override/DPLAYER.BCS',
         'override/WTASIGHT.BCS', 'override/PRIEST1.BCS',
         'override/M_BGXR27.lua')

class Hold(ValueError):
    pass

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def unsafe_link(p: Path) -> bool:
    if p.is_symlink():
        return True
    try:
        return bool(p.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)
    except (AttributeError, FileNotFoundError):
        return False

def checked_file(p: Path, required=False) -> bytes | None:
    if unsafe_link(p) or any(unsafe_link(parent) for parent in p.parents if parent.exists()):
        raise Hold('SYMLINK_OR_REPARSE_DENIED')
    if not p.exists():
        if required: raise Hold('REQUIRED_FILE_MISSING:'+p.name)
        return None
    if not p.is_file():
        raise Hold('NOT_REGULAR_FILE:'+p.name)
    return p.read_bytes()

def source_check(source: Path, game: Path) -> dict:
    raw = checked_file(source, required=True)
    if digest(raw) != SOURCE_SHA256:
        raise Hold('BAF_SOURCE_SHA256_MISMATCH')
    # The single-updater may stage a SHA-pinned source in BGXAI_DEV, but never
    # allow arbitrary staged scripts under override or an installed mod folder.
    src=source.resolve(strict=True)
    if src==game or game in src.parents:
        allowed=(game/'BGXAI_DEV'/'weapon_priority_v3'/SOURCE_NAME).resolve()
        if src!=allowed:
            raise Hold('SOURCE_INSIDE_GAME_NOT_PINNED_STAGING_PATH')
    text=raw.decode('utf-8')
    if text.count('SelectWeaponAbility(')!=8 or text.count('!WeaponCanDamage(NearestEnemyOf(Myself),MAINHAND)')!=4:
        raise Hold('BAF_NATIVE_GUARD_SOURCE_DRIFT')
    if len(re.findall(r'(?m)^IF\s*$',text))!=8:
        raise Hold('BAF_BLOCK_COUNT_DRIFT')
    return {'sha256':digest(raw),'size':len(raw),'blocks':8,'actionCount':8}

def selected_tlk(game: Path) -> Path:
    conf=checked_file(game/'weidu.conf')
    chosen=None
    if conf is not None:
        for line in conf.decode('utf-8-sig',errors='replace').splitlines():
            m=re.fullmatch(r'\s*lang_dir\s*=\s*([A-Za-z0-9_-]+)\s*',line,re.I)
            if m:
                if chosen is not None: raise Hold('AMBIGUOUS_LANG_DIR')
                chosen=m.group(1).casefold()
    folder=game/'lang'
    candidates={}
    if folder.is_dir() and not unsafe_link(folder):
        for d in folder.iterdir():
            if d.is_dir() and not unsafe_link(d):
                tlk=d/'dialog.tlk'
                if tlk.is_file() and not unsafe_link(tlk):
                    candidates.setdefault(d.name.casefold(),[]).append(tlk)
    if chosen:
        possible=candidates.get(chosen,[])
        if len(possible)!=1:raise Hold('CONFIGURED_DIALOG_TLK_MISSING_OR_AMBIGUOUS')
        return possible[0]
    if len(candidates.get('ru_ru',[]))==1:
        return candidates['ru_ru'][0]
    all_tlks=[v[0] for v in candidates.values() if len(v)==1]
    if len(candidates)==1 and len(all_tlks)==1:
        return all_tlks[0]
    root_tlk=game/'dialog.tlk'
    if not candidates and checked_file(root_tlk) is not None:
        return root_tlk
    raise Hold('DIALOG_TLK_NOT_UNIQUELY_RESOLVED')

def baseline(game: Path, tlk: Path) -> dict:
    items={}
    for relative in WATCH:
        raw=checked_file(game/relative, required=relative in ('chitin.key','WeiDU.log'))
        items[relative.lower()]=digest(raw) if raw is not None else None
    for p in (tlk,tlk.with_name('dialogf.tlk')):
        raw=checked_file(p,required=p==tlk)
        items[str(p.relative_to(game)).replace('\\','/').lower()]=digest(raw) if raw is not None else None
    return items

def compile_readonly(game: Path, source: Path, weidu: Path, run=subprocess.run) -> dict:
    # A preflight compiles *only* in TEMP; any live file write is a safety failure.
    if unsafe_link(game) or not game.is_dir():raise Hold('INVALID_GAME_DIRECTORY')
    game=game.resolve(strict=True)
    source=Path(source)
    weidu=Path(weidu)
    src=source_check(source,game)
    if unsafe_link(weidu) or not weidu.is_file():raise Hold('WEIDU_MISSING_OR_LINK')
    if weidu.resolve(strict=True).parent!=game:
        raise Hold('WEIDU_EXECUTABLE_OUTSIDE_GAME_ROOT')
    compiler_bytes=checked_file(weidu,required=True)
    if not compiler_bytes or len(compiler_bytes)<16:
        raise Hold('WEIDU_EXECUTABLE_INVALID')
    compiler_sha=digest(compiler_bytes)
    tlk=selected_tlk(game)
    before=baseline(game,tlk)
    result={'schema':'BGXAI_WEAPON_NATIVE_COMPILE_RO_V1',
            'status':'NOT_STARTED','source':src,'compilerSha256':compiler_sha,
            'nativeSymbolsAcceptedByCompiler':False,'engineBehaviorVerified':False,
            'wholeGameTreeChecked':False,'watchedFilesChanged':None,
            'gameplayLiveVerified':False,'installPerformed':False,
            'ordersSent':0,'dispatchAuthorized':False,'weaponSwitchAuthorized':False}
    with tempfile.TemporaryDirectory(prefix='BGXAI_WEAPON_NATIVE_RO_') as directory:
        temp=Path(directory).resolve(strict=True)
        if temp==game or game in temp.parents:raise Hold('UNSAFE_TEMP_INSIDE_GAME')
        output=temp/'out';output.mkdir()
        copy=temp/'weidu.exe'
        # Preserve executable permissions on Linux instead of writing a 0644 file.
        # On Windows this remains an ordinary copied .exe, not setup-*.exe.
        shutil.copy2(weidu,copy)
        if digest(copy.read_bytes())!=compiler_sha:raise Hold('TEMP_COMPILER_COPY_SHA_DRIFT')
        baf=temp/TEMP_SOURCE_NAME
        baf.write_bytes(checked_file(source,required=True))
        logfile=temp/'weidu.debug'
        cmd=[str(copy),'--noautoupdate','--no-auto-tp2','--no-exit-pause',
             '--game',str(game),'--tlkin',str(tlk),'--log',str(logfile),
             '--script-style','BG2','--out',str(output),str(baf)]
        try:
            proc=run(cmd,cwd=str(game),stdin=subprocess.DEVNULL,capture_output=True,
                     text=True,encoding='utf-8',errors='replace',timeout=TIMEOUT_SECONDS,check=False)
            log=((proc.stdout or '')+'\n'+(proc.stderr or ''))[-3000:]
            result['exitCode']=proc.returncode
            result['compilerOutputTail']=log[-900:]
            bad=bool(re.search(r'(?im)(?:^|\s)(?:FATAL\s+ERROR|ERROR:|WARNING:|UNRESOLVED\b|UNKNOWN\s+TRIGGER|UNKNOWN\s+ACTION)',log))
            compiled=list(output.rglob('*.bcs'))+list(output.rglob('*.BCS'))
            expected=[p for p in set(compiled) if p.stem.casefold()==baf.stem.casefold()]
            if proc.returncode==0 and not bad and len(expected)==1:
                compiled_bytes=checked_file(expected[0],required=True)
                if len(compiled_bytes)>=16 and compiled_bytes[:3]==b'SC\n':
                    result.update(status='NATIVE_WEIDU_COMPILED_TEMP_ONLY',
                                  compiledSha256=digest(compiled_bytes),
                                  compiledSize=len(compiled_bytes),nativeSymbolsAcceptedByCompiler=True)
                else:
                    result['status']='BCS_OUTPUT_INVALID'
            else:
                result['status']='WEIDU_COMPILE_FAILED_OR_UNRESOLVED_IDS'
        except subprocess.TimeoutExpired:
            result['status']='WEIDU_TIMEOUT'
        except OSError as e:
            result['status']='WEIDU_PROCESS_FAILURE'
            result['exceptionType']=type(e).__name__
        finally:
            after=baseline(game,tlk)
            result['watchedFilesChanged']=after!=before
            if result['watchedFilesChanged']:
                result['status']='REVIEW_WATCHED_LIVE_FILES_CHANGED'
                result['nativeSymbolsAcceptedByCompiler']=False
    result['temporaryOutputRemoved']=True
    return result

def main(argv=None) -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--game',type=Path,default=Path(r'C:\Games\BG_EET_FOXX_NEW'))
    ap.add_argument('--source',type=Path,default=Path(__file__).with_name(SOURCE_NAME))
    ap.add_argument('--weidu',type=Path)
    args=ap.parse_args(argv)
    exe=args.weidu or (args.game/'weidu.exe' if (args.game/'weidu.exe').is_file() else args.game/'setup-enhanced-powergaming-scripts.exe')
    try:
        report=compile_readonly(args.game,args.source,exe)
    except (Hold,ValueError,OSError,UnicodeError) as e:
        report={'schema':'BGXAI_WEAPON_NATIVE_COMPILE_RO_V1','status':'BLOCKED_BEFORE_COMPILER',
                'reason':str(e),'installPerformed':False,'ordersSent':0,
                'dispatchAuthorized':False,'weaponSwitchAuthorized':False}
    print(json.dumps(report,indent=2,ensure_ascii=False))
    return 0 if report['status']=='NATIVE_WEIDU_COMPILED_TEMP_ONLY' and report['watchedFilesChanged'] is False else 3

if __name__=='__main__':
    raise SystemExit(main())