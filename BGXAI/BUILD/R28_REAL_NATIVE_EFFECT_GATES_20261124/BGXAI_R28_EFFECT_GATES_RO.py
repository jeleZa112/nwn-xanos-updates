#!/usr/bin/env python3
"""Fail-closed raw ITM effect/provenance classification for the user's R28 report.

Source-only analysis. Never an engine ability probe, weapon selector, installer or a
claim that raw item effects are active. Outputs no game commands of any kind.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys

SCHEMA = 'BGXAI_R28_EFFECT_GATES_RO_V1'
MAX_INPUT = 1_000_000
REQUIRED_ITEMS = {'AROW01', 'BOW05', 'STAF01', 'SW1H04'}

class Hold(ValueError):
    pass

def evaluate(data: dict) -> dict:
    if not isinstance(data, dict) or data.get('schema') != 'BGXAI_R28_NATIVE_FROM_R27_RO_V1' or data.get('status') != 'R28_NATIVE_ITEMS_RAW_READ_AWAITING_REVIEW':
        raise Hold('R28_REPORT_UNKNOWN')
    live, audit = data.get('liveR27Evidence'), data.get('nativeAudit')
    if not isinstance(live,dict) or not isinstance(audit,dict): raise Hold('R27_OR_NATIVE_AUDIT_MISSING')
    if data.get('captureSha256') != live.get('sourceSha256') or len(str(data.get('captureSha256',''))) != 64: raise Hold('SOURCE_PROVENANCE_BROKEN')
    if not (live.get('r27SessionMarkers') == 1 and type(live.get('r27ConfirmedCallbacks')) is int and 1 <= live['r27ConfirmedCallbacks'] <= 64): raise Hold('R27_SESSION_UNCONFIRMED')
    samples=live.get('samplesSelectedOnly')
    if not isinstance(samples,list) or len(samples) != live['r27ConfirmedCallbacks']:raise Hold('R27_SAMPLE_COUNT_MISMATCH')
    if [x.get('sequence') for x in samples if isinstance(x,dict)] != list(range(1,len(samples)+1)):
        raise Hold('R27_EVENT_SEQUENCE_BROKEN')
    if audit.get('sourceKind') != 'CURRENT_GAME' or audit.get('status') != 'ITM_NATIVE_ALL_ITEMS_RAW_READ' or audit.get('missingItemsOrLinkedSpells') != []:
        raise Hold('NATIVE_NOT_CURRENT_OR_INCOMPLETE')
    if any(data.get(k) is not False for k in ('gameModified','gameplayActionOriginVerified','manualAndEPSQueueVerified','effectiveAlternateAPRVerified','launcherAmmoPairVerified','weaponSwitchAuthorized','dispatchAuthorized')) or data.get('ordersSent') != 0:
        raise Hold('R28_NONPASSIVE_OR_UNKNOWN_FLAG')
    if any(live.get(k) is not False for k in ('gameModified','effectiveAlternateAPRVerified','manualAndEPSQueueVerified','weaponSwitchAuthorized','dispatchAuthorized')):raise Hold('R27_NONPASSIVE_OR_UNKNOWN_FLAG')
    items=audit.get('items')
    if not isinstance(items,dict) or set(items) != REQUIRED_ITEMS:raise Hold('UNEXPECTED_LOADOUT_RESREFS')
    if set(live.get('observedRawItemResrefs',[])) != REQUIRED_ITEMS:raise Hold('R27_R28_ITEM_SET_MISMATCH')
    links=audit.get('linkedSpells')
    if not isinstance(links,dict):raise Hold('LINKED_SPELLS_MISSING')
    rows=[]
    for ref in sorted(items):
        v=items[ref]
        if not isinstance(v,dict) or v.get('resource') != ref:raise Hold('RESOURCE_MISMATCH')
        prov,it=v.get('provenance'),v.get('item')
        if not isinstance(prov,dict) or prov.get('origin') not in ('CURRENT_GAME_OVERRIDE','CURRENT_GAME_BIFF') or not isinstance(it,dict):raise Hold('ITEM_PROVENANCE_UNKNOWN')
        if it.get('rawOnly') is not True or it.get('characterCanEquipVerified') is not False or it.get('engineEffectsAppliedVerified') is not False:raise Hold('ITEM_LIVE_FLAGS_UNKNOWN')
        abilities=it.get('abilities'); equip=it.get('equippedEffects')
        if not isinstance(abilities,list) or not 1<=len(abilities)<=8 or not isinstance(equip,list):raise Hold('ITEM_ABILITIES_UNKNOWN')
        if any(not isinstance(e,dict) or type(e.get('opcodeRaw')) is not int for e in equip):raise Hold('ITEM_EFFECTS_MALFORMED')
        if any(not isinstance(a,dict) or not isinstance(a.get('effects'),list) for a in abilities):raise Hold('ABILITY_EFFECTS_MALFORMED')
        flat=[e for e in equip if e['opcodeRaw']==1 and e.get('parameter2Raw')==1]
        apr_effects=[{'modifierRaw':e.get('parameter1Raw'),'typeRaw':e.get('parameter2Raw'),'timingRaw':e.get('timingRaw')}
                    for e in equip if e['opcodeRaw']==1]
        cast_refs={e.get('resourceRaw') for a in abilities for e in a['effects'] if isinstance(e,dict) and e.get('opcodeRaw')==146 and isinstance(e.get('resourceRaw'),str)}
        mutations=[]
        for cast in cast_refs:
            spell=links.get(cast)
            if not isinstance(spell,dict) or spell.get('effectCompletionVerified') is not False:raise Hold('LINKED_EFFECT_COMPLETION_NOT_EXPLICITLY_UNKNOWN')
            effs=[e for a in spell.get('spell',{}).get('abilities',[]) for e in a.get('effects',[]) if isinstance(e,dict)]
            mutations.extend(sorted({e['opcodeRaw'] for e in effs if e.get('opcodeRaw') in (112,122,123)}))
        ability=abilities[0]
        rows.append({'resource':ref,'origin':prov['origin'],
                     'abilityCount':len(abilities), 'baseDamageMeanBeforeEffects':ability.get('baseDamageMeanBeforeEffects'),
                     'rangeRaw':ability.get('rangeRaw'),'speedRaw':ability.get('speedRaw'),
                     'launcherRequiredRaw':ability.get('launcherRequiredRaw'),
                     'aprEffectOverridesRaw':apr_effects,'flatAprEffectObserved':bool(flat),
                     'linkedSpellRefsRaw':sorted(cast_refs), 'linkedItemMutationOpcodesRaw':sorted(set(mutations)),
                     'usabilityRestrictionOpcode319Observed':any(e['opcodeRaw']==319 for e in equip),
                     'allActiveBuffsVerified':False,'effectiveDamageVerified':False,
                     'effectiveAlternateAprVerified':False,'safeToAutoSwitch':False})
    if audit.get('aprtables',{}).get('WSPATCK',{}).get('table',{}).get('semanticsAndCharacterRowVerified') is not False:
        raise Hold('WSPATCK_ROW_SEMANTICS_UNKNOWN')
    if audit.get('aprtables',{}).get('CLSWPBON',{}).get('table',{}).get('semanticsAndCharacterRowVerified') is not False:
        raise Hold('CLASS_ROW_SEMANTICS_UNKNOWN')
    return {'schema':SCHEMA,'status':'R28_REAL_STATIC_EVIDENCE_CLASSIFIED_NO_DISPATCH',
            'r27Callbacks':len(samples),'actualInstalledItemCount':len(rows),
            'observations':rows,
            'criticalFindings':['BOW05_EQUIPPED_OPCODE_1_TYPE_1_FLAT_APR',
                                'SW1H04_ABILITY_OPCODE_146_LINKS_SPELL_WITH_112_122',
                                'OPCODE_319_ITEM_USABILITY_CONDITION_NOT_PROVEN'],
            'remainingBlocks':['ALTERNATE_EFFECTIVE_APR','ACTIVE_EFFECTS_AND_TARGET','AMMO_LAUNCHER_VERIFIED','EPS_ORIGIN_AND_ACTION_QUEUE','SAFE_NONINTERRUPT_BOUNDARY'],
            'nativeItemValuesMayBeUsedAs':'STATIC_RAW_INPUT_ONLY',
            'mayCompareEffectiveDps':False,'mayScheduleWeaponSwitch':False,
            'installedGameModified':False,'ordersSent':0,'dispatchAuthorized':False}

def read(path:Path):
    if path.is_symlink() or not path.is_file() or not 0<path.stat().st_size<=MAX_INPUT:raise Hold('INPUT_UNSAFE')
    raw=path.read_bytes()
    return evaluate(json.loads(raw)),hashlib.sha256(raw).hexdigest()

if __name__=='__main__':
    result,digest=read(Path(sys.argv[1]))
    result['sourceReportSha256']=digest
    print(json.dumps(result,indent=2,ensure_ascii=False))
