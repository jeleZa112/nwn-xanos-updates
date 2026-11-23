# BG_EET_RU V114 — дополнение: кандидаты на этап записи журнала

Исследование 23.11.2026; **SOURCE ONLY**, игра и обновлятор V112 не изменены.

В репозитории Bubb13/EEex у `InfinityLoader.db` обнаружен символ `CMessageHandler::AddMessage` (x64, шаблон `4889742410574883EC20488B02`). В `EEex_Sprite.lua` реализована `EEex_Sprite_DisplayTextRef(sprite, text, optionalArgs)`: создаётся `CMessageDisplayTextRef`, задаются `m_sourceId`, `m_targetId`, `m_name`, `m_text`, затем вызывается `EngineGlobals.g_pBaldurChitin.m_cMessageHandler:AddMessage(message, false)`.

**Что подтверждено:** EEex может создавать и ставить в очередь текстовые сообщения движка через `CMessageHandler::AddMessage` с ID источника/цели. Это рабочий путь публикации *своего* текста, но НЕ означает, что каждый встроенный бросок атаки проходит через него, что сообщение попадает в `combatLog[rowNumber]` или что сообщение имеет идентификатор конкретного броска. В опубликованных в исследованных источниках `EEex_Menu.lua`/`EEex_Action.lua` не найден готовый высокоуровневый listener `AddMessage`/per-roll `journal_row_id`.

**Что ещё не доказано (обязательные отдельные ворота):**

1. Путь фактического сообщения об атаке, сформированного внутри `CGameSprite::Hit()`, до добавления **именно** записи боевого журнала, а не только текстового сообщения.
2. Надёжный, неизменный `roll_instance_id`, который можно передать из `Hit()` в событие создания строки, не переписывая механику броска и не угадывая по времени/имени.
3. Подтверждение x64-совместимости текущего установленного EEex и структуры сообщения; точные SHA, read-only proof, отдельное разрешение на опыт и откат до любых возможных изменений.

**Не делать:** считать `m_sourceId`/`m_targetId` ключом конкретного броска, добавлять собственные сообщения с придуманными подписями, переписывать результат атаки, использовать `CMessageHandler::AddMessage` хук по одному шаблону из исходников. При 2 APR или снарядах в полёте подпись оружия по actor/target будет ложной.

Источники:
- https://github.com/Bubb13/EEex/blob/a6d21abe44e20509f5d0259ccc6c7e7f9d12b285/EEex/copy/EEex_scripts/EEex_Sprite.lua
- https://github.com/Bubb13/EEex/blob/a6d21abe44e20509f5d0259ccc6c7e7f9d12b285/EEex/loader/InfinityLoader.db
- https://github.com/Bubb13/EEex/pull/136

Этот документ дополняет `BG_EET_RU_V114_X64_ROLL_FEASIBILITY_20261123.md` и уточняет следующий исследовательский участок. Новая версия Windows updater для него **не нужна**.