# -*- coding: utf-8 -*-
"""BG Voice RU 3.5: Replace textual 'Ха!' with an original game laughter candidate.
Audio surgery only. Does not claim expressive TTS or alter existing voices.
"""
from pathlib import Path
import argparse, sys, hashlib
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = HERE / 'OUTPUT_LAUGH_35'
SOURCE_EN = ROOT / 'RVC_DATASETS' / 'IMOEN'
SOURCE_RU = ROOT / 'BG_RU_IMOEN_PROSODY_29' / 'OUTPUT'
# Coarse, auditionable time ranges selected from source waveforms.
# EN 06 opening is a 0.2s isolated vocal burst, followed by a silence.
# EN 77A has an isolated ~0.4s chuckle after the greeting.
PROFILES = {
    'IMOEN06_': {
        'en': 'IMOEN06_.wav', 'ru': 'IMOEN06__PARTS_29.wav',
        'laugh_start': 0.00, 'laugh_end': 0.225,
        'ru_front': (0.0, 0.0), 'ru_after': 1.06,
        'join_pause_ms': 90,
    },
    'IMOEN77A': {
        'en': 'IMOEN77A.wav', 'ru': 'IMOEN77A_PARTS_29.wav',
        'laugh_start': 2.42, 'laugh_end': 2.91,
        'ru_front': (0.0, 3.76), 'ru_after': 4.62,
        'join_pause_ms': 110,
    },
}

def read(path):
    a,sr = sf.read(str(path),dtype='float32',always_2d=True)
    if a.shape[0] == 0 or sr < 8000: raise ValueError('Invalid audio: '+str(path))
    return a.mean(axis=1),int(sr)

def resample(a,orig,target):
    if orig == target: return a
    from math import gcd
    g=gcd(orig,target)
    return resample_poly(a,target//g,orig//g).astype(np.float32)

def fade(a,sr,ms=10):
    a=a.copy()
    n=min(int(sr*ms/1000),len(a)//3)
    if n > 1:
        a[:n]*=np.linspace(0,1,n,dtype=np.float32)
        a[-n:]*=np.linspace(1,0,n,dtype=np.float32)
    return a

def get_path(source,name):
    p=source/name
    if not p.is_file():raise FileNotFoundError('Missing '+str(p))
    return p

def build_one(name,p,check_only=False):
    en_path=get_path(SOURCE_EN,p['en'])
    ru_path=get_path(SOURCE_RU,p['ru'])
    en,esr=read(en_path); ru,rsr=read(ru_path)
    for t in [p['laugh_start'],p['laugh_end']]:
        if t<0 or t>len(en)/esr:raise ValueError('English laugh crop outside recording')
    if not 0 < p['ru_after'] < len(ru)/rsr: raise ValueError('Russian trim outside recording')
    if check_only:
        print(name,'CHECK OK',round(len(en)/esr,2),'sec EN',round(len(ru)/rsr,2),'sec RU')
        return None
    laugh=fade(resample(en[int(p['laugh_start']*esr):int(p['laugh_end']*esr)],esr,rsr),rsr,10)
    if len(laugh)<.1*rsr:raise ValueError('English laugh too short')
    before=ru[int(p['ru_front'][0]*rsr):int(p['ru_front'][1]*rsr)]
    after=fade(ru[int(p['ru_after']*rsr):],rsr,8)
    silence=np.zeros(int(rsr*p['join_pause_ms']/1000),dtype=np.float32)
    if len(before):
        before=fade(before,rsr,8)
        result=np.concatenate([before,silence,laugh,silence,after])
    else:
        result=np.concatenate([silence,laugh,silence,after])
    peak=float(np.max(np.abs(result)))
    if not 0.0001<peak<1.2:raise ValueError('Bad audio level')
    if peak>.95:result*=.95/peak
    OUT.mkdir(exist_ok=True)
    dest=OUT/(name+'_EN_LAUGH_RU_PARTS_35.wav')
    if dest.exists():
        print('KEEP existing',dest)
        return dest
    temp=dest.with_suffix('.partial.wav')
    if temp.exists():raise FileExistsError('Partial output exists: '+str(temp))
    sf.write(str(temp),result,rsr,subtype='PCM_16')
    check,sr=read(temp)
    if sr!=rsr or len(check)!=len(result):raise ValueError('Readback mismatch')
    temp.rename(dest)
    print('DONE',dest.name,round(len(result)/rsr,2),'seconds', 'SHA256',hashlib.sha256(dest.read_bytes()).hexdigest())
    return dest

def main():
    ar=argparse.ArgumentParser();ar.add_argument('--check',action='store_true');args=ar.parse_args()
    for name,p in PROFILES.items():build_one(name,p,args.check)
    if args.check:return
    txt='''<!doctype html><html lang="ru"><meta charset="utf-8"><title>BG Voice RU 3.5: Real Laugh</title>
    <style>body{font:16px system-ui;max-width:800px;margin:30px auto;padding:20px}audio{display:block;width:100%;margin:10px 0}section{margin:12px 0;padding:14px;border:1px solid #ccc;border-radius:10px}</style>
    <h1>BG Voice RU 3.5: исходный смех вместо прочитанного «Ха!»</h1>
    <p>Это реальный аудиомонтаж, НЕ перенос эмоционального тембра. Сравни на слух, особенно отличается ли английский смех от русского тембра.</p>'''
    for key,p in PROFILES.items():
        txt+=f'<section><h3>{key}</h3><strong>Английский оригинал</strong><audio controls src="../RVC_DATASETS/IMOEN/{p["en"]}"></audio><strong>Русский PARTS 2.9</strong><audio controls src="../BG_RU_IMOEN_PROSODY_29/OUTPUT/{p["ru"]}"></audio><strong>Гибрид 3.5 со смехом</strong><audio controls src="OUTPUT_LAUGH_35/{key}_EN_LAUGH_RU_PARTS_35.wav"></audio></section>'
    txt+='</html>'
    (HERE/'LISTEN_LAUGH_35.html').write_text(txt,encoding='utf-8')
    print('OPEN',HERE/'LISTEN_LAUGH_35.html')

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('ERROR',repr(exc),file=sys.stderr);raise SystemExit(1)