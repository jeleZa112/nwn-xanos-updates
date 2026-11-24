#!/usr/bin/env python3
"""BGXAI R29 narrow native weapon switching pilot: source-only default.

No modification in status/preflight. Typed installation only, exact baseline SHA,
external checked backups, WeiDU last-only rollback. Not a generalized V3 scorer.
"""
from __future__ import annotations
import argparse, datetime, hashlib, json, os, pathlib, re, shutil, subprocess, sys, tempfile

GAME = pathlib.Path(r'C:\Games\BG_EET_FOXX_NEW')
PACKAGE = 'BGXR29'
SOURCE = pathlib.Path(__file__).with_name('BGXAI_R29_KHALID_BOW_TO_SWORD.baf')
BASELINE = {
    'override/BDDEFAI.BCS': '9bd4e5b413f60ba383fcb78859f9bfe0aab762ee8b0ec2b3f164b6c03377055e',
    'override/DPLAYER.BCS': '4d640ed7f4c50ed10e30b9482940c6733196f3ad7ae1814516ded410405e64ed',
    'override/WTASIGHT.BCS': 'ec50ad2e91a33aad4e4b6b1bc33ac87f0f02f4af49f9649b5cad6c36faeaa403',
    'override/PRIEST1.BCS': '86a3c63799f09e7b9d51f6a61a893eff36f50ee3d6a3fe7eaa2dae97d2861589',
    'override/M_BGXR27.lua': 'e5eb400c56ffb1bc23344a0cf30dcc724d8d18fc2752fabd1c2c63cdcca73735',
    'EEex/copy/EEex_scripts/EEex_Action.lua': '7a64c157418f503e914c4fb3083c97f017e70c9787024fcac779f162c86f20da',
    'enhanced-powergaming-scripts/lib/core_base.tph': '1da3e226645367aa4cc8ba3ff8c1f14627df5ccd3c3e0852941c256b5301e776',
}
WATCH = (*BASELINE, 'chitin.key', 'WeiDU.log', 'weidu.conf')
INSTALL_TOKEN = 'INSTALL_BGXR29_KHALID_BOW_TO_SWORD_PILOT'
ROLLBACK_TOKEN = 'ROLLBACK_BGXR29_KHALID_BOW_TO_SWORD_PILOT'
SOURCE_SHA256 = 'e184c6468e4d927b628b826395b0b573e11b98602e58bacbba4ac9370cda3eee'
EXPECTED_WEIDU_SHA = '0d17e26e3f3ef5b36796eb0ee8ae73cb851d8b62c9702c2e224da2945caafb75'
EXPECTED_WEIDU_LOG_SHA = '96d9db5d80e64c546022aa252e4f4714a869b81526b0df2822d7b8e7c567818f'
BEFORE_LAST = re.compile(r'^~(?:[^~]*[/\\])?BGXRANGED7[/\\]SETUP-BGXRANGED7[.]TP2~\s+#0\s+#0(?:\s|$)', re.I)
RANGED6_LAST = re.compile(r'^~(?:[^~]*[/\\])?BGXRANGED6[/\\]SETUP-BGXRANGED6[.]TP2~\s+#0\s+#0(?:\s|$)', re.I)
RANGED6_PROOF = 'BGXRANGED6/PROOF.json'
RANGED6_STAGE = 'BGXRANGED6/staged/DPLAYER.BCS'
AFTER_LAST = re.compile(r'^~(?:[^~]*[/\\])?BGXR29[/\\]SETUP-BGXR29[.]TP2~\s+#0\s+#0(?:\s|$)', re.I)
RANGED7_PROOF = 'BGXRANGED7/PROOF.json'
RANGED7_STAGE = 'BGXRANGED7/staged/DPLAYER.BCS'
RANGED7_PREVIOUS_SHA = '1786f4dc050be5c4bef65d9b0c39100975a03fdf74057b21fe1b1c2b926d661f'
RANGED7_SOURCE_SHA = '2fd136f4eac23beb24c31744b01ae897aa6a9476e27cfe8392941ef30b600032'
BCS = 'override/BDDEFAI.BCS'
STAGED = f'{PACKAGE}/staged/BDDEFAI.BCS'
PROOF = f'{PACKAGE}/PROOF.json'
TP2 = f'{PACKAGE}/setup-BGXR29.tp2'
SETUP = 'setup-BGXR29.exe'
TP2_TEXT = ('BACKUP ~BGXR29/backup~\n'
            'AUTHOR ~BGXAI R29 narrowly scoped native bow-to-sword guarded pilot~\n'
            'BEGIN ~BGXR29 fighter quickslot bow-to-sword rule~\n'
            'COPY ~BGXR29/staged/BDDEFAI.BCS~ ~override/BDDEFAI.BCS~\n')
