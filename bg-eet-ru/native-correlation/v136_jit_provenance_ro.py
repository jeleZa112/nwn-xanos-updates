"""BG_EET_RU V136: external read-only FirstCall target and paired Hit() site proof.

No hooks, no DLL injection, no code writes, no remote calls or thread suspension.
A readable executable JIT target is NOT proof that EEex owns the redirection,
registered runtime unwind metadata, callback ABI, nor gameplay evidence.
"""
from __future__ import annotations

import ctypes
import hashlib
import os
import sys
from pathlib import Path

SCHEMA='BG_EET_RU_V136_LIVE_JIT_REGION_PAIR_SITES_READONLY'
GAME_EXE_SHA='fc821a4806a0305b84fd85f1aad2bd472c8db642ed34b4494ae62351cae1c580'
FIRST=0x39DA86
# These are original RVA locations in a pinned Baldur.exe, not absolute addresses.
SITES={
 'entry_after_unwind_prologue':(0x39DA6F,bytes.fromhex('4c8bf2488bd9')),
 'exit_pre_epilogue':(0x39E99B,bytes.fromhex('488b9c24d8000000')),
 'return_byte_transfer':(0x39E9A3,bytes.fromhex('410fb6c6')),
 'stack_restore':(0x39E9A7,bytes.fromhex('4881c480000000')),
}
MEM_COMMIT=0x1000
MEM_IMAGE=0x1000000
MEM_PRIVATE=0x20000
MEM_MAPPED=0x40000
PAGE_GUARD=0x100
PAGE_NOACCESS=0x01
EXECUTABLE={0x10,0x20,0x40,0x80}
MAX_USER_PTR=0x0000800000000000
SNAP_BYTES=48


def _hold(reason: str) -> dict:
 return {'schema':SCHEMA,'status':'V136_RUNTIME_OWNER_AND_GAMEPLAY_HOLD',
         'reason':reason,'firstcall_owner_verified':False,
         'runtime_unwind_registered_verified':False,'native_abi_verified':False,
         'native_hooks_installed':False,'game_files_written':0,
         'hit_miss_meaning_verified':False,'row_join_verified':False,
         'gameplay_verified':False}


def _valid_ptr(x: int) -> bool:
 return type(x) is int and 0x10000 <= x < MAX_USER_PTR


def _in_module(address: int, mods: list[tuple]) -> list[str]:
 ans=[]
 for name,_path,base,size in mods:
  if isinstance(name,str) and _valid_ptr(base) and type(size) is int and 0 < size <= 1<<32:
   if base <= address < base+size:ans.append(name.lower())
 return ans


def _query_checked(query, address: int) -> dict:
 info=query(address)
 if not isinstance(info,dict):raise ValueError('MEMORY_REGION_QUERY_NOT_A_DICT')
 required=('base','size','state','protect','type')
 if any(type(info.get(k)) is not int for k in required):
  raise ValueError('MEMORY_REGION_FIELDS_MISSING')
 start,sz=info['base'],info['size']
 if not (_valid_ptr(start) and sz>0 and start <= address < start+sz and sz<1<<45):
  raise ValueError('MEMORY_REGION_RANGE_INVALID')
 if info['state']!=MEM_COMMIT:raise ValueError('MEMORY_TARGET_NOT_COMMITTED')
 prot=info['protect']
 if prot&PAGE_GUARD or prot&PAGE_NOACCESS or prot&0xff not in EXECUTABLE:
  raise ValueError('MEMORY_TARGET_NOT_SAFE_EXECUTABLE')
 if info['type'] not in (MEM_IMAGE,MEM_PRIVATE,MEM_MAPPED):
  raise ValueError('MEMORY_TARGET_TYPE_UNEXPECTED')
 return info


