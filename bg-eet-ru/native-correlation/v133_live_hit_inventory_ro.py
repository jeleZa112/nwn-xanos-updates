"""BG_EET_RU external Windows process-memory inventory. READ ONLY.

No injection, hooking, suspending threads, WriteProcessMemory or game mutation.
Integrated into the existing one-file updater as a strictly read-only optional audit.
The real-game branch requires exact pinned on-disk Baldur.exe hash and game path.
Runtime JMP target ownership is deliberately NOT inferred from JMP E9 alone.
"""
from __future__ import annotations
import argparse
import ctypes
import hashlib
import json
import os
import sys
from pathlib import Path

GAME_EXE_SHA='fc821a4806a0305b84fd85f1aad2bd472c8db642ed34b4494ae62351cae1c580'
FIRST=0x39DA86
VTABLE=0x597CD0
# Exact first 7 CMessage vtable method RVAs from pinned private V120 EXE.
# This vtable is *also* used by Damage(), so it never proves attack-roll identity.
VTABLE_METHODS=(0x1A4460,0x14DD50,0x117B80,0x1E4C50,0x20AEA0,0x21AA80,0x2110B0)
SEND_TARGET=0x204C60
EXIT_TARGET=0x3FCE00
EXPECTED={
 'prologue_stack_allocation':(0x39DA68,bytes.fromhex('4881ec80000000')),
 'post_prologue_capture_candidate':(0x39DA6F,bytes.fromhex('4c8bf2488bd9')),
 'forbidden_rip_relative':(0x39DA75,bytes.fromhex('488d15a1c92400')),
 'message':(0x39E84B,bytes.fromhex('e81064e6ff')),
 'exit':(0x39E996,bytes.fromhex('e865e40500')),
}

def sha_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def audit_memory(read,base:int)->dict:
    """Single bounded snapshot: read-only, site-exact, fails closed on drift."""
    checks={}
    result={
      'schema':'BG_EET_RU_V133_WINDOWS_EXTERNAL_MEMORY_RO',
      'status':'RUNTIME_MEMORY_HOLD',
      'mode':'PROCESS_READ_ONLY',
      'game_writes':0,'native_hooks_installed':False,
      'firstcall_owner_verified':False,
      'native_abi_verified':False,'miss_resref_verified':False,
      'visible_row_verified':False,'gameplay_verified':False,
      'checks':checks}
    if not isinstance(base,int) or base<=0x10000000 or base%0x10000:
        result['reason']='MODULE_BASE_UNVERIFIED';return result
    if not callable(read):result['reason']='MEMORY_READER_MISSING';return result
    snapshots=[]
    for round_no in range(2):
        current={}
        for key,(rva,expected) in EXPECTED.items():
            try:
                raw=read(base+rva,len(expected))
            except Exception as exc:
                result['reason']='SITE_READ_ERROR_'+key;return result
            if not isinstance(raw,bytes) or len(raw)!=len(expected):
                result['reason']='SITE_READ_MISSING_'+key;return result
            current[key]=raw
            checks['original_'+key]=raw==expected
            if raw!=expected:
                result['reason']='SITE_CHANGED_'+key;return result
        try:
            jmp=read(base+FIRST,5)
            vtable=read(base+VTABLE,56)
        except Exception:
            result['reason']='JMP_OR_VTABLE_READ_ERROR';return result
        if not isinstance(jmp,bytes) or len(jmp)!=5 or jmp[0]!=0xe9:
            result['reason']='EEEX_FIRSTCALL_NOT_JMP';return result
        if not isinstance(vtable,bytes) or len(vtable)!=56:
            result['reason']='MESSAGE_VTABLE_UNREADABLE';return result
        current['eeex_jmp']=jmp
        current['vtable']=vtable
        snapshots.append(current)
    if snapshots[0]!=snapshots[1]:
        result['reason']='MEMORY_CHANGED_DURING_READ';return result
    def rel32(op,rva):
        raw=snapshots[0][op]
        if len(raw)!=5 or raw[0]!=0xe8:return None
        return rva+5+int.from_bytes(raw[1:],'little',signed=True)
    checks['message_call_target']=rel32('message',EXPECTED['message'][0])==SEND_TARGET
    checks['exit_call_target']=rel32('exit',EXPECTED['exit'][0])==EXIT_TARGET
    dest=FIRST+5+int.from_bytes(snapshots[0]['eeex_jmp'][1:],'little',signed=True)
    checks['firstcall_jump_sane']=dest>0 and dest!=FIRST
    # No raw pointer/address values or memory dumps in the public report.
    checks['vtable_exact_methods']=all(
        int.from_bytes(snapshots[0]['vtable'][i*8:i*8+8],'little')==base+rva
        for i,rva in enumerate(VTABLE_METHODS))
    if not all(checks.values()):
        result['reason']='STATIC_OR_RUNTIME_INSTRUCTION_MISMATCH';return result
    result['status']='LIVE_SITES_MATCH_OWNER_UNVERIFIED_RUNTIME_HOLD'
    result['reason']='JIT_OWNER_UNKNOWN_AND_MISS_TO_VISIBLE_ROW_UNVERIFIED'
    result['sites_checked']=len(EXPECTED)+2
    result['post_prologue_rva']='0x39DA6F'
    result['native_registers_preserved_proven']=False
    result['same_hit_to_visible_row_verified']=False
    result['memory_read_twice']=True
    result['firstcall_jmp_detected']=True
    result['firstcall_owner_verified']=False
    result['vtable_shared_with_damage']=True
    return result