RULES = (
 'InParty(Myself)','!InPartySlot(Myself,0)','Class(Myself,FIGHTER)',
 'Global("BGX38_GUARD","LOCALS",1)',
 'Global("BGX66_S_HEAL_SLOT","LOCALS",0)',
 'Global("BGX29_DISABLE","LOCALS",0)','ActionListEmpty()',
 '!GlobalTimerNotExpired("MO_SpellCast","LOCALS")','ModalState(NONE)',
 '!StateCheck(Myself,STATE_PANIC)','!StateCheck(Myself,STATE_HELPLESS)',
 'IsWeaponRanged(Myself)',
 'CheckItemSlot(Myself,"SW1H04",SLOT_WEAPON0)',
 'CheckItemSlot(Myself,"BOW05",SLOT_WEAPON1)',
 'CurrentAmmo("AROW01",Myself)','See(NearestEnemyOf(Myself))',
 '!InParty(NearestEnemyOf(Myself))',
 '!Allegiance(NearestEnemyOf(Myself),GOODCUTOFF)',
 'Range(NearestEnemyOf(Myself),6)',
)
ACTION = 'SelectWeaponAbility(SLOT_WEAPON0,0)'

class Hold(ValueError): pass

def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def safe(path: pathlib.Path) -> None:
    p = path
    while True:
        if p.is_symlink() or (hasattr(p, 'is_junction') and p.is_junction()):
            raise Hold('SYMLINK_OR_JUNCTION_DENIED:' + p.name)
        if p == p.parent: break
        p = p.parent

def sha(path: pathlib.Path) -> str:
    safe(path)
    if not path.is_file(): raise Hold('REQUIRED_FILE_MISSING:' + path.name)
    return hash_bytes(path.read_bytes())

def no_game_process() -> None:
    if os.name != 'nt':
        raise Hold('WINDOWS_REQUIRED_FOR_NATIVE_INSTALL')
    p=subprocess.run(['tasklist.exe','/FO','CSV','/NH'],capture_output=True,
                     text=True,errors='replace',timeout=10,check=False)
    if p.returncode: raise Hold('TASKLIST_FAILED')
    names={'baldur.exe','bg2ee.exe','baldursgate.exe','infinityloader.exe',
           'weidu.exe','setup-enhanced-powergaming-scripts.exe',SETUP.lower()}
    for row in p.stdout.splitlines():
        name=row.split(',',1)[0].strip().strip('"').lower()
        if name in names or name.startswith('setup-bg') or name.startswith('baldur'):
            raise Hold('CLOSE_GAME_AND_WEIDU:' + name)

def last_weidu(game: pathlib.Path) -> str:
    lines=(game/'WeiDU.log').read_text(encoding='utf-8-sig',errors='replace').splitlines()
    # WeiDU log installed component line, not comments.
    values=[line.strip() for line in lines if line.lstrip().startswith('~')]
    if not values: raise Hold('WEIDU_LAST_RECORD_MISSING')
    return values[-1]

def weidu_entries(game: pathlib.Path) -> list[str]:
    log=game/'WeiDU.log'
    safe(log)
    if not log.is_file() or log.stat().st_size>8_000_000:
        raise Hold('WEIDU_LOG_MISSING_OR_OVERSIZED')
    lines=log.read_text(encoding='utf-8-sig',errors='replace').splitlines()
    found=[v.strip() for v in lines if v.lstrip().startswith('~')]
    if not found:raise Hold('WEIDU_INSTALLED_COMPONENTS_MISSING')
    return found

