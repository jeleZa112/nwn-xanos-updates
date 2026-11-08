# BALDURS_GATE_EET_AI / BGXAI 043 — проверенный мост EEex v1.1.7 (09.11.2026)

## Текущий игровой статус

- У пользователя реально установлена и прошла первый игровой тест **BGXAI 042B** поверх 041 + EPS 18.4. Охрана с включённой автоатакой EPS отреагировала против Шанка, хотя Джейд получила много урона на старте; причиной низкого HP не считать непроверенную задержку ИИ.
- Реальный BCS 042B: SHA256 `8602e8853a9c0e8b1bd5733021e6dd9c9ac73e03beb6c9900ef6ebd09dacb9a0`. WeiDU installation, last-mod status and preinstall rollback backup ранее подтверждены на пользовательском компьютере.
- Не менять установленную игру, 041, 042B, текущий `BGXAI_UPDATE.cmd`, мод NWN/main.

## Сделано в этой сессии — реальный код, не только аудит

1. Изучен **именно тег EEex v1.1.7**, исходный upstream commit `cd016e03d7c62968d8ab917f44eef09bef25593a`. Фактически проверены API `EEex_Action_AddSpriteStartedActionListener`, `EEex_Action_LuaHook_OnAfterSpriteStartedAction(sprite)`, `EEex_Sprite_GetInPortraitID(0..5)`, поля действия `m_actionID`, `m_acteeID.m_Instance`, sprite `m_id`, `m_pos.x/y`.
2. **Написан `M_BGX43Probe.lua`**, пассивный EEex listener. Для action `Attack(3)`/`AttackOneRound(105)` при нападении не-члена партии на члена партии записывает идентификаторы, opcode, позицию, монотонный номер в ограниченный буфер максимум 64 событий. Возвращает read-only `BGX43Probe.snapshot()`; snapshot — копия. Без игрового назначения ролей, внеустановочный исходник.
3. **Написан `eeex_bridge_043.py`**, строго проверяет JSON экспорта из Lua: исключает фальшивые атаки и подмены участника/цели, никогда не объявляет неизвестную видимость, ручное происхождение или очередь достоверными. `execution_allowed=false` и `action_commands=[]` при любых входных событиях.
4. Добавлена **реальная интеграция на уровне кода**: `simulate_policy_offline` связывает событие атаки из формата Lua с прежним `intercept_policy.plan()` при **явно синтетических** данных о здоровье/классе/занятости. Два защитника получают разные advisory намерения; при ручном приказе/касте они не выбираются. Это НЕ live EET execution.
5. **38/38 unittest PASS**, включая Lua 5.4 runtime-имитацию, регистрацию listener, фильтрацию атак, заполняемость ring-64, сброс/копирование, Python валидатор, связку с политикой и запрет игровых команд. Синтаксис Lua проверен настоящим Lua C runtime, но не на EEex LuaJIT.
6. Source-only ZIP `/mnt/data/BGXAI_043_EEEX117_READ_ONLY_BRIDGE_SOURCE_ONLY.zip`, 18 472 байта, SHA256 `bab896e8b6843fe342bd550e10cdc6facdb321b41f329cad1e629d7abbe89dfe`, CRC и архивные source SHA256 пройдены. **Никакого пользовательского BCS/TLK или upstream EEex source в ZIP**.

## Точное ограничение (не скрывать)

- В EEex v1.1.7 listener не сообщает происхождение приказа от пользователя или ИИ. Нельзя безопасно использовать `QueueResponse`/`ClearActions` на основе одного action ID. Не выполнен live EEex тест в самой EET, файл `M_BGX43Probe.lua` ещё не помещён в `override`.
- Текущий 043 — исходный *наблюдающий* мост и модель офлайн. Не боевой патч. Никаких копирований в игру, отмены магии, остановки бардов и переустановки 042B.
- Следующий инженерный шаг: отдельная безопасная **source-only/optionally opt-in read-only** установка EEex-модуля через прежний updater с контролем хешей и штатным откатом; при пользовательском согласии одна короткая проверка callback в EET 1.1.7. Перед выдачей игровых команд необходимо найти надёжный engine/manual-origin gate, иначе сохранять отказ от dispatch.

## Хранение

- Library: `/BALDURS_GATE_EET_AI/BUILD/BGXAI_043_EEEX_BRIDGE/` и `/BALDURS_GATE_EET_AI/CURRENT/BGXAI_043_EEEX_BRIDGE_CHECKPOINT_20261109_RU.md`.
- GitHub `jeleZa112/nwn-xanos-updates`, **только** ветка `bg-eet-ai`, исходный код в `BGXAI/fox_new/experimental_043_eeex_bridge/`, текущий handoff и work log. NWN/main не трогать.

Документация исходной версии:
- https://github.com/Bubb13/EEex/blob/v1.1.7/EEex/copy/EEex_scripts/EEex_Action.lua
- https://github.com/Bubb13/EEex/blob/v1.1.7/EEex/copy/EEex_scripts/EEex_Sprite.lua
- https://eeex-docs.readthedocs.io/en/latest/EEex%20Functions/Action/index.html
