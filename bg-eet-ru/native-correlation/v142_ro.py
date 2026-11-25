"""BG_EET_RU V142 (V140/V136 preserved): external read-only FirstCall target and paired Hit() site proof.

No hooks, no DLL injection, no code writes, no remote calls or thread suspension.
A readable executable JIT target is NOT proof that EEex owns the redirection,
registered runtime unwind metadata, callback ABI, nor gameplay evidence.
"""
from __future__ import annotations

import ctypes
import hashlib
import os
import sys
import struct
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


TARGET_RVA=0x398530
MAX_CALLEE_BYTES=16384

class Hold(Exception):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_u16(b: bytes, off: int) -> int:
    if off < 0 or off + 2 > len(b): raise Hold('PE_TRUNCATED_U16')
    return struct.unpack_from('<H', b, off)[0]


def _read_u32(b: bytes, off: int) -> int:
    if off < 0 or off + 4 > len(b): raise Hold('PE_TRUNCATED_U32')
    return struct.unpack_from('<I', b, off)[0]


def _section_list(data: bytes):
    """Parse x64 PE32+ file headers and section spans without mapping/executing PE."""
    if type(data) is not bytes or len(data) < 0x200 or data[:2] != b'MZ':
        raise Hold('EXACT_PE_MZ_MISSING')
    pe = _read_u32(data, 0x3c)
    if pe < 0x40 or pe > 4096 or data[pe:pe+4] != b'PE\0\0':
        raise Hold('EXACT_PE_SIGNATURE_MISSING')
    if _read_u16(data, pe+4) != 0x8664: raise Hold('ONLY_AMD64_SUPPORTED')
    count = _read_u16(data, pe+6)
    optlen = _read_u16(data, pe+20)
    opt = pe+24
    if count < 2 or count > 96 or optlen < 0xF0 or opt+optlen > len(data):
        raise Hold('PE_SECTION_OR_OPTIONAL_HEADER_INVALID')
    if _read_u16(data, opt) != 0x20b: raise Hold('ONLY_PE32_PLUS_SUPPORTED')
    if _read_u32(data, opt+108) < 4: raise Hold('PE_NO_EXCEPTION_DATA_DIRECTORY')
    exception_rva, exception_size = _read_u32(data, opt+112+3*8), _read_u32(data, opt+116+3*8)
    if exception_rva == 0 or exception_size == 0 or exception_size%12:
        raise Hold('PE_MISSING_OR_UNALIGNED_PDATA_DIRECTORY')
    sect = opt+optlen
    if sect+count*40 > len(data): raise Hold('PE_TRUNCATED_SECTION_TABLE')
    sections=[]
    for i in range(count):
        o=sect+i*40
        name=data[o:o+8].split(b'\0')[0].decode('latin1')
        virtual_size, virtual_address, raw_size, raw_ptr = struct.unpack_from('<IIII',data,o+8)
        flags=_read_u32(data,o+36)
        if not virtual_size or not raw_size or raw_ptr+raw_size > len(data):
            raise Hold('PE_SECTION_SIZE_OR_RAW_RANGE_INVALID')
        sections.append(dict(name=name,rva=virtual_address,vsize=virtual_size,rawsize=raw_size,raw=raw_ptr,flags=flags))
    return sections,exception_rva,exception_size


def _rva_to_raw(sections: list[dict], rva: int, size: int, *, executable=None) -> int:
    if type(rva) is not int or type(size) is not int or size <= 0 or size > 1<<20:
        raise Hold('RVA_OR_SIZE_INVALID')
    matches=[]
    for s in sections:
        if s['rva'] <= rva and rva+size <= s['rva']+min(s['rawsize'],s['vsize']):
            if executable is None or bool(s['flags'] & 0x20000000)==executable:
                matches.append(s['raw']+rva-s['rva'])
    if len(matches)!=1: raise Hold('RVA_SECTION_AMBIGUOUS_OR_UNAVAILABLE')
    return matches[0]