def sanitize_component(line:str)->str:
    # Display basename only, never expose absolute game or user paths.
    m=re.match(r'^~([^~]+)~\s+#\d+\s+#\d+',line)
    if not m:return 'UNKNOWN_COMPONENT'
    name=m.group(1).replace('\\','/').rsplit('/',1)[-1]
    return name[:80] if re.fullmatch(r'[a-zA-Z0-9_.-]{1,80}',name) else 'UNKNOWN_COMPONENT'

def verify_ranged7_history(game:pathlib.Path)->dict:
    """Authenticate the installed V6 OR V7 DPLAYER guard, never assume V7.

    V6 was deployed and live-tested; V7 is source-only in the project plan.
    The same final exact DPLAYER SHA can come from V6 or V7, so a file hash
    alone is insufficient evidence of provenance. All historical and all V6
    installations require their exact on-disk proof, staged BCS and old backup.
    """
    entries=weidu_entries(game)
    latest=entries[-1]
    if any(AFTER_LAST.match(v) for v in entries):
        raise Hold('R29_ALREADY_IN_WEIDU_LOG_STOP')
    v6=[v for v in entries if RANGED6_LAST.match(v)]
    v7=[v for v in entries if BEFORE_LAST.match(v)]
    if len(v6)==1 and not v7:
        version='6'; match=RANGED6_LAST
        proof_rel=RANGED6_PROOF; stage_rel=RANGED6_STAGE
    elif len(v7)==1 and not v6:
        version='7'; match=BEFORE_LAST
        proof_rel=RANGED7_PROOF; stage_rel=RANGED7_STAGE
    elif len(v6)>1:
        raise Hold('RANGED6_NOT_EXACTLY_ONCE_IN_WEIDU_LOG')
    elif len(v7)>1:
        raise Hold('RANGED7_NOT_EXACTLY_ONCE_IN_WEIDU_LOG')
    elif v6 and v7:
        raise Hold('AMBIGUOUS_RANGED6_AND_RANGED7_HISTORY')
    else:
        raise Hold('RANGED6_OR_RANGED7_NOT_INSTALLED_IN_WEIDU_LOG')
    last_is_selected=bool(match.match(latest))
    if sha(game/'override/DPLAYER.BCS')!=BASELINE['override/DPLAYER.BCS']:
        raise Hold('RANGED_LIVE_DPLAYER_SHA_DRIFT')
    # V6 is the actual user-deployed guard. Never substitute hypothetical V7.
    # For V7-last, preserve the old strict last+hash contract; any historical
    # component (and V6 regardless of position) needs independent proof.
    check_proof=(version=='6' or not last_is_selected)
    if check_proof:
        stem='RANGED'+version+'_HISTORICAL_'
        proof_path=game/proof_rel
        safe(proof_path)
        if not proof_path.is_file() or proof_path.stat().st_size>100_000:
            raise Hold(stem+'INSTALL_PROOF_MISSING')
        try:
            proof=json.loads(proof_path.read_text('utf-8'))
        except (ValueError,UnicodeError) as exc:
            raise Hold(stem+'PROOF_INVALID') from exc
        if not isinstance(proof,dict) or (proof.get('old_dplayer_sha256')!=RANGED7_PREVIOUS_SHA or
            proof.get('new_dplayer_sha256')!=BASELINE['override/DPLAYER.BCS'] or
            proof.get('source_sha256')!=RANGED7_SOURCE_SHA or
            proof.get('changed_blocks')!=[1,2]):
            raise Hold(stem+'PROOF_DRIFT')
        if sha(game/stage_rel)!=BASELINE['override/DPLAYER.BCS']:
            raise Hold(stem+'STAGED_DPLAYER_DRIFT')
        folder=proof.get('backup')
        if not isinstance(folder,str) or not folder or len(folder)>1024:
            raise Hold(stem+'BACKUP_REFERENCE_MISSING')
        backup=pathlib.Path(folder)
        if not backup.is_absolute():
            raise Hold(stem+'BACKUP_NOT_ABSOLUTE')
        safe(backup)
        manifest=backup/'SHA256.json'
        safe(manifest)
        if not manifest.is_file() or manifest.stat().st_size>100_000:
            raise Hold(stem+'BACKUP_MANIFEST_MISSING')
        try:
            backup_hashes=json.loads(manifest.read_text('utf-8'))
        except (ValueError,UnicodeError) as exc:
            raise Hold(stem+'BACKUP_MANIFEST_INVALID') from exc
        if not isinstance(backup_hashes,dict) or backup_hashes.get('override/DPLAYER.BCS')!=RANGED7_PREVIOUS_SHA:
            raise Hold(stem+'BACKUP_SHA_DRIFT')
        if sha(backup/'override/DPLAYER.BCS')!=RANGED7_PREVIOUS_SHA:
            raise Hold(stem+'BACKUP_DPLAYER_CORRUPTED')
        # Every recorded backup object must match the backed-up manifest.
        # No manual bypass or regeneration of proof is permitted.
        for rel,expected in backup_hashes.items():
            if not isinstance(rel,str) or not re.fullmatch(r'[A-Za-z0-9_./-]{1,200}',rel) or \
               rel.startswith('/') or '..' in pathlib.PurePosixPath(rel).parts or \
               not isinstance(expected,str) or not re.fullmatch(r'[0-9a-f]{64}',expected):
                raise Hold(stem+'BACKUP_MANIFEST_UNTRUSTED')
            if sha(backup/rel)!=expected:
                raise Hold(stem+'BACKUP_FILE_CORRUPTED')
    return {
        'rangedInstalledVariant':'BGXRANGED'+version,
        'ranged6InWeiDULog':version=='6',
        'ranged7InWeiDULog':version=='7',
        'ranged7LastWeiDU':version=='7' and last_is_selected,
        'ranged6LastWeiDU':version=='6' and last_is_selected,
        'ranged7HistoricalProofVerified':version=='7' and check_proof,
        'ranged6InstallProofVerified':version=='6' and check_proof,
        'lastComponentBasename':sanitize_component(latest),
        'liveDPLAYERExactBaseline':True,
        'manualEpsOriginVerified':False,
        'gameplayLiveVerified':False,
    }

