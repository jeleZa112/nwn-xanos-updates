# BALDURS_GATE_EET_AI / BGXAI 045 — фиксация исправления имён Lua

Дата: 2026-11-09. Статус: **source-only пакет + обновлённый однофайловый updater на GitHub; в EET не установлен**.

## Причина, подтверждения, границы уверенности

- Пользователь подтвердил, что после реальной успешной WeiDU установки 044 и запуска игры сочетание Ctrl+Alt+F11 **не показывает** диагностическую строку. Ранее 043P не показал уведомление после подтверждённой атаки Шанка по Jade. Подтверждённый установленный BCS 042B не изменялся. Эти наблюдения не доказывают, что вся система EEex отключена.
- Найдена конкретная ошибка проектирования: старый Lua `M_BGX43Probe.lua` — 12 символов basename, `M_BGX44Diag.lua` — 11. В движке EE Lua действует предел **8 символов ResRef**, который распространяется на автозагрузку `M_*.lua`. Модификации с короткими именами подтверждают это правило: пример открытого кода BG2Narrator `M_BG2NAR.lua` прямо отмечает этот предел; BG EE/EEex документация описывает 8-символьные ResRef. Поэтому оба старых файла могли пройти WeiDU, но остаться не загруженными. Причина вероятная и хорошо подкреплена, **окончательно подтверждается только живым тестом 045**.
- Источники: https://eeex-docs.readthedocs.io/en/latest/EE%20Game%20Classes%20%28x86%29/CResRef/ , https://eeex-docs.readthedocs.io/en/latest/EE%20Game%20Lua%20Functions/Infinity/ , https://github.com/MariusTBjercke/bg2narrator/blob/d9f5a8f0b08baec27f8f155b7c0b748069b6699a/BG2Narrator/lua/M_BG2NAR.lua

## Реализация 045

- Новый отдельный компонент WeiDU `BGX45/setup-BGX45.tp2` **только ДОБАВЛЯЕТ**: `override/M_BX43.lua` (6 символов) и `override/M_BX44.lua` (6 символов). Содержимое этих файлов ПОБАЙТОВО совпадает с прежними 043P и 044 Lua, SHA256 `f1e6fcc6989512bee5e217a66ef42ea48a828c407c7009e6012a90b95d5db19f` и `a7bdfba10cdb3cc26351072dac0c6f375e03b4ce3a288f0eb15db945411dd33f`. Глобальные имена `BGX43Probe` / `BGX44Diag` без изменений; оригинальные длинные Lua остаются на месте.
- WeiDU установщик `BGXAI45_INSTALL.py`: точный game root, SHA 042B BCS `8602e8853a9c0e8b1bd5733021e6dd9c9ac73e03beb6c9900ef6ebd09dacb9a0`, точные SHA обоих старых Lua, BGX42/43/44 в WeiDU и 044 **последним**, отсутствие 045/коротких файлов, контроль работающих процессов, полная проверка исходников SHA и destination. Перед установкой внешний backup `Documents/BGXAI45_SAFE_BACKUPS`, после — проверка нового last, копий и неизменности боевого BCS/043P/044, EEex boot, chitin, dialog.tlk. При `REVIEW`/`BLOCKED` не повторять вслепую. Штатный откат через WeiDU только при 045-last и verified backup.
- **Нет изменения AI команд, BCS, сохранений, интерфейса, TLK, пользовательских или игровых архивов.** Название модуля и установка не делают его «командным ИИ»; 043/044 пассивные.
- Офлайн-тесты: **19/19 PASS** (манифест, точные Lua SHA, ограничение resref, запреты на вредные Lua-вызовы, запрет коллизий, отказ на изменённый BCS/неверный WeiDU-last, полноценная имитация install/rollback с WeiDU runner, подмена файлов и блокировка отката). `compileall PASS`, ZIP CRC PASS; тесты исполнялись в Python и с **mock WeiDU**, а не на живой Windows EET.
- ZIP: `/mnt/data/BGXAI_045_RESREF_FIX_SOURCE_ONLY.zip`, **15 439 байт**, SHA256 `6e802a254eda29eff2676c31883d0ffdfcf5bf8499f6dcc07633b03d300cda90`. Исходники и ZIP размещены в Library `BUILD/BGXAI_045_RESREF_FIX/`; публичный GitHub — `BGXAI/fox_new/release_045/`, **8/8 SHA и размер совпали** по фактически опубликованным файлам.

## Обновлятор

- Ветка GitHub `jeleZa112/nwn-xanos-updates:bg-eet-ai`. `BGXAI/BGXAI_SYNC.ps1` immutable commit `cf92755b0074a3f70d5cc7be2211085ca36f9fb4`, SHA256 `96b2d4823fb0dbd7ab538547cbaefaef9eb0a31d7fb470c5ed5887e5d7f010a4`, **31 936 байт**; `BOOTSTRAP_PIN.json` обновлён commit `7af64803557d6e7c66ef76c46e532512fb6786d4`. Байт-проверки пина и всех 8 релизных исходников прошли.
- Сохранились старые пункты **1–27**, новые: `28` 045 READ ONLY preflight; `29` verified sources only; `30` experiment opt-in YES install; `31` READ ONLY status; `32` guarded rollback. Локальный существующий CMD сам загружает новую версию по pin (уже имеет cache-buster). Никаких новых CMD.

## Одно безопасное следующее действие пользователя

1. Закрыть игру и InfinityLoader, запустить **существующий** `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`.
2. Выбрать **28 — BGXAI 045 READ-ONLY PREFLIGHT**. При `BASELINE OK. NOT INSTALLED.` затем выбрать 30 и подтвердить `YES`. Если `REVIEW`, `BLOCKED` или неправильные SHA/версия, остановиться и прислать вывод, не повторять.
3. После `INSTALLED_PASSIVE_045`, запуск через InfinityLoader, загрузить любое сохранение и ОДИН раз Ctrl+Alt+F11. Ожидается строка `BGX44: 043P loaded=true listener=true ...` без нового боя. В случае отсутствия строки больше не экспериментировать наугад: проверять runtime EEex и путь отображения, раздельно от управления охраной 042B.

**Не просить WeiDU.log, scripts.zip, три архива EET; все уже в постоянной библиотеке. Не переустанавливать 043/044, не откатывать рабочую 042B.**