def get_windows_api():
    if sys.platform!='win32' or ctypes.sizeof(ctypes.c_void_p)!=8:
        raise RuntimeError('WINDOWS_X64_PYTHON_REQUIRED')
    from ctypes import wintypes
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
    k.OpenProcess.restype=wintypes.HANDLE
    k.CloseHandle.argtypes=[wintypes.HANDLE]
    k.CloseHandle.restype=wintypes.BOOL
    k.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
    k.ReadProcessMemory.restype=wintypes.BOOL
    k.CreateToolhelp32Snapshot.argtypes=[wintypes.DWORD,wintypes.DWORD]
    k.CreateToolhelp32Snapshot.restype=wintypes.HANDLE
    k.Module32FirstW.argtypes=[wintypes.HANDLE,ctypes.c_void_p]
    k.Module32FirstW.restype=wintypes.BOOL
    k.Module32NextW.argtypes=[wintypes.HANDLE,ctypes.c_void_p]
    k.Module32NextW.restype=wintypes.BOOL
    k.Process32FirstW.argtypes=[wintypes.HANDLE,ctypes.c_void_p]
    k.Process32FirstW.restype=wintypes.BOOL
    k.Process32NextW.argtypes=[wintypes.HANDLE,ctypes.c_void_p]
    k.Process32NextW.restype=wintypes.BOOL
    k.QueryFullProcessImageNameW.argtypes=[wintypes.HANDLE,wintypes.DWORD,wintypes.LPWSTR,ctypes.POINTER(wintypes.DWORD)]
    k.QueryFullProcessImageNameW.restype=wintypes.BOOL
    return k,wintypes

class NativeError(RuntimeError):pass


def _structures(w):
    class PROCESSENTRY32W(ctypes.Structure):
        _fields_=[('dwSize',w.DWORD),('cntUsage',w.DWORD),('th32ProcessID',w.DWORD),
           ('th32DefaultHeapID',ctypes.c_void_p),('th32ModuleID',w.DWORD),
           ('cntThreads',w.DWORD),('th32ParentProcessID',w.DWORD),
           ('pcPriClassBase',w.LONG),('dwFlags',w.DWORD),('szExeFile',w.WCHAR*260)]
    class MODULEENTRY32W(ctypes.Structure):
        _fields_=[('dwSize',w.DWORD),('th32ModuleID',w.DWORD),('th32ProcessID',w.DWORD),
           ('GlblcntUsage',w.DWORD),('ProccntUsage',w.DWORD),
           ('modBaseAddr',ctypes.c_void_p),('modBaseSize',w.DWORD),('hModule',ctypes.c_void_p),
           ('szModule',w.WCHAR*256),('szExePath',w.WCHAR*260)]
    return PROCESSENTRY32W,MODULEENTRY32W