def bcs_parts(raw:bytes) -> list[bytes]:
    if not raw.startswith(b'SC\nCR\nCO\n') or not raw.endswith(b'CR\nSC\n'):
        raise Hold('INVALID_BCS_ENVELOPE')
    starts=[m.start(1) for m in re.finditer(rb'(?:^|\n)(CR\nCO\n)',raw)]
    if not starts or starts[0]!=3: raise Hold('INVALID_BCS_START')
    parts=[raw[a:b] for a,b in zip(starts,starts[1:]+[len(raw)])]
    if b'SC\n'+b''.join(parts)!=raw: raise Hold('NOT_LOSSLESS_BCS_SPLIT')
    return parts

def parse_blocks(raw:str)->list[tuple[tuple[str,...],tuple[str,...]]]:
    blocks=[];mode=None;cond=[];actions=[];responses=0
    for line in raw.splitlines():
        x=line.strip()
        if not x or x.startswith('//'):continue
        if x=='IF':
            if mode is not None:raise Hold('BAF_NESTED_IF')
            mode='cond';cond=[];actions=[];responses=0
        elif x=='THEN':
            if mode!='cond': raise Hold('BAF_BAD_THEN')
            mode='action'
        elif x=='END':
            if mode!='action' or not cond or not actions or responses!=1:
                raise Hold('BAF_BLOCK_INVALID')
            blocks.append((tuple(cond),tuple(actions)));mode=None
        elif x.upper()=='RESPONSE #100' and mode=='action':responses+=1
        elif mode=='cond':cond.append(x)
        elif mode=='action':actions.append(x)
        else:raise Hold('BAF_UNEXPECTED_TOKEN:'+x[:32])
    if mode is not None:raise Hold('BAF_TRUNCATED')
    return blocks

