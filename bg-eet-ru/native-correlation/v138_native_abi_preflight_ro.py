"""BG_EET_RU V138: SOURCE-ONLY native ABI/Win64 COFF + real-archive gate.

Compiled COFF .pdata/.xdata existence does NOT establish a safe EEex hook,
remote JIT unwind registration, SEH safety, or game behavior. This validator
never loads an object into Baldur.exe; no process APIs, patches, or hooks.
"""
from __future__ import annotations
import hashlib
import json
import struct
import zipfile
from pathlib import Path

SCHEMA='BG_EET_RU_V138_NATIVE_LEDGER_COFF_ABI_SOURCE_PREFLIGHT'
USER_ZIP_SHA='8a9596b461887e41c859704b264d49fcbc2bb0d6a86269f164095878db41686d'
HIT_NAME='19_V68_COMBAT_CODE/functions/0039DA50_0039E9DC.bin'
HIT_SHA='19c1d11b7ac41d261d22b19506b3570427e356544e48f2e2c622c1efdb74cc79'
HIT_BASE=0x39DA50
ANCHORS={
 'entry_after_native_prolog':(0x39DA6F,'4c8bf2488bd9'),
 'ability_from_r9d':(0x39DA7C,'418bf1'),
 'item_from_r8':(0x39DA83,'4d8bf8'),
 'existing_firstcall_original':(0x39DA86,'e8e5f20500'),
 'raw_return_byte_to_eax':(0x39E9A3,'410fb6c6'),
 'stack_restore':(0x39E9A7,'4881c480000000'),
 'branch_bypasses_conditional_message':(0x39E7B3,'0f859c000000'),
 'conditional_message':(0x39E84B,'e81064e6ff'),
}

class Hold(ValueError):pass

def sha(data:bytes)->str:return hashlib.sha256(data).hexdigest()

def audit_coff(data:bytes)->dict:
    """Parse PE COFF headers and exact .pdata/.xdata records, no linker needed."""
    if type(data) is not bytes or len(data)<60:
        raise Hold('COFF_TRUNCATED')
    machine,nsections,_,_,_,optional,_=struct.unpack_from('<HHLLLHH',data)
    if machine!=0x8664 or not 3<=nsections<=32 or optional!=0:
        raise Hold('NOT_AMD64_COFF_OBJECT')
    if len(data)<20+nsections*40:raise Hold('COFF_SECTION_TABLE_TRUNCATED')
    sections={}
    for i in range(nsections):
        name,_,_,size,ptr,relocptr,_,numreloc,_,flags=struct.unpack_from(
            '<8sLLLLLLHHL',data,20+i*40)
        name=name.rstrip(b'\0').decode('ascii','replace')
        if name in sections:raise Hold('COFF_DUPLICATE_SECTION')
        if size and not (ptr==0 and flags&0x80):
            if ptr==0 or ptr>len(data) or size>len(data)-ptr:
                raise Hold('COFF_SECTION_DATA_OUT_OF_BOUNDS')
        if numreloc and (relocptr==0 or relocptr>len(data) or numreloc*10>len(data)-relocptr):
            raise Hold('COFF_RELOCATIONS_OUT_OF_BOUNDS')
        sections[name]={'data':data[ptr:ptr+size] if size and ptr else b'',
                        'relocations':data[relocptr:relocptr+numreloc*10] if numreloc else b'',
                        'count':numreloc,'size':size,'flags':flags}
    if any(name not in sections for name in ('.text','.pdata','.xdata')):
        raise Hold('WIN64_UNWIND_SECTION_MISSING')
    pdata=sections['.pdata'];xdata=sections['.xdata']
    if pdata['size']<12 or pdata['size']%12 or xdata['size']<4:
        raise Hold('WIN64_UNWIND_DATA_INVALID_LENGTH')
    count=pdata['size']//12
    if pdata['count']!=count*3:
        raise Hold('WIN64_PDATA_RELOCATION_COUNT_NOT_EXACT')
    entries=[]
    for i in range(count):
        begin,end,unwind=struct.unpack_from('<LLL',pdata['data'],12*i)
        if end<=begin or end>sections['.text']['size'] or unwind+4>xdata['size']:
            raise Hold('WIN64_PDATA_ENTRY_INVALID')
        reloc=[]
        for j in range(3):
            offset,symbol,kind=struct.unpack_from('<LLH',pdata['relocations'],(i*3+j)*10)
            if offset!=i*12+j*4 or kind!=3:
                raise Hold('WIN64_PDATA_RELOCATION_INVALID')
            reloc.append(symbol)
        if reloc[0]!=reloc[1] or reloc[2]==reloc[0]:
            raise Hold('WIN64_PDATA_RELOCATION_SYMBOL_INVALID')
        hdr=xdata['data'][unwind:unwind+4]
        version=hdr[0]&7
        flags=hdr[0]>>3
        prolog=hdr[1];codes=hdr[2]
        if version!=1 or flags!=0 or codes==0 or prolog==0:
            raise Hold('WIN64_XDATA_HEADER_INVALID')
        code_len=4+2*codes+2*(codes%2)
        if unwind+code_len>xdata['size']:
            raise Hold('WIN64_XDATA_CODES_TRUNCATED')
        entries.append({'text_begin':begin,'text_end':end,'xdata_offset':unwind,
                        'unwind_version':version,'prolog_size':prolog,'code_count':codes})
    return {'coff_amd64':True,'coff_sha256':sha(data),
            'section_text_bytes':sections['.text']['size'],
            'unwind_entries_count':count,'win64_compiler_emitted_pdata_xdata':True,
            'unwind_entries':entries,
            'actual_runtime_registration_verified':False,
            'native_hook_or_injection_performed':False}

