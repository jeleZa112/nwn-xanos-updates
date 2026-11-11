# BGXAI 064 — точный Lua-мост 061 восстановлен; исправление ARE, 12.11.2026

## База и живой статус

- BGXAI 061 **INSTALLED**, один реальный игровой эпизод подтверждён пользователем: охранник подошёл к союзнику, бафнулся, убил нападавшего. Не распространять вывод на все боевые ситуации.
- Текущий код Lua восстановлен **побайтно по исходнику 056 и двум известным заменам 061**: 056 SHA256 `35e450b6600f0fc65d47e535126a52e0303c360033307fa920776faec3f581ab` → 061 SHA256 `fd39d23dc722b549c2af1eaf065541b2ed358a9714f2636b8cab4e45fe7dcec5`. SHA совпадает с ранее подтверждённым реальным установленным Lua.
- Обнаружена фактическая логическая ошибка 061: Lua выбирает ближайшего F=ON стража по координатам без сравнения ARE, хотя BCS 061 потом требует `InMyArea`. Это допускает бездействие из-за выбора защитника за дверью. Старые исследования 056/059 уже фиксировали подобный сценарий.

## Источниковое исправление 064 (не установлено)

- В прежнем единственном `BGX52Bridge.prepare` добавлены проверка `victim.m_pArea`, `guard.m_pArea` и `EEex_UDEqual` внутри `pcall`, плюс точная версия и диагностическая причина отказа. **Всего 4 уникальные обратимые замены**; никаких дополнительных селекторов, Lua-боевых приказов или переписывания BCS/EPS/WeiDU.
- Новый исходник `BGXAI/fox_new/experimental_064_same_area_061_source_only/M_BX43_064_CANDIDATE.lua`, SHA256 `bfee5278b5b69b1fb4a02e3fea321082b0238407789df83ec6bd2f78d7e19f4b`, GitHub source creation commit `a53147dcfabc219c17a8775c191c4fc46d777a54`.
- Extracted literal `B.prepare` source confirmed identical to GitHub candidate by 4389-character length + CRC32 `2cd385f8`; 15 native Lua 5.4 tests pass, including P4 outside / P3 inside, same-area fallback, no API, exceptions, dedup, no action commands.
- `BGXAI64_PATCH.py` pins both SHA and checks exact reversible deltas. `BGXAI64_PREFLIGHT_READONLY.py` checks current `WeiDU.log`, live/staged BCS/Lua, version hashes and candidate SHA with no game writes. Two test suites added: 11 patch tests + 14 read-only preflight tests. Combined with existing 103 baseline tests = **143/143 PASS** in one isolated Python+Lua test run.
- All source files, tests and compatible SHA `manifest.json` (10 files) saved in GitHub `BGXAI/fox_new/experimental_064_same_area_061_source_only/` and Library `/BALDURS_GATE_EET_AI/BUILD/BGXAI_064_SAME_AREA_SOURCE_ONLY/`. Source files and manifests checked against local Git blob SHA. The manifest and source draft agree on all 10 filenames.

## Установочный маршрут — разработка, НЕ активирован

- В GitHub **отдельно** подготовлен `BGXAI_SYNC_070_071_DRAFT.ps1` source-only draft, commit `711e7b70a9510c1db48595c305b3d6d116a2ebbb` (Git blob `8182572c3dcbf2e42e27d219046c2ff5632f298e`). Это проект пунктов 70 (source sync) и 71 (read-only preflight) существующего одного автообновлятора.
- Пять текстовых вставок в draft обратимы; пункты 1–69 сохранены, новые пункты вызывают только SHA-верификацию и read-only preflight, нет команды установки 064.
- **ЖИВОЙ `BGXAI/BGXAI_SYNC.ps1` не изменён** (blob `2c868030f44a0f59a5efffc9458fa7e29766c24d`), его bootstrap/пины и игра не изменены. В доступном пользователю updater **нет пунктов 70/71**. Не советовать выбирать их до реального релиза.
- Нативная среда PowerShell недоступна здесь: draft **НЕ проверен исполнением в PowerShell** и НЕ готов к активации. Наличие `EEex_UDEqual` ранее подтверждено в пользовательской игре (`AREAAPI=function`), но безопасность вызова в on-hit listener ещё не доказана. Если API не работает, кандидат 064 намеренно пропускает guard Q — не устанавливать до native proof.

