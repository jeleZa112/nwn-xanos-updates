# BGXAI — комплекс R38 в едином обновляторе (27.11.2026)

## Краткий статус

**ВЫПУЩЕН КОД И ЕДИНЫЙ ОБНОВЛЯТОР. ПРОВЕРКИ WINDOWS/LINUX ПРОЙДЕНЫ. РЕАЛЬНОЙ УСТАНОВКИ R38 НЕТ.**

Пользователь подтвердил действующий R37 (read-only `status` пункта 174):

- `R37_PRESENT_LAST_PASSIVE`, последний компонент WeiDU **№153**.
- `WeiDU.log` SHA-256: `3f838e42236898b63cacb3256e9fff4bcea1b9f2273baba4baff27e8883f4538`.
- `override/M_BGXR27.lua` SHA-256: `5ece282270f0e6a1fa7a6086b7f13c57c77de98759637efa4b2ab0cc1e5744d6`.
- Игра не изменялась при проверке, `ordersSent=0`.

Ранее **реальный пункт 176 прошёл нативную компиляцию V3 BAF** из пользовательской EET: `status=V3_NATIVE_TEMP_COMPILE_PASS_NO_INSTALL`, `compiledBcsSha256=f6b14191fb1b6e9023dfaa9363809876578ffbea72d20c8b172a5a1c96bc3a85`. Это не означает установку, допустимость для класса/kit/ITM, действие в правильный момент или успешный перенос. Не повторять 175/старый 176 без основания.

## Что реализовано разом

Комплексная программа **R38**, используя рабочий R37 как строго проверяемый исходник:

1. `preflight` — read-only: проверяет свежие WeiDU №153 и SHA R37, proof R37, ресурсы EPS/EEex/DPLAYER, оригинальный WeiDU, отсутствие посторонней установки, SHA-кандидата R38, закрытые процессы. **Никакой записи в игру.**
2. `status` — read-only: различает `R38_NOT_INSTALLED_R37_PRESENT_LAST`, `R38_PRESENT_LAST_PASSIVE`, `R38_HOLD_UNKNOWN_WEIDU_OR_LUA`.
3. `install` — **только с отдельной явной typed-фразой** `INSTALL_BGXAI_R38_PASSIVE_IDENTITY_AFTER_R37` при успешном свежем preflight; создаёт внешнюю SHA-проверенную резервную копию `Documents/BGXAI_BACKUPS/PRE_BGXR38_*`, устанавливает **новый последний компонент WeiDU №154**, заменяющий только `override/M_BGXR27.lua`, последовательно проверяет контрольные хеши и log. При ошибке останавливается без автоматического восстановления/повторения.
4. `rollback` — **только с явной фразой** `ROLLBACK_BGXAI_R38_RESTORE_R37_ONLY` и если R38 действительно последний компонент; сверяет внешнюю копию, затем родной WeiDU должен вернуть R37. Это **подготовленная логика**, фактический откат в пользовательской игре ещё не проходил.
5. `capture` — после законной установки через уже существующий InfinityLoader собирает и строго сопоставляет четыре последовательности `[BGXR27]`, `[BGXR37]`, `[BGXINV3]`, `[BGXID]`. Не выполняет двигательных или экипировочных приказов, записывает только внешние отчёты/логи.

**Один пользовательский запуск:** `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`. Меню **176** теперь вызывает подменю:

- `1` / Enter — прежняя нативная проверка V3 (read-only, по умолчанию).
- `2` — R38 preflight (read-only).
- `3` — R38 status (read-only).
- `4` — R38 install (только после введённой вручную точной фразы).
- `5` — R38 rollback (только после введённой вручную точной фразы).
- `6` — R38 capture (после установки запускает оригинальный InfinityLoader, пользователь закрывает игру, затем формируется отчёт).
- `0` — выход.

Старый пункт 175 и все 1–174 сохранены; новых CMD/PowerShell-файлов пользователю не выдавать. Если консоль в 176 не интерактивна (`stdin.isatty=false`), автоматически остаётся прежняя безопасная проверка V3; не делать обходов и не заявлять, что подменю работало.

## Выпускные пины и артефакты

