# BG_EET_RU — актуальный статус native Hit V2 (24.11.2026)

## Достигнуто
- Сохранён пользовательский pinned V120 ZIP: `08a9d5da367404b33bc982871627e8c3e1179c7a8ec8808bab0a75bea5755015`. Источники/EXE не изменялись.
- Разделены типы перехватов: `sub rsp,0x80` (`0x39DA68`) — safe relocatable instruction; `call rel32` (`0x39E84B`, `0x39E996`) — требует EEex HookBeforeCall, не raw-copy. Цели CALL вычислены по байтам: `0x204C60`, `0x3FCE00`. Upstream `FirstCall 0x39DA86` не трогать, прежнюю RIP-relative `0x39DA75` не использовать.
- Устранён потенциальный Lua exception при `Exit(nil)`/NaN и обращении к аварийному EEex label/memory API. При конфликте кадров блокировка очищается только после всех парных выходов, лимиты памяти и self-HOLD.
- Реальный Lua 5.4 исполняет основной тест (45 assertions) и mock-live-preflight/exception тест (46 assertions). 39/39 статических ворот Lua, 18/18 статический контракт маршрута, 7+6 adversarial Python, 735/735 прежняя source suite.
- Полный один проход: `SOURCE_PASS_RUNTIME_HOLD` (7 независимых stages). Проверки исходников нельзя выдавать за runtime/gameplay PASS.
- Рабочий канонический Windows `BG_EET_RU_UPDATE.cmd` **V121**, один пользовательский файл, один отчётный ZIP, без новых release в этом исследовании.

## Блокеры native и gameplay
1. Реальный Win64 JIT wrapper (volatile regs, flags, XMM, alignment); проверка фактических EEex Lua-типов `CItem` и всех выбранных обвязок.
2. LIVE memory SHA/site ownership и другие хуки, исключение частичного JIT-инсталла и SEH/unwind.
3. Проверить, действительно ли CItem у каждого промаха и может ли этот же CMessage быть однозначно сопоставлен с видимой UI-строкой; до этого не подставлять названия оружия.
4. Guarded install с точным разрешением, внешним backup и rollback. После снятия блокеров — **один комплексный игровой тест** (меч, лук, праща, дротики, стрелы, две руки, две цели, попадания и промахи).

**SOURCE PASS / NATIVE INSTALL HOLD / GAMEPLAY NOT TESTED. Никаких действий пользователя сейчас.**