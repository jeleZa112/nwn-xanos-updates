# BG_EET_RU — контрольная точка V127, 24.11.2026

**Состояние:** V127 выпущен и проверен CI Windows/Linux. **На ПК пользователя не установлен автоматически через GitHub; локальная установка UI-наблюдателя ещё не подтверждена.**

## Реальные входные доказательства
- Единственный реальный пользовательский комплексный прогон V125: `SEND_TO_CHATGPT_BG_EET_RU(20261124-155035).zip`, 132 файла, ZIP CRC PASS, 14/14 этапов запущено, 5 без HOLD, 9 HOLD; `62_V124_ONE_RUN_BOT.json` `updater_version=125`.
- По `48_V102_ROLL_MODIFIER_LABELS.json`: текущий `override/UI.MENU` SHA256 `86ba0c4c36b33a97c4dd57f07ee344df6c2198f46f444f574c798791ad6f7a09`, V102 не установлен. По `56_V112...`: размер UI 597129, единственная в исходнике ссылка на `combatLog[rowNumber]`.
- V108 уже установлен и получает ограниченные события RESREF, но не доказаны hit/miss/launcher, attacker ID, target ID, native per-Hit sequence или строка UI.
- V122 настоящая read-only память: 6 сайтов прочитаны дважды, 8 проверок истинны, но owner/ABI/miss/row join остаются HOLD.
- Строгая source-only модель для Hit → CMessage → видимая строка merged ранее PR #94; **не native runtime hook**.

## Работающий следующий безопасный этап: пассивный UI-наблюдатель
- Код наблюдателя `bg-eet-ru/live-observer/visible_row_guarded_v1.py`. Он опционально пишет **только** `override/UI.MENU` после SHA, external backup и точной фразы пользователя. Не трогает BGXAI, Voice RU, EXE, TLK, сейвы.
- Меняет только одно известное выражение отображения, сохраняя возвращаемый текст без изменений. Ограниченный вывод строк в консоль/опционально TSV. Никаких JIT/EEex native хуков.
- Режим `capture` через InfinityLoader — реальные строки из game stdout **ещё не подтверждены**.
- Сам наблюдатель V126 может собирать только `ui_row_number` и текст, **не** native message pointer; это не готовое описание оружия на промахах.

## Дефект V126, исправленный В V127
Основная ветка до hotfix уже содержала V126 с `read(15001)` для 16178-байтного модуля и `ns={}` без `__name__`. Таким образом пользователю был недоступен этот этап установки даже при точном SHA. Отдельный PR #96 стал конфликтным и закрыт. 

**Исправление:** PR #97 merged, squash commit `d7513ecbef5db17ca8f294e3e5081d4d11470645`, без смены самого модуля. Загрузка теперь `read(20001)`, Python `ns={'__name__':'v126'}`, exact SHA pinned. Реальный интеграционный тест кода/загрузки/кеша/ZIP добавлен в `bg-eet-ru/autofix/test_v126_dispatch_loader.py`; на Windows checkout строковые окончания нормализуются для сравнения **только в тесте**, не в установленном модуле.

**CI:** GitHub Actions run `45438206168`, Windows PASS и Linux PASS, включая V127 full-loader, 14-stage, V122, all source pins, full one-file selftest.

**Единственный релиз:** `bg-eet-ru/onefile/BG_EET_RU_UPDATE.cmd`, `SELF_VERSION=127`, размер `749993` байта, SHA256 `1cbb34cdee3d78011bc91daa3206c8381564a358ae2f44451ee6518c3e7bb012`. `bg-eet-ru/onefile/release.json` версия 127, SHA matches, `game_writes_allowed=false`: автоматической записи в игру нет.

## Один пользовательский путь
1. **Закрыть игру и InfinityLoader.** Запустить прежний `C:\Users\Drevo\Documents\BG_EET_RU\BG_EET_RU_UPDATE.cmd`. При наличии GitHub raw он сам обновится до V127. Если сеть мешает обновлению, одноразовая ручная замена **этого же** файла из `bg-eet-ai/bg-eet-ru/onefile`, без второго CMD.
2. В меню выбрать **2** (установка UI-наблюдателя), затем ввести строго `INSTALL_BG_EET_RU_V126_VISIBLE_ROW_OBSERVER`. Ожидаемый статус `V126_VISIBLE_ROW_OBSERVER_INSTALLED_AWAITING_RUNTIME_UI_TEST` в `63_V126_VISIBLE_ROW_OBSERVER.json`. Если любой SAFE_STOP, **не форсировать**.
3. Закрыть возможные процессы и повторно запустить **тот же CMD**, выбрать **4**. Это запустит InfinityLoader. Загрузить отдельный тестовый сейв, выполнить короткий бой с ударом и промахом, **выйти из игры**, чтобы окончился процесс захвата. Результат в **одном** `C:\Users\Drevo\Documents\BG_EET_RU\SEND_TO_CHATGPT_BG_EET_RU.zip` (entry 63) прислать в чат. Если нет console markers, не считать runtime доказанным.
4. Для отката (только если нужен) закрыть игру, в том же CMD выбрать **3**, точная фраза `ROLLBACK_BG_EET_RU_V126_VISIBLE_ROW_OBSERVER`. Возвращает byte-exact оригинальный UI по внешнему backup.

**Не повторять 14 проверок V125 без причины.** Пункт 1 меню означает исследования (по умолчанию), а не установку.

Следующий *настоящий* native этап — доказанная per-Hit same CMessage/attacker/target/attack seq и 1:1 visible row join, с отдельным typed approval и backup. **CI PASS — не gameplay PASS.**
