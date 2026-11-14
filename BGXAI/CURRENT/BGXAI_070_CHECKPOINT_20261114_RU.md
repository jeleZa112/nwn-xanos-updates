# BGXAI 070 — ПАССИВНЫЙ СНИМОК ПОЛЕЙ EEex / SOURCE ONLY

**14.11.2026.** У пользователя в EET Foxx (05.11.2026), SCS 35.21 + EEex 1.1.7 + EPS 18.4, Insane последней подтверждённо установлена **BGXAI 066S**. Ветка **067 ON HOLD**, версии 068/069/070 **SOURCE ONLY**, ни одна не установлена в игру. Правило: **EPS-first**, клавиша **F** — собственная охрана BGXAI, не штатный переключатель EPS.

## Реализовано 070

1. Получено подтверждение имён полей движка из документации EEex: `m_typeAI.m_Class`, `m_baseStats.m_hitPoints`, `m_derivedStats.m_nMaxHitPoints`, `m_derivedStats.m_nKit`, `m_derivedStats.m_nLevel1/2/3`, `m_derivedStats.m_bPolymorphed`. Они лишь **источники сырых числовых наблюдений**. Старый код 066S использовал `m_nModalState`, `BGX38_GUARD`. Пользовательская сборка EEex **не была проверена во время этой работы**.
2. Создан `BGXAI070_EEEX_FACTS_READONLY.lua` с `snapshot(sprite)`, `facts_for_069(snapshot)`, `inspect(sprite, role_069)`; читает именованные поля безопасно через `pcall`, все семантически непроверенные состояния маркирует `UNKNOWN`/`verified=false`.
3. `m_nKit` **не** конвертируется в название/подтверждённую способность до точной сверки с пользовательскими `KIT.IDS` и `KITLIST.2DA`. `m_bPolymorphed` **не** доказывает оборотня, три уровня **не** доказывают восстановления предыдущего класса дуала. `m_nModalState=0` **не** доказывает свободную очередь EPS и отсутствие ручного приказа.
4. Совместно с **неизменённым** `BGXAI069_ROLE_OBSERVER.lua` (SHA256 `4e65f1bb9ddbc3501d593199442decf5fed2525fb2373b3ed7f7ad0dff068efd`) не выдаёт `possible_interceptor=true`, поскольку нет доказанных `actions`/`combat` и особых классовых состояний. Отсутствие фактов о дуале передаётся как `nil`, а не ложное утверждение, что персонаж прошёл дуал.
5. Нативный Lua (`texlua test_070.lua`): **230/230 assertions PASS** (mock EEex, НЕ игра). `python verify_070.py`: проверка SHA256 пяти исходных файлов + статическая проверка отсутствия вызовов боевых команд, регистрации listeners и записи LOCALS — **PASS**. Python syntax compile PASS. Эти проверки **не** доказывают совместимость с действующим EEex, Win WeiDU или отсутствие всех классов возможных ошибок.
6. Создан воспроизводимый ZIP `BGXAI_070_READONLY_EEEX_FACTS_SOURCE_ONLY.zip`, SHA256 `483a6cfe9f6a6d17893aaff5c0c4f49a977c6d8bf0b647d02f2d5fde6a43b55b`, размер 11419 байт. Внутри 069 копия, 070 Lua, test_070.lua, verify_070.py, README_RU.md, JSON manifest.

## Чего не делали

- Не меняли игру, `BGXAI_UPDATE.cmd`, pin загрузчика, `WeiDU.log`, `override/BDDEFAI.BCS` или `override/M_BX43.lua`.
- Не регистрировали EEex hooks, не устанавливали 067/070, не отправляли боевые приказы или заклинания.
- Не проводили игровую диагностику на ПК пользователя и не выдавали офлайн-модель за реальную работу в EET.
- Не трогали другие проекты, включая BG Voice RU.

## Канонические ссылки

- GitHub, branch `bg-eet-ai`: `BGXAI/fox_new/experimental_070_readonly_eeex_facts_source_only/`.
- GitHub отчёт: `BGXAI/CURRENT/BGXAI_070_CHECKPOINT_20261114_RU.md`.
- Library: `/BALDURS_GATE_EET_AI/BUILD/BGXAI_070_READONLY_EEEX_FACTS_SOURCE_ONLY/` и `/BALDURS_GATE_EET_AI/CURRENT/BGXAI_070_CHECKPOINT_20261114_RU.md`.
- EEex named-struct fields: https://eeex-docs.readthedocs.io/en/latest/EE%20Game%20Structures%20%28x64%29/CD/ ; EEex author's explanation: https://forums.beamdog.com/discussion/71798/mod-eeex-v1-3-0/p41 .

## Следующая безопасная задача: 071

Использовать уже сохранённые EET ресурсы для **read-only** сверки `KIT.IDS`, `KITLIST.2DA`, особенностей SCS пересборки, и диагностировать дуал/форму с проверяемым значением `verified=true` только после реального источника доказательств. Отдельно проверить приоритеты EPS. Не просить пользователя повторять архивы, не предлагать установку 067, 069 или 070. До успешного арбитража EPS все новые модули **пассивны**.
