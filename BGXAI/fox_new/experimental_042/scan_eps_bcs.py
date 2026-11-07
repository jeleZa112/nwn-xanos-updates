#!/usr/bin/env python3
"""Read-only audit of compiled EPS BDDEFAI.BCS and WeiDU.log.

Reads selected files and writes ONLY stdout; deliberately no patching capability.
Does NOT interpret compiled actions as proof that a branch was executed in-game.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re

BLOCK = re.compile(r'(?s)CR\nCO\n(.*?)\nRS\n(.*?)\nRS\nCR(?=\n(?:CR|SC))')
TRIGGER = re.compile(r'\nTR\n(-?\d+)\s')
ACTION = re.compile(r'(?:^|\n)(?:\d+)?AC\n(-?\d+)OB\n')
TR_ACTION_LIST_EMPTY = 0x402B
ACTION_NAMES = {3:'Attack',87:'ProtectObject',105:'AttackOneRound',134:'AttackReevaluate',31:'Spell',191:'SpellNoDec'}


def inspect(raw: bytes) -> dict:
    if len(raw)>8_000_000 or not raw.startswith(b'SC\n'):
        raise ValueError('Expected compiled BCS text (SC header, max 8 MB); refusing unrelated file')
    script = raw.decode('latin-1')
    matches = list(BLOCK.finditer(script))
    if not matches:
        raise ValueError('No complete BCS condition/action blocks; cannot audit')
    records=[]
    stats=collections.Counter()
    for i,m in enumerate(matches,1):
        conditions,body = m.group(1),m.group(2)
        triggers = [int(x) for x in TRIGGER.findall('\n'+conditions)]
        actions = [int(x) for x in ACTION.findall('\n'+body)]
        all_codes=triggers+actions
        for id in actions:stats[id]+=1
        names=[x for x in ('BDAI_ATTACK_MODE','BGX38_GUARD','BGX39_TEAM_CD','BGX41_ICON_INIT','BGX42') if x in conditions or x in body]
        records.append({'block':i,'action_ids':actions,'action_names':[ACTION_NAMES.get(j,str(j)) for j in actions],
                        'triggers_action_list_empty':TR_ACTION_LIST_EMPTY in triggers,
                        'has_attack_mode': 'BDAI_ATTACK_MODE' in conditions,
                        'has_guard_flag':'BGX38_GUARD' in conditions,
                        'tags':names})
    attack_mode=[r for r in records if r['has_attack_mode']]
    guard=[r for r in records if r['has_guard_flag']]
    return {
        'sha256':hashlib.sha256(raw).hexdigest(), 'size':len(raw),
        'complete_blocks':len(records),
        'attack_mode_blocks':len(attack_mode),
        'guard_flag_blocks':len(guard),
        'all_attack_mode_gated_by_idle':all(x['triggers_action_list_empty'] for x in attack_mode) if attack_mode else None,
        'actions':{ACTION_NAMES.get(j,str(j)):c for j,c in sorted(stats.items())},
        'attack_mode_samples':attack_mode[:12],
        'guard_samples':guard[:12],
        'contains_038_guard_flag':'BGX38_GUARD' in script,
        'contains_attack_mode':'BDAI_ATTACK_MODE' in script,
        'interpretation':'BCS branch inventory only. Does not prove action priority or runtime behavior.'
    }


def weidu_state(log:bytes)->dict:
    lines=log.decode('utf-8-sig',errors='replace').splitlines()
    active=[ln.strip() for ln in lines if ln.strip().startswith('~')]
    mods={str(n):any(re.search(r'BGX'+str(n)+r'[^~]*\.TP2~',ln,re.I) for ln in active) for n in [39,40,41,42]}
    return {'bgxai_installed':mods,'last_is_041': bool(active and re.search(r'BGX41[^~]*\.TP2~',active[-1],re.I)),
            'total_active_mod_components':len(active)}


def main():
    a=argparse.ArgumentParser(description='BGXAI 042 BCS priority diagnostics (READ ONLY)')
    a.add_argument('--bcs',type=Path,required=True)
    a.add_argument('--weidu-log',type=Path)
    a.add_argument('--json',action='store_true')
    opts=a.parse_args()
    result=inspect(opts.bcs.read_bytes())
    if opts.weidu_log:result['weidu']=weidu_state(opts.weidu_log.read_bytes())
    if opts.json:print(json.dumps(result,ensure_ascii=False,indent=2));return
    print('BGXAI 042 — ИНВЕНТАРИЗАЦИЯ СЦЕНАРИЯ EPS (ТОЛЬКО ЧТЕНИЕ)')
    print('SHA256:',result['sha256'],'байт:',result['size'])
    print('Полных блоков:',result['complete_blocks'])
    print('Блоков с режимом автоатаки BDAI_ATTACK_MODE:',result['attack_mode_blocks'])
    print('Блоков с охраной BGX38_GUARD:',result['guard_flag_blocks'])
    print('Все блоки автоатаки требуют свободную очередь?:',result['all_attack_mode_gated_by_idle'])
    print('Команды:',result['actions'])
    for v in result['attack_mode_samples'][:6]:
        print('  EPS блок',v['block'],'команды',','.join(v['action_names']) or 'нет','проверяет ActionListEmpty:',v['triggers_action_list_empty'])
    if opts.weidu_log:print('WeiDU:',result['weidu'])
    print('НЕТ ИЗМЕНЕНИЙ ИГРЫ. Для исправления нужны правила реального BCS, не догадки.')

if __name__=='__main__':main()
