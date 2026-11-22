# BGXAI — пункт 160 опубликован через единственный обновлятор

Дата: 22 ноября 2026. Статус: `CODE_WIN_PS51_PASS / PIN_PUBLISHED / AWAIT_USER_READONLY_SCAN / NO_GAME_INSTALL`.

## Подтверждённая публикация

- Ветка GitHub: `bg-eet-ai`, PIN promotion commit `89d629c51d5c7526b9d76d6f23886ef3751d4f52`.
- PIN: `BGXAI/fox_new/BOOTSTRAP_PIN.json`, указывает на **неизменяемый** release commit `6b26d44770a14aeb63277e17e14e91796bcce56c`.
- Один штатный Windows CMD: `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`. CMD **не менялся**; bootstrap самостоятельно считывает новую запись PIN.
- Новый `BGXAI/BGXAI_SYNC.ps1`: **79943 байта**, SHA256 `30b248b6d043580eeec32e243ecc529b51fa6299724a0f448b81c88060e0c1ed`. Лимит существующего bootstrap 80000 байт.
- Новый пункт `160 - Weapon EEex R11 static compat READ ONLY`; старые `1..159` семантически неизменны (проверено Windows CI обратным преобразованием исключительно коротких имён переменных).
- Сканер: `BGXAI/patchsets/ranged_fighter_guarded_20261119/BGXAI_EEEX_R11_STATIC_COMPAT_RO_V2.py`, 6044 байта, SHA256 `0b05e83a6a34bfc2b97be87d8b06761719b43ddaab39593a3863bf1f2317e316`. Он скачивается из того же закреплённого release commit с проверкой длины и SHA256, запускается из временного кеша пользователя и затем удаляется.
- Проверки GitHub Actions: `45041910485` (Windows PowerShell 5.1 AST + PS7 AST + 1–159 regression + 26 Python tests **SUCCESS**) и `45041871994` (точные размеры и SHA256 **SUCCESS**).
- В игру не устанавливались R11/R12; WeiDU, V6, EPS 18.4, сейвы, действующие R1–R4 и одобренный updater CMD не изменены.

## Единственное действие пользователя сейчас

1. Закрыть игру и InfinityLoader.
2. Запустить обычный `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`.
3. В главном меню выбрать **160**.
4. Прислать в чат полный вывод с полем `status`, включая сообщения `STOP` в случае остановки.

Пункт 160 только читает `chitin.key`, `EEex_scripts/B3AttackInfo.lua`, `EEex_scripts/EEex_Action.lua`, установленные пассивные R1/R2/R4 и bootstrap EEex. Не меняет установку. Возможный успех `STATIC_CALLSITES_FOUND_RUNTIME_NOT_PROVEN` — **не** LIVE доказательство EEex VM и не разрешение переключения оружия. `HOLD`/`STOP` не требует переустановки; анализировать отчёт адресно и без повторных пройденных тестов.

## Дальше

Автоматически анализировать результат статического сканирования. Если успешен, подготовить следующий безопасный read-only игровой этап R11/R12 с однозначной проверкой цели/оружия и защитой EPS/manual, но любое изменение файлов игры — только после отдельного typed approval и внешнего backup. Не запрашивать повторно существующий отчёт `159->3` или тесты R1–R4.

## Резервный канал

Предыдущий pinned источник при необходимости доступен по commit `0811abcf0903c621b408997481ada0ee2009d9a9`, SHA256 `96bbc0f8ebb15be902535e63ae5afe0da81629f6dd93749a8a502683b679e8c8`, 79984 байта. Для отката пункта 160 достаточно восстановить **точные** значения старого канального PIN после диагностики; не требуется и не допускается ручной WeiDU rollback.
