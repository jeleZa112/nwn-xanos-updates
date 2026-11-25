"""BG_EET_RU V139 -- bounded exact PE target and combat dispatch evidence, READ ONLY.

The native target at RVA 0x398530 is called from both Hit and Damage and is
NOT proven to directly populate combatLog or be CScreenWorld::DisplayText.
Everything in this module is SOURCE_ONLY. It never hooks or modifies a game.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path
from zipfile import ZipFile, BadZipFile

SCHEMA = 'BG_EET_RU_V139_EXACT_DISPATCH_CALLEE_PROVENANCE_SOURCE_ONLY'
GAME_EXE_SHA = 'fc821a4806a0305b84fd85f1aad2bd472c8db642ed34b4494ae62351cae1c580'
ARCHIVE_SHA = '8a9596b461887e41c859704b264d49fcbc2bb0d6a86269f164095878db41686d'
HIT_FILE = '19_V68_COMBAT_CODE/functions/0039DA50_0039E9DC.bin'
DAMAGE_FILE = '19_V68_COMBAT_CODE/functions/0038FBF0_00390F3C.bin'
UI_FILE = '35_V87_COMBAT_JOURNAL_UI_BINDING_EXACT_SOURCE.json'
ROWS_FILE = '63_V126_VISIBLE_ROW_OBSERVER.json'
HIT_RVA, HIT_END = 0x39DA50, 0x39E9DC
DAMAGE_RVA, DAMAGE_END = 0x38FBF0, 0x390F3C
TARGET_RVA = 0x398530
MAX_CALLEE_BYTES = 16384
HIT_SHA = '19c1d11b7ac41d261d22b19506b3570427e356544e48f2e2c622c1efdb74cc79'
# Published unmodified Hit and Damage slices in the user's V68 evidence.
DAMAGE_SHA = '59fa0cdbc7206698acd7bd49c7c68807a02d9318a001f13911e04d0d5e49723a'
# For every site, an exact known instruction that establishes the numeric EDX argument.
# This is a machine-code argument, not a semantic attack-outcome or UI type.
HIT_DISPATCH = [
    (0x39E661, 0x39E658, '418d5128', 40, 'edx=r9d+40, with preceding r9d=0'),
    (0x39E754, 0x39E74B, '418d5103', 3, 'edx=r9d+3, with preceding r9d=0'),
    (0x39E89E, 0x39E883, 'ba04000000', 4, 'edx=4; r9d from r14d before call'),
]
DAMAGE_DISPATCH = [
    (0x39027B, 0x390278, '8d5053', 83, 'edx=eax+83, with preceding eax=0'),
    (0x3902E2, 0x3902DF, '8d5053', 83, 'edx=eax+83, with preceding eax=0'),
    (0x39056E, 0x39056B, '8d5052', 82, 'edx=eax+82, with preceding eax=0'),
    (0x3905C5, 0x3905C2, '8d5051', 81, 'edx=eax+81, with preceding eax=0'),
    (0x39071F, 0x39071C, '8d5040', 64, 'edx=eax+64, with preceding eax=0'),
    (0x390781, 0x39077E, '8d5040', 64, 'edx=eax+64, with preceding eax=0'),
    (0x390954, 0x390951, '8d5001', 1, 'edx=eax+1, with preceding eax=0'),
    (0x3909A5, 0x3909A2, '8d501c', 28, 'edx=eax+28, with preceding eax=0'),
]

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


def _all_target_call_offsets(code: bytes, start: int, target=TARGET_RVA):
    hits=[]
    for off in range(len(code)-4):
        if code[off]==0xe8:
            displacement=struct.unpack_from('<i',code,off+1)[0]
            if start+off+5+displacement==target:
                hits.append(start+off)
    return hits


def verify_dispatch(code: bytes, start: int, end: int, source_sha: str, specs: list[tuple]):
    if type(code) is not bytes or len(code)!=end-start or digest(code)!=source_sha:
        raise Hold('PINNED_CALLER_FUNCTION_SHA_MISMATCH')
    expected=[s[0] for s in specs]
    if _all_target_call_offsets(code,start)!=expected:
        raise Hold('SHARED_DISPATCH_CALLSITE_SET_DRIFT')
    out=[]
    for call_rva, arg_rva, encoded, numeric, descr in specs:
        call=code[call_rva-start:call_rva-start+5]
        if len(call)!=5 or call[0]!=0xe8 or call_rva+5+struct.unpack('<i',call[1:])[0]!=TARGET_RVA:
            raise Hold('EXACT_CALL_TO_DISPATCH_CHANGED')
        payload=bytes.fromhex(encoded)
        if code[arg_rva-start:arg_rva-start+len(payload)]!=payload:
            raise Hold('EXACT_ARGUMENT_INSTRUCTION_CHANGED')
        out.append({'call_rva':hex(call_rva),'edx_instruction_rva':hex(arg_rva),
                    'numeric_edx_candidate':numeric,'source_argument_evidence':descr,
                    'semantic_row_type_proven':False})
    return out


def audit_zip(zbytes: bytes):
    if type(zbytes) is not bytes or digest(zbytes)!=ARCHIVE_SHA:
        raise Hold('PINNED_USER_ARCHIVE_SHA_MISMATCH')
    try:
        with ZipFile(__import__('io').BytesIO(zbytes)) as z:
            if z.testzip() is not None: raise Hold('USER_ARCHIVE_CRC_ERROR')
            names=z.namelist()
            if len(names)!=len(set(names)):raise Hold('USER_ARCHIVE_DUPLICATE_ENTRY')
            hit=z.read(HIT_FILE)
            damage=z.read(DAMAGE_FILE)
            ui=json.loads(z.read(UI_FILE))
            rows=json.loads(z.read(ROWS_FILE))
    except (KeyError,BadZipFile,ValueError) as e:
        raise Hold('USER_ARCHIVE_EVIDENCE_UNREADABLE') from e
    h=verify_dispatch(hit,HIT_RVA,HIT_END,HIT_SHA,HIT_DISPATCH)
    d=verify_dispatch(damage,DAMAGE_RVA,DAMAGE_END,DAMAGE_SHA,DAMAGE_DISPATCH)
    renderer=ui.get('ui',{}).get('anchors',{}).get('text_renderer',{}).get('source',{}).get('text','')
    clean=ui.get('ui',{}).get('anchors',{}).get('clean_definition',{}).get('source',{}).get('text','')
    if 'clean(combatLog[rowNumber])' not in renderer or 'function clean(str)' not in clean:
        raise Hold('PINNED_UI_CONSUMER_MISSING')
    samples=rows.get('captured',{}).get('samples',[])
    if rows.get('captured',{}).get('rows')!=72 or len(samples)!=72:
        raise Hold('PINNED_VISIBLE_ROW_COUNT_DRIFT')
    return {
        'status':'V139_PINNED_CALLSITE_ARGUMENTS_AND_UI_CONSUMER_SOURCE_PASS',
        'exact_hit_caller_sha256':digest(hit),'exact_damage_caller_sha256':digest(damage),
        'shared_callee_rva':hex(TARGET_RVA),'hit_calls':h,'damage_calls':d,
        'displayed_rows':len(samples),
        'ui_consumer':'clean(combatLog[rowNumber])',
        'call_target_to_ui_chain_verified':False,
        'direct_render_token_verified':False,
        'gameplay_verified':False,'game_files_written':0,'native_hooks_installed':False,
    }


def run(archive: Path, game: Path|None=None):
    out={
        'schema':SCHEMA,'status':'V139_SOURCE_ONLY_HOLD',
        'game_files_written':0,'native_hooks_installed':False,
        'gameplay_verified':False,'safe_to_install':False,
        'firstcall_owner_verified':False,'win64_runtime_unwind_verified':False,
        'per_attempt_hit_miss_verified':False,'visible_row_join_verified':False,
    }
    try:
        out.update(audit_zip(archive.read_bytes()))
        if game is None:
            out['reason']='DISPATCH_CALLEE_BYTES_NOT_CAPTURED_FROM_PINNED_GAME'
            out['status']='V139_PINNED_CALLSITE_PASS_DISPATCH_CALLEE_HOLD'
        else:
            exe=game.resolve(strict=True)/'Baldur.exe'
            if exe.is_symlink() or not exe.is_file():raise Hold('GAME_EXE_NOT_REGULAR_FILE')
            out['callee']=extract_pdata_function(exe.read_bytes())
            out['status']='V139_PINNED_FUNCTION_EXTRACTED_SEMANTIC_PROVENANCE_HOLD'
            out['reason']='CALLEE_BYTES_CAPTURED_BUT_DIRECT_ROW_CHAIN_UNVERIFIED'
    except (Hold, OSError, ValueError) as e:
        out['status']='V139_SOURCE_ONLY_HOLD'
        out['reason']=str(e)[:130]
    return out


def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument('--archive',type=Path,required=True)
    p.add_argument('--game',type=Path)
    p.add_argument('--output',type=Path)
    a=p.parse_args(argv)
    result=run(a.archive,a.game)
    if a.output:
        dest=a.output.expanduser().resolve()
        if a.output.is_symlink() or (a.game and (dest==a.game.resolve() or a.game.resolve() in dest.parents)):
            raise SystemExit('REPORT_OUTPUT_IN_GAME_ROOT_FORBIDDEN')
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(result['status'])
    return 0 if result['status']!='V139_SOURCE_ONLY_HOLD' else 2

if __name__=='__main__':raise SystemExit(main())
