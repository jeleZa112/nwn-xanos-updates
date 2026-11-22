# BG Voice RU V70 remote 1.1.0: one CMD, one report, read-only blind A/B calibration.
from __future__ import annotations
import csv,hashlib,html,io,json,os,shutil,tempfile,wave,zipfile
from pathlib import Path,PureWindowsPath
VERSION='1.1.0'
PREFIX='V70/QA_NEXT12/'
ROOT='C:\\BG_VOICE_RU_MASTER\\08_VOXCPM2_ALL_CHARACTERS\\RUSSIAN_WAV_TWO_VERSIONS\\'

def _bytes(path,expected):
    if not path.lower().startswith(ROOT.lower()) or '..' in PureWindowsPath(path).parts:
        return None,'SOURCE_PATH_HOLD'
    try:
        p=Path(path)
        if not p.is_file() or p.stat().st_size>12*1024*1024:return None,'MISSING_OR_TOO_LARGE_HOLD'
        b=p.read_bytes()
        if hashlib.sha256(b).hexdigest()!=expected.lower():return None,'SHA_MISMATCH_HOLD'
        with wave.open(io.BytesIO(b)) as w:
            if (w.getnchannels(),w.getsampwidth(),w.getframerate())!=(1,2,48000) or not w.getnframes():
                return None,'PCM_FORMAT_HOLD'
        return b,'OK'
    except (OSError,ValueError,EOFError,wave.Error):return None,'BAD_WAV_HOLD'

def _csv(rows,fields):
    out=io.StringIO(newline='');w=csv.DictWriter(out,fieldnames=fields,extrasaction='ignore')
    w.writeheader();w.writerows(rows);return out.getvalue().encode('utf-8-sig')

def _make(report):
    with zipfile.ZipFile(report) as z:
        if z.testzip():raise ValueError('REPORT_CRC_HOLD')
        payload=z.read('V70/V70_ORIGINAL_PAYLOAD_SHA256_VERIFIED.zip')
        status=json.loads(z.read('V70/STATUS.json'))
        if hashlib.sha256(payload).hexdigest()!=status['payload_sha256']:
            raise ValueError('PAYLOAD_SHA_HOLD')
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        if z.testzip():raise ValueError('EMBEDDED_CRC_HOLD')
        rows=list(csv.DictReader(io.StringIO(z.read('06_CALIBRATION_REVIEW_96.csv').decode('utf-8-sig'))))
        protected={r['sound_id'] for r in csv.DictReader(io.StringIO(z.read('05_USER_LOCKS_AND_CHOICES.csv').decode('utf-8-sig')))}
    if len(rows)!=96:raise ValueError('CALIBRATION_COUNT_HOLD')
    selected=[r for r in rows if r['priority_lane']=='ACTING_REVIEW_298' and r['sound_id'] not in protected][:12]
    if len(selected)!=12:raise ValueError('ACTING_12_HOLD')
    assets={};index=[];mapping={};total=0
    for r in selected:
        sid=r['sound_id'];s,ss=_bytes(r['stable_source'],r['stable_sha256_v55'])
        p,ps=_bytes(r['per_line_source'],r['per_line_sha256_v55'])
        state='READY_FOR_HUMAN_AB' if s is not None and p is not None else 'HOLD_SOURCE'
        if state=='READY_FOR_HUMAN_AB' and total+len(s)+len(p)>75*1024*1024:state='HOLD_PACKET_LIMIT'
        names={'A':'','B':''};modes={'A':'HOLD','B':'HOLD'}
        if state=='READY_FOR_HUMAN_AB':
            if hashlib.sha256(sid.encode('ascii')).digest()[0]&1:
                files={'A':p,'B':s};modes={'A':'PER_LINE','B':'STABLE'}
            else:
                files={'A':s,'B':p};modes={'A':'STABLE','B':'PER_LINE'}
            for k,b in files.items():
                names[k]=PREFIX+k+'/'+sid+'.wav';assets[names[k]]=b
            total+=len(s)+len(p)
        index.append({'sound_id':sid,'character':r['character'],
                      'english_text':r['english_text'],
                      'russian_game_text_UNCHANGED':r['russian_game_text_UNCHANGED'],
                      'status':state,'detail':ss+';'+ps,'wav_A':names['A'],'wav_B':names['B']})
        mapping[sid]=modes
    fields=['sound_id','character','english_text','russian_game_text_UNCHANGED','status','detail','wav_A','wav_B']
    assets[PREFIX+'INDEX.csv']=_csv(index,fields)
    assets[PREFIX+'PRIVATE_AB_MAPPING.json']=json.dumps(mapping,ensure_ascii=False,indent=2).encode('utf-8')
    assets[PREFIX+'STATUS.json']=json.dumps({'schema':'BGVOICE_V70_ACTING_AB12',
        'version':VERSION,'attempted':12,'ready':sum(x['status']=='READY_FOR_HUMAN_AB' for x in index),
        'hold':sum(x['status']!='READY_FOR_HUMAN_AB' for x in index),
        'game_approvals':0,'source_wavs_modified':False,'voice_synthesis':False,
        'requires_human_voice_acting_review':True},ensure_ascii=False,indent=2).encode('utf-8')
    webpage=['<!doctype html><html lang="ru"><meta charset="utf-8"><title>BG Voice RU A/B</title>',
        '<style>body{font:16px system-ui;max-width:900px;margin:auto}section{border-bottom:1px solid #aaa;padding:15px}audio{width:360px;max-width:100%}</style>',
        '<h1>12 актёрских сравнений — Stable / Per_line</h1><p>Сначала голос, полнота, эмоция. Ударения проверяем после выбора. Ничего не устанавливается в игру.</p>']
    for r in index:
        sid=html.escape(r['sound_id']);webpage.extend(['<section><h3>',sid,' — ',html.escape(r['character']),'</h3>',
            '<p>RU: ',html.escape(r['russian_game_text_UNCHANGED']),'</p>',
            '<p>EN: ',html.escape(r['english_text']),'</p>'])
        if r['status']=='READY_FOR_HUMAN_AB':
            for k in ('A','B'):
                webpage.extend(['<p>',k,': <audio controls preload="none" src="',k,'/',sid,'.wav"></audio></p>'])
            for val in ('A','B','HOLD'):
                webpage.extend(['<label><input name="',sid,'" type="radio" value="',val,'">',val,'</label> '])
        else:webpage.extend(['<p>HOLD: ',html.escape(r['detail']),'</p>'])
        webpage.append('</section>')
    webpage.extend(['<p>Распакуйте всю папку QA_NEXT12, затем откройте эту страницу.</p>',
        '<button onclick="go()">Скопировать решения</button><script>function go(){let s="sound_id,choice";',
        'for(let id of ',json.dumps([r['sound_id'] for r in index]),'){' ,
        'let x=document.querySelector(`input[name="${id}"]:checked`);if(x)s+="\\n"+id+","+x.value}',
        'navigator.clipboard.writeText(s).then(()=>alert("Скопировано"),()=>prompt("Скопируйте",s))}</script></html>'])
    assets[PREFIX+'OPEN_REVIEW.html']=''.join(webpage).encode('utf-8')
    return assets

