# BGXAI — исправление источника выбранного APR: EEex derivedStats vs tempStats (24.11.2026)

**Только исходники. Не установлено в EET, EPS, EEex, WeiDU или едином обновляторе.**

## Новый факт в официальном EEex v1.1.7

`EEex/copy/EEex_scripts/EEex_Sprite.lua`, `EEex_Sprite_GetActiveStats(sprite)`:

```lua
return sprite.m_bAllowEffectListCall ~= 0 and sprite.m_derivedStats or sprite.m_tempStats
```

При `m_bAllowEffectListCall == 0` это **временные данные внутри обработки эффектов**, а не стабильные окончательные stats. Отсутствие/необычное значение этого поля нельзя трактовать как проверенный результат. API возвращает характеристики **текущего** выбранного оружия, а не пер-слотовый APR альтернатив.

Upstream: https://github.com/Bubb13/EEex/blob/v1.1.7/EEex/copy/EEex_scripts/EEex_Sprite.lua

## Что изменено

1. В существующий `BGXAI_WEAPON_ACTIVE_R4_READONLY.lua` добавлен `observeStableDerived` **без изменения старого** `observe`: проверка `m_bAllowEffectListCall == 1` до и после каждого чтения; два чтения всех 68 raw-полей R4; сравнение APR, THAC0, STR, proficiency, haste, class, kit и остальных полей; повторная проверка действия/selection **после последнего чтения** (иначе гонка остаётся). Любое несовпадение → HOLD; текущая атака не прерывается. Это не полная проверка всех бафов.
2. Старый **неустанавливаемый** кандидат `BGXAI_R27_R2_REFRESH_SOURCE_ONLY.lua` теперь использует `R4_CORE.observeStableDerived` вместе с двойным чтением raw inventory. Результат содержит `selectedDerivedStatsDoubleReadConsistent=true` только при стабильной выборке; в bounded консольном JSON это отдельное булево поле, рядом строго сериализуется `r4Status`, чтобы R6 мог отвергать записи от временного stats-пути. Никаких новых callbacks, авто-слушателей и engine writes.
3. Существующий кэш исторических selected APR `R6.observe_r27` теперь **не принимает** запись без `selectedDerivedStatsDoubleReadConsistent==true` и строго ожидаемого `r4Status`.
4. Сохранён старый установленный `M_BGXR27.lua` SHA256 `e5eb400c56ffb1bc23344a0cf30dcc724d8d18fc2752fabd1c2c63cdcca73735`, ни одной переустановки не делалось. `BGXAI_UPDATE.cmd` и PIN неизменны.

## Локальная проверка

- R4: 49/49 тестов под LuaTeX (`luatex --luaonly`).
- R27 refresh: 65/65 тестовых условий под LuaTeX; Python 8/8 строгих проверок сборки/старого установленного sha.
- R6: 18/18 расширенных локальных условий чтения R27 под LuaTeX; 14/14 в опубликованном CI на каждом из трёх Lua. Исходные 28 R6 legacy и реальные 16 событий не изменялись.
- GitHub Actions https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45443795441 — **SUCCESS Windows + Ubuntu**; Lua 5.3, Lua 5.4, LuaJIT: R4 49/49, R27 65/65, R6 14/14, прежние V3 439-case регрессии; Python 8/8 PASS.

## Ограничения

`CODE/LOCAL TEST PASS`, `DEPLOY NO`, `LIVE NO`. Нет native proof для alternative effective APR, engine launcher+ammo, полной истории временных эффектов, ручных/EPS приказов. Ни один из обновлённых модулей не уполномочен отправлять действия, выбирать оружие или считать исторический APR альтернативы текущим. Следующий настоящий P0 остаётся **native/current alternate effective stats + EPS/manual provenance**. Для нового поведения нужна отдельная согласованная guarded установка с внешним backup.
