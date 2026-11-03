# BGXAI — реальный Advanced AI `BDDEFAI.BCS` из пользовательской EET, структурный аудит
**Дата:** 2026-11-03. **Источник:** пользовательский архив `BALDURS_GATE_EET_AI/SOURCES/BG_EET_AUDIT_02_QUESTS_AI.zip`, файл **`BDDEFAI.BCS`** (override). Таблицы `ACTION.IDS`, `TRIGGER.IDS`, `SPELL.IDS`, `WEIDU_CURRENT.log` — из `BG_EET_AUDIT_01_MAGIC.zip`. Архив `scripts_USER_2026-10-31.zip` содержит 28 других .BS, **BDDEFAI там нет**; не путать с ним.

## Фактическая идентификация
- `BDDEFAI.BCS`: **489 880 байт**, SHA256 **`2d98605d2ee5a1d8abb17961f03f2ca9c9d48ea24a1007860e938f49c650165a`**.
- Реальные данные в файле: **644 CR-блока**, **5577 TR-условий** и **1022 AC-действий**, по числу открывающих записей BCS. Это **факты бинарного файла**, а не декомпиляция BAF с полными именами параметров.
- Частые действия (сопоставлено с `ACTION.IDS` этой установки): `SetGlobalTimer` 348, `SetInterrupt` 288, `Spell / SpellRES` 277, `SetGlobal` 59, `Continue` 13, `AttackOneRound` 10, `UseItem / UseItemSlotAbility / UseItemSlot` 8, `EquipMostDamagingMelee` 2, `EquipRanged` 1, `FindTraps` 1, `Hide` 1, `BattleSong` 1, `Turn` 1. Число записей действий НЕ означает число фактических применений в бою; один условный блок может срабатывать многократно.
- Частые условия: `StateCheck` 800, `CheckStatGT` 783, `Global` 461, `InParty` 408, `CheckStat` 389, `CheckStatLT` 364, `GlobalTimerNotExpired` 342, `ActionListEmpty` 313, `HaveSpell/HaveSpellRES` 286, `See` 237, `CheckSpellState` 215, `Range` 174, `OR` 161. Следовательно, текущий Improved AI действительно много внимания уделяет **доступности заклинаний, состояниям, очереди команд, таймерам и ресурсам**.
- Найдены управляемые переменные: `BDAI_DISABLE_DEFENSIVE`, `BDAI_DISABLE_OFFENSIVE`, `BDAI_DISABLE_SPECIAL`, `BDAI_DISABLE_ATTACK`, `BDAI_DISABLE_ITEMS`, `BDAI_NO_ARCANE`, `BDAI_SKILL_MODE`, `BDAI_ATTACK_MODE` и `BDAI_INIT_* `. Это фактические имена **настроек/локальных флагов в бинарном ресурсе**, не доказательство того, что каждый флаг уже учтён другими нашими скриптами.
- Выявлены собственные разделяемые переменные отдельных spell-групп `BD_Cast`, `BD_DInv`, `BD_Support`, `BD_Wand`, `BD_Hide` и другие.
- Из `WEIDU_CURRENT.log` подтверждён SCS 35.21 и улучшенный NPC customization (#4100), но запись **`Ease-of-use party AI` отсутствует**. Вероятнейший текущий базовый скрипт — штатный `BDDEFAI`, но его нельзя объявлять гарантированно побайтно ванильным без эталона соответствующего EE v2.6.6.0; override мог меняться другими компонентами.
  
## Доказанные и документированные принципы поведения
По Beamdog wiki/forums для стандартного Advanced AI доступны отдельные параметры Attack Enemies, Prefer Melee vs Prefer Ranged (или ни то ни другое), Use Items, Use Special Abilities, Use Defensive Spells, Use Offensive Spells; а также режимы Find Traps, Hide in Shadows, Sing Bard Song, Turn Undead. По документации Beamdog последний набор — **взаимоисключающие текущие модальные действия**: нельзя одновременно петь/искать ловушки/прятаться/изгонять, но можно хранить все разрешения и выбирать, что выполнять в моменте. Для выбранных сюжетных NPC штатные combat scripts иногда основаны только на исходном классе и неправильно реагируют на дуал: это важный недостаток, который наш BGXAI должен исправить фактическим определением класса/кита/активного уровня.

Внешние примеры для дальнейшей, явно отдельной, учебной сверки: `RichMartel/uscript` — улучшенная защита ручных приказов/ретаргетинг; `SarahG-579462/Enhanced-Powergaming-Scripts` — групповой prebuff, лечение без дублирования, выбор снятия защит, настройка меню. **Они НЕ заявлены установленными у пользователя и не подменяют анализ собственного BDDEFAI.**

## Что переносим в наш отдельный BGXAI
1. Схема независимых личных включателей, которые включаются на экране одного выбранного персонажа; не привязывать к имени или портретному слоту.
2. `ActionListEmpty` и защита команд игрока; таймеры/гистерезис; проверки `HaveSpell`, `CheckSpellState`, состояния, класса и способностей **до** выдачи действия.
3. Порядок принятия решения: опасность жизни -> не прервать ручное/боевое действие -> подтвержденное лечение/защита -> контроль -> отбор физической атаки -> мирные режимы.
4. Унифицировать возможности по классу+киту+мультиклассу+активному дуалу, а не создавать фиксированные отдельные AI для Ксара, Имоен и т.д.
5. Улучшить базовые правила: командные приоритеты и reserve slots; 3E sneak melee-only; безопасность маршрута и не сбивать invisibility; урон/резисты/касты по доказанным данным; использовать расходники только по пользовательским разрешениям.
6. Объединять **разрешения**, но **не одновременные несовместимые modal states**. Скрытность, поиск ловушек, песня и Turn Undead могут быть одновременно разрешены, но арбитр выбирает текущий режим. Не втискивать Turn/BattleSong/FindTraps в последовательный спам.
7. Не изменять установленный `BDDEFAI`; наш отдельный `BGXAI` должен переиспользовать идеи и проверенные API, не перезаписывать исходный файл. Учитывать лицензию внешних модов, не копировать большие куски без оснований.

## Степень проверки и следующий технический шаг
Выполнен фактический **бинарный аудит структуры и статистики** при помощи BCS-формата и игровых IDS; не выполнена полная декомпиляция BAF (нужны WeiDU/NearInfinity с правильной локализацией/компиляционным контекстом), игровой smoke-test и сравнение пошагового поведения. Следующая задача: разметить `BDDEFAI` по 644 ветвям, восстановить условия и действия с помощью ACTION/TRIGGER/OBJECT/SPELL IDS, проследить точные зависимости включателей/приоритетов, и сопоставить с `BGXAI/menu/BGX_UNIVERSAL_ARBITER_V03.js`; затем EEex read-only адаптер и меню.

## Источники
- Реальные файлы проекта, перечисленные выше.
- Advanced AI options and caveats: https://forums.beamdog.com/discussion/82536/is-there-a-way-to-customize-the-party-ai
- SCS Ease-of-use party AI behavior: https://gibberlings3.github.io/Documentation/readmes/readme-stratagems.html
- WeiDU biff-get/BAF decompile manual: https://weidu.org/WeiDU/README-WeiDU.html
- NearInfinity BCS decompilation: https://github-wiki-see.page/m/NearInfinityBrowser/NearInfinity/wiki/Documentation-Tools
