"""V132 exact-build EEex source / Win64 raw-unwind fingerprint (READ ONLY).

V131 proved the installed PE unwind header, but discarded the *contents* of
extra UWOP_SAVE_NONVOL slots. V132 decodes that byte-for-byte, and audits the
*installed* EEex x64 assembly sources for their actual unwind/JIT contract.

No Lua execution, code injection, loader launch, process access, file writes,
native patching, DLL loading, or modification to game/Voice/BGXAI/saves.

The upstream public EEex source shows RtlLookupFunctionEntry and
RtlAddFunctionTable, but cannot prove the user's installed source uses the
same version or that a live JIT trampoline was correctly registered.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
import struct

SCHEMA="BG_EET_RU_V132_INSTALLED_EEEX_X64_AND_EXACT_UNWIND_READONLY"
EXE_SHA="fc821a4806a0305b84fd85f1aad2bd472c8db642ed34b4494ae62351cae1c580"
HIT_START=0x39DA50
HIT_END=0x39E9DC
UNWIND_RVA=0x639100
CANDIDATE=0x39DA6F
EXPECTED_SIZE_OF_PROLOG=31
EXPECTED_SAVE_RBX_OFFSET=216
MAX_GAME_EXE=16_000_000
MAX_SCRIPT=1_000_000
ASM_PATH="EEex_scripts/EEex_Assembly_x86-64.lua"
PATCH_PATH="EEex_scripts/EEex_Sprite_Patch.lua"
DB_PATH="InfinityLoader.db"
UPSTREAM_GITHUB="Bubb13/EEex/EEex/copy/EEex_scripts/EEex_Assembly_x86-64.lua"
UPSTREAM_BLOB_SHA="e8c6a2fe303fdac3e92d9df9ea25c6a7af1e5a5c"

# Deliberately require the entire call chain instead of the word JIT alone.
ASSEMBLY_MARKERS={
    "hook_before_restore_signature":"function EEex_HookBeforeRestoreWithLabels(",
    "hook_call_internal_signature":"function EEex_HookCallInternal(",
    "jit_near":"EEex_JITNear(",
    "jit_at":"EEex_JITAt(",
    "function_table_writer":"function EEex_Assembly_Private_WriteAndRegisterFunctionTable(",
    "function_table_postjit":"function EEex_Assembly_Private_PostJIT(",
    "lookup_original_function_entry":"EEex_RtlLookupFunctionEntry(",
    "register_jit_function_table":"EEex_RtlAddFunctionTable(",
    "make_prolog":"#MAKE_PROLOG",
    "hook_integrity_watchdog":"EEex_HookIntegrityWatchdog_",
}
FIRSTCALL_LABEL="Hook-CGameSprite::Hit()-FirstCall"

class Hold(ValueError):
    pass

def sha(blob:bytes)->str:return hashlib.sha256(blob).hexdigest()

def u16(buf:bytes,index:int)->int:
    if index<0 or index+2>len(buf):raise Hold("U16_OUT_OF_RANGE")
    return struct.unpack_from("<H",buf,index)[0]

def u32(buf:bytes,index:int)->int:
    if index<0 or index+4>len(buf):raise Hold("U32_OUT_OF_RANGE")
    return struct.unpack_from("<I",buf,index)[0]

def pe_unwind_raw(data:bytes,*,require_pin=True)->dict:
    """Read only on-disk PE data; reject unpinned or malformed source."""
    if not isinstance(data,bytes) or not 0x400<=len(data)<=MAX_GAME_EXE:
        raise Hold("PE_SIZE_HOLD")
    if require_pin and sha(data)!=EXE_SHA:
        raise Hold("BALDUR_EXE_SHA_DRIFT_HOLD")
    if data[:2]!=b"MZ":raise Hold("NO_DOS_HEADER")
    pe=u32(data,0x3c)
    if pe<0x40 or pe+24>len(data) or data[pe:pe+4]!=b"PE\0\0":
        raise Hold("NO_PE_HEADER")
    coff=pe+4
    if u16(data,coff)!=0x8664:raise Hold("NOT_AMD64")
    nsec=u16(data,coff+2)
    opt=coff+20
    opt_len=u16(data,coff+16)
    if not 1<=nsec<=64 or opt_len<0xF0 or opt+opt_len+nsec*40>len(data):
        raise Hold("INVALID_SECTION_TABLE")
    if u16(data,opt)!=0x20b:raise Hold("NOT_PE32PLUS")
    if u32(data,opt+0x6c)<4:raise Hold("MISSING_EXCEPTION_DIRECTORY")
    ex_rva=u32(data,opt+0x70+3*8)
    ex_size=u32(data,opt+0x70+3*8+4)
    if ex_size<12 or ex_size>2_000_000 or ex_size%12:
        raise Hold("PDATA_DIRECTORY_MALFORMED")
    sections=[]
    for i in range(nsec):
        p=opt+opt_len+i*40
        name=data[p:p+8].split(b"\0")[0].decode("ascii","replace")
        virtual_size=u32(data,p+8);rva=u32(data,p+12)
        raw_size=u32(data,p+16);raw_off=u32(data,p+20)
        if raw_size and (raw_off>len(data) or raw_off+raw_size>len(data)):
            raise Hold("SECTION_RAW_OUT_OF_RANGE")
        sections.append((name,rva,raw_size,raw_off,virtual_size))
    def section_bytes(rva:int,size:int,names:tuple[str,...])->bytes:
        if rva<=0 or size<=0 or size>2_000_000:raise Hold("INVALID_RVA_OR_SIZE")
        cand=[(raw_off+rva-start,raw_off) for name,start,raw_len,raw_off,_ in sections
              if name in names and rva>=start and rva+size<=start+raw_len]
        if len(cand)!=1:raise Hold("RVA_SECTION_NOT_UNIQUE")
        return data[cand[0][0]:cand[0][0]+size]
    pdata=section_bytes(ex_rva,ex_size,(".pdata",))
    matched=[]
    for pos in range(0,len(pdata),12):
        begin,end,info=struct.unpack_from("<III",pdata,pos)
        if begin<=HIT_START<end:matched.append((begin,end,info))
    if len(matched)!=1:raise Hold("HIT_RUNTIME_FUNCTION_COUNT_HOLD")
    begin,end,info_rva=matched[0]
    if (begin,end,info_rva)!=(HIT_START,HIT_END,UNWIND_RVA):
        raise Hold("HIT_RUNTIME_FUNCTION_UNWIND_RVA_DRIFT")
    if section_bytes(CANDIDATE,6,(".text",))!=bytes.fromhex("4c8bf2488bd9"):
        raise Hold("SIX_BYTE_CANDIDATE_DRIFT")
    if section_bytes(0x39DA75,7,(".text",))!=bytes.fromhex("488d15a1c92400"):
        raise Hold("RIP_RELATIVE_BOUNDARY_DRIFT")
    xdata=section_bytes(info_rva,4,(".xdata",".rdata"))
    version=xdata[0]&7
    flags=xdata[0]>>3
    prolog=xdata[1];count=xdata[2]
    frame=xdata[3]&15
    frame_offset=xdata[3]>>4
    if version!=1 or flags!=0 or prolog!=EXPECTED_SIZE_OF_PROLOG or frame!=0 or frame_offset!=0 or count<10 or count>50:
        raise Hold("WIN64_UNWIND_HEADER_DRIFT")
    slots=section_bytes(info_rva+4,count*2,(".xdata",".rdata"))
    records=[]
    index=0
    while index<count:
        offset=slots[index*2];op=slots[index*2+1]&15;reg=slots[index*2+1]>>4
        extra=(2 if op==1 and reg==1 else 1 if op==1 and reg==0 else
               1 if op in (4,8) else 2 if op in (5,9) else
               0 if op in (0,2,3,10) else None)
        if extra is None or index+extra>=count or offset>prolog:
            raise Hold("UNWIND_OPCODE_OR_SLOT_DRIFT")
        operand=None
        if extra:
            operand=u32(slots,(index+1)*2) if extra==2 else u16(slots,(index+1)*2)
        records.append({"offset":offset,"opcode":op,"register":reg,"extra_slots":extra,
                        "operand":operand})
        index+=1+extra
    save=[x for x in records if x["opcode"]==4 and x["register"]==3 and x["offset"]==31]
    alloc=[x for x in records if x["opcode"]==2 and x["register"]==15 and x["offset"]==31]
    pushes=[x for x in records if x["opcode"]==0]
    expected_pushes={5,6,7,12,13,14,15}
    if len(save)!=1 or len(alloc)!=1 or len(pushes)!=7 or {x["register"] for x in pushes}!=expected_pushes:
        raise Hold("EXPECTED_RBX_SAVE_ALLOC_PUSHES_UNWIND_DRIFT")
    rbxdistance=save[0]["operand"]*8
    if rbxdistance!=EXPECTED_SAVE_RBX_OFFSET:
        raise Hold("RBX_UNWIND_RAW_SAVE_OFFSET_NOT_216")
    if not (HIT_START+prolog==CANDIDATE):
        raise Hold("NOT_EXACT_END_OF_PROLOGUE")
    return {
      "status":"RAW_WIN64_SAVE_RBX_OFFSET_AND_POST_PROLOG_STATIC_PASS",
      "game_exe_sha256":sha(data),
      "real_exe_pin_checked":require_pin,
      "unwind_info_rva":hex(info_rva),
      "unwind_code_slot_count":count,
      "unwind_record_count":len(records),
      "unwind_raw_sha256":sha(xdata+slots),
      "raw_save_rbx_encoded_scaled_offset":save[0]["operand"],
      "raw_save_rbx_stack_offset_bytes":rbxdistance,
      "raw_rbx_offset_exact_216_verified":True,
      "alloc_stack_bytes":alloc[0]["register"]*8+8,
      "push_nonvolatile_count":len(pushes),
      "exact_6_byte_post_prolog_candidate":hex(CANDIDATE),
      "unwind_version":version,
      "unwind_flags":flags,
      "game_file_writes":0,
    }

def source_audit(raw:bytes)->dict:
    if not isinstance(raw,bytes) or not 5000<=len(raw)<=MAX_SCRIPT:
        raise Hold("EEEX_X64_ASSEMBLY_SOURCE_SIZE_HOLD")
    text=raw.decode("utf8","strict")
    anchors={k:text.count(pattern) for k,pattern in ASSEMBLY_MARKERS.items()}
    all_pass=all(n>=1 for n in anchors.values())
    # Only anchoring callsites does not prove installed runtime module loading
    # or full correctness of registered JIT unwind entries.
    return {
      "status":"INSTALLED_SOURCE_JIT_UNWIND_PRIMITIVES_PRESENT_RUNTIME_HOLD" if all_pass
               else "INSTALLED_SOURCE_MISSING_REQUIRED_API_HOLD",
      "installed_source_sha256":sha(raw),
      "installed_source_bytes":len(raw),
      "matches_upstream_source_blob":"NOT_PROVEN_FROM_GIT_BLOB_HASH",
      "upstream_repository_path":UPSTREAM_GITHUB,
      "upstream_git_blob_sha":UPSTREAM_BLOB_SHA,
      "symbol_counts":anchors,
      "all_required_symbols_present":all_pass,
      "installed_eeex_runtime_loaded_verified":False,
      "rtl_lookup_runtime_owner_verified":False,
      "jit_unwind_registration_runtime_verified":False,
    }

def read_regular(root:Path,relative:str,max_size:int)->bytes:
    p=root.joinpath(*relative.split("/"))
    if p.is_symlink() or not p.is_file() or p.stat().st_size>max_size:
        raise Hold("MISSING_OR_UNSAFE:"+relative)
    return p.read_bytes()

def audit_game(root:Path)->dict:
    root=Path(root)
    result={
      "schema":SCHEMA,
      "status":"STATIC_SOURCE_OR_RAW_XDATA_HOLD",
      "game_files_written":0,"gameplay_verified":False,
      "native_hook_install_allowed":False,
      "eeex_existing_firstcall_owner_verified":False,
      "runtime_jit_unwind_proven":False,
      "native_registers_preserved_proven":False,
      "user_visible_combat_row_join_verified":False,
      "notes":"Source anchors cannot establish installed live EEex JIT owner or safe atomic rollback",
    }
    try:
        exe=read_regular(root,"Baldur.exe",MAX_GAME_EXE)
        result["unwind"]=pe_unwind_raw(exe)
    except (Hold,OSError,UnicodeError) as e:
        result["unwind"]={"status":"HOLD","reason":str(e)[:140]}
    try:
        source=read_regular(root,ASM_PATH,MAX_SCRIPT)
        result["eeex_x64"]=source_audit(source)
    except (Hold,OSError,UnicodeError) as e:
        result["eeex_x64"]={"status":"HOLD","reason":str(e)[:140]}
    try:
        patch=read_regular(root,PATCH_PATH,MAX_SCRIPT)
        result["eeex_sprite_patch_sha256"]=sha(patch)
        result["eeex_sprite_patch_matches_v104_recorded"]=sha(patch)=="e301b46770477cf29e3d39d6591a5a9fba4f3aeafa03c3dbfa75f7ef6bc13b7f"
    except (Hold,OSError):
        result["eeex_sprite_patch_status"]="MISSING_OR_UNSAFE_HOLD"
    try:
        db=read_regular(root,DB_PATH,2_000_000)
        result["infinityloader_db_sha256"]=sha(db)
        result["firstcall_label_present_in_db"]=FIRSTCALL_LABEL.encode("ascii") in db
    except (Hold,OSError):
        result["infinityloader_db_status"]="MISSING_OR_UNSAFE_HOLD"
    if (result["unwind"].get("status")=="RAW_WIN64_SAVE_RBX_OFFSET_AND_POST_PROLOG_STATIC_PASS"
        and result["eeex_x64"].get("all_required_symbols_present") is True
        and result.get("firstcall_label_present_in_db") is True):
        result["status"]="REAL_XDATA_AND_INSTALLED_EEEX_STATIC_CONTRACT_PASS_RUNTIME_HOLD"
    else:
        result["status"]="STATIC_SOURCE_OR_RAW_XDATA_HOLD"
    return result

if __name__=="__main__":
    import argparse,json
    p=argparse.ArgumentParser()
    p.add_argument("game_dir",type=Path)
    a=p.parse_args()
    print(json.dumps(audit_game(a.game_dir),ensure_ascii=False,indent=2))
