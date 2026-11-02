# BGXAI — дефект provenance сборки и исправление v0.6.21
Дата: 2026-11-02. Ветка: `bg-eet-ai`, основная ветка NWN `main` не затронута.

## Факты, доказанные пользователем
- `BGXAI_UPDATE(1).log`: успешная установка `v0.6.20-liveness-first-pilot` и совпадение `override/BGXGRP.BCS` / `scripts/BGXGRP.BS`, аналогично Халиду. Но эти SHA не доказывают, что бинарник нужной версии.
- Реальные бои: надписи `BGXGRP614 EVADE SHORT` и `TRAPPED: DEFEND`, Халид стоит вдали от противника, Джахейра погибает.
- `BGXAI_RESOURCE_AUDIT(2).txt`, 18:10:06: `WARNING COMPILED VERSION MARKER MISSING BGXGRP`, `WARNING LEGACY MODE DETECTED BGXGRP`, `WARNING COMPILED VERSION MARKER MISSING BGXTANK`. Все копии файлов совпали.
- В `Documents` до аудита файлов BGXGRP/BGXTANK не было; гипотеза о прежней пользовательской shadow-копии опровергнута.
- Вывод: требуемые новые исходники не доказаны в **фактически установленных** BCS/BS. Пара SHA равных файлов может быть парой старых файлов. Не делать новых боевых тестов на таких бинарниках.

## Техническая гипотеза
`BGXAI.TP2` использовал `COMPILE BGXGRP.BAF` и затем `COPY override/BGXGRP.BCS -> scripts/BGXGRP.BS` под одними и теми же именами на каждой переустановке. Старые compiled artifacts могли переиспользоваться или перезаписываться в процессе WeiDU reinstall. Без свежих уникальных имён и проверки версии определить это было невозможно. Механика `COMPILE` документирована: https://weidu.org/WeiDU/README-WeiDU.html

## Исправление v0.6.21
- Код тактики аналогичен v0.6.20, но имеет идентификатор `BGXVER21`, видимые сообщения `BGXGRP621` / `BGXTANK621`.
- Источники компилируются под **новыми resource names** `BGG621.BAF` / `BGT621.BAF`, результат WeiDU: `override/BGG621.BCS` и `override/BGT621.BCS`.
- `BGXAI_VERIFY_ACTIVATE_621.ps1` требует реального `BGXVER21` в каждом новом BCS, отсутствия `BGXMODE`, проверяет SHA256; только после этого переносит содержимое в действующие имена `BGXGRP.BCS`/`BGXGRP.BS`, `BGXTANK.BCS`/`BGXTANK.BS`.
- До WeiDU отдельно сохраняются активные бинарники; при ошибке предпринимается откат файлов. Полный откат метаданных WeiDU **не гарантируется**.
- После активации запускается аудит пользовательских папок и сверка бинарного маркера; лишь затем меняется `bgxai-updater-version.txt` и выводится SUCCESS.
- На повторном запуске `Already current` допускается только если `BGXVER21` присутствует в активных бинарниках.
- **Компиляция и запуск на Windows EET пользователя всё ещё не подтверждены.** Возможны ошибки синтаксиса или несовместимости, которые должны привести к FAIL, а не к фальшивому SUCCESS.

## Единственная следующая проверка
1. Закрыть игру. Запустить прежний `BGXAI_UPDATE.cmd`.
2. Требуемый вывод: `PROVEN NEW COMPILED BGG621`, `PROVEN NEW COMPILED BGT621`, `VERIFIED ACTIVE BGXVER21 BGXGRP`, `VERIFIED ACTIVE BGXVER21 BGXTANK`, `SUCCESS: BGXAI 0.6.21-verified-compile-pilot`.
3. При FAIL прислать последние 30 строк `BGXAI_UPDATE.log` + `SETUP-BGXAI.DEBUG`; **боевой тест не делать**.
4. Если PASS — убедиться, что впервые в игровом журнале появляются `BGXGRP621` / `BGXTANK621`. Только тогда тестировать собственно поведение, без дальнейшей модификации сборщика.
