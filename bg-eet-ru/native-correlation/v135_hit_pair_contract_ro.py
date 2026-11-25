"""BG_EET_RU V135 — pinned CGameSprite::Hit entry/exit pair contract, SOURCE ONLY.

This verifies original machine-code anchors and a candidate return-value site.
It does NOT hook, start, modify, inject, or inspect a running game process.
It cannot determine whether returned 0/1 maps to a displayed miss/hit.
The separately supplied Lua bridge is a bounded pure-Lua model; not deployed.
"""
from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path

SCHEMA = 'BG_EET_RU_V135_PINNED_HIT_ENTRY_EXIT_RAW_RETURN_CONTRACT_RO'
ZIP_SHA = 'b1050448afe45b82193f1fc38f1db10f044a8615f200113ddb80009564172e35'
HIT_NAME = '19_V68_COMBAT_CODE/functions/0039DA50_0039E9DC.bin'
HIT_SHA = '19c1d11b7ac41d261d22b19506b3570427e356544e48f2e2c622c1efdb74cc79'
BASE, END = 0x39DA50, 0x39E9DC
ENTRY = 0x39DA6F
EXIT_PRE_EPILOG = 0x39E99B
OUTPUT_RAW = 0x39E9A3
EXPECTED = {
  'after_prolog_rcx_rdx_preserved': (0x39DA6F, '4c8bf2488bd9'),
  'source_ability_from_r9d': (0x39DA7C, '418bf1'),
  'source_item_from_r8': (0x39DA83, '4d8bf8'),
  'eeex_firstcall_prepatch_original': (0x39DA86, 'e8e5f20500'),
  'native_result_compare': (0x39E533, '66443b7d48'),
  'native_result_setge': (0x39E546, '0f9dc0'),
  'native_result_store': (0x39E549, '894540'),
  'forced_one_const': (0x39E59A, 'b801000000'),
  'forced_one_store': (0x39E5A2, '894540'),
  'r14_lowbyte_set_one_other_path': (0x39E2FA, '41b601'),
  'r14d_from_stack_result': (0x39E66F, '448b7540'),
  'r14d_from_r12d_other_path': (0x39E717, '458bf4'),
  'possible_message_bypass': (0x39E7B3, '0f859c000000'),
  'conditional_message_call': (0x39E84B, 'e81064e6ff'),
  'pre_epilog_exit_anchor_abi_unverified': (EXIT_PRE_EPILOG, '488b9c24d8000000'),
  'raw_return_from_r14b': (OUTPUT_RAW, '410fb6c6'),
  'stack_restore_after_return_transfer': (0x39E9A7, '4881c480000000'),
  'restore_r15': (0x39E9AE, '415f'),
  'restore_r14': (0x39E9B0, '415e'),
  'restore_r12': (0x39E9B4, '415c'),
  'end_ret': (0x39E9B9, 'c3'),
}

class Hold(ValueError):
    pass


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def exact_original_hit(code: bytes) -> dict:
    """Reject even tiny byte deviations; no executable patch or unpinned fallback."""
    if type(code) is not bytes or len(code) != END - BASE:
        raise Hold('HIT_ORIGINAL_FUNCTION_LENGTH_HOLD')
    if sha256(code) != HIT_SHA:
        raise Hold('HIT_ORIGINAL_FUNCTION_SHA_HOLD')
    for name, (rva, hexbytes) in EXPECTED.items():
        pattern = bytes.fromhex(hexbytes)
        if code[rva - BASE:rva - BASE + len(pattern)] != pattern:
            raise Hold('HIT_PINNED_INSTRUCTION_DRIFT_' + name)
    if ENTRY != BASE + 0x1f:
        raise Hold('NOT_AFTER_31_BYTE_UNWIND_PROLOGUE')
    if EXIT_PRE_EPILOG + 8 != OUTPUT_RAW:
        raise Hold('EXIT_ANCHOR_NOT_FULL_NON_RIP_RELATIVE_INSTRUCTION')
    if OUTPUT_RAW + 4 != 0x39E9A7:
        raise Hold('RAW_RESULT_NOT_BEFORE_STACK_EPILOG')
    if code[0x39E7B3 - BASE + 2:0x39E7B3 - BASE + 6] != bytes.fromhex('9c000000'):
        raise Hold('V129_BYPASS_DRIFT')
    # The 0x39E7B3 branch target is 0x39E855 (skips the message CALL at 0x39E84B).
    if 0x39E7B3 + 6 + int.from_bytes(bytes.fromhex('9c000000'), 'little', signed=True) != 0x39E855:
        raise Hold('V129_BRANCH_TARGET_HOLD')
    return {
      'status': 'PINNED_ENTRY_AND_PRE_EPILOG_EXIT_SITES_STATIC_PASS',
      'original_hit_sha256': HIT_SHA,
      'hit_original_length': len(code),
      'instruction_anchors_checked': len(EXPECTED),
      'entry_rva': f'0x{ENTRY:x}',
      'entry_expected_original_bytes': EXPECTED['after_prolog_rcx_rdx_preserved'][1],
      'exit_rva': f'0x{EXIT_PRE_EPILOG:x}',
      'exit_expected_original_bytes': EXPECTED['pre_epilog_exit_anchor_abi_unverified'][1],
      'raw_return_rva': f'0x{OUTPUT_RAW:x}',
      'raw_return_instruction': 'movzx eax,r14b',
      'next_instruction': 'add rsp,0x80',
      'firstcall_in_original_binary_only': 'call 0x3FCD70',
      'firstcall_live_owner_verified': False,
      'input_register_hypothesis': {'rcx': 'attacker_ptr', 'rdx': 'target_ptr',
                                     'r8': 'item_ptr', 'r9d': 'ability_index',
                                     'rbp': 'frame_pointer_after_prologue'},
      'exit_register_hypothesis': {'r14b': 'raw_return_byte', 'rbp': 'same_frame_pointer'},
      'return_0_is_miss_proven': False,
      'return_1_is_hit_proven': False,
      'return_byte_always_maps_to_visible_d20_result': False,
      'native_hook_safe_or_installed': False,
      'runtime_callback_abi_verified': False,
      'xmm_and_gpr_preservation_verified': False,
      'jit_unwind_registered_verified': False,
      'hook_owner_and_rollback_verified': False,
    }


