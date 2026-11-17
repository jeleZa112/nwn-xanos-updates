# BG Voice RU 4.9.8: integrity-pinned local runtime with improved source discovery.
# The launcher, all original audio, existing decisions and voice models are immutable.
from __future__ import annotations
from pathlib import Path
import importlib.util
import json
import os
import re
import sqlite3
import subprocess
import sys
import zipfile

VERSION = '4.9.8-offline'


def _en_proof(path: Path) -> bool:
    parts = [part.lower() for part in path.parts]
    if 'russian_wav_two_versions' in parts or any(part in ('ru', 'russian_wav', 'voice_repair', 'redo') for part in parts):
        return False
    stem = path.stem.lower()
    return (stem.endswith('_en') or any(part in ('en_reference_wav', 'english_wav', 'en_wav', 'en_wavs',
              '01_english_wav', 'original_en', 'en_originals', 'originals_en') or
              ('english' in part and 'russian' not in part) for part in parts))


def _project_roots(master: Path, work: Path):
    home = Path.home()
    downloads = home / 'Downloads'
    roots = [master, work, master / 'EN_REFERENCE_WAV', master / 'ENGLISH_WAV',
             master / '02_ENGLISH_MP4', home / 'Documents' / 'BG_VOICE_RU',
             downloads / 'BG_VOICE_RU_STRESS_CHECKER_V02',
             downloads / 'BG_VOICE_RU_PRIMARY_CUE_AUDIO_QA_V2_READY']
    if os.environ.get('BG_VOICE_EN_ROOT'):
        roots.insert(0, Path(os.environ['BG_VOICE_EN_ROOT']))
    try:
        roots.extend(p for p in downloads.iterdir() if p.is_dir() and
                     p.name.upper().startswith(('BG_VOICE_RU_', 'BG_VOT_', 'EN_REFERENCE_')))
    except OSError:
        pass
    unique = []
    seen = set()
    for root in roots:
        try:
            key = str(root.resolve()).casefold()
            if root.is_dir() and key not in seen:
                seen.add(key)
                unique.append(root)
        except OSError:
            pass
    return unique


