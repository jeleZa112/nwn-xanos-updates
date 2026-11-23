# BG_EET_RU — контрольная точка V106 (23.11.2026)

**Статус: CODE PASS / CI TEST PASS / RELEASE PUBLISHED / USER-SIDE PREFLIGHT NOT YET RUN / V106 NOT INSTALLED / V106 LIVE UNVERIFIED.**

## Основание и действующие результаты
- V101 русский боевой журнал установлен, краткий/полный режимы показаны в игровом тесте; V102 лишь preflight, не установлен.
- V105 защищённый наблюдатель установлен на пользовательской EET 2.6.6.0 + EEex; реальный результат в консоли: `OBS=true IO=false`; после стрельбы Халида `V105 EVENTS=3 BUFFER=3`.
- В реально наблюдаемом событии поля `attacker, target, weapon, ability, effect` имеют тип userdata, `attackRoll` number, `isCritical/isLeftHand` boolean. Наличие userdata НЕ доказывает RESREF или название стрелы/лука.
- `io.open` недоступен. В соседнем BGXAI канал `Infinity_Log` + перенаправление stdout InfinityLoader проверен отдельным реальным логом; новый канал для BG_EET_RU всё ещё требует собственной живой проверки.
- Не трогать модуль BGXAI, файлы BG Voice RU, сохранения, TLK/EXE, UI.MENU и работающий M_BGERU.lua. При необходимости выбирать журнал BRIEF-only, FULL сохранять исходным.

## Реализация V106
- Единственный обновлятор: `C:\Users\Drevo\Documents\BG_EET_RU\BG_EET_RU_UPDATE.cmd`.
- Основная ветка GitHub: `jeleZa112/nwn-xanos-updates` / `bg-eet-ai`.
- Release manifest: `bg-eet-ru/onefile/release.json`, version 106, code SHA256 **bdc1b738a4181b10afe91a0f35b81d8d7958112e56fb1fb0b29f90f0a75573be**.
- Режим по умолчанию **READ ONLY**. Отчёт `52_V106_WEAPON_CONSOLE_BRIDGE.json` добавляется к существующему единому `SEND_TO_CHATGPT_BG_EET_RU.zip`. Не менять игру по умолчанию.
- После PASS preflight и отдельного введённого пользователем разрешения команда `--install-v106-weapon-console` проверяет SHA V105, целостность Main, отсутствие процесса игры, создаёт внешнюю SHA-подтверждённую резервную копию, и заменяет **только `EEex_scripts/BG_EET_RU_WeaponObserver.lua`**; `EEex_Main.lua` не меняется, используется уже действующая загрузка V105.
- Точная строка разрешения: `INSTALL_BG_EET_RU_V106_CONSOLE_BRIDGE`. Не считать текущее «делаем» таким отдельным подтверждением на пользовательском компьютере.
- Консольная запись `[BG_EET_RU_V106] SOURCE_LOADED`, `START`, `EVENT`; ограничение 64 событий за игровую сессию, только типы и примитивные поля V105, без дереференцирования userdata, без регистрации второго listener и без изменения context/урона.
- Команда `--capture-v106-weapon-console` запускает оригинальный InfinityLoader с перенаправлением stdout/stderr во внешнюю папку `Documents\BG_EET_RU`; после закрытия извлекает ограниченные строки по префиксу V106 в единственный ZIP. Это не вывод уже случившихся событий V105 задним числом: требуется новый тест после разрешённой установки V106.
- Команда `--rollback-v106-weapon-console`: точная фраза `ROLLBACK_BG_EET_RU_V106_CONSOLE_BRIDGE`, восстанавливает тот же SHA-проверенный файл V105 и покрывает прерванную PREPARED-установку.
- Для V105 rollback после установки V106 сначала требуется откат V106; В105 и В106 нельзя откатывать в неправильном порядке.

## Тесты
- Веточная V106 CI: `https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45126046230` PASS.
- Основная ветка native/synthetic + независимая Python SHA256-сверка опубликованного релиза: `https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45126344714` PASS.
- Прежние проверки onefile `https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45126173063` PASS и V105 `https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45126173041` PASS.
- Ни один CI не запускает пользовательскую игру. Геймплей V106 неизвестен до живого теста.
- Не заявлять, что префикс V106 реально захватывается, пока не будет пользовательского лога.

## Следующее действие для пользователя
1. С закрытой игрой запустить **существующий** `BG_EET_RU_UPDATE.cmd` без аргументов; обновление до V106, статус `V106_CONSOLE_BRIDGE_PREFLIGHT_PASS_NOT_INSTALLED`.
2. Предоставить ZIP или полный вывод, чтобы проверить отсутствие HOLD. Никаких новых установок на этом шаге.
3. Только затем с отдельным точным разрешением установить V106 командой `--install-v106-weapon-console`, протестировать новый бой, затем захватить InfinityLoader консоль через `--capture-v106-weapon-console`; не повторять V103/V104 и прежние V105 тесты.
4. Для распознавания по именам оружия/боеприпасов нужен **следующий отдельный этап** безопасного чтения CItem RESREF в момент callback и сопоставление с атакой/снарядом; нынешний V106 только транспортирует уже подтверждённые примитивные поля. Промахи в damage listener не доказаны.

