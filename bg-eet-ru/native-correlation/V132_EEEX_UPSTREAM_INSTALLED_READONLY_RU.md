# BG_EET_RU — V132 installed EEex + raw unwind evidence (25.11.2026)

## Реально подтверждено в игре
V126 UI наблюдатель установлен. В настоящем бою захвачены 72 видимые combatLog строки, 11 d20 результатов (5 HIT, 6 MISS), без изменений текста журнала. V131 SHA-pinned Baldur.exe успешно проверил Win64 SizeOfProlog=31 и кандидата 0x39DA6F сразу после пролога. V129 доказал, что конкретный CGameSprite::Hit()->AddMessage callsite в 0x39E84B условен; отсутствие CMessage не означает промах. Никаких новых native hook не ставили.

## Доказанный upstream EEex (но НЕ версия пользователя)
Официальный Bubb13/EEex, путь EEex/copy/EEex_scripts/EEex_Assembly_x86-64.lua, Git blob e8c6a2fe303fdac3e92d9df9ea25c6a7af1e5a5c.
EEex_Assembly_Private_WriteAndRegisterFunctionTable и EEex_Assembly_Private_PostJIT используют EEex_RtlLookupFunctionEntry(hookAddress) и EEex_RtlAddFunctionTable, регистрируя unwind сведения сгенерированного JIT-кода. EEex_HookBeforeRestoreWithLabels и EEex_HookCallInternal используют EEex_JITNear / EEex_JITAt. Это сведения upstream, не подтверждение exact installed build, runtime JIT owner или safety.

## Новый V132 (source read-only, optional onefile)
bg-eet-ru/native-correlation/v132_eeex_unwind_contract_ro.py — on-disk read-only анализ точного Baldur.exe .pdata/.xdata: сохраняет raw UWOP_SAVE_NONVOL RBX encoded slot, проверяет 27*8=216 байт, ALLOC128 и 7 PUSH. V131 не сохранял raw extra slot operand в отчёте. Одновременно читает SHA и точные якоря установленного EEex_scripts/EEex_Assembly_x86-64.lua, EEex_Sprite_Patch.lua, InfinityLoader.db FirstCall label (само наличие метки НЕ доказывает hook ownership). Не выполняет Lua, не обращается к процессу, не пишет игровые файлы.
Полный V132 onefile через существующий BG_EET_RU_UPDATE.cmd, SELF_VERSION 132; 749856 байт; SHA256 b4b6d8dd864dc2ad6beeec50965015396e8d5f02efc22c0071dc8f5835e86644. release.json version132 соответствует. Новое меню 7=abi запускает только этот анализ, сохраняет 65_V132_EEEX_ABI.json в прежнем SEND_TO_CHATGPT_BG_EET_RU.zip. В игре ничего не меняет.
CI GitHub run 45448762926: Windows PASS, Ubuntu PASS. Проверено реальное скачивание module SHA, offline cache, прежний пункт V131, V132 synthetic unwind 216-byte counterexamples и полный selftest. CI PASS не означает игровой JIT PASS.

## Статус и следующие действия
Native callback ABI/XMM, реальное сохранение регистров, EEex JIT owner, безопасный rollback и same-hit→combatLog-row event key остаются HOLD. Hook install запрещён, даже при положительном статическом отчёте.
Один пользовательский шаг после публикации: запустить старый C:\Users\Drevo\Documents\BG_EET_RU\BG_EET_RU_UPDATE.cmd, обновиться до v132, выбрать только 7 — abi, прислать единственный обновлённый SEND_TO_CHATGPT_BG_EET_RU.zip. Не повторять бой, 14 stage, V126 install, V131 option 6. Пользовательский V132 capture ещё не выполнен.
Работающие V108, V126 UI, BGXAI, BG Voice RU, EXE, TLK и сохранения остаются нетронутыми.