def _patch_runtime(scope: dict, launcher: Path, diagnostics: dict):
    old_walk = scope['bounded_walk']
    sid_pattern = scope['SID_RE']
    analyzer_has_diagnostics = str(scope.get('VERSION','')).startswith('4.8')

    def find_english(master, plan, errors, work=None):
        ids = set(plan)
        for row in plan.values():
            for key in ('stable_source_sound_id', 'english_sound_id', 'sound_id'):
                value = str(row.get(key) or '').strip().upper()
                if value.endswith('_EN'):
                    value = value[:-3]
                if sid_pattern.fullmatch(value):
                    ids.add(value)
        found = {}
        roots = _project_roots(Path(master), launcher.parent)
        visited = set()
        checked = 0
        for base in roots:
            for path in old_walk(base, max_depth=10):
                if path.suffix.lower() != '.wav' or not _en_proof(path):
                    continue
                sid = path.stem.upper()
                if sid.endswith('_EN'):
                    sid = sid[:-3]
                if sid not in ids or not sid_pattern.fullmatch(sid):
                    continue
                try:
                    unique = str(path.resolve()).casefold()
                except OSError:
                    continue
                if unique in visited:
                    continue
                visited.add(unique)
                checked += 1
                current = found.get(sid)
                if current is None:
                    found[sid] = path
                elif 'en_reference_wav' in [a.lower() for a in path.parts] and \
                        'en_reference_wav' not in [a.lower() for a in current.parts]:
                    found[sid] = path
        result = {'roots': [str(p) for p in roots],
                  'indexed': len(found), 'wav_candidates_scanned': checked, 'duplicate_candidates': 0,
                  'sample': [{'sound_id': s, 'path': str(found[s])} for s in sorted(found)[:8]]}
        diagnostics['english_search'] = result
        print('EN REFERENCE SEARCH:', len(found), 'of', len(plan), '| roots:', len(roots), flush=True)
        return (found, result) if analyzer_has_diagnostics else found

    def get_ref(sid, entry, en, master):
        # An English sample belonging to the same CHARACTER is not necessarily
        # the English original of this LINE.  Never silently substitute it.
        # Historical stable_source_sound_id is a voice seed, not a line ID.
        sid = str(sid).strip().upper()
        exact = en.get(sid)
        if exact is not None:
            return exact
        for key in ('english_wav','en_wav','english_wav_path','original_wav',
                    'reference_wav_path','stable_reference_wav','reference_wav',
                    'stable_reference_path','source_wav'):
            value = entry.get(key)
            if not isinstance(value, str) or not value.lower().endswith('.wav'):
                continue
            p = Path(value)
            if not p.is_absolute():
                p = Path(master) / p
            stem = p.stem.upper()
            if stem.endswith('_EN'):
                stem = stem[:-3]
            if stem == sid and p.is_file() and _en_proof(p):
                return p
        # No exact original: leave HOLD without a synthetic voice score.
        return None

    diagnostics['reference_matching_policy'] = 'STRICT_SAME_SOUND_ID_OR_HOLD'
    print('EN REFERENCE POLICY: strict same-sound-id; no voice-seed substitution',flush=True)

    def find_model_python(work, root):
        if os.name != 'nt' or os.environ.get('BG_VOICE_RU_ENV_SELECTED') == '1':
            return None
        names = ('torch', 'resemblyzer', 'speechbrain', 'faster_whisper', 'whisper')
        def rank(flags):
            return ((35 if flags.get('torch') and flags.get('resemblyzer') else 0) +
                    (30 if flags.get('torch') and flags.get('speechbrain') else 0) +
                    (10 if flags.get('faster_whisper') else 0) +
                    (9 if flags.get('whisper') else 0) +
                    (1 if flags.get('torch') else 0))
        current = {k: importlib.util.find_spec(k) is not None for k in names}
        best_score = rank(current)
        best = None
        checked = 0
        root = Path(root)
        master = root.parent if root.name.upper() == '08_VOXCPM2_ALL_CHARACTERS' else root
        dl = Path.home() / 'Downloads'
        sources = [Path(work), root, master, dl / 'BG_VOICE_RU_STRESS_CHECKER_V02',
                   dl / 'BG_VOICE_RU_TTS_READY',
                   dl / 'BG_VOICE_RU_KELDORN_EMOTION_CLONING_PILOT_V1']
        try:
            sources.extend(p for p in dl.iterdir() if p.is_dir() and p.name.upper().startswith('BG_VOICE_RU_'))
        except OSError:
            pass
        envnames = ('.venv', '.venv_speaker', '.venv_voxcpm2', '.venv_emotion',
                    '.venv_asr', 'venv', 'venv311', 'speaker_env', 'vox_env', 'voice_env')
        probe = ("import importlib.util,json; n=('torch','resemblyzer','speechbrain','faster_whisper','whisper');"
                 "print(json.dumps({k:importlib.util.find_spec(k) is not None for k in n}))")
        paths = set()
        for source in sources:
            if not source.is_dir():
                continue
            folders = [source]
            try:
                folders.extend(p for p in source.iterdir() if p.is_dir() and
                               p.name.lower() not in ('russian_wav_two_versions', 'en_reference_wav', 'node_modules'))
            except OSError:
                pass
            for folder in folders:
                for name in envnames:
                    path = folder / name / 'Scripts' / 'python.exe'
                    if path.is_file():
                        paths.add(str(path))
                if folder.name.lower() in envnames:
                    path = folder / 'Scripts' / 'python.exe'
                    if path.is_file():
                        paths.add(str(path))
        for path in sorted(paths):
            try:
                result = subprocess.run([path, '-c', probe], capture_output=True, text=True, timeout=12)
                checked += 1
                if result.returncode or not result.stdout.strip():
                    continue
                flags = json.loads(result.stdout.strip().splitlines()[-1])
                score = rank(flags)
                if score > best_score:
                    best, best_score = path, score
            except (OSError, subprocess.SubprocessError, ValueError, json.JSONDecodeError):
                continue
        diagnostics['python_env'] = {'checked': checked, 'selected': best or sys.executable,
                                     'current_modules': current, 'score': best_score}
        print('OFFLINE ENV SEARCH:', checked, '| chosen:', best or sys.executable, flush=True)
        if best is None:
            return None
        env = os.environ.copy()
        env['BG_VOICE_RU_ENV_SELECTED'] = '1'
        # Re-run the VERIFIED CACHED CORE in the selected interpreter, NOT the old
        # embedded 4.7.1 core. Otherwise all English discovery fixes are lost.
        loader = (
            "import sys,sqlite3,hashlib,pathlib; "
            "p=pathlib.Path(sys.argv.pop(1));v=sys.argv.pop(1); "
            "db=sqlite3.connect(str(p.parent/'BG_VOICE_RU_PROGRESS.sqlite3')); "
            "row=db.execute('select sha256,source from bgvoice_cached_engines where version=?',(v,)).fetchone(); "
            "db.close(); "
            "assert row is not None,'cached core not found'; "
            "assert hashlib.sha256(row[1]).hexdigest()==row[0],'cached core hash mismatch'; "
            "exec(compile(row[1].decode('utf-8-sig'),str(p),'exec'),"
            "{'__name__':'__main__','__file__':str(p)})"
        )
        current_version = VERSION.split('-')[0]
        return subprocess.call([best, '-c', loader, str(launcher), current_version, *sys.argv[1:]], env=env)

    # ECAPA on Windows: avoid SpeechBrain's default symlink collection without
    # requesting admin privileges, modifying SpeechBrain or changing WAV files.
    original_speaker = scope['Speaker']

    class WindowsCopySpeaker(original_speaker):
        def __init__(self, master):
            try:
                from speechbrain.utils.parameter_transfer import Pretrainer
                from speechbrain.utils.fetching import LocalStrategy
                from speechbrain.inference.classifiers import EncoderClassifier
            except (ImportError, AttributeError):
                super().__init__(master)
                return
            import inspect
            original_collect = Pretrainer.collect_files
            original_hparams = EncoderClassifier.from_hparams
            own_method = 'from_hparams' in EncoderClassifier.__dict__
            original_hparams_descriptor = inspect.getattr_static(EncoderClassifier, 'from_hparams')

            def load_direct_from_cache(*args, **kwargs):
                # Existing snapshot is the source.  Avoid making a collection
                # directory and never create links into the model cache.
                kwargs['savedir'] = None
                kwargs['local_strategy'] = LocalStrategy.COPY
                return original_hparams(*args, **kwargs)

            def collect_without_symlinks(pretrainer, *args, **kwargs):
                # SpeechBrain 1.0/1.1 collect_files positional args:
                # (default_source, local_strategy, fetch_config).
                args = list(args)
                if len(args) >= 2:
                    args[1] = LocalStrategy.COPY
                    kwargs.pop('local_strategy', None)
                else:
                    kwargs['local_strategy'] = LocalStrategy.COPY
                return original_collect(pretrainer, *args, **kwargs)

            Pretrainer.collect_files = collect_without_symlinks
            EncoderClassifier.from_hparams = staticmethod(load_direct_from_cache)
            try:
                super().__init__(master)
            finally:
                Pretrainer.collect_files = original_collect
                if own_method:
                    EncoderClassifier.from_hparams = original_hparams_descriptor
                else:
                    del EncoderClassifier.from_hparams

    scope['Speaker'] = WindowsCopySpeaker
    diagnostics['speaker_loader'] = 'speechbrain-ecapa-windows-local-copy-no-symlinks'
    scope['find_english'] = find_english
    scope['get_ref'] = get_ref
    scope['maybe_switch_to_installed_model_env'] = find_model_python


