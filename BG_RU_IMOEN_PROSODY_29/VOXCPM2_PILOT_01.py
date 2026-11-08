# -*- coding: utf-8 -*-
"""BG Voice RU: independent VoxCPM2 expressive cloning pilot for IMOEN77A.

Output is separate. No game edits, model overwrites, filters or paid services.
Requires VoxCPM2 in a separate Windows venv. --check runs without it.
"""
from __future__ import annotations
import argparse
import csv
import html
import json
import math
import os
from pathlib import Path
import sys
import time
import wave

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = HERE / 'VOXCPM2_PILOT_01_OUTPUT'
PART_OUT = OUT / 'PARTS'
LOG = OUT / 'VOXCPM2_PILOT_01.log'
TARGET = 'IMOEN77A'
FULL = ('Приятно снова встретить тебя, маленький братец. Ха! '
        'Мне нравится так тебя называть. Ну, ты готов идти? '
        'Мне бы хотелось путешествовать с тобой, если можно.')
PARTS = (
    ('greeting', 'Приятно снова встретить тебя, маленький братец.',
     'A bright, youthful, lively female voice, warmly excited and playful, natural conversational speed.'),
    ('tease', 'Мне нравится так тебя называть.',
     'A bright, teasing, mischievous young female voice, smiling, lightly amused, sparkling articulation.'),
    ('question', 'Ну, ты готов идти?',
     'A curious, playful, energetic question, clear rising intonation, youthful ringing female voice.'),
    ('request', 'Мне бы хотелось путешествовать с тобой, если можно.',
     'A warm, sincere female voice, softly hopeful but still lively and clear, natural intimate speech.'),
)
ENG_CANDIDATES = (
    ROOT / 'RVC_DATASETS' / 'IMOEN' / 'IMOEN77A.wav',
    HERE / 'ORIGINAL_EN' / 'IMOEN77A.wav',
)
REFS = (
    ROOT / 'BG_RU_RASK75_CLONE_24' / 'RASK75_LONG.wav',
    ROOT / 'BG_RU_IMOEN_BATCH_26' / 'RASK75_LONG.wav',
    ROOT / 'BG_RU_RASK75_CLONE_24' / 'RASK01_SHORT.wav',
)
PREVIOUS = HERE / 'OUTPUT_LAUGH_35' / 'IMOEN77A_EN_LAUGH_RU_PARTS_35.wav'
LAUGH_A, LAUGH_B = 2.42, 2.91


def log(message):
    OUT.mkdir(parents=True, exist_ok=True)
    line = time.strftime('%H:%M:%S') + ' ' + message
    print(line, flush=True)
    with LOG.open('a', encoding='utf-8') as f:
        f.write(line + '\n')


def wav_duration(path):
    if not path.exists():
        return 0.
    try:
        with wave.open(str(path), 'rb') as w:
            return w.getnframes() / w.getframerate()
    except (OSError, ValueError, wave.Error, ZeroDivisionError):
        return 0.


def first_valid(items, min_seconds, max_seconds):
    for p in items:
        dur = wav_duration(p)
        if min_seconds <= dur <= max_seconds:
            return p
    return None


def manifest_check():
    p = ROOT / 'VOICE_MANIFEST.csv'
    if not p.is_file():
        raise RuntimeError('VOICE_MANIFEST.csv not found in ' + str(ROOT))
    with p.open(encoding='utf-8-sig', newline='') as f:
        found = [r for r in csv.DictReader(f)
                 if (r.get('Resource') or '').strip().upper() == TARGET]
    if len(found) != 1 or (found[0].get('Character') or '').strip().upper() != 'IMOEN':
        raise RuntimeError('Unexpected manifest entry for ' + TARGET)
    value = (found[0].get('Russian_existing') or '').split(' | ')[0].strip()
    if value != FULL:
        raise RuntimeError('Russian text differs from verified manifest; no generated words will be guessed. Received: ' + repr(value))


