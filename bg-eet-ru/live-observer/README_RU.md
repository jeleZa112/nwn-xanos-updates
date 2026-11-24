# BG_EET_RU — V126: установка пассивного наблюдателя видимых строк

Дата 24 ноября 2026. Статус: **код V126 подготовлен и прошёл CI, но ещё НЕ установлен на компьютере пользователя**.

## Что делает
В единственном `BG_EET_RU_UPDATE.cmd` появилась безопасная ветка для наблюдения за выводимыми строками `combatLog[rowNumber]` в `WORLD_MESSAGES` lefreut UI. Она не меняет текст сообщения, а записывает только его видимый номер и текст в ограниченном console capture. Это *наблюдение рендеринга*, НЕ per-Hit native pointer, НЕ определение оружия при промахе. Эталонная V4 модель thread/frame/CMessage по-прежнему не установлена.

По умолчанию (`Enter`/пункт 1) выполняются прежние 14 диагностических этапов, без записи в игру. Пункты меню:
- `2` — guarded install. Требует закрыть Baldur.exe/InfinityLoader.exe, точный SHA256 `override/UI.MENU`, внешнюю backup, проверку обеих SHA и дословный ввод `INSTALL_BG_EET_RU_V126_VISIBLE_ROW_OBSERVER`.
- `3` — exact rollback `UI.MENU` после закрытия игры и ввода `ROLLBACK_BG_EET_RU_V126_VISIBLE_ROW_OBSERVER`.
- `4` — захват. Требует сначала установленный V126 и закрытую игру, запускает её через `InfinityLoader.exe`, перенаправляет консоль в отдельный лог под `Documents\BG_EET_RU`. После выхода из игры лог добавляется в **тот же ZIP** как JSON `63_V126_VISIBLE_ROW_OBSERVER.json`.
- `5` — просмотр статуса/собранных строк, без изменения игры.

## Технические правила
- Только `C:\Games\BG_EET_FOXX_NEW\override\UI.MENU`. Предварительная проверка SHA256 `86ba0c4c36b33a97c4dd57f07ee344df6c2198f46f444f574c798791ad6f7a09` из реального V125 ZIP. Другой SHA — **SAFE STOP без изменений**.
- В исходном UI разрешается ровно один предсказуемый `text lua "...combatLog[rowNumber]..."` renderer, и ровно одна `function clean(str)` в Lua. Любое расхождение — **SAFE STOP**.
- Старая копия в `Documents\BG_EET_RU\SAFE_BACKUPS\UI_MENU_V126_*.bak`, состояние `BG_EET_RU_V126_ROW_OBSERVER_STATE.json`, ZIP `SEND_TO_CHATGPT_BG_EET_RU.zip`. Перед и после замены — точные SHA.
- Текст рендеринга возвращается без изменения. До 160 уникальных строк на игровую сессию; дедупликация по номеру и содержимому. Никакого native hook, патча EXE, TLK, сейвов, BGXAI, BG Voice RU.
- Обнаружено по IESDP: стандартная UI Lua Beamdog по умолчанию **не загружает файловую библиотеку `io`**. Поэтому основной сбор идет через `print('BG_EET_RU_V126_ROW...')` и запуск игры с console redirect. `io.open` лишь необязательный fallback. Направление этих строк в stdout InfinityLoader **в реальной пользовательской сборке ещё не проверено**.
- Наличие `ui_row_number` НЕ доказывает уникальность `CMessage` и идентификатор атаки. `miss_weapon_verified=false`, `combat_row_join_verified=false`; не добавлять названия оружия в журнал по догадке.

## Релиз
`bg-eet-ru/onefile/release.json` — V126, один CMD `749993` bytes, SHA256 `971a96175c5746d652a9b1df36771dae156c4cd7d3e985d028bc05eb631326c6`.
Пассивный модуль: pinned commit `601785e3a0e838ec3bc50e19ce26377153507932`, SHA256 `3c079918170ecbea959e1148e1fc9c629d84c751bf0d89415166c98a26921703`.
Ветка пользователя `bg-eet-ai` после merge. CI Ubuntu/Windows (16+ synthetic scenarios) + реальный Lua 5.4 test без `io`, полная самопроверка CMD.
Game state на пользовательском ПК **не менялся** этим GitHub-релизом.

## Следующее
После одного разрешённого запуска пользователя пунктов 2 и 4 принять **один** ZIP с `63_V126_VISIBLE_ROW_OBSERVER.json`; определить, появились ли консольные строки. Если `NO_UI_ROW_CAPTURE_YET`, не менять game files вслепую. Следующая настоящая задача — безопасный native per-Hit message pointer/attacker/target/attack sequence для строгого UI join, с отдельной проверкой ABI и новым explicit approval. V108 оставить нетронутым.
