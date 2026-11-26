# CRITICAL CORRECTION — 26.11.2026 V3
Previous source-only Inventory Prep V1/V2 used **WRONG** `15..34` as backpack. In BG(2)EE 15..17 are QUICK ITEM, 18..33 are **16 backpack** slots, 34 is magical weapon. **Do not use V1/V2 for any executor or install.** Corrected CODE + Lua5.3 offline tests are at `BGXAI/BUILD/WEAPON_INVENTORY_CORRECTED_V3_20261126/`; V3 still source-only, NOT connected to R37, NO active equipment move. Source: BG(2)EE CRE v1 Item Slots https://gibberlings3.github.io/iesdp/file_formats/ie_formats/cre_v1.htm . IMPORTANT: the public `ITMSLOTS.2DA` page is **PSTEE ONLY** (44..47 slots NOT BG(2)EE). `BGXAI_BACKPACK16_R37_RO_V3.lua` requires action/selection/queue/script double check before/after reading 18..33, but cannot prove safe current attack boundary or manual/EPS source. V2 CI denylist regex had an unmatched parenthesis; repaired with selftest, see .github/workflows. V3 local LuaTeX 5.3 after fix: 13/13 mock PASS; GH Actions still pending independent verification. Old entries below are historical, not active implementation authority.

---

# 26.11.2026 — USER PRIORITY CORRECTION: V6 ALREADY REDUCED CLOSE-RANGE SHOTS; ADD INVENTORY-AWARE AUTO-EQUIP

**MOST RECENT USER INSTRUCTIONS, overrides older "remove remaining extra arrow" priorities:** The combat round has a duration; a shot queued/committed inside it may be mechanically impossible to cancel without breaking attacks. Earlier project already optimized this: **V5 observed up to 3 extra close-range shots, V6 installed 21 Nov cut to at most 1 shot then sword**, and R37 real 26 Nov verified autonomous bow→sword. **Do not touch / tune V6 or R29 unless direct evidence shows NEW attack orders AFTER contact**. Stop/ClearActions/cancel queue are not acceptable solutions; 6-second attack round and per-weapon initiative. V6 native DPLAYER two-block patch deliberately vetoes NEW duplicate `AttackOneRound` close range, cannot cancel prior actions. Reference `BGXAI/CURRENT/BGXAI_R29_V6_LINEAGE_REPAIR_20261124_RU.md`, `BGXAI/CURRENT/BGXRANGED7_FUNCTIONAL_DPLAYER_PILOT_RU.md`, live R37.

**NEW SECOND REQUIREMENT:** AI should also **look through inventory/backpack for a more appropriate situational weapon**, not just 2/3/4 quickslots, and autonomously equip it if genuinely better; shield, poisoned attacks, vs-immunity, APR, temporary buffs, target resistances and manual/EPS action preservation matter. Official BGEE IESDP confirms `XEquipItem("HAMM01",Protagonist,SLOT_WEAPON1,EQUIP)` is available; `EquipItemEx` doesn't move item and `FillSlot` can destroy existing slot item, must never use `FillSlot`. Inventory slots 15..34, quick weapons 35..38, offhand 9; class quickslots capacity verified per actor.

**CURRENT COMPLETED SOURCE ONLY / TEST (no game changes):** module `BGXAI/BUILD/WEAPON_INVENTORY_PREP_V1_20261126/BGXAI_WEAPON_INVENTORY_PREP_RO_V1.lua` reuses EEex R2 raw item accessor, scans backpack 15..34, and proposes a verified-model candidate to an **empty permitted** quickweapon slot, no overwrite, uses V3/V4/V5 provenance and extensive fail-closed checks. 18 synthetic Lua tests with no engine action, CI on Lua5.3+5.4 **[PASS 45762553756](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45762553756)**. `M.plan` remains source-only advisory `ordersSent=0`, no native live dispatch, no game installed. [Implementation/readiness README](../BUILD/WEAPON_INVENTORY_PREP_V1_20261126/README_RU.md).

