# BGXAI R27 — единый обновлятор, защищённое меню 165 — 23.11.2026

## Статус — 4 отдельные стадии

- **CODE:** PASS. Создан `BGXAI_R27_GUARDED.py` для R27 пассивного наблюдателя `M_BGXR27.lua`. Существующий `BGXAI_UPDATE.cmd` не изменялся.
- **TEST:** PASS. 21/21 тестов установщика на Windows и Linux, включая поддельный WeiDU, реальный исходный SHA и отрицательные сценарии. Windows PowerShell 5.1 syntax parse PASS, доставка через GitHub SHA256 pin PASS. GitHub Actions: https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45212630451.
- **DEPLOY В ИГРУ:** **NO.** Никаких игровых скриптов, WeiDU, EPS и сохранений в текущем сеансе не изменено.
- **LIVE R27:** **NO.** Нужен один защищённый preflight на пользовательской машине, затем отдельное typed подтверждение установки и реальный лог.

## Состояние единого обновлятора

- Существующий файл на компьютере пользователя: `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd` (не заменять и не скачивать новый CMD).
- Backend: `BGXAI/BGXAI_SYNC.ps1` branch `bg-eet-ai`, immutable commit `7177bff58f6f9bfe703147c29eaadb549aa4c386`, размер **79897 bytes**, SHA256 **`bac78ddf83fe4b87dce2a5d3b8568ef5062fea2591460a5e893c1026d4f5be18`**. Лимит старого CMD — 80000 bytes, пройден. Консольное отображение *старых* опций 1–69 сгруппировано, сами обработки опций 1–164 сохранены.
- `BGXAI/fox_new/BOOTSTRAP_PIN.json` теперь указывает на этот immutable commit/hash/size, обновление pin commit `24ae9184dee65f9feccee1a7a3ff8a4f747b4a96`. Bootstrap загружает только точный hash; не меняет игру при загрузке меню.
- Меню **165** добавлено **в существующий** `BGXAI_SYNC.ps1`; использует старый `SyncRelease` (manifest/commit/SHA check) и сохраняет source-only файлы в `BGXAI_DEV\weapon_r27_observer`.
- Release manifest: `BGXAI/BUILD/R27_SINGLE_CALLBACK_SELECTED_RO_20261123/manifest_updater.json`, version `0.3.89-R27-PASSIVE-GUARDED`; содержит **ровно два** файла: `BGXAI_R27_GUARDED.py` (SHA256 `83b0a23140ab04310e56e24ebaf32ed8b446724a65687ae987583d5cfa2c3268`, 14742 bytes) и `M_BGXR27.lua` (SHA256 `e5eb400c56ffb1bc23344a0cf30dcc724d8d18fc2752fabd1c2c63cdcca73735`, 28890 bytes).

## Пользовательский следующий шаг (ТОЛЬКО READ ONLY)

1. **Закрыть Baldur's Gate, InfinityLoader и WeiDU.**
2. Запустить только `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`.
3. В главном меню выбрать **165**; внутри R27 выбрать **2** (это значение по умолчанию — можно Enter).
4. Прислать **текст результата**. Ожидаем возможный `R27_PREFLIGHT_PASS_NO_INSTALL`, но **это не гарантировано**, поскольку актуальное состояние игровых файлов и последний WeiDU проверяются только у пользователя. Если видим `R27_STOP`, не устанавливать, не исправлять автоматически; исследовать конкретную причину.

После реального preflight PASS возможна **отдельная** установка из меню 165→3 с точной фразой `INSTALL_BGXAI_R27_PASSIVE_OBSERVER`. По умолчанию ENTER отменяет установку. Внешний SHA-верифицированный backup сохраняется в `Documents\BGXAI_BACKUPS`; runtime-only Lua `override/M_BGXR27.lua` ставится через WeiDU, требует TD15 **последним** в WeiDU.log, и не трогает текущий R13.2/TD15, R2, R4, EPS, BG_EET_RU и BG Voice RU. Откат через меню 165→4 с `ROLLBACK_BGXAI_R27_PASSIVE_OBSERVER` разрешён только если R27 сам последний WeiDU и проверена внешняя копия. Если WeiDU не последний — HOLD, без разрушительных исправлений.

## Что R27 НЕ доказывает

- Только APR **выбранного** оружия, наблюдения быстрых слотов, отсутствие автоматических приказов и один пассивный EEex started-action callback с ограничением до 64 событий.
- **Не** подтверждены альтернативный effective APR, расчёт всех эффектов, engine-native launcher/ammo pairing, lifetime/ABI item ability, идентификатор native event и гарантированно пустая очередь команд ручного управления/EPS.
- R27 **не переключает оружие** и **не включает** автоматическое оружейное управление. Для этого нужны отдельные доказательства и будущая согласованная разработка.

Постоянное правило проекта: при PASS продолжать следующие безопасные действия в этом обращении, не ждать `+`; не выдавать SOURCE/CI PASS за GAME/LIVE PASS и не обещать работу в фоне между сообщениями.
