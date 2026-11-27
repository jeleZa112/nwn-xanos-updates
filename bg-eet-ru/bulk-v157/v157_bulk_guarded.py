"""BG_EET_RU v157: one-CMD guarded batch: 10 exact TLK edits; 10 banter edits SOURCE HOLD.

External state/backup only, pinned source bytes, fail-closed. No game files are
changed by preflight/status. Installation requires interactive exact approval.
"""
from __future__ import annotations
import base64, csv, hashlib, io, json, os, shutil, struct, subprocess, sys, time, uuid, zlib
from pathlib import Path

SCHEMA='BG_EET_RU_V157_ONE_BATCH_GUARDED_V1'
MANIFEST_B64='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'
MANIFEST=json.loads(zlib.decompress(base64.b64decode(MANIFEST_B64)).decode('utf-8'))
TLKS=('dialog.tlk','dialogf.tlk')
IDS=(216190,227151,227254,227304,231440,276225,276226,276227,276240,315861)
ENTRY=26
HDR=18
MAX_TLK=220_000_000
MAX_TXT=8192
INSTALL_TOKEN='INSTALL_BG_EET_RU_BULK_10_TLK_EXACT'
ROLLBACK_TOKEN='ROLLBACK_BG_EET_RU_BULK_10_TLK_EXACT'

class Hold(RuntimeError): pass

def digest(b):return hashlib.sha256(b).hexdigest()
def file_sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for v in iter(lambda:f.read(1<<20),b''):h.update(v)
 return h.hexdigest()

def check_file(path, game=None):
 if path.is_symlink() or not path.is_file():raise Hold('FILE_UNSAFE_OR_MISSING:'+path.name)
 if game is not None and not path.resolve().is_relative_to(game.resolve()):raise Hold('FILE_OUTSIDE_GAME:'+path.name)

def load_tlk(data):
 if not HDR<=len(data)<=MAX_TLK or data[:8]!=b'TLK V1  ':raise Hold('TLK_HEADER_OR_SIZE')
 n,start=struct.unpack_from('<II',data,10)
 if not 0<n<=10000000 or not HDR+ENTRY*n<=start<=len(data):raise Hold('TLK_TABLE_LAYOUT')
 return n,start

def row_text(data,idx,n,start):
 if idx<0 or idx>=n:raise Hold('STRREF_OUT_OF_RANGE')
 off=HDR+ENTRY*idx
 flag=struct.unpack_from('<H',data,off)[0]
 begin,size=struct.unpack_from('<II',data,off+18)
 if not flag&1 or size<1 or begin+size>len(data)-start:raise Hold('TLK_STRING_BOUNDS')
 return data[start+begin:start+begin+size]

def prepare_tlk(data,name):
 if name not in TLKS:raise Hold('BAD_TARGET_NAME')
 expected=MANIFEST['expected_source_tlk_sha256'][name]
 if digest(data)!=expected:raise Hold('TLK_SHA_DRIFT:'+name)
 n,start=load_tlk(data)
 changes=MANIFEST['tlk_editorial_changes']
 if len(changes)!=10 or tuple(sorted(row['strref'] for row in changes))!=IDS:raise Hold('MANIFEST_SCOPE_DRIFT')
 out=bytearray(data);tail=len(data)-start
 for row in sorted(changes,key=lambda x:x['strref']):
  idx=row['strref'];old=row['existing_ru_exact'].encode('utf-8');new=row['proposed_ru_exact'].encode('utf-8')
  if not (0<len(old)<=MAX_TXT and 0<len(new)<=MAX_TXT) or b'\x00' in old or b'\x00' in new:raise Hold('BAD_EDITORIAL_TEXT')
  if old==new or digest(old)!=row['old_utf8_sha256'] or digest(new)!=row['new_utf8_sha256']:raise Hold('EDITORIAL_CONTENT_DRIFT')
  if row_text(data,idx,n,start)!=old:raise Hold('TARGET_TEXT_DRIFT:'+str(idx))
  if tail+len(new)>=1<<32:raise Hold('TLK_OFFSET_OVERFLOW')
  struct.pack_into('<II',out,HDR+ENTRY*idx+18,tail,len(new));out+=new;tail+=len(new)
 dst=bytes(out)
 if load_tlk(dst)!=(n,start):raise Hold('LAYOUT_CHANGED')
 check=bytearray(dst[:len(data)])
 for row in changes:
  idx=row['strref'];pos=HDR+ENTRY*idx+18
  if row_text(dst,idx,n,start)!=row['proposed_ru_exact'].encode('utf-8'):raise Hold('TEXT_POSTCHECK_FAILED')
  check[pos:pos+8]=data[pos:pos+8]
 if bytes(check)!=data:raise Hold('NON_TARGET_BYTES_CHANGED')
 return dst

