# BGXAI 2026-11-02 — почему продолжали исполняться сообщения BGXGRP614
Состояние: источник старого скрипта в профиле пока **подозревается, но НЕ подтверждён отчётом пользователя**.

Наблюдения:
- На экране v0.6.20 всё ещё появлялись `BGXGRP614 EVADE SHORT`, Халид не перехватывал волка, Джахейра погибала.
- `BGXAI_UPDATE.log` показал `VERIFY compiled BGXGRP`, `VERIFY compiled BGXTANK`, `SUCCESS: BGXAI 0.6.20-liveness-first-pilot`. Назначения в игровом меню также `BGXGRP` и `BGXTANK`.
- `InfinityLoader` сканирует `C:/Users/Drevo/Documents/Baldur's Gate - Enhanced Edition Trilogy/scripts` **до** папки установки. Источник: https://gibberlings3.github.io/iesdp/appendices/override.htm (сначала home:/scripts, потом install:/scripts).
- Предыдущий updater проверял только `install:/scripts`; это не доказывало, какой сценарий движок берёт при наличии копии в `home:/scripts`.

Изменение:
- Коммит `c1917b3` обновляет `BGXAI/BGXAI_SYNC.ps1`: существующий постоянный CMD запускает диагностику и синхронизацию даже при `Already current`, без WeiDU.
- `BGXAI/BGXAI_RESOURCE_AUDIT.ps1` проверяет SHA256 `override/NAME.BCS` и `scripts/NAME.BS`, затем находит папку `Documents/Baldur's Gate - Enhanced Edition Trilogy` и при наличии сохраняет старые версии `BGXGRP.BS` и `BGXTANK.BS` в `%LOCALAPPDATA%/BGXAI_UPDATER/shadow_backup_TIMESTAMP`, переписывает их текущей компиляцией, проверяет хеш. То же для существующих конфликтующих BGX*.BS/.BCS в других пользовательских override-папках.
- Пишет `BGXAI_RESOURCE_AUDIT.txt` в корне игры. До чтения отчёта не делать вывод, что корень проблемы подтверждён. Если профиля нет или имеются другие переопределения, развивать диагностическое покрытие.
- Никакого боевого ИИ, Lua или WeiDU этот аудит не меняет.

Следующая приемка: прочесть `BGXAI_RESOURCE_AUDIT.txt`, убедиться в `PROFILE FOUND`, `SYNCED`/ `MATCH` и `AUDIT SUCCESS`. После этого перезапустить игру через InfinityLoader, изучить боевой лог и убедиться, что выполняются только BGXGRP620 / BGXTANK620, прежде чем править тактику дальше.


## ФАКТИЧЕСКИЙ РЕЗУЛЬТАТ 18:03:51 (BGXAI_RESOURCE_AUDIT(1).txt)
- `AUDIT SUCCESS profiles=1`.
- `SHADOW NEW user_scripts_BGXGRP_BS` и `SHADOW NEW user_scripts_BGXTANK_BS`: в пользовательском `Documents/.../scripts` перед аудитом этих двух файлов **не было**. Прежняя гипотеза, что там лежала старая перекрывающая копия, **опровергнута**.
- Аудит создал обе пользовательские копии и сверил их хеши с установленными скриптами: BGXGRP `c592ff13f3bc7010`, BGXTANK `7ab68209d9fa8c2a`.
- Это не доказывает, что движок действительно исполняет новый код; ранее экран показывал `BGXGRP614 EVADE SHORT` при успешном WeiDU v0.6.20.
- Коммит `af52fa7`: дополнительный аудит прочитывает бинарный признак `BGXVER20` и ищет конфликты ресурсов в папках `install` и `home` без нового игрового теста; **исполнение в Windows ещё не подтверждено**.
- На время диагностики **не править тактику**, не требовать ещё боёв, сначала установить происхождение старого скрипта.
