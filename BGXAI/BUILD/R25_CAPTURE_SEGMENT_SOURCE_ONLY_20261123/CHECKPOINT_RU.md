# BGXAI R25 — verified real-source offline console dedup (23.11.2026)

`CODE=SOURCE ONLY`, `TEST=19/19 Python local` и `REAL_OFFLINE_EVIDENCE=3/3 genuine saved R2/R4/console captures inspected`. Это НЕ новые runtime игры/установки; CI результат фиксировать отдельно после проверки. Публичный пакет не содержит необработанных логов.

Устранено реальное ложное удвоение R2 событий в console: 32 raw `SLOTS` = 16 уникальных последовательностей; 18 зеркальных пар всего (в том числе два SESSION/READY), R4 — 16 `ACTIVE` независимых записей. Отдельные сохранённые R2 и R4 jsonl: 10 и 4 события. Для неизвестных/искажённых зеркал `HOLD`, не молчаливая очистка. Параллельные источники R2 и R4 НЕ объединяются по одному `seq` как нативное событие.

Уточнение: TD15/R13 константа `BGXTD13_UNAUTHENTICATED`, R2/R4 UTC `UNKNOWN` или отсутствует — нет реального engine identity для R24 `sessionToken`; R25 вычисляет только локальный токен захвата. Не менять `BGXAI_UPDATE.cmd`, game/EEex/WeiDU, EPS и live TD15. Auto-switch OFF, deployment R25 NO, LIVE R25 NO.

Правило: после любого безопасного PASS в этом обращении продолжать следующий полезный шаг; не создавать новую версию ради повторного HOLD. Следующий реальный барьер — API/события для native lifetime, alternate APR, эффекты/launcher, ручной/EPS queue; нужны одобрение и guarded live pilot, прежде чем игра сможет автоматически переключать оружие.