def audit_user_archive(data:bytes)->dict:
    if type(data) is not bytes or sha(data)!=USER_ZIP_SHA:raise Hold('USER_V136_ZIP_PIN_DRIFT')
    import io
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        if len(z.namelist())!=len(set(z.namelist())) or z.testzip() is not None:
            raise Hold('ZIP_DUPLICATES_OR_CRC')
        hit=z.read(HIT_NAME)
        v132=json.loads(z.read('65_V132_EEEX_ABI.json'))
        v136=json.loads(z.read('67_V136_LIVE_JIT_TARGET_RO.json'))
        v87=json.loads(z.read('35_V87_COMBAT_JOURNAL_UI_BINDING_EXACT_SOURCE.json'))
    if sha(hit)!=HIT_SHA:raise Hold('ORIGINAL_HIT_FUNCTION_SHA_DRIFT')
    for name,(rva,hexpart) in ANCHORS.items():
        raw=bytes.fromhex(hexpart)
        if hit[rva-HIT_BASE:rva-HIT_BASE+len(raw)]!=raw:
            raise Hold('HIT_MACHINE_CODE_DRIFT_'+name)
    # Exact branch 0x39E7B3 + 6 + signed(0x9C) = 0x39E855,
    # skips the call at 0x39E84B.
    disp=int.from_bytes(bytes.fromhex('9c000000'),'little',signed=True)
    if 0x39E7B3+6+disp!=0x39E855:
        raise Hold('ORIGINAL_HIT_MESSAGE_BYPASS_DRIFT')
    if (v136.get('status')!='V136_LIVE_PAIR_SITES_AND_EXECUTABLE_TARGET_OBSERVED_OWNER_HOLD'
        or v136.get('firstcall_owner_verified') is not False
        or v136.get('memory_snapshot_twice_equal') is not True):
        raise Hold('V136_LIVE_RUNTIME_EVIDENCE_DRIFT')
    unwind=v132.get('unwind',{})
    if (v132.get('status')!='REAL_XDATA_AND_INSTALLED_EEEX_STATIC_CONTRACT_PASS_RUNTIME_HOLD'
        or unwind.get('alloc_stack_bytes')!=128
        or unwind.get('raw_save_rbx_stack_offset_bytes')!=216):
        raise Hold('V132_ORIGINAL_HIT_UNWIND_DRIFT')
    txt=v87['ui']['anchors']['text_renderer']['source']['text']
    if 'text lua "clean(combatLog[rowNumber])"' not in txt:
        raise Hold('ACTUAL_UI_RENDERER_SOURCE_MISMATCH')
    return {'user_zip_sha256':sha(data),'original_hit_sha256':sha(hit),
            'machine_anchors_checked':len(ANCHORS),
            'source_ability_rva':'0x39da7c','source_item_rva':'0x39da83',
            'original_entry_candidate_rva':'0x39da6f',
            'raw_return_candidate_rva':'0x39e9a3',
            'message_bypass_verified':True,
            'actual_render_expression':'clean(combatLog[rowNumber])',
            'renderer_direct_token_available':False,
            'installed_eeex_firstcall_exists_owner_unverified':True,
            'native_live_owner_verified':False}

def audit(user_zip:Path,obj:Path)->dict:
    result={'schema':SCHEMA,'status':'V138_SOURCE_COMPILED_NATIVE_LEDGER_RENDER_HOLD',
           'game_files_written':0,'native_hooks_installed':False,
           'runtime_owner_verified':False,'native_hook_callback_abi_verified':False,
           'gameplay_verified':False,'exact_item_layout_verified':False,
           'direct_render_token_emitted_in_live_game':False,
           'return_0_is_miss_proven':False,'return_1_is_hit_proven':False,
           'safe_to_install':False}
    if user_zip.is_symlink() or obj.is_symlink():raise Hold('SOURCE_SYMLINK_FORBIDDEN')
    result['archive_proof']=audit_user_archive(user_zip.read_bytes())
    result['coff_proof']=audit_coff(obj.read_bytes())
    return result

def main(argv=None):
    import argparse
    p=argparse.ArgumentParser(description='BG EET RU V138 compiled C + real V136 source static preflight')
    p.add_argument('--user-zip',required=True,type=Path)
    p.add_argument('--win64-coff',required=True,type=Path)
    p.add_argument('--output',type=Path)
    args=p.parse_args(argv)
    r=audit(args.user_zip,args.win64_coff)
    if args.output:
        if args.output.resolve() in (args.user_zip.resolve(),args.win64_coff.resolve()):
            raise Hold('MUST_NOT_OVERWRITE_INPUT')
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    print(r['status'])
    return 0

if __name__=='__main__':raise SystemExit(main())
