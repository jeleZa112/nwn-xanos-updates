# BGXAI AUTO BATCH 168 — EPS/EEex source inventory (24.11.2026)

## User EET result (already done; DO NOT repeat old checks)
`BGXAI_AUTO_BATCH_RO_20261124T073318947435Z.json` reported `SAFE_READONLY_BATCH_COMPLETE_GAMEPLAY_HOLD`, 10 stages, 50 Python cases (3 skipped), 512 synthetic safety cases, 108 BAF guard assertions, `gameFilesChanged=false`, `ordersSent=0`. Previous real native WeiDU compilation successfully reused. Runtime APR alternative, selected launcher-ammo, player/EPS/AI origin, action boundary, target freshness and authenticated producer all HOLD.

## Source audit
- Installed R27 callback observes **selected only** `m_nNumberOfAttacks` / THAC0; no proof of alternate slot APR.
- EEex **v1.1.7** `EEex_Action.lua` offers action-start hook; it does not by itself prove whether action came from player, EPS or BGXAI.
- EEex `EEex_Sprite.lua` exposes `EEex_Sprite_GetActiveStats`, still current-state not counterfactual alt-slot APR.
- Published EPS source `SarahG-579462/Enhanced-Powergaming-Scripts` `core_base.tph` includes `MO_SpellCast` and `ActionListEmpty()`. Public `main` SHA is not automatically the user's installed 18.4 version. Never infer manual origin from these alone.

## Implemented automatically in SAME updater, no separate CMD
- Existing `BGXAI_UPDATE.cmd` menu **168** now has one extra `installedScriptSources` stage: 11 total. Scans a **fixed allowlist of 7 relative locations** for likely EPS `core_base.tph` / `mocore.baf` and EEex `EEex_Action.lua` / `EEex_Sprite.lua`; bounded 3MB/file, checks symlink/reparse, SHA256 and counts of relevant predicates, reports only relative names, no user paths.
- It **never** claims same installed version, real manual/EPS-origin or alt-slot APR proof. Missing source returns an informational state, not a false PASS; symlinks and oversized source HOLD. Never uses code from these files, never alters game.
- Package preserved existing 168 loader script 79,935 bytes, unchanged 1..168 branches. Updated five-file SHA256 manifest and immutable pin to `76b7d47998fcfeeaa5e532eefeed171c5e2c3895`. New batch source SHA256 `cf0503c7d7c0f3097ee5519f755d4d0291c653e5d52a33d266ae1c2db3572f85`; test source SHA256 `b8a9fbc1b00d43f0dcc601c46307118e19211c053773b6783c972b66624247ba`.
- Local **38/38** test suite PASS on Linux; 21 native WeiDU contract tests. Independent GitHub CI **SUCCESS** Windows+Ubuntu: https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45414065171 ; includes existing Lua 439 x3 on Linux and PS5.1 syntax on Windows.
- Single report remains `%USERPROFILE%\Documents\BGXAI_LIVE_REPORTS\BGXAI_AUTO_BATCH_RO_*.json`. Next run **168** is necessary only to gather **NEW installed-source inventory**, not to retest R27/R28/167, not to authorize game switching. Once it returns, analyze one report and update same program, no duplicate user scripts.

**CODE/CI DONE; NEW GAMEPLAY V3 DEPLOY/LIVE NO.** Do not confuse data collection with achieving runtime producer/queue origin.