def source_contract(data: bytes) -> None:
    if hash_bytes(data)!=SOURCE_SHA256: raise Hold('PILOT_SOURCE_SHA_DRIFT')
    blocks=parse_blocks(data.decode('utf-8'))
    if len(blocks)!=1 or blocks[0]!=(RULES,(ACTION,)):
        raise Hold('PILOT_RULE_OR_ACTION_DRIFT')
    if b'Attack(' in data or b'ClearActions(' in data or b'ForceSpell(' in data:
        raise Hold('PILOT_PROHIBITED_ACTION')

def call_native(exe:pathlib.Path,game:pathlib.Path,work:pathlib.Path,
                source:pathlib.Path,out:pathlib.Path,step:str)->None:
    p=subprocess.run([str(exe),'--no-auto-tp2','--noautoupdate',
                      '--no-exit-pause','--game',str(game),
                      '--out',str(out),str(source)],
                     cwd=work,stdin=subprocess.DEVNULL,capture_output=True,text=True,
                     errors='replace',timeout=180,check=False)
    msg=(p.stdout or '')+'\n'+(p.stderr or '')
    if p.returncode or re.search(r'(?mi)^\s*(?:ERROR:|FATAL ERROR:)',msg):
        raise Hold('NATIVE_'+step+'_FAILED:'+msg[-350:])
    if out.is_symlink() or not out.is_file() or out.stat().st_size<16:
        raise Hold('NATIVE_'+step+'_OUTPUT_MISSING')

def baseline(game:pathlib.Path, require_last:bool=True)->dict:
    if game != GAME:raise Hold('WRONG_GAME_ROOT')
    no_game_process()
    for name,expected in BASELINE.items():
        if sha(game/name)!=expected:raise Hold('BASELINE_SHA_DRIFT:'+name)
    for name in ('chitin.key','weidu.conf','WeiDU.log'):sha(game/name)
    if sha(game/'WeiDU.log')!=EXPECTED_WEIDU_LOG_SHA:
        raise Hold('WEIDU_LOG_SHA_DRIFT')
    # Historical RANGED7 is acceptable ONLY with proof, staged SHA, backup,
    # exact live DPLAYER/BDDEFAI/EPS/EEex hashes and exact pinned WeiDU.log.
    # `require_last` is kept for old caller compatibility but is not enough
    # to certify a historical component on its own.
    verify_ranged7_history(game)
    compiler=game/'weidu.exe'
    if sha(compiler)!=EXPECTED_WEIDU_SHA:
        raise Hold('GAME_NATIVE_WEIDU_SHA_DRIFT')
    source_contract(SOURCE.read_bytes())
    for name in (STAGED,PROOF,TP2,SETUP):
        safe(game/name)
        if (game/name).exists():raise Hold('R29_STAGE_COLLISION:'+name)
    return {name:sha(game/name) for name in WATCH}