def _powershell_get(url: str, limit: int) -> bytes:
    """Use Windows PowerShell downloader when Python cannot reach GitHub."""
    import base64
    if not re.fullmatch(r'https://raw[.]githubusercontent[.]com/jeleZa112/nwn-xanos-updates/[A-Za-z0-9._/-]+', url):
        raise ValueError('Unapproved update address')
    script = ("$ErrorActionPreference='Stop';$t=[IO.Path]::GetTempFileName();"
              "try {Invoke-WebRequest -Uri '" + url + "' -OutFile $t -UseBasicParsing -TimeoutSec 12 -ErrorAction Stop;"
              "$a=[IO.File]::ReadAllBytes($t);"
              "if ($a.Length -gt " + str(limit) + ") {throw 'Oversize core'};"
              "[Console]::Write([Convert]::ToBase64String($a))}"
              "finally {Remove-Item -LiteralPath $t -Force -ErrorAction SilentlyContinue}")
    result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', script],
                            text=True, capture_output=True, timeout=25, check=False)
    if result.returncode != 0:
        raise OSError('PowerShell download failed: ' + result.stderr.strip()[-220:])
    payload = base64.b64decode(result.stdout.strip(), validate=True)
    if len(payload) > limit:
        raise ValueError('Update download exceeds limit')
    return payload


