# BGXAI — ВПЕРВЫЕ подтверждена нативная компиляция V3 в EET (27.11.2026)

**Каноническая контрольная точка после фактического пользовательского отчёта.** Этим документом перекрывается старый статус `NOT_NATIVE` для точного V3 BAF, но **никаких подтверждений игрового исполнения это не создаёт**.

## Реальный входной факт

Участник проекта запустил только существующий `BGXAI_UPDATE.cmd`, пункт **176**, и прислал `BGXAI_XEQUIP176_V3_RO_20261127T134903503792.json`. Размер исходного пользовательского отчёта — **1993 байта**, SHA-256 — `ab0e071dbe41175c20050bfce44b963cc3be6a734b2cbdaecad884d3c82ac496`. Исходный пользовательский JSON с локальными путями и пользовательскими данными **не публикуется в GitHub**; публикуются только обезличенные контрольные поля и хеш.

По точному JSON:

| Поле | Результат |
|---|---|
| `status` | `V3_NATIVE_TEMP_COMPILE_PASS_NO_INSTALL` |
| `innerReport.status` | `V3_NATIVE_BAF_COMPILED_TEMP_ONLY` |
| `nativeWeiDUCompileVerified` | **true** |
| Скомпилированный BAF SHA-256 | `996fd8896225ddbcd1ba2e260ca866acb70de09a6f91c9eb4338063fb7ae23e1` |
| Размер BAF | 762 байта |
| SHA-256 WeiDU | `0d17e26e3f3ef5b36796eb0ee8ae73cb851d8b62c9702c2e224da2945caafb75` |
| SHA-256 выходного BCS | `f6b14191fb1b6e9023dfaa9363809876578ffbea72d20c8b172a5a1c96bc3a85` |
| `watchedFilesChanged` | **false** |
| `wholeGameTreeChecked` | false — не выдавать за проверку всех файлов |
| `temporaryOutputRemoved` | true |
| `installed`, `gameplayFeatureInstalled` | false |
| `ordersSent`, `newGameFilesWrittenByThisRunner` | 0 |

**Вывод:** Впервые нативный WeiDU установленной игры принял точный source-only BAF V3 с `XEquipItem("STAF01",Myself,SLOT_WEAPON0,EQUIP)` (одноразовое правило с actor LOCALS). Компилятор распознал имена триггеров/действий/слотов и сформировал BCS. Это не является доказательством выполнения команды, её безопасности или сохранения APР/текущего раунда. Предыдущий `HOLD_PINNED_DOWNLOAD_OR_HASH_FAILURE:KeyError,KeyError` устранён; старый пункт 175 и этот 176 **НЕ ПОВТОРЯТЬ**.

## Что ещё НЕ подтверждено

1. `runtimeActorIdentityVerified=false`: портрет/идентификатор Джагана и фактический инвентарь в текущей игровой сессии ещё не привязаны к сохранённому GAM.
2. `classKitItmUsabilityVerified=false`: успешная компиляция `STAF01` не проверяет в конкретной сессии ограничения класса/набора/предмета.
3. `safeActionBoundaryVerified=false`: `ActionStarted` существующего EEex R37 и `ActionListEmpty()` не доказывают, что сейчас можно безопасно вставить приказ. Атаки идут раундами; нельзя прерывать текущую атаку.
4. `manualEpsOriginVerified=false`: указатель источника действия в R37/Q81 лишь необработанный код, а не доказанный приказ игрока/EPS.
5. `engineTransferVerified=false`: никто не сделал реальный перенос `STAF01`, поэтому не доказаны сохранение экземпляра, зарядов, эффектов или повторное отсутствие исполнения.
6. `wholeGameTreeChecked=false`: мониторились оговорённые файлы, не всё дерево игры.

## Следующее минимальное действие без изменений игры

Текущий `BGXAI_SYNC.ps1` содержит существующий **174** — status/preflight/capture для R37. Чтобы не перепрыгивать, прежде чем готовить игровой тест, нужно узнать **какой наблюдатель действительно установлен**. На закрытой игре в единственном `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd` выбрать **174 → 3 (status)**. При `R37_PRESENT_LAST_PASSIVE` можно проектировать следующее одноразовое **read-only** runtime-снятие; при `R33_PRESENT_LAST_BEFORE_R37` либо `R37_HOLD_UNKNOWN_GAME_STATE` — **HOLD**, без установок и без догадок о доступности R37. Ничего не устанавливать и не откатывать без typed разрешения. От пользователя нужен лишь новый JSON статуса или точный текст STOP.

R34 умеет извлекать сырые данные ITM/владения оружием, но явно ставит `characterCanEquipVerified=false`; это **не готовое доказательство**, что Джаган вправе экипировать предмет. Использовать текущие методы, не создавать второй updater или callback.

## Разделение статусов

**CODE=PASS; CI=PASS; NATIVE_EET=PASS; R37_INSTALLED_STATUS=UNKNOWN; RUNTIME_SAFE_BOUNDARY=HOLD; ITEM_USABILITY=HOLD; DEPLOY=NO; LIVE=NO.**

Не трогать EPS, R29/V6, BG_EET_RU, BG Voice RU, game override, WeiDU.log или сейвы. Внешний backup и typed согласие обязательны для любого будущего установки игрового скрипта.