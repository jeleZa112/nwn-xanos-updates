## АУДИТ ПРОДОЛЖЕНИЯ 21.11.2026: РИСК RUNTIME-ВЫВОДА R1

Проверено чтением GitHub-исходника `BGXAI/patchsets/ranged_fighter_guarded_20261119/M_BGXWP.lua`, теста `test_weapon_runtime_observer_r1.lua` и предыдущего `M_BXFR_CONSOLE_V2.lua`. В R1 функция `init()` НЕ регистрирует EEex listener, если отсутствует Lua `os.getenv` или `io.open`, либо файл не открылся: возвращает `REPORT_IO_UNAVAILABLE` / `REPORT_DIRECTORY_UNAVAILABLE` и `registered=false`. Консольного fallback в R1 НЕТ. Старый BGXFTRACE использовал console fallback именно для `LuaPatchMode=INTERNAL`. Офлайн-тесты R1 подменяют `io` и `os` макетами, а случай `no_file` прямо проверяет **отсутствие регистрации**. Поэтому 12/12 + 22/22 и 34/34 НЕ доказывают, что R1 создаст JSONL на действительной EET.

Существование API `EEex_Sprite_GetInPortraitID`, `EEex_Sprite_GetActiveStats`, `EEex_Action_AddSpriteStartedActionListener` подтверждено в upstream EEex v1.1.7. **Состояние реального `io/os` в пользовательском runtime НЕ проверено**; не называть R1 установленным или сломанным в игре без LIVE. Пункт 159→1 безопасен как read-only preflight, но **НЕ рекомендовать пока 159→2** до подтверждения рабочего output sink либо source-only исправления с консольным fallback + автоматическим сбором в едином обновляторе, SHA-проверкой, новыми тестами и отдельным разрешением установки. Не подменять это новым номером версии бота; не трогать V6, EPS, WeiDU, сейвы. Актуальная активная задача — по-прежнему приоритетный выбор оружия без прерывания действий.

---

# BGXAI — Weapon Runtime R1: реальное пассивное наблюдение EEex 1.1.7

Дата: 21.11.2026. Задача: выбор лучшего оружия, без остановок текущих действий. Основная ветка BGXAI сохраняет установленную V6 и EPS.

## Новый игровой этап
- Модуль `M_BGXWP.lua` — **отдельный пассивный EEex listener** (`EEex_Action_AddSpriteStartedActionListener`) с ограничением 320 записей за запуск, только членам партии. Считывает сырые `m_equipment.m_selectedWeapon`, `m_curAction.m_actionID`, `m_nNumberOfAttacks`, `m_nTHAC0`, Силу, Ловкость, бонусы урона и флаг Improved Haste через `EEex_Sprite_GetActiveStats`. Эти поля подтверждены в опубликованных EEex структурах; реальные значения/кодировка APR пользователя ещё **НЕ ПРОВЕРЕНЫ**. Данные о 4 альтернативных слотах и происхождении команды EPS не заявляются.
- Результат — `C:\Users\Drevo\Documents\BGXAI_LIVE_REPORTS\BGXAI_WEAPON_RUNTIME_RAW_R1.jsonl`. Никаких игровых приказов, экипировки, удаления очереди, скриптов V6, ручных действий, изменения EPS. Поток записей может быть просмотрен после естественного игрового боя; для начала наблюдения достаточно загрузить игру как обычно, особых тестовых сейвов нет.
- Управление строго через **один** `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd` → новый пункт 159 → подменю: `1` preflight (не меняет игру), `2` guarded install (только после ввода точной разрешающей фразы), `3` status, `4` WeiDU last-only rollback (только после отдельного разрешения). Ни отдельного CMD/ZIP/PowerShell, ни автоматической установки.
- Guarded install добавляет **только** новый файл `override/M_BGXWP.lua` и необходимые WeiDU metadata/installer files. До установки сверяет исходник по SHA256, игровую V6 и соседние BCS/Lua по хешам реального отчёта 158, EEex bootstrap, отсутствие коллизий, отсутствие активной игры, создаёт внешний backup `Documents\BGXAI_BACKUPS`. При конфликте FAIL-CLOSED. Rollback только если BGXWP — последняя запись WeiDU и backup подтверждён.

## Тесты и честный статус
- Lua 5.3 mock listener **12/12 PASS**: изменение Improved Haste, доступность полей, отсутствие вызовов игрового API действий, запись в единую папку, ограничение нагрузки, idempotent hook, не-члены партии игнорируются.
- Python unittest **22/22 PASS**: source SHA, preflight game unchanged, защита от коллизий, запрет установки без typed approval, отчёт вне игрового дерева, копии backup, симуляция install/last-only rollback, STOP при чужой установке после BGXWP. Python `py_compile` PASS.
- REAL EET (согласно ранее полученному JSON): Native WeiDU **PASS** для BAF выбора 4 слотов; установленная V6 hash EXACT; игровые файлы без изменений. Это **НЕ доказывает**, что новый runtime observer загрузится/выдаст показания. Никогда не представлять mocks как LIVE PASS.
- До typed approval: **CODE/TEST PASS, DEPLOY/LIVE НЕТ**. После установления наблюдателя потребуются обычный игровой запуск и присылка одного `BGXAI_WEAPON_RUNTIME_RAW_R1.jsonl`; затем сопоставление реальных APR с выбранными слотами, бафами и подготовка per-slot rankings без вмешательства в действие.