def candidate(game:pathlib.Path)->tuple[bytes,dict]:
    before=baseline(game)
    original=(game/BCS).read_bytes()
    old=bcs_parts(original)
    if len(old)!=1162:raise Hold('EXPECTED_1162_BDDEFAI_BLOCKS')
    with tempfile.TemporaryDirectory(prefix='BGX29_Native_') as td:
        work=pathlib.Path(td)
        binary=work/'weidu.exe';shutil.copy2(game/'weidu.exe',binary)
        baf=work/'PILOT.BAF';baf.write_bytes(SOURCE.read_bytes())
        compiled=work/'PILOT.BCS'
        call_native(binary,game,work,baf,compiled,'PILOT_COMPILE')
        parts=bcs_parts(compiled.read_bytes())
        if len(parts)!=1:raise Hold('PILOT_NOT_SINGLE_BCS_BLOCK')
        candidate_bytes=b'SC\n'+b''.join(parts)[:-3]+b''.join(old)
        new_parts=bcs_parts(candidate_bytes)
        if len(new_parts)!=1163 or new_parts[1:]!=old:
            raise Hold('ORIGINAL_1162_BLOCKS_NOT_PRESERVED')
        input_bcs=work/'CANDIDATE.BCS';input_bcs.write_bytes(candidate_bytes)
        out_baf=work/'CANDIDATE.BAF'
        call_native(binary,game,work,input_bcs,out_baf,'FULL_DECOMPILE')
        newblocks=parse_blocks(out_baf.read_text('utf-8-sig',errors='replace'))
        if len(newblocks)!=1163 or newblocks[0]!=(RULES,(ACTION,)):
            raise Hold('NATIVE_DECOMPILE_FIRST_BLOCK_NOT_EXACT')
    if any(sha(game/k)!=v for k,v in before.items()):
        raise Hold('GAME_CHANGED_DURING_NATIVE_PREFLIGHT')
    historical=verify_ranged7_history(game)
    return candidate_bytes,{'status':'R29_NATIVE_CANDIDATE_READY_NO_INSTALL',
                            'ranged7History':historical,
                            'sourceSha256':SOURCE_SHA256,
                            'newBCSSha256':hash_bytes(candidate_bytes),
                            'newBCSBytes':len(candidate_bytes),
                            'oldBlocks':1162,'newBlocks':1163,
                            'originalBlocksBytePreserved':True,
                            'manualAndEPSOriginVerified':False,
                            'fullWeaponAprImplemented':False,
                            'gameplayLiveVerified':False,'gameModified':False,
                            'dispatchAuthorized':False,'ordersSent':0,
                            'baselineSnapshot':before}

def external_backup(game:pathlib.Path,baseline_sha:dict)->pathlib.Path:
    parent=pathlib.Path(os.environ['USERPROFILE'])/'Documents'/'BGXAI_R29_SAFE_BACKUPS'
    safe(parent)
    dest=parent/('PRE_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    safe(dest);dest.mkdir(parents=True,exist_ok=False)
    for name,expected in baseline_sha.items():
        source=game/name;target=dest/name
        safe(source);safe(target)
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,target)
        if sha(target)!=expected:raise Hold('BACKUP_SHA_MISMATCH:'+name)
    (dest/'SHA256.json').write_text(json.dumps(baseline_sha,indent=2),encoding='utf-8')
    return dest

def use_weidu(game:pathlib.Path,uninstall:bool=False)->None:
    exe=game/SETUP
    safe(exe)
    if sha(exe)!=EXPECTED_WEIDU_SHA:raise Hold('STAGED_SETUP_EXE_SHA_DRIFT')
    op='--force-uninstall' if uninstall else '--force-install'
    args=[str(exe),'--noautoupdate','--no-exit-pause','--game',str(game),
          '--use-lang','ru_ru',op,'0']
    p=subprocess.run(args,cwd=game,stdin=subprocess.DEVNULL,capture_output=True,
                     text=True,errors='replace',timeout=240,check=False)
    out=(p.stdout or '')+'\n'+(p.stderr or '')
    if p.returncode or re.search(r'(?mi)^\s*(?:ERROR:|FATAL ERROR:)',out):
        raise Hold('WEIDU_REQUIRES_MANUAL_REVIEW:'+out[-600:])

def preflight(game:pathlib.Path)->dict:
    _,p=candidate(game)
    return {**p,'status':'R29_NATIVE_PREFLIGHT_PASS_INSTALL_NOT_PERFORMED'}

