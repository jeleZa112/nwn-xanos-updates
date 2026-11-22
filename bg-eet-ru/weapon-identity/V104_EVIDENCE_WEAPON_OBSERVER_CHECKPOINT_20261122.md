# BG_EET_RU — Weapon/ammo combat log: V104 evidence and observer pilot

Status: SOURCE ONLY. No game installation. Date: 2026-11-22.

## Primary evidence inspected

The user's canonical ZIP `SEND_TO_CHATGPT_BG_EET_RU(20261122-181655).zip` was actually opened; its SHA256 is `4bf3cbacd7cd0978f2cfc2b0811ae7ccd11d2d764410d05922ca54d4a6830db9`; 121 unique entries; ZIP CRC PASS. Source member `50_V104_EEEX_ATTACK_CONTEXT_EVIDENCE.json` confirms:

* Installed local `EEex_scripts/EEex_Sprite.lua`: 61,992 bytes, SHA256 `4813ae620f0b472903848018d66488805db7ba2012e065019f4ea5f2a6afab28`.
* Launcher API `EEex_Sprite_GetLauncher(sprite, curAbility)`: unique, line 916.
* `EEex_Sprite_LuaHook_AlterBaseWeaponDamage(context)`: unique, line 1617.
* `EEex_Sprite_AddAlterBaseWeaponDamageListener(listener)`: unique, line 1000.
* `EEex_Sprite_LuaHook_CheckBlockWeaponHit(attackingSprite, targetSprite, weapon, weaponAbility)`: **0 matches**.
* Installed `EEex_scripts/EEex_Sprite_Patch.lua`: 39,164 bytes, SHA256 `e301b46770477cf29e3d39d6591a5a9fba4f3aeafa03c3dbfa75f7ef6bc13b7f`; damage hooks -1 and -2 uniquely found, lines 802 and 803.
* Optional `B3AttackInfo.lua` not installed. It is not a prerequisite for the known sprite API, so its absence must NOT trigger an install or block static study.
* Canonical ZIP V104 status: `V104_SIGNATURE_MISMATCH_HOLD`; this is due to the missing exact block-hit dispatch symbol, **not** a failed loader, damage listener, or launcher.
* `49_V103_WEAPON_AMMO_SOURCE_AUDIT.json` found launcher and damage listener in local source, but its overall status is `V103_SOURCE_CAPABILITIES_INCOMPLETE_HOLD` because the optional B3 component was missing.
* `47_V101_ABGR_PALETTE.json`: `V101_INSTALLED_GAMEPLAY_TEST_REQUIRED` (runtime screenshot partly verified separately).
* `48_V102_ROLL_MODIFIER_LABELS.json`: `V102_ROLL_LABEL_PREFLIGHT_PASS_NOT_INSTALLED`; do NOT assume V102 is installed.
* All V103 and V104 stages show zero game-file writes.

## Design conclusion

The absence of one **exactly named** Lua callback cannot be fixed by replacing the symbol with another unverified function. The base weapon damage callback can potentially inspect an event context, but its exact keys (weapon item, launcher, ammo, target) remain unknown. This callback cannot establish missed attacks, and the selected current weapon at some other time is not proof that it produced a particular logged hit.

Do not attach raw `Launcher` or `Missile` labels to the wrong combat component. Link weapon and ammunition only if the actual attack event, ability, item and combat log row can be correlated on the exact running game build.

## Source-only pilot

`BG_EET_RU_WEAPON_EVENT_OBSERVER_V1.lua` is an **uninstalled** native Lua 5.4 prototype:
* By default disabled and unregistered.
* A future explicit `Start()` would register only the verified `EEex_Sprite_AddAlterBaseWeaponDamageListener`, if present.
* Does not alter the callback `context`, game combat state, damage, actions, AI, TLK, UI, game saves or files.
* Captures only key/type and bounded primitive values of context, with a 64-event memory buffer; userdatas are never dereferenced.
* `Stop()` disables recording and **does not claim to deregister** the listener, because removal API is unverified.
* Does not claim hit/miss classification, ammo names, launcher identity or log-row matching.

**Offline verification:** local liblua5.4.so.0 compiled this exact source; native behavioral test PASS for missing EEex API, stub listener registration, event schema, no return/no context modifications, stop/restart without duplicate registration, 64-event cap and no claimed miss/weapon attribution. Local source SHA256: `cd7dcf4ad862eed985471e866e8e41db241ec6a7dbc18d47f94f232c662f1448`.

This proof is SOURCE/TEST only, never GAMEPLAY/LIVE PASS. No automatic user-side modification or new updater should be created based solely on this work.

## Next gate

Before any runtime observer can be installed, prepare the implementation through **the same single** `C:\Users\Drevo\Documents\BG_EET_RU\BG_EET_RU_UPDATE.cmd`, with installed-file SHA precheck, external backup, closed-game validation and explicit typed authorization. Determine how the bounded samples will be exported to the existing canonical ZIP with no new user-facing scripts; do not install until these safety gates are actually coded and checked. The user should never be asked to rerun already completed V103/V104 preflights just to reprove the known missing callback.

Only after actual runtime proof: pair per-attack launcher and missile/knife/dart or bullet/arrow/bolt; prove hit/miss coverage and proper log correlation; add **BRIEF-only** labels while keeping FULL original. Never touch BGXAI or BG Voice RU.
