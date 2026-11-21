## НАЙНОВЕЙШИЙ LIVE РЕЗУЛЬТАТ 21.11.2026 — R1.1 ИЗ ИГРЫ

**DEPLOY/LIVE наблюдателя уже подтверждены** пользовательским `BGXAI_WEAPON_RUNTIME_RAW_R1.jsonl`: 1 SESSION, 1 READY, 29 ACTION, actor 139135050 (portrait 2), selected raw 12→35 на seq28, aprRaw 2→7. Старое `DEPLOY/LIVE=NO` ниже относится к прошлому этапу ДО установки и теперь устарело. Кодировка IESDP условно означает 2.0→1.5 APR, а не 2→7 APR; `SLOTS.IDS` предполагает AMMO1→WEAPON. Не доказаны реальные item/launcher/ammo resref, четыре альтернативных APR и происхождение ручной/EPS команды. Обнаружен и исправлен SOURCE ONLY баг 16-битного лимита actorId в V2, 18/18 Lua offline PASS. Игровой приоритетный переключатель НЕ установлен, только прежняя V6. Не повторять 158, 159 preflight/install и уже выполненный live-сбор. Подробнее: `CURRENT/BGXAI_WEAPON_RUNTIME_R1_LIVE_CHECKPOINT_20261121_RU.md`. Текущий следующий этап: per-slot / item / ammo / EPS evidence read-only, после отдельного разрешения на любой новый игровой deploy. Документ ниже хранит исторические этапы.

---

# 21.11.2026 — BGXWP R1.1 реально установлен, LIVE ещё не проверен

Получен `BGXWP_OBSERVER_SETUP_R1(1).json` от пользователя. Проверены байты: SHA256 `f8a1cfb448430c3107ae70f48d18438b603a5fceb304207779c1edc21a5fef0f`; статус `BGXWP_OBSERVER_INSTALLED_NOT_YET_RUNTIME_TESTED`; `game_modified=true`; `source_sha256=f62a467c8bc5b952612ca23f701ecc23838b8782799c7801f2e01a38267e8f36`; UTC установки `2026-11-21T12:47:16.604553+00:00`. Внешний backup: `C:\Users\Drevo\Documents\BGXAI_BACKUPS\PRE_BGXWP_20261121T124714Z`. Архив отчёта: Library `/BALDURS_GATE_EET_AI/DIAGNOSTICS/BGXWP_OBSERVER_INSTALL_REAL_20261121T124716Z.json`.

**CODE/TEST:** R1.1 исходники опубликованы, 16/16 Lua и 18/18 Python офлайн PASS. **DEPLOY:** пользовательский guarded WeiDU установщик сообщил успех, новый `override/M_BGXWP.lua` установлен; независимо игровые файлы не просматривались, а доказательство — результат самого установщика. **LIVE:** не проверен EEex hook, запись APR/THAC0, значения 4 альтернативных слотов, источник ручной/EPS команды, выбор оружия. НЕ просить повторно 158, 159→1 или 159→2. Игру, V6, EPS и сейвы дополнительно не изменять.

**Следующее действие:** закрыть игру, штатный `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd` → **159 → 5** (запускает InfinityLoader с перенаправлением консоли, это и есть запуск игры; не запускать InfinityLoader вторым способом). Провести обычный бой, затем выйти из игры и штатный updater → **159 → 6** (сбор данных), прислать `C:\Users\Drevo\Documents\BGXAI_LIVE_REPORTS\BGXAI_WEAPON_RUNTIME_RAW_R1.jsonl`, если он создан, и `BGXWP_OBSERVER_SETUP_R1.json` со статусом сборщика. При STOP, пустом логе или отсутствии JSONL: прислать последний setup report и сообщение, не запускать повторно без анализа. Без LIVE задача умного выбора оружия не завершена.

---

# 21.11.2026 — реальный Windows preflight 159→1: PASS

Получен от пользователя `BGXWP_OBSERVER_SETUP_R1.json` (SHA256 вложения `76de217afb8132f08f0c72e1cfdf0b09aa356d3216f960a111d4010cb68eeb5e`). `status=PREFLIGHT_OBSERVER_READY_SOURCE_ONLY`, `game_modified=false`, `runtime_EEex_validated=false`, `source_sha256=f62a467c8bc5b952612ca23f701ecc23838b8782799c7801f2e01a38267e8f36`. Проверенные исходные BCS и Lua совпадают с V6 baseline. Последняя запись WeiDU: `BGXRANGED6`, а не `BGXWP`. Сохранённая копия отчёта: ChatGPT Library `/BALDURS_GATE_EET_AI/DIAGNOSTICS/BGXWP_OBSERVER_PREFLIGHT_REAL_PASS_20261121.json`.

