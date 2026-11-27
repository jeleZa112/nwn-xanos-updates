# BGXAI — 27.11.2026: пункт 176 в едином обновляторе — выпущен, нативный EET runtime пока HOLD

**Актуальный результат:** ONEFILE_MENU176_RELEASED_PINNED, SOURCE_CI_PASS_WINDOWS_LINUX, **NATIVE_EET_V3_NOT_RUN**, **ITEM_TRANSFER_NOT_INSTALLED**, **GAME_CHANGED_BY_THIS_STAGE=NO**.

## Подтверждённое исходное состояние

- Пользователь ранее прислал подлинный `BALDUR(1).gam` (не загружать в публичный GitHub). SHA256 `7e926634c0972e90e25c975a18c9bf34b96f4d85184195c630555fdd43f7e19c`. GAMEV2.0, CRE V1.0; Джаган, partyIndex 1, CLERIC raw 3, уникальный `STAF01` в рюкзаке slot20 (`SLOT_MISC5`), quickweapon slot35 (`SLOT_WEAPON0`) был пуст в сохранении. Это НЕ доказательство актуального состояния в работающей EET.
- V3 BAF точно 762 ASCII байта SHA256 `996fd8896225ddbcd1ba2e260ca866acb70de09a6f91c9eb4338063fb7ae23e1`: при отдельно выставленных `BGXW3ARM/TAG/TRY` в LOCALS и вне боя однократно вызывает `XEquipItem("STAF01",Myself,SLOT_WEAPON0,EQUIP)`. Автоактивации НЕТ.
- R37+INV3+ID проверены как единый исходник с одним callback; это READ-ONLY, не безопасная граница idle и не источник разрешения на перенос. LIVE игра не запускалась на этом этапе.
- Старый пункт 175 компилировал инертный BAF и уже PASS в реальной EET; заново его НЕ запускать.

## Новый конкретный результат

1. Подготовлен Python-обработчик с раздельными режимами: файл `BGXAI/BUILD/WEAPON_XEQUIP_ONEFILE_175_RO_20261126/BGXAI_XEQUIP_ONEFILE_175_RO_V1.py`, теперь **12 657 байт**, SHA256 `6645ca3c80860a4a740d9497f564ec8fa44385a4d1a57930e884a2641373e0e6`. Без `--v3` старый пункт 175 сохраняет `SOURCES` из 4 файлов и существующую функцию `prepare()`; с `--v3` разрешена только проверка точного V3 BAF/проверенного native backend/аудита по трем SHA-пинам. Исходник передаётся во внешнюю временную папку, игровой BCS не записывается, LOCALS не выставляются.
2. В **том же** `BGXAI/BGXAI_SYNC.ps1` появилось меню **176**; пункт 175 (инертный) остался, обработчики 1–174 сохранены побайтно. Использован PowerShell 5.1 `switch`-предикат только для 175/176 и передача `--v3` только при выборе 176. Размер файла **79 999/80 000 байт**, SHA256 **`6cc2af578c82fc06b19a13be0f0a26fff09e42650e2065cdf9be8e850629495e`**.
3. Реальный GitHub-коммит, содержащий опубликованный `BGXAI_SYNC.ps1` и dual-mode Python: **`60b9c40c05a76594d753bde5cf13b81ce0de32b8`**. `BGXAI/fox_new/BOOTSTRAP_PIN.json` установлен на этот commit/SHA/79999 B отдельным commit **`df7e0877fb265c58eafc3c76228f7b980bb00693`**. Пин проверен чтением исходника по **самому указанному immutable commit** и по главной ветке: байты совпали.
4. [Эталонный staged Windows/Linux PS5.1 CI](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45951351236): на обеих системах 6+11+13 тестов, Windows native PS5.1 AST/dispatch/splat PASS. [Выпускной независимый CI](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45951720324): Windows и Linux **6+11+13+6 тестов каждый PASS** плюс реальный PowerShell 5.1. [Последний старый пункт 175 CI](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45951657995) SUCCESS после выпуска.
5. Есть **исторические CI с устаревшими ожиданиями** (`169 - ...`, `170 R30 RO`, R19 11013 байт вместо 11252 и подобные). Они срабатывают на изменении BGXAI_SYNC/pin и могут давать FAIL независимо от V3-проверок. Нельзя выдавать их как все исправленные; при дальнейшей работе стоит сравнивать каждое со старой базой, не переписывать логику EPS/игры ради зелёной отметки. Новые узкоспециализированные выпускные проверки подтверждены PASS.

## Следующее единственное действие пользователя (после чтения этой точки)

1. **Закрыть игру и InfinityLoader**.
2. Запустить существующий `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd` — никаких дополнительных скриптов/CMD/ZIP.
3. Выбрать **176**, дождаться завершения read-only native preflight.
4. Прикрепить **один JSON-отчёт** `BGXAI_XEQUIP176_V3_RO_*.json` из `C:\Users\Drevo\Documents\BGXAI_LIVE_REPORTS`. Если файл не создался или STOP, передать текст консоли; не повторять автоматически.

Ожидаемый настоящий критерий PASS: внешний отчёт `status=V3_NATIVE_TEMP_COMPILE_PASS_NO_INSTALL`, `innerReport.status=V3_NATIVE_BAF_COMPILED_TEMP_ONLY`, `nativeWeiDUCompileVerified=true`, `watchedFilesChanged=false`, `installed=false`, `ordersSent=0`, `dispatchAuthorized=false`. **CI уже PASS != native EET PASS**, не приписывать выполненную компиляцию до пользовательского отчёта. Никаких записей `BGXW3ARM=1`, никаких активных `XEquipItem` сейчас.

## Следующий этап после native PASS

Надёжно доказать границу idle/manual/EPS, актуальную live-идентичность Джагана, класс/kit/ITM-совместимость, наличие unique `STAF01` и пустого 35 слота непосредственно в EET. Только после этого подготовить отдельно разрешаемый guarded WeiDU last-only однократный пилот с внешним backup и постусловием сохранности предметов/зарядов. Разрешение на реальные изменения игры по-прежнему **НЕ ДАНО**.

**Правила:** один обновлятор, никаких повторений 175/старого R37, SAFE HOLD без авто-retry, не трогать BG_EET_RU, BG Voice RU, EPS, V6, R29, пользовательские сейвы. SOURCE CI не эквивалентно игровой установке.