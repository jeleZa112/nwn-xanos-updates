# BGXAI — контрольная точка 14.11.2026: реальное чтение книги заклинаний EEex 1.1.7, SOURCE ONLY

**Последняя реально установленная версия игры остаётся BGXAI 066S**, EPS 18.4. Lua `override/M_BX43.lua` SHA256 `50640902ec4c25a2c85e5088d7231678b54445a847b41743c476974236d1d70f`; BCS `override/BDDEFAI.BCS` SHA256 `fb435d82e6c3e0ebea1d6a9532753921bd5411d70ac0677dc1fd8ec483380476`. Текущая работа НЕ меняла игру, WeiDU, EPS, update, BCS или Lua на Windows. Не просить вводить PowerShell, не устанавливать исходный ZIP.

## Реализованное изменение

Продолжен **тот же** source-only кандидат после коррекции коллизий охраны и лечения: `M_BX43_066S_CAPABILITY_CANDIDATE.lua` (prior). Добавлен в него ограниченный read-only модуль `BGX66_EEEX117_SPELLBOOK_EVIDENCE.lua` и передача доказательства из книги третьим аргументом уже имевшегося `S.capabilityVerifier`. Никакой новый боевой исполнитель, новый action listener, BCS receiver, `ClearActions` или замена EPS не создавались. Новый кандидат `M_BX43_066S_EEEX_BOOK_EVIDENCE_CANDIDATE.lua` SHA256 `cd5075482f451e9edc2237317b2939001428cbe265b25b113acd0f8369e2a4cc`; сам модуль SHA256 `df470dd06060b8f77338f66c732864ce1a6d73e6467a399c63f7e76f6d2f7659`.

Новый считыватель обращается только к документированным EEex v1.1.7 `sprite.m_memorizedSpellsPriest` / `sprite.m_memorizedSpellsMage`, `:getReference(0)`, `EEex_Utility_IterateCPtrList` и полям `entry.m_spellId:get()` / `entry.m_flags`. Для первого круга используется авторитетный **пользовательский** EET-каталог `/BALDURS_GATE_EET_AI/INDEX/SPELL_POLICY_CATALOG_469.csv`: `CLERIC_CURE_LIGHT_WOUNDS` (IDS 1103, `SPPR103`) и `WIZARD_SHIELD` (IDS 2114, `SPWI114`). Лишние/израсходованные записи не считаются, нарушения структуры — `nil` / fail-closed. Считыватель выводит число свободных подготовленных экземпляров, **не** пригодность применить прямо сейчас, **не** состояние EPS/очереди/ручного приказа, **не** активность старого класса дуала. Спонтанные заклинания шамана/чародея не считаются доказанно отсутствующими только по обычной книге.

В модуле S по умолчанию `S.capabilityVerifier=nil`, `S.requireMemorizedEvidence=false`; в модуле T `T.capabilityVerifier=nil`, `T.capabilitySourceVerified=false`. Внешний доверенный верификатор может использовать третий аргумент, но должен сам доказать кастабельность/команды. Новая опция строгой проверки лишь **запрещает** запрос при пустой/нечитаемой книге и сама НЕ авторизует никакое действие. Применять её к шаманам и чародеям без отдельной спонтанной модели запрещено.

## Сохранение поведения и доказательства

- Истинный оригинал 066S: **18/18** тестов на native Lua 5.4 mocks.
- Новый кандидат: **74/74** (17 исторических, 22 охраны, 9 прошлой магии, 4 пересекающихся BCS-запросов, 22 новых проверок чтения EEex), PASS.
- Ранее объединённый кандидат: **18/18 + 17/17 + 36/36**, PASS без изменений.
- `texlua parse.lua`: PASS.
- Новый release verifier: **33/33 SHA256** всех файлов, точное сравнение единственной вставки со старым кандидатом и контроль отсутствия новых действий, PASS.
- Чистая распаковка финального ZIP в временную папку: повторно PASS обоих test runners, verifier и syntax.
- **Всё это офлайн тесты** с mock-структурами, не работа подключённого EEex в настоящем EET. Не утверждать, что бот теперь изменил боевое поведение.

Архив `BGXAI_066S_EEEX117_SPELLBOOK_EVIDENCE_SOURCE_ONLY.zip`, SHA256 `94bbfea9d7f787c8999d516efae3c345badad3de2cffbc3a448a9766a62b9232` (128733 байт, 34 файла). Полное сохранение Library `/BALDURS_GATE_EET_AI/BUILD/BGXAI_066S_EEEX117_SPELLBOOK_EVIDENCE_SOURCE_ONLY/` и текущая записка `/BALDURS_GATE_EET_AI/CURRENT/BGXAI_EEEX117_SPELLBOOK_READONLY_CHECKPOINT_20261114_RU.md`.

## Ссылки на исходные API

- Bubb13/EEex tag v1.1.7, `EEex/copy/EEex_scripts/EEex_Utility.lua` Git blob `f10ed5e25ff0c03bc63507d04263f96daae60e7b` — iterator.
- Bubb13/EEex tag v1.1.7 `EEex/copy/EEex_scripts/EEex_Trigger.lua` Git blob `80da96ed5dc7cbcaa726631a3542ecafa533ec6f` — evaluator использует `m_pendingTriggers`; НЕ используется здесь.
- Gibberlings3/Tweaks-Anthology `cdtweaks/luke/lua/class/spontaneous_casting.lua`, Git blob `74ad408872f9e45a9d27e0b578134e1bed80d2b9` — аналогичные поля книги и flag bit0; их запись не переносилась.

## Нерешённые барьеры

EEex 1.1.7 started-action callback передаёт sprite и начатое действие, но не удостоверяет источник ручного приказа и не доказывает пустую очередь EPS; нельзя включать боевые запросы на основе него. Для работающего нового ИИ необходим отдельный строго проверенный источник: текущее состояние / отмена приказов / class-kit-dual active / identity цели BCS / безопасная конкуренция с EPS. Остаются запреты на включение `T.capabilitySourceVerified`, на удаление `ActionListEmpty()` и на любые действия, разрушающие работающий EPS 18.4. Никакой новой диагностики с номером или установки в игру не требуется от пользователя прямо сейчас.
