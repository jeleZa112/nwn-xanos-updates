# BGXAI 065 — live native class/HP API PASS, source-only gate R1 (2026-11-12)

## Источники

- GitHub `jeleZa112/nwn-xanos-updates`, branch `bg-eet-ai`, `BGXAI/CURRENT/HANDOFF_LATEST_RU.md` и `BGXAI/CURRENT/WORK_LOG_RU.md`.
- Библиотека `/BALDURS_GATE_EET_AI/CURRENT/BGXAI_065_PRIORITY_SOURCE_ONLY_CHECKPOINT_20261112_RU.md` и старые CURRENT/PROJECT_STATE/HANDOFF/LEDGER, DOCS/INDEX/AI_BAF.
- Скриншот игрока EET v2.6.6.0 от 12 ноября 2026, окно EEex Lua/C:DisplayText.

## Новое живое доказательство

- `BGX65 P0 2:14/14`, `BGX65 P1 1:14/14`, `BGX65 P2 5:6/6`, `BGX65 P3 3:8/8`. Это подтверждает для четырёх занятых портретов EEex x64 доступ к `m_typeAI.m_Class`, `m_baseStats.m_hitPoints`, `m_derivedStats.m_nMaxHitPoints`.
- `BGX65 P4 API_ERROR`, `BGX65 P5 API_ERROR`; в партии только четыре портрета, два слота пустые. Нельзя утверждать, что EEex поля не работают. Возможный недочёт старой команды: `if not id` не отсеивает truthy sentinel (-1 / 0xFFFFFFFF); сама конкретная причина не подтверждена до отдельного id/слот-теста.
- Текущая установленная в игре версия **064**, с подтверждённой реакцией одиночного F-охранника после попадания. 065 остаётся **SOURCE ONLY / NOT INSTALLED**. Никакие исходники игры/WeiDU/override, закреплённый `BGXAI_UPDATE.cmd` и активный pinned updater не менялись.

## Продолжение, реально сделанное

- Из сохранённого Library ZIP `BGXAI_065_PRIORITY_SOURCE_ONLY.zip` повторно развёрнуты исходники, проверен байтовый SHA256 baseline Lua 064: `bfee5278b5b69b1fb4a02e3fea321082b0238407789df83ec6bd2f78d7e19f4b`.
- Повторно 42/42 настоящих нативных тестов Lua 5.4 для 065: PASS.
- Добавлена новая отдельная диагностика **R1**, не переписывая закреплённый пакет 065:
  1. `BGXAI65_CLASS_HP_CONSOLE_R1.lua`: уважаем пустые ID (`nil`, отрицательные, `0xFFFFFFFF`), отдельно выводим `OBJECT_MISSING` и реальный `API_ERROR`.
  2. `BGXAI65_POLICY_SNAPSHOT_GATE.lua`: без записи читает `m_id`, `m_pos.x/y`, `getLocalInt('BGX38_GUARD')`, `m_nModalState`, наличие `m_pArea`; их доступность в EET ещё НЕ проверена. Это необходимые поля для `BGX65Policy.partySnapshot` и назначения F-охранников.
  3. `test_065_live_gate.py`: 10/10 тестов Lua 5.4 PASS на симулированных движковых объектах, включая 4 занятых/2 пустых, неверный ID, ошибку полей, mismatch объекта, запрет записи.
- Итого **42 старых PASS + 10 новых PASS**, без игрового инсталлятора и без изменений `BDDEFAI.BCS` / `M_BX43.lua`.

## Следующий практический шаг

Сохранить игровую 064 без переустановки. Чтобы проверить достаточность полей для мультиохранника 065, в *игровой* Lua-консоли выполнить одну строку из `BGXAI65_POLICY_SNAPSHOT_GATE.lua` и показать `BGX65G P0...P5`. **Не PowerShell**. Сама команда только читает, не отдаёт атак/кастов, не устанавливает ИИ. До положительного native результата 065 не активировать.

Затем source-only: надёжный resolver точной вражеской цели до удара, с reject неверных/неподтверждённых целей, отдельные тесты координации нескольких F-защитников. Только затем возможна активная стадия с явным opt-in, проверенным WeiDU-бэкапом и откатом к 064. Сохранять ограничения SCS 35.21, EPS 18.4, EEex 1.1.7, Insane, класс/кит после respec, сюжетную доступность, ограничения магии и запрет отмены ручных приказов.

## Инварианты безопасности

- Текущий `BOOTSTRAP_PIN.json` pinned commit `d66ae072c4a1466521d384c15fe5c0c1ed6205cc`; активный updater blob `ffb7558caf39e8f640dc02386c37c536b4bf6fbf` — не обновлять в этом source-only шаге.
- Политика 065 и observer не активированы, команды/LOCALS не записывают, исходники не копируются в игру.
- Не просить снова WeiDU.log, scripts.zip, EET ZIP или повтор BGX64 AREACHECK/Шанк.
