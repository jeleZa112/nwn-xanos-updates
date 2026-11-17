# BG Voice RU 4.9.2: integrity-pinned local runtime with improved source discovery.
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

VERSION = '4.9.2-offline'


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

    def find_english(master, plan, errors):
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
        diagnostics['english_search'] = {'roots': [str(p) for p in roots],
                  'matched_ids': len(found), 'candidates': checked,
                  'sample': [str(found[s]) for s in sorted(found)[:8]]}
        print('EN REFERENCE SEARCH:', len(found), 'of', len(plan), '| roots:', len(roots), flush=True)
        return found

    def get_ref(sid, entry, en, master):
        for key in ('english_wav','en_wav','english_wav_path','original_wav',
                    'reference_wav_path','stable_reference_wav','reference_wav',
                    'stable_reference_path','source_wav'):
            value = entry.get(key)
            if not isinstance(value, str) or not value.lower().endswith('.wav'):
                continue
            p = Path(value)
            if not p.is_absolute():
                p = Path(master) / p
            if p.is_file() and _en_proof(p):
                return p
        alias = str(entry.get('stable_source_sound_id') or entry.get('english_sound_id') or sid).strip().upper()
        if alias.endswith('_EN'):
            alias = alias[:-3]
        return en.get(alias) or en.get(sid)

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

    scope['find_english'] = find_english
    scope['get_ref'] = get_ref
    scope['maybe_switch_to_installed_model_env'] = find_model_python


def main():
    launcher = Path(__file__).resolve()
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
