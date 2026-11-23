# BGXAI R18 — source-only on-demand EEex native candidate (23.11.2026)

**Последнее подтверждённое игровое состояние:** TD15 R13.2 установлен, `M_BGXD13.lua` SHA256 `040a5df62c84363fd0d566c9509636efba7721439afcc90c72758da094e7f5f8`; реально получены 4 `DEFENSE` по 9 сырых полей одной цели. Последний LIVE-файл `BGXAI_R13_2_CONSOLE_20261123T064924087770Z.log` SHA256 `cebfa573df8fc9e5180ec8cbcfc8b67a865a12c6381394d5dcd511cdf7500945`. `R1/R2/R4` и R13 уже проверены — новые бои не повторять. Р17 завершён офлайн: расход стрел (окна 20→19, 20→18, 18→17) и статические R3 способности, 30/30 Windows+Linux CI PASS; связь launcher/ammo не доказана нативно.

**Что делает R18:**

1. Проверена upstream реализация EEex v1.1.7 в репозитории `Bubb13/EEex`: `CItem:getAbility()`, `sprite:getLauncher()`, `EEex_Sprite_GetActiveStats()` и listener callback. Git blob SHA зафиксированы в `R18_UPSTREAM_API_CONTRACT_V1.json`.
2. Созданы **два неустанавливаемых Lua-модуля**: безопасный pure on-demand наблюдатель и кандидант адаптера EEex. Вызовы от реальной игры НЕ подключены. `observe(sprite,action,api)` — кандидат: двойная проверка ID/выбранных слота/способности/launcher и 8 текущих скаляров. Слот 10 (кулаки) не читает CItem; слот 12 (стрелы) при наличии апи предлагает `getLauncher` и слот 35..38; слот 35 (меч) не вызывает launcher. Нет эффекто-сканера, native shared event ID, статусов switch/pass, hook listener, игрового I/O.
3. Тесты локально: **28 Lua probe + 12 Lua adapter + 18 Python статических = 58/58 PASS**. Нативный установленный EEex **не проверен**. Отдельный CI Windows/Linux проверяется после публикации.

**Сдерживающие факторы/опасности:** методы подтверждены только upstream, а не по SHA файлов конкретного EET. У `CItem:getAbility()` есть путь к `pRes.pHeader`; нельзя запускать, не проверив готовность ресурса. 8-скалярный ключ не заменяет полного fingerprint временных эффектов и не доказывает доступность другого оружия. Строго `HOLD`, если нет структуры способности, launcher, стабильности двух чтений. Нет допуска к автопереключению.

**Разделение стадий:** R18 CODE=YES, OFFLINE TEST=PASS, DEPLOY=NO, LIVE=NO, WEAPON_SWITCH=OFF. TD15 не трогать. Пользователю сейчас ничего запускать не нужно. Сохранить в `BGXAI/BUILD/R18_EEEX_NATIVE_LINK_RO_20261123/`, контрольные точки в `BGXAI/CURRENT/` и Library `/BALDURS_GATE_EET_AI/CURRENT/`; обновить `00_AUTO_CONTINUE_READ_FIRST.md` после независимого CI.

**Дальше:** аудит точных установленных EEex API + защита доступа к Item_ability_st, затем source-only конструкция слушателя с подпиской только после отдельного typed approval. Прежде чем включать выбор оружия — доказать актуальность item/ability, launcher+ammo, полную применимость эффектов, альтернативный APR и отсутствие вмешательства в ручные/EPS действия. Повторно не писать существующий ранкер V1/V2/V5 и NONINTERRUPT.
