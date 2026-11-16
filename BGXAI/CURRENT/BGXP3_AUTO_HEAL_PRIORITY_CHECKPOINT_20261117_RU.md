# BGXAI — AUTO лечебный приоритет / BGXP3 (17.11.2026)

## Подтверждённое живое состояние
- Пользователь успешно установил BGXP2 поверх BGXPR в BG_EET_FOXX_NEW EET + EPS 18.4: WeiDU last `BGXP2`; BCS SHA256 `583e0a5e78c6ae66ffc3c03b8811ade0168377660a6afc79b0859718d84a82eb`, 1158 BCS блоков; Lua `74ddc016e15fae3451bafe3039b299740c9d2efae8ecfb3e86badea257fa650c`.
- В режиме BATTLE при EPS атаке/боевых заклинаниях OFF самостоятельно использовал Command на Шанке; источник вызова непосредственно не залогирован.
- В режиме AUTO: Command, затем атака; у Джейд HP 3/6 и после 2/6, Жаган добил Шанка без лечения. `CLERIC_CURE_LIGHT_WOUNDS` был подготовлен/запомнен. Общий AI/F ON, EPS самоусиление ON, остальные EPS боевые действия выключены.
- Самостоятельное лечение в HEALER ранее было подтверждено, но **AUTO heal failed in this fight**. Не дублировать испытание и не утверждать, что виновата только очередь.

## Точный технический анализ
- BGXPR AUTO уже лечит при `HPPercentLT(PlayerN,45)`, `Range(PlayerN,10)`, `See(PlayerN)`, `HaveSpell(CLERIC_CURE_LIGHT_WOUNDS)`, `ActionListEmpty()` и свободных таймерах/слотах.
- BGXP2 AUTO Command и AttackOneRound находятся в конце после старых 1130 блоков и требуют `!HPPercentLT(Player1..6,45)`, `ActionListEmpty()`, F ON. При 3/6 HP (50%) начало атаки разрешено; уже выполняемая AttackOneRound не отменяется при падении HP.
- Достоверный источник IE scripting: IESDP AttackOneRound возвращает пустой список действий после одного раунда; AttackReevaluate **не** эквивалентное безопасное решение, поскольку не очищает ActionListEmpty при истечении интервала. Запрещено слепо внедрять ClearActions/ForceSpell: нет доказанного provenance ручных приказов.
- Возможные иные блокировки лечения: ActionListEmpty, LOS/Range, таймеры, BGX66_S_HEAL_SLOT или старые EPS блоки — по скриншоту не различимы.

## Фактический код, опубликованный в GitHub
`BGXAI/patchsets/priest_auto_attack_buffer_source_only_20261117/`
- `BGXP3_AUTO_ATTACK_BUFFER_SOURCE_ONLY.py`: SHA-pinned оригинальный BGXP2 BAF `a93dd1d46bf55ff7a5d53f15b0b55c1fc2ad10e39a4a23ae90ece62bfd76df2d`, fail-closed, Windows CRLF нормализуется только до канонического LF с точной SHA-проверкой. Поменяны лишь 6 `!HPPercentLT(PlayerN,45)` в **последнем AUTO AttackOneRound блоке** на `...60`. 27 предыдущих блоков без изменений, Command/HEALER/SUPPORT/Lua и BCS действий не меняет.
- `test_bgxp3_auto_attack_buffer.py`: 7/7 тестов PASS на Windows GitHub Actions.
- `README_RU.md`: ограничения и статус.
- SHA256 канонического нового BAF кандидата: `c3d41f9d046203e8acbb2e8ff3896183b10a12e58eaef743d67eeab77213f378`.
- CI: https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/43923824138 (PASS).
- Игровые файлы не менялись; **BGXP3 только source-only**, не готов к установке.

## Следующие инженерные шаги (без новых пользовательских команд до готовности)
1. Строгий верификатор compiled BCS: на действующем BGXP2 (1158) проверить штатный native 28-блочный compiled фрагмент и отличие **только последнего AUTO AttackOneRound блока**; без изменения остальных 1157 и сохранённого BGXPR.
2. Guarded WeiDU installer BGXP3 с точным last=BGXP2, SHA BCS/Lua, external SHA-verified backup и отдельным откатом. Не устанавливать автоматически.
3. Интегрировать **только** через прежний `BGXAI_UPDATE.cmd` (единственный автообновлятор). Текущий pinned `BGXAI_SYNC.ps1` 79303 из лимита 80000 байт: новую группу меню безопасно не вставить без рефакторинга/проверенного pin и Windows AST. Не нарушать существующие пункты 1–108.
4. После preflight нового кандидата один независимый бой с контролем свободной очереди/здоровья/запомненных заклинаний. Не утверждать, что новая 60% защита гарантирует спасение при мгновенном падении с полного HP ниже 45%.
5. Для полного решения приоритетного лечения нужен подтверждённый action provenance; не сбрасывать ручные/EPS команды ради необоснованного ForceSpell.

## Правило
Не путать разработанный исходник и установленную игру. Не просить заново доказанные тесты Command/HEALER. Работать автономно над безопасными этапами, а на изменение игры — только отдельное явное разрешение через один CMD.
