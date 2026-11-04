# BGXAI 04.11.2026 — 0.1.3 ONE EXISTING UPDATE.CMD — CHECKPOINT

**Зафиксировано:** с этого момента пользователь запускает **только `BGXAI_UPDATE.cmd`**, который уже находится в корне EET возле `chitin.key`. **НЕ предлагать новые пользовательские CMD и ZIP**. Не просить заменять исходный CMD. Старые `BGXUNI_SETUP.cmd`, `BGXUNI_RUN_012.cmd` и их ссылки считать устаревшими; их удаление необязательно.

## Реально опубликованные изменения

- `BGXAI_UPDATE.cmd`: НЕ ИЗМЕНЁН; старый один-файловый bootstrap GitHub, blob SHA `faeffbba72ef2a64b631ef557c06037d6b145a9d`.
- `BGXAI/BGXAI_SYNC.ps1`: удалённо обновлён в **`bg-eet-ai`**, GitHub commit `342ad6602c3a93ef09f690664f612db2157cda95`, source blob `b3f8a1b2f339f22bce5c58b4d84ada2bd795c726`. Появился выбор: `1` или Enter = отдельный BGXUN1; `2` = прежний 0.6.x updater; `3` = выход. **Сравнено с оригинальным blob `a02080cab3b59a384c66b8edb56c54f68f94cb4f`: удаление нового selector-фрагмента даёт точное совпадение всего старого текста.**
- Новый remote-only helper `BGXAI/pilots/BGXUNI_010/parallel/BGXUNI_AUTOINSTALL.ps1`: SHA256 `a8fa668786e95f8b108ae6efa95a3300ee521ad278e8b87e6d1c74bc310101e2`, blob SHA `b64663bf27b66d43113488279cbd622776e5e221`.
- Манифест `BGXAI/pilots/BGXUNI_010/parallel/latest.json` с exact SHA256 helper+BAF+TP2, blob SHA `8e2e72dadf80b432c396741033465681521a3c2c`.
- `BGXUNI/BGXUN1.BAF` blob SHA `84fc92fa3d9357cd7ebe41e9b3f42f5392fce913`, `BGXUNI/setup-BGXUNI.tp2` blob SHA `055b1f0f8ef99d7538b10f7513ed3711f366ac73`. Сверка всех четырёх исходных файлов GitHub с локальными git blob SHA — **PASS**. Исправлены пропущенные в GitHub завершающие LF, чтобы манифест не давал ложный SHA256 mismatch.
- README, тесты и исходный PowerShell selector сохранены в `BGXAI/pilots/BGXUNI_010/parallel/` и Library `/BALDURS_GATE_EET_AI/BUILD/BGXUNI_013_ONE_FILE_UPDATER/`.

## Безопасность и тесты

- **34/34** офлайн теста BAF, включая **2000 seeded random scenes**, **7/7** предыдущих тестов установщика, **15/15** новых тестов single-updater — PASS. Они не заменяют проверку настоящего Windows PowerShell / WeiDU 251 / EET runtime.
- Новый путь компилирует только `BGXUN1.BAF` в независимый `scripts/BGXUN1.BS`, на основании отдельно верифицированных BAF/TP2; не изменяет `BDDEFAI`, `BGXGRP`, `BGXTANK`, `BGXAI/latest.json` v0.6.27, LIVE 0.4.4 или NWN/main. Контроль закрытия игры/InfinityLoader, проверка SHA256, защита от конфликтующих ресурсов, файловые бэкапы. **WeiDU metadata/TLK rollback пока не доказан**.
- Список 19 опций ещё НЕ интегрирован в игровое EEex меню. Сейчас 11 BAF блоков в унифицированном пилоте. Класс/кит не привязан к имени персонажа.

## Следующий тест пользователем

1. Сохранить игру и полностью закрыть Baldur's Gate + InfinityLoader.
2. Запустить **старый `BGXAI_UPDATE.cmd`** из корня игры, НЕ BGXUNI_SETUP и НЕ BGXUNI_RUN_012.
3. Появится `BGXAI ONE UPDATE FILE - EET / WeiDU 251`. **Нажать Enter/1**, не выбирать 2 (оно обновляет старые роли!).
4. Дождаться строки **`[BGXUNI] SUCCESS BGXUNI 0.1.3:`** и `scripts\BGXUN1.BS`, отправить только последний экран/конец `BGXUNI_UPDATE.log` если FAIL. Не требовать старые 3 архивы, WeiDU.log или scripts.zip.
5. После этого создать отдельный игровой сейв и назначить BGXUN1 одному NPC. Ожидаемый стартовый маркер `BGXUN1 V010 READY`.

**Не утверждать**, что Windows установка уже пройдена: это следующий этап. У пользователя уже была путаница, когда несколько раз запускался старый CMD с неподдерживаемым `--tp2`; с новой схемой ни `--tp2`, ни ручная замена CMD не нужны.