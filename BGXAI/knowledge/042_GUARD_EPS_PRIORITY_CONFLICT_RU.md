# BGXAI 042 — конфликты охраны и автоатаки EPS
Дата 2026-11-07. EET Foxx, EPS 18.4, BGXAI 0381+039+040+041.

## Факт в игре
Пользователь сообщил: «работает если отключить атаку врагов и сценарии». Название конкретного второго переключателя неизвестно; не предполагать, что глобальный AI выключен. В игре охрана и значок 041 уже работают при отключении конкурирующих EPS-поведений.

## Причина в собственных исходниках
- BGX38 EXTEND_BOTTOM BDDEFAI.BCS: Guard flag 1 + ActionListEmpty() + ProtectObject(Player1,6).
- BGX39 также EXTEND_BOTTOM, 10 защитных условий с ActionListEmpty(), с ProtectObject для Player2–Player6.
- EPS атакующие блоки стоят раньше; долгосрочная Attack или AttackReevaluate может не освобождать очередь. IESDP: даже переоценка AttackReevaluate сама по себе не делает ActionListEmpty истинным.
- BGX40 и BGX41 меняют только F и текст/значок — не боевые приоритеты.
- Видимый значок означает установленный LOCALS-флаг, а не гарантию, что защита выполняется.

## Техническая задача следующей версии
Нужен 042 контроллер приоритета охраны для actor с BGX38_GUARD=1, при этом сохранить остальные функции EPS, спасение/лечение, ручные команды, песни бардов и касты. Не применять безусловный ClearActions. Не ограничиваться перестановкой EXTEND_BOTTOM -> EXTEND_TOP с прежним ActionListEmpty — очередь всё равно может быть занята. Не убирать ActionListEmpty повсеместно без проверки прерывания кастов и ручных приказов.
Сначала снять и изучить реальные верхние блоки установленного BDDEFAI.BCS и EPS `Атаковать врагов`, затем создать отдельный безопасный кандидат 042 с WeiDU backup/rollback, тестировать EPS attack ON vs OFF, охрану нескольких союзников, касты и песню барда.

Текущую 041 не откатывать и не переустанавливать. Временный режим: в индивидуальных настройках EPS отключить конфликтующую автоматическую атаку для охранника; глобальный AI отряда оставить включённым, иначе скрипт BCS не будет исполняться.

Справка IESDP BG(2)EE Actions — ProtectObject, ActionListEmpty, AttackReevaluate: https://gibberlings3.github.io/iesdp/scripting/actions/bgeeactions.htm
Другая обязательная незакрытая задача — русский перевод фактического расширенного боевого журнала с расшифровкой бросков d20, THAC0/КД и бонусов.

### Уточнение пользователя — НЕ считать механизм доказанным
Позднее пользователь уточнил: «работает не знаю она включается тогда когда выключена атака врагов». Это осторожное наблюдение, а не подтверждение точной причины. Не доказано, что при включённой автоатаке перестаёт работать именно защитное поведение: возможно, не срабатывает само переключение F (текст и значок), либо срабатывает переключение, но не выполняется ProtectObject.
Принципиально важно: 040/041 F HotKey-блоки EXTEND_TOP и НЕ содержат ActionListEmpty(); этим нельзя объяснять несрабатывание переключателя F. Напротив, 038/039 защитные блоки EXTEND_BOTTOM требуют ActionListEmpty(), поэтому их вытеснение автоатакой — разумная гипотеза только о *защитном действии*, не о горячей клавише.
В будущей 042 диагностике отдельно проверять события F (BGX38_GUARD и текст/иконка) и применение ProtectObject, не утверждать проверенный механизм до игровых данных. Пользователь устал от многократных тестов: по умолчанию не требовать новые прогоны. Текущий безопасный обход: выключить EPS `Атаковать врагов` только у охранника, общий AI оставить включённым; остальным разрешена атака.

### 2026-11-07 20:51 — Shank vs Jade: dual F guard ON AND EPS attack enemies ON; cannot attribute fight to guard
User provided TWO gameplay screenshots, one combat log and one EPS scenario configuration screen, and states `включил у двоих охрану ... гном пошел дратся теранн чуть позже ? у обоих вкл атаковать врагов`. In combat log Shank attacks Jade, critical hit and 2 piercing damage; Tarana activated Barbarian Rage, attacked Shank twice, did 16 crushing damage, Shank died. Gnome Jagan Battleforge attacked Shank earlier per user. EPS `Атаковать врагов` enabled for both guardians, so attack actions can derive entirely from EPS, not proven `ProtectObject`. Tarana delayed by Rage is NOT proof of lack of protection.
User confusion is justified: external behavior of attacking threatened foe is indistinguishable between autoattack and guard in this screenshot. Do not claim successful guard or broken guard. Also `F` active on two NPCs is allowed but does not assign an explicit ward target: 0381/039 dynamic Player1 then Player3/4/5/6/2.
One discriminating isolated test only if user chooses: keep GLOBAL party AI on and same EPS AI script, turn off ONLY personal `Атаковать врагов` for the guardian(s), leave F on, let Shank aggro Jade. If defenders intervene this supports BGX guard. If no reaction investigate script priority, distance, ActionListEmpty. Do NOT require repeated fight loops or disable entire AI script via `НЕТ`.
Product requirement BGXAI 042: distinguish active mode icon vs actually issued protect command, coordinate with autoattack. Current 041 F+icon works in game, no need rollback/reinstall. In-game Russian detailed hit-roll translation still open.

### 2026-11-07 — USER CONFIRMED REAL GUARD PROTECTION WITH EPS ATTACK OFF
- After Shank vs Jade ambiguous combat, assistant requested ONE discriminating combat test: BOTH Tarana and dwarf have F Guard=ON, turn off ONLY personal EPS `Атаковать врагов`, keep overall party AI running, let enemy attack Jade. User responded **`сработало`**.
- This is direct user-confirmed in-game evidence that BGXAI guard **protective action works under EPS autoattack OFF**, rather than an illusion caused by EPS attacking foes. No need to repeat this case.
- The mechanism when EPS attack ON is still not isolated/proven. Competing EPS automated attacks in earlier test both attacked Shank but could be autoattack or guard. Working hypothesis: EPS upper attack blocks vs BGX038/039 EXTEND_BOTTOM + ActionListEmpty may starve guard. Need test or implement safe priority arbitration in 042, with roles, spellcasting, bard songs preserved, without ClearActions/overriding manual control.
- Current stable live 041: F ON/OFF Russian feedback and portrait icon observed, plus 038/039 defense when attack OFF. No reinstall or rollback necessary. Temporary setting: personal autoattack OFF for guardians, overall party AI ON; unrelated party companions may retain own autoattack.
- Separate REQUIRED roadmap: in-game detailed attack-roll decoding/translation (d20, THAC0, AC/КД, modifiers). Standalone parser exists, runtime UI patch pending.