**Не просить повторять 159→1 или 158.** Следующая контролируемая стадия — 159→2 (guarded install) **только с отдельным явно введённым разрешением** `INSTALL_BGXWP_READONLY_OBSERVER`; до него `DEPLOY=NO, LIVE=NO`. Установка касается только нового пассивного `override/M_BGXWP.lua` и WeiDU метаданных, но требует закрытых игры/InfinityLoader/WeiDU, SHA-валидации и внешнего backup. Получить один `BGXWP_OBSERVER_SETUP_R1.json` после установки либо STOP (при STOP не повторять, не вмешиваться). При успехе — 159→5 для консольного захвата, обычный бой, выход из игры, 159→6 для сбора `BGXAI_WEAPON_RUNTIME_RAW_R1.jsonl`. Реальный APR всех альтернативных слотов, provenance EPS/manual и переключение без задержки пока НЕ доказаны. Прежние разделы ниже — история.

---

# 21.11.2026 — BGXAI Weapon Runtime R1.1: резервный вывод и единый пункт 159

**Активная задача только одна:** приоритетный выбор оружия без прерывания атаки, заклинания, лечения или ручного приказа. Рабочая BGXRANGED6 V6, BGXFENEMY, EPS 18.4, EET и сохранения не изменены.

**CODE:** `BGXAI/patchsets/ranged_fighter_guarded_20261119/M_BGXWP.lua` (R1.1) теперь пишет диагностические JSONL в `Documents/BGXAI_LIVE_REPORTS`, если есть Lua `io.open`+`os.getenv`, ИНАЧЕ выводит те же JSON-сообщения с префиксом `[BGXWP]` через `Infinity_Log`/`print`. При отказе обоих каналов — fail-closed, listener не регистрируется. На каждом событии — `sequence` для дедупликации двух консольных каналов без потери отдельных атак. Сохраняются только сырые наблюдаемые поля текущей атаки; APR всех четырех слотов, оружейные эффекты, очередь EPS/manual и безопасная граница переключения не доказаны. Ни одной игровой команды и переключения. SHA256 Lua `f62a467c8bc5b952612ca23f701ecc23838b8782799c7801f2e01a38267e8f36`, 5149 байт.

**CODE единого обновлятора:** существующий `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd` не заменяется и по-прежнему показывает пункт **159**. Внутри Python `BGXWP_OBSERVER_GUARDED.py` подменю 1–4 без изменения разрешений: 1 preflight RO, 2 install с точным токеном и SHA/backup/WeiDU, 3 статус RO, 4 last-only rollback с отдельным токеном. Добавлены **5** — запуск обычного `InfinityLoader.exe` с сохранением stdout/stderr вне игры; **6** — сбор последнего ограниченного консольного лога в `BGXAI_WEAPON_RUNTIME_RAW_R1.jsonl` с проверкой SESSION/READY/ACTION. Если прямой JSONL уже существует, он сохраняется, не перезаписывается. Если файлы не содержат достаточных свидетельств — STOP/HOLD, не выдумывать LIVE успех. SHA Python `90dd7386eb94bccce959f14ef0fea40779d7b1f4fea461a55dd5cd22607fbcb6`, 22340 байт.

**TEST:** локальный Lua 5.3 (luahbtex) **16/16 PASS**: файловый вывод, console при отсутствии `io`/`os`, ошибка записи, `Infinity_Log` без print, print без Infinity_Log, no-sink, EEex fail, APR/бафы, 320 записей, идемпотентность и отсутствие игровых команд. Локальные Python `unittest` **18/18 PASS**: прямой RAW файл, консольный поток, дубли, последовательности атак, валидация ограничений, ошибки, пустая сессия, symlink, oversize, запуск/отказ launcher. Ранее 22/22 исходных guarded mocks относились к R1; полный новый интегрированный guarded модуль НЕ проверен реальным Windows/WeiDU и их нельзя автоматически объявлять повторно пройденными.

**PIN:** immutable source commit `f502eed6fca8e5522e49b4d3dc062581d99c2cf8` закреплен `BGXAI/fox_new/BOOTSTRAP_PIN.json` commit `3a00369eefbda3e31eda568f3e46a075ba2449fc`. Старый `BGXAI_SYNC.ps1` не изменен: 79900 байт, SHA256 `6f1e0a03968785ef916c85d5b7a8c82c99c49fa1102ffa43097b8d2172fde45c`; пункт 159 автоматически синхронизирует два новых SHA из manifest, старые пункты 1–158 сохранены.