def _snapshot(k,flags,pid):
    h=k.CreateToolhelp32Snapshot(flags,pid)
    if h in (None,ctypes.c_void_p(-1).value):raise NativeError('TOOLHELP_SNAPSHOT_FAILED')
    return h


def _exe_pid_candidates(k,w,name='Baldur.exe'):
    P,_=_structures(w)
    s=_snapshot(k,0x2,0)
    try:
        entry=P();entry.dwSize=ctypes.sizeof(P)
        out=[]
        if k.Process32FirstW(s,ctypes.byref(entry)):
            while True:
                if entry.szExeFile.casefold()==name.casefold():out.append(int(entry.th32ProcessID))
                entry.dwSize=ctypes.sizeof(P)
                if not k.Process32NextW(s,ctypes.byref(entry)):break
        return out
    finally:k.CloseHandle(s)


def _modules(k,w,pid):
    _,M=_structures(w)
    s=_snapshot(k,0x8|0x10,pid)
    try:
        entry=M();entry.dwSize=ctypes.sizeof(M)
        out=[]
        if not k.Module32FirstW(s,ctypes.byref(entry)):
            raise NativeError('MODULE32_FIRST_FAILED')
        while True:
            out.append((entry.szModule,entry.szExePath,int(entry.modBaseAddr or 0),int(entry.modBaseSize)))
            entry.dwSize=ctypes.sizeof(M)
            if not k.Module32NextW(s,ctypes.byref(entry)):break
        return out
    finally:k.CloseHandle(s)


def _read_remote(k,h,address,count):
    if count<=0 or count>64 or address<0x10000:raise NativeError('INVALID_READ_SIZE_OR_ADDRESS')
    b=ctypes.create_string_buffer(count);got=ctypes.c_size_t()
    if not k.ReadProcessMemory(h,ctypes.c_void_p(address),b,count,ctypes.byref(got)) or got.value!=count:
        raise NativeError('READPROCESSMEMORY_FAILED')
    return b.raw


def _image_path(k,w,h):
    buf=ctypes.create_unicode_buffer(32768)
    n=w.DWORD(len(buf))
    if not k.QueryFullProcessImageNameW(h,0,buf,ctypes.byref(n)):
        raise NativeError('PROCESS_IMAGE_QUERY_FAILED')
    return Path(buf.value)


