# BG_EET_RU — V111 next gate: misses in existing UI versus weapon identity (2026-11-23)

## New Windows V111 result (do not re-test)
The user ZIP `SEND_TO_CHATGPT_BG_EET_RU(20261123-142938).zip` contains `55_V111_ACTUAL_ITM_TLK_NAMES_READONLY.json` with three locally verified item name/type records: `SW1H04` identified “Длинный меч”; `AROW01` identified “Стрела”, but *unidentified* “Отличная стрела”; `BOW05` identified “Короткий лук”. Live V108 prior events still identify `AROW01` (weapon) + `BOW05` (launcher) in damage callbacks. See `V111_WINDOWS_EFFECTIVE_ITEM_TLK_NAMES_20261123_RU.md`.

## Existing journal code already handles textual misses without a new engine hook
Existing installed V101 came from the V88 `V88_RENDER_NEW` binding:
`text lua "BG_EET_RU_LogView(clean(combatLog[rowNumber]))"`.

Its BRIEF-only `BG_EET_RU_LogView(original)` helper selects rows containing `бросок атаки`, checks d20 and arithmetic, recognizes the original text endings `промах` / `попадание` and formats `ПРОМАХ` / `ПОПАДАНИЕ`. FULL mode returns unmodified original text. This **does not require a new native miss listener** to display the existing textual outcome. The prior V86 source-only `v86_parse_roll_line()` supports similar text from an old user screenshot but is not a runtime event callback.

**What is still missing:** a correct **item weapon/ammunition identity for a missed attack**, not the textual word “промах”. V108's damage callback does not have demonstrated miss coverage. Do not assume `LAST_WEAPON`, most recent damage event, equipped weapon after the fact, or actor/clock timestamps are unique: multiple APR attacks, attackers, dual-wielding, missiles in flight and switches can invalidate association. Any enhanced text must degrade gracefully to outcome without weapon rather than assert an unproven weapon.

## Upstream leads and risks
- Pinned official EEex `EEex_Sprite_Patch.lua` implements base weapon damage from native `CGameSprite::Override_Damage`, and captures `CGameSprite_Hit_Roll` internally. This is **not** a documented full hit/miss CItem listener without further proof.
- A **January 2021 x86** Beamdog forum example used `EEex_AddActionHookGlobal("ONATTACK",...)` to inspect attack-action intent before attack rolls. It **does not prove** that current user's x64 EEex has the same API, that it fires once per attack swing, or that it reports hit/miss or exact weapon. DO NOT copy legacy offsets `+0x34`, `+0x20`, `+0xA80` into modern x64 game; the EEex author expressly warns 64-bit transition invalidates old hooks. Source: https://forums.beamdog.com/discussion/71798/mod-eeex-v0-10-2-alpha/p35 .
- Before a future installation, seek an **already supported, safe, read-only attack-roll event** with stable actor, target, weapon/launcher, and result fields. If unavailable, keep misses in journal as “ПРОМАХ” without fabricated weapon and enrich *verified damage rows* only after unique correlation.
- No new game changes, no extra hook or updater version mandated by this research. Preserve V101 FULL/BRIEF, V108 observer, BGXAI, BG Voice RU, EXE/TLK/UI/saves.

This is SOURCE evidence and design guidance, **not new Windows LIVE proof**.