def game_paths(game):
 game=Path(game).resolve()
 if not (game/'chitin.key').is_file():raise Hold('GAME_NOT_FOUND')
 root=game/'lang'/'ru_RU'
 paths={name:root/name for name in TLKS}
 for p in paths.values():check_file(p,game)
 return paths

def state_file(workdir):return Path(workdir)/'BG_EET_RU_V157_BULK_STATE.json'
def backup_root(workdir):return Path(workdir)/'BG_EET_RU_V157_SAFE_BACKUPS'

def external_guard(game,workdir):
 game=Path(game).resolve();workdir=Path(workdir).resolve()
 if workdir.is_relative_to(game) or game.is_relative_to(workdir):raise Hold('BACKUP_MUST_BE_EXTERNAL')
 if workdir.is_symlink():raise Hold('EXTERNAL_WORKDIR_SYMLINK')
 return game,workdir

def read_state(workdir):
 p=state_file(workdir)
 if not p.exists():return None
 check_file(p)
 try:s=json.loads(p.read_text(encoding='utf-8'))
 except Exception as e:raise Hold('STATE_UNREADABLE') from e
 if s.get('schema')!=SCHEMA or s.get('status') not in ('PREPARING','INSTALLED','RECOVERY_REQUIRED','ROLLED_BACK'):
  raise Hold('UNKNOWN_STATE')
 return s

