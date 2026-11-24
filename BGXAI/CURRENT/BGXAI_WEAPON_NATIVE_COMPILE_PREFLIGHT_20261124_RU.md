# BGXAI — новый безопасный native WeiDU preflight для восьмиветочного выбора оружия

**Дата:** 24.11.2026. **Статус:** SOURCE/LOCAL TEST PASS. **DEPLOY NO / LIVE NO.**

## Реальный результат

После предыдущего source-only `BGXAI_WEAPON_SLOT_CONSUMER_V3.baf` (8 веток, SHA256 `92b8b1d3393a286d4d69f38b9542651acb429f8ef6627051195c7a1a95c09f30`) подготовлен новый **отдельный read-only preflight**, а не ещё один ранкер или альтернативный установщик:

- `BGXAI_WEAPON_NATIVE_COMPILE_PREFLIGHT_RO.py` проверяет исходник по **точному pinned SHA256**, ожидает 8 веток и 4 штатных `WeaponCanDamage`-триггера.
- Использует найденный ранее в проекте шаблон `release_054/compile_guard_054.py`: копирует проверенный `weidu.exe` или `setup-enhanced-powergaming-scripts.exe` во временную директорию **под именем `weidu.exe`**, не запускает TP2, передаёт `--noautoupdate`, `--no-auto-tp2`, `--no-exit-pause`, `--game`, `--tlkin`, `--out`, `--log` с временным выводом и закрытым stdin. Исходный EET служит только источником реально установленных IDS/TLK.
- Принимает компиляцию только если exit code=0, stdout/stderr без `ERROR/WARNING/UNRESOLVED`, в TEMP существует **ровно один BCS** с ожидаемым именем, непустым компилированным содержимым и сигнатурой `SC\n`.
- Контролирует SHA256 **выбранных** live-файлов до/после: `chitin.key`, `WeiDU.log`, `weidu.conf`, `lang/ru_ru/dialog.tlk`, `dialogf.tlk`, `override/DPLAYER.BCS`, `WTASIGHT.BCS`, `PRIEST1.BCS`, `M_BGXR27.lua`. При изменении отмечает `REVIEW_WATCHED_LIVE_FILES_CHANGED`, никогда не откатывает автоматически.
- Вывод честно содержит `wholeGameTreeChecked=false`: контроль ограничен перечисленными файлами, **не весь каталог игры**. `engineBehaviorVerified=false`, `gameplayLiveVerified=false`, `installPerformed=false`, `ordersSent=0`, `dispatchAuthorized=false`.
- Источник может быть временно размещён только **вне игры** либо в точном будущем каталоге штатного обновлятора `BGXAI_DEV/weapon_priority_v3/` с тем же SHA. **В `BGXAI_UPDATE.cmd` и BGXAI_SYNC.ps1 этот preflight пока НЕ подключён**; пользователь не должен запускать отдельный CMD/PowerShell или ставить его в игру.

## Выполненные проверки

1. `test_weapon_native_compile_ro_v1.py`: **21/21 на Linux локально**, включая 20 типовых mock/negative случаев и **один реальный OS subprocess для тестового fake-weidu**. В процессе тестирования обнаружили и **устранили потерю права исполнения** после временного копирования бинарника; теперь `shutil.copy2` + сравнение SHA. Это не реальный WeiDU.
2. Включение в существующий `run_weapon_priority_v3_regression.py --static-only`: static advisory + BAF 8/8 + новый preflight 21/21 PASS.
3. Общий LuaTeX: **439/439 offline тестов** (59 V3, 34 V4, 25 V5, 22 NONINTERRUPT, 11 интеграция, 288 матрица). Проверено, что изменения не затрагивают Lua-ранкеры, BAF и игру.
4. CI workflow `bgxai-weapon-priority-v3-regression.yml` дополнен новыми исходниками и preflight-тестами в **том же** пакетном запуске Ubuntu/Windows. После GitHub публикации необходимо проверить фактический run и журналы; локальные PASS не равны CI PASS.

## Чего это НЕ доказывает

- Настоящая игра `C:\Games\BG_EET_FOXX_NEW` недоступна в текущем окружении. **Ни реальный EET TRIGGER.IDS/HAND.IDS, ни установленный Windows WeiDU не запускались**. Успехов native compile пока нет.
- Mock-процесс с `SC\n` может имитировать компиляцию, поэтому тесты гарантируют только защитный контракт preflight, **не доказательство native компиляции**.
- Нет доказанного эффективного APR альтернативного слота, launcher/ammo pairing, manual/EPS provenance или игры с полным выбором оружия. В существующем BAF 1..4 и 5..8 ветки остаются SOURCE ONLY и не исполняются; `BGXW3_NATIVE_PROVENANCE=1` само по себе не подтверждает право посылать команду.

## Следующий необходимый этап

1. После независимой CI сделать один **объединённый** штатный read-only шаг с проверкой installed IDS и реальным native WeiDU через **существующий** `BGXAI_UPDATE.cmd`, а не новый батник; это требует отдельного безопасного добавления меню и пересмотра лимита подписанного загрузчика (сейчас PS1 близок к пределу 80 КБ). Прежние R27/R28/V6 не повторять.
2. Если native compile на реальном EET PASS и хеши live не изменены — продолжить проверку происхождения ручной/EPS очереди, актуальности цели и выбора пригодного альтернативного оружия; до подтверждения **не подключать BCS producer**.
3. Любой активный install только после typed user consent, SHA preflight, external backup, WeiDU last-only rollback и A/B в настоящем бою. Не затрагивать BG_EET_RU/Voice RU/сейвы/EPS/SCS/EEex без отдельной необходимости.

