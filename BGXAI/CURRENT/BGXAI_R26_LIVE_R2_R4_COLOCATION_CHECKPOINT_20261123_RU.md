# BGXAI R26 — реальная сверка R2/R4 по одному журналу, 23.11.2026

**Текущее состояние:** `CODE=SOURCE_ONLY_PASS`, `TEST=28/28 локально, Windows 28/28 PASS, Ubuntu 28/28 PASS`, `OFFLINE_REAL_DATA=16/16 co-located source candidates`, `GAME_DEPLOY=NO`, `R26_LIVE=NO`.

## Что реально выполнено

1. Готов Python `BGXAI/BUILD/R26_R2_R4_COLOCATION_RO_20261123/BGXAI_R26_COLOCATED_R2_R4_RO.py`, который **переиспользует R25.inspect**, не копирует старый парсер, не читает файлы самостоятельно и не выдаёт игровые команды. 28/28 синтетических положительных и отрицательных тестов, включая фальсификацию авторизации, перестановку R2/R4, смену цели/слота, неверный raw APR, несколько сессий и испорченные дубли.
2. На сохранённом реальном **общем консольном логе 22.11.2026** (сырые персональные данные НЕ публиковались) найдено **16/16** соседних первичных R2 SLOTS→R4 ACTIVE; совпадает `seq`, `actor`, `partyIndex`, `actionRaw`, `selectedWeaponRaw`, `selectedAbilityRaw`. R25 подтвердил и убрал 18 зеркальных LUA/LPRINT записей перед сверкой.
3. По **текущему выбранному** оружию (не альтернативному): slot38 посох raw APR 1 — 10 наблюдений, slot12 стрелы raw APR 2 — 5, slot35 меч raw APR 7 (1.5) — 1. Action ID 23 — 12; action ID 3 — 4. **Это 16 пар наблюдений начатых действий, НЕ 16 попаданий, и не engine-verified projectile/launcher pair.**
4. CI: Windows 28/28 + Ubuntu 28/28 + исходные SHA/pinned R25/passive source policy **PASS**: https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45198432734 (оба job завершены success). Первый CI run https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45198212665 FAIL на **Windows Git autocrlf преобразовании строк**, не на логике; workflow исправлен отключением autocrlf перед checkout, повтор PASS. Не повторять работающие проверки.

## Дополнительная source-проверка после CI PASS

На официальном EEex v1.1.7 `EEex_Action.lua` Git blob `e7543274ed066b5abe3c58262105212f208d1595` подтверждено: `EEex_Action_AddSpriteStartedActionListener(func)` добавляет слушателей в общий список, а `EEex_Action_LuaHook_OnAfterSpriteStartedAction` вызывает каждого последовательно с `(sprite, action)`. Сохранённые исходники R2 `M_BGXW2.lua` (Git blob `6d7d169d4c354726b61a522706d5177370b08a73`) и R4 `M_BGXW4.lua` (Git blob `45cde4c415555efbf9844f8cda590775df942234`) регистрируют именно этот listener; их `on_started` копирует скалярные поля для read-only логирования. Это существенно усиливает трактовку соседства в общем журнале, но до общего нативного события с доказанной non-reentrant identity **всё ещё кандидат, не удостоверение**.

Найдена также **важная версия EEex**: `B3AttackInfo.lua` отсутствует в дереве официального EEex **v1.1.7**, имеется в **v1.3.1**. В v1.3.1 этот модуль обращается к `m_selectedWeapon` и `m_selectedWeaponAbility`, то есть **к текущему выбранному оружию**, а не безопасно рассчитывает полные эффективные параметры **альтернативных** слотов. Не переносить API новой версии в установленную сборку.

Официальный `EEex_Sprite_GetActiveStats()` в v1.1.7 берёт активный derived stats (избегая промежуточной стадии перерасчёта эффектов), но не пересчитывает другой слот. `EEex_Resource_Demand()` возвращает native resource pointer; документация пока не доказывает требуемый Demand/Release ownership lifecycle, а `item:getAbility()` использует подозрительный stride. **Не использовать без отдельного ABI/lifetime proof**.

## Куда сохранять и что делать дальше

Source+tests+README+sanitized machine verdict: `BGXAI/BUILD/R26_R2_R4_COLOCATION_RO_20261123/` в GitHub `jeleZa112/nwn-xanos-updates` branch `bg-eet-ai` и Library `/BALDURS_GATE_EET_AI/BUILD/R26_R2_R4_COLOCATION_RO_20261123/`. Главный read-first: `BGXAI/CURRENT/00_AUTO_CONTINUE_READ_FIRST.md`.

**Реальный следующий блокер:** нет достоверного runtime API для APR всех **невыбранных** слотов, полных эффектов, связки launcher/ammo, ручной/EPS queue provenance и нативной привязки событий; исправления требуют отдельной безопасной диагностической разработки и согласованного **typed live read-only pilot** через прежний `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`. Нельзя автоматически устанавливать и тем более включать switching. Исходные EPS 18.4, TD15/R13.2, BG_EET_RU, BG Voice RU, сейвы, WeiDU неизменны.

**ПОСТОЯННОЕ ПРАВИЛО:** при успешном безопасном результате сразу продолжать следующий полезный этап в *этом* обращении, без `+`; не обещать фоновой работы. Не делать новую версию только ради ещё одного HOLD-отчёта.