def preflight():
    manifest_check()
    eng = first_valid(ENG_CANDIDATES, 8., 14.)
    ref = first_valid(REFS[:2], 15., 35.)
    if eng is None:
        raise RuntimeError('Missing English original IMOEN77A.wav in RVC_DATASETS/IMOEN')
    if ref is None:
        raise RuntimeError('Missing approved original RASK75_LONG.wav in existing Rask folders')
    if not 0 <= LAUGH_A < LAUGH_B <= wav_duration(eng):
        raise RuntimeError('Original laugh timing not within source')
    log('PREFLIGHT OK: English %.2fs, reference %.2fs. Approved voices untouched.' % (wav_duration(eng), wav_duration(ref)))
    try:
        import torch
        if torch.cuda.is_available():
            total = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            free, _ = torch.cuda.mem_get_info(0)
            log('GPU %s: total %.2f GiB, free %.2f GiB' % (torch.cuda.get_device_name(0), total, free / (1024**3)))
            if free / (1024**3) < 6.7:
                log('WARNING: Low free VRAM. Close games/OBS/browsers before generation; model may not fit 8GB.')
        else:
            log('WARNING: CUDA unavailable in this Python. Actual generation will stop rather than run on CPU.')
    except ImportError:
        log('Torch not installed for check; will verify CUDA before generation.')
    return eng, ref


