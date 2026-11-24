"""Source-only proof of native Hit() callsite provenance, *not* a game hook.

The private V120 ZIP is read locally and never copied to public CI. Strict
full-ZIP and function SHA pins prevent mixing builds. This verifier distinguishes
callsite provenance from a generic vtable: damage code uses that same vtable.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import zipfile
from pathlib import Path

PIN_ZIP='08a9d5da367404b33bc982871627e8c3e1179c7a8ec8808bab0a75bea5755015'
FUNC='19_V68_COMBAT_CODE/functions/0039DA50_0039E9DC.bin'
DAMAGE='19_V68_COMBAT_CODE/functions/0038FBF0_00390F3C.bin'
PIN_FUNC='19c1d11b7ac41d261d22b19506b3570427e356544e48f2e2c622c1efdb74cc79'
PIN_DAMAGE='59fa0cdbc7206698acd7bd49c7c68807a02d9318a001f13911e04d0d5e49723a'
FUNC_BASE=0x39DA50
DAMAGE_BASE=0x38FBF0
RVA_VTABLE=0x597CD0
RVA_ADD=0x204C60
RVA_FIRST=0x39DA86
# Instruction locations, hex from independently checked private game EXE.
SITES={
  'entry_rbp': (0x39DA65,'488bec'),
  'capture_sub_rsp':(0x39DA68,'4881ec80000000'),
  'firstcall_original':(0x39DA86,'e8e5f20500'),
  'weapon_getter':(0x39DB72,'498bcf'),
  'ability_getter':(0x39DB7A,'8bd6'),
  'message_vtable_rip_lea':(0x39E7D9,'488d0df0941f00'),
  'message_store_vtable':(0x39E7E0,'48890e'),
  'message_arg':(0x39E848,'488bd6'),
  'send_message_call':(0x39E84B,'e81064e6ff'),
  'normal_exit_call':(0x39E996,'e865e40500'),
  'epilogue_add_rsp':(0x39E9A7,'4881c480000000'),
  'epilogue_pop_rbp':(0x39E9B8,'5d'),
  'return':(0x39E9B9,'c3'),
}
DAMAGE_VTABLE_SITE=(0x390DF9,'488d0dd06e2000')


def sha(x:bytes)->str:return hashlib.sha256(x).hexdigest()
def extract(buf:bytes,base:int,rva:int,n:int)->bytes:
    i=rva-base
    if i<0 or i+n>len(buf):return b''
    return buf[i:i+n]
def disp32(buf:bytes)->int:return int.from_bytes(buf,'little',signed=True)
def target_of_rel32(rva:int, raw:bytes)->int:
    if len(raw)!=5 or raw[0]!=0xe8:raise ValueError('NOT_CALL_REL32')
    return rva+5+disp32(raw[1:])
def target_of_lea(rva:int,raw:bytes)->int:
    if len(raw)!=7 or raw[:3]!=bytes.fromhex('488d0d'):raise ValueError('NOT_LEA_RIP')
    return rva+7+disp32(raw[3:])


def verify(archive:Path)->dict:
    out=dict(schema='BG_EET_RU_V4_SAME_HIT_MESSAGE_CALLSITE_PROOF',status='SOURCE_HOLD',
             checks=[], game_files_written=0, runtime_hook_installed=False,
             gameplay_verified=False, message_to_visible_row_verified=False)
    def check(name,ok):
        out['checks'].append(dict(name=name,passed=bool(ok)))
        return bool(ok)
    try:
        raw=archive.read_bytes()
        check('exact_zip_sha',sha(raw)==PIN_ZIP)
        if sha(raw)!=PIN_ZIP:raise ValueError('PIN_ZIP_SHA_HOLD')
        with zipfile.ZipFile(archive) as z:
            check('zip_crc',z.testzip() is None)
            check('zip_unique',len(z.namelist())==len(set(z.namelist())))
            hit=z.read(FUNC)
            dmg=z.read(DAMAGE)
        check('hit_sha',sha(hit)==PIN_FUNC)
        check('damage_sha',sha(dmg)==PIN_DAMAGE)
        if sha(hit)!=PIN_FUNC or sha(dmg)!=PIN_DAMAGE:raise ValueError('PINNED_FUNCTION_CHANGED_HOLD')
        for name,(rva,hexstr) in SITES.items():
            check('exact_instruction_'+name,extract(hit,FUNC_BASE,rva,len(bytes.fromhex(hexstr)))==bytes.fromhex(hexstr))
        rva,hexstr=DAMAGE_VTABLE_SITE
        check('damage_same_class_bytes',extract(dmg,DAMAGE_BASE,rva,7)==bytes.fromhex(hexstr))
        check('hit_vtable_target',target_of_lea(SITES['message_vtable_rip_lea'][0],
              extract(hit,FUNC_BASE,SITES['message_vtable_rip_lea'][0],7))==RVA_VTABLE)
        check('damage_vtable_target',target_of_lea(rva,extract(dmg,DAMAGE_BASE,rva,7))==RVA_VTABLE)
        check('exact_send_target',target_of_rel32(SITES['send_message_call'][0],
              extract(hit,FUNC_BASE,SITES['send_message_call'][0],5))==RVA_ADD)
        check('sequence_order',0x39DA68<0x39DB72<0x39DB7A<0x39E7D9<0x39E7E0<0x39E848<0x39E84B<0x39E996<0x39E9B8)
        # Ensure a native function can't be mislabeled just because it uses the same vtable.
        check('class_not_unique_to_roll',target_of_lea(rva,extract(dmg,DAMAGE_BASE,rva,7))==RVA_VTABLE)
        check('callsite_required_for_identity',0x39E84B!=0x390DF9)
        if not all(x['passed'] for x in out['checks']):raise ValueError('STATIC_INSTRUCTION_MISMATCH')
        out.update(status='PINNED_SOURCE_CALLSITE_PROVED_RUNTIME_HOLD',checks_passed=len(out['checks']),
              hit_rva=hex(FUNC_BASE),send_message_callsite_rva=hex(0x39E84B),
              vtable_rva=hex(RVA_VTABLE),message_class_shared_with_damage=True,
              expected_kind='Hit() CALLSITE + vtable + thread/frame, not vtable alone',
              actual_item_resref_on_miss='NOT_TESTED',native_thread_id_source='NOT_TESTED')
    except Exception as exc:
        out['reason']=str(exc)[:160]
    return out


def main():
    p=argparse.ArgumentParser()
    p.add_argument('v120_zip',type=Path)
    p.add_argument('--output',type=Path)
    a=p.parse_args()
    result=verify(a.v120_zip)
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf8')
    print(result['status'],'checks',sum(x['passed'] for x in result['checks']),'/',len(result['checks']))
    return 0 if result['status']=='PINNED_SOURCE_CALLSITE_PROVED_RUNTIME_HOLD' else 2

if __name__=='__main__':raise SystemExit(main())