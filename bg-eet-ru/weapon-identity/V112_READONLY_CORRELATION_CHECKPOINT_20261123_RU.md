# BG_EET_RU V112 — one-file read-only correlation preflight (2026-11-23)

## Release
- One-file updater version **112**, `bg-eet-ru/onefile/BG_EET_RU_UPDATE.cmd`.
- SHA256 `e469de3968e24d938fc004c936900b6af35c8fdbadad7f0a36e3b3c52798c873`, size 742984 bytes (below 750000-byte older-client download cap).
- `game_writes_allowed=false`, no UI.MENU/TLK/EEex Lua edits, no new native listeners.
- Commit `882abb3a7dc2cc50ce047ac1827cb765056f11f3`.
- Four CI workflows all PASS: onefile selftest `45199967104`, V108 guarded `45199967110`, V106 regression `45199967289`, V105 source `45199967067`. **Do not claim a real Windows V112 run yet.**

## Motivation and what is proven
V108 live damage callback proved `weapon_resref=AROW01`, `launcher_resref=BOW05` for ranged event and `weapon_resref=SW1H04` for melee; V111 Windows read-only local ITM/TLK lookup proved item names and types. However the captured events have no `attacker_id`, `target_id`, `attack_sequence` or `journal_row_id` fields. `hit_miss` and `journal_row` remain unverified. Thus **per-attack weapon attribution to a UI combatLog row, particularly a miss, is not established**. Matching the latest damage event by timestamp or equipment state is not safe.

V112 gathers only static local evidence of existing `override/UI.MENU` combat-log display binding, `EEex_Action.lua` action-start API and relevant saved V108/V111 report structure. It writes just `56_V112_COMBAT_JOURNAL_CORRELATION_PREFLIGHT.json` into the canonical ZIP outside the game, preserving previous entries and verifying CRC/idempotence. A source API being present is **not** runtime proof that every swing or missed attack has a distinct action-start event.

## Next gate
Run the existing updater normally after closing game and loader, obtain V112 Windows read-only audit. If UI/Action source is present, research a genuine stable per-attack ID and matching row ID from supported EEex callbacks; otherwise HOLD, preserving existing FULL/BRIEF text and all mods. No extra game testing or new installs without separate justification and approval.
