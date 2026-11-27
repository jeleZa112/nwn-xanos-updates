"""BG_EET_RU v159: 16 verified Russian editorial TLK revisions, one existing CMD only.

External state/backup only, pinned source bytes, fail-closed. No game files are
changed by preflight/status. Installation requires interactive exact approval.
"""
from __future__ import annotations
import base64, csv, hashlib, io, json, os, shutil, struct, subprocess, sys, time, uuid, zlib
from pathlib import Path

SCHEMA='BG_EET_RU_V159_EDITORIAL_BATCH_GUARDED_V1'
MANIFEST_B64='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'
MANIFEST=json.loads(zlib.decompress(base64.b64decode(MANIFEST_B64)).decode('utf-8'))
TLKS=('dialog.tlk','dialogf.tlk')
IDS=(25215, 32143, 39516, 39521, 70538, 100348, 100349, 224302, 225370, 226679, 231205, 232220, 232221, 310921, 358950, 359859)
ENTRY=26
HDR=18
MAX_TLK=220_000_000
MAX_TXT=8192
INSTALL_TOKEN='INSTALL_BG_EET_RU_BULK_16_TLK_EXACT'
ROLLBACK_TOKEN='ROLLBACK_BG_EET_RU_BULK_16_TLK_EXACT'

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
 if len(changes)!=16 or tuple(sorted(row['strref'] for row in changes))!=IDS:raise Hold('MANIFEST_SCOPE_DRIFT')
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

def state_file(workdir):return Path(workdir)/'BG_EET_RU_V159_BULK_STATE.json'
def backup_root(workdir):return Path(workdir)/'BG_EET_RU_V159_SAFE_BACKUPS'

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
 return {'schema':SCHEMA,'status':'UNTESTED','game_files_written':0,
         'archived_source_texts_reviewed':18,'prepared_editorial_entries':16,
         'numeric_values_preserved':True,'v157_installed_content_preserved':True,
         'source_archive_sha256':'2ec639c058d73c5891602bdb0d711f98984c8f6066b23abafb502059bdabcbf3',
         'single_updater':True,'gameplay_verified':False}

def check_v157_installed(game,workdir):
 p=Path(workdir)/'BG_EET_RU_V157_BULK_STATE.json'
 check_file(p)
 try: s=json.loads(p.read_text(encoding='utf-8'))
 except (ValueError,UnicodeError) as e:raise Hold('V157_STATE_UNREADABLE') from e
 if s.get('schema')!='BG_EET_RU_V157_ONE_BATCH_GUARDED_V1' or s.get('status')!='INSTALLED':
  raise Hold('V157_NOT_ACTIVE')
 if Path(s.get('game_root','')).resolve()!=Path(game).resolve():
  raise Hold('V157_GAME_ROOT_MISMATCH')
 if s.get('installed_sha256')!=MANIFEST['expected_source_tlk_sha256']:
  raise Hold('V157_INSTALLED_TLK_SHA_UNEXPECTED')
 return True

def preflight(game,workdir):
 game,workdir=external_guard(game,workdir)
 report=base_report();state=read_state(workdir)
 check_v157_installed(game,workdir)
 if state and state['status'] in ('PREPARING','INSTALLED','RECOVERY_REQUIRED'):
  report.update(status='HOLD_STATE_ALREADY_ACTIVE',state=state['status']);return report
 try:
  paths,src,dst=read_sources(game)
  report.update(status='V159_DUAL_TLK_EXACT_PREFLIGHT_PASS',
       files={name:{'path':str(paths[name]),'source_sha256':digest(src[name]),'candidate_sha256':digest(dst[name]),'source_bytes':len(src[name]),'candidate_bytes':len(dst[name])} for name in TLKS},
       weidu_log_sha256=checked_wei(game),
       note='NO_GAME_WRITE; 16 TLK entries staged in RAM only; preexisting V157 and banter remain unchanged')
 except Exception as exc:
  report.update(status='V159_SAFE_STOP',reason=type(exc).__name__+':'+str(exc)[:180])
 return report

def store_backup(root,name,data):
 path=root/name
 if path.exists() or path.is_symlink():raise Hold('BACKUP_EXISTS')
 with path.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
 if file_sha(path)!=digest(data):raise Hold('BACKUP_VERIFICATION_FAILED')
 return path

def swap(path,data,expected_current=None):
 if expected_current is not None and file_sha(path)!=expected_current:raise Hold('FILE_CHANGED_BEFORE_SWAP:'+path.name)
 stage=path.with_name(path.name+'.v159_stage')
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
 if pre['status']!='V159_DUAL_TLK_EXACT_PREFLIGHT_PASS':return pre
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
 batch=root/('V159_'+time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())+'_'+uuid.uuid4().hex[:8]);batch.mkdir()
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
 rep=base_report();rep.update(status='V159_16_TLK_INSTALLED_AWAITING_GAMEPLAY',game_files_written=2,
        installed_strrefs=list(IDS),files={name:{'old_sha256':digest(src[name]),'new_sha256':digest(dst[name])} for name in TLKS},
        backup_dir=str(batch),earlier_v157_preserved=True)
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
 rep=base_report();rep.update(status='V159_GUARDED_ROLLBACK_DONE',game_files_written=2,restored_strrefs=list(IDS))
 return rep

def status(game,workdir):
 game,workdir=external_guard(game,workdir)
 s=read_state(workdir);rep=base_report()
 if not s:return {**rep,'status':'V159_NOT_INSTALLED'}
 rep.update(status='V159_'+s['status'],backup_dir=s.get('backup_dir'))
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
  r=base_report();r.update(status='V159_SAFE_STOP',reason=type(ex).__name__+':'+str(ex)[:220],game_files_written='UNKNOWN_IF_EXCEPTION_AFTER_AUTHORIZED_WRITE' if mode in ('install','rollback') else 0)
  return r
