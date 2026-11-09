# BGXAI 044 — диагностический хоткей для EEex; выпуск source-only / opt-in (09.11.2026)

## Контекст, подтверждённый живыми скриншотами

EET 2.6.6.0 + SCS 35.21 + EPS 18.4 + EEex 1.1.7 + InfinityLoader, Insane. Рабочая BGXAI 042B с хешем `8602e8853a9c0e8b1bd5733021e6dd9c9ac73e03beb6c9900ef6ebd09dacb9a0` и отдельный пассивный наблюдатель 043P установлены на Windows. Пункт 21 подтвердил хеш исходника 043-P `f1e6fcc6989512bee5e217a66ef42ea48a828c407c7009e6012a90b95d5db19f` и наличие verified rollback backup. На скриншотах Шанк произносит `атакует цель: Jade`; Джейд получила 1 колющего урона. Одноразовая надпись 043P не появилась. Это НЕ доказывает проблему загрузки Lua или неправильный callback, поскольку неизвестны внутренние action ID и доступность UI-печати. Ctrl+Space у пользователя открывает только паузу, не Lua-консоль.

## Что создано

Новая версия `0.3.15-044-DIAG`: отдельный read-only Lua `BGX44/M_BGX44Diag.lua` для **Ctrl+Alt+F11**. Возвращает строку `BGX44: 043P loaded=... listener=... enabled=... attacks=... errors=... notice=... API=... last=...`. Это состояние в памяти, НЕ запись в боевой журнал. Два состояния отдельны: 043P собирает события атаки и не отдаёт команды; 044 читает глобальную переменную 043P и регистрирует только обработчик клавиатуры без потребления клавиши. Если 044 сам не загрузился или UI DisplayString недоступен, отсутствие строки остаётся неоднозначным — нужен отдельный разбор; сам по себе это не провал 043P.

Независимая установка `BGXAI44_INSTALL.py` + `BGX44/setup-BGX44.tp2` размещает через WeiDU только `override/M_BGX44Diag.lua`. Пакет требует точного SHA256 исходного BCS 042B и Lua 043P, проверяет наличие 043P последним в WeiDU.log, наличие EEex boot/InfinityLoader/WeiDU, конфликт имён, отсутствие процессов игры/WeiDU перед записью, точные SHA256 исходников. Перед установкой создаёт и проверяет внешний backup в `%USERPROFILE%\Documents\BGXAI44_SAFE_BACKUPS`; после запуска сверяет WeiDU status, хеш Lua и неизменность BCS/chitin/043P/EEex. При недопустимом состоянии BLOCKED или REVIEW не продолжает. Откат — отдельный WeiDU `--force-uninstall`, только если 044 последний и есть проверенный backup; rollback проверяет восстановление последним 043P и неизменность BCS/043P. `BDDEFAI.BCS`, 043P, SCS/EPS, UI.MENU, TLK не изменяются скриптом установки 044.

## Проверки

- **17/17 PASS** в офлайн unittest: 11 тестов установщика/манифеста/запрета вмешательства/фиктивного WeiDU и 6 тестов Lua 5.4 C runtime, включая Ctrl+Alt+F11, неверные модификаторы, ноль событий, буфер 2 событий, отсутствие дисплея и непоглощение клавиатуры.
- Python compileall/py_compile успешен; ZIP CRC PASS.
- Архив `BGXAI_044_DIAG_SAFE_SOURCE_ONLY.zip` — **13 299 байт**, SHA256 `d1f4e66b9893f6f8011c5ebb7ad5f590e36f1294a0941913f7f7599271bd01dc`.
- Все **7/7** опубликованных источников `BGXAI/fox_new/release_044/` сравнены побайтово по длине и SHA256 с `manifest.json`: PASS. Отдельный `manifest.json` также есть в ветке GitHub.
- Изменён только GitHub `bg-eet-ai`, не NWN/main. Старые пункты обновлятора **1–22** сохранены, добавлены **23** read-only precheck, **24** source sync, **25** opt-in WeiDU install, **26** status, **27** verified rollback.
- Диспетчер GitHub: commit `a51f2c42a02dfa796e34722012adf95f30aff7da`, 28 164 байта, SHA256 `57be8fa5f1df7b67334990cf895932ec9c6237c7b6fae54781ffad43ccbdd4ba`. Новый pin записан в `BGXAI/fox_new/BOOTSTRAP_PIN.json`, commit `8b7554af3d23deba514ccf174f48520307fdfaba`, повторно сверен по размерам и SHA. Локальный CMD пользователя уже ранее был обновлён для cache-busting pointer.

## Что НЕ подтверждено

044 **ещё не установлен** на живом Windows у пользователя; результаты 17/17 — модельные тесты на системном Lua и фальшивом WeiDU, не реальная компиляция / LuaJIT/EEex выполнение. 043P имеет установленный файл, но реальное обнаружение атаки и печать пока не верифицированы. Активный 043-перехват/прикрытие только офлайн-модель, в игру не внедрён.

## Одно практическое действие пользователя

Закрыть EET/InfinityLoader/WeiDU, запустить **существующий** `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`. Должен появиться проверенный pinned dispatcher `a51f2c42a02d...` и пункты 23–27. **25** делает автоматический source sync с SHA256 + повторный preflight + backup; при запросе сознательно ввести `YES`. При `BLOCKED/REVIEW/STOP` не повторять автоматически, предоставить полный вывод. Если результат `INSTALLED_PASSIVE_044` со всеми True, можно проверить **26 status**, затем игру через InfinityLoader и `Ctrl+Alt+F11` в игровом окне без специально разыгранного боя; прислать текст строки/скриншот. **НЕ выбирать повторно 20** для 043P, **не удалять 042B**.

## Места хранения

- Постоянная Library: `/BALDURS_GATE_EET_AI/BUILD/BGXAI_044_DIAG_RELEASE/` и этот чекпойнт `/BALDURS_GATE_EET_AI/CURRENT/BGXAI_044_RELEASE_CHECKPOINT_20261109_RU.md`.
- GitHub `jeleZa112/nwn-xanos-updates`, branch `bg-eet-ai`, `BGXAI/fox_new/release_044/`, `BGXAI/BGXAI_SYNC.ps1`, `BGXAI/fox_new/BOOTSTRAP_PIN.json`, `BGXAI/CURRENT/HANDOFF_LATEST_RU.md`, `BGXAI/CURRENT/WORK_LOG_RU.md`.

Никакой повторной загрузки старых WeiDU.log, scripts.zip или трёх игровых архивов EET не требуется. При новом чате проверять прямой доступ к Library через файловые инструменты.