def _powershell_check_update(launcher: Path):
    """Cache future verified releases in SQLite; never change CMD or source WAVs."""
    import datetime as datetime
    import hashlib
    import sqlite3
    if os.name != 'nt' or os.environ.get('BG_VOICE_RU_OFFLINE','').lower() in ('1','true','yes'):
        return None
    dbfile = launcher.parent / 'BG_VOICE_RU_PROGRESS.sqlite3'
    now = datetime.datetime.now(datetime.timezone.utc)
    with sqlite3.connect(str(dbfile), timeout=20) as db:
        db.execute('pragma busy_timeout=20000')
        db.execute("create table if not exists bgvoice_update_status "
                   "(slot integer primary key, last_checked text not null, last_result text not null)")
        db.execute("create table if not exists bgvoice_cached_engines "
                   "(version text primary key, sha256 text not null, source blob not null, at_utc text not null)")
        row = db.execute('select last_checked from bgvoice_update_status where slot=2').fetchone()
        force = os.environ.get('BG_VOICE_FORCE_UPDATE','').lower() in ('1','true','yes')
        if row and not force:
            try:
                if (now-datetime.datetime.fromisoformat(row[0])).total_seconds() < 6*3600:
                    return None
            except (ValueError,TypeError):
                pass
    status = 'not_checked'
    new_source = None
    try:
        prefix = 'https://raw.githubusercontent.com/jeleZa112/nwn-xanos-updates/'
        manifest_raw = _powershell_get(prefix + 'bg-voice-ru/BG_VOICE_RUNTIME_MANIFEST.json', 8192)
        manifest = json.loads(manifest_raw.decode('utf-8'))
        version = str(manifest.get('version',''))
        commit = str(manifest.get('commit',''))
        digest = str(manifest.get('sha256','')).lower()
        if (manifest.get('project') != 'BG_VOICE_RU' or
            manifest.get('path') != 'BG_VOICE_CORE.py' or
            not re.fullmatch(r'[0-9a-f]{40}',commit) or
            not re.fullmatch(r'[0-9a-f]{64}',digest) or
            not re.fullmatch(r'4\.(?:9|[1-9][0-9]+)\.[0-9]+',version)):
            raise ValueError('Invalid update manifest')
        def ver(t):
            return tuple(int(n) for n in t.split('.'))
        if ver(version) <= ver(VERSION.split('-')[0]):
            status = 'up_to_date_'+VERSION
        else:
            raw = _powershell_get(prefix+commit+'/BG_VOICE_CORE.py',300000)
            if hashlib.sha256(raw).hexdigest() != digest:
                raise ValueError('Update SHA256 mismatch')
            source = raw.decode('utf-8-sig')
            compile(source, '<bg_voice_next_core>', 'exec')
            child = ("import sys; p=sys.argv.pop(1); b=sys.stdin.buffer.read();"
                     "exec(compile(b,'<bg_voice_next_core>','exec'),"
                     "{'__name__':'__main__','__file__':p})")
            env = os.environ.copy()
            env['BG_VOICE_RU_OFFLINE'] = '1'
            result = subprocess.run([sys.executable, '-c', child, str(launcher), '--self-test'],
                                    input=raw, capture_output=True, timeout=30, env=env)
            if result.returncode or b'SELF_TEST_OK' not in result.stdout:
                raise ValueError('Update self-test failed')
            with sqlite3.connect(str(dbfile),timeout=20) as db:
                db.execute('insert or replace into bgvoice_cached_engines values(?,?,?,?)',
                           (version,digest,raw,now.isoformat()))
                db.commit()
            status = 'updated_to_'+version
            new_source = source
    except Exception as exc:
        status = 'offline_fallback_'+type(exc).__name__+': '+str(exc)[:200]
    try:
        with sqlite3.connect(str(dbfile),timeout=20) as db:
            db.execute('insert or replace into bgvoice_update_status values(2,?,?)',
                       (now.isoformat(),status))
            db.commit()
    except (OSError,sqlite3.Error):
        pass
    print('AUTO UPDATE POWERSHELL:',status,flush=True)
    return new_source



