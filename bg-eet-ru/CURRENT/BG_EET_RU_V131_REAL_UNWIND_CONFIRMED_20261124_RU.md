# BG_EET_RU — реальная Win64 unwind-проверка V131 (архив пользователя 24.11.2026, 17:15)

## Подтверждённый результат
Оригинальный пользовательский `SEND_TO_CHATGPT_BG_EET_RU(20261124-171543).zip`: SHA256 `c07d5444d8582daa3461e8c531833b968f8b2f01e478898f5df2d9ed98e4685f`, **134 уникальных файлов, CRC PASS**. По `64_V130_PE_UNWIND.json`:
- `status=POST_PROLOGUE_CANDIDATE_STATIC_PASS_RUNTIME_HOLD`;
- исходный `Baldur.exe` SHA256 `fc821a4806a0305b84fd85f1aad2bd472c8db642ed34b4494ae62351cae1c580` совпадает;
- `CGameSprite::Hit()`: `0x39DA50–0x39E9DC`, `UNWIND_INFO RVA=0x639100`;
- `SizeOfProlog=31` байт; прежняя точка `0x39DA68` с `sub rsp,0x80` лежит **внутри пролога**;
- новая точка `0x39DA6F` начинается ровно на границе конца пролога и занимает 6 байт (`4c8bf2488bd9`); сразу после неё опасная RIP-relative LEA `0x39DA75`;
- `UNWIND_INFO version=1`, flags=0, frame-register=0, 9 отдельных записей операций (7 PUSH_NONVOL, 1 ALLOC_SMALL, 1 SAVE_NONVOL RBX). Это не значит, что в функции нет вообще исключений, и НЕ делает внешние native callback-и unwind-safe;
- `native_abi_xmm_verified=false`, `eeex_existing_hook_owner_verified=false`, `runtime_exception_unwind_verified=false`, `reentrancy_and_rollback_verified=false`, `native_hook_install_allowed=false`, `game_files_written=0`.

## Независимая проверка уже присланной информации — без нового запуска игры
Из того же ZIP взят настоящий `19_V68_COMBAT_CODE/functions/0039DA50_0039E9DC.bin` SHA256 `19c1d11b7ac41d261d22b19506b3570427e356544e48f2e2c622c1efdb74cc79`. Проверены **26 точных байтовых якорей** в прологе, кандидатной точке и эпилоге, **12/12** независимых требований:
- 7 PUSH_NONVOL: RBP, RSI, RDI, R12, R13, R14, R15; кодам раскрутки это соответствует;
- ALLOC_SMALL size=128 байт;
- сохранён RBX при входе `mov [rsp+0x20],rbx`, восстановлен в эпилоге `mov rbx,[rsp+0xd8]`; 7×8+128+32=216 байт, реальные машинные байты совпадают;
- при стандартном Win64 RSP mod16 = 8 на входе функции после 7 PUSH и выделения 128 байт RSP выровнен на 16 байт к точке `0x39DA6F`;
- `0x39DA6F` `mov r14,rdx`, `0x39DA72` `mov rbx,rcx`; следом `0x39DA7C` `mov esi,r9d`, `0x39DA83` `mov r15,r8`. Это регистровый след; **семантику атакующего, цели и CItem по этому одному коду НЕ присваивать**.

Результат локального анализатора: `POST_PROLOGUE_STATIC_CROSSCHECK_PASS`; отдельный JSON `BG_EET_RU_V131_REAL_UNWIND_SEMANTIC_CROSSCHECK.json` создан в данном ответе.

### Критическое ограничение V130 JSON
JSON хранит `unwind_operations[].extra_slots` как КОЛИЧЕСТВО дополнительных слотов, но **не их исходные значения**, то есть полный raw `UWOP_SAVE_NONVOL` stack-offset из `.xdata` в пользовательский ZIP **не попал**. Согласованность ожидаемых 216 байт подтверждается байтами обычного пролога/эпилога, но не независимым повторным декодированием этого raw operand. НЕ выдавать проверку всех сырых unwind байтов за выполненную.

## Решение
**ПОСЛЕ-ПРОЛОГОВАЯ ТОЧКА ВЕРИФИЦИРОВАНА СТАТИЧЕСКИ. LIVE NATIVE ПЕРЕХВАТ ПО-ПРЕЖНЕМУ ЗАПРЕЩЁН.** Следующий разработческий шаг без новых пользовательских действий — инженерный контракт native callback/trampoline с сохранением Win64 XMM/регистров, shadow space, регистрацией unwind для JIT памяти (где это требуется), точным EEex owner и безопасным rollback; доказать attacker/target/CItem и единый event key. Отсутствие сообщения из `Hit()` не равно MISS (вывод V129). `UI.MENU` V126 уже установлен и успешно собрал 72 строки. Не менять игру, TLK, EXE, BGXAI, Voice RU, сейвы. Не просить повторного боя или 14 старых аудитов.

Ни одна установленная версия обновлятора/мода после нового ZIP не менялась. Последний опубликованный onefile — V131; повторно запускать пункт 6 не требуется.
