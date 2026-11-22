# BGXAI — пункт 160: EEex R11 static preflight (READ ONLY)
Дата: 22.11.2026.
Статус: CODE_WIN_PS5_AST_PASS / TEST_PASS / PIN_PROMOTION_NEXT / USER_LIVE_NOT_YET_CHECKED.
Единственный пользовательский файл остаётся C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd, его содержимое НЕ менялось.

В существующий BGXAI/BGXAI_SYNC.ps1 добавлен пункт 160 без удаления и без семантического изменения обработчиков 1–159. Изменения прежнего кода — только альфа-переименование внутренних переменных ($releaseRanged->$rg и др.). Доказательство обратного преобразования: кандидат с удалённым пунктом 160 и восстановленными именами побайтово равен прежнему файлу (GitHub Windows CI).

160 скачивает из ТОГО ЖЕ immutable pinned commit файл BGXAI/patchsets/ranged_fighter_guarded_20261119/BGXAI_EEEX_R11_STATIC_COMPAT_RO_V2.py через существующий Get-PinnedBytes. Перед исполнением сверяет 6044 байта и SHA256 0b05e83a6a34bfc2b97be87d8b06761719b43ddaab39593a3863bf1f2317e316; временный скрипт создаётся эксклюзивно в %LOCALAPPDATA%\BGXAI_UPDATER и удаляется, никаких новых CMD не требуется. Скрипт читает установленную EET и выводит JSON в консоль; никаких установок, правок BCS/Lua/WeiDU/EPS/сейвов.

Новый BGXAI_SYNC.ps1: 79943 байта, SHA256 30b248b6d043580eeec32e243ecc529b51fa6299724a0f448b81c88060e0c1ed (ниже лимита 80000).
Старый BGXAI_SYNC.ps1: 79984 байта, SHA256 96bbc0f8ebb15be902535e63ae5afe0da81629f6dd93749a8a502683b679e8c8.
Windows CI:
- https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45041910485 — PowerShell 7 AST, Windows PowerShell 5.1 AST, 1–159 regression, 26 offline Python checks SUCCESS.
- https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45041871994 — source exact SHA256,size, AST and unit tests SUCCESS.

Даже если 160 выдаст STATIC_CALLSITES_FOUND_RUNTIME_NOT_PROVEN, это НЕ означает, что EEex API безопасен в игровом VM, что APR альтернативных слотов рассчитан, или что можно переключать оружие. R11/R12 остаются SOURCE_ONLY, автопереключение отключено.

Откат меню 160 требует только возврата BOOTSTRAP_PIN.json к прежним значениям commit=0811abcf0903c621b408997481ada0ee2009d9a9, script_sha256=96bbc0f8ebb15be902535e63ae5afe0da81629f6dd93749a8a502683b679e8c8, script_size=79984. Никакой WeiDU-откат не допускается и не нужен.
Правило: после безопасного PASS продолжать самостоятельно, но не менять игру без отдельного явного разрешения.
