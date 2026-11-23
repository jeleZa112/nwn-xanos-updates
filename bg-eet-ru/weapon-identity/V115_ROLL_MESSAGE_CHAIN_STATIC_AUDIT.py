# coding: utf-8
"""BG_EET_RU V115: evaluate exact archived x64 function slices, never write to the game.

Research tool only. The private player's original function bytes are not embedded,
exported, uploaded or copied by this script. This checks an independent archived
V68 extraction against a later V107 static fingerprint of the same game EXE.
"""
import argparse
import hashlib
import json
import struct
import zipfile
from pathlib import Path

SCHEMA = "BG_EET_RU_V115_ROLL_AND_MESSAGE_SAME_FUNCTION_SOURCE_ONLY"
ATTACK_FUNC = "19_V68_COMBAT_CODE/functions/0039DA50_0039E9DC.bin"
DAMAGE_FUNC = "19_V68_COMBAT_CODE/functions/0038FBF0_00390F3C.bin"
ANCHORS = {
    "roll_format_string_rip_lea": (0x39DADA, "488d15", 0x5AD308),
    "roll_string_format_call": (0x39DAF3, "e8", 0x3FE080),
    "attacker_object_id_load": (0x39E7C9, "8b7b48", None),
    "message_id_field_a": (0x39E7D6, "897e0c", None),
    "message_id_field_b": (0x39E7E7, "897e08", None),
    "message_text_field": (0x39E80B, "488d4e18", None),
    "message_text_copy_call": (0x39E80F, "e8", 0x3FCE30),
    "handler_global_object": (0x39E837, "488b0d", None),
    "handler_receiver_offset": (0x39E841, "4881c168170000", None),
    "message_arg_ptr": (0x39E848, "488bd6", None),
    "message_send_call": (0x39E84B, "e8", 0x204C60),
}
DAMAGE_SEND_CALLS = (0x39049D, 0x39052E, 0x390918, 0x390E6F)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read_bounded(z, name, max_bytes=40000):
    info=z.getinfo(name)
    if info.file_size > max_bytes or info.file_size < 1:
        raise ValueError("V115_RESOURCE_SIZE_HOLD: " + name)
    raw=z.read(name)
    if len(raw) != info.file_size:
        raise ValueError("V115_ZIP_SIZE_MISMATCH")
    return raw


def anchored_slice(raw, base, absolute, length):
    off=absolute-base
    if off<0 or off+length>len(raw):
        raise ValueError("V115_ADDRESS_OUT_OF_ARCHIVED_SLICE")
    return raw[off:off+length]


def relative_target(raw, base, location, instruction_size=5, lead=b'\xe8'):
    fragment=anchored_slice(raw,base,location,instruction_size)
    if not fragment.startswith(lead):
        raise ValueError("V115_CALL_OR_RIP_INSTRUCTION_MISMATCH")
    delta=struct.unpack_from('<i',fragment,len(lead))[0]
    return location+instruction_size+delta


def verify_anchor(raw, base, name, spec):
    address,expected,expected_target=spec
    lead=bytes.fromhex(expected)
    current=anchored_slice(raw,base,address,len(lead))
    if current!=lead:
        raise ValueError("V115_SOURCE_SIGNATURE_DRIFT:"+name)
    found_target=None
    if expected_target is not None:
        found_target=relative_target(raw,base,address,7 if lead==bytes.fromhex('488d15') else 5,lead)
        if found_target!=expected_target:
            raise ValueError("V115_BRANCH_TARGET_DRIFT:"+name)
    return {"name":name,"site_rva":f"0x{address:06X}",
            "instruction_type":"RIP_LEA" if len(lead)==3 else ("CALL" if lead==b'\xe8' else "DATA_MOVE"),
            "verified":True,"resolved_target_rva":f"0x{found_target:06X}" if found_target is not None else None}


def analyze_bytes(attack, damage):
    if len(attack)!=3980 or len(damage)!=4940:
        raise ValueError("V115_FUNCTION_LENGTH_DRIFT")
    verified=[verify_anchor(attack,0x39DA50,name,item) for name,item in ANCHORS.items()]
    damage_targets=[]
    for address in DAMAGE_SEND_CALLS:
        dest=relative_target(damage,0x38FBF0,address)
        if dest!=0x204C60:
            raise ValueError("V115_DAMAGE_DISPATCH_TARGET_DRIFT")
        damage_targets.append({"site_rva":f"0x{address:06X}","resolved_target_rva":f"0x{dest:06X}"})
    return {"attack_function_rva":"0x39DA50","attack_function_bytes":len(attack),
            "damage_function_rva":"0x38FBF0","damage_function_bytes":len(damage),
            "verified_attack_function_anchors":verified,
            "verified_shared_message_send_calls_in_damage_function":damage_targets,
            "shared_dispatch_target_rva":"0x204C60",
            "callsite_count_to_shared_dispatch":1+len(damage_targets),
            "proven_directly_by_bytes": [
                "Roll:%d RIP-relative format-string reference in 0x39DA50 function",
                "The same function calls string formatter and constructs an object with attacker id fields",
                "A text field is copied into the object before a single same-function dispatch call",
                "The other captured damage function also calls the same dispatch RVA four times"
            ],
            "not_proven": [
                "0x204C60 function body/actual symbol (not present in archived slices)",
                "every roll results in the displayed combatLog[rowNumber] row",
                "event callback for miss as well as hit with verified weapon CItem",
                "same unique event/row identity or guaranteed event order",
                "weapon and launcher RESREF availability at this dispatch site",
                "safety or ABI of any runtime intervention"
            ]}