def write_wav_no_overwrite(path, audio, sr):
    import numpy as np
    import soundfile as sf
    a = np.asarray(audio, dtype='float32').squeeze()
    if a.ndim != 1 or not np.isfinite(a).all() or not 16000 <= int(sr) <= 96000:
        raise RuntimeError('Unexpected VoxCPM audio data')
    sec = len(a) / sr
    if not 0.35 < sec < 60.0 or float(np.max(abs(a))) < 0.005:
        raise RuntimeError('VoxCPM produced silent/invalid duration audio')
    if path.exists():
        raise FileExistsError('Existing WAV preserved: ' + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    # Only protect against clipping. Never EQ, time stretch or synthesize rasp.
    peak = float(np.max(abs(a)))
    if peak > 0.99:
        a = a * (0.98 / peak)
    import io
    buff = io.BytesIO()
    sf.write(buff, a, int(sr), format='WAV', subtype='PCM_16')
    blob = buff.getvalue()
    with path.open('xb') as f:
        f.write(blob)
    if wav_duration(path) < 0.35:
        raise RuntimeError('Invalid WAV after saving ' + path.name)


def read_audio(path):
    import numpy as np
    import soundfile as sf
    data, sr = sf.read(str(path), dtype='float32', always_2d=True)
    if not data.size:
        raise RuntimeError('Empty audio ' + str(path))
    return np.mean(data, axis=1), int(sr)


def resample(x, input_sr, output_sr):
    from scipy.signal import resample_poly
    from math import gcd
    if input_sr == output_sr:
        return x
    g = gcd(input_sr, output_sr)
    return resample_poly(x, output_sr // g, input_sr // g).astype('float32')


def soft_fade(a, sr, milliseconds=12):
    import numpy as np
    x = a.copy()
    n = min(int(sr * milliseconds / 1000), len(x) // 3)
    if n > 2:
        x[:n] *= np.linspace(0, 1, n, dtype='float32')
        x[-n:] *= np.linspace(1, 0, n, dtype='float32')
    return x


def part_path(key):
    return PART_OUT / ('IMOEN77A_' + key.upper() + '_VOXCPM2_01.wav')


def combine(eng):
    import numpy as np
    output = OUT / 'IMOEN77A_EN_LAUGH_RU_VOXCPM2_01.wav'
    if wav_duration(output) > 1.:
        log('KEEP previous complete montage ' + output.name)
        return output
    segments = [read_audio(part_path(key)) for key, _, _ in PARTS]
    rate = segments[0][1]
    if any(sr != rate for _, sr in segments):
        raise RuntimeError('Model returned inconsistent sample rates')
    original, eng_sr = read_audio(eng)
    laugh = resample(original[int(LAUGH_A * eng_sr):int(LAUGH_B * eng_sr)], eng_sr, rate)
    if not 0.3 < len(laugh)/rate < 0.8:
        raise RuntimeError('Laugh extraction duration invalid')
    chunks = [soft_fade(v, rate) for v, _ in segments]
    silence = lambda ms: np.zeros(int(ms*rate/1000), dtype='float32')
    whole = np.concatenate([
        chunks[0], silence(130), soft_fade(laugh,rate,7), silence(90),
        chunks[1], silence(130), chunks[2], silence(160), chunks[3],
    ])
    write_wav_no_overwrite(output, whole, rate)
    log('MONTAGE OK %.2fs, original laugh preserved. No signal processing.' % wav_duration(output))
    return output


def html_report(eng, ref):
    out = OUT / 'LISTEN_VOXCPM2_01.html'
    from urllib.parse import quote
    clips = [
        ('English original IMOEN77A', eng),
        ('Previously approved 3.5 WAV (if present locally)', PREVIOUS),
        ('VoxCPM2: fresh Russian generation + original English laugh', OUT / 'IMOEN77A_EN_LAUGH_RU_VOXCPM2_01.wav'),
        ('Voice reference: Rask75 (not modified)', ref),
    ]
    parts=[]
    for key, text, style in PARTS:
        parts.append('<section><h3>'+html.escape(key)+' — '+html.escape(text)+'</h3><p>Direction: '+html.escape(style)+'</p>')
        p=part_path(key)
        if wav_duration(p) > 0.35:
            path=os.path.relpath(p,OUT).replace('\\','/')
            parts.append('<audio controls src="'+html.escape(path,quote=True)+'"></audio>')
        else:
            parts.append('<p>Not generated yet</p>')
        parts.append('</section>')
    rows=[]
    for label, p in clips:
        rows.append('<section><strong>'+html.escape(label)+'</strong>')
        if wav_duration(p)>0.35:
            path=os.path.relpath(p,OUT).replace('\\','/')
            rows.append('<audio controls src="'+html.escape(path,quote=True)+'"></audio>')
        else:
            rows.append('<p>Not available at this local path</p>')
        rows.append('</section>')
    out.write_text('<!DOCTYPE html><html lang="ru"><meta charset="utf-8"><title>BG Voice RU VoxCPM2 first pilot</title><style>body{font:16px system-ui;max-width:900px;margin:auto;padding:24px}section{margin:14px 0;padding:12px;border:1px solid #ccc;border-radius:8px}audio{display:block;width:100%;margin-top:8px}</style><h1>IMOEN77A: VoxCPM2 vs English</h1><p>Real model test only after local run. Different prompts per semantic clause; English laugh is an original clip. Not automatically exact English prosody. Check for Russian word repetition.</p>'+''.join(rows)+''.join(parts)+'</html>', encoding='utf-8')
    log('LISTEN '+str(out))


def generate(eng,ref):
    import torch
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA not available in the SEPARATE VoxCPM2 venv. Do not touch Qwen.')
    free_bytes, total = torch.cuda.mem_get_info(0)
    log('CUDA FREE %.2f GiB / %.2f GiB; VoxCPM2 needs approximately 8 GB VRAM' % (free_bytes/1024**3,total/1024**3))
    if free_bytes < 6.5*1024**3:
        raise RuntimeError('GPU free memory below 6.5 GiB; close games/OBS/browsers before retrying.')
    from voxcpm import VoxCPM
    os.environ.setdefault('HF_HUB_ETAG_TIMEOUT','120')
    os.environ.setdefault('HF_HUB_DOWNLOAD_TIMEOUT','300')
    log('Loading official openbmb/VoxCPM2 with optimize=False and load_denoiser=False')
    try:
        model=VoxCPM.from_pretrained('openbmb/VoxCPM2', device='cuda:0', optimize=False, load_denoiser=False)
    except torch.cuda.OutOfMemoryError as e:
        raise RuntimeError('RTX GPU OOM while LOADING VoxCPM2; Qwen untouched, do not retry without changes') from e
    model_rate=int(model.tts_model.sample_rate)
    for i, (key,text,style) in enumerate(PARTS):
        p=part_path(key)
        if p.exists() and wav_duration(p)>0.35:
            log('KEEP '+p.name)
            continue
        if p.exists():
            raise RuntimeError('Existing bad WAV preserved: '+str(p))
        torch.manual_seed(37001+i)
        log('GENERATE '+key+': '+text)
        try:
            with torch.inference_mode():
                wav=model.generate(text='('+style+') '+text,
                    reference_wav_path=str(ref), cfg_value=2.0,
                    inference_timesteps=10, normalize=False, denoise=False)
            write_wav_no_overwrite(p,wav,model_rate)
        except torch.cuda.OutOfMemoryError as e:
            raise RuntimeError('GPU memory exhausted on '+key+'; completed parts saved, no overwrites') from e
        log('DONE '+p.name+' %.2fs' % wav_duration(p))
        html_report(eng,ref)
    combine(eng)
    html_report(eng,ref)
    log('SUCCESS: pilot generated. Compare with original; review Russian pronunciation.')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--check',action='store_true',help='Only verify source text, WAV and GPU readiness, no download')
    parser.add_argument('--run',action='store_true',help='Download official VoxCPM2 if needed; generate separate WAV')
    args=parser.parse_args()
    if not (args.check or args.run):
        parser.error('Choose --check or --run')
    eng,ref=preflight()
    html_report(eng,ref)
    if args.check:
        return
    generate(eng,ref)

if __name__=='__main__':
    try:
        main()
    except Exception as exc:
        log('STOP '+repr(exc))
        raise SystemExit(1)