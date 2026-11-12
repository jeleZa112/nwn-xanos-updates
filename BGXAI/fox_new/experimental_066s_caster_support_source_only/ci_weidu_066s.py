"""Real WeiDU v251 isolated BAF grammar + synthetic IDS compile; no EET installation.
Synthetic IDS validates layout only, not full SCS/EET symbol resolution.
"""
from pathlib import Path
import tempfile,urllib.request,zipfile,subprocess,hashlib,re,json,sys
ROOT=Path(__file__).parent
ASSET='WeiDU-Linux-251.zip'
URL='https://github.com/WeiDUorg/weidu/releases/download/v251.00/'+ASSET
EXPECTED_BYTES=2723764
BAF=ROOT/'BGX66_CASTER_RECEIVER_SOURCE_ONLY.baf'

def run():
 with tempfile.TemporaryDirectory(prefix='BGX66S_WEIDU_') as tmp:
  tmp=Path(tmp);z=tmp/ASSET
  with urllib.request.urlopen(URL,timeout=45) as res,z.open('wb') as fp:
   while v:=res.read(1024*256):fp.write(v)
  if z.stat().st_size!=EXPECTED_BYTES:raise RuntimeError('WeiDU official release size drift')
  with zipfile.ZipFile(z) as zf:
   c=[x for x in zf.namelist() if Path(x).name=='weidu']
   if len(c)!=1:raise RuntimeError('WeiDU binary missing')
   tool=tmp/'weidu';tool.write_bytes(zf.read(c[0]));tool.chmod(0o700)
  src=tmp/'BX66SCHK.baf';src.write_bytes(BAF.read_bytes())
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
  if not compiled:compiled=list(tmp.rglob('BX66SCHK.bcs'))
  if compile.returncode!=0 or len(compiled)!=1 or compiled[0].stat().st_size<100:
   raise RuntimeError('SYNTHETIC_BCS_COMPILE_FAILED\n'+compile.stdout[-2400:]+compile.stderr[-1000:])
  b=compiled[0].read_bytes()
  # 11 blocks, compiled 7 Spell actions at action opcode 31.
  crs=len(re.findall(rb'(?m)^(?:[0-9]+)?CR\r?$',b))
  ids=[int(x) for x in re.findall(rb'(?:^|\n)(?:[0-9]+)?AC\r?\n(-?[0-9]+)OB\r?\n',b)]
  if crs!=22 or ids.count(31)!=7:raise RuntimeError(f'BCS_STRUCTURE_MISMATCH crs={crs} spells={ids.count(31)} all={ids}')
  return {'status':'WEIDU_251_BAF_PARSE_AND_SYNTHETIC_BCS_PASS','blocks':11,'spell_actions':7,'bcs_bytes':len(b),
          'bcs_sha256':hashlib.sha256(b).hexdigest(),'ids_fixture':'SYNTHETIC_SUBSET_NOT_GAME_EET',
          'game_modified':False,'weidu_sha256':hashlib.sha256(tool.read_bytes()).hexdigest()}
if __name__=='__main__':
 try:r=run();ok=True
 except Exception as e:r={'status':'FAILED','error':str(e)};ok=False
 print(json.dumps(r,indent=2));sys.exit(0 if ok else 1)
