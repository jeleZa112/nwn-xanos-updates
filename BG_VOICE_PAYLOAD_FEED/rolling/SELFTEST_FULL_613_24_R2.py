"""Offline synthetic full-coverage test only; does NOT synthesize real voices."""
import csv,hashlib,io,json,os,sys,tempfile,wave
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parent))
import BGVOICE_ROLLING_CONTINUATION as w

def wav(sid,mode):
    x=io.BytesIO(); seed=hashlib.sha256((sid+mode).encode()).digest()
    with wave.open(x,'wb') as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(48000)
        f.writeframes(bytes(seed[i%len(seed)] for i in range(3200)))
    return x.getvalue()

m, data=w._read_manifest(Path(__file__).parent)
assert len(data[w.CSV_613])==613 and len(data[w.CSV_QA24])==24
assert len(set(r['character'] for r in data[w.CSV_613]))==111
with tempfile.TemporaryDirectory(prefix='bgvoice_full_r2_') as tmp:
    root=Path(tmp); source=root/'RUSSIAN_WAV_TWO_VERSIONS'; output=root/'FULL_PRODUCTION'; payload=root/'PAYLOAD'; payload.mkdir()
    rows613=[dict(r) for r in data[w.CSV_613]]
    for row in rows613:
        sid=row['sound_id'];mode=row['mode'];b=wav(sid,mode);row['expected_sha256']=w.sha(b)
        path=source/row['character']/(sid+'__'+mode.lower()+'_RU.wav')
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b)
    rows24=[dict(r) for r in data[w.CSV_QA24]]
    for row in rows24:
        sid=row['sound_id'];char=row['character']
        for mode,field in [('STABLE','stable_sha256'),('PER_LINE','per_line_sha256')]:
            b=wav(sid,mode);row[field]=w.sha(b)
            path=source/char/(sid+'__'+mode.lower()+'_RU.wav')
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b)
    for name,rows in [(w.CSV_613,rows613),(w.CSV_QA24,rows24)]:
        (payload/name).write_bytes(w._as_csv(rows,list(rows[0])))
    mm=dict(m);mm['files']={name:{'sha256':w.sha((payload/name).read_bytes()),'bytes':(payload/name).stat().st_size} for name in (w.CSV_613,w.CSV_QA24)}
    (payload/'MANIFEST.json').write_text(json.dumps(mm,ensure_ascii=False),encoding='utf-8')
    a=w._run(payload,source,output,tests=True)
    assert a['stage_total']==613 and a['stage_status_counts']=={'STAGED_NOT_APPROVED':613}, a
    assert (a['qa24_ready'],a['qa24_hold'])==(24,0),a
    assert len(list((output/'VOICE_BACKED_SECOND_PASS').glob('*.wav')))==613
    assert len(list((output/'VOICE_AB_NEXT24'/'A').glob('*.wav')))==24
    assert len(list((output/'VOICE_AB_NEXT24'/'B').glob('*.wav')))==24
    assert a['game_modified'] is False and a['voice_and_emotion_human_approved']==0
    b=w._run(payload,source,output,tests=True)
    assert b['stage_status_counts']=={'REUSED_SHA_VERIFIED':613} and b['qa24_ready']==24,b
    # Failing single copied file MUST NOT replace it or stop the other 612.
    target=output/'VOICE_BACKED_SECOND_PASS'/(rows613[0]['sound_id']+'__'+rows613[0]['mode']+'__NOT_APPROVED.wav')
    target.write_bytes(b'CORRUPTED')
    c=w._run(payload,source,output,tests=True)
    assert c['stage_status_counts']=={'HOLD':1,'REUSED_SHA_VERIFIED':612},c
    assert target.read_bytes()==b'CORRUPTED'
    # Failing one source audio hash also proceeds with rest.
    source_path=source/rows613[1]['character']/(rows613[1]['sound_id']+'__'+rows613[1]['mode'].lower()+'_RU.wav')
    original=source_path.read_bytes();source_path.write_bytes(b'CORRUPTED SOURCE')
    d=w._run(payload,source,output,tests=True)
    assert d['stage_status_counts']=={'HOLD':2,'REUSED_SHA_VERIFIED':611},d
    assert source_path.read_bytes()==b'CORRUPTED SOURCE'
    source_path.write_bytes(original)
    # Concurrent actor creates destination after the preliminary check:
    # os.link must refuse with no overwrite (regression for former os.rename).
    race_dir=root/'race';race_dir.mkdir();race_dest=race_dir/'nooverwrite.wav';source_bytes=wav('RACE01','STABLE')
    real_link=os.link
    def race_link(src,dst):
        Path(dst).write_bytes(b'OTHER_WRITER')
        return real_link(src,dst)
    with patch.object(w.os,'link',race_link):
        try:w._write_once(race_dest,source_bytes);raise AssertionError('RACE OVERWROTE DESTINATION')
        except ValueError as exc:assert 'CONCURRENT_STAGE_TARGET_EXISTS' in str(exc)
    assert race_dest.read_bytes()==b'OTHER_WRITER'
    # Child folder symlink rejection prevents source/target path redirection.
    linkfolder=root/'symlink';linkfolder.symlink_to(source, target_is_directory=True)
    try:w._safe_bytes(linkfolder/'notfound.wav','0'*64);raise AssertionError('symlink accepted')
    except ValueError as exc:assert 'SYMLINK' in str(exc)
    # The present manifest self-integrity is fixed and all row IDs remain unique.
    assert len({r['sound_id'] for r in rows613})==613
    assert len({r['sound_id'] for r in rows24})==24
print('FULL_R2_PASS: 613 staged, 24 AB ready; 613 reused; corrupt staged HOLD+612 reused; source SHA mismatch HOLD+611 reused; concurrent overwrite forbidden; symlink rejected; originals protected')