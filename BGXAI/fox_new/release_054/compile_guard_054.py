"""BGXAI 054 SOURCE ONLY: compile BAF against actual game IDS via WeiDU,
with no TP2 install and no intended writes to the EET tree.

The game must be closed. Executable comes from installed EET and is invoked
with a temporary output directory, not a mod installer. If anything in the
watched live baseline changes, fail and leave evidence; do NOT auto-restore.
"""
from __future__ import annotations
import argparse, hashlib,json,os,re,subprocess,sys,tempfile
from pathlib import Path
import verify_053_baseline as preflight

NAME='BGX52_guard_receiver_PREVIEW.baf'
COMPILE_NAME='BX52CHK.baf' # 8-character WeiDU/Infinity Engine resref; temporary only
BAF_SHA='10c625ecb516e676d5ea264665f186d5f2a16a6809f88e569a7023b65d2e414c'
DANGEROUS={'ClearActions','ActionOverride','Attack','AttackReevaluate',
           'Spell','ForceSpell','ReallyForceSpell','StartCutSceneMode',
           'SetGlobal','ChangeAIScript'}
# SetGlobal only in reset/cooldown blocks of trusted baseline, so exact BAF SHA gate
# prevents arbitrary modifications; the set is informational, not a full parser.
MAX_COMPILER_SECONDS=90

def digest(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*256),b''):h.update(chunk)
    return h.hexdigest()

def live_paths(game:Path)->list[Path]:
    base=['WeiDU.log','chitin.key','override/BDDEFAI.BCS','override/M_BX43.lua',
          'override/M_BX44.lua','weidu.conf','lang/ru_ru/dialog.tlk','lang/ru_ru/dialogf.tlk']
    return [game/x for x in base]

def snapshot(game:Path)->dict:
    return {str(p.relative_to(game)).lower():
            (digest(p) if p.is_file() and not p.is_symlink() else None)
            for p in live_paths(game)}

def validate_baf(file:Path)->dict:
    if not file.is_file() or file.is_symlink():raise ValueError('BAF missing/link')
    if digest(file)!=BAF_SHA:raise ValueError('BAF_SHA_MISMATCH')
    data=file.read_text(encoding='ascii')
    blocks=re.findall(r'(?ms)^IF\s*\n(.*?)\nTHEN\s*\n(.*?)\nEND\s*$',data)
    if len(blocks)!=8:raise ValueError('EXPECTED_EIGHT_BAF_BLOCKS')
    protected=[]
    for i,(triggers,actions) in enumerate(blocks):
        real=[x.strip() for x in actions.splitlines() if x.strip()]
        if len(real)<2 or real[0]!='RESPONSE #100':raise ValueError('bad response')
        if i<2:
            if not any('SetGlobal("BGX52_REQ_SLOT","LOCALS",0)'==x for x in real):
                raise ValueError('cleanup missing')
            if real[-1]!='Continue()':raise ValueError('cleanup missing Continue')
            if 'ProtectObject(' in actions:raise ValueError('protect in cleanup')
        else:
            slot=i-1
            required=[f'Global("BGX52_REQ_SLOT","LOCALS",{slot})',
                      'Global("BGX38_GUARD","LOCALS",1)',
                      'GlobalTimerNotExpired("BGX52_EXPIRE","LOCALS")',
                      '!GlobalTimerNotExpired("BGX52_COOLDOWN","LOCALS")',
                      'ActionListEmpty()','ModalState(NONE)',
                      'InParty(Myself)',f'InParty(Player{slot})',
                      f'See(Player{slot})',f'Range(Player{slot},10)',
                      f'See(NearestEnemyOf(Player{slot}))',
                      f'Range(NearestEnemyOf(Player{slot}),7)']
            if any(line not in triggers for line in required):raise ValueError('missing guard for slot '+str(slot))
            if real[1:] != [
                    'SetGlobal("BGX52_REQ_SLOT","LOCALS",0)',
                    'SetGlobalTimer("BGX52_COOLDOWN","LOCALS",8)',
                    f'ProtectObject(Player{slot},6)']:
                raise ValueError('unexpected actions in slot '+str(slot))
            protected.append(slot)
    return {'blocks':len(blocks),'protect_slots':protected,'source_sha256':digest(file)}

