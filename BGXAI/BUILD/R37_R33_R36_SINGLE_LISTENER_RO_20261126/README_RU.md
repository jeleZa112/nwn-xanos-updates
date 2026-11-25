## АКТУАЛЬНОЕ ОБНОВЛЕНИЕ: 26.11.2026 — пункт 174 В ЕДИНОМ обновляторе

Предыдущий текст ниже описывает состояние **до** выпуска меню 174. Сейчас **защищённая реализация подготовлена и включена в установленный пользователем единый путь обновления** `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`, но **R37 ещё НЕ установлен в игре**.

- Меню **174 — R37**, по умолчанию режим **1: preflight / READ ONLY**. Доступны 2: typed install, 3: status, 4: typed last-only rollback. Старые пункты 1–173 сохранены побайтно.
- Guard `R37_GUARDED_SOURCE_ONLY.py`: 19 107 байт, SHA256 `847d59d70f14274a005244b009850a8f563e2a302517e8237cdcb063bc23b9ab`. Подтверждение установки `INSTALL_BGXAI_R37_PASSIVE_ADVICE_AFTER_R33`, отката `ROLLBACK_BGXAI_R37_RESTORE_R33_ONLY`. Требует R33 installed last в WeiDU (152), проверяет SHA, создаёт внешнюю копию, использует native WeiDU; если установлен другой компонент, останавливается без правки игры.
- Lua R37: 60 835 байт, SHA256 `5ece282270f0e6a1fa7a6086b7f13c57c77de98759637efa4b2ab0cc1e5744d6`.
- **Фактический hard limit оригинального CMD 80 000 байт** учтён. Текущий SHA-pinned PS **79 701 байт**, SHA256 `5efb1648aa107f24bb785553e89f23bffa744c3220c1740e6b57d7303f64b71c`, immutable commit `52f73efaa2900b6cdee6ff0f428ae6744193fafd`. Для размера вынесены повторяющиеся константы манифестов; все 174 обработчика остались такими же.
- [Source guard 17 тестов на Windows/Linux — PASS](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45675195682). [Windows PS5.1, pinned SHA, старая 173-менюшка и лимит оригинального CMD — PASS](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45677080408). [Комплексный CI BGXAI 7/7 — PASS](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45677090975).
- **CODE/TEST PASS, DEPLOY/LIVE R37 NOT YET VERIFIED.** Важно: ни один тест выше не является доказательством работы в реальном бою. Переустановка R33, вторые CMD, ручное копирование в override и нетипизированная установка не нужны.

---

# BGXAI R37 — R36 внутри существующего единственного R33 обработчика, SOURCE ONLY

**Дата:** 26 ноября 2026. **Статус:** CODE+SOURCE/CI PASS; **NOT INSTALLED**, новый LIVE не получен.

## Цель и конкретный результат

После реального R33 (8 движковых событий) и R36 (изменение AROW01 20→19 и actionRaw 23→3) построен **рабочий исходный модуль** `M_BGXR27_R37_SOURCE_ONLY.lua` — целая, самостоятельная Lua-копия будущего `M_BGXR27.lua`, строго на основе R33 `M_BGXR27_R33_SOURCE_ONLY.lua` и неизменённого ядра R36 `BGXAI_R36_R33_ADVICE_INVALIDATION.lua`. Это НЕ отдельный мод и НЕ второй EEex observer.

**Было в R33:** один `EEex_Action_AddSpriteStartedActionListener`, R2+R4 double-read stats, original `[BGXR27]` console JSON. **Добавлено в R37:** в ТОТ ЖЕ callback после готового `R27.observe(...)` вызывается чистая `R36_CORE.capture(result)`, сравнение с предыдущим наблюдением того же party slot и безопасное текстовое событие `[BGXR37]`. **Осталось без изменений:** одна регистрация слушателя, 2 чтения `EEex_Sprite_GetActiveStats` за валидный callback, оригинальные данные `[BGXR27]` и вся игровая логика (в этом модуле её нет). Слот партии хранит только одну прошлую raw копию; максимум 6 ключей, максимум 64 события. Смена актёра и неполные данные возвращают HOLD, а старый совет аннулируется. Вторая попытка загрузить модуль в той же игровой сессии не регистрирует ещё один слушатель.

