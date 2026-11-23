# R24 checkpoint 23.11.2026 — офлайн интеграция R24 (SOURCE ONLY)

- Исправлена неудачная гипотеза: `frame.snapshotId` изменяется каждый кадр, нельзя добавлять его в существующий NONINTERRUPT signature. Экспериментальный патч отвергнут, старые 22/22 тестов возвращены PASS. **Существующий файл НЕ меняли.**
- В новом offline-bridge есть собственное разделение `sessionToken`, actor, pipeline; при изменении сессии нет переноса pending плана. Однако реальный источник `sessionToken` **пока не подтвержден**.
- Использованы старые V3.preview, V4, current stats bridge / V5, NONINTERRUPT; никакой новый ranker не написан. Полный алгоритм проверен на синтетических сценах и защищён от изменения action/queues. С real/unverified inputs fail-closed.
- Код/тесты: `BGXAI/BUILD/R24_SESSION_ADVISORY_SOURCE_ONLY_20261123/`; независимую CI учитывать только после её фактического результата.
- `CODE=SOURCE READY`, `TEST=local Lua 12/12 + old Lua 22/22 + old integration 3/3; Python 12/12`, `DEPLOY=NO`, `LIVE R24=NO`. Указанные числа — **не игровые бои**.
- Последний LIVE: TD15/R13.2. R20 read-only menu 164 завершён; повтор не нужен. Р21, Р22 source-only passes. Weapon switch OFF. Для подключения реального EET требуются безопасная native-ability/lifetime, alt APR, launcher-ammo pair, full effects, manual/EPS origin, session provenance и отдельное typed согласие на game-modification.
- Главная политика: после положительной безопасной проверки автоматически переходить к следующему полезному шагу в **текущем обращении**; не создавать второй CMD или подменять игровой runtime.
