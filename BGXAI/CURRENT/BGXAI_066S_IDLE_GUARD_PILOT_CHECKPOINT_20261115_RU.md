# BGXAI 066S — первый минимальный потенциально игровой патч выбора незанятого охранника (15.11.2026)

**Игра не изменена.** Последнее реально подтверждённое состояние пользователя: BGXAI 066S, Lua SHA256 `50640902ec4c25a2c85e5088d7231678b54445a847b41743c476974236d1d70f`, BCS SHA256 `fb435d82e6c3e0ebea1d6a9532753921bd5411d70ac0677dc1fd8ec483380476`, EPS 18.4 / EET / SCS 35.21 / EEex 1.1.7. Оригинальный BCS не затрагивается.

## Причина новой приоритетной цели
Официальная IESDP BGEE: `ActionListEmpty()` true только при отсутствии действий; `AttackReevaluate()` может поддерживать действующую атаку постоянно и `ActionListEmpty()` не становится true. Lua 066S всегда выбирает ближайшего F-включённого бойца из CLASS.IDS 2/6/12, поэтому при двух защитниках занятый ближайший может получить единственную BCS-заявку, а свободный дальний не получит. Это гипотеза для настоящего игрового сравнения, НЕ доказанная причина пользовательского эпизода.

## Реализовано и проверено
Узкий Lua-патч к **побайтно точному** live M_BX43.lua 066S: в существующем выборе защитников читаем `sprite.m_curAction.m_actionID` через `pcall`; `0` используется только как предпочтение при сортировке, НЕ как подтверждение незанятой очереди EPS или происхождения ручного приказа. Другие состояния/ошибки не маркируются как свободные. При одинаковом hint сохраняем прошлую сортировку distance/slot. Два участка исходника изменены, остальные без изменений. Новый Lua SHA256 `2bf43c6ce4d607c13ce1aaf5a6af34810e0d4e81e2272c7a37dce384b6413e1a`.

**Не менялись:** EPS/BCS, Lua hooks/listeners, F toggle, BCS ActionListEmpty/ModalState/HaveSpell, лечение, бафы, песни, ловушки, автоматические заклинания или действия игрока. Ни одного нового Attack/Spell/ClearActions. Ещё не расширены роли/киты/дуалы. При единственном занятом охраннике это не решает старую задержку.

Доказательства: реальные native Lua5.4 mock tests **18/18 old + 17/17 changed legacy + 15/15 new**; original OLD chooses nearest busy, new chooses more distant idle; one red-green acceptance, no writes beyond old BCS request. `verify_release.py`: **15/15 SHA256**, EXACT_TWO_REGION_DIFF, original EEex listeners unchanged, no new engine actions; `texlua parse.lua` PASS; fresh ZIP extraction + all checks repeated PASS. Это тесты на имитации EEex, не реальный EET gameplay.

Архив `BGXAI_066S_IDLE_GUARD_PILOT_SOURCE_ONLY.zip` SHA256 `5902dd32d0a66b4f5468baa9985c236bdf2bac07ea73b7935b67d4b424da78e8`, 45238 bytes, 16 files. Главный кандидат `M_BX43_066S_IDLE_GUARD_CANDIDATE.lua`.

**Крайне важно:** НЕ устанавливать исходный ZIP напрямую! Пока отсутствует отдельное согласие на изменение игры и WeiDU-совместимый установщик с внешним проверенным backup/rollback и SHA pin. Сначала один ограниченный игровой A/B тест при согласии пользователя с двумя F-включёнными охранниками: ближайший в EPS автоатаке, дальний свободен, враг попадает по магу; измерить эффективность, EPS buffs/спеллы/ручные приказы; при проблемах немедленно откат. До этого installed=066S, candidate=SOURCE ONLY.

Документация движка: https://iesdp.bgforge.net/scripting/triggers/bgeetriggers и https://iesdp.bgforge.net/scripting/actions/bgeeactions .
