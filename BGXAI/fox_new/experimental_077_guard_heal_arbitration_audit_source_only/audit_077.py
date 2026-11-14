#!/usr/bin/env python3
"""BGXAI 077: strict read-only source audit of BGXAI 061 / installed 066S Lua+BAF.

Does NOT read from or write to a running EET; never imports game modules.
Original user source inputs are *not* redistributed in release ZIP.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

INPUTS = {
    'BGX61_RECEIVER.baf': '94b4beca0d9e470ed0cad566a19038566f626c19d53454d590fd409d294fcd1e',
    'BGX66_CASTER_RECEIVER_SOURCE_ONLY.baf': 'c678a70a08dbcff7584e0f2703aa8bed5ae5945856287666016ee47c9d6f69ae',
    'BGX66_CASTER_SUPPORT.lua': 'b365ac770c508e292b87c280c58f922c20306a0b9d3ca68c99b0cd1223872020',
    'M_BX43_066S_CASTER_CANDIDATE.lua': '50640902ec4c25a2c85e5088d7231678b54445a847b41743c476974236d1d70f',
}

class AuditError(ValueError):
    pass


def read_exact(folder: Path) -> dict[str, str]:
    result = {}
    for name, sha in INPUTS.items():
        raw = (folder / name).read_bytes()  # source READ only
        if hashlib.sha256(raw).hexdigest() != sha:
            raise AuditError('SOURCE_SHA_MISMATCH:' + name)
        result[name] = raw.decode('utf-8')
    return result


def baf_blocks(src: str) -> list[str]:
    blocks = [m.group(0) for m in re.finditer(r'(?ms)^IF\s*\n.*?^END\s*$', src)]
    if not blocks or len(blocks) != len(re.findall(r'(?m)^IF\s*$', src)):
        raise AuditError('BAF_BLOCK_PARSE_INCOMPLETE')
    return blocks


def lua_class_ids(source: str, var: str) -> list[int]:
    m = re.search(r'local\s+' + re.escape(var) + r'\s*=\s*\{([^}]*)\}', source)
    if not m:
        raise AuditError('MISSING_CLASS_TABLE:' + var)
    ids = [int(x) for x in re.findall(r'\[(\d+)\]\s*=\s*(?:true|\x27[^\x27]*\x27)', m.group(1))]
    if not ids or len(ids) != len(set(ids)):
        raise AuditError('MALFORMED_CLASS_TABLE:' + var)
    return sorted(ids)


def check_obligatory(condition: bool, reason: str) -> None:
    if not condition:
        raise AuditError(reason)


def analyze(sources: dict[str, str]) -> dict:
    a061 = sources['BGX61_RECEIVER.baf']
    a066 = sources['BGX66_CASTER_RECEIVER_SOURCE_ONLY.baf']
    lua066 = sources['M_BX43_066S_CASTER_CANDIDATE.lua']
    luahealer = sources['BGX66_CASTER_SUPPORT.lua']

    guard = baf_blocks(a061)
    cast = baf_blocks(a066)
    check_obligatory(len(guard) == 20, 'EXPECTED_20_GUARD_BLOCKS')
    check_obligatory(len(cast) == 11, 'EXPECTED_11_CASTER_BLOCKS')
    guard_act = guard[2:]
    cast_act = cast[4:]
    guard_actions = {
        'attack_reevaluate': sum('AttackReevaluate(' in x for x in guard_act),
        'move_to_ally': sum('MoveToObject(' in x for x in guard_act),
        'protect_ally': sum('ProtectObject(' in x for x in guard_act),
    }
    check_obligatory(guard_actions == {'attack_reevaluate': 6, 'move_to_ally': 6, 'protect_ally': 6}, 'GUARD_ACTION_LAYOUT_DRIFT')
    check_obligatory(all('ActionListEmpty()' in x for x in guard_act), 'GUARD_QUEUE_GATE_MISSING')
    healing = cast[4:10]
    ward = cast[10]
    check_obligatory(len(healing) == 6 and len(cast_act) == 7, 'CAST_ACTION_COUNT_DRIFT')
    check_obligatory(all('ActionListEmpty()' in x for x in cast_act), 'CAST_QUEUE_GATE_MISSING')
    check_obligatory(all('HaveSpell(CLERIC_CURE_LIGHT_WOUNDS)' in x for x in healing), 'HEAL_SPELL_GATE_DRIFT')
    check_obligatory(all('Range(Player' in x and ',10)' in x for x in healing), 'HEAL_RANGE_GATE_DRIFT')
    check_obligatory(all('Spell(Player' in x for x in healing), 'HEAL_ACTION_DRIFT')
    check_obligatory('HaveSpell(WIZARD_SHIELD)' in ward and 'Spell(Myself,WIZARD_SHIELD)' in ward, 'WARD_GATE_DRIFT')

    frontline = lua_class_ids(lua066, 'FRONTLINE')
    healer = lua_class_ids(luahealer, 'HEALER')
    arcane = lua_class_ids(luahealer, 'ARCANE')
    check_obligatory(frontline == [2,6,12], 'FRONTLINE_DRIFT')
    check_obligatory(healer == [3,8,11,14,15,16,17,18], 'HEALER_DRIFT')
    check_obligatory(not (set(frontline) & set(healer)), 'FRONTLINE_HEALER_OVERLAP')
    check_obligatory('BGX52Bridge.prepare=T.prepare' in lua066, 'FRONTLINE_WRAP_MISSING')
    callback = re.search(r'local basePrepare=BGX52Bridge\.prepare\s*\nBGX52Bridge\.prepare=function\(hit\)(.*?)\nend', lua066, re.S)
    check_obligatory(callback is not None, 'SUPPORT_WRAP_MISSING')
    body=callback.group(1)
    check_obligatory('basePrepare(hit)' in body and 'S.onHit(hit)' in body and body.index('basePrepare(hit)') < body.index('S.onHit(hit)'), 'WRAPPER_ORDER_DRIFT')
    check_obligatory('BGX66_S_HEAL_SLOT' in luahealer, 'HEAL_SELECTOR_MISSING')
    select = re.search(r'if HEALER\[cls\].*?\n\s*end',luahealer,re.S)
    check_obligatory(select is not None, 'HEAL_CLASS_SELECTOR_MISSING')
    select_src=select.group(0)
    check_obligatory('dist=(ox-vx)^2+(oy-vy)^2' in select_src, 'HEAL_NEAREST_SELECTOR_CHANGED')
    # No capability/range check in Lua selector: BCS verifies later.
    checks_late = 'HaveSpell(' not in select_src and 'Range(' not in select_src
    check_obligatory(checks_late, 'HEAL_SELECTOR_NOW_CHECKS_FEASIBILITY_REAUDIT')
    check_obligatory('if healer and ward and healer.id==ward.id then ward=nil end' in luahealer, 'ONE_ACTOR_GUARD_MISSING')
    check_obligatory('local HEALER' in luahealer and '[21]' not in re.search(r'local HEALER=\{([^}]+)\}',luahealer).group(1), 'SHAMAN_GAP_CHANGED')
    check_obligatory('if guardOK and guardRecord then' in lua066 and 'pcall(BGX52Bridge.prepare, guardRecord)' in lua066,
                     'ON_HIT_EVENT_ENTRY_DRIFT')
    return {
        'status': 'SOURCE_ONLY_BGXAI_077_AUDIT_CONFIRMED',
        'source_provenance': 'SHA-locked saved EET BGXAI 061/066S BAF+Lua sources; no game runtime tested',
        'baf': {'061_blocks':len(guard),'061_cleanup_blocks':2,'061_action_blocks':len(guard_act),
                '061_action_list_empty':sum('ActionListEmpty()' in x for x in guard_act),
                **guard_actions, '066s_blocks':len(cast),'066s_cleanup_blocks':4,
                '066s_cast_blocks':len(cast_act),'066s_action_list_empty':sum('ActionListEmpty()' in x for x in cast_act),
                '066s_heal_blocks':len(healing),'066s_ward_blocks':1,
                'healing_bcs_checks_have_spell_and_range_10':True},
        'roles':{'frontline_ids':frontline,'healer_ids':healer,'arcane_ids':arcane,
                 'frontline_healer_id_overlap':sorted(set(frontline)&set(healer)),
                 'shaman_21_in_healer':21 in healer},
        'event_path':{'weapon_hit_dispatch_first_calls_frontline_then_support':True,
                      'support_callback_runs_even_when_frontline_returns_no_candidate':True,
                      'support_uses_same_confirmed_hit_advisory':True},
        'limitation':{
            'healer_chosen_by_nearest_distance_without_available_spell_or_10ft_eligibility':True,
            'actual_spell_and_10ft_requirements_checked_later_in_BCS':True,
            'no_definitive_same_actor_061_vs_066s_interception_on_066s_base_class_sets':True,
            'no_runtime_queue_priority_or_spell_success_proven':True,
            'not_all_class_multi_dual_kit_combinations_currently_supported':True,
        },
        'candidate_fixes_noninstalled': [
            'Prioritize confirmed usable/reachable healer without overriding EPS action queue; never infer spell availability from CLASS.IDS alone',
            'Handle multi/dual/kit via verified active capabilities rather than widening raw class allowlists blindly',
            'Add request expiry and reason diagnostics to distinguish eligible actor absent vs busy vs out of spell/range',
            'Preserve EPS / manual action / bard song, make any active change opt-in with exact SHA backup and separately approved in-game tests',
        ],
    }


def main() -> int:
    p=argparse.ArgumentParser(description='BGXAI 077 source-only evidence audit, cannot modify game')
    p.add_argument('--source-dir', required=True, type=Path, help='Offline library SOURCE copies (read only)')
    args=p.parse_args()
    try:
        r=analyze(read_exact(args.source_dir))
    except (AuditError, OSError, UnicodeError) as e:
        r={'status':'AUDIT_BLOCKED_NO_CHANGE','reason':str(e)}
    print(json.dumps(r,ensure_ascii=False,indent=2))
    return 0 if r['status']=='SOURCE_ONLY_BGXAI_077_AUDIT_CONFIRMED' else 2

if __name__=='__main__':
    raise SystemExit(main())