# The optional ASR-only runner is embedded in the SHA-pinned cached core;
# no additional Python scripts are installed beside the permanent launcher.
def _init_bgvoice_asr_496():
    import base64, hashlib, zlib
    encoded = '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'
    source = zlib.decompress(base64.b64decode(encoded))
    if hashlib.sha256(source).hexdigest() != 'be98a22eb1942cbffc6de7abf6086ba3fdd7e4701f5bea1b87a7e544aaf556a4':
        raise RuntimeError('ASR 4.9.8 source SHA256 mismatch')
    source_code = source.decode('utf-8')
    if source_code.count('4.9.6') != 3:
        raise RuntimeError('ASR pinned-source version patch failed')
    source_code = source_code.replace('4.9.6', '4.9.8')
    exec(compile(source_code,'<BG_VOICE_ASR_497>','exec'), globals())

_init_bgvoice_asr_496()


def _asr_cuda_bootstrap():
    # Process-local DLL discovery; no installs, copies, or permanent PATH edits.
    if os.name != 'nt':
        return
    root = Path(os.environ.get('BG_VOICE_RU_ROOT',
                               r'C:\BG_VOICE_RU_MASTER\08_VOXCPM2_ALL_CHARACTERS'))
    bases = [
        Path(sys.prefix) / 'Lib' / 'site-packages',
        root / 'BG_VOICE_RU_AUTO_ASR_V1' / '.venv_asr' / 'Lib' / 'site-packages',
        root / 'BG_VOICE_RU_AUTO_ASR_V1' / 'BG_VOICE_RU_AUTO_ASR_V1' / '.venv_asr' / 'Lib' / 'site-packages',
        Path.home() / 'Downloads' / 'BG_VOICE_RU_AUTO_ASR_V1' / '.venv_asr' / 'Lib' / 'site-packages',
    ]
    override = os.environ.get('BG_VOICE_ASR_SITE_PACKAGES', '').strip()
    if override:
        bases.insert(0, Path(override))
    suffixes = (
        Path('nvidia/cublas/bin'), Path('ctranslate2'),
        Path('nvidia/cudnn/bin'), Path('nvidia/cuda_runtime/bin'),
        Path('torch/lib'),
    )
    required = ('cublas64_12.dll', 'cublasLt64_12.dll',
                'cudnn64_9.dll', 'cudart64_12.dll')
    folders = []
    found = set()
    visited = set()
    for base in bases:
        for suffix in suffixes:
            folder = base / suffix
            key = str(folder).casefold()
            if key in visited or not folder.is_dir():
                continue
            visited.add(key)
            present = [dll for dll in required if (folder / dll).is_file()]
            if present:
                folders.append(folder)
                found.update(present)
    if len(found) != len(required):
        print('ASR CUDA DLLS: {}/4 found; CPU fallback remains available'.format(len(found)),
              flush=True)
        return
    existing = os.environ.get('PATH', '')
    existing_parts = set(part.strip().casefold() for part in existing.split(os.pathsep))
    new = [str(folder) for folder in folders
           if str(folder).casefold() not in existing_parts]
    if new:
        os.environ['PATH'] = os.pathsep.join(new) + os.pathsep + existing
    print('ASR CUDA DLLS: 4/4 found; process-local search paths configured', flush=True)



