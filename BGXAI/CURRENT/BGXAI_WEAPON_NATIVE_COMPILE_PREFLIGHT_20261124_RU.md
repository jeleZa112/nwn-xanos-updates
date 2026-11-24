# BGXAI — новый безопасный native WeiDU preflight для восьмиветочного выбора оружия

**Дата:** 24.11.2026. **Статус:** SOURCE/LOCAL TEST PASS. **DEPLOY NO / LIVE NO.**

## Реальный результат

После предыдущего source-only `BGXAI_WEAPON_SLOT_CONSUMER_V3.baf` (8 веток, SHA256 `7d8c615894b21674be7624d6d1a61b0b42ad92f116e8cd5f9f5db1b7f7a52911`) подготовлен новый **отдельный read-only preflight**, а не ещё один ранкер или альтернативный установщик:

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