# BG_EET_RU — CURRENT V131 (24.11.2026)

## Последний пользовательский результат
V126 UI.MENU наблюдатель реально установлен. В единственном пользовательском ZIP от 24.11.2026 16:48 собрано 72 видимые строки combatLog (11 исходов d20: 5 HIT, 6 MISS), console exit 0. Текст журнала не изменён. V108 RESREF оружия не имеет проверенного идентификатора той же попытки, с этими строками по соседству не объединять.

## V129 и V130 — проверенные новые выводы
Точная функция CGameSprite::Hit() SHA256 19c1d11b7ac41d261d22b19506b3570427e356544e48f2e2c622c1efdb74cc79: некоторые условные ветви обходят вызов AddMessage по адресу 0x39E84B. Вызов не является универсальным событием атаки, отсутствие вызова НЕ означает промах. Новый per-attempt source-only ledger учитывает это.
Старый кандидат перехвата 0x39DA68 — инструкция sub rsp,0x80 (вероятно unwind prologue). Новый кандидат 0x39DA6F — две обычные MOV инструкции общей длиной 6 байт, после выделения стека, перед RIP LEA 0x39DA75 и существующим EEex патчем 0x39DA86. Для реальной безопасности нужна проверка .pdata/.xdata установленного EXE.

## Новый V131 (один CMD, НЕ установка native-хука)
V130 PE unwind gate source-only PR #100 merged ea012654ce6323b265ba1a91c1b71d9e0a866ad8; V131 onefile PR #101 merged 35994ebf25980444905a3992dfaed4dc4a48d229.
Единственный BG_EET_RU_UPDATE.cmd: V131, 749889 байт, SHA256 b5cb631f0d11623b5b3d33802172251bb4ef759af80703e43a66fd243617d144. release.json V131 SHA совпадает. Windows и Linux CI PASS run 45445853600, включая реальную SHA-загрузку Python PE parser с dataclass, кеш, единый ZIP, исходный 14-stage regression, и отрицательные .pdata/.xdata тесты. CI не равен runtime-подтверждению.
В меню V131 пункт 6=unwind. Только читает локальный Baldur.exe (требуется exact SHA fc821a4806a0305b84fd85f1aad2bd472c8db642ed34b4494ae62351cae1c580) и добавляет 64_V130_PE_UNWIND.json в существующий SEND_TO_CHATGPT_BG_EET_RU.zip. Только статус, никогда game files written и native install. V126 и V108 не затрагиваются.

## РОВНО СЛЕДУЮЩЕЕ ДЕЙСТВИЕ
Запустить привычный C:\Users\Drevo\Documents\BG_EET_RU\BG_EET_RU_UPDATE.cmd, проверить автоматическое обновление до v131. Выбрать ТОЛЬКО пункт 6 — unwind, а не 1 (старые 14 аудитов), не 2 (UI install), не 4 (игровой capture). Прикрепить сюда ЕДИНЫЙ обновлённый SEND_TO_CHATGPT_BG_EET_RU.zip.
В новом отчёте 64_V130_PE_UNWIND.json проверить реальные unwind границы и длину пролога; после этого доработать Win64 ABI/XMM, EEex owner, JIT coexistence, SEH и deterministic rollback. Никаких новых native hooks и изменения журналов без нового явного подтверждения. Не повторять ранее пройденные игровые бои.