def audit(read, query, base: int, modules: list[tuple], game_size: int) -> dict:
 """Two snapshots; hostile-testable adapter; never interprets raw attack result."""
 out=_hold('UNVERIFIED')
 if not _valid_ptr(base) or base%0x10000!=0 or type(game_size) is not int or game_size<0x600000:
  out['reason']='GAME_IMAGE_BASE_OR_SIZE_INVALID';return out
 if not callable(read) or not callable(query):
  out['reason']='REMOTE_READ_OR_QUERY_MISSING';return out
 if not isinstance(modules,list):out['reason']='MODULE_LIST_MISSING';return out
 exact_game=[m for m in modules if len(m)==4 and m[0].lower()=='baldur.exe' and m[2]==base]
 if len(exact_game)!=1:out['reason']='EXACT_GAME_MODULE_MISSING';return out
 if not any(len(m)==4 and m[0].lower()=='eeex.dll' for m in modules):
  out['reason']='EEEX_DLL_NOT_LOADED';return out
 snap=[]
 for _ in range(2):
  try:
   raw={}
   for name,(rva,expected) in SITES.items():
    data=read(base+rva,len(expected))
    if type(data) is not bytes or data!=expected:
     raise ValueError('EXACT_SITE_CHANGED_'+name)
    raw[name]=data
   jmp=read(base+FIRST,5)
   if type(jmp) is not bytes or len(jmp)!=5 or jmp[0]!=0xe9:
    raise ValueError('FIRSTCALL_JMP_MISSING_OR_CHANGED')
   displacement=int.from_bytes(jmp[1:],'little',signed=True)
   target=base+FIRST+5+displacement
   if not _valid_ptr(target) or target==base+FIRST:
    raise ValueError('FIRSTCALL_TARGET_NOT_CANONICAL')
   src=_query_checked(query,base+FIRST)
   dst=_query_checked(query,target)
   # A read can cross the page boundary. Keep it within a single validated region.
   amount=min(SNAP_BYTES,dst['base']+dst['size']-target)
   if amount<16:raise ValueError('JIT_TARGET_NOT_ENOUGH_READABLE_BYTES')
   snippet=read(target,amount)
   if type(snippet) is not bytes or len(snippet)!=amount:
    raise ValueError('JIT_TARGET_READ_FAILED')
   raw.update(firstcall=jmp,target=target,source_region=src,target_region=dst,snippet=snippet)
   snap.append(raw)
  except Exception as e:
   out['reason']=str(e)[:110];return out
 if snap[0]!=snap[1]:
  out['reason']='PROCESS_MEMORY_CHANGED_DURING_TWO_SNAPSHOTS';return out
 x=snap[0]
 target=x['target']
 memberships=_in_module(target,modules)
 game_start=base
 game_end=base+game_size
 if game_start<=target<game_end:
  out['reason']='FIRSTCALL_TARGET_INSIDE_GAME_IMAGE_NOT_VERIFIED_JIT';return out
 if len(memberships)>1:
  out['reason']='FIRSTCALL_TARGET_OVERLAPPING_MODULES';return out
 if memberships and memberships[0]!='eeex.dll':
  out['reason']='FIRSTCALL_TARGET_OTHER_MODULE_UNVERIFIED';return out
 region=x['target_region']
 out.update(status='V136_LIVE_PAIR_SITES_AND_EXECUTABLE_TARGET_OBSERVED_OWNER_HOLD',
   reason='EEEX_FIRSTCALL_OWNER_AND_RUNTIME_UNWIND_STILL_UNVERIFIED',
   entry_exit_original_bytes_verified=True,
   sites_checked=len(SITES),
   firstcall_e9_jump_present=True,
   firstcall_target_executable=True,
   firstcall_target_region_type={MEM_IMAGE:'IMAGE',MEM_PRIVATE:'PRIVATE',MEM_MAPPED:'MAPPED'}[region['type']],
   firstcall_target_page_protect_code=hex(region['protect']),
   firstcall_target_inside_eeex_module=(memberships==['eeex.dll']),
   firstcall_target_in_unlisted_region=(len(memberships)==0),
   jit_target_code_sample_length=len(x['snippet']),
   jit_target_code_sample_sha256=hashlib.sha256(x['snippet']).hexdigest(),
   memory_snapshot_twice_equal=True,
   source_region_executable=True,
   operator_must_approve_native_install=True)
 # Deliberately omit absolute addresses, PID, raw memory and ASLR-dependent hashes.
 # Sample SHA is useful only for detecting drift between two captures of same process.
 return out