def report_from_zip(path):
    with zipfile.ZipFile(path) as z:
        names=z.namelist()
        if len(names)!=len(set(names)) or z.testzip() is not None:
            raise ValueError("V115_BAD_ARCHIVE_CRC_OR_DUPLICATE_ENTRY")
        v68=json.loads(read_bounded(z,"19_V68_COMBAT_CODE_STATUS.json",10000))
        v107=json.loads(read_bounded(z,"53_V107_CITEM_STATIC_ABI_PREFLIGHT.json",30000))
        refs=json.loads(read_bounded(z,"19_V68_COMBAT_CODE_REFERENCES.json",200000))
        expected=v68['exe_sha256']
        observed=v107['files']['Baldur.exe']['sha256']
        if len(expected)!=64 or expected!=observed:
            raise ValueError("V115_SOURCE_EXE_BUILD_MISMATCH_HOLD")
        if expected!="fc821a4806a0305b84fd85f1aad2bd472c8db642ed34b4494ae62351cae1c580":
            raise ValueError("V115_EXE_SHA_NOT_PINNED")
        target_refs=[r for r in refs if r.get('source_en')=='Roll:%d' and
                     any(x.get('function',{}).get('begin_rva')==0x39DA50 and x.get('ins_rva')==0x39DADA for x in r.get('refs',[]))]
        if len(target_refs)!=1 or target_refs[0].get('source_rva')!=0x5AD308:
            raise ValueError("V115_ROLL_STRING_REFERENCE_HOLD")
        attack=read_bounded(z,ATTACK_FUNC)
        damage=read_bounded(z,DAMAGE_FUNC)
        chain=analyze_bytes(attack,damage)
    return {"schema":SCHEMA,"status":"V115_SAME_FUNCTION_ROLL_TEXT_AND_SHARED_DISPATCH_CONFIRMED_STATIC_ONLY",
            "evidence_kind":"ARCHIVED_PRIVATE_GAME_EXE_BYTE_SLICES_STATIC_DISASSEMBLY_CROSSCHECK",
            "source_archive_name":Path(path).name,
            "source_archive_sha256":digest(Path(path).read_bytes()),
            "v68_v107_installed_exe_sha256_equal":True,
            "current_exe_sha256_at_snapshot":expected,
            "code_windows_sha256_only": {"roll_and_message_function":digest(attack),"damage_function":digest(damage)},
            "chain":chain,
            "interpretation":"Call target 0x204C60 has message-dispatch-like signature but symbol and combatLog append unverified; exact actor/weapon/row event join remains HOLD",
            "conclusion_gates":{"roll_and_dispatch_in_same_captured_function":True,
                "identical_dispatch_target_in_other_function":True,
                "raw_message_dispatch_target_body_captured":False,
                "exact_dispatch_function_symbol_verified":False,
                "combatLog_row_append_verified":False,
                "per_roll_weapon_launcher_verified":False,
                "miss_weapon_identity_verified":False,
                "join_install_authorized":False},
            "game_files_written":0,"new_hook_installed":False,"updater_modified":False}


def selftest():
    # Synthetic private byte slices only; never loads a game or edits a save.
    attack=bytearray(3980);damage=bytearray(4940)
    for name,(addr,hexlead,target) in ANCHORS.items():
        prefix=bytes.fromhex(hexlead);i=addr-0x39DA50
        attack[i:i+len(prefix)]=prefix
        if target is not None:
            length=7 if len(prefix)==3 else 5
            struct.pack_into('<i',attack,i+len(prefix),target-(addr+length))
    for addr in DAMAGE_SEND_CALLS:
        i=addr-0x38FBF0;damage[i]=0xe8
        struct.pack_into('<i',damage,i+1,0x204C60-(addr+5))
    scenarios=0
    assert analyze_bytes(attack,damage)['callsite_count_to_shared_dispatch']==5;scenarios+=1
    for name,(addr,_,_) in ANCHORS.items():
        bad=bytearray(attack);bad[addr-0x39DA50]^=0xff
        try:analyze_bytes(bad,damage)
        except ValueError:pass
        else:raise AssertionError('mutation did not trigger fail-closed: '+name)
        scenarios+=1
    for addr in DAMAGE_SEND_CALLS:
        bad=bytearray(damage);bad[addr-0x38FBF0+1]^=1
        try:analyze_bytes(attack,bad)
        except ValueError:pass
        else:raise AssertionError('damage dispatch drift undetected')
        scenarios+=1
    try:analyze_bytes(attack[:-1],damage)
    except ValueError:pass
    else:raise AssertionError('truncated source accepted')
    scenarios+=1
    try:anchored_slice(attack,0x39DA50,0x39DA49,7)
    except ValueError:pass
    else:raise AssertionError('off-range source accepted')
    scenarios+=1
    return {"status":"V115_SYNTHETIC_SOURCE_ONLY_PASS","scenarios":scenarios}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--archive',type=Path)
    p.add_argument('--out',type=Path)
    p.add_argument('--selftest',action='store_true')
    args=p.parse_args()
    output={"selftest":selftest()}
    if args.archive:
        output.update(report_from_zip(args.archive))
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in output.items() if k in ('selftest','status','conclusion_gates')},ensure_ascii=False,indent=2))

if __name__=='__main__':main()