def prepare(game:Path, source:Path, exe:Path)->tuple[dict,dict,dict]:
    # Fail closed before any subprocess. No source may be taken from game directory.
    game=game.expanduser().resolve(strict=True)
    source=source.expanduser().resolve(strict=True)
    exe=exe.expanduser().resolve(strict=True)
    if not game.is_dir() or not (game/'chitin.key').is_file():raise ValueError('NOT_AN_EET_GAME')
    if game == source.parent or game in source.parents:
        # The verified one-file updater stores SOURCE ONLY under BGXAI_DEV,
        # inside the game directory. Allow precisely that hashed source path;
        # never compile a BAF taken from override, mods or other game folders.
        allowed=(game/'BGXAI_DEV'/'experimental_054'/NAME).resolve()
        if source!=allowed:raise ValueError('SOURCE_IN_LIVE_GAME_UNAPPROVED')
    if not exe.is_file():raise ValueError('WEIDU_EXECUTABLE_MISSING')
    if (exe.parent != game):raise ValueError('WEIDU_MUST_BE_IN_GAME_ROOT')
    source_info=validate_baf(source)
    pre=preflight.inspect(game)
    if pre['verdict']!='BASELINE_OK_SOURCE_ONLY':raise ValueError('BASELINE_GATE_BLOCKED: '+','.join(pre['issues']))
    before=snapshot(game)
    if not before.get('weidu.log') or not before.get('lang/ru_ru/dialog.tlk'):
        raise ValueError('REQUIRED_LOG_OR_TLK_MISSING')
    return pre,source_info,before

def compile_readonly(game:Path,source:Path,exe:Path,runner=subprocess.run)->dict:
    pre,src,before=prepare(game,source,exe)
    game=game.resolve(); source=source.resolve(); exe=exe.resolve()
    report={'schema':1,'tool':'BGXAI-054-ISOLATED-BAF-COMPILE',
            'status':'NOT_STARTED','preflight':pre['verdict'],'source':src,
            'compiler':str(exe),'game_root':str(game),'live_before':before,
            'live_after':None,'live_unchanged':False,'install_performed':False}
    with tempfile.TemporaryDirectory(prefix='BGXAI_054_COMPILE_') as tmp:
        work=Path(tmp); out=work/'out';out.mkdir()
        local=work/COMPILE_NAME;local.write_bytes(source.read_bytes())
        # --tlkin avoids --use-lang which may save a setting in weidu.conf.
        cmd=[str(exe),'--noautoupdate','--game',str(game),
             '--tlkin',str(game/'lang/ru_ru/dialog.tlk'),
             '--script-style','BG2','--out',str(out),str(local)]
        try:
            proc=runner(cmd,cwd=str(work),capture_output=True,text=True,
                        encoding='utf-8',errors='replace',timeout=MAX_COMPILER_SECONDS,check=False)
            report['return_code']=proc.returncode
            report['stdout_tail']=(proc.stdout or '')[-1200:]
            report['stderr_tail']=(proc.stderr or '')[-1200:]
            generated=list(out.rglob('*.bcs'))
            if not generated:generated=list(work.rglob('*.bcs'))
            valid=[p for p in generated if p.stem.lower()==local.stem.lower()]
            if proc.returncode==0 and len(valid)==1 and valid[0].stat().st_size>0:
                report['compiler_output_sha256']=digest(valid[0])
                report['compiler_output_size']=valid[0].stat().st_size
                report['compiler_output_first8']=valid[0].open('rb').read(8).hex()
                report['status']='COMPILED_TEMP_ONLY'
            else:report['status']='COMPILER_FAILED'
        except (OSError,subprocess.TimeoutExpired) as e:
            report['status']='COMPILER_ERROR';report['error']=str(e)[:250]
        finally:
            report['live_after']=snapshot(game)
            report['live_unchanged']=before==report['live_after']
            if not report['live_unchanged']:
                report['status']='REVIEW_LIVE_HASH_CHANGED'
    # Generated BCS exists only in the temporary directory, deliberately not installed.
    report['output_deleted_after_verification']=True
    return report

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--compile-readonly',action='store_true',help='Read-only BAF compile audit; no TP2 install')
    p.add_argument('--game',type=Path,default=Path(r'C:\Games\BG_EET_FOXX_NEW'))
    p.add_argument('--weidu',type=Path)
    p.add_argument('--source',type=Path,default=Path(__file__).with_name(NAME))
    a=p.parse_args()
    exe=a.weidu or (a.game/'weidu.exe' if (a.game/'weidu.exe').is_file() else a.game/'setup-enhanced-powergaming-scripts.exe')
    try:r=compile_readonly(a.game,a.source,exe)
    except Exception as exc:
        r={'schema':1,'tool':'BGXAI-054-ISOLATED-BAF-COMPILE',
           'status':'BLOCKED_BEFORE_COMPILER','reason':str(exc),'install_performed':False}
    print(json.dumps(r,indent=2,ensure_ascii=False))
    return 0 if r['status']=='COMPILED_TEMP_ONLY' and r['live_unchanged'] else 3

if __name__=='__main__':raise SystemExit(main())
