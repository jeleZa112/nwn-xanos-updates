# -*- coding: utf-8 -*-
"""BG Voice RU: collect existing English game WAVs for three RUTUBE MP4s.

Standard Python only. No pip, no ffmpeg, no Pillow, no VPN dependency,
no game file changes or TTS generation. Outputs one ZIP for upload to ChatGPT.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
from pathlib import Path
import re
import sys
import wave
import zipfile

CATS = {'IMOEN': ('Имоуэн', 131), 'XZARR': ('Ксар', 41), 'MONTR': ('Монтарон', 39)}
VALID = re.compile(r'^(IMOEN|XZARR|MONTR)[A-Z0-9_]*$', re.I)
BLOCK = ('RASK', 'GENERAT', 'OUTPUT', 'BATCH', 'PARTS', 'PROSODY', 'RVC_',
         'TEST', '_RU', '_EN_', 'REFERENCE', 'VOXCPM', 'EMOTION', 'STYLE',
         'RENDER', 'COMPAR', 'CLONE')


def good_resource(path):
    p = Path(str(path).replace('\\', '/'))
    if p.suffix.lower() != '.wav':
        return None
    stem = p.stem.upper()
    if not VALID.fullmatch(stem) or any(x in stem for x in BLOCK):
        return None
    return next(((code, stem) for code in CATS if stem.startswith(code)), None)


def collect(root):
    candidates = []
    paths = [
        'BG_RU_FULL_17/ORIGINAL_EN', 'ORIGINAL_EN',
        'BG_RU_FULL_17/EN_ORIGINAL', 'ORIGINAL_WAV', 'ORIGINALS_EN',
        'BG_RU_FULL_17/ORIGINAL_WAV', 'BG_RU_FULL_17', 'RVC_DATASETS'
    ]
    for rel in paths:
        d = root / rel
        if not d.is_dir():
            continue
        for p in sorted(d.rglob('*')):
            if not p.is_file() or p.suffix.lower() != '.wav':
                continue
            identity = good_resource(p.name)
            if not identity:
                continue
            part = '/' + '/'.join(x.upper() for x in p.relative_to(root).parts) + '/'
            if any(t in part for t in ('/OUTPUT/', '/PARTS/', '/RASK/', '/QWEN/', '/SYNTH/', '/CONVERT/')):
                continue
            priority = 0 if 'ORIGINAL' in str(d).upper() or rel == 'BG_RU_FULL_17' else 3
            candidates.append((priority, identity, p, 'file'))

    packs = [root/'BG_VOICE_RU_VOICE_TRAIN_2_0.zip',
             root/'BG_VOICE_RU_VOICE_TRAIN_2_0'/'BG_VOICE_RU_VOICE_TRAIN_2_0.zip',
             root.parent/'BG_VOICE_RU_VOICE_TRAIN_2_0.zip',
             root/'IMOEN.zip', root.parent/'IMOEN.zip']
    seen = set()
    for pack in packs:
        if not pack.is_file() or pack.resolve() in seen:
            continue
        seen.add(pack.resolve())
        try:
            with zipfile.ZipFile(pack) as z:
                for name in z.namelist():
                    identity = good_resource(name)
                    if identity:
                        priority = 1 if 'VOICE_TRAIN' in pack.name.upper() else 4
                        candidates.append((priority, identity, (pack, name), 'zip'))
        except (OSError, zipfile.BadZipFile) as e:
            print('WARNING: bad archive:', pack, repr(e), flush=True)
    chosen = {}
    for priority, identity, source, kind in sorted(candidates, key=lambda x: (x[0], str(x[2]))):
        chosen.setdefault(identity, (source, kind))
    return {code: [(name, *chosen[(c, name)]) for c, name in sorted(chosen) if c == code] for code in CATS}


def read_bytes(source, kind):
    if kind == 'zip':
        with zipfile.ZipFile(source[0]) as z:
            return z.read(source[1])
    return source.read_bytes()


def probe_wav(blob):
    try:
        with wave.open(io.BytesIO(blob), 'rb') as w:
            duration = w.getnframes() / w.getframerate()
            return round(duration, 4), f'{w.getframerate()}/{w.getnchannels()}ch/{w.getsampwidth()*8}bit'
    except (OSError, ValueError, wave.Error, ZeroDivisionError):
        return '', 'unverified WAV encoding'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parent.parent)
    args = p.parse_args()
    root = args.root.resolve()
    print('PROJECT:', root, flush=True)
    if not (root/'VOICE_MANIFEST.csv').exists():
        raise RuntimeError('VOICE_MANIFEST.csv missing. Extract tool into BG_RU_IMOEN_PROSODY_29 inside bg_voice_release_v2.')
    records = collect(root)
    outdir = root/'BG_RU_RUTUBE_3_CHARACTERS_44'/'UPLOAD_SOURCES'
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir/'BG_VOICE_RU_3_CHARACTERS_EN_WAV_FOR_MP4.zip'
    if out.exists():
        raise RuntimeError('Archive already exists and was NOT overwritten: ' + str(out))
    count = 0
    csvrows = []
    with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as z:
        for code, (friendly, total) in CATS.items():
            lines = records[code]
            print(f'{friendly}: {len(lines)} WAV found; target accounting {total}', flush=True)
            if len(lines) < total:
                print('  Missing source files are not invented. Originals stay unchanged.', flush=True)
            for i, (name, source, kind) in enumerate(lines, 1):
                raw = read_bytes(source, kind)
                seconds, fmt = probe_wav(raw)
                if not raw[:4] == b'RIFF' or raw[8:12] != b'WAVE':
                    print('  SKIP not RIFF/WAVE:', name, flush=True)
                    continue
                dest = f'{code}/{name}.wav'
                z.writestr(dest, raw)
                csvrows.append((code, i, name, seconds, fmt, hashlib.sha256(raw).hexdigest(), dest))
                count += 1
            print(f'  packed {sum(r[0] == code for r in csvrows)} WAV', flush=True)
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(['character', 'order', 'resource', 'duration_seconds', 'format', 'sha256', 'archive_name'])
        writer.writerows(csvrows)
        z.writestr('ORIGINALS_MANIFEST.csv', '\ufeff' + buf.getvalue())
        z.writestr('READ_ME_RU.txt',
            'Английские оригиналы BG Voice RU. Без обработки и новой генерации.\n'
            'Архив создан локально стандартным Python без FFmpeg и pip.\n'
            'Отправьте этот ZIP в ChatGPT, чтобы собрать три MP4 для RUTUBE с паузами 3 секунды.\n'
            'Количество файлов может быть меньше проектного учёта: отсутствующие WAV не восстановлены.\n')
    with zipfile.ZipFile(out) as z:
        if z.testzip():
            raise RuntimeError('ZIP CRC validation failed')
        if len([n for n in z.namelist() if n.endswith('.wav')]) != count:
            raise RuntimeError('Bad ZIP count')
    print(f'SUCCESS: {count} real original WAV, ZIP {out.stat().st_size/1048576:.2f} MiB', flush=True)
    print('FILE:', out, flush=True)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print('ERROR:', type(exc).__name__, str(exc), flush=True)
        sys.exit(1)