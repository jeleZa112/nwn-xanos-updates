# BGXAI 064 — LIVE пункт 71 source-sync/read-only preflight PASS
Дата: 2026-11-12. Результат от пользователя, подлинный вывод Windows:
- Bootstrap: `BGXAI: verified pinned script 75e61c00754d (SHA256 OK)`; no GitHub REST API.
- Menu has 70 and 71. User selected **71**.
- 10 source files `VERIFIED` and `BGXAI 064 SOURCE SYNC DONE. Live scripts and WeiDU unchanged.`
- Return JSON: `status: 064_SOURCE_ONLY_PREFLIGHT_PASS`;
  `last_weidu: ~BGX61\SETUP-BGX61.TP2~ #0 #0 // BGXAI 061 move-to-hit-ally with bounded TTL (BCS + Lua)`;
  `game_bcs_sha: db0fcba4678b00defa2ed7887b57c0d4207effc064891aeb9a0d7dcc1a1a6b0b`;
  `game_lua_sha: fd39d23dc722b549c2af1eaf065541b2ed358a9714f2636b8cab4e45fe7dcec5`;
  `candidate_lua_sha: bfee5278b5b69b1fb4a02e3fea321082b0238407789df83ec6bd2f78d7e19f4b`.
- `patch_proof.changed_anchors: 4`; `other_code_unchanged: true`; `single_existing_selector: true`; `game_written: false`; `installed_game_changed: false`.
- `eeex_runtime_area_api: NOT_CHECKED`; `authorized_to_install: false`.
- `BGXAI064 SOURCE-ONLY PASS. NO GAME WRITES. INSTALL NOT AUTHORIZED.`
- `BGXAI 064 SOURCE ONLY: preflight PASSED. NOT INSTALLED. EEex runtime API NOT VERIFIED.`
- updater completed `BGXAI: update/status action completed.`.

**No repeats required:** do not ask user to rerun 68/71, resend logs or earlier archives. **061 remains installed, 064 NOT installed.**

NEXT: Source-only EEex same-area runtime probe, full-integrated install/rollback candidate audit and explicit guarded opt-in if/when appropriate; preserve user game and original BGXAI_UPDATE.cmd. Prior 170/170 offline tests are not EEex runtime proof. Global AUTO_CONTINUE: progress further through safe steps without requiring '+', never claim background work or silently install.


## Автоматическое продолжение после реального PASS 71

- Пункт 71 пользователя подтверждает исходный код и Sha, но `eeex_runtime_area_api: NOT_CHECKED` остаётся фактическим незакрытым пунктом.
- Создан **read-only EEex native area probe** в `BGXAI/fox_new/experimental_064_same_area_061_source_only/runtime_smoke/`:
  `BGX64_LIVE_AREA_PROBE.lua`, `BGX64_AREA_CONSOLE_ONE_LINE.lua`, `test_064_live_area_probe.py`, `test_064_area_console.py`, `README_LIVE_AREA_RU.md`.
- В настоящем локальном Lua 5.4: **17 новых исполняемых тестов PASS**, в том числе реальная ошибка дубля номера портрета обнаружена и исправлена. С предыдущими 67 тестами 064 тот же запуск **84/84 PASS**. Исходники опубликованы и побайтно сверены с Library.
- Одна строка для **уже доступной пользователю игровой Lua-консоли** читает `m_pArea` у спрайтов партии и проверяет `EEex_UDEqual` с `pcall`, печатает через `C:DisplayText`: `BGX64 AREA api=... self=... same=... diff=... errors=...`. Она не меняет LOCALS/игру/файлы, не регистрирует события; НЕ запускать её в PowerShell.
- **Next live boundary**: один спокойный тест этой однострочной диагностики в запущенной игре без боя. Требуется `api=true`, `self>=2`, `same>=1`, `errors=0` для подтверждения синхронного вызова EEex на реальных объектах; это не доказательство безопасности хука, так что новый мод останется отдельным opt-in. Не заставлять повторять 68 или 71, не просить снова Shank / WeiDU.log.
- Рабочая 061 остаётся установленной, 064 не установлен; ни один файл override/WeiDU не менялся.

