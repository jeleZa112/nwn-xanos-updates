"""V129 SOURCE ONLY: prove an exact CGameSprite::Hit() path BYPASSES AddMessage.

The original V4 same-Hit -> CMessage design treated 0x39E84B as a
universal bridge. Actual pinned function bytes have explicit branches which
skip that CALL. Therefore an observer at this CALLSITE alone cannot
serve as a total attack-attempt event source (hit/miss completeness).

No process access, EEex code execution, Lua hooks or game writes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import zipfile

SCHEMA="BG_EET_RU_V129_CONDITIONAL_HIT_MESSAGE_COVERAGE_PROOF"
FUNC_PATH="19_V68_COMBAT_CODE/functions/0039DA50_0039E9DC.bin"
EXPECTED_FUNCTION_SHA="19c1d11b7ac41d261d22b19506b3570427e356544e48f2e2c622c1efdb74cc79"
FUNC_BASE=0x39DA50
FUNC_END=0x39E9DC
CALLSITE=0x39E84B
CALL_TARGET=0x204C60
BYPASS=0x39E855
SHARED_VTABLE=0x597CD0

# Exact byte patterns extracted from the user's EET executable function.
# Anchor names deliberately describe machine semantics, NOT game meaning.
SITES={
 "compare_0x182":(0x39E694,"3d82010000"),
 "branch_0x182":(0x39E699,"0f8401010000"),
 "compare_0x502":(0x39E69F,"3d02050000"),
 "branch_0x502":(0x39E6A4,"0f84f6000000"),
 "other_path_original_eax":(0x39E6AA,"418bc4"),
 "other_path_esi_1":(0x39E6AD,"be01000000"),
 "other_path_join":(0x39E6B2,"e9f0000000"),
 "forced_path_esi_1":(0x39E7A0,"be01000000"),
 "forced_path_eax_esi":(0x39E7A5,"8bc6"),
 "conditional_replace_eax":(0x39E7AE,"0f44c6"),
 "test_eax":(0x39E7B1,"85c0"),
 "jne_bypass":(0x39E7B3,"0f859c000000"),
 "send_message_call":(CALLSITE,"e81064e6ff"),
 "bypass_destination":(BYPASS,"6683bbf803000062"),
 "one_known_exit":(0x39E9B9,"c3"),
}

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def fragment(data:bytes,addr:int,length:int)->bytes:
    at=addr-FUNC_BASE
    if at<0 or at+length>len(data):
        raise ValueError("SOURCE_FUNCTION_RANGE_HOLD")
    return data[at:at+length]

def branch_target(code:bytes,addr:int):
    if len(code)==6 and code[:2] in (b'\x0f\x84',b'\x0f\x85'):
        return addr+6+struct.unpack("<i",code[2:])[0]
    if len(code)==5 and code[0] in (0xe8,0xe9):
        return addr+5+struct.unpack("<i",code[1:])[0]
    raise ValueError("NOT_A_PINNED_REL32_BRANCH")

def evaluate_function(binary:bytes,*,require_sha=True)->dict:
    if not isinstance(binary,bytes) or len(binary)!=(FUNC_END-FUNC_BASE):
        raise ValueError("HIT_FUNCTION_LENGTH_HOLD")
    digest=sha(binary)
    if require_sha and digest!=EXPECTED_FUNCTION_SHA:
        raise ValueError("HIT_FUNCTION_PINNED_SHA_MISMATCH_HOLD")
    checks={}
    for name,(rva,expected_hex) in SITES.items():
        pattern=bytes.fromhex(expected_hex)
        checks[name]=fragment(binary,rva,len(pattern))==pattern
    if not all(checks.values()):
        raise ValueError("HIT_FUNCTION_INSTRUCTION_DRIFT_HOLD")
    targets={
      "branch_0x182":branch_target(fragment(binary,0x39E699,6),0x39E699),
      "branch_0x502":branch_target(fragment(binary,0x39E6A4,6),0x39E6A4),
      "other_path_join":branch_target(fragment(binary,0x39E6B2,5),0x39E6B2),
      "jne_bypass":branch_target(fragment(binary,0x39E7B3,6),0x39E7B3),
      "send_message_call":branch_target(fragment(binary,CALLSITE,5),CALLSITE),
    }
    expected={
      "branch_0x182":0x39E7A0,
      "branch_0x502":0x39E7A0,
      "other_path_join":0x39E7A7,
      "jne_bypass":BYPASS,
      "send_message_call":CALL_TARGET,
    }
    if targets!=expected:
        raise ValueError("HIT_BRANCH_TARGETS_OR_MESSAGE_CALLEE_DRIFT_HOLD")
    if not (0x39E7A0<0x39E7A5<0x39E7B1<0x39E7B3<CALLSITE<BYPASS):
        raise ValueError("HIT_COVERAGE_ORDER_HOLD")
    # A path from either equality branch to 0x39E7A0 sets ESI=1,
    # then MOV EAX,ESI. CMOVE EAX,ESI cannot change EAX from 1.
    # TEST EAX,EAX makes JNE unconditionally jump over 0x39E84B.
    # This is a machine-code counterexample, not a claim about how often
    # those branches occur during gameplay or what 0x182/0x502 mean.
    return {
      "schema":SCHEMA,
      "status":"PINNED_SOURCE_PROVES_CONDITIONAL_MESSAGE_DISPATCH",
      "function_sha256":digest,
      "checks_passed":len(checks)+len(targets),
      "all_site_checks":checks,
      "conditional_paths":[{
        "compare_constant":"0x182",
        "trace_rva":["0x39e694","0x39e699","0x39e7a0","0x39e7a5","0x39e7ae","0x39e7b1","0x39e7b3","0x39e855"],
        "skips_message_callsite":True},
        {"compare_constant":"0x502",
        "trace_rva":["0x39e69f","0x39e6a4","0x39e7a0","0x39e7a5","0x39e7ae","0x39e7b1","0x39e7b3","0x39e855"],
        "skips_message_callsite":True}],
      "message_callsite":"0x39e84b",
      "message_callee":"0x204c60",
      "message_callsite_is_universal_event_source":False,
      "message_callsite_not_called_in_some_code_paths":True,
      "attack_coverage_in_actual_game":"NOT_MEASURED",
      "game_meaning_of_0x182_0x502":"UNKNOWN",
      "new_hook_installed":False,
      "game_files_written":0,
      "gameplay_verified":False,
      "engineering_decision":{
        "primary_attempt_event":"SOURCE_ONLY_PLAN_FUNCTION_ENTRY_WITH_PROVEN_ITEM_AND_OUTCOME",
        "optional_message_event":"CALLSITE_39E84B_MAY_BE_ABSENT",
        "ui_join":"REQUIRE_INDEPENDENT_EVENT_TO_DISPLAY_ROW_PROOF",
        "on_missing_message":"DO_NOT_CLASSIFY_AS_MISS_OR_ASSIGN_WEAPON",
        "keep_existing_v126_ui_observer":True,
        "native_install_allowed":False,
        "before_install":["Win64 ABI/XMM and original call frame correctness",
                          "EEex JIT ownership and multiple hooks/rollback",
                          "SEH/unwind and reentrancy", "explicit new typed authorization"],
      },
    }

def read_user_zip(path:Path)->bytes:
    if not path.is_file() or path.is_symlink():
        raise ValueError("USER_ZIP_UNSAFE")
    with zipfile.ZipFile(path) as z:
        names=z.namelist()
        if z.testzip() is not None or len(names)!=len(set(names)):
            raise ValueError("USER_ZIP_CRC_OR_UNIQUE_HOLD")
        return z.read(FUNC_PATH)

def evaluate_user_zip(path:Path)->dict:
    out=evaluate_function(read_user_zip(path))
    out["source_kind"]="HISTORICAL_USER_ZIP_SAME_FUNCTION_SHA"
    with zipfile.ZipFile(path) as z:
        if "63_V126_VISIBLE_ROW_OBSERVER.json" in z.namelist():
            try:
                capture=json.loads(z.read("63_V126_VISIBLE_ROW_OBSERVER.json"))
                cap=capture.get("captured",{})
                out["ui_capture"]={
                    "status":cap.get("status"),
                    "rendered_rows":cap.get("rows"),
                    "row_to_weapon_join_verified":cap.get("row_to_weapon_join_verified") is True,
                    "native_message_pointer_verified":cap.get("native_message_pointer_verified") is True,
                    "attack_sequence_verified":cap.get("attack_sequence_verified") is True}
            except (ValueError,TypeError):
                out["ui_capture"]={"status":"UNREADABLE_HOLD"}
    return out

def main(argv=None)->int:
    parser=argparse.ArgumentParser(description="Read-only pinned Hit() conditional AddMessage bypass proof")
    parser.add_argument("user_zip",type=Path)
    parser.add_argument("--out",type=Path)
    a=parser.parse_args(argv)
    report=evaluate_user_zip(a.user_zip)
    data=json.dumps(report,ensure_ascii=False,indent=2)
    if a.out:
        if a.out.resolve()==a.user_zip.resolve():parser.error("OUTPUT_MUST_NOT_OVERWRITE_SOURCE")
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(data+"\n",encoding="utf8")
    print(data)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