def audit_zip(path: Path) -> dict:
    """Consumes exact user evidence; no game read; emits no false gameplay PASS."""
    if path.is_symlink() or not path.is_file() or sha256(path.read_bytes()) != ZIP_SHA:
        raise Hold('EXACT_USER_V133_ARCHIVE_PIN_HOLD')
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        if len(names) != len(set(names)) or z.testzip() is not None:
            raise Hold('ZIP_DUPLICATES_OR_CRC_HOLD')
        try:
            original = z.read(HIT_NAME)
            r133 = json.loads(z.read('66_V133_LIVE_HIT_INVENTORY.json'))
            r132 = json.loads(z.read('65_V132_EEEX_ABI.json'))
        except (KeyError, ValueError) as e:
            raise Hold('SOURCE_REPORTS_MISSING_OR_BAD_' + type(e).__name__) from e
    if (r133.get('status') != 'LIVE_SITES_MATCH_OWNER_UNVERIFIED_RUNTIME_HOLD'
        or r133.get('game_files_written') != 0
        or r133.get('post_prologue_rva') != '0x39DA6F'
        or r133.get('firstcall_owner_verified') is not False):
        raise Hold('V133_EVIDENCE_DRIFT')
    if (r132.get('status') != 'REAL_XDATA_AND_INSTALLED_EEEX_STATIC_CONTRACT_PASS_RUNTIME_HOLD'
        or r132.get('unwind', {}).get('exact_6_byte_post_prolog_candidate') != '0x39da6f'
        or r132.get('unwind', {}).get('raw_rbx_offset_exact_216_verified') is not True):
        raise Hold('V132_UNWIND_EVIDENCE_DRIFT')
    contract = exact_original_hit(original)
    return {
      'schema': SCHEMA,
      'status': 'V135_SOURCE_PAIR_MODEL_READY_NATIVE_LIVE_HOLD',
      'v133_zip_sha256': ZIP_SHA,
      'native_contract': contract,
      'runtime_pairing_installed': False,
      'same_swing_item_resref_verified': False,
      'same_swing_hit_miss_verified': False,
      'native_return_semantics_proven': False,
      'row_join_verified': False,
      'game_files_written': 0,
      'native_hooks_installed': False,
      'gameplay_verified': False,
      'engineering_next': 'VERIFY_ABI_AND_OWNER_BEFORE_GUARDED_SYNCHRONOUS_PAIR_HOOK',
      'must_preserve': ['V126_VISIBLE_ROW_OBSERVER', 'V133_LIVE_MEMORY_GATE',
                        'BGXAI', 'BG_VOICE_RU'],
    }


def main(argv: list[str] | None = None) -> int:
    import argparse
    p = argparse.ArgumentParser(description='V135 exact user-source Hit entry/exit pair, read-only')
    p.add_argument('user_zip', type=Path)
    p.add_argument('--output', type=Path)
    a = p.parse_args(argv)
    out = audit_zip(a.user_zip)
    if a.output:
        if a.output.resolve() == a.user_zip.resolve():
            raise Hold('CANNOT_OVERWRITE_USER_ZIP')
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(out['status'])
    return 0

if __name__ == '__main__':
    sys.exit(main())