**Результат в одном прежнем консольном журнале:** каждая валидная запись `[BGXR27]` сопровождается дополнительной короткой `[BGXR37]` со статусом `R37_FIRST_R33_SAMPLE_NO_PRIOR`, `RAW_FIELDS_EQUAL_NOT_EFFECT_OR_EPS_PROOF`, `EQUIPMENT_OR_AMMO_CHANGED_INVALIDATE_ADVICE`, `ACTION_CONTEXT_CHANGED_INVALIDATE_ADVICE`, `OBSERVED_STATS_CHANGED_INVALIDATE_ADVICE`, `NATURAL_SELECTION_CHANGED_INVALIDATE_ADVICE` либо `R37_R33_CAPTURE_HOLD_NO_DISPATCH`. Нет raw actor ID или m_source pointer в добавочной записи. *Утверждать «0 в очереди = можно переключать» запрещено.*

## Как проверено

- Отдельный [R37 три-job CI](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45671377104): PASS Windows / Ubuntu SHA/no-new-listener проверка и PASS полноценного 60KB Lua-модуля на Lua 5.3, Lua 5.4 и LuaJIT.
- Тест `test_r37_single_listener_runtime.lua` фактически загружает полный исходник R37 (не обрезанный mock функции) с подставными EEex функциями; фиксирует **ровно 1 listener**, **ровно 2 stats reads**, прежние R33 JSON, расход стрел 20→19, смену действия и силы, HOLD при дрейфе, очистку старого advisory и **0 игровых приказов**. Отдельно повторяет `dofile` и проверяет, что ещё один listener НЕ создаётся.
- `test_r37_source_integrity.py`: 8 тестов на Windows+Linux, frozen исходник R33 `1420ef723df1090d56f8f6590fd82e5c69107ba97a39b2ca2ba73f93e0e77069` (SHA256), original R36 git blob `f7d4e11a219cd254a52a0f53f18582c9415223af`; точный единственный R36 core embedded, отсутствие новых Stats/EEex listeners и forbidden engine commands, неизменный pinned единственный updater `BGXAI_UPDATE.cmd`/backend.
- В том же workflow повторно подтверждены 27 R36 Python негативных тестов Windows и Ubuntu и 20 R36 Lua на трёх интерпретаторах.
- Новый R37 добавлен в **существующий комплексный BGXAI workflow**: V3/V4/V5 + R27–R37 + EPS 081 контекст + BGXP лечение + BGX120 AoE + дружеский огонь + PowerShell5.1 single updater.

## Почему нельзя пока классифицировать EPS/manual

Проверен [оригинальный код EEex Action.lua](https://github.com/Bubb13/EEex/blob/master/EEex/copy/EEex_scripts/EEex_Action.lua): `EEex_Action_AddSpriteStartedActionListener(func)` регистрирует слушателя, который при начале действия вызывается из EEex с sprite/action; отдельного подтверждённого поля «владелец приказа: игрок или EPS» в интерфейсе нет. Ранее R33 в игре вернул `ACTION_SOURCE_POINTER_UNAVAILABLE` для `m_source`. Даже когда поле возвращает raw строку, оно помечено `UNCLASSIFIED_CAI_ACTION_M_SOURCE`, не доказанный `manual`/EPS. Очередь `m_queuedActions.m_nCount=0` тоже не определяет безопасную границу смены оружия. Поэтому **никакой классификации происхождения или разрешения на приказ R37 не делает**.

## Что остаётся

1. **DEPLOY / LIVE R37:** ещё не выполнялись; официальный защитный install через единственный обновлятор потребует отдельной подготовки, SHA-префлайта, сохранения действующего R33, backup/last-only rollback и явно введённого пользователем разрешения. `M_BGXR27_R37_SOURCE_ONLY.lua` **не копировать в игру вручную**. Уже зарегистрированный в процессе R33 слушатель нельзя безопасно «заменить» вторым; понадобится новый игровой процесс после разрешённого WeiDU-замещения.
2. **Active weapon switch:** заблокирован. R37 не выдаёт `Stop`, `Attack`, `SelectWeaponAbility`, `ClearActions` и не меняет game state / EPS / WeiDU / Lua IN GAME.
3. **Незакрытые настоящие препятствия:** достоверное происхождение приказа EPS/manual, безопасный boundary атаки (смена оружия сбрасывает таймер), полные активные эффекты для обоих слотов одновременно и доказанная пара ammo→launcher. До этого останется пассивный совет, без диспетчеризации.

**Один `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd` сохранён.** BG_EET_RU, BG Voice RU и сохранения не изменялись.