def write_atomic_json(path,obj):
 stage=path.with_name(path.name+'.stage')
 if stage.exists() or stage.is_symlink():raise Hold('STALE_STATE_STAGE')
 body=(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode('utf-8')
 try:
  with stage.open('xb') as f:f.write(body);f.flush();os.fsync(f.fileno())
  os.replace(stage,path)
 finally:
  if stage.exists():stage.unlink()

def no_running_game():
 if os.name!='nt':raise Hold('WINDOWS_ONLY_GAME_WRITE')
 p=subprocess.run(['tasklist','/FO','CSV','/NH'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=12)
 if p.returncode!=0:raise Hold('TASKLIST_FAILED')
 txt=p.stdout.decode('utf-8','replace')
 for row in csv.reader(io.StringIO(txt)):
  if not row:continue
  image=row[0].strip().lower()
  if image in ('baldur.exe','infinityloader.exe','weidu.exe') or (image.startswith('setup-') and image.endswith('.exe')):
   raise Hold('CLOSE_GAME_AND_WEIDU_FIRST:'+image)

def checked_wei(game):
 p=game/'WeiDU.log';check_file(p,game)
 return file_sha(p)

def read_sources(game):
 paths=game_paths(game)
 data={name:paths[name].read_bytes() for name in TLKS}
 candidates={name:prepare_tlk(data[name],name) for name in TLKS}
 return paths,data,candidates

def base_report():
 return {'schema':SCHEMA,'status':'UNTESTED','game_files_written':0,'reviewed_total':338,
         'reviewed_banter':300,'reviewed_tlk':38,'prepared_edits':20,
         'tlk_installable_edits':10,'banter_editorial_edits':10,
         'banter_install':'HOLD_NO_LIVE_VISIBILITY_OR_CURRENT_DLG_BASELINE',
         'banter_source_sha256':MANIFEST['ru_tra_source_sha256'],
         'banter_candidate_sha256':MANIFEST['ru_tra_revised_sha256'],
         'single_updater':True,'new_updater_created':False,'gameplay_verified':False}

def preflight(game,workdir):
 game,workdir=external_guard(game,workdir)
 report=base_report();state=read_state(workdir)
 if state and state['status'] in ('PREPARING','INSTALLED','RECOVERY_REQUIRED'):
  report.update(status='HOLD_STATE_ALREADY_ACTIVE',state=state['status']);return report
 try:
  paths,src,dst=read_sources(game)
  report.update(status='V157_DUAL_TLK_EXACT_PREFLIGHT_PASS',
       files={name:{'path':str(paths[name]),'source_sha256':digest(src[name]),'candidate_sha256':digest(dst[name]),'source_bytes':len(src[name]),'candidate_bytes':len(dst[name])} for name in TLKS},
       weidu_log_sha256=checked_wei(game),
       note='NO_GAME_WRITE; 10 TLK entries staged in RAM only; 10 banter edits still HOLD')
 except Exception as exc:
  report.update(status='V157_SAFE_STOP',reason=type(exc).__name__+':'+str(exc)[:180])
 return report

def store_backup(root,name,data):
 path=root/name
 if path.exists() or path.is_symlink():raise Hold('BACKUP_EXISTS')
 with path.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
 if file_sha(path)!=digest(data):raise Hold('BACKUP_VERIFICATION_FAILED')
 return path

def swap(path,data,expected_current=None):
 if expected_current is not None and file_sha(path)!=expected_current:raise Hold('FILE_CHANGED_BEFORE_SWAP:'+path.name)
 stage=path.with_name(path.name+'.v157_stage')
 if stage.exists() or stage.is_symlink():raise Hold('GAME_STAGE_EXISTS:'+path.name)
 try:
  with stage.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
  if file_sha(stage)!=digest(data):raise Hold('STAGED_SHA_MISMATCH')
  os.replace(stage,path)
  if file_sha(path)!=digest(data):raise Hold('POST_SWAP_SHA_MISMATCH')
 finally:
  if stage.exists():stage.unlink()

def approved(token):
 try:typed=input('Type '+token+' exactly (ENTER cancels): ').strip()
 except EOFError:typed=''
 if typed!=token:raise Hold('TYPED_APPROVAL_REQUIRED')

def install(game,workdir):
 game,workdir=external_guard(game,workdir)
 no_running_game()
 pre=preflight(game,workdir)
 if pre['status']!='V157_DUAL_TLK_EXACT_PREFLIGHT_PASS':return pre
 approved(INSTALL_TOKEN)
 no_running_game()
 if read_state(workdir) and read_state(workdir)['status']!='ROLLED_BACK':raise Hold('ACTIVE_STATE_RACE')
 paths,src,dst=read_sources(game)
 if checked_wei(game)!=pre['weidu_log_sha256']:raise Hold('WEIDU_CHANGED_SINCE_PREFLIGHT')
 for name in TLKS:
  if digest(src[name])!=pre['files'][name]['source_sha256'] or digest(dst[name])!=pre['files'][name]['candidate_sha256']:raise Hold('SOURCE_CHANGED_SINCE_APPROVAL')
 workdir.mkdir(parents=True,exist_ok=True)
 root=backup_root(workdir);root.mkdir(exist_ok=True)
 if root.is_symlink():raise Hold('BACKUP_ROOT_SYMLINK')
 batch=root/('V157_'+time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())+'_'+uuid.uuid4().hex[:8]);batch.mkdir()
 backups={name:store_backup(batch,name,src[name]) for name in TLKS}
 state={'schema':SCHEMA,'status':'PREPARING','backup_dir':str(batch),'game_root':str(game),
        'weidu_sha256':pre['weidu_log_sha256'],
        'source_sha256':{name:digest(src[name]) for name in TLKS},
        'installed_sha256':{name:digest(dst[name]) for name in TLKS},
        'ui_sha256':file_sha(game/'override'/'UI.MENU') if (game/'override'/'UI.MENU').is_file() else None}
 st=state_file(workdir);write_atomic_json(st,state)
 changed=[]
 try:
  for name in TLKS:
   swap(paths[name],dst[name],digest(src[name]));changed.append(name)
  if checked_wei(game)!=state['weidu_sha256']:raise Hold('WEIDU_CHANGED_DURING_INSTALL')
  state['status']='INSTALLED';write_atomic_json(st,state)
 except BaseException as ex:
  try:
   for name in reversed(changed):
    if file_sha(paths[name])!=digest(dst[name]):raise Hold('POST_FAILURE_FILE_DRIFT')
    swap(paths[name],src[name],digest(dst[name]))
   state['status']='ROLLED_BACK';write_atomic_json(st,state)
  except BaseException:
   state['status']='RECOVERY_REQUIRED'
   try:write_atomic_json(st,state)
   except BaseException:pass
   raise Hold('PARTIAL_INSTALL_RECOVERY_REQUIRED') from ex
  raise
 rep=base_report();rep.update(status='V157_10_TLK_INSTALLED_AWAITING_GAMEPLAY',game_files_written=2,
        installed_strrefs=list(IDS),files={name:{'old_sha256':digest(src[name]),'new_sha256':digest(dst[name])} for name in TLKS},
        backup_dir=str(batch),banter_install='HOLD_NOT_INSTALLED')
 return rep

def rollback(game,workdir):
 game,workdir=external_guard(game,workdir)
 no_running_game();s=read_state(workdir)
 if not s or s['status']!='INSTALLED' or s['game_root']!=str(game):raise Hold('NO_LAST_INSTALLED_STATE')
 if checked_wei(game)!=s['weidu_sha256']:raise Hold('WEIDU_DRIFT_LAST_ONLY')
 ui=game/'override'/'UI.MENU'
 if (file_sha(ui) if ui.is_file() else None)!=s['ui_sha256']:raise Hold('UI_DRIFT_LAST_ONLY')
 path=Path(s['backup_dir'])
 if not path.resolve().is_relative_to(backup_root(workdir).resolve()) or path.is_symlink():raise Hold('BACKUP_PATH_UNSAFE')
 sources={};targets=game_paths(game)
 for name in TLKS:
  backup=path/name;check_file(backup)
  sources[name]=backup.read_bytes()
  if digest(sources[name])!=s['source_sha256'][name] or file_sha(targets[name])!=s['installed_sha256'][name]:raise Hold('ROLLBACK_LAST_ONLY_SHA_DRIFT')
 approved(ROLLBACK_TOKEN);no_running_game()
 for name in TLKS:
  if file_sha(targets[name])!=s['installed_sha256'][name]:raise Hold('ROLLBACK_RACE_DRIFT')
 replaced=[]
 try:
  for name in TLKS:
   swap(targets[name],sources[name],s['installed_sha256'][name]);replaced.append(name)
  s['status']='ROLLED_BACK';write_atomic_json(state_file(workdir),s)
 except BaseException as ex:
  s['status']='RECOVERY_REQUIRED';write_atomic_json(state_file(workdir),s)
  raise Hold('ROLLBACK_RECOVERY_REQUIRED') from ex
 rep=base_report();rep.update(status='V157_GUARDED_ROLLBACK_DONE',game_files_written=2,restored_strrefs=list(IDS))
 return rep

def status(game,workdir):
 game,workdir=external_guard(game,workdir)
 s=read_state(workdir);rep=base_report()
 if not s:return {**rep,'status':'V157_NOT_INSTALLED'}
 rep.update(status='V157_'+s['status'],backup_dir=s.get('backup_dir'))
 if s['status']=='INSTALLED':
  try:
   paths=game_paths(game)
   rep['current_tlk_sha_matches']={name:file_sha(paths[name])==s['installed_sha256'][name] for name in TLKS}
   rep['weidu_unchanged']=checked_wei(game)==s['weidu_sha256']
  except Exception as ex:rep.update(reason=str(ex)[:160])
 return rep

def run(game,workdir,mode='preflight'):
 try:
  if mode=='preflight':return preflight(game,workdir)
  if mode=='status':return status(game,workdir)
  if mode=='install':return install(game,workdir)
  if mode=='rollback':return rollback(game,workdir)
  raise Hold('UNKNOWN_MODE')
 except Exception as ex:
  r=base_report();r.update(status='V157_SAFE_STOP',reason=type(ex).__name__+':'+str(ex)[:220],game_files_written='UNKNOWN_IF_EXCEPTION_AFTER_AUTHORIZED_WRITE' if mode in ('install','rollback') else 0)
  return r