- `BGXAI/BGXAI_SYNC.ps1`, ровно **79 998 байт**, SHA-256 `d56ef12a986e2eb0628618b14d4d20b32ae5666fa0784a8d9444b06d7488a163`, неизменяемый commit `35708d0594c8b50e58fea5c7386b0f0bf0d6b5db`.
- `BGXAI/fox_new/BOOTSTRAP_PIN.json` обновлён commit `d4b4c41ebafc24cd8f36e4248945ff3ade12c194`. Ссылка на script commit проверена сравнением содержимого exact commit и ветки `bg-eet-ai`; байты совпали.
- Релизный Python обработчик `BGXAI/BUILD/WEAPON_XEQUIP_ONEFILE_175_RO_20261126/BGXAI_XEQUIP_ONEFILE_175_RO_V1.py`, **16 827 байт**, SHA-256 `c2fbefb877782047e2987b60fc517f1de11daec32da376893713b58e1fcbffcf`.
- Новый R38 installer/observer `BGXAI/BUILD/R38_GUARDED_FROM_R37_20261127/BGXAI_R38_GUARDED_FROM_R37.py`, **21 303 байта**, SHA-256 `f39c0efb08ef9db7097fe062db88c6f6b1452e4e77ec9b395d4e934d39440b9c`.
- Пассивный R38 Lua кандидат `BGXAI/BUILD/R37_XEQUIP_IDENTITY_SINGLE_LISTENER_SOURCEONLY_20261127/M_BGXR27_R37_INV3_IDENTITY_SOURCE_ONLY.lua`, **78 927 байт**, SHA-256 `958a3b7b8bd26840d62df63ad8b89d12a01a6ef97b446f7e7a969503afd0e19c`.
- Точный исходный R37 helper `BGXAI/BUILD/R37_R33_R36_SINGLE_LISTENER_RO_20261126/R37_GUARDED_SOURCE_ONLY.py`, 26 252 байта, SHA-256 `b34c93a0315c578989079c3565c6f0704315b8cdeabfb15be06508e4b5367e2d`.
- Оставшийся лимит 80 000 байт соблюдён без новой оболочки. Нет отгрузки `.GAM` в публичный GitHub.

## Тесты (проверенные по журналам CI)

- [Основной выпускной CI](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45956688461) — **Windows 106/106 PASS; Linux 106/106 PASS**: 10 release, 30 guarded, 25 onefile R38, 11 legacy175, 13 V3, 11 воспроизведение KeyError, 6 сохранность Lua. Windows дополнительно PowerShell 5.1 AST PASS.
- [Стадийный CI PS 5.1](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45956404946) — Windows/Linux PASS; только две SHA/size замены в PS, все прежние пункты по байтам не изменены.
- [Первоначальный CI R38](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45956238705) — Windows/Linux **96/96 PASS**.
- [Выпускной CI legacy 175](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45956571636) — Windows/Linux PASS.

Результаты CI — только тесты кода в синтетической/изолированной среде. Не выдавать их за факт установки, живую идентификацию персонажа или реальную проверку всех механик при экипировке.

## Строгое различие стадий

| Стадия | Состояние |
| --- | --- |
| R37 текущий LIVE install | подтверждён пользователем — 153 последний, контрольные SHA верны |
| V3 BAF native EET compile | PASS по настоящему отчёту пользователя, временный BCS удалён |
| R38 source + guarded updater | CODE released, CI Windows/Linux PASS |
| R38 fresh preflight на пользовательской EET | **не выполнен** |
| R38 WeiDU install last-only №154 | **не выполнен** |
| R38 runtime identity/inventory `[BGXID]` | **не выполнен** |
| XEquipItem в игровом мире | **не выполнялся**; классовая совместимость, origin manual/EPS и safe idle не подтверждены |

## Ближайшее одно действие пользователя

Закрыть игру/InfinityLoader, открыть обычный `BGXAI_UPDATE.cmd`, убедиться, что он показывает `verified pinned script 35708d0594c8`, выбрать **176**, затем **2 (R38 preflight)**. Отправить один файл `BGXAI_R38_PREFLIGHT_*.json` из `C:\Users\Drevo\Documents\BGXAI_LIVE_REPORTS` либо текст STOP/HOLD. Не запускать повторно 175 и не вводить typed установку заранее. Если preflight PASS, следующий шаг — отдельное явное разрешение пользователя на установку пассивного наблюдателя; нельзя выдавать устоявшийся CI за consent.

## Глобальные правила

- Один обновлятор, никаких лишних команд вручную и новых CMD.
- Без проверки реальной игры при `preflight=PASS` не активировать функции. Нет автоarm `BGXW3ARM=1`; ActionStarted НЕ является доказательством idle.
- Сохранять текущие EPS, SCS, R29/V6, BG_EET_RU, BG Voice RU, сейвы. Кандидат R38 не меняет engine-очередь, не создаёт предметы, не прерывает раунд.
- После HOLD/STOP — остановка с анализом, без автоматического ретрая, не пытаться вручную откатить WeiDU.
- Любые будущие изменения по локальной исходной точке оформлять отдельными проверяемыми методами/записями; не путать подготовленный rollback и реально проверенный игровой rollback.