**Next concrete engineering**: bridge backpack to existing R37 read-only callback WITHOUT another listener; reuse V3/V4/V5 effective scorer; safety-check *actual* XEquipItem transaction with unique instance/no quest/curse, item preservation, **first only empty quickslot**; later full-slot safe swap. Action origin/manual/EPS/protected queues must be proven; do not send actions/replace items now. One existing `BGXAI_UPDATE.cmd` only, typed approval / backup / last-only WeiDU for future LIVE; no BG Voice RU/BG_EET_RU/UI/save changes. No new real-game test is required from the user at this point.

---

# BGXAI — реальная следующая работа ПОСЛЕ R37 LIVE (26.11.2026)

**Верхний приоритет: улучшить уже РАБОТАЮЩИЙ автономный выбор вооружения; не добавлять ради версии очередного наблюдателя и не ломать R29/V6.** Этот файл — проектное решение / acceptance gates, НЕ новый устанавливаемый патч и НЕ доказательство улучшения в игре.

## Доказанные исходные условия из пользовательской реальной EET

- Игрок давал ручные команды только ДО начала боя, но не в течение боя. Халид сам изменил выбранное оружие с `selectedWeaponRaw=12` (стрелы `AROW01` из `BOW05`) на `selectedWeaponRaw=35` (`SW1H04`), а `SHLD03A` был в offhand-слоте 9 на всех снимках до/после. Нет свидетельств отдельного приказа на щит.
- `BGXAI_R37_CONSOLE_20261126T050555209778Z.log`: seq7 `actionRaw=105` (`AttackOneRound`), selected 12, ammo 20, `currentScriptNumberRaw=3`; seq8 `actionRaw=92` (**`SelectWeaponAbility`**), selected ещё 12, ammo уже **18**, script 3; seq9 `actionRaw=134` (`AttackReevaluate`), selected уже **35**, script 5; seq10 `actionRaw=105`, selected 35, script 6. `queuedActionsRaw=0` во всех, но это НЕ доказательство пустого активного действия. Источник action 92 EPS vs R29 точно не подтверждён (origin UNKNOWN).
- В этом бою был близкий выстрел с **`Дистанция: -8`**, который закончился промахом; другая стрела попала, нанеся 1 метательного урона. Далее меч нанёс **9 рубящего урона**, враг погиб. Значит, конкретная цель улучшения — устранить ИЗБЫТОЧНЫЕ НОВЫЕ стрелковые команды на ближней дистанции, а не прерывать уже летящую стрелу.
- APR selection raw `2` = **2.0 атаки/раунд** для лука, raw `7` = **1.5 атаки/раунд** для меча (декодер проекта уже существует). Нельзя численно сравнивать 7 > 2 или два разных контекста как финальные альтернативы.
- `BGXRANGED6` (DPLAYER.BCS) и `R29` (BDDEFAI.BCS) уже отмечены как установленные в канонической истории; скрипты РАЗНЫЕ, но overlap по поведению. R29 `BGXAI_R29_KHALID_BOW_TO_SWORD.baf` требует `ActionListEmpty()`, `MO_SpellCast`, F guard, class FIGHTER, именно `SW1H04/BOW05/AROW01`, врага в `Range(...,6)`, и выполняет ОДИН `SelectWeaponAbility(SLOT_WEAPON0,0)`. V6 исходный кандидат `BGXRANGED_V6_DPLAYER_CLOSE_GUARD_SOURCE_ONLY.baf` ограничивает два DPLAYER блока с `AttackOneRound` вблизи и НЕ отменяет существующее действие. Отдельная серверная копия .baf с SOURCE ONLY не заменяет факта установленного ранее эквивалентного BCS; состояние сравнивать по уже сохранённым хешам, не верить имени .baf.
- R37 passive LIVE PASS: 12 оригинальных callback и 12 advisory, 12/12 seq+party, 0 malformed, 0 orders, 7 invalidations включая 1 init, `actionOrigin=UNKNOWN`, `safeActionBoundaryVerified=false`. Еще одну копию R37 не устанавливать.

## Этап 1. Локализовать отправителя команды 92 в УЖЕ записанном бою