# Versioned offline QA: merge historical metadata and 4.9.7 ASR without inference.
def _bgvoice_qa_report(launcher):
    import base64, hashlib, zlib
    blob = zlib.decompress(base64.b64decode('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'))
    if hashlib.sha256(blob).hexdigest() != '823670d4a08a8496628b37d15ed6314541a6e5fbfc82f9d34e138520426d450a':
        raise RuntimeError('BG Voice 4.9.8 QA integrity mismatch')
    scope = {'__name__':'bgvoice_qa_report_498'}
    exec(compile(blob.decode('utf-8'), '<bg_voice_qa_498>', 'exec'), scope)
    source = Path(launcher).read_text(encoding='utf-8-sig').split('\n#BGVOICE_PYTHON_START\n',1)[1]
    host = {'__name__':'bgvoice_qa_metadata_only', '__file__':str(launcher)}
    exec(compile(source,str(launcher),'exec'),host)
    with zipfile.ZipFile(Path(launcher).parent / 'SEND_TO_CHATGPT_BG_VOICE_RU.zip') as archive:
        previous = json.loads(archive.read('SUMMARY.json'))
    base = previous.get('voice_baseline', previous)
    root_text = str(base.get('root') or '').strip()
    if not root_text:
        raise RuntimeError('Original BG Voice project root not found in report summary')
    root = Path(root_text)
    if not root.is_dir():
        raise RuntimeError('Original BG Voice project folder is unavailable: '+root_text)
    master = root.parent if root.name.upper() == '08_VOXCPM2_ALL_CHARACTERS' else root
    errors = []
    plan, plan_path = host['plan_scan'](root,errors)
    manual, old_asr, conflicts, scanned = host['parse_meta'](master,Path(launcher).parent,errors)
    print('QA SOURCE: plan rows',len(plan),'legacy metadata ASR',len(old_asr),
          'files scanned',scanned,'metadata issues',len(errors),flush=True)
    status = scope['_make'](launcher,old_asr,plan)
    if status['asr_records_merged'] < 14412:
        print('QA NOTICE: historical ASR incomplete; see ASR_MISSING_QUEUE.csv',flush=True)
    return 0

def main():
    launcher = Path(__file__).resolve()
    next_version = _powershell_check_update(launcher)
    if next_version:
        scope_next = {'__name__':'__main__','__file__':str(launcher)}
        exec(compile(next_version, '<bg_voice_next_core>', 'exec'), scope_next)
        return 0
    if '--qa-only' in sys.argv:
        return _bgvoice_qa_report(launcher)
    asr_limit = _asr_options()
    if asr_limit is not None:
        _asr_cuda_bootstrap()
        return _asr_only(launcher,asr_limit)
    content = launcher.read_text(encoding='utf-8-sig')
    body = content.split('\n#BGVOICE_PYTHON_START\n', 1)[1]
    scope = {'__name__': 'bgvoice_embedded_runtime', '__file__': str(launcher)}
    exec(compile(body, str(launcher), 'exec'), scope)
    diagnostics = {'version': VERSION, 'root': str(launcher.parent)}
    _patch_runtime(scope, launcher, diagnostics)
    scope['VERSION'] = VERSION
    result = scope['main']()
    if result == 0 and '--self-test' not in sys.argv:
        report = launcher.parent / 'SEND_TO_CHATGPT_BG_VOICE_RU.zip'
        db_path = launcher.parent / 'BG_VOICE_RU_PROGRESS.sqlite3'
        try:
            with sqlite3.connect(str(db_path), timeout=5) as db:
                row = db.execute('select last_result,last_checked from bgvoice_update_status where slot=1').fetchone()
            diagnostics['update_result'] = row[0] if row else 'none'
            diagnostics['update_last_checked'] = row[1] if row else None
            diagnostics['original_wavs_modified'] = False
            if report.is_file():
                with zipfile.ZipFile(report, 'a', zipfile.ZIP_DEFLATED) as archive:
                    name = 'AUTO_UPDATE_STATUS.json'
                    if name not in archive.namelist():
                        archive.writestr(name, json.dumps(diagnostics, ensure_ascii=False, indent=2))
        except (OSError, sqlite3.Error, zipfile.BadZipFile) as err:
            print('AUTO UPDATE INFO: could not append diagnostic:', repr(err))
    return result


if __name__ == '__main__':
    sys.exit(main())
