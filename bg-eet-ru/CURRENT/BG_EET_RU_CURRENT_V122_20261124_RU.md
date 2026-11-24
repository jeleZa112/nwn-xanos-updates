# BG_EET_RU — актуальная контрольная точка V122, 24.11.2026

## Выпущенная версия, а не исследовательский пакет
- **Выпуск V122 подтверждён:** draft PR #90 после Windows/Linux CI был объединён в ветку `bg-eet-ai`; squash commit `3a08f981e8974a6ee798b79fb32d5d340839283f`.
- Канонический пользовательский файл тот же: `C:\Users\Drevo\Documents\BG_EET_RU\BG_EET_RU_UPDATE.cmd`. Дополнительный CMD/PowerShell пользователь не запускает.
- Manifest `bg-eet-ru/onefile/release.json`: version **122**, SHA256 файла **`0f60ee78fc5a51db410664659dcbfeaf98ca07be27fc3ea9a3d660e4fed773ec`**, размер **749971 байт**. Это **меньше старого защитного лимита V121 750000** — следовательно, V121 может принять V122 при штатном успешном обновлении без ручной замены.
- **НЕ подтверждено**, что Windows пользователя уже скачал V122: после публикации локальный запуск отсутствует. Не утверждать установки.
- Встроенный V121 AutoFix сохранён: 14 доверенных модулей, 735 статических/модельных проверок, SHA-pinned кеш, карантин, только один ZIP.
- В стандартный путь V121 добавлен `v122_run()`: при запуске V121 source AutoFix автоматически сохраняет ещё одну запись **`61_V122_LIVE_HIT_READONLY.json`** в том же `SEND_TO_CHATGPT_BG_EET_RU.zip`. Есть также флаг `--live-hit-readonly` для адресного READ ONLY сбора через **тот же CMD**.
- Windows reader `bg-eet-ru/live-inventory/windows_live_hit_inventory_ro.py` доступен в исходниках, а updater получает байты с **иммутабельного commit** `91165691e629db817ba734ec394042c34bc2f8c3`, SHA256 **`ba5f4cc2b0c690f706dea032b791c0773cf673725452dfbba3d5dbe11b356d26`**. Ранее работающая V121 загрузка/кеш/карантин переиспользованы, код читает только после проверки SHA.
- `.gitattributes` добавлен `bg-eet-ru/live-inventory/*.py text eol=lf`, иначе Windows checkout менял SHA из-за CRLF. Контроль SHA **не ослаблялся**.

## Технически реализованный внешний READ ONLY сбор
- Использует Windows API `OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_LIMITED_INFORMATION)`, `ReadProcessMemory`, `QueryFullProcessImageNameW`, `CreateToolhelp32Snapshot`, `Module32FirstW` и `Process32FirstW`; не использует `WriteProcessMemory`, code patching, suspend, DLL injection.
- Валидация точного on-disk `Baldur.exe` SHA `fc821a4806a0305b84fd85f1aad2bd472c8db642ed34b4494ae62351cae1c580`, процесса по реальному пути EXE, базы модуля, pre-Hit code capture RVA `0x39DA68`, запрет RIP-relative RVA `0x39DA75`, callsite `0x39E84B`, exit `0x39E996`, существующий EEex `FirstCall` RVA `0x39DA86`, seven vtable pointers `0x597CD0`, два native call target. Все участки читаются дважды; обнаруженное изменение → HOLD.
- **Не считать opcode E9 доказательством владельца JIT trampoline**; status с совпавшими участками = `LIVE_SITES_MATCH_OWNER_AND_GAMEPLAY_HOLD`.
- При отсутствии открытой игры, несовпадении SHA, отсутствии сети и кеша, неизвестной инструкции — явный `RUNTIME_MEMORY_HOLD`, **0 изменений игры**. Один ZIP сохраняет все прежние записи.
- V122 не устанавливает хуки, не изменяет EXE/TLK/UI/BCS/WAV/save, BGXAI и BG Voice RU.

## Проверки и ошибки
- Полные проверки V122 на Linux и Windows подтверждены в GitHub Actions PR #90: AST, size <750000, точный release manifest SHA, неизменные 14 эталонных AutoFix модулей, full onefile selftest, PIN SRC SHA, 15 mock-memory tests, **настоящий Win64 ReadProcessMemory на CI self-process**, интеграция кеша/offline-HOLD/одного ZIP. `bg-eet-ru-onefile-selftest.yml` прошёл на squash commit `3a08f981...`.
- Первоначальный Windows CI обнаружил CRLF SHA error, устранён `.gitattributes` и повторный CI успешен.
- После объединения legacy V108 test fixture использовал synthetic game без report ZIP и не подменял появившийся в V121 AutoFix; тест был неактуален. Отдельный CI test fixture исправлен на ветке `bg-eet-ai`, commit `372d0e3df5a0177ca283ed023d68f1c85b0ed9bc`, добавлением mock v121_run в ожидаемую последовательность. Следить за итоговым CI этого коммита; НЕ менять или отключать защиту самого AutoFix ради старого мок-теста.

## Оставшиеся блокеры перед игровым результатом
- **Работающий native hook всё ещё не установлен**; сработал ли новый V122 на конкретной игре пользователя — ещё не проверено.
- Точный фактический item RESREF при промахе, launcher/ammo, идентичность CMessage и конкретной видимой UI строки `combatLog`, реентерабельный Win64 JIT wrapper, unwind/SEH, ownership другого EEex хука — пока HOLD.
- Дальнейшее: один **реальный** Windows READ ONLY снимок через **тот же** `BG_EET_RU_UPDATE.cmd` с открытым Baldur's Gate и одна пересылка `SEND_TO_CHATGPT_BG_EET_RU.zip`, если пользователь согласится; без доступа к его Windows RAM невозможно подтвердить локальный owner. Затем один guarded native-пилот при separate typed approval и backup+rollback, один комплексный gameplay test. Никаких мелких серий по одному адресу.
- Постоянное правило `bg-eet-ru/ONE_RUN_AUTONOMOUS_POLICY_RU.md`: максимальный автономный пакет, fail-closed ошибки, source/CI ≠ gameplay, пользовательские изменения только по отдельному точному согласию.
