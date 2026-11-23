# BG_EET_RU V111 — research on miss events, SOURCE ONLY (2026-11-23)

## Exact evidence already verified LIVE
- V108 real EEex callback `EEex_Sprite_AddAlterBaseWeaponDamageListener` returned `SW1H04` on two sword events and `weapon_resref=AROW01`, `launcher_resref=BOW05` on two successful ranged-damage events. These prove the CItem field values in a **base weapon damage callback only**.
- User personally confirmed **two bow shots missed** before switching to sword+shield in the sword-only capture, consistent with the absence of missed shots in that callback. Absence **does not by itself prove** comprehensive miss coverage behavior.

## External source evidence, not a tested miss API
- Official upstream EEex file `Bubb13/EEex`, `EEex/copy/EEex_scripts/EEex_Sprite.lua`, pinned commit `a6d21abe44e20509f5d0259ccc6c7e7f9d12b285`, exposes `EEex_Sprite_AddBlockWeaponHitListener` and `EEex_Sprite_AddAlterBaseWeaponDamageListener`, but not a clearly named `AddAttackRollListener` / `AddWeaponHitListener` / `AddHitListener` in the inspected file. https://github.com/Bubb13/EEex/blob/a6d21abe44e20509f5d0259ccc6c7e7f9d12b285/EEex/copy/EEex_scripts/EEex_Sprite.lua
- Upstream `EEex_Sprite_Patch.lua` describes `CGameSprite::Override_Damage` and `EEex_Sprite_LuaHook_AlterBaseWeaponDamage(context)`; its native JIT tracks `CGameSprite_Hit_Roll` and intercepts `Hook-CGameSprite::Hit()-FormatRollCall`. This is **not** a documented safe Lua listener for every miss nor a proof that adding another native hook is safe in the user's game. https://github.com/Bubb13/EEex/blob/a6d21abe44e20509f5d0259ccc6c7e7f9d12b285/EEex/copy/EEex_scripts/EEex_Sprite_Patch.lua
- `BlockWeaponHitListener` is a hook intended to block base damage and on-hit effects; it must **not** be used just to observe misses without proof, because it can affect combat mechanics and may only see hit paths.
- Engine `FormatRollCall` label may offer a research lead. Do **not** patch binary addresses, introduce old x86 offsets, dereference native memory, or register an invasive hook merely from these source names.

## Next gating work
1. First complete **V111** Windows READ ONLY audit of current `ITM` and Russian `TLK` names. Three targeted resources only, no modifications and no game run.
2. For future miss capture, identify a documented or currently installed, observer-only callback that emits every attack attempt, with a reliable attacker/target identifier, weapon/ammo and roll outcomes. A source-only symbol/call-graph audit is useful; no native install before separately assessing safety.
3. Prove **runtime journal row correlation** independently, including how FULL and BRIEF handle hits/misses; no UI modifications until evidence exists.
4. Do not repeat V108 melee and bow capture. Do not touch BGXAI, BG Voice RU, installed V101 FULL/BRIEF, `UI.MENU`, TLK, EXE, or saves.

This report distinguishes **upstream source evidence** from Windows **LIVE** observations; it is not a new miss implementation.
