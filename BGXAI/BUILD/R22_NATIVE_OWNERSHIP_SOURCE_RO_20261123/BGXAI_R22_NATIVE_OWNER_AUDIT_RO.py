"""BGXAI R22 — pure source-evidence audit. Not an EEex extension or game installer.

Inputs are snippets from inspected upstream sources, not live memory. Never calls
CItem::Demand/GetAbility, Lua listeners, or actions. Passing source checks DOES NOT
authorize using a pointer. The only possible outcome is a correctly reasoned HOLD.
"""
from __future__ import annotations

import re
from collections.abc import Mapping

SCHEMA = 'BGXAI_R22_NATIVE_OWNERSHIP_SOURCE_AUDIT_RO_V1'
UPSTREAM_BLOBS = {
    'resource': '5ecd3c2f9e9bcc6cbd317653fc057a06d956916b',
    'sprite': 'b2d8d930c47785737bd30dad08e9f35a9d859578',
    'utility': 'f10ed5e25ff0c03bc63507d04263f96daae60e7b',
    'cpp': '6646e9a4206459315d641400771e1dd109e4186a',
    'sprite_patch': '8a9fd16e3cb0f1657486089a998d5d47259e73ec',
}
OWNERSHIP_BLOCKERS = (
    'NATIVE_CITEM_DEMAND_RELEASE_OWNERSHIP_NOT_PROVEN',
    'LUA_GETABILITY_UNGUARDED_PRES_PHEADER',
    'ABILITY_STRIDE_SOURCE_MISMATCH',
    'CALLBACK_ABILITY_POINTER_LIFETIME_NOT_PROVEN',
    'ON_HIT_HOOK_CAN_BLOCK_DAMAGE',
    'ON_HIT_EVENT_TOO_LATE_FOR_PRE_ATTACK_SLOT_DECISION',
    'ALTERNATE_APR_EFFECTS_LAUNCHER_AMMO_NOT_VERIFIED',
    'MANUAL_EPS_ACTION_QUEUE_BOUNDARY_NOT_PROVEN',
)

def _contains(pattern: str, source: str) -> bool:
    return bool(re.search(pattern, source, re.MULTILINE | re.DOTALL))


def inspect(source_fragments: Mapping[str, str], documented_sizes: Mapping[str, object],
            verified_blobs: Mapping[str, str]) -> dict:
    """Evaluate *source snippets*, never attempt to dereference native pointers.

    The caller must separately authenticate full upstream Git blobs; the hash
    strings supplied here are only a consistency check, not that authentication.
    """
    fragments_valid = (isinstance(source_fragments, Mapping) and
                       all(isinstance(source_fragments.get(k), str) for k in UPSTREAM_BLOBS))
    src = (source_fragments if fragments_valid else {})
    sizes = documented_sizes if isinstance(documented_sizes, Mapping) else {}
    pins = verified_blobs if isinstance(verified_blobs, Mapping) else {}
    checks = {
        'upstreamManifestPinsMatch': all(pins.get(k) == v for k, v in UPSTREAM_BLOBS.items()),
        'x64SizesHeader114Ability56': (type(sizes.get('Item_Header_st')) is int and
                                        sizes.get('Item_Header_st') == 114 and
                                        type(sizes.get('Item_ability_st')) is int and
                                        sizes.get('Item_ability_st') == 56),
        'luaItemHelperUsesHeaderStride': _contains(
            r'function\s+EEex_Resource_GetItemAbility\s*\(\s*itemHeader\s*,\s*abilityIndex\s*\)'
            r'.*?Item_Header_st\.sizeof\s*\*\s*abilityIndex\s*,\s*"Item_ability_st"',
            src.get('resource', '')),
        'luaCitemDereferencesHeader': _contains(
            r'function\s+EEex_Resource_GetCItemAbility\s*\(\s*item\s*,\s*abilityIndex\s*\)'
            r'\s*return\s+item\.pRes\.pHeader:getAbility\(abilityIndex\)',
            src.get('resource', '')),
        'cppDemandsBeforeNativeGetAbility': _contains(
            r'curWeaponIn->Demand\s*\(\s*\)\s*;\s*'
            r'(?:const\s+)?Item_ability_st\s*\*\s*const\s+pWeaponAbility\s*=\s*'
            r'curWeaponIn->GetAbility\s*\(\s*curAttackNum\s*\)',
            src.get('cpp', '')),
        'cppPushesEngineAbilityToLuaCallback': _contains(
            r'tolua_pushusertype\s*\(\s*L\s*,\s*pWeaponAbility\s*,\s*"Item_ability_st"\s*\)',
            src.get('cpp', '')),
        'luaHitHookExposesAbilityWithinContext': _contains(
            r'function\s+EEex_Sprite_Hook_CheckBlockWeaponHit\s*\('
            r'attackingSprite\s*,\s*targetSprite\s*,\s*weapon\s*,\s*weaponAbility\s*\)'
            r'.*?\["weaponAbility"\]\s*=\s*weaponAbility',
            src.get('sprite', '')),
        'luaHitHookCanCancelDamage': _contains(
            r'EEex_Sprite_Private_BlockWeaponHitListeners\s*\)\s*do\s*'
            r'if\s+EEex_Utility_TryIgnore\s*\(\s*listener\s*,\s*listenerContext\s*\)'
            r'\s*then\s*return\s+true',
            src.get('sprite', '')),
        'utilityReturnsSuccessfulListenerResult': _contains(
            r'function\s+EEex_Utility_TryIgnore\s*\(\s*func\s*,\s*\.\.\.\s*\)'
            r'.*?return\s+select\s*\(\s*2\s*,\s*table\.unpack\s*\(\s*result\s*\)\s*\)',
            src.get('utility', '')),
        'patchDocumentsFalseNoChangeTrueBlocks': _contains(
            r'false\s*-\s*Don.t alter engine behavior', src.get('sprite_patch', '')) and
            _contains(r'true\s*-\s*Block base weapon damage', src.get('sprite_patch', '')),
    }
    consistent = fragments_valid and all(checks.values())
    return {
        'schema': SCHEMA,
        'status': ('SOURCE_CHAIN_MATCHED_LIFETIME_HOLD' if consistent else
                   'SOURCE_DRIFT_OR_INCOMPLETE_LIFETIME_HOLD'),
        'allSourceChecksPass': consistent,
        'sourceChecks': checks,
        'staticAbilityStrideMismatchBytesAtIndex1': 58 if consistent else None,
        'cppDemandOrderObserved': checks['cppDemandsBeforeNativeGetAbility'],
        'actualDemandReleaseLifetimeProven': False,
        'nativeDllAbiRuntimeVerified': False,
        'callbackPointerLifetimeVerified': False,
        'callbackCanAlterCombat': checks['luaHitHookCanCancelDamage'],
        'callbackCouldBeUsedForPreAttackRanking': False,
        'safeToCallGetAbility': False,
        'safeToCallGetLauncher': False,
        'safeToRegisterListener': False,
        'safeToReadNativeAbilityFields': False,
        'fullActiveEffectsVerified': False,
        'alternateSlotAPRVerified': False,
        'manualEpsActionQueueVerified': False,
        'weaponSwitchAuthorized': False,
        'dispatchAuthorized': False,
        'installAuthorized': False,
        'gameModified': False,
        'ordersSent': 0,
        'readOnly': True,
        'sourceOnly': True,
        'nextAction': 'KEEP_CURRENT_WEAPON_NO_DISPATCH',
        'blockers': list(OWNERSHIP_BLOCKERS),
    }