def extract_pdata_function(data: bytes, *, rva=TARGET_RVA, expected_sha=GAME_EXE_SHA):
    """Never disassemble, load, execute or patch game PE. Source bytes only."""
    if type(data) is not bytes or not expected_sha or digest(data)!=expected_sha:
        raise Hold('EXACT_GAME_EXE_SHA_MISMATCH')
    sections,pdata_rva,pdata_size=_section_list(data)
    poff=_rva_to_raw(sections,pdata_rva,pdata_size)
    entries=[]
    for i in range(pdata_size//12):
        lo,hi,unwind=struct.unpack_from('<III',data,poff+12*i)
        if lo and hi and unwind and lo<hi and lo<=rva<hi:
            entries.append((lo,hi,unwind))
    if len(entries)!=1: raise Hold('CALLEE_PDATA_ENTRY_MISSING_OR_AMBIGUOUS')
    start,end,unwind=entries[0]
    length=end-start
    if length > MAX_CALLEE_BYTES: raise Hold('CALLEE_LENGTH_OVER_SAFETY_LIMIT')
    raw=_rva_to_raw(sections,start,length,executable=True)
    _rva_to_raw(sections,unwind,4)
    source=data[raw:raw+length]
    return {
        'callee_rva':hex(rva),'function_begin_rva':hex(start),'function_end_rva':hex(end),
        'unwind_info_rva':hex(unwind),'function_bytes':length,
        'callee_source_sha256':digest(source),
        'callee_source_hex':source.hex(),
        'semantic_label':'SHARED_DISPATCH_CALLEE_UNCLASSIFIED',
        'verified_direct_combatlog_producer':False,
        'verified_renderer_token_source':False,
        'native_hook_installed':False,
    }



# V140 is an evidence-only successor. Old V136 runtime observation is preserved.
V140_SCHEMA='BG_EET_RU_V140_DISPATCH_CALLEE_DISK_READONLY'
_v136_run_game=run_game

def run_game(game_root: Path, legacy_module) -> dict:
    live=_v136_run_game(game_root,legacy_module)
    out={'schema':V140_SCHEMA,'status':'V140_CALLEE_SOURCE_HOLD',
         'v136_live_observation':live,
         'game_files_written':0,'native_hooks_installed':False,
         'safe_to_install':False,'gameplay_verified':False,
         'firstcall_owner_verified':False,'win64_runtime_unwind_verified':False,
         'per_attempt_hit_miss_verified':False,'visible_row_join_verified':False,
         'calleeto_combatlog_verified':False}
    try:
        root=Path(game_root).expanduser().resolve(strict=True)
        exe=root/'Baldur.exe'
        if exe.is_symlink() or not exe.is_file():
            raise Hold('EXACT_GAME_EXE_NOT_REGULAR_FILE')
        before=exe.stat()
        if before.st_size<=0 or before.st_size>128*1024*1024:
            raise Hold('GAME_EXE_SIZE_OUTSIDE_READONLY_LIMIT')
        source=exe.read_bytes()
        if len(source)!=before.st_size:
            raise Hold('GAME_EXE_READ_SIZE_CHANGED')
        callee=extract_pdata_function(source)
        after=exe.stat()
        if (before.st_size,before.st_mtime_ns,before.st_ino)!=(after.st_size,after.st_mtime_ns,after.st_ino):
            raise Hold('GAME_EXE_CHANGED_DURING_READ')
        out['callee']=callee
        try:
            out['delivery_capture']=v142_delivery(source)
            out['status']='V142_PINNED_DISPATCH_MESSAGE_ROUTING_CAPTURED_UI_HOLD'
            out['reason']='QUEUE_AND_VTABLE_CODE_CAPTURED_BUT_RENDER_JOIN_UNVERIFIED'
        except (Hold,OSError,ValueError) as e:
            out['delivery_capture_hold']=str(e)[:140]
        out['game_exe_sha256']=GAME_EXE_SHA
        out.setdefault('status','V140_PINNED_FUNCTION_EXTRACTED_SEMANTIC_PROVENANCE_HOLD')
        out.setdefault('reason','CALL_CHAIN_TO_COMBATLOG_AND_DIRECT_RENDER_TOKEN_UNVERIFIED')
    except (Hold, OSError, ValueError) as e:
        out['reason']=str(e)[:150]
    return out


# V142 bounded source windows; direct game EXE read only, never map or run.
def v142_delivery(data:bytes)->dict:
 if digest(data)!=GAME_EXE_SHA:raise Hold('EXACT_GAME_EXE_SHA_DRIFT')
 sections,_,_=_section_list(data)
 pe=struct.unpack_from('<I',data,0x3c)[0]
 base=struct.unpack_from('<Q',data,pe+24+24)[0]
 if base<0x10000 or base>0x7fffffffffff:raise Hold('IMAGE_BASE_INVALID')
 output={'status':'V142_ON_DISK_WINDOWS_CAPTURED_NOT_UI_PROOF',
         'queue_target_rva':'0x204c60','on_disk_image_base':hex(base),
         'render_row_writer_proven':False,'native_hook_installed':False}
 raw=_rva_to_raw(sections,0x204c60,1024,executable=True)
 q=data[raw:raw+1024]
 output['queue_target_window']={'rva':'0x204c60','bytes':len(q),
      'sha256':digest(q),'hex':q.hex(),'function_boundaries_proven':False}
 try:
  output['queue_pdata_function']=extract_pdata_function(data,rva=0x204c60)
 except Hold as e:output['queue_pdata_hold']=str(e)[:100]
 tables={}
 for va in (0x58e140,0x597cd0,0x5901f0):
  raw=_rva_to_raw(sections,va,96,executable=False)
  pointers=struct.unpack_from('<12Q',data,raw)
  entries=[]
  for i,pointer in enumerate(pointers):
   v=pointer-base
   e={'slot':i,'image_va':hex(pointer)}
   if 0<=v<0x10000000:
    e['rva']=hex(v)
    if i<8:
     try:
      o=_rva_to_raw(sections,v,512,executable=True)
      b=data[o:o+512]
      e['code_window']={'sha256':digest(b),'hex':b.hex(),
                        'bytes':len(b),'exact_function_boundaries':False}
     except Hold as exc:e['code_window_hold']=str(exc)[:90]
   else:e['pointer_normalization_hold']=True
   entries.append(e)
  tables[hex(va)]=entries
 output['vtable_pointers_and_bounded_code_windows']=tables
 output['static_vtable_names_verified']=False
 output['message_queue_to_combatlog_proven']=False
 return output

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