def _make_windows_api():
 if sys.platform!='win32' or ctypes.sizeof(ctypes.c_void_p)!=8:
  raise RuntimeError('WINDOWS_X64_PYTHON_REQUIRED')
 from ctypes import wintypes as w
 k=ctypes.WinDLL('kernel32',use_last_error=True)
 class MEMORY_BASIC_INFORMATION(ctypes.Structure):
  _fields_=[('BaseAddress',ctypes.c_void_p),('AllocationBase',ctypes.c_void_p),
            ('AllocationProtect',w.DWORD),('PartitionId',w.WORD),
            ('RegionSize',ctypes.c_size_t),('State',w.DWORD),('Protect',w.DWORD),('Type',w.DWORD)]
 if ctypes.sizeof(MEMORY_BASIC_INFORMATION)!=48:
  raise RuntimeError('WINDOWS_MEMORY_BASIC_INFORMATION_LAYOUT_MISMATCH')
 k.VirtualQueryEx.argtypes=[w.HANDLE,ctypes.c_void_p,ctypes.POINTER(MEMORY_BASIC_INFORMATION),ctypes.c_size_t]
 k.VirtualQueryEx.restype=ctypes.c_size_t
 k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE
 k.CloseHandle.argtypes=[w.HANDLE];k.CloseHandle.restype=w.BOOL
 k.ReadProcessMemory.argtypes=[w.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
 k.ReadProcessMemory.restype=w.BOOL
 return k,w,MEMORY_BASIC_INFORMATION


def _query_region(k,h,T,addr):
 b=T();n=k.VirtualQueryEx(h,ctypes.c_void_p(addr),ctypes.byref(b),ctypes.sizeof(T))
 if n!=ctypes.sizeof(T):raise RuntimeError('VIRTUAL_QUERY_EX_FAILED')
 return {'base':int(b.BaseAddress or 0),'size':int(b.RegionSize),
         'state':int(b.State),'protect':int(b.Protect),'type':int(b.Type)}


def _read_remote(k,h,w,addr,n):
 if not _valid_ptr(addr) or not 0<n<=SNAP_BYTES:raise RuntimeError('INVALID_REMOTE_READ')
 buf=ctypes.create_string_buffer(n);got=ctypes.c_size_t(0)
 if not k.ReadProcessMemory(h,ctypes.c_void_p(addr),buf,n,ctypes.byref(got)) or got.value!=n:
  raise RuntimeError('READ_PROCESS_MEMORY_FAILED')
 return buf.raw


def run_game(game_root: Path, legacy_module) -> dict:
 out=_hold('WINDOWS_REMOTE_SNAPSHOT_NOT_RUN')
 try:
  k,w,T=_make_windows_api()
  enum_k,enum_w=legacy_module.get_windows_api()
  exe=(game_root.expanduser().resolve(strict=True)/'Baldur.exe')
  if not exe.is_file() or exe.is_symlink() or legacy_module.sha_file(exe)!=GAME_EXE_SHA:
   raise RuntimeError('EXACT_GAME_EXE_SHA_DRIFT')
  pids=legacy_module._exe_pid_candidates(enum_k,enum_w)
  matches=[]
  for pid in pids:
   h=k.OpenProcess(0x0410,False,pid)  # PROCESS_QUERY_INFORMATION | PROCESS_VM_READ; no write.
   if not h:continue
   try:
    actual=legacy_module._image_path(enum_k,enum_w,h).resolve()
    if os.path.normcase(str(actual))==os.path.normcase(str(exe.resolve())):matches.append(pid)
   finally:k.CloseHandle(h)
  if len(matches)!=1:raise RuntimeError('EXACT_GAME_PROCESS_NOT_UNIQUE')
  h=k.OpenProcess(0x0410,False,matches[0])
  if not h:raise RuntimeError('PROCESS_READ_ONLY_OPEN_FAILED')
  try:
   modules=legacy_module._modules(enum_k,enum_w,matches[0])
   games=[m for m in modules if len(m)==4 and m[0].lower()=='baldur.exe' and
          os.path.normcase(str(Path(m[1]).resolve()))==os.path.normcase(str(exe.resolve()))]
   if len(games)!=1:raise RuntimeError('EXACT_GAME_MODULE_NOT_UNIQUE')
   base,size=games[0][2],games[0][3]
   out=audit(lambda a,n:_read_remote(k,h,w,a,n),
             lambda a:_query_region(k,h,T,a),base,modules,size)
  finally:k.CloseHandle(h)
  if legacy_module.sha_file(exe)!=GAME_EXE_SHA:
   return _hold('EXACT_GAME_EXE_CHANGED_DURING_SNAPSHOT')
 except Exception as e:
  return _hold(str(e)[:130])
 return out


def selftest_windows() -> dict:
 k,w,T=_make_windows_api()
 h=k.OpenProcess(0x0410,False,os.getpid())
 if not h:raise RuntimeError('SELFTEST_PROCESS_OPEN_FAILED')
 try:
  ptr=ctypes.cast(k.ReadProcessMemory,ctypes.c_void_p).value
  region=_query_region(k,h,T,ptr)
  assert region['state']==MEM_COMMIT
  assert (region['protect']&0xff) in EXECUTABLE
  assert len(_read_remote(k,h,w,ptr,16))==16
  return {'status':'WINDOWS_READ_AND_VIRTUALQUERYEX_SELFTEST_PASS',
          'remote_writes':0,'native_hooks_installed':False,'gameplay_verified':False}
 finally:k.CloseHandle(h)


def main(argv=None):
 import argparse,json
 p=argparse.ArgumentParser(description='V136 read-only FirstCall target and paired Hit site')
 p.add_argument('--game',type=Path)
 p.add_argument('--selftest-windows',action='store_true')
 p.add_argument('--output',type=Path)
 a=p.parse_args(argv)
 if a.selftest_windows:result=selftest_windows()
 else:
  if a.game is None:p.error('--game is required')
  import v133_live_hit_inventory_ro as legacy
  result=run_game(a.game,legacy)
 if a.output:
  dest=a.output.expanduser().resolve()
  if a.output.is_symlink():raise RuntimeError('SYMLINK_REPORT_FORBIDDEN')
  if a.game and (dest==a.game.resolve() or a.game.resolve() in dest.parents):
   raise RuntimeError('GAME_DIRECTORY_OUTPUT_FORBIDDEN')
  dest.parent.mkdir(parents=True,exist_ok=True)
  dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(result['status'])
 return 0 if (result['status'].startswith('V136_LIVE_') or
              result['status']=='WINDOWS_READ_AND_VIRTUALQUERYEX_SELFTEST_PASS') else 2

if __name__=='__main__':raise SystemExit(main())
