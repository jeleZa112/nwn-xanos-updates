"""One-pass SOURCE verification for the first installable candidate of same-Hit observer.

Never attaches to a process, writes game files, or authorizes native JIT. This
intentionally tests the *corrected* 0x39DA68 site, and prohibits the original
RIP-relative LEA at 0x39DA75. Use pinned user-private V120 archive for evidence.
"""
import hashlib, zipfile, json, os, re
from pathlib import Path

PINNED_ARCHIVE='08a9d5da367404b33bc982871627e8c3e1179c7a8ec8808bab0a75bea5755015'
FUNC='19_V68_COMBAT_CODE/functions/0039DA50_0039E9DC.bin'
PINNED_FUNC='19c1d11b7ac41d261d22b19506b3570427e356544e48f2e2c622c1efdb74cc79'
BASE=0x39DA50
SITES={
'corrected_early_capture':(0x39DA68,'4881ec80000000'),
'old_rip_relative_forbidden':(0x39DA75,'488d15a1c92400'),
'existing_upstream_eeex_owned_call':(0x39DA86,'e8e5f20500'),
'same_frame_addmessage':(0x39E84B,'e81064e6ff'),
'same_frame_exit':(0x39E996,'e865e40500'),
'same_frame_return':(0x39E9B9,'c3'),
}
HOOK_KEYS=('corrected_early_capture','same_frame_addmessage','same_frame_exit')

def sha(b): return hashlib.sha256(b).hexdigest()
def verify(archive,source):
    archive=Path(archive);source=Path(source)
    data=archive.read_bytes();lua=source.read_bytes()
    checks={}
    def ck(name,b):checks[name]=bool(b)
    ck('exact_v120_archive',sha(data)==PINNED_ARCHIVE)
    with zipfile.ZipFile(archive) as z:
        ck('zip_crc',z.testzip() is None)
        ck('zip_no_duplicate_names',len(z.namelist())==len(set(z.namelist())))
        b=z.read(FUNC)
    ck('exact_hit_fragment',sha(b)==PINNED_FUNC)
    ck('exact_hit_length',len(b)==0x39E9DC-BASE)
    for k,(addr,hexb) in SITES.items():
        ck('byte_'+k,b[addr-BASE:addr-BASE+len(bytes.fromhex(hexb))]==bytes.fromhex(hexb))
    spans={k:(SITES[k][0],SITES[k][0]+len(bytes.fromhex(SITES[k][1]))) for k in HOOK_KEYS}
    for i,k in enumerate(HOOK_KEYS):
        for l in HOOK_KEYS[i+1:]:
            a,b2=spans[k],spans[l]
            ck('hook_disjoint_'+k+'_'+l,a[1]<=b2[0] or b2[1]<=a[0])
    ck('does_not_touch_reserved_firstcall',all(not (a<=0x39DA86<c) for a,c in spans.values()))
    ck('old_hook_not_selected',0x39DA75 not in [SITES[k][0] for k in HOOK_KEYS])
    ck('relocatable_sub_rsp',b[0x39DA68-BASE:0x39DA6F-BASE]==bytes.fromhex('4881ec80000000'))
    ck('native_frame_established',b[0x39DA65-BASE:0x39DA68-BASE]==bytes.fromhex('488bec'))
    ck('capture_before_context_clobber',0x39DA68<0x39DA6F<0x39DA72<0x39DA7C<0x39DA83)
    ck('message_before_exit',0x39E84B+5<0x39E996<0x39E9B9)
    ck('hook_pair_firstcall_distances',0x39DA86-0x39DA68==0x1E and 0x39E84B-0x39DA86==0xDC5 and 0x39E996-0x39DA86==0xF10)
    ck('passive_pilot_source_only',b'authorized_install = false' in lua and b'runtime_abi_verified = false' in lua)
    ck('atomic_install_guard',b'atomic_three_hook_install_verified = false' in lua)
    ck('startup_refuses_hook',b"return false,'RUNTIME_HOOK_IMPLEMENTATION_NOT_VERIFIED'" in lua)
    ck('no_runtime_hook_calls',b'EEex_HookBeforeCallWithLabels(' not in lua and b'EEex_HookBeforeRestoreWithLabels(' not in lua and b'EEex_JITAt(' not in lua)
    ck('never_modify_message',b'function BG_EET_RU_HIT_PILOT_Message' in lua and b'SAME_FRAME_MESSAGE_UNTYPED' in lua)
    ck('never_use_old_site_for_capture',b'capture=first-0x1E' in lua and b'forbidden=first-0x11' in lua)
    ck('never_persist_native_item',b'item.cResRef:get()' in lua and b'P.active[frame]={weapon=ref:upper()' in lua)
    ck('prevent_duplicate_frame',b'if P.active[frame] or P.blocked[frame]' in lua)
    ck('clear_after_exit',b'P.active[frame]=nil;P.blocked[frame]=nil' in lua)
    ck('bounded_frames',b'max_active = 128' in lua)
    ck('bounded_telemetry',b'max_samples = 64' in lua)
    ck('not_an_installer',b'not an installable release' in lua)
    return {'schema':'BG_EET_RU_CORRECTED_SAME_HIT_SOURCE_V1','status':'SOURCE_PASS_RUNTIME_HOLD' if all(checks.values()) else 'SOURCE_INVALID_HOLD','passed':sum(checks.values()),'total':len(checks),'checks':checks,'game_files_written':0,'native_hooks_installed':False,'gameplay_tested':False,'remaining_blockers':['Lua binding correctness in running EEex','Win64 ABI/XMM preservation','atomic multi-site native JIT installation and rollback','actual live-site bytes and patch conflicts','unwind/exception recovery','same message class and UI row proof','separate typed game change authorization']}