"""Real WeiDU v251 isolated BAF grammar + synthetic IDS compile; no EET installation.
Synthetic IDS validates layout only, not full SCS/EET symbol resolution.
"""
from pathlib import Path
import tempfile,urllib.request,zipfile,subprocess,hashlib,re,json,sys
ROOT=Path(__file__).parent
ASSET='WeiDU-Linux-251.zip'
URL='https://github.com/WeiDUorg/weidu/releases/download/v251.00/'+ASSET
EXPECTED_BYTES=2723764
BAF=ROOT/'BGX67_EARLY_GUARD.baf'

def run():
 with tempfile.TemporaryDirectory(prefix='BGX67_WEIDU_') as tmp:
  tmp=Path(tmp);z=tmp/ASSET
  with urllib.request.urlopen(URL,timeout=45) as res,z.open('wb') as fp:
   while v:=res.read(1024*256):fp.write(v)
  if z.stat().st_size!=EXPECTED_BYTES:raise RuntimeError('WeiDU official release size drift')
  with zipfile.ZipFile(z) as zf:
   c=[x for x in zf.namelist() if Path(x).name=='weidu']
   if len(c)!=1:raise RuntimeError('WeiDU binary missing')
   tool=tmp/'weidu';tool.write_bytes(zf.read(c[0]));tool.chmod(0o700)
  src=tmp/'BX67CHCK.baf';src.write_bytes(BAF.read_bytes())
  flags=['--nogame','--no-auto-tp2','--no-exit-pause','--noautoupdate',
     '--search-ids',str(ROOT/'ids'),'--search',str(ROOT/'ids'),'--script-style','BG2']
  check=subprocess.run([str(tool),*flags,'--parse-check','BAF',str(src)],cwd=tmp,
              capture_output=True,text=True,timeout=30)
  if check.returncode!=0 or 'successfully parsed as type [BAF]' not in check.stdout or 'NOT successfully parsed' in check.stdout:
   raise RuntimeError('BAF_GRAMMAR_FAILED\n'+check.stdout[-2000:]+check.stderr[-1000:])
  out=tmp/'out';out.mkdir()
  compile=subprocess.run([str(tool),*flags,'--out',str(out),str(src)],cwd=tmp,
             capture_output=True,text=True,timeout=30)
  compiled=list(out.rglob('*.bcs'))
  if not compiled:compiled=list(tmp.rglob('BX67CHCK.bcs'))
  if compile.returncode!=0 or len(compiled)!=1 or compiled[0].stat().st_size<100:
   raise RuntimeError('SYNTHETIC_BCS_COMPILE_FAILED\n'+compile.stdout[-2400:]+compile.stderr[-1000:])
  b=compiled[0].read_bytes()
  # 8 blocks: 2 cleanup, 6 bounded AttackReevaluate actions (134).
  crs=len(re.findall(rb'(?m)^(?:[0-9]+)?CR\r?$',b))
  ids=[int(x) for x in re.findall(rb'(?:^|\n)(?:[0-9]+)?AC\r?\n(-?[0-9]+)OB\r?\n',b)]
  if crs!=16 or ids.count(134)!=6:raise RuntimeError(f'BCS_STRUCTURE_MISMATCH crs={crs} attacks={ids.count(134)} all={ids}')
  # Validate the release two-override-file TP2 with the official WeiDU binary.
  from BGXAI67_INSTALL import TP2_TEXT
  tp2=tmp/'setup-BGX67.tp2';tp2.write_text(TP2_TEXT,encoding='utf-8',newline='\n')
  tp2check=subprocess.run([str(tool),'--nogame','--no-auto-tp2',
      '--no-exit-pause','--noautoupdate','--parse-check','TP2',str(tp2)],
      cwd=tmp,capture_output=True,text=True,timeout=30)
  if (tp2check.returncode!=0 or
      'successfully parsed as type [TP2]' not in tp2check.stdout or
      'NOT successfully parsed' in tp2check.stdout):
   raise RuntimeError('067_TP2_PARSE_FAILED\n'+tp2check.stdout[-1500:]+tp2check.stderr[-800:])
  return {'status':'WEIDU_251_BAF_PARSE_AND_SYNTHETIC_BCS_PASS','blocks':8,'bounded_attack_actions':6,'bcs_bytes':len(b),
          'bcs_sha256':hashlib.sha256(b).hexdigest(),'ids_fixture':'SYNTHETIC_SUBSET_NOT_GAME_EET',
          'game_modified':False,'official_tp2_parse':True,'weidu_sha256':hashlib.sha256(tool.read_bytes()).hexdigest()}
if __name__=='__main__':
 try:r=run();ok=True
 except Exception as e:r={'status':'FAILED','error':str(e)};ok=False
 print(json.dumps(r,indent=2));sys.exit(0 if ok else 1)
