"""BG Voice RU R3: strictly read-only Windows preparation inventory.

No model imports, no GPU, no network, no WAV generation, no writing files.
Intended for a future hook inside the existing BG_VOICE_UPDATE.cmd pipeline,
not a new updater or direct installer. Caller owns report packaging.
"""
from __future__ import annotations

from pathlib import Path
import hashlib
import json
import os
import sys

from bgvoice_safeguards_r2 import inspect_existing_bundle_readonly, inspect_report_readonly, file_sha256


def _status_file(p: Path) -> dict:
    if not p.is_file() or p.is_symlink():
        return {'status': 'HOLD_NOT_PRESENT_OR_LINK', 'path': str(p)}
    try:
        return {'status': 'EXISTS_READONLY_SHA256', 'path': str(p), 'bytes': p.stat().st_size,
                'sha256': file_sha256(p)}
    except OSError as exc:
        return {'status': 'HOLD_FILE_UNREADABLE', 'error': type(exc).__name__}


def inspect_voxcpm_install_readonly(python_exe: Path) -> dict:
    """Inspect files in the selected venv; never import/execute voxcpm."""
    site = python_exe.parent.parent / 'Lib' / 'site-packages'
    if not site.is_dir() or site.is_symlink():
        return {'status': 'HOLD_VOXCMP_SITE_PACKAGES_UNKNOWN', 'style_support': 'NOT_VERIFIED'}
    folder = site / 'voxcpm'
    if not folder.is_dir() or folder.is_symlink():
        return {'status': 'HOLD_VOXCMP_PACKAGE_ABSENT', 'style_support': 'NOT_VERIFIED'}
    files = []
    try:
        for path in sorted(folder.rglob('*.py')):
            if path.is_symlink() or not path.is_file():
                raise ValueError('VOXCPM_PACKAGE_SYMLINK_HOLD')
            if len(files) >= 40:
                raise ValueError('VOXCPM_MODULE_COUNT_EXCEEDED_HOLD')
            files.append({'relative_path': path.relative_to(folder).as_posix(),
                          'bytes': path.stat().st_size,
                          'sha256': file_sha256(path)})
    except (ValueError, OSError) as exc:
        return {'status': 'HOLD_VOXCPM_SOURCE_INSPECTION_ERROR', 'reason': str(exc),
                'style_support': 'NOT_VERIFIED'}
    return {'status': 'VOXCPM_SOURCE_INVENTORY_ONLY', 'style_support': 'NOT_VERIFIED',
            'python_modules': files,
            'warning': 'Source hashes alone cannot prove Style Control works at runtime'}


def probe_local_environment(*, updater_path: str | Path, model_root: str | Path,
                            python_venv: str | Path, report_path: str | Path,
                            include_model_hashes: bool = False,
                            max_model_files: int = 150) -> dict:
    """Return evidence, not proof that style control or production TTS works.

    Heavy SHA of 4.5GB model weights is opt-in; default only stat/sizes.
    Report can later be attached to the ONE existing ZIP via R3 transaction.
    """
    updater = Path(updater_path)
    model = Path(model_root)
    venv = Path(python_venv)
    report = Path(report_path)
    result = {
        'schema': 'BGVOICE_WINDOWS_PROBE_R3',
        'read_only': True,
        'windows_real_run': os.name == 'nt',
        'wrote_files': False,
        'executed_models': False,
        'model_inference': False,
        'style_control_supported': 'NOT_VERIFIED',
        'release_signature_trusted_key': 'NOT_CONFIGURED',
        'movie_tts_allowed': False,
        'game_write_allowed': False,
        'updater': _status_file(updater),
        'venv_python': _status_file(venv),
        'voxcpm_package': inspect_voxcpm_install_readonly(venv),
        'report': inspect_report_readonly(report),
        'model_inventory': None
    }
    if not model.is_dir() or model.is_symlink():
        result['model_inventory'] = {'status': 'HOLD_MODEL_DIRECTORY_MISSING'}
    elif include_model_hashes:
        result['model_inventory'] = inspect_existing_bundle_readonly(model, max_files=max_model_files)
    else:
        # Name and size only: enough to request exact pinset later, NOT validation.
        entries = []
        try:
            for p in sorted(model.rglob('*')):
                if p.is_symlink():
                    raise ValueError('MODEL_SYMLINK_PRESENT_HOLD')
                if p.is_file():
                    if len(entries) >= max_model_files:
                        raise ValueError('MODEL_FILE_COUNT_LIMIT_HOLD')
                    entries.append({'relative_path':p.relative_to(model).as_posix(),
                                    'bytes':p.stat().st_size})
            result['model_inventory'] = {'status': 'SIZE_INVENTORY_ONLY_NOT_SHA_VERIFIED', 'files':entries}
        except (OSError, ValueError) as exc:
            result['model_inventory'] = {'status':'HOLD_MODEL_INVENTORY_ERROR', 'reason':str(exc)}
    has_all = (result['updater']['status'] == 'EXISTS_READONLY_SHA256'
               and result['report']['status'] == 'REPORT_INTEGRITY_PASS_NOT_AUDIO_APPROVED'
               and result['model_inventory']['status'] not in
                    ('HOLD_MODEL_DIRECTORY_MISSING','HOLD_MODEL_INVENTORY_ERROR'))
    result['status'] = ('READONLY_EVIDENCE_COLLECTED_STILL_TTS_HOLD' if has_all
                        else 'READONLY_EVIDENCE_INCOMPLETE_HOLD')
    return result


def known_windows_paths(home: Path | None = None) -> dict:
    home = Path.home() if home is None else Path(home)
    return {
        'updater_path': home / 'Downloads' / 'BG_VOICE_RU_TTS_READY' / 'bg_voice_release_v2' / 'BG_VOICE_UPDATE.cmd',
        'model_root': Path('C:/BG_VOICE_RU_MASTER/08_VOXCPM2_ALL_CHARACTERS/EXPERIMENTAL_MODELS/Shtorm-VoxCPM2-RU_481ce51'),
        'python_venv': home / 'Downloads' / 'BG_VOICE_RU_KELDORN_EMOTION_CLONING_PILOT_V1' / 'BG_VOICE_RU_KELDORN_CLONE_PILOT' / '.venv' / 'Scripts' / 'python.exe',
        'report_path': home / 'Documents' / 'BG_VOICE_RU' / 'FULL_PRODUCTION' / 'SEND_TO_CHATGPT_BG_VOICE_RU.zip',
    }
