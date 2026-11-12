# BGXAI 064 — реальный пункт 73 PASS (2026-11-12)

## Подтверждено выводом пользователя Windows

- Existing single CMD verified pinned updater `d66ae072c4a1` (`SHA256 OK`).
- User selected **73** (guarded WeiDU PRECHECK / NO INSTALL); new options 72–76 are present.
- `BGXAI 064G sources already verified. Game unchanged.`; ten file names listed `VERIFIED`.
- Actual preflight JSON: `proof.status=064_SOURCE_ONLY_PREFLIGHT_PASS`, `last_weidu=~BGX61\\SETUP-BGX61.TP2~ #0 #0`; verified BCS SHA256 `db0fcba4678b00defa2ed7887b57c0d4207effc064891aeb9a0d7dcc1a1a6b0b`; Lua source SHA256 `fd39d23dc722b549c2af1eaf065541b2ed358a9714f2636b8cab4e45fe7dcec5`; candidate 064 Lua SHA256 `bfee5278b5b69b1fb4a02e3fea321082b0238407789df83ec6bd2f78d7e19f4b`.
- Patch delta `changed_anchors=4`, `other_code_unchanged=true`, `single_existing_selector=true`, `game_written=false`, `installed_game_changed=false`.
- `authorized_to_install=false` (as expected for read-only preflight).
- `BGXAI064 guarded preflight PASS. Installed 061 remains unchanged.`; `BGXAI: update/status action completed.`

## Context and limits

Earlier user also reported Windows menu 68 / 71 PASS and actual EET in-game `BGX64 AREACHECK true true`; no repeat necessary. This separate native console test confirms `EEex_UDEqual` operates on same-area sprites **outside** the hit callback. It does not prove 064 works under combat-hook conditions. Offline guarded installer tests were `46/46 PASS`, including mock WeiDU install/rollback, SHA gating, wrong root, game process guard. This does not prove real Windows WeiDU installer execution.

## Next boundary

Protected install **menu 74** is ready for explicit user choice **only after** closing game and InfinityLoader; it will back up files externally and require typing exact `INSTALL_BGXAI_064` in the CMD menu. This **modifies installed Lua and WeiDU**; it is not authorized by the user's safe auto-continue rule. Do not trigger menu 74 automatically. Game remains 061 until user explicitly opts in. If user chooses to install, collect installation output including verified backup path and SHA before recommending a new live guard test. Follow with read-only status menu 75. If errors/failed WeiDU, STOP and diagnose without blind retries; menu 76 is guarded rollback only when 064 is last and hashes match.

Do not request repetition of options 68, 71, 73, or the EEex smoke. Avoid source zip instructions—existing pinned one-file updater is canonical.
