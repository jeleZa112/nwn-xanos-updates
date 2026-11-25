# BGXAI R32 — реальный WSPATCK/CLSWPBON из EET, READ ONLY

## ДОПОЛНЕНИЕ: EEex engine-resolved 2DA и CI PASS (25.11.2026)

**R32 engine API adapter уже реализован:** `BGXAI_R32_EEEX_ENGINE_2DA_RO.lua`. Использует документированный `EEex_Resource_Load2DA("WSPATCK")` и `EEex_Resource_Load2DA("CLSWPBON")`, считывает `C2DArray:getDimensions(), getColumnLabel(), getRowLabel(), getAtPoint()` с точными 0-based индексами; **EEex размер X включает столбец меток строк**, поэтому число значений = sizeX−1. Это позволяет читать и ресурсы BIFF внутри игрового движка. Официальный источник: [Bubb13/EEex EEex_Resource.lua](https://github.com/Bubb13/EEex/blob/master/EEex/copy/EEex_scripts/EEex_Resource.lua). API вызывается только в будущей игровой интеграции; здесь `M.observe(classRow,rank,level,loader)` является SOURCE ONLY. Нет ни новых слушателей EEex, ни оружейных приказов, ни изменения игровых файлов. Возвращает только `ENGINE_RESOLVED_APR_TABLE_CANDIDATE_READ_ONLY`, не подтверждает active dual class, equip-state, allEffects, effective APR других слотов и не даёт dispatch.

**CI:** [BGXAI R32 read-only Windows/Linux/EEex Lua CI 45643546399](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45643546399) — **SUCCESS**: Python 3.12 unit on Windows and Ubuntu и имитация C2DArray на Lua5.3/Lua5.4/LuaJIT. Отдельно проверены бонусы и значения `GETS_PROF_APR`, ошибки структуры, недоступные API и запрет engine orders. **Это не LIVE EEex runtime**, а синтетический native-language тест.

**Незакрыто:** классы/мультиклассы/дуалы должны быть подтверждены в текущем состоянии реального актёра; связь weapon type→proficiency; учёт бафов/магических эффектов, предметов, APR двух рук и active engine stats каждого альтернативного слота. Не внедрять в боевую логику до решения этих блокеров. Старый live R31 оставить установленным, не повторять capture.

---


## Цель без повторной разработки V3/V5

Имеющийся `BGXAI_WEAPON_APR_PROVENANCE_V5.lua` уже проверяет итоговый APR и защиту от двойного добавления бонусов, но **не читает установленные WSPATCK.2DA и CLSWPBON.2DA**. R32 — только недостающее звено чтения и проверки таблиц EET. Он **не содержит второго механизма выбора оружия**, не меняет живой R31, WeiDU или EPS.

### Механика, которую программа должна соблюдать

- `WSPATCK.2DA` кодирует **добавочный APR**: `-1 → +0.5`, `1 → +1`, `-2 → +1.5`; это не итоговое число атак за раунд и его нельзя второй раз прибавлять к финальному APR, возвращённому движком. Источник: [IESDP WSPATCK](https://burner1024.github.io/iesdp/files/2da/2da_tob/wspatck.htm).
- `CLSWPBON.2DA` содержит `GETS_PROF_APR`, определяющий право класса на бонус; таблица также содержит `UNARMED_DIVISOR` и `ZERO_SKILL_THAC0`, которые не следует принимать за APR. Источник: [IESDP CLSWPBON (BG2EE)](https://burner1024.github.io/iesdp/files/2da/2da_bgee/clswpbon.htm).
- Результат class+pip+level — **только условный табличный бонус**. Для реального персонажа ещё нужны проверенные класс/кит, активность дуала/мультикласса, соответствие вида оружия навыку, точный режим использования, прочие бонусы от предметов, заклинания, Haste/Improved Haste, APR в обеих руках, а также движковый APR другого слота. **Нельзя выдавать результат R32 за финальный APR или автоматически переключать оружие.**
- Вместо догадок о содержимом BIFF/KEY R32 читает только два конкретных файла `override/WSPATCK.2DA` и `override/CLSWPBON.2DA` из переданной игры. Если какого-либо файла нет в `override` — честно возвращает `HOLD_*NO_BIF_FALLBACK`. Не скачивает и не подменяет таблицы. В будущей версии отдельно подключить уже проверенный, неизменяющий игру ресурсный загрузчик.

## Состав

- `BGXAI_R32_APR_EET_TABLES_RO.py` — разбор 2DA V1.0, SHA256 обоих файлов, отказ при неоднозначных строках, нецелых кодах, отсутствующих классах/уровнях/рангах, отсутствии таблиц; вывод JSON только в консоль.
- `test_r32_apr_eet_tables_ro.py` — синтетические тесты структуры IESDP, плюсы/минусы APR, мультиклассы, неизвестный источник, отсутствие таблиц, отсутствие разрешений, защита от записи.
- `.github/workflows/bgxai-r32-apr-installed-tables-readonly.yml` — Windows/Linux Python 3.12, AST + unit.

## Статус

**CODE: подготовлен; CI: проверять отдельно; DEPLOY R32: NO; GAME FILES: UNCHANGED**. Это промежуточная инфраструктура для V5, не новая команда пользователю и не пункт обновлятора. Никаких отдельных bat/ps1 для пользователя. Продолжать с интеграции чтения установленных таблиц в прежний единственный обновлятор *без* установки и с SHA guard, когда проверены все существующие контракты.

## Важная реальная точка

R31 live capture 25.11: 12/12 событий с `queuedActionsRaw=0`, одно `actionRaw=3` при реальном выстреле. Следовательно, ноль очереди — **не** разрешение на переключение. R32 вообще не участвует в движковых командах и не меняет этот вывод. Источник: `BGXAI/CURRENT/BGXAI_R31_LIVE_VERDICT_20261125.json`.