def install(game:pathlib.Path)->dict:
    compiled,p=candidate(game)
    # Check again after human approval, before any path beneath game is touched.
    print('R29 experimental ONE-WAY bow->sword on fighter with EXACT item slots.')
    print('Not locked to a named character; another fighter matching both slots may switch.')
    print('This does NOT prove manual/EPS provenance or universal action safety.')
    if input('Type '+INSTALL_TOKEN+' exactly (ENTER cancels): ').strip()!=INSTALL_TOKEN:
        return {'status':'CANCELLED_WITHOUT_GAME_CHANGES','gameModified':False}
    if any(sha(game/k)!=v for k,v in p['baselineSnapshot'].items()):
        raise Hold('BASELINE_CHANGED_BEFORE_INSTALL')
    no_game_process()
    backup=external_backup(game,p['baselineSnapshot'])
    package=game/PACKAGE
    safe(package);package.mkdir(parents=True,exist_ok=False)
    stage=game/STAGED
    safe(stage);stage.parent.mkdir(parents=True,exist_ok=False)
    stage.write_bytes(compiled)
    (game/TP2).write_text(TP2_TEXT,encoding='ascii')
    shutil.copy2(game/'weidu.exe',game/SETUP)
    if sha(stage)!=p['newBCSSha256'] or sha(game/SETUP)!=EXPECTED_WEIDU_SHA:
        raise Hold('STAGING_SHA_MISMATCH_STOP')
    use_weidu(game)
    if not AFTER_LAST.match(last_weidu(game)) or sha(game/BCS)!=p['newBCSSha256']:
        raise Hold('R29_INSTALL_RESULT_NOT_VERIFIED_MANUAL_REVIEW')
    for name,expected in p['baselineSnapshot'].items():
        if name not in (BCS,'WeiDU.log') and sha(game/name)!=expected:
            raise Hold('UNRELATED_GAME_FILE_CHANGED_MANUAL_REVIEW:'+name)
    proof={**p,'status':'R29_INSTALLED_AWAITING_LIVE_AB',
           'backup':str(backup),'installedBCSSha256':p['newBCSSha256'],
           'gameModified':True,'installPerformed':True,
           'weaponSwitchAuthorized':False,'gameplayLiveVerified':False}
    (game/PROOF).write_text(json.dumps(proof,ensure_ascii=False,indent=2),encoding='utf-8')
    return proof

def read_proof(game:pathlib.Path)->dict:
    proof_path=game/PROOF
    safe(proof_path)
    proof=json.loads(proof_path.read_text(encoding='utf-8'))
    if proof.get('status')!='R29_INSTALLED_AWAITING_LIVE_AB' or \
       proof.get('sourceSha256')!=SOURCE_SHA256 or not isinstance(proof.get('backup'),str):
        raise Hold('R29_PROOF_INVALID')
    backup=pathlib.Path(proof['backup']);safe(backup)
    hashes=json.loads((backup/'SHA256.json').read_text(encoding='utf-8'))
    if hashes!=proof.get('baselineSnapshot'):raise Hold('R29_BACKUP_MANIFEST_MISMATCH')
    for name,expected in hashes.items():
        if sha(backup/name)!=expected:raise Hold('R29_BACKUP_CORRUPTED:'+name)
    return proof

def status(game:pathlib.Path)->dict:
    if game != GAME:raise Hold('WRONG_GAME_ROOT')
    no_game_process()
    latest=last_weidu(game)
    if not AFTER_LAST.match(latest):
        # If R29 is absent, a later unrelated WeiDU mod is not an error.
        # Require the same exact baseline + authenticated V6/V7 chain.
        snap=baseline(game)
        return {'status':'R29_NOT_INSTALLED_BASELINE',
                'ranged7History':verify_ranged7_history(game),
                'baselineCheckedFiles':len(snap),'gameModified':False}
    p=read_proof(game)
    if sha(game/BCS)!=p['newBCSSha256']:
        raise Hold('INSTALLED_BCS_SHA_DRIFT')
    return {'status':'R29_INSTALLED_UNTESTED_IN_GAME','newBCSSha256':p['newBCSSha256']}

def rollback(game:pathlib.Path)->dict:
    if game!=GAME:raise Hold('WRONG_GAME_ROOT')
    no_game_process()
    if not AFTER_LAST.match(last_weidu(game)):
        raise Hold('R29_NOT_LAST_NO_ROLLBACK')
    p=read_proof(game)
    if sha(game/BCS)!=p['newBCSSha256']:
        raise Hold('LIVE_BCS_CHANGED_ROLLBACK_STOP')
    if input('Type '+ROLLBACK_TOKEN+' exactly (ENTER cancels): ').strip()!=ROLLBACK_TOKEN:
        return {'status':'ROLLBACK_CANCELLED'}
    use_weidu(game,uninstall=True)
    if sha(game/BCS)!=BASELINE[BCS]:
        raise Hold('ROLLBACK_BASELINE_NOT_RESTORED')
    return {'status':'R29_ROLLBACK_VERIFIED','restoredBCSSha256':BASELINE[BCS]}

