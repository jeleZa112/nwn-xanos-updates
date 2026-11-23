# BGXAI R24 + R25 — работающие SOURCE-ONLY этапы, подтверждённые настоящими данными (23.11.2026)

## Приоритет и правило

Обязательное правило пользователя — **после PASS немедленно следующий безопасный этап в рамках того же обращения**, без ожидания `+`; игра/установки/WeiDU только по отдельному typed разрешению. Это правило сохранено в `BGXAI/CURRENT/BGXAI_AUTO_CONTINUE_RULE_20261122_RU.md` и Library.

В данном обращении после R23 выполнены **R24 (код + реальные существующие Lua модули)**, затем после его PASS **R25 (работающий offline обработчик сохранённых реальных логов)**. Никакой новой версии ранкера, нового CMD/ZIP, дублирующей системы лечения или обновления игры.

## R24: интеграция действующих компонентов без игровых команд

**SOURCE:** `BGXAI/BUILD/R24_SESSION_ADVISORY_SOURCE_ONLY_20261123/BGXAI_R24_SESSION_ADVISORY_BRIDGE_RO.lua`, source code pinned SHA256 `fb04199ba75ae0443e75fd4d103037d25df6fa0a355c9dabab07de26e39a8171` (подтверждён GitHub blob `0822fa1412e76e3ee361928b2c36095c3f2d0a13`).

**Реальная инженерная связка:** использованы ровно оригинальные `V3.preview`, `V4`, `CURRENT_STATS_BRIDGE` / `V5`, `NONINTERRUPT.step`; исходные модули не изменены и в новом BUILD не дублированы. Wrapper держит `sessionToken` отдельно от изменяющегося на каждом кадре `snapshotId`: при новой *синтетической* сессии/персонаже/pipeline предыдущая рекомендация сбрасывается, при обычном новом кадре — может продолжиться. **Не выдавать искусственный sessionToken за достоверный игровой.**

В начале был отвергнут ошибочный вариант: включение `snapshotId` прямо в штатный noninterrupt key ломало уже имевшиеся 22/22 контракта, поскольку snapshotId меняется каждый кадр. Изменение **отменено**; старые файлы восстановлены и побайтно идентичны Git blobs.

**TEST:** 12/12 новых Lua, 22/22 старых Lua NONINTERRUPT, 3/3 старых pipeline Lua, 12/12 Python static/hash checks Windows, 12/12 Python checks Linux. CI https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45191478160 **completed/success**, все три job success. Первоначальная публикация получила нечитаемую текстовую заглушку вместо Lua и CI `45191085138` FAIL; исправлено прямым восстановлением файла, source blob/manifest совпадают; **финальный CI PASS**, ошибку считать закрытой. Real/unverified sources возвращают `KEEP_CURRENT_WEAPON_NO_DISPATCH`. **GAME DEPLOY=NO, LIVE R24=NO.**

## R25: обнаружена и исправлена реальная ошибка счёта наблюдений R2

Сохранённые настоящие пользовательские файлы из Library `/BALDURS_GATE_EET_AI/DIAGNOSTICS/`:
- `BGXAI_WEAPON_SLOTS_RAW_R2_LIVE_20261121.jsonl`: **10** SLOTS, SESSION+READY, 1 offline segment;
- `BGXAI_WEAPON_ACTIVE_RAW_R4_LIVE_20261122.jsonl`: **4** ACTIVE, SESSION+READY, 1 offline segment;
- `BGXAI_WEAPON_CONSOLE_20261122T131454167969Z.log`: **54** tagged R2/R4 raw records; из них **18** побайтно одинаковых соседних LUA→LPRINT пар, включая служебные SESSION/READY. После устранения зеркал **36** записей, в том числе **16 уникальных SLOTS (R2) + 16 ACTIVE (R4)** и четыре служебных SESSION/READY. Данные R2 и R4 НЕ объявлять одним engine action по совпадению `seq`.

**SOURCE:** `BGXAI/BUILD/R25_CAPTURE_SEGMENT_SOURCE_ONLY_20261123/BGXAI_R25_CAPTURE_SEGMENT_RO.py`. Модуль обрабатывает только bounded bytes, строго группирует по маркерам сессии и двум каналам, отклоняет конфликтующие/непарные зеркала, неожиданные seq, несовместимые актёры и неверные права. Не читает runtime, не посылает игровые приказы. Публичный GitHub **не содержит сырых пользовательских журналов**; агрегированная обезличенная информация в `R25_REAL_CAPTURE_SANITIZED_VERDICT.json`.

**TEST:** 19/19 Python локально, 19/19 Windows CI, 19/19 Linux CI и manifest/no-dispatch PASS, https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45193019195, jobs completed/success. **REAL DATA OFFLINE:** 3/3 файла проанализированы успешно. **GAME DEPLOY=NO, LIVE R25=NO.**

## Точная граница: offline session != engine session

R2 `SESSION.utc` в реальном файле = `UNKNOWN`, в пересохранённом R4 JSONL UTC отсутствует, а TD15/R13 `sessionId='BGXTD13_UNAUTHENTICATED'` — не уникальная доказанная сессия. R25 создаёт capture-local deterministic token только для безопасной сегментации логов, **НЕ** удостоверяет игровую session identity, action queue или EPS/manual command origin. Не передавать этот offline token в активное переключение.

## Следующая полезная работа и реальный блокер

**База LIVE:** установленный TD15/R13.2 и предыдущие R1–R4 наблюдения. **R20/menu164 уже выполнен**; не повторять. R21/R22 source investigation нашёл опасный upstream `item:getAbility` pointer path и возможный stride mismatch. Не вызывать на реальном EEex, не регистрировать on-hit hook (может отменить урон).

Пока остаются недоказанными native-lifetime, точная launcher/ammo пара, *эффективный APR невыбранных слотов*, полный список действующих эффектов и источников действий EPS/manual, а также live session identity. **Нельзя разрешать auto weapon switch без них**; `installAuthorized=false`, `dispatchAuthorized=false`. Для нового guarded read-only GAME pilot сначала нужен безопасный адаптер с понятными API и отдельно подтверждённое typed согласие; текущие R24/R25 не кандидаты на установку. Сохранять EPS18.4, лечение, F-охрану, AoE, BG Voice RU, BG_EET_RU, один `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`, сейвы и WeiDU нетронутыми.

## Источники

- R24 source: https://github.com/jeleZa112/nwn-xanos-updates/tree/bg-eet-ai/BGXAI/BUILD/R24_SESSION_ADVISORY_SOURCE_ONLY_20261123
- R25 source: https://github.com/jeleZa112/nwn-xanos-updates/tree/bg-eet-ai/BGXAI/BUILD/R25_CAPTURE_SEGMENT_SOURCE_ONLY_20261123
- R24 CI https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45191478160
- R25 CI https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45193019195