**Файлы проекта:** `BGXAI/patchsets/ranged_fighter_guarded_20261119/` и текущая точка `BGXAI/CURRENT/BGXAI_WEAPON_NATIVE_COMPILE_PREFLIGHT_20261124_RU.md`.

## Исправление точного SHA после первого CI

Первый CI `45331124467` верно остановился на `BAF_SOURCE_SHA256_MISMATCH`: Локальная Library-копия BAF имела завершающий LF, в отличие от GitHub-источника в ветке `bg-eet-ai` заканчивается ровно `END` без LF. Сверены через GitHub connector строки Library и GitHub (6761 символ без финального перевода строки); различие обнаружено в байтовом представлении копий, а не в логике BAF. Причину добавления/удаления LF нельзя достоверно установить без трассировки всего пути сохранения. Зафиксирован **именно байтовый GitHub BAF без финального LF** (6763 байта, SHA256 `92b8b1d3393a286d4d69f38b9542651acb429f8ef6627051195c7a1a95c09f30`). Исходник BAF в GitHub **не менялся**, пин SHA не отключался. Повторный локальный тест и повторный независимый CI обязательны; не писать CI PASS до проверки run.

## Итог независимой CI после исправлений — ПОДТВЕРЖДЕНО 24.11.2026

**Проверено фактическими GitHub Actions jobs и логами:** [run 45331726567](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45331726567) **completed / SUCCESS** на commit `db9584b79bf4ee1bf078314f9dc36ad87d746a4f`.

- Ubuntu Lua 5.3: **439/439 PASS**, native compiler safety **21/21 PASS**, BAF static **8/8 PASS**.
- Ubuntu Lua 5.4: **439/439 PASS**, native safety **21/21 PASS**, BAF static **8/8 PASS**.
- Ubuntu LuaJIT: **439/439 PASS**, native safety **21/21 PASS**, BAF static **8/8 PASS**.
- Windows static: BAF static **8/8 PASS**, native compiler **19/19 PASS**, **2 POSIX/symlink теста намеренно SKIPPED**. Оба jobs завершились `success`.

Отрицательные CI запуски `45331124467`, `45331386209`, `45331597656` завершились FAILURE и **не скрываются**. Их проблемы полностью устранены до успешного прогона:

1. Источник BAF в GitHub имеет SHA256 `92b8b1d3393a286d4d69f38b9542651acb429f8ef6627051195c7a1a95c09f30` **без конечного LF**; исходный SHA-пин из Library-копии с LF был отличен. Проверено сравнение Git blob SHA1 `84e478827bbd7726d48ea2c9e2e6624eb652bac0` с вычисленным git blob SHA1 у байтового кандидата. Source pin исправлен в commit `3b9ce200184349369c05de248c752670b58d75b4`. BAF в GitHub не переписывали.
2. Windows Git по умолчанию менял окончания строк BAF при checkout. В корень репозитория добавлен единственный точный `.gitattributes`: `BGXAI/patchsets/ranged_fighter_guarded_20261119/BGXAI_WEAPON_SLOT_CONSUMER_V3.baf -text`; это сохраняет **точные SHA-проверяемые байты BAF** на Windows; commit `3e2a402d88115892c281b45a7bf468a4fb7c3fe9`.
3. Windows TEMP возвращал 8.3-путь `RUNNER~1`, в то время как `Path.resolve()` давал полное имя `runneradmin`. Тест исправлен сравнением именно разрешённых путей, без отключения проверки директории; commit `db9584b79bf4ee1bf078314f9dc36ad87d746a4f`.

Все исправления **не изменяют установленную EET, EPS, Lua/BSC/WEIDU, сохранения или единый обновлятор**. `installedIdSVerified` не заявляется; статус результата `nativeSymbolsAcceptedByCompiler` будет устанавливаться лишь после успешной реальной компиляции с установленными IDS.

**Следующий безопасный шаг после CI:** проверено подключение к единственному updater. `BGXAI/BGXAI_SYNC.ps1` на ветке `bg-eet-ai` — **79 937 UTF-8 байт**, а загрузчик `BGXAI_UPDATE.cmd` ограничивает скрипт **80 000 байт**. Свободно **63 байта**, для нового пункта меню и signed manifest этого недостаточно. Не внедрять новый пункт без сокращения script source с сохранением старых действий, pin manifest, статических Windows/PowerShell тестов и размера ниже лимита. Не обходить 80KB cap. Не требовать отдельного bat/PowerShell от пользователя.

**Текущий функциональный рубеж:** native preflight подготовлен, **но не подключён** к `BGXAI_UPDATE.cmd` и **не проверял настоящий EET WeiDU**. После безопасной интеграции запустить одним updater один read-only native preflight, затем перейти к alt-slot effective APR, launcher/ammo, manual/EPS provenance, отдельно разрешённому install и LIVE A/B. Не повторять R27/R28/V6.