## Следующий шаг без вопросов

Продолжить безопасную подготовку, если доступно: PowerShell execution test на корректной Windows-среде/CI; интроспекция EEex в самой игре read-only через существующий механизм, *без новых ручных установщиков*. Затем отдельный предустановочный контроль и согласие на запись в игру. **Оставить установленную рабочую 061 без изменений.** Пользовательское правило AUTO-CONTINUE действует для всех безопасных действий, но не означает фоновой работы после ответа.

## Дополнение 12.11.2026 — полный Lua-мост + WeiDU mock release rehearsal

1. Восстановлен реальный полный `M_BX43.lua` 061 **из сохранённого пакета 056**, проверены SHA256 056 `35e450…581ab`, 061 `fd39d2…dcec5` и 064 `bfee52…e19f4b`. В текущей разработке сохранены `M_BX43_061_BASELINE_READONLY.lua` и `M_BX43_064_CANDIDATE.lua`. Это не чтение текущего пользовательского диска; совпадение 061 сопоставлено с его ранее присланным выводом установщика.
2. Создано `test_064_full_lua.py`: 13 новых тестов реальных целых Lua-модулей 061/064 в Lua 5.4 под mock EEex, через всю цепочку `EEex_Sprite_AddBlockWeaponHitListener` → `P.onWeaponHit` → `BGX52Bridge.prepare` → запрос LOCALS. Тест на 061 *воспроизводит ошибку выбора P4 из другой ARE*, тест на 064 выбирает доступного защитника в той же ARE. Проверены 2 охранника, F=OFF, отсутствие API/ошибка userdata, дубликат попадания, отказ при атаке союзника, неподавление попадания, отсутствие Lua-боевых команд.
3. Создан `BGXAI64_INSTALL_SOURCE_ONLY.py`: **не подключённый к автообновлятору** проект опциональной установки/отката через WeiDU с проверкой exact SHA/последнего WeiDU, `--yes --confirm INSTALL_BGXAI_064`, проверкой закрытых процессов Windows, внешними SHA-подтверждёнными backup, установкой только Lua, BCS неизменён, отказами при дрейфе и запретом слепой повторной установки. `test_064_install_mock.py` проверяет 14 сценариев с *подменённым WeiDU во временной папке*, включая установку → проверку → откат к точной 061 и ошибочные ветви; реальный WeiDU/Windows **не запускался**. Исправлена утечка файлового дескриптора в source code, повторено с `-Werror::ResourceWarning`.
4. Обе группы последовательно прошли в одной текущей среде: прежний набор **103/103 PASS**, новый пакет **67/67 PASS**, итого **170/170 офлайн-тестов**. Интеграция в игру **не проверена**.
5. Новые исходники/тесты добавлены в ту же существующую папку GitHub `BGXAI/fox_new/experimental_064_same_area_061_source_only/` и в Library `BUILD/BGXAI_064_SAME_AREA_SOURCE_ONLY/`; отдельный ZIP или новый независимый установщик пользователю не предлагать.
6. **Важная развилка:** действующий bootstrap pin всё ещё ссылается на старый коммит `e0bd9bdd5c9b2872e0c47f28b414bef67c9ea907` с меню 1–69. Черновые 70/71 лежат в отдельном PS1 и пока НЕ доступны. Обновление активного updater/bootstrap без Windows PowerShell runtime-теста может лишить пользователя работающего меню. Не менять до такого теста; не объявлять меню 70/71 готовым. Нужна ещё нативная EEex проверка same-area внутри on-hit callback и отдельное согласие на game write.

**Следующая реальная граница:** native Windows PowerShell syntax/execution test черновика + read-only проверка текущего 061 в пользовательском updater (68, когда потребуется), затем только guarded release. Не просить пользователя заново присылать исходные ZIP или гонять Шанка; сохранять рабочую 061. Не утверждать, что 064 установлена.