**DEPLOY:** только GitHub SOURCE/PIN и библиотека ChatGPT; игра Windows не менялась. **LIVE:** нет новой записи и нет проверки загрузки R1.1 в реальной EET. 158 уже PASS, повторять не нужно. Следующая граница: **159 → 1 (read-only preflight)**; при явном точном согласии на игровую установку — **159 → 2** (не запускать автоматически). После установки и перед игровым запуском **159 → 5** для страховки консольного вывода; затем обычный бой, закрыть игру, **159 → 6** и приложить один `BGXAI_WEAPON_RUNTIME_RAW_R1.jsonl`. Сам запуск 159→5 без установки не даст журнал R1.1. По реальным данным продолжить именно оружейный per-slot/APR/effects/queue адаптер; не переключаться на AoE, песни, роли или лечение.

---

## АУДИТ ПРОДОЛЖЕНИЯ 21.11.2026 — НЕПРОВЕРЕННЫЙ КАНАЛ ВЫВОДА R1

Код M_BGXWP.lua и test_weapon_runtime_observer_r1.lua проверены повторно по исходникам GitHub ветки bg-eet-ai. R1 при отсутствии io.open, os.getenv или невозможности открыть JSONL выходит из init() без регистрации listener (registered=false), не переходит на консоль. Модельные 12/12 Lua + 22/22 Python = 34/34 доказывают лишь офлайн-поведение; тест no_file намеренно ожидает незарегистрированный listener, io и os в базовом тесте подставлены макетами. Прежний живой BGXFTRACE M_BXFR_CONSOLE_V2.lua предусматривает fallback Infinity_Log/print для среды INTERNAL. Наличие io/os в живой пользовательской EEex 1.1.7 ещё не подтверждено. Это риск пустого отчёта, а не доказанный LIVE-сбой.

Upstream EEex v1.1.7 подтверждает EEex_Sprite_GetInPortraitID, EEex_Sprite_GetActiveStats, EEex_Action_AddSpriteStartedActionListener и автоматическую загрузку M_*.lua; проблема касается именно output sink. Установка в игру по-прежнему НЕ выполнена. Пункт 159→1 является read-only preflight, но 159→2 пока не рекомендован: сначала обеспечить проверенный файловый вывод либо fallback console с автоматическим сбором из единого BGXAI_UPDATE.cmd, затем тесты, SHA/backup/явное согласие. Не менять установленную V6, EPS18.4, BGXFENEMY, игру и сохранения. Фокус не смещать с приоритетного выбора оружия.

---

# 21.11.2026 — WEAPON RUNTIME R1, OPTION 159 (NEXT STEP)

**Фокус:** только интеллектуальный выбор оружия, без прерывания текущей атаки/каста. Реальный JSON 158 уже PASS (V6 exact, 4-slot WeiDU compile success, game unchanged), повторять 158 не требуется.
**CODE/TEST:** опубликован `M_BGXWP.lua` — изолированный EEex 1.1.7 passive started-action listener, читает сырые APR/THAC0/STR/DEX/ImprovedHaste, selectedWeaponRaw, без приказов/переключения/очередей EPS. 12/12 Lua offline PASS. Guarded `BGXWP_OBSERVER_GUARDED.py`: 22/22 Python mock PASS, проверка baseline SHA из реального отчёта, external backup, точное разрешение на установку, last-only WeiDU rollback.
**Один обновлятор:** `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd` меню 159 (1 preflight RO; 2 consent install; 3 status RO; 4 consent rollback). Pinned updater commit `3043e5188ad4754d1fdb71bef23f1a793f367129`, SHA256 `6f1e0a03968785ef916c85d5b7a8c82c99c49fa1102ffa43097b8d2172fde45c`, 79900 bytes. Bootstrap pin changed on GH commit `bb0e3d9aa94ae3e831f737c03ef095e0e6bc0dc2`; choices 1–158 unchanged.
**Результат при LIVE запуске после отдельного согласия на модуль:** `C:\Users\Drevo\Documents\BGXAI_LIVE_REPORTS\BGXAI_WEAPON_RUNTIME_RAW_R1.jsonl` (сырая диагностика, НЕ подтверждение альтернативных APR или полноценного ИИ). **DEPLOY/LIVE:** модуль не установлен; игра, V6/EPS, saves нетронуты. Следующий шаг: игровая проверка 159 и присылка одного отчёта, не новые моковые версии. Разрешение необходимо только для 159→2, проверка 159→1 без изменений игры.

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
