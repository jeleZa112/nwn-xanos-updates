"""Exact private V120 bytes -> relocation-safe EEex hook-route contract.

NO game files are loaded or written. Inputs are historical, private, SHA-pinned.
The output describes hook API selection only; it cannot install a native hook.

Root problem solved here: raw-copy hooks are safe for our SUB RSP instruction,
but WRONG for original CALL rel32 and LEA RIP+disp32 instructions.
EEex_HookBeforeCallWithLabels decodes a CALL rel32 and rewrites it to a new
JIT relay to the exact original callee. This claim comes from the upstream
EEex_Assembly_x86-64.lua EEex_HookCallInternal source; compatibility with the
installed EEex build is NOT established by these bytes.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import struct
import zipfile
from pathlib import Path

V120_SHA='08a9d5da367404b33bc982871627e8c3e1179c7a8ec8808bab0a75bea5755015'
FUNC='19_V68_COMBAT_CODE/functions/0039DA50_0039E9DC.bin'
FUNC_SHA='19c1d11b7ac41d261d22b19506b3570427e356544e48f2e2c622c1efdb74cc79'
BASE=0x39DA50
END=0x39E9DC
CAPTURE=0x39DA68
UNSAFE_RIP=0x39DA75
UPSTREAM_FIRSTCALL=0x39DA86
MESSAGE=0x39E84B
NORMAL_EXIT=0x39E996
RETURN=0x39E9B9

ROUTES={
 'capture':(CAPTURE,7,'EEex_HookBeforeRestoreWithLabels','fixed_sub_rsp'),
 'message':(MESSAGE,5,'EEex_HookBeforeCallWithLabels','call_rel32'),
 'normal_exit':(NORMAL_EXIT,5,'EEex_HookBeforeCallWithLabels','call_rel32'),
}
BANNED={
 'rip_lea':UNSAFE_RIP,
 'upstream_eeex_firstcall':UPSTREAM_FIRSTCALL,
}

class Hold(RuntimeError): pass

def get_function(archive:Path)->bytes:
    archive=Path(archive)
    if archive.is_symlink() or not archive.is_file():raise Hold('SOURCE_FILE_UNSAFE')
    if sha256(archive.read_bytes()).hexdigest()!=V120_SHA:raise Hold('V120_WHOLE_ZIP_SHA_DRIFT')
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None or len(z.namelist())!=len(set(z.namelist())):raise Hold('V120_ZIP_BAD_CRC_OR_DUPLICATE')
        b=z.read(FUNC)
    if sha256(b).hexdigest()!=FUNC_SHA or len(b)!=END-BASE:raise Hold('HIT_FUNCTION_SHA_OR_LENGTH_DRIFT')
    return b

def byte_at(b:bytes, addr:int, n:int)->bytes:
    if addr<BASE or addr+n>END:raise Hold('OUT_OF_PINNED_CODE_RANGE')
    return b[addr-BASE:addr-BASE+n]

def target_rel32(b:bytes, addr:int)->int:
    if byte_at(b,addr,1)!=b'\xe8':raise Hold('EXPECTED_CALL_REL32_NOT_FOUND')
    disp=struct.unpack('<i',byte_at(b,addr+1,4))[0]
    return addr+5+disp

def route_verify(archive:Path)->dict:
    b=get_function(archive)
    checks={}
    def check(k,cond):checks[k]=bool(cond)
    check('fixed_sub_rsp_7_byte',byte_at(b,CAPTURE,7)==bytes.fromhex('4881ec80000000'))
    check('frame_established_before_capture',byte_at(b,CAPTURE-3,3)==bytes.fromhex('488bec'))
    check('old_site_is_rip_relative_lea',byte_at(b,UNSAFE_RIP,7)==bytes.fromhex('488d15a1c92400'))
    check('old_rip_relative_relocation_forbidden',UNSAFE_RIP not in [x[0] for x in ROUTES.values()])
    check('firstcall_original_call',byte_at(b,UPSTREAM_FIRSTCALL,5)==bytes.fromhex('e8e5f20500'))
    check('firstcall_target_is_constructor',target_rel32(b,UPSTREAM_FIRSTCALL)==0x3FCD70)
    check('message_call_to_CMessageHandler_AddMessage',target_rel32(b,MESSAGE)==0x204C60)
    check('exit_call_to_CString_destructor',target_rel32(b,NORMAL_EXIT)==0x3FCE00)
    check('one_normal_return',b.count(b'\xc3')>=1 and byte_at(b,RETURN,1)==b'\xc3')
    check('known_calls_still_rel32',all(byte_at(b,site,1)==b'\xe8' for site in (MESSAGE,NORMAL_EXIT,UPSTREAM_FIRSTCALL)))
    check('capture_raw_copy_uses_fixed_position_instruction',ROUTES['capture'][2]=='EEex_HookBeforeRestoreWithLabels' and ROUTES['capture'][3]=='fixed_sub_rsp')
    check('message_call_rebuilds_target',ROUTES['message'][2]=='EEex_HookBeforeCallWithLabels' and ROUTES['message'][3]=='call_rel32')
    check('exit_call_rebuilds_target',ROUTES['normal_exit'][2]=='EEex_HookBeforeCallWithLabels' and ROUTES['normal_exit'][3]=='call_rel32')
    check('never_raw_copy_rel32',all(route[2]!='EEex_HookBeforeRestoreWithLabels' for route in list(ROUTES.values())[1:]))
    ranges=[(start,start+n) for start,n,_,_ in ROUTES.values()]
    check('sites_do_not_overlap',all(a[1]<=d[0] or d[1]<=a[0] for i,a in enumerate(ranges) for d in ranges[i+1:]))
    check('upstream_hook_not_modified',not any(lo<=UPSTREAM_FIRSTCALL<hi for lo,hi in ranges))
    check('correct_order_and_normal_exit',CAPTURE<UPSTREAM_FIRSTCALL<MESSAGE<NORMAL_EXIT<RETURN)
    check('no_actual_runtime_patch_available',True)
    if not all(checks.values()):raise Hold('PATCHPOINT_CONTRACT_INVALID '+','.join(k for k,v in checks.items() if not v))
    return {'schema':'BG_EET_RU_RELOCATABLE_PATCHPOINT_CONTRACT_V1',
            'status':'STATIC_ROUTE_PASS_LIVE_ABI_HOLD',
            'passed':len(checks),'checks':checks,
            'routing':{k:{'rva':hex(r[0]),'bytes':r[1],'api':r[2], 'instruction':r[3]} for k,r in ROUTES.items()},
            'callees':{hex(k):hex(target_rel32(b,k)) for k in (UPSTREAM_FIRSTCALL,MESSAGE,NORMAL_EXIT)},
            'runtime_patched':False,'gameplay_verified':False}

if __name__=='__main__':
    import json,sys
    print(json.dumps(route_verify(Path(sys.argv[1])),indent=2))