def run_game(game_root:Path,pid:int|None=None)->dict:
    """Strict live-game preflight only; never starts a process or writes game files."""
    result={'schema':'BG_EET_RU_V133_EXTERNAL_WINDOWS_PREFLIGHT',
      'status':'RUNTIME_MEMORY_HOLD','game_files_written':0,'native_hooks_installed':False,
      'gameplay_verified':False,'operator_action_required':False}
    try:
        k,w=get_windows_api()
        root=game_root.expanduser().resolve(strict=True)
        exe=root/'Baldur.exe'
        if not exe.is_file() or exe.is_symlink() or sha_file(exe)!=GAME_EXE_SHA:
            raise NativeError('DISK_EXECUTABLE_SHA_HOLD')
        candidates=[pid] if pid else _exe_pid_candidates(k,w)
        valid=[]
        for candidate in candidates:
            if not isinstance(candidate,int) or candidate<=0:continue
            handle=k.OpenProcess(0x1010,False,candidate) # QUERY_LIMITED_INFORMATION | VM_READ
            if not handle:continue
            try:
                actual=_image_path(k,w,handle).resolve()
                if os.path.normcase(str(actual))==os.path.normcase(str(exe.resolve())):
                    valid.append(candidate)
            finally:k.CloseHandle(handle)
        if len(valid)!=1:raise NativeError('GAME_PROCESS_NOT_UNIQUELY_VERIFIED')
        chosen=valid[0]
        handle=k.OpenProcess(0x1010,False,chosen)
        if not handle:raise NativeError('PROCESS_READ_OPEN_FAILED')
        try:
            mods=_modules(k,w,chosen)
            own=[m for m in mods if m[0].casefold()=='baldur.exe' and
                 os.path.normcase(str(Path(m[1]).resolve()))==os.path.normcase(str(exe.resolve()))]
            if len(own)!=1:raise NativeError('EXE_MODULE_BASE_HOLD')
            base=own[0][2]
            if own[0][3]<0x600000:raise NativeError('EXE_MODULE_SIZE_HOLD')
            report=audit_memory(lambda addr,n:_read_remote(k,handle,addr,n),base)
        finally:k.CloseHandle(handle)
        result.update(report)
        # Check executable on disk again to detect changed evidence while reading.
        if sha_file(exe)!=GAME_EXE_SHA:
            result.update(status='RUNTIME_MEMORY_HOLD',reason='EXE_CHANGED_DURING_SNAPSHOT')
        result['process_count_verified']=1
        result['eeex_module_present']=any(x[0].casefold()=='eeex.dll' for x in mods)
        # Presence is NOT ownership of the FirstCall trampoline.
    except Exception as exc:
        result['status']='RUNTIME_MEMORY_HOLD'
        result['reason']=str(exc)[:160]
    return result


def selftest_windows()->dict:
    """True kernel32 cross-process API test, with current process as read target."""
    k,w=get_windows_api()
    h=k.OpenProcess(0x1010,False,os.getpid())
    if not h:raise NativeError('SELFTEST_OPENPROCESS_FAILED')
    try:
        payload=ctypes.create_string_buffer(b'BG_EET_RU_V4_TEST_READ_ONLY' + bytes([7,13,29]))
        got=_read_remote(k,h,ctypes.addressof(payload),len(payload.raw))
        assert got==payload.raw
        try:_read_remote(k,h,0x1000,16)
        except NativeError:pass
        else:raise AssertionError('INVALID_POINTER_READ_NOT_REJECTED')
        mods=_modules(k,w,os.getpid())
        assert any(m[2] for m in mods),'MODULE_ENUMERATION_FAILED'
        assert _image_path(k,w,h).is_file(),'PROCESS_IMAGE_PATH_FAILED'
        return {'status':'WINDOWS_KERNEL32_SELFTEST_PASS',
           'readprocessmemory_real':True,'module_enum_real':True,
           'invalid_memory_blocked':True,'game_files_written':0,'gameplay_verified':False}
    finally:k.CloseHandle(h)


def main():
    p=argparse.ArgumentParser(description='BG_EET_RU Win64 external READ-ONLY game memory snapshot')
    p.add_argument('--game',type=Path,help='Absolute game root; required except in CI selftest')
    p.add_argument('--pid',type=int)
    p.add_argument('--selftest-windows',action='store_true',help='Test kernel32 against this process; NOT the game')
    p.add_argument('--output',type=Path)
    a=p.parse_args()
    if a.selftest_windows:
        report=selftest_windows()
    elif not a.game:
        p.error('--game required for live game inspection')
    else:report=run_game(a.game,a.pid)
    if a.output:
        if a.game:
            root=a.game.expanduser().resolve()
            outfile=a.output.expanduser().resolve()
            if outfile==root or root in outfile.parents:
                raise NativeError('REPORT_CANNOT_BE_WRITTEN_IN_GAME_ROOT')
            if a.output.is_symlink():raise NativeError('REPORT_SYMLINK_FORBIDDEN')
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')
    print(report['status'])
    return 0 if report['status'] in ('WINDOWS_KERNEL32_SELFTEST_PASS','LIVE_SITES_MATCH_OWNER_UNVERIFIED_RUNTIME_HOLD') else 2
if __name__=='__main__':raise SystemExit(main())