def _put(report,assets):
    fd,tmp=tempfile.mkstemp(prefix='V70_QA_',suffix='.zip.pending',dir=report.parent);os.close(fd)
    try:
        with zipfile.ZipFile(report) as old,zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED,compresslevel=4,allowZip64=True) as out:
            if old.testzip():raise ValueError('REPORT_CRC_HOLD')
            for meta in old.infolist():
                if meta.filename.startswith(PREFIX):continue
                if meta.filename.endswith('/'):out.writestr(meta,b'')
                else:
                    with old.open(meta) as src,out.open(meta,'w',force_zip64=True) as dst:
                        shutil.copyfileobj(src,dst,1024*1024)
            for name,b in sorted(assets.items()):out.writestr(name,b)
        with zipfile.ZipFile(tmp) as z:
            if z.testzip() or len(z.namelist())!=len(set(z.namelist())):raise ValueError('NEW_REPORT_CRC_HOLD')
        os.replace(tmp,report)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def selftest():
    assert VERSION=='1.1.0' and _csv([{'id':'1'}],['id']).endswith(b'1\r\n')
    print('BG_VOICE_V70_CORE_SELFTEST_PASS');return 0

def run(host,*,mode='stage',limit=None):
    if set(host)!={'run_local'} or not callable(host['run_local']):raise RuntimeError('BAD_V70_HOST')
    if mode not in ('stage','calibration') or (limit is not None and (type(limit)!=int or not 1<=limit<=420)):
        raise RuntimeError('BAD_V70_MODE')
    result=host['run_local'](mode=mode,limit=limit)
    try:
        report=Path.home()/'Documents'/'BG_VOICE_RU'/'FULL_PRODUCTION'/'SEND_TO_CHATGPT_BG_VOICE_RU.zip'
        if not report.is_file():raise FileNotFoundError('ONE_REPORT_NOT_FOUND')
        assets=_make(report);_put(report,assets)
        status=json.loads(assets[PREFIX+'STATUS.json'])
        print('V70_ACTING_AB12:',status['ready'],'ready,',status['hold'],'HOLD; one report only',flush=True)
    except Exception as exc:
        print('V70_ACTING_AB12_HOLD; existing V70 preserved:',type(exc).__name__,str(exc)[:120],flush=True)
    return result

if __name__=='__main__':raise SystemExit(selftest())