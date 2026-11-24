# BGXAI — меню 167: проверка native WeiDU без установки

Дата: **24.11.2026**. Этап: **CODE / CI PASS; NATIVE EET NOT RUN; DEPLOY/LIVE нового выбора оружия NO**.

## Фактически сделано

- Единственный пользовательский загрузчик остаётся `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`. Его байты и bootstrap-лимит **80 000** не менялись.
- В `BGXAI/BGXAI_SYNC.ps1` сохранены **все 166 прежних веток меню**, автоматически проверена точная нормализованная неизменность команд; сокращены только имена внутренних функций `AssertNotReparse→ANR`, `VerifiedManifest→VM`, `RunRelease→RR`, `BGXOneFileManaged→BOM` вместе со всеми их вызовами. Новая ветка **167 — Weapon V3 native BAF compile (READ ONLY)**.
- `BGXAI_SYNC.ps1`: **79 674/80 000 байт**, SHA256 `5f53f7a7f3a76dbe2477776f9d0331f5d9b7a57f421267f70ddf421ebf27b129`, свободно 326 байт. Не увеличивали ограничение.
- `BGXAI/fox_new/BOOTSTRAP_PIN.json` указывает на **неизменяемый коммит исходника** `557c97c093fbfffc3d4027dd0e570d41c4aadd22`, строго эти размер+SHA. Итоговый опубликованный HEAD ветки до документа `cec6873b4d219594b362689a8dab7b689d0a3b5c`. Пин выставлен через два объекта commit/tree, ветка сдвинута **один раз** за согласованный релиз, не было транзитного несовпадения.
- Новый манифест `BGXAI_WEAPON_NATIVE_COMPILE_MANIFEST_V1.json` содержит только два файла: `BGXAI_WEAPON_NATIVE_COMPILE_PREFLIGHT_RO.py` (9551 байт, SHA256 `27285b3d067eab2c67b075dc8654b9a0f74da0d7920b2e96339ced3e14bcd10a`) и `BGXAI_WEAPON_SLOT_CONSUMER_V3.baf` (6763 байта, SHA256 `92b8b1d3393a286d4d69f38b9542651acb429f8ef6627051195c7a1a95c09f30`). Исходники загружаются проверенным `SyncRelease` в `BGXAI_DEV\weapon_priority_v3`; **не копируются в override, не устанавливаются через TP2**.
- Опция 167 запускает уже проверенный isolated read-only WeiDU preflight: временная копия `weidu.exe`, временный BAF/BCS, `--no-auto-tp2`, выбранный `dialog.tlk`, контроль SHA затрагиваемых игровых файлов до/после и **NO INSTALL**.
- Одно JSON-сообщение сохраняется в `%USERPROFILE%\Documents\BGXAI_LIVE_REPORTS\BGXAI_WEAPON_NATIVE_COMPILE_RO_<timestamp>.json`; строка `REPORT_FILE=` выводит его точный путь. При отказе/ошибке компиляции отчёт также должен сохраняться, код возврата ненулевой и меню печатает STOP.

## Независимые проверки

**GitHub Actions 45340782245 — completed SUCCESS** на `windows-latest` и `ubuntu-latest`: полный контракт старых веток 1–166, SHA+размер, новый read-only 167, SHA двух исходников/манифеста, фиктивный игровой root и отказоустойчивость native WeiDU, Windows PowerShell 5.1 AST parse. https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45340782245

Отдельные CI того же release HEAD: **R27 45340782232 SUCCESS**, **V7 45340782286 SUCCESS**. В предыдущей цепочке выбора оружия — **439/439 на каждом Lua5.3/Lua5.4/LuaJIT, исходники PASS** (run 45322504666); её в этом пакете заново не меняли.

**Остальные старые CI не обязательно зелёные:** R20 pin/size tests по-прежнему привязаны к давно устаревшему immutable commit и размеру 79 871, WTASIGHT ожидает устаревший V6/34-file manifest; EPS-first validator проверяет прежний шаблон CMD. Эти проверки нельзя использовать как утверждение о дефекте menu167, но они остаются техническим долгом и не должны маскироваться.

## Следующий единственный нужный пользователю шаг

**Закрыть Baldur's Gate и InfinityLoader.** Запустить **существующий** `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd` и в меню выбрать `167`. **Не выбирать 166 (V7)**, не переустанавливать V6/R27 и не запускать командные файлы вручную.

Ожидается один JSON из `Documents\BGXAI_LIVE_REPORTS` — приложить его к чату. `NATIVE_WEIDU_COMPILED_TEMP_ONLY` вместе с `watchedFilesChanged=false` означает только успешную **компиляцию во временной папке**, а не автоматическую смену оружия. `BLOCKED_BEFORE_COMPILER`/`WEIDU_COMPILE_FAILED_OR_UNRESOLVED_IDS` — адресно исправить существующий код после чтения отчёта. `REVIEW_WATCHED_LIVE_FILES_CHANGED` — STOP без автофикса.

После реальной native компиляции — выяснить effective APR альтернативных слотов, ammo/launcher и происхождение manual/EPS очереди, затем подключать **существующий** guarded producer/BAF и лишь с отдельным typed install разрешением проводить один реальный A/B игровой тест. **CODE/CI ≠ GAME LIVE**. Сохранения, EPS, BG_EET_RU, BG Voice RU и игровые BCS в этом обращении не менялись.

Постоянные правила: без лишних «+», максимальный пакет тестов за один запуск, не повторять R27/R28/V6, не плодить похожие скрипты, единый updater и один отчёт.