def save_report(result: dict, mode: str) -> pathlib.Path:
    """Exactly one atomic JSON OUTSIDE game, no silent preflight success."""
    root=pathlib.Path(os.environ.get('USERPROFILE',str(pathlib.Path.home())))
    out=root/'Documents'/'BGXAI_LIVE_REPORTS'
    safe(out)
    if out==GAME or GAME in out.parents:
        raise Hold('REPORT_DESTINATION_INSIDE_GAME')
    out.mkdir(parents=True,exist_ok=True)
    name=('BGXAI_R29_'+mode.upper()+'_'
          +datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json')
    target=out/name
    temp=target.with_suffix('.tmp')
    safe(target);safe(temp)
    if target.exists() or temp.exists():raise Hold('R29_REPORT_FILENAME_COLLISION')
    with temp.open('x',encoding='utf-8') as handle:
        json.dump({'schema':'BGXAI_R29_GUARDED_V1','mode':mode,**result},
                  handle,ensure_ascii=False,indent=2)
        handle.write('\n')
    os.replace(temp,target)
    return target

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--game',type=pathlib.Path,default=GAME)
    p.add_argument('mode',nargs='?',choices=('preflight','install','status','rollback'))
    args=p.parse_args()
    mode=args.mode
    if mode is None:
        print('R29 Khalid exact BOW05+AROW01 -> SW1H04 pilot (not general V3)')
        print('1=read-only native preflight; 2=typed install; 3=status; 4=typed last-only rollback; 0=exit')
        mode={'1':'preflight','2':'install','3':'status','4':'rollback','0':'exit'}.get(input('Choice [0]: ').strip() or '0','exit')
    if mode=='exit':return 0
    try:
        result=globals()[mode](args.game.resolve())
        print(json.dumps(result,ensure_ascii=False,indent=2))
        path=save_report(result,mode)
        print('REPORT_FILE='+str(path))
        return 0
    except (Hold,OSError,ValueError,subprocess.TimeoutExpired,UnicodeError) as e:
        print('R29 SAFE STOP: '+str(e),file=sys.stderr)
        failed={'status':'R29_SAFE_STOP','reason':str(e),
                'gameModifiedUnknown':mode in ('install','rollback'),
                'dispatchAuthorized':False,'ordersSent':0}
        if mode in ('preflight','status'):
            # Source-only explanation: never leak full Windows paths or change
            # the state of WeiDU; do not turn this into a successful preflight.
            try:
                if args.game.resolve()==GAME:
                    entries=weidu_entries(args.game.resolve())
                    failed['weiduHistoryReadOnly']={
                        'lastComponentBasename':sanitize_component(entries[-1]),
                        'ranged6InstalledEntryCount':sum(bool(RANGED6_LAST.match(v)) for v in entries),
                        'ranged7InstalledEntryCount':sum(bool(BEFORE_LAST.match(v)) for v in entries),
                        'r29InstalledEntryPresent':any(bool(AFTER_LAST.match(v)) for v in entries),
                        'ranged6InstallProofPresent':(GAME/RANGED6_PROOF).is_file(),
                        'ranged7InstallProofPresent':(GAME/RANGED7_PROOF).is_file(),
                        'liveDPLAYERBaselineMatches':sha(GAME/'override/DPLAYER.BCS')==BASELINE['override/DPLAYER.BCS'],
                    }
            except (OSError,ValueError,UnicodeError):
                pass
        try:
            path=save_report(failed,mode)
            print('REPORT_FILE='+str(path))
        except (Hold,OSError,ValueError) as err:
            print('R29 REPORT SAVE FAILED: '+str(err),file=sys.stderr)
        return 3
if __name__=='__main__':raise SystemExit(main())