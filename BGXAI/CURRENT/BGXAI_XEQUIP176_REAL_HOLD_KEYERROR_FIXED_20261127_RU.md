# BGXAI XEquip V3 menu176 — фактический HOLD исправлен, 27.11.2026

## Источник сбоя (фактический пользовательский запуск)

Единственный обновлятор `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`, пункт `176`, сообщил:

```text
BGXAI: verified pinned script 60b9c40c05a7 (SHA256 OK)
Choice [0]: 176
"schema": "BGXAI_XEQUIP_ONEFILE_175_READONLY_V1",
"status": "HOLD_XEQUIP175",
"reason": "HOLD_PINNED_DOWNLOAD_OR_HASH_FAILURE:KeyError,KeyError",
"ordersSent": 0,
"newGameFilesWrittenByThisRunner": 0
BGXAI STOP: 175 RO STOP
```

Отчёт у пользователя: `C:\Users\Drevo\Documents\BGXAI_LIVE_REPORTS\BGXAI_XEQUIP176_V3_RO_20261127T133646303228.json`.

**Диагноз подтверждён точной строкой исходника:** после разрешения пути из объединённого списка `SOURCES` и `V3_SOURCES`, сетевой `fetch_pinned()` использовал только `SOURCES[path][0]` для лимита чтения. Первые два V3-файла отсутствовали в старом `SOURCES`, поэтому оба зеркала вызывали `KeyError`. Это программная ошибка обработчика до нативной компиляции, не отказ WeiDU и не поведение игры.

## Исправление

В `BGXAI/BUILD/WEAPON_XEQUIP_ONEFILE_175_RO_20261126/BGXAI_XEQUIP_ONEFILE_175_RO_V1.py`:

```python
raw = h.read((SOURCES.get(path) or V3_SOURCES[path])[0] + 1)
```

В обработчике `main()` при `--v3` теперь корректные `schema=BGXAI_XEQUIP_ONEFILE_176_V3_READONLY_V1` и `status=HOLD_XEQUIP176_V3`, если настоящий отказ всё же произойдёт.

Главный `BGXAI_SYNC.ps1` теперь сообщает `$choice RO STOP` с действительным номером, сохраняет все предыдущие маршруты 1–175 и ограничение 80 000 байт.

Старые `SOURCE`-пины не удалены и не ослаблены. В V3 скачиваются только заранее перечисленные исходники, проверяемые по точному SHA-256 и длине; никакой резервной установки не предусмотрено.

## Опубликованные и проверенные версии

- `BGXAI/BGXAI_SYNC.ps1`, коммит `58001197c959fac13d6d530cb8cc4d678e0e14ba`, **79 998 байт**, SHA-256 `e16acdb69231aa8723ce50d820ce75101d93494ac9f12d894ec63a3956ec461d`.
- `BGXAI/fox_new/BOOTSTRAP_PIN.json`: закрепляет ровно тот коммит, SHA-256 и размер. Коммит обновления пина `bf82ba5b5d7e8759bf4c45ec69c46a81f03ed8d1`.
- Исправленный обработчик: 12 783 байта; режим 175 по умолчанию остался инертным, V3 доступен отдельно через 176.
- В `BGXAI/BUILD/WEAPON_XEQUIP_ONEFILE_175_RO_20261126/test_xequip_176_download_keyerror_regression.py` — 11 новых тестов с подменой `urllib.request.urlopen`: отдельные V3 пути, fallback CDN, отказ при изменённом SHA, полный запуск реального Python source-only V3 и старого 175 с временным staging, корректный HOLD.
- [GitHub Actions — обязательный выпускной CI](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45953426161): **PASS Windows + Linux**, на каждой системе `6+11+13+11+6` тестов; на Windows также PowerShell 5.1 AST.
- [Проверка исторического menu175](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45953407249): **PASS Windows + Linux**.
- [Первоначальная независимая регрессия KeyError](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45953152984): **PASS Windows + Linux**.

## Разграничение стадий

- **CODE:** ошибка реальной загрузки исправлена.
- **TEST/CI:** Windows и Linux PASS; фактические HTTP ответы заменялись строго контролируемыми mock-ответами и выверялись по действительным GitHub файлам.
- **GAME NATIVE:** **НЕ ПРОВЕРЕНО** после исправления. Компиляция точного активируемого BAF с `STAF01` в установленной EET не подтверждена.
- **DEPLOY/LIVE:** **НЕ ПРОВЕРЕНО**. Ни `XEquipItem`, ни флаги `BGXW3ARM` в игре не запускались.
- Никаких изменений рабочих игровых файлов, WeiDU.log, BG_EET_RU, BG Voice RU, EPS и сейвов этой работой не делалось.

## Ровно одно следующее действие пользователя

После закрытия игры и InfinityLoader открыть обычный `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`, проверить в заголовке `verified pinned script 58001197c959` и выбрать **176** один раз. Отправить новый файл `C:\Users\Drevo\Documents\BGXAI_LIVE_REPORTS\BGXAI_XEQUIP176_V3_RO_*.json` или текст нового STOP/HOLD. Не повторять 175; не запускать по второму CMD/PowerShell. Если HOLD/STOP — не делать автоматических повторов.

**Следующий технический этап после нативного PASS:** проверить безопасную границу действия в настоящей игре, затем отдельная typed установка после подтверждения личности Джагана и права экипировать посох; CI не означает игровую работоспособность.
