# 21.11.2026 — РЕАЛЬНЫЙ ОТЧЁТ 158 И ЕДИНАЯ ПАПКА BGXAI_LIVE_REPORTS

- Получен пользовательский `BGXAI_WEAPON_NATIVE_PREFLIGHT_V1.json`, сгенерирован `2026-11-21T11:40:16Z`: `READONLY_NATIVE_PREFLIGHT_PASS`; `V6_DPLAYER_BINARY_EXACT`; `NATIVE_COMPILED_TEMP_ONLY`; `game_files_unchanged=true`. Компиляция 4690 байт, SHA256 `3a3c416ea9c2f99ede389a9242aa2c9d5e7145ab1a2a69ccc53917bbd01ef7a6`. `WSPATCK.2DA` не найден именно в `override`; это НЕ доказывает отсутствия ресурса в BIF. В отчёте `live_eeex_character_stats_read=false`, all_four_weapon_item_stats=false, EPS/manual provenance=false; Weapon Priority LIVE НЕТ.
- Восстановлено давно согласованное место диагностик на Windows: **`C:\Users\Drevo\Documents\BGXAI_LIVE_REPORTS`**; ранее использовалось для `BGXAI_FRIENDLY_AGGRO_READONLY_*.json` и ZIP. Источник `BGXAI_WEAPON_GAME_PREFLIGHT_RO.py` изменён: будущий пункт **158** пишет `BGXAI_WEAPON_NATIVE_PREFLIGHT_V1.json` именно туда, без новых разрозненных папок и без fallback.
- Локально 15/15 Python-тестов PASS, включая контроль новой папки и сохранность старых файлов, `py_compile` PASS. SHA256 нового RO-источника `a02930a6ba5f7a093475f9105fc72d385d5ab1aac40c588763c5bc941dfe5547` (8412 байт), манифест обновлён и pinned commit `c9ef9245d20621a7bb05b5ab4abc363b6688a87a`. Новый `BOOTSTRAP_PIN.json` зафиксирован коммитом `4528daa626c2232ef41d68adc40cf07d89164f21`. Единый `BGXAI_SYNC.ps1` НЕ изменялся (79 962 байт; SHA256 `5fc39ea68c0eeab4aed8d014c02b07fe05eaaa6657cc6b59757d39614db1f9d6`).
- Прикреплённый отчёт архивирован в Library `/BALDURS_GATE_EET_AI/DIAGNOSTICS/BGXAI_WEAPON_NATIVE_PREFLIGHT_V1_20261121T114016Z.json`. Копия на Windows в старом пути не перемещалась удалённо — нет доступа к ПК. Ни новая версия пункта 158, ни архивирование не запускали игру; существующая V6/EPS не менялась. Старый успешный пункт 158 повторно запускать не нужно только ради архивации.
- Следующий технический этап — полный game-verified EEex снимок характеристик/APR, бафов и четырёх slots + EPS/manual safety; затем gated deployment с отдельным разрешением. Не переходить к AoE/прочим веткам.

---

# BGXAI — 21.11.2026 — реальная проверка выбора оружия через единый обновлятор, пункт 158

## Что сделано

- Добавлен **пункт 158 — Weapon V3 native preflight READ ONLY** в существующий `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd` через новую SHA256-закреплённую версию `BGXAI/BGXAI_SYNC.ps1`. Старый CMD не меняется; он сам скачивает закреплённый скрипт из GitHub после сверки SHA.
- Скрипт в закреплённом коммите `fad6c28957bc0f09f3655193f08fe7c7b8f77416`, SHA256 `5fc39ea68c0eeab4aed8d014c02b07fe05eaaa6657cc6b59757d39614db1f9d6`, размер **79 962 байта** (ниже жёсткого лимита 80 000). `BOOTSTRAP_PIN.json` обновлён коммитом `4ce5d61013d28cd6dda08d8b304e27529f15fba7`.
- Старые пункты **1–157 сохранены**. Из прежнего скрипта изменены только строки отображения меню (`Write-Host` → `echo` в экранном меню), сокращены девять текстов `NO GAME FILES CHANGED.`, добавлены read-only release spec, надпись 158 и команда 158. Никаких изменений работающих инсталляторов, BCS, EPS, BGXFENEMY и V6.
- Пункт 158 синхронизирует только два файла из нового manifest через `SyncRelease`, проверяет размер/SHA256, помещает их в `BGXAI_DEV\weapon_native_ro` и вызывает read-only Python preflight. Внешних CMD/ZIP/PowerShell файлов от пользователя не требуется.
- Native preflight сверяет `chitin.key`, `WeiDU.log`, `DPLAYER.BCS`, `BDDEFAI.BCS`, `WTASIGHT.BCS`, `PRIEST1.BCS`, Lua EPS/BGX и доступные override 2DA по SHA до и после; пытается **скомпилировать BAF выбора четырёх слотов через WeiDU и установленные EET IDS только во временной папке**. В `override` ничего не копирует, игру/сохранения не меняет. Отчёт в `%LOCALAPPDATA%\BGXAI_UPDATER\reports\BGXAI_WEAPON_NATIVE_PREFLIGHT_V1.json`.

## Проверки и ограничения

- **CODE:** Python `BGXAI_WEAPON_GAME_PREFLIGHT_RO.py`, 4-блочный read-only BAF и manifest опубликованы в GitHub `bg-eet-ai/BGXAI/patchsets/ranged_fighter_guarded_20261119/`. Их GitHub-байты сверены с SHA256 манифеста до обновления updater.
- **TEST:** 13/13 Python `unittest` на макете EET, включая контроль неизменности файлов, симуляцию сбоя компилятора, missing WeiDU, drift исходника, изменение WeiDU.log и запрет иного пути игры. `py_compile` PASS. Отдельно проверены 158 существующих числовых ветвей `switch` и размер/SHA закреплённого обновлятора. **Настоящий WeiDU на пользовательской EET ещё НЕ запускался.**
- **DEPLOY:** обновлён только **канал исходников в GitHub** (pin / onefile). Сам пользовательский CMD не заменяется и игровые файлы не изменены.
- **LIVE:** выбора приоритетного оружия в игре пока **НЕТ**; последняя установленная работающая V6 остаётся прежней.
- Пункт 158 **не доказывает реальный APR альтернативных слотов, активные бафы EEex или происхождение приказов EPS**: это следующий граничащий этап после проверки native compile. К исходному `BGXAI_WEAPON_SLOT_CONSUMER_V3.baf` не добавлено исполнение.

## Одно следующее действие пользователя

Запустить обычный `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`, выбрать **158** и прислать **один JSON** по пути, напечатанному как `REPORT_FILE`. При STOP/INCOMPLETE — тоже прислать этот JSON, не повторять запуск. Перед проверкой лучше закрыть игру и WeiDU, но новых установочных подтверждений вводить не нужно: пункт только читает/компилирует временный файл.

После реальной native-проверки продолжать ТОЛЬКО реализацию достоверного snapshot EEex всех 4 слотов и безопасного переключения без простоя. Не переключаться на AoE/другие задачи. Установка требует отдельного разрешения с SHA, внешней резервной копией и rollback только last-only WeiDU.
