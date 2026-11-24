# BG_EET_RU CURRENT — V126 guarded UI-row observer (24.11.2026)

## Shipped
Merged PR #95 into `bg-eet-ai`, squash `677fde40f4acb9436eb3440658f42b0cdc64b0ce`. Canonical `bg-eet-ru/onefile/BG_EET_RU_UPDATE.cmd` now V126, 749992 bytes, SHA256 `a4dab31bb437344350790c4258983cd28fa9987a6a1dfe22e83ccea4d43a2c89`, pinned by `bg-eet-ru/onefile/release.json`. Source module `bg-eet-ru/live-observer/visible_row_guarded_v1.py` frozen commit `601785e3a0e838ec3bc50e19ce26377153507932`, SHA256 `3c079918170ecbea959e1148e1fc9c629d84c751bf0d89415166c98a26921703`.
CI for module and onefile: Windows + Linux PASS, actual Lua 5.4 limited smoke test with `io=nil` PASS. CI status URLs: https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45436051338 and https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45436051294 (later rerun green: 45436307373, 45436307427).

## Exact user step (one existing updater, no second CMD)
Path: `C:\Users\Drevo\Documents\BG_EET_RU\BG_EET_RU_UPDATE.cmd`. Existing V125 should auto-fetch V126; if it fails, replace exact same CMD from raw branch URL after checking file SHA. **Close game and InfinityLoader first.**
Normal double-click V126 menu:
- 1/Enter: default 14 read-only research stages
- 2: guarded install UI-row recorder (only `C:\Games\BG_EET_FOXX_NEW\override\UI.MENU` exact baseline SHA `86ba0c4c36b33a97c4dd57f07ee344df6c2198f46f444f574c798791ad6f7a09`), explicit typed `INSTALL_BG_EET_RU_V126_VISIBLE_ROW_OBSERVER`; external original-backup with SHA; exact rollback state
- 3: rollback exact owned UI change, explicit typed `ROLLBACK_BG_EET_RU_V126_VISIBLE_ROW_OBSERVER`
- 4: game capture: with game closed, launches InfinityLoader.exe, stdout/stderr redirected. User loads a saved game, performs a few hit/miss actions, **closes game to end capture**; V126 parses bounded console markers; result `63_V126_VISIBLE_ROW_OBSERVER.json` in existing `SEND_TO_CHATGPT_BG_EET_RU.zip`
- 5: inspect read-only status of current install and captured rows.

## Technical reality and guardrails
V125 14/14 live run already proven, V108 installed and recorded some weapon/ammo; original V112 has no exact attacker/target/sequence/combatLog message pointer or visible row key.
V126 does **not** install native Hit/CMessage/JIT hooks, and does **not** add weapon names to misses or any journal strings. It instruments only rendering of `combatLog[rowNumber]` to log a bounded set of visible `rowNumber` and existing display strings. Lua `print()` primary transport; `io.open` optional fallback, because standard UI Lua does not expose `io`. Whether print() from this UI goes to redirected InfinityLoader stdout in **the user's specific game build remains unverified**. If no row markers, leave full existing game UI text and save as is; report HOLD.
The exact original `UI.MENU` SHA and unique Lua/render anchors must pass at runtime, else SAFE STOP without writes. Game closed prior to install/restore. Backs up outside game in `Documents\BG_EET_RU\SAFE_BACKUPS`, retains rollback state.
Real game install/capture on user's PC **has not been performed by assistant**; GitHub release alone does not modify game. Need user to run same CMD and type consent. BGXAI, BG Voice RU, TLK, EXE, saves are not changed by updater.

## Next work
Analyze one real V126 captured ZIP (especially `63_V126_VISIBLE_ROW_OBSERVER.json`), verify visible-row recording does not affect presentation. Then continue real native per-hit identity (attacker/target/attack sequence, Win64 ABI/JIT owner, exact CMessage pointer) with separate typed approval, and no unverified attribution. Avoid rerunning V125 old batch without reason. If UI renderer or console markers fail, fix targeted behavior and keep exact backups; do not enable unsafe native hook.
