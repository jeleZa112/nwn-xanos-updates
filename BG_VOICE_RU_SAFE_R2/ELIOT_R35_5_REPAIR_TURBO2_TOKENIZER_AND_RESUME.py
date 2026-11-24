# -*- coding: utf-8 -*-
"""R35.5 one-time repair for absent RUAccent turbo2 tokenizer sidecars.

Never modifies installed BG_VOICE_UPDATE.cmd, master audio, game or other projects.
Only downloads missing, small official RUAccent tokenizer files in the existing R35 cache,
checks the real local tokenizer, then invokes existing R35 stress gate (and generation only
on gate PASS). Fail closed on unknown updater or failed/incomplete model inputs.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path.home() / 'Documents' / 'BG_VOICE_RU' / 'FULL_PRODUCTION'
UPDATER = Path.home() / 'Downloads' / 'BG_VOICE_RU_TTS_READY' / 'bg_voice_release_v2' / 'BG_VOICE_UPDATE.cmd'
PRIVATE_PY = ROOT / 'ELIOT_R35_TEXT_ONLY_VENV' / 'Scripts' / 'python.exe'
MODEL_ROOT = ROOT / 'ELIOT_R35_MOVIE_G08_DUAL_METHOD' / 'RUACCENT_MODELS'
TURBO = MODEL_ROOT / 'nn' / 'nn_omograph' / 'turbo2'
REPORT = ROOT / 'SEND_TO_CHATGPT_BG_VOICE_RU.zip'
EXPECTED_UPDATER_SHA256 = '08e290df36e9bf11758d764ddcab17ce6b9577698aad748ffdf54a9aaefd153f'
REPO = 'ruaccent/accentuator'
REVISION = '795cc4505324b9e0eaf54ebe792f3854a710e6ef'
FILES = {
    'added_tokens.json': (50_000, 'json'),
    'config.json': (300, 'json'),
    'merges.txt': (500_000, 'text'),
    'special_tokens_map.json': (100, 'json'),
    'tokenizer.json': (4_000_000, 'json'),
    'tokenizer_config.json': (200, 'json'),
    'vocab.json': (1_000_000, 'json'),
}
ONNX_SIZE = 359_306_923  # measured in user R35.2 Windows run
EMBED = (
    'import sys;p=sys.argv.pop(1);t=open(p,encoding="utf-8-sig").read();'
    'exec(compile(t.split(chr(10)+"#BGVOICE_PYTHON_START"+chr(10),1)[1],'
    'p,"exec"),{"__name__":"__main__","__file__":p})'
)


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def check_path(path: Path) -> None:
    for p in [path, *path.parents]:
        if p.is_symlink():
            raise RuntimeError('SYMLINK_HOLD ' + str(p))


def sidecar_good(name: str) -> bool:
    lower_size, kind = FILES[name]
    f = TURBO / name
    if not f.is_file() or f.stat().st_size < lower_size:
        return False
    if kind == 'json':
        with f.open('r', encoding='utf-8') as inp:
            obj = json.load(inp)
        if not isinstance(obj, dict):
            raise RuntimeError('INVALID_SIDE_CAR_JSON ' + name)
    return True


def inspect() -> list[str]:
    if os.name != 'nt' or sys.version_info[:2] != (3, 11):
        raise RuntimeError('REQUIRES_WIN10_PY311')
    for p in (UPDATER, PRIVATE_PY, ROOT, MODEL_ROOT, TURBO, REPORT):
        check_path(p)
    if not UPDATER.is_file() or not PRIVATE_PY.is_file() or not REPORT.is_file():
        raise RuntimeError('EXPECTED_UPDATER_PRIVATE_VENV_OR_REPORT_MISSING')
    installed_sha = sha_file(UPDATER)
    if installed_sha != EXPECTED_UPDATER_SHA256:
        raise RuntimeError('UNKNOWN_UPDATE_CMD_SHA_HOLD ' + installed_sha)
    onnx = TURBO / 'model.onnx'
    if not onnx.is_file() or onnx.stat().st_size != ONNX_SIZE:
        raise RuntimeError('RUACCENT_TURBO2_ONNX_NOT_PREVIOUSLY_VERIFIED_HOLD')
    missing = [name for name in FILES if not sidecar_good(name)]
    print('ELIOT_R35_5_EXACT_R35_1_ATTESTED', installed_sha, flush=True)
    print('ELIOT_R35_5_TURBO2_SIDE_CAR_MISSING', missing, flush=True)
    return missing


DOWNLOAD_WORKER = r'''
import os,sys,json
from pathlib import Path
from huggingface_hub import hf_hub_download
repo, revision, root, relname = sys.argv[1:5]
path = hf_hub_download(repo_id=repo, revision=revision, filename=relname,
                        local_dir=root, force_download=False, local_files_only=False)
print('ELIOT_R35_5_OFFICIAL_HF_FILE_READY', path, flush=True)
'''
TOKENIZER_WORKER = r'''
import sys
from transformers import AutoTokenizer
folder = sys.argv[1]
tok = AutoTokenizer.from_pretrained(folder, local_files_only=True)
encoded = tok('Не прошло и нескольких недель, как из Хребта Мира хлынули полчища гоблинов.')
ids = encoded['input_ids']
if not isinstance(ids,list) or len(ids)<8:raise RuntimeError('TOKENIZER_RETURNED_TOO_FEW_IDS')
print('ELIOT_R35_5_REAL_LOCAL_TOKENIZER_PASS',type(tok).__name__,'tokens',len(ids),flush=True)
'''


def private_call(code: str, args: list[str], env: dict[str,str], timeout: int = 240) -> None:
    result = subprocess.run([str(PRIVATE_PY), '-u', '-c', code, *args],
                            env=env, timeout=timeout, check=False)
    if result.returncode != 0:
        raise RuntimeError('PRIVATE_WORKER_HOLD_RC_' + str(result.returncode))


def repair(missing: list[str]) -> None:
    if not missing:
        print('ELIOT_R35_5_EXISTING_SIDE_CARS_ALREADY_COMPLETE', flush=True)
        return
    env = os.environ.copy()
    env['HF_HUB_OFFLINE'] = '0'
    env['HF_HUB_DISABLE_XET'] = '1'
    env['HF_HUB_DISABLE_TELEMETRY'] = '1'
    env['HF_HUB_ETAG_TIMEOUT'] = '30'
    env['HF_HUB_DOWNLOAD_TIMEOUT'] = '180'
    env['HF_HOME'] = str(ROOT / 'ELIOT_R35_MOVIE_G08_DUAL_METHOD' / 'HF')
    print('ELIOT_R35_5_FETCH_ONLY_MISSING_TOKENIZER_FILES', len(missing),
          'official Hugging Face pinned revision', REVISION, flush=True)
    for name in missing:
        f = TURBO / name
        if f.exists() and f.stat().st_size > 0:
            # Do not overwrite even partially existing assets without an explicit backup.
            # The prior logs show missing, not truncated, tokenizer sidecars.
            raise RuntimeError('PARTIAL_SIDECAR_NEEDS_SEPARATE_BACKUP_HOLD ' + name)
        rel = 'nn/nn_omograph/turbo2/' + name
        private_call(DOWNLOAD_WORKER, [REPO, REVISION, str(MODEL_ROOT), rel], env, timeout=300)
        if not sidecar_good(name):
            raise RuntimeError('DOWNLOADED_SIDE_CAR_INVALID ' + name)
    if any(not sidecar_good(name) for name in FILES):
        raise RuntimeError('INCOMPLETE_TOKENIZER_ASSETS_HOLD')
    print('ELIOT_R35_5_TOKENIZER_SIDE_CARS_COMPLETE', flush=True)


def run_updater(flag: str) -> None:
    if sha_file(UPDATER) != EXPECTED_UPDATER_SHA256:
        raise RuntimeError('UPDATER_CHANGED_DURING_RECOVERY_HOLD')
    env = os.environ.copy()
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    env['HF_HUB_DISABLE_TELEMETRY'] = '1'
    result = subprocess.run([sys.executable, '-u', '-c', EMBED, str(UPDATER), flag],
                            env=env, check=False)
    if result.returncode != 0:
        raise RuntimeError('R35_1_' + flag.replace('-', '_') + '_HOLD_RC_' + str(result.returncode))


def main() -> int:
    missing = inspect()
    repair(missing)
    env = os.environ.copy()
    env['HF_HUB_OFFLINE'] = '1'
    private_call(TOKENIZER_WORKER, [str(TURBO)], env, timeout=180)
    for flag in ('--eliot-r35-selftest', '--eliot-r35-preflight', '--eliot-r35-stresscheck'):
        print('ELIOT_R35_5_CONTINUE', flag, flush=True)
        run_updater(flag)
    print('ELIOT_R35_5_STRESS_GATE_PASS: generating limited G08 pilot', flush=True)
    run_updater('--eliot-r35-generate')
    print('ELIOT_R35_5_SUCCESS: check unchanged old WAV and new G08 candidates in report', flush=True)
    return 0

if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print('ELIOT_R35_5_INTERRUPTED: no unverified generation', flush=True)
        raise SystemExit(130)
    except Exception as exc:
        print('ELIOT_R35_5_HOLD', type(exc).__name__, str(exc)[:400], flush=True)
        raise SystemExit(2)
