"""BGXAI 0.3.1: package a disabled shadow script for LATER ISOLATED testing.

This tool ONLY writes self-authored sources into BGXAI_LOCAL_BUILD/BGX31_STAGE.
It NEVER installs WeiDU, copies game BCS/EPS sources, or modifies the live game.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import sys

APPROVED_ROOT = Path(r'C:\Games\BG_EET_FOXX_NEW')
REL_LOCAL = 'BGXAI_LOCAL_BUILD'
REL_030 = 'BGXAI_030_COMPATIBILITY_REPORT.json'
STAGE_NAME = 'BGX31_STAGE_NOT_INSTALLED'

TP2 = '''// BGXAI 031 - compile prototype for ISOLATED EET TEST ONLY.
// DO NOT INSTALL THIS IN THE LIVE GAME. No EPS source distributed.
BACKUP ~BGX31/backup~
AUTHOR ~BGXAI private local experiment~
VERSION ~0.3.1-ISOLATED-ONLY~
BEGIN ~BGXAI 031 disabled EPS clone - isolated compilation test~
REQUIRE_PREDICATE GAME_IS ~eet~ ~This test requires EET~
REQUIRE_PREDICATE FILE_EXISTS_IN_GAME ~BDDEFAI.BCS~ ~Cannot find installed BDDEFAI~
COPY_EXISTING ~BDDEFAI.BCS~ ~override/BGX31.BCS~
EXTEND_BOTTOM ~BGX31.BCS~ ~BGX31/disabled_observer.baf~
COPY_EXISTING ~BGX31.BCS~ ~scripts/BGX31.BS~
'''

BAF = '''// BGXAI 031 - disabled by default. NO offensive actions or movement.
IF
  Global("BGX31_OBS","LOCALS",1)
  ActionListEmpty()
  GlobalTimerExpired("BGX31_NOTE","LOCALS")
THEN
  RESPONSE #100
    SetGlobalTimer("BGX31_NOTE","LOCALS",12)
    DisplayStringHead(Myself,~BGXAI 031: no party orders changed~)
    Continue()
END
'''

README = '''BGXAI 0.3.1 — ISOLATED-COMPILATION SOURCE PACKAGE ONLY

This is NOT an installed playable BGXAI and NOT a mod for the LIVE Foxx EET.
Do NOT run setup-BGX31.tp2 in C:\\Games\\BG_EET_FOXX_NEW.

User's game: C:\\Games\\BG_EET_FOXX_NEW, with working EPS 18.4.
Package contains ONLY independent BGXAI-written TP2/BAF. It does not copy
EPS, BDDEFAI.BCS, any game files, saved games, or copyrighted mod assets.

How it would work IN A SEPARATE ISOLATED COPY later:
  1. Read the currently installed BDDEFAI resource from the isolated game.
  2. Copy to BGX31.BCS (separate resource; original BDDEFAI unchanged).
  3. Append ONE diagnostic block, initially OFF (BGX31_OBS=0 by default).
  4. Copy new BGX31.BCS to scripts/BGX31.BS in that isolated installation.

No Attack, Spell, MoveToPoint, BattleSong, or RunAway from the new block.
Setting the diagnostic variable to 1 has NOT been tested. Do not do that.
WeiDU compile/install/uninstall in an ISOLATED EET and in-game parity are NOT
verified. The existing EPS script remains assigned to all live characters.

Next step: test copy isolation, real WeiDU compile, hash originals before/after,
then a reversible gameplay integration. Do NOT assume static tests prove runtime.
'''


def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()


def _is_path_in(parent: Path, child: Path) -> bool:
    try: return child.resolve().is_relative_to(parent.resolve())
    except (OSError, ValueError): return False


def build(root: Path, *, enforce_path=True) -> dict:
    root=Path(root).resolve()
    if enforce_path and os.path.normcase(str(root)).casefold()!=os.path.normcase(str(APPROVED_ROOT.resolve())).casefold():
        raise ValueError('Not the approved new Foxx path')
    if not (root/'chitin.key').is_file() or (root/'chitin.key').is_symlink():
        raise ValueError('Game marker missing or redirected')
    local=root/REL_LOCAL
    if not local.is_dir() or local.is_symlink() or not _is_path_in(root,local):
        raise ValueError('Missing/redirected local folder')
    reportfile=local/REL_030
    if reportfile.is_symlink() or not reportfile.is_file() or reportfile.stat().st_size>1000000:
        raise ValueError('Missing/redirected/oversized 030 preflight report')
    report=json.loads(reportfile.read_text(encoding='utf-8'))
    if report.get('schema')!=30 or report.get('mode')!='OFFLINE_READ_ONLY_PREFLIGHT' or \
       report.get('status')!='READY_FOR_ISOLATED_COMPILATION_REVIEW' or \
       report.get('source_files_checked')!=235 or report.get('changed_file_count')!=0 or \
       report.get('eps_weidu_components')!=3 or report.get('bddefai_override_state')!='SAME_AS_SNAPSHOT' or \
       report.get('blockers')!=[] or report.get('bgxai_installed') is not False or \
       report.get('game_modified') is not False or report.get('uploaded') is not False:
        raise ValueError('030 report not ready or not the confirmed local baseline')
    # The report is not fresh evidence by itself. Refuse a changed BCS.
    sid=report.get('snapshot_id')
    if not isinstance(sid,str) or not re.fullmatch(r'EPS_BASELINE_[A-Za-z0-9_-]{1,40}',sid):
        raise ValueError('Invalid baseline id')
    snap=local/sid
    meta_file=snap/'LOCAL_MANIFEST.json'
    if snap.is_symlink() or meta_file.is_symlink() or not meta_file.is_file() or meta_file.stat().st_size>4000000:
        raise ValueError('Local baseline metadata missing')
    metadata=json.loads(meta_file.read_text(encoding='utf-8'))
    bcs_metadata=metadata.get('binary_bcs_info') or {}
    bcs=root/'override'/'BDDEFAI.BCS'
    if bcs.is_symlink() or not bcs.is_file() or bcs_metadata.get('present_in_override') is not True or \
       not isinstance(bcs_metadata.get('sha256'),str) or sha256(bcs)!=bcs_metadata['sha256']:
        raise ValueError('The installed BDDEFAI changed after baseline; STOP')
    if len(metadata.get('source_files',[]))!=235 or metadata.get('weidu_eps_components')!=3:
        raise ValueError('EPS baseline count changed')
    eps=root/'enhanced-powergaming-scripts'
    if eps.is_symlink() or not (eps/'enhanced-powergaming-scripts.tp2').is_file():
        raise ValueError('EPS installation no longer present')
    stage=local/STAGE_NAME
    if stage.exists() or stage.is_symlink():
        raise ValueError('Stage already exists: refusing overwrite; preserve previous copy')
    stage.mkdir(parents=False,exist_ok=False)
    try:
        files={
          'setup-BGX31.tp2':TP2,
          'BGX31/disabled_observer.baf':BAF,
          'README_RU.txt':README
        }
        integrity={}
        for rel,content in files.items():
            dest=stage/rel
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes(content.encode('utf-8'))
            integrity[rel]={'bytes':dest.stat().st_size,'sha256':sha256(dest)}
        manifest={'schema':31,'status':'ISOLATED_COMPILATION_SOURCE_ONLY',
                  'source_status':'030_READY_235_FILES_3_COMPONENTS_BCS_IDENTICAL',
                  'stage':str(stage),'source_included':False,
                  'eps_files_included':False,'bcs_files_included':False,
                  'game_modified':False,'weiDU_executed':False,
                  'game_ai_replaced':False,'files':integrity}
        (stage/'BGX31_STAGE_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        return manifest
    except Exception:
        # Only remove an incomplete stage that this execution created.
        import shutil
        shutil.rmtree(stage,ignore_errors=True)
        raise


def main():
    try:
        result=build(APPROVED_ROOT)
        print('BGXAI 031: STAGED_ISOLATED_SOURCE_ONLY')
        print('Files staged:',len(result['files']))
        print('STAGE:',result['stage'])
        print('NO game files changed. NO WeiDU executed. EPS remains active.')
        return 0
    except (ValueError,OSError,TypeError,KeyError,json.JSONDecodeError) as e:
        print('BGXAI 031 ERROR:',e)
        return 1

if __name__=='__main__':sys.exit(main())