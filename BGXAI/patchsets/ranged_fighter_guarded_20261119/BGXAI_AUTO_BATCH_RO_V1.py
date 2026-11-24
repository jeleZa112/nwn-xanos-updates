#!/usr/bin/env python3
"""BGXAI automatic one-run READ ONLY verification of the actual EET source.

Intended entry: BGXAI_UPDATE.cmd -> BGXAI_SYNC.ps1 menu 168.
Runs independent checks in one pass, including on individual failures, and
writes exactly one JSON report OUTSIDE the game. Never authorizes a game action.
The score/provenance gaps are *reported*, never filled with invented evidence.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
sys.dont_write_bytecode=True  # Never create __pycache__ inside staged BGXAI_DEV.
import time
import traceback

SCHEMA = 'BGXAI_AUTO_BATCH_RO_V1'
NATIVE_SHA = '27285b3d067eab2c67b075dc8654b9a0f74da0d7920b2e96339ced3e14bcd10a'
BAF_SHA = '92b8b1d3393a286d4d69f38b9542651acb429f8ef6627051195c7a1a95c09f30'
BAF = 'BGXAI_WEAPON_SLOT_CONSUMER_V3.baf'
NATIVE = 'BGXAI_WEAPON_NATIVE_COMPILE_PREFLIGHT_RO.py'
TEST_NATIVE = 'test_weapon_native_compile_ro_v1.py'
GAME_PATHS = ('chitin.key', 'WeiDU.log', 'weidu.conf', 'override/DPLAYER.BCS',
              'override/WTASIGHT.BCS', 'override/PRIEST1.BCS',
              'override/M_BGXR27.lua')
RUNTIME_GATES = (
    'ALTERNATE_QUICKSLOT_EFFECTIVE_APR_THAC0_DAMAGE_UNDER_CURRENT_BUFFS',
    'ENGINE_LAUNCHER_AMMO_PAIR_AND_TARGET_EFFECTS',
    'MANUAL_ORDER_VS_EPS_VS_AI_ORIGIN_PROVEN',
    'NONINTERRUPT_ACTION_RECOVERY_AND_QUEUE_BOUNDARY_PROVEN',
    'FRESH_TARGET_AND_EQUIPMENT_IDENTITY_PROVEN',
    'AUTHENTICATED_PRODUCER_AND_INSTALL_ROLLBACK',
)
GAME_EXECUTABLES = ('baldur.exe','baldursgate.exe','bg2ee.exe',
                    'infinityloader.exe','weidu.exe','setup-enhanced-powergaming-scripts.exe')

class Hold(Exception):
    pass


def sha_file(path: Path, max_bytes: int = 200_000_000) -> str | None:
    if path.is_symlink():
        raise Hold('SYMLINK_DENIED:' + path.name)
    if not path.exists():
        return None
    if not path.is_file():
        raise Hold('NOT_A_REGULAR_FILE:' + path.name)
    try:
        if path.stat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise Hold('REPARSE_DENIED:' + path.name)
    except AttributeError:
        pass
    if path.stat().st_size > max_bytes:
        raise Hold('FILE_TOO_LARGE:' + path.name)
    h=hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def marker(status: str, **data) -> dict:
    return {'status':status, **data}


def parse_game_snapshot(game: Path) -> dict:
    readings={}
    for rel in GAME_PATHS:
        readings[rel]=sha_file(game/rel)
    # Only source identity, not entire game state or an EPS queue proof.
    return readings


# Fixed-list installed source fingerprinting; no recursive traversal and no imports.
# Records raw source identity and keyword counts, NEVER a proven action origin.
INSTALLED_SOURCE_CANDIDATES = (
    'enhanced-powergaming-scripts/lib/core_base.tph',
    'enhanced-powergaming-scripts/baf/normal/mocore.baf',
    'enhanced-powergaming-scripts/baf/accelerated/mocore.baf',
    'EEex/copy/EEex_scripts/EEex_Action.lua',
    'EEex/copy/EEex_scripts/EEex_Sprite.lua',
    'EEex/EEex_scripts/EEex_Action.lua',
    'EEex/EEex_scripts/EEex_Sprite.lua',
)

def inspect_installed_script_sources(game: Path) -> dict:
    found=[]
    missing=[]
    terms=(b'ActionListEmpty()', b'MO_SpellCast',
           b'EEex_Action_AddSpriteStartedActionListener',
           b'EEex_Sprite_GetActiveStats')
    for name in INSTALLED_SOURCE_CANDIDATES:
        path=game/Path(name)
        # Block symlinked directories as well as files. Do not follow junctions.
        for parent in (path, *path.parents):
            if parent==game.parent:
                break
            if parent.is_symlink():
                raise Hold('INSTALLED_SOURCE_SYMLINK_DENIED:'+name)
            try:
                if parent.exists() and (parent.stat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT):
                    raise Hold('INSTALLED_SOURCE_REPARSE_DENIED:'+name)
            except AttributeError:
                pass
        if not path.exists():
            missing.append(name)
            continue
        if not path.is_file() or not 0<path.stat().st_size<=3_000_000:
            raise Hold('INSTALLED_SOURCE_NOT_READABLE_OR_OVERSIZE:'+name)
        data=path.read_bytes()
        found.append({'relativeSource':name,
                      'size':len(data),
                      'sha256':hashlib.sha256(data).hexdigest(),
                      'literalCounts':{term.decode('ascii'):data.count(term) for term in terms}})
    return marker('INFO_INSTALLED_EPS_EEEX_SOURCE_INVENTORY',
                  candidatesChecked=len(INSTALLED_SOURCE_CANDIDATES),
                  found=found,notFound=missing,
                  version18_4Verified=False,
                  installedSourceMatchedPublicRepository=False,
                  manualVsEpsOriginVerified=False,
                  alternateEffectiveAprVerified=False,
                  dispatchAuthorized=False,
                  ordersSent=0)

# Installed-source EPS action arbitration map. This is a SOURCE-level map,
# not the interpreter's runtime script priority, not an order-origin proof.
# Never evaluate BAF/TPH/Lua, and never expose entire user source lines.
_EPS_SOURCES = INSTALLED_SOURCE_CANDIDATES[:3]
_EEEX_ACTION = INSTALLED_SOURCE_CANDIDATES[3]
_R27_PINNED_EEEX_ACTION_SHA = '7a64c157418f503e914c4fb3083c97f017e70c9787024fcac779f162c86f20da'
_START_IF = re.compile(rb'(?m)^[ \t]*IF[ \t]*(?:\r?\n)')
_END_IF = re.compile(rb'(?m)^[ \t]*END(?:[ \t]*(?:\r?\n|$))')
_THEN = re.compile(rb'(?m)^[ \t]*THEN[ \t]*(?:\r?\n)')
_ACTION_CAST = re.compile(rb'(?mi)^[ \t]*(?:ReallyForceSpell|ForceSpell|Spell|SpellRES|UseItem|UseItemSlot|ApplySpell)(?:\s|\()')
_ACTION_ATTACK = re.compile(rb'(?mi)^[ \t]*(?:Attack|AttackOneRound|AttackReevaluate|ForceAttack)(?:\s|\()')


def _eps_block_logic(data: bytes) -> dict:
    # This bounded regex scanner recognizes only literal BAF IF/THEN/END lines.
    # WeiDU macros, aliases, expansions and actual runtime priorities are UNKNOWN.
    stats={'literalIfThenEndBlocks':0,'blocksWithQueueEmptyTrigger':0,
           'blocksWithMOSpellCastTrigger':0,'blocksWithBothTriggers':0,
           'blocksWithSpellOrItemAction':0,'blocksWithAttackAction':0,
           'blocksWithPotentialOrderWithoutQueueGuard':0,
           'sourceMentionsBGXW3Req':data.count(b'BGXW3_REQ')}
    pending=None
    for line in data.splitlines(keepends=True):
        if _START_IF.fullmatch(line):
            pending={'trigger':bytearray(),'actions':bytearray(),'then':False}
        elif pending is not None and _THEN.fullmatch(line):
            pending['then']=True
        elif pending is not None and _END_IF.fullmatch(line):
            if pending['then']:
                trig=bytes(pending['trigger']);actions=bytes(pending['actions'])
                queue=b'ActionListEmpty()' in trig
                spell_timer=b'MO_SpellCast' in trig
                cast=bool(_ACTION_CAST.search(actions))
                attack=bool(_ACTION_ATTACK.search(actions))
                stats['literalIfThenEndBlocks']+=1
                stats['blocksWithQueueEmptyTrigger']+=int(queue)
                stats['blocksWithMOSpellCastTrigger']+=int(spell_timer)
                stats['blocksWithBothTriggers']+=int(queue and spell_timer)
                stats['blocksWithSpellOrItemAction']+=int(cast)
                stats['blocksWithAttackAction']+=int(attack)
                stats['blocksWithPotentialOrderWithoutQueueGuard']+=int((cast or attack) and not queue)
            pending=None
        elif pending is not None:
            part='actions' if pending['then'] else 'trigger'
            # Keep memory bounded if a non-BAF file has an extremely long macro.
            if len(pending[part])<80_000:
                pending[part].extend(line[:min(len(line),80_000-len(pending[part]))])
    return stats


def inspect_installed_eps_priority(game: Path, inventory: dict) -> dict:
    if inventory.get('status')!='INFO_INSTALLED_EPS_EEEX_SOURCE_INVENTORY':
        return marker('INFO_EPS_SOURCE_INVENTORY_REQUIRED',filesAnalyzed=0,
                      manualVsEpsOriginVerified=False,dispatchAuthorized=False,ordersSent=0)
    items={x.get('relativeSource'):x for x in inventory.get('found',[])}
    if len(items)!=len(inventory.get('found',[])):
        raise Hold('REPEATED_SOURCE_IDENTITY_IN_INVENTORY')
    analyses=[]
    for name in _EPS_SOURCES:
        item=items.get(name)
        if item is None:continue
        path=game/name
        if sha_file(path,max_bytes=3_000_000)!=item.get('sha256'):
            raise Hold('EPS_SOURCE_CHANGED_BETWEEN_INVENTORY_AND_AUDIT:'+name)
        data=path.read_bytes()
        if hashlib.sha256(data).hexdigest()!=item['sha256']:
            raise Hold('EPS_SOURCE_CHANGED_DURING_AUDIT:'+name)
        x=_eps_block_logic(data)
        if x['sourceMentionsBGXW3Req']:
            raise Hold('EPS_SOURCE_MENTIONS_RESERVED_BGXW3_REQUEST:'+name)
        analyses.append({'relativeSource':name,'sha256':item['sha256'],
                         'size':len(data),'sourceLevelHeuristicOnly':True,**x})
    action=items.get(_EEEX_ACTION)
    hook_sha_known=bool(action and action.get('sha256')==_R27_PINNED_EEEX_ACTION_SHA)
    return marker('INFO_EPS_LITERAL_SOURCE_PRIORITY_MAP_NOT_RUNTIME_PROOF',
                  filesAnalyzed=len(analyses),fileResults=analyses,
                  eeexActionSourceMatchesR27PinnedHook=hook_sha_known,
                  eeexActionHookAvailabilityInCurrentLiveSessionVerified=False,
                  selectedEpsNormalOrAcceleratedRuntimeProfileVerified=False,
                  weiDuMacroExpandedPriorityVerified=False,
                  currentlyCompiledEPSRuntimePriorityVerified=False,
                  alternativeQuickslotEffectiveAprVerified=False,
                  manualVsEpsOriginVerified=False,
                  actionBoundaryVerified=False,
                  dispatchAuthorized=False,weaponSwitchAuthorized=False,ordersSent=0)

def verified_existing_native(report_dir: Path, game: Path, compiler: Path) -> dict | None:
    try:
        compiler_hash=sha_file(compiler)
        if not compiler_hash:
            return None
        reports=sorted(report_dir.glob('BGXAI_WEAPON_NATIVE_COMPILE_RO_*.json'),
                       key=lambda f:f.stat().st_mtime,reverse=True)
        for path in reports[:20]:
            if path.is_symlink() or path.stat().st_size > 256_000:
                continue
            obj=json.loads(path.read_text(encoding='utf-8-sig'))
            if not isinstance(obj,dict) or obj.get('schema') != 'BGXAI_WEAPON_NATIVE_COMPILE_RO_V1':
                continue
            source=obj.get('source') or {}
            if (obj.get('status') == 'NATIVE_WEIDU_COMPILED_TEMP_ONLY' and
                obj.get('exitCode') == 0 and obj.get('compilerSha256') == compiler_hash and
                source.get('sha256') == BAF_SHA and source.get('size') == 6763 and
                source.get('blocks') == 8 and source.get('actionCount') == 8 and
                obj.get('compiledSize',0) >= 16 and
                re.fullmatch(r'[0-9a-f]{64}',str(obj.get('compiledSha256',''))) and
                obj.get('nativeSymbolsAcceptedByCompiler') is True and
                obj.get('watchedFilesChanged') is False and
                obj.get('gameplayLiveVerified') is False and
                obj.get('engineBehaviorVerified') is False and
                obj.get('installPerformed') is False and
                obj.get('ordersSent') == 0 and type(obj.get('ordersSent')) is int and
                obj.get('dispatchAuthorized') is False and
                obj.get('weaponSwitchAuthorized') is False):
                return {'verifiedHistoricalSource':BAF_SHA,'compiledBcsSha256':obj['compiledSha256'],
                        'compiledBcsSize':obj['compiledSize'],
                        'currentGameNativeRecheck':False,
                        'source':'PREVIOUS_REAL_EET_REPORT_MATCHES_SAME_WEIDU_EXE',
                        'historicalOnly':True}
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError):
        pass
    return None


def inspect_game_processes() -> dict:
    if os.name != 'nt':
        return marker('HOLD_PROCESS_STATE_UNPROVEN',platform=os.name)
    try:
        cp=subprocess.run(['tasklist.exe','/FO','CSV','/NH'],capture_output=True,
                          timeout=8,text=True,errors='replace',check=False)
        if cp.returncode != 0:
            return marker('HOLD_TASKLIST_FAILED',exitCode=cp.returncode)
        running=[]
        for line in cp.stdout.splitlines():
            # CSV first column is the executable name.
            name=line.split(',',1)[0].strip().strip('"').lower()
            if (name in GAME_EXECUTABLES or name.startswith('baldur') or
                name.startswith('bgmain') or name.startswith('setup-') or
                name.endswith('weidu.exe')):
                running.append(name)
        return marker('HOLD_GAME_OR_WEIDU_RUNNING' if running else 'PASS_NO_KNOWN_GAME_PROCESS',running=running)
    except (OSError,subprocess.TimeoutExpired):
        return marker('HOLD_PROCESS_STATE_UNPROVEN')


def safe_compiler(game: Path) -> Path | None:
    for name in ('weidu.exe','setup-enhanced-powergaming-scripts.exe'):
        p=game/name
        if p.is_file() and not p.is_symlink():
            return p
    return None


def static_baf_contract(path: Path) -> dict:
    if sha_file(path) != BAF_SHA:
        raise Hold('PINNED_BAF_SHA_MISMATCH')
    text=path.read_text(encoding='utf-8')
    blocks=re.findall(r'(?m)^IF\s*\n(.*?)^END\s*$',text,re.S|re.M)
    if len(blocks)!=8:
        raise Hold('EXPECTED_EXACTLY_EIGHT_BCS_BLOCKS')
    checks=0
    for i,block in enumerate(blocks):
        for needle in (f'Global("BGXW3_REQ","LOCALS",{i+1})',
                       f'HasItemSlot(Myself,SLOT_WEAPON{i%4})',
                       f'SelectWeaponAbility(SLOT_WEAPON{i%4},0)',
                       'ActionListEmpty()',
                       'Global("BGX38_GUARD","LOCALS",1)',
                       'Global("BGX66_S_HEAL_SLOT","LOCALS",0)',
                       'GlobalTimerNotExpired("BGXW3_LEASE","LOCALS")',
                       'See(NearestEnemyOf(Myself))',
                       '!InParty(NearestEnemyOf(Myself))',
                       '!Allegiance(NearestEnemyOf(Myself),GOODCUTOFF)',
                       'ModalState(NONE)'):
            checks+=1
            if needle not in block:
                raise Hold('GUARD_MISSING:'+needle)
        checks+=1
        if block.count('SelectWeaponAbility(')!=1:
            raise Hold('WRONG_NUMBER_WEAPON_COMMANDS')
        if i>=4:
            for needle in ('!WeaponCanDamage(NearestEnemyOf(Myself),MAINHAND)',
                           'Global("BGXW3_NATIVE_PROVENANCE","LOCALS",1)'):
                checks+=1
                if needle not in block:
                    raise Hold('MISSING_NATIVE_GUARD:'+needle)
        else:
            checks+=1
            if 'WeaponCanDamage(' in block or 'BGXW3_NATIVE_PROVENANCE' in block:
                raise Hold('OLD_OPTIMIZER_BRANCH_MUTATED')
    return marker('PASS_BAF_EIGHT_BRANCH_STATIC',assertions=checks,
                  compiledOnRealEETInPriorReportOnly=True)


CAPTURE_REQUIREMENTS = RUNTIME_GATES + ('SOURCE_ORIGIN_TRUSTED',)


def evaluate_capture_candidate(snapshot: object, slot: object) -> dict:
    """Real pure-function policy for the *advisory* gate, never a dispatch gate.

    A Boolean supplied by an untrusted caller is NOT engine proof. Even a
    fully positive synthetic scene is only a candidate to inspect further.
    No returned field can authorize a weapon switch or a game action.
    """
    if type(slot) is not int or not 0 <= slot <= 3 or not isinstance(snapshot,dict):
        return marker('REJECT_BAD_SLOT_OR_SNAPSHOT',candidateReady=False,
                      dispatchAuthorized=False,weaponSwitchAuthorized=False,ordersSent=0)
    # Exact key set and exact Boolean types: neither missing keys, False==0,
    # nor attacker-added metadata can silently satisfy evidence requirements.
    if set(snapshot) != set(CAPTURE_REQUIREMENTS) or any(
            type(snapshot[k]) is not bool for k in CAPTURE_REQUIREMENTS):
        return marker('REJECT_UNVERIFIED_EVIDENCE_SHAPE',candidateReady=False,
                      dispatchAuthorized=False,weaponSwitchAuthorized=False,ordersSent=0)
    absent=[k for k in CAPTURE_REQUIREMENTS if snapshot[k] is not True]
    return marker('CANDIDATE_COMPLETE_UNTRUSTED_NO_DISPATCH' if not absent
                  else 'HOLD_MISSING_SNAPSHOT_REQUIREMENTS',
                  candidateReady=not absent, missing=absent,
                  dispatchAuthorized=False,weaponSwitchAuthorized=False,ordersSent=0)


def negative_matrix_contract() -> dict:
    """Run actual advisory gate over every combination: 2^7 states x 4 slots.

    This tests source policy on synthetic inputs, NOT live action provenance,
    EPS state, gameplay, or authority to write to BCS/LOCALS.
    """
    checks=0;incomplete=0;complete=0
    for bits in range(128):
        for slot in range(4):
            evidence={name:bool(bits & (1<<i))
                      for i,name in enumerate(CAPTURE_REQUIREMENTS)}
            result=evaluate_capture_candidate(evidence,slot)
            expected_complete=bits==127
            if result['candidateReady'] is not expected_complete or \
               result['dispatchAuthorized'] is not False or \
               result['weaponSwitchAuthorized'] is not False or \
               type(result['ordersSent']) is not int or result['ordersSent']!=0 or \
               len(result['missing']) != len(CAPTURE_REQUIREMENTS)-bits.bit_count():
                raise Hold('SYNTHETIC_POLICY_MATRIX_CONTRACT_FAILURE')
            if expected_complete:complete+=1
            else:incomplete+=1
            checks+=1
    if checks!=512 or complete!=4 or incomplete!=508:
        raise Hold('SYNTHETIC_POLICY_MATRIX_CARDINALITY_DRIFT')
    return marker('PASS_512_ADVISORY_GATE_CASES',cases=checks,
                  rejectedIncompleteCases=incomplete,
                  untrustedCompleteCandidatesNoDispatch=complete,
                  note='ACTUAL_SOURCE_GATE_ON_SYNTHETIC_INPUTS_NOT_GAMEPLAY')


def run_subprocess_test(path: Path, cwd: Path) -> dict:
    if not path.is_file():
        return marker('HOLD_TEST_SOURCE_NOT_STAGED',test=path.name)
    try:
        proc=subprocess.run([sys.executable,'-B',str(path)],cwd=str(cwd),capture_output=True,
                            text=True,errors='replace',timeout=35,check=False)
        tail=(proc.stdout+'\n'+proc.stderr)[-2400:]
        match=re.search(r'Ran (\d+) tests?',tail)
        if not match or proc.returncode!=0 or not re.search(r'(?m)^OK(?: \(skipped=\d+\))?\s*$',tail):
            return marker('HOLD_UNIT_TESTS_FAIL',exitCode=proc.returncode,
                          passedTests=None,tail=tail[-1100:])
        skipped=re.search(r'OK \(skipped=(\d+)\)',tail)
        return marker('PASS_UNIT_TESTS',totalTests=int(match.group(1)),
                      skippedTests=int(skipped.group(1)) if skipped else 0)
    except (OSError,subprocess.TimeoutExpired) as e:
        return marker('HOLD_UNIT_TESTS_RUNTIME',reason=type(e).__name__)


def game_live_proof_gates(installed_r27_sha: str | None = None) -> dict:
    # The already installed R27 SOURCE identity is useful evidence, but still
    # captures ONLY the selected weapon. Never project APR to another slot.
    # Authoritative source hash comes from actual R27 deployment manifest.
    selected_only=(installed_r27_sha ==
                   'e5eb400c56ffb1bc23344a0cf30dcc724d8d18fc2752fabd1c2c63cdcca73735')
    return marker('HOLD_LIVE_ORIGIN_AND_ALT_STATS_NOT_PROVEN',
                  missing=list(RUNTIME_GATES),
                  selectedOnlyR27SourceShaRecognized=selected_only,
                  selectedOnlyObserverIsNotAlternateAPRProof=True,
                  currentBCSSyntaxPreviouslyCompiledOnly=True,
                  alternateEffectiveAprVerified=False,
                  launcherAmmoEnginePairVerified=False,
                  manualVsEpsOriginVerified=False,
                  nativeActionRecoveryVerified=False,
                  dispatchAuthorized=False,weaponSwitchAuthorized=False,
                  ordersSent=0)


def run_batch(game:Path, source_dir:Path, report_dir:Path, fresh_native:bool=False,
              process_override:dict|None=None) -> tuple[dict,int]:
    started=time.monotonic()
    report={'schema':SCHEMA,'sourceOnly':True,'installPerformed':False,
            'gameplayLiveVerified':False,'weaponSwitchAuthorized':False,
            'dispatchAuthorized':False,'ordersSent':0,'localsWritten':0,
            'gameFilesChanged':None,'stages':{},'missingRuntimeProof':list(RUNTIME_GATES)}
    stages=report['stages']
    def stage(name,func):
        began=time.monotonic()
        try:
            value=func()
            if not isinstance(value,dict) or not isinstance(value.get('status'),str):
                raise Hold('STAGE_BAD_RESULT')
            stages[name]=value
        except (Hold,ValueError,OSError,UnicodeError,AssertionError,RuntimeError) as e:
            stages[name]=marker('HOLD_'+type(e).__name__.upper(),reason=str(e)[:250])
        except Exception as e: # Never kill independent checks, but never hide exception.
            stages[name]=marker('HOLD_UNEXPECTED_EXCEPTION',exceptionType=type(e).__name__)
        stages[name]['durationMs']=round((time.monotonic()-began)*1000)
    game=Path(game).resolve();source_dir=Path(source_dir).resolve();report_dir=Path(report_dir).resolve()
    stage('sourcePin',lambda: marker('PASS_PINNED_SOURCE',
          bafSha256=BAF_SHA,nativeModuleSha256=NATIVE_SHA)
          if sha_file(source_dir/BAF)==BAF_SHA and
             sha_file(source_dir/NATIVE)==NATIVE_SHA else
          marker('HOLD_PINNED_SOURCE_BYTES_MISMATCH'))
    stage('bafGuard',lambda:static_baf_contract(source_dir/BAF))
    stage('policyMatrix',negative_matrix_contract)
    stage('nativeMockContracts',lambda:run_subprocess_test(source_dir/TEST_NATIVE,source_dir))
    stage('batchSelftests',lambda:run_subprocess_test(source_dir/'test_auto_batch_ro_v1.py',source_dir))
    stage('processes',lambda:process_override if process_override is not None else inspect_game_processes())
    stage('installedScriptSources',lambda:inspect_installed_script_sources(game))
    stage('epsSourcePriorityMap',lambda:inspect_installed_eps_priority(game,stages['installedScriptSources']))
    stage('gameBefore',lambda: marker('PASS_OBSERVED_WATCH_SET',
          files=parse_game_snapshot(game)) if (game/'chitin.key').is_file() and
          (game/'WeiDU.log').is_file() else
          marker('HOLD_CHITIN_OR_WEIDU_LOG_NOT_FOUND'))
    def native_stage():
        if stages['sourcePin']['status']!='PASS_PINNED_SOURCE':
            return marker('HOLD_PINNED_SOURCE_BEFORE_WEIDU')
        if stages['processes']['status']!='PASS_NO_KNOWN_GAME_PROCESS':
            return marker('HOLD_PROCESS_STATE_BEFORE_NATIVE_COMPILE',
                          processStatus=stages['processes']['status'])
        if stages['gameBefore']['status']!='PASS_OBSERVED_WATCH_SET':
            return marker('HOLD_GAME_BASELINE_BEFORE_NATIVE_COMPILE')
        compiler=safe_compiler(game)
        if compiler is None:
            return marker('HOLD_WEIDU_EXE_MISSING')
        previous=None if fresh_native else verified_existing_native(report_dir,game,compiler)
        if previous is not None:
            return marker('PASS_PRIOR_NATIVE_COMPILE_REUSED_HISTORICAL_ONLY',**previous)
        spec=importlib.util.spec_from_file_location('bgxai_native_readonly',str(source_dir/NATIVE))
        if not spec or not spec.loader:
            raise Hold('NATIVE_MODULE_LOAD_FAILED')
        mod=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        native=mod.compile_readonly(game,source_dir/BAF,compiler)
        return marker('PASS_NATIVE_TEMP_COMPILED_NO_INSTALL' if
                      native.get('status')=='NATIVE_WEIDU_COMPILED_TEMP_ONLY' and
                      native.get('watchedFilesChanged') is False else
                      'HOLD_NATIVE_COMPILE_DID_NOT_PASS',
                      nativeStatus=native.get('status'),
                      nativeSymbolsAccepted=bool(native.get('nativeSymbolsAcceptedByCompiler')),
                      compiledBcsSha256=native.get('compiledSha256'),
                      watchedFilesChanged=native.get('watchedFilesChanged'),
                      noInstall=not native.get('installPerformed',True))
    stage('nativeWeiDU',native_stage)
    stage('gameAfter',lambda: marker('PASS_WATCHED_GAME_FILES_UNCHANGED',
          filesCompared=len(GAME_PATHS)) if
          stages['gameBefore']['status']=='PASS_OBSERVED_WATCH_SET' and
          stages['gameBefore']['files']==parse_game_snapshot(game) else
          marker('HOLD_WATCHED_GAME_FILE_DIFF_OR_BASELINE_MISSING'))
    stage('runtimeProof',lambda:game_live_proof_gates(
          stages.get('gameBefore',{}).get('files',{}).get('override/M_BGXR27.lua')))
    failed=[name for name,item in stages.items() if item['status'].startswith('HOLD_')
            and name != 'runtimeProof']
    report['gameFilesChanged'] = False if stages['gameAfter']['status']=='PASS_WATCHED_GAME_FILES_UNCHANGED' else None
    report['stepCount']=len(stages)
    report['batchCaseCount']=stages.get('policyMatrix',{}).get('cases',0)
    report['unitTestCount']=sum(stages.get(k,{}).get('totalTests',0) or 0 for k in
                                ('nativeMockContracts','batchSelftests'))
    report['unitTestSkipped']=sum(stages.get(k,{}).get('skippedTests',0) or 0 for k in
                                  ('nativeMockContracts','batchSelftests'))
    report['hasSafetyHold']=bool(failed)
    report['hasGameplayHold']=bool(stages['runtimeProof']['status'].startswith('HOLD_'))
    report['runtimeGatesMissingCount']=len(RUNTIME_GATES)
    report['nextRequiredCapability']='PROVE_ALT_STATS_AND_EPS_ORDER_ORIGIN_WITH_PASSIVE_LIVE_ADAPTER'
    report['safeChecksCompletedNotGameplayPass']=True
    report['holdStages']=failed
    report['status']='SAFE_READONLY_BATCH_COMPLETE_GAMEPLAY_HOLD' if not failed else 'READONLY_BATCH_SAFETY_HOLD'
    report['elapsedMs']=round((time.monotonic()-started)*1000)
    # A successful batch is never equivalent to a switch being authorized.
    return report, 0 if not failed else 3


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game',type=Path,default=Path(r'C:\Games\BG_EET_FOXX_NEW'))
    p.add_argument('--source-dir',type=Path,default=Path(__file__).resolve().parent)
    p.add_argument('--report-dir',type=Path,default=Path.home()/'Documents'/'BGXAI_LIVE_REPORTS')
    p.add_argument('--fresh-native',action='store_true',help='explicitly repeat native read-only compilation')
    args=p.parse_args(argv)
    out=args.report_dir.resolve()
    game=args.game.resolve()
    # Never save even a JSON report inside the game or its override folder.
    if out==game or game in out.parents:
        print('BGXAI AUTO BATCH STOP: report destination inside game',file=sys.stderr)
        return 3
    if out.is_symlink():
        print('BGXAI AUTO BATCH STOP: report folder is symlink',file=sys.stderr)
        return 3
    out.mkdir(parents=True,exist_ok=True)
    # Keep one report per run, no per-step artifacts; atomic publish.
    report,rc=run_batch(game,args.source_dir,out,args.fresh_native)
    target=out/('BGXAI_AUTO_BATCH_RO_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json')
    tmp=target.with_suffix('.tmp')
    try:
        if tmp.exists():
            raise Hold('CONFLICTING_TEMP_REPORT')
        with tmp.open('x',encoding='utf-8') as h:
            json.dump(report,h,ensure_ascii=False,indent=2)
            h.write('\n')
        os.replace(tmp,target)
    except (OSError,Hold) as e:
        print('BGXAI AUTO BATCH REPORT STOP: '+str(e),file=sys.stderr)
        return 3
    print('BGXAI AUTO BATCH '+report['status'])
    print('CHECKS='+str(report['stepCount'])+' MATRIX_CASES='+str(report['batchCaseCount'])+
          ' UNIT_TESTS='+str(report['unitTestCount']))
    print('NEW_GAME_ACTIONS=0 INSTALL=NO LIVE_NEW_WEAPON_AI=NO')
    print('GAMEPLAY_HOLD='+str(report['hasGameplayHold']).lower()+
          ' MISSING_PROOFS='+str(report['runtimeGatesMissingCount']))
    print('REPORT_FILE='+str(target))
    return rc

if __name__=='__main__':
    raise SystemExit(main())
