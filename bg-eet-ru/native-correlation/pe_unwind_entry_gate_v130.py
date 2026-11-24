"""BG_EET_RU V130: exact Win64 PE .pdata/.xdata gate for Hit() hook placement.

SOURCE/READ ONLY. No process access, game mutation, hook, DLL loading,
injection, CMD installation or runtime claiming. The user's V129 evidence
contains Hit() CODE but NOT the on-disk PE unwind metadata, so a real
unwind result can only be obtained against the exact installed Baldur.exe.

The old 0x39DA68 candidate is the SUB RSP prologue instruction.
The alternative 0x39DA6F is six bytes of relocatable MOVs, after the SUB,
before an unsafe RIP-relative LEA at 0x39DA75 and the upstream EEex patch
at 0x39DA86. A static PE unwind gate is necessary but NOT sufficient for
a safe hook (JIT owner, ABI/XMM, SEH and rollback still unproven).
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
from pathlib import Path
import struct

GAME_SHA="fc821a4806a0305b84fd85f1aad2bd472c8db642ed34b4494ae62351cae1c580"
HIT_FUNCTION_SHA="19c1d11b7ac41d261d22b19506b3570427e356544e48f2e2c622c1efdb74cc79"
BEGIN=0x39DA50
FUNCTION_BODY_END=0x39E9BA
OLD_SITE=0x39DA68
PROPOSED_SITE=0x39DA6F
PROPOSED_SITE_END=0x39DA75
UNSAFE_SITE=0x39DA75
EEEX_UPSTREAM=0x39DA86
CODE_PREFIX=bytes.fromhex(
    "48895c2420"  # mov [rsp+20h],rbx, 5 bytes
    "4c89442418"  # mov [rsp+18h],r8, 5
    "55"          # push rbp
    "56"          # push rsi
    "57"          # push rdi
    "4154"        # push r12
    "4155"        # push r13
    "4156"        # push r14
    "4157"        # push r15
    "488bec"      # mov rbp,rsp
    "4881ec80000000"  # sub rsp,0x80
    "4c8bf2"      # mov r14,rdx
    "488bd9"      # mov rbx,rcx
    "488d15a1c92400"  # LEA RDX,[RIP+disp32] (DO NOT RELOCATE RAW)
)
PROPOSED_BYTES=bytes.fromhex("4c8bf2488bd9")
BANNED_BYTES=bytes.fromhex("488d15a1c92400")
EXIT_BYTES=bytes.fromhex(
    "4881c480000000415f415e415d415c5f5e5dc3"  # full normal epilogue
)

class Hold(ValueError):pass

def u16(a:bytes,i:int)->int:
    if i<0 or i+2>len(a):raise Hold("TRUNCATED_U16")
    return struct.unpack_from("<H",a,i)[0]
def u32(a:bytes,i:int)->int:
    if i<0 or i+4>len(a):raise Hold("TRUNCATED_U32")
    return struct.unpack_from("<I",a,i)[0]
def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()

@dataclass(frozen=True)
class Section:
    name:str
    rva:int
    virtual_size:int
    raw_ptr:int
    raw_size:int

def inspect_pe(data:bytes, *, pin_exe=True)->dict:
    """Pure PE32+ parser. A valid synthetic fixture may disable the SHA gate."""
    if not isinstance(data,bytes) or not 0x200<=len(data)<=16_000_000:
        raise Hold("PE_SIZE_OR_TYPE_HOLD")
    if pin_exe and sha(data)!=GAME_SHA:
        raise Hold("EXACT_GAME_EXE_SHA_MISMATCH")
    if data[:2]!=b"MZ":raise Hold("PE_MZ_REQUIRED")
    pe=u32(data,0x3c)
    if pe<0x40 or pe+24>len(data) or data[pe:pe+4]!=b"PE\x00\x00":
        raise Hold("PE_SIGNATURE_HOLD")
    coff=pe+4
    machine=u16(data,coff);nsec=u16(data,coff+2)
    optional_size=u16(data,coff+16)
    if machine!=0x8664 or not 1<=nsec<=64:raise Hold("AMD64_SECTION_COUNT_HOLD")
    opt=coff+20
    if u16(data,opt)!=0x20b or optional_size<0xF0 or opt+optional_size>len(data):
        raise Hold("PE32PLUS_OPTIONAL_HEADER_HOLD")
    if u32(data,opt+0x6c)<4:raise Hold("NO_EXCEPTION_DATA_DIRECTORY")
    ex_rva=u32(data,opt+0x70+3*8)
    ex_size=u32(data,opt+0x70+3*8+4)
    if ex_size==0 or ex_size%12 or ex_size>2_000_000:
        raise Hold("PDATA_EXCEPTION_DIRECTORY_INVALID")
    secs=[]
    start=opt+optional_size
    if start+nsec*40>len(data):raise Hold("SECTION_TABLE_TRUNCATED")
    for i in range(nsec):
        at=start+i*40
        name=data[at:at+8].split(b"\0",1)[0].decode("ascii","replace")
        virtual_size=u32(data,at+8);rva=u32(data,at+12)
        raw_size=u32(data,at+16);raw_ptr=u32(data,at+20)
        if raw_size and (raw_ptr>len(data) or raw_ptr+raw_size>len(data)):
            raise Hold("SECTION_RAW_RANGE_INVALID")
        secs.append(Section(name,rva,virtual_size,raw_ptr,raw_size))
    def read_rva(rva:int,length:int,allowed=(".text",".pdata",".xdata",".rdata"))->bytes:
        if rva<=0 or length<=0 or length>2_000_000:
            raise Hold("RVA_READ_RANGE_INVALID")
        matches=[sec for sec in secs if sec.name in allowed
                 and rva>=sec.rva and rva+length<=sec.rva+sec.raw_size]
        if len(matches)!=1:raise Hold("RVA_SECTION_AMBIGUOUS_OR_UNAVAILABLE")
        sec=matches[0];offset=sec.raw_ptr+rva-sec.rva
        return data[offset:offset+length]

    prefix=read_rva(BEGIN,len(CODE_PREFIX),(".text",))
    if prefix!=CODE_PREFIX:raise Hold("HIT_ENTRY_PROLOGUE_OR_CANDIDATE_DRIFT")
    if read_rva(PROPOSED_SITE,6,(".text",))!=PROPOSED_BYTES:
        raise Hold("CANDIDATE_MOV_BYTES_DRIFT")
    if read_rva(UNSAFE_SITE,7,(".text",))!=BANNED_BYTES:
        raise Hold("RIP_RELATIVE_BOUNDARY_DRIFT")
    if read_rva(0x39E9A7,len(EXIT_BYTES),(".text",))!=EXIT_BYTES:
        raise Hold("HIT_RETURN_EPILOGUE_DRIFT")
    if read_rva(EEEX_UPSTREAM,5,(".text",))!=bytes.fromhex("e8e5f20500"):
        raise Hold("ORIGINAL_UPSTREAM_FIRSTCALL_DRIFT")

    pdata=read_rva(ex_rva,ex_size,(".pdata",))
    containing=[]
    for i in range(0,len(pdata),12):
        begin,end,unwind=struct.unpack_from("<III",pdata,i)
        if begin<=BEGIN<end:
            containing.append((begin,end,unwind))
    if len(containing)!=1:raise Hold("HIT_PDATA_FUNCTION_COUNT_HOLD")
    fn_begin,fn_end,unwind_rva=containing[0]
    if fn_begin!=BEGIN or not FUNCTION_BODY_END<=fn_end<=0x39EA00:
        raise Hold("HIT_PDATA_BEGIN_END_NOT_PINNED")
    raw=read_rva(unwind_rva,4,(".xdata",".rdata"))
    version=raw[0]&7;flags=raw[0]>>3;prologue=raw[1]
    count=raw[2];frame_register=raw[3]&15;frame_offset=raw[3]>>4
    if version!=1 or count>128 or prologue>240:
        raise Hold("UNWIND_HEADER_UNSUPPORTED")
    # Extra slot accounting for variable-size Win64 UNWIND_CODE instructions.
    slots=read_rva(unwind_rva+4,2*count,(".xdata",".rdata")) if count else b""
    operations=[]
    index=0
    extras={0:0,1:None,2:0,3:0,4:1,5:2,8:1,9:2,10:0}
    while index<count:
        code_offset=slots[index*2]
        octet=slots[index*2+1]
        op=octet&15;info=octet>>4
        if op not in extras:raise Hold("UNWIND_OPCODE_UNSUPPORTED")
        size=2 if op==1 and info==1 else 1 if op==1 and info==0 else extras[op]
        if op==1 and info not in (0,1):raise Hold("ALLOC_LARGE_ENCODING_HOLD")
        if op==10 and info>1:raise Hold("MACHINE_FRAME_ENCODING_HOLD")
        if index+size>=count:raise Hold("UNWIND_CODE_TRUNCATED")
        if code_offset>prologue:raise Hold("UNWIND_CODE_AFTER_PROLOGUE")
        operations.append({"offset":code_offset,"opcode":op,"info":info,"extra_slots":size})
        index+=1+size
    old_offset=OLD_SITE-BEGIN
    new_offset=PROPOSED_SITE-BEGIN
    after_prolog=prologue<=new_offset
    old_in_prolog=old_offset<prologue
    # Flags indicate exception/unwind/chain metadata; report them, never
    # pretend simple trampolines are unwind-safe when any handler is present.
    owner_complex=flags!=0
    static_gate=after_prolog and old_in_prolog and not owner_complex
    return {
      "schema":"BG_EET_RU_V130_AMD64_UNWIND_GATE_READ_ONLY",
      "status":"POST_PROLOGUE_CANDIDATE_STATIC_PASS_RUNTIME_HOLD" if static_gate
                else "UNWIND_OR_PROLOGUE_PLACEMENT_HOLD",
      "game_exe_sha256":sha(data),
      "exact_game_build_proven":pin_exe,
      "hit_begin_rva":hex(fn_begin),"hit_end_rva":hex(fn_end),
      "unwind_info_rva":hex(unwind_rva),
      "prologue_length":prologue,
      "old_sub_rsp_in_prologue":old_in_prolog,
      "new_candidate_after_prologue":after_prolog,
      "candidate_rva":hex(PROPOSED_SITE),"candidate_length":6,
      "candidate_bytes":PROPOSED_BYTES.hex(),
      "candidate_code_is_non_rip_relative":True,
      "unsafe_rip_relative_lea_rva":hex(UNSAFE_SITE),
      "existing_eeex_firstcall_rva":hex(EEEX_UPSTREAM),
      "unwind_version":version,"unwind_flags":flags,
      "unwind_frame_register":frame_register,
      "unwind_frame_offset_scaled_16":frame_offset,
      "unwind_operations":operations,
      "handler_or_chain_present":owner_complex,
      "static_candidate_gate":static_gate,
      "native_abi_xmm_verified":False,
      "eeex_existing_hook_owner_verified":False,
      "runtime_exception_unwind_verified":False,
      "reentrancy_and_rollback_verified":False,
      "native_hook_install_allowed":False,
      "game_files_written":0,"gameplay_verified":False
    }

def inspect_game_exe(exe:Path)->dict:
    exe=Path(exe)
    if exe.is_symlink() or not exe.is_file():raise Hold("LIVE_EXE_NOT_REGULAR")
    if exe.name.lower()!="baldur.exe":raise Hold("LIVE_EXE_NAME_MISMATCH")
    if exe.stat().st_size>16_000_000:raise Hold("LIVE_EXE_TOO_LARGE")
    return inspect_pe(exe.read_bytes(),pin_exe=True)

if __name__=="__main__":
    import argparse,json
    p=argparse.ArgumentParser(description="Read-only AMD64 PE .pdata/.xdata gate. Does NOT install hooks")
    p.add_argument("baldur_exe",type=Path)
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    r=inspect_game_exe(a.baldur_exe)
    if a.output:
        if a.output.resolve()==a.baldur_exe.resolve():p.error("OUTPUT_MUST_NOT_OVERWRITE_GAME_EXE")
        a.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(json.dumps(r,ensure_ascii=False,indent=2))