1. Просмотреть исходники/компиляционные блоки `BDDEFAI.BCS`, `DPLAYER.BCS`, R29 и EPS 18.4 (сохранённые live evidence/технические артефакты, не переустанавливать).
2. `currentScriptNumberRaw=3` у seq7 и seq8 — **только цифра**. Не объявлять её идентичностью `BDDEFAI` или `DPLAYER` до сверки с EEex script-slot mapping. Установленный R29 `SelectWeaponAbility` — сильный кандидат, **не доказанный источник**.
3. Если реальный отправитель уже переключает без сбоя, не дублировать даже новым Lua-перехватчиком. Отдельный unknown source блокирует потенциально конфликтующий активный switch.

## Этап 2. Малое функциональное улучшение без нарушения очереди

- Работать в существующем native BCS/R29-V6 контуре: **раньше предотвращать выдачу НОВОГО ненужного дальнего AttackOneRound вблизи**, но НЕ `Stop()`, `ClearActions()`, `Attack()` и не ускорять переключение путём прерывания уже выполняемой атаки.
- Прежде чем менять threshold 6 / 10, проверить, что BCS trigger обращается к ТОМУ ЖЕ врагу и что он активный/агрессивный, а range/hysteresis не приводит к метанию лук↔меч или бегу в опасный AoE.
- Ручной приказ, EPS heal/buff/cast, погибший/невидимый/дружелюбный target, паника, проклятое или недоступное оружие → **пропуск**, а не принудительное переключение.
- Добавлять только минимальное изменение, которое действительно делает поведение лучше, после source regression и разрешённой установки с внешним backup/WeiDU last-only; до доказательства этих условий **никаких игровых записей**.

## Этап 3. Универсальный выбор оружия для всей партии, а не только Халида

- Переиспользовать существующие V3 priority, V4 effects, V5 APR, NONINTERRUPT, R32 tables, R34 ITM, R35 current selected stats; не переписывать уже готовое. Провести надёжную связку launcher↔ammo, проверку активного класса/кита дуалов и мультиклассов, и фактических effect+APR выбранного/альтернативного слота. Не подменять живые значения офлайн-прогнозом.
- Поддержка дротики ↔ меч, праща + бонусы силы, отравленные боеприпасы, иммунитеты и магические эффекты, THAC0, APR с владением и бафами, штраф близкой дистанции, выбор обороны/щита, экономия расходников.
- Для слабых магов/воров в опасных AoE — предпочтение дистанции/отступления; для устойчивых воинов — ближний бой по сцене, не автоматический преследователь в паутину.
- Пересчёт оценки оружия не останавливает текущую атаку, лечение или каст, а ожидает подлинно безопасную границу действий.

## Порядок/критерий приемки

**Сейчас:** игроку НЕ требуется повторять R37 capture, R29 install или V6 install. На уровне реальных сохранённых исходников исследовать право на команду 92 и почему близкий выстрел смог произойти. До обнаружения конкретного источника и безопасного изменения — CODE/ANALYSIS, не обещать DEPLOY.

**Следующий тест ТОЛЬКО после рабочего, проверенного минимального патча:** отдельный typed install в ТОМ ЖЕ `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`; внешняя копия, SHA, WeiDU last-only. Live A/B на сохранении с тем же сценарием: лучник начинает огонь издалека, враг подходит; фиксировать число **новых** стрелковых приказов на дистанции melee и время/порядок `105→92→134→105`, отсутствие лишних выстрелов с `Дистанция:-8`, отсутствие простоя/прерывания уже начатой атаки, правильное использование `SW1H04` и штатного щита, возврат к луку на безопасной дистанции; сравнить с нынешним **исходным** R37. Не обещать ноль потерянных кадров без доступных timestamp/движковых снимков.

**Не трогать:** EET/EPS/пользовательские сейвы, BG_EET_RU, BG Voice RU, working heal/AoE/friendly guard, оригинальный CMD до готового минимального patch и его тестов.

### Документация кодов действий

- IESDP BG(2)EE ACTIONS: https://gibberlings3.github.io/iesdp/scripting/actions/bgeeactions.htm
- Script action 92 = SelectWeaponAbility; 105 = AttackOneRound; 134 = AttackReevaluate.
