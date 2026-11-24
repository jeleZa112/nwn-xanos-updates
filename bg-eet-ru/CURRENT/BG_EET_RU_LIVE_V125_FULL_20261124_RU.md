# BG_EET_RU — реальный V125 14/14 Windows ZIP (24.11.2026)

Вход: `SEND_TO_CHATGPT_BG_EET_RU(20261124-155035).zip`, SHA256 `c8ad57e5e07be0023e7edd915ad59e5fd5063795313741ec30b2b0e5cfe04782`; 132 файла, CRC/уникальность PASS.

**Впервые полностью доказан реальный запуск V125:** `62_V124_ONE_RUN_BOT.json`: `updater_version=125`, `stage_count=14`, `hold_count=9`, `game_files_written=0`, `native_hooks_installed=false`, `gameplay_verified=false`. Пользователю не нужно повторять V125.

### Результаты
- Без HOLD (5): V85 установлен, V102 preflight не установлен, V108 установлен, V111 3 имена ITM/TLK извлечены, V116 CMessage dispatch static symbol match. «Без HOLD» не означает gameplay.
- HOLD (9): V103 sources incomplete; V104 signature mismatch; V105 `V105_INSTALLED_FILE_INTEGRITY_HOLD`; V106 `V106_INSTALLED_MODULE_SHA_DRIFT`; V107 static ABI only; V112 no actor/row correlation; FULL static runtime join HOLD; V121 `RuntimeError:SUITE_CASE_COUNT_UNEXPECTED_HOLD`; V122 JIT owner/miss/visible row HOLD.
- V122: один проверенный процесс игры, EEex присутствует, 6 мест прочитаны дважды, все 8 булевых memory checks true. `firstcall_owner_verified=false`, `native_abi_verified=false`, `miss_resref_verified=false`, `visible_row_verified=false`.
- V111 actual names: SW1H04 «Длинный меч», AROW01 identified «Стрела», unidentified «Отличная стрела»; BOW05 «Короткий лук».
- V112: в отчётных V108 callback events нет attacker/target/sequence/journal row key; **никакие имена оружия не вставлять в строку боя по догадке**.

### Техническая оценка без повтора пользовательских тестов
1. Старые SHA-претензии V105/106 возможны из-за установленного V108; сравнить точные состояния и SHA и исправлять только семантику status, НЕ менять модули игры/не откатывать V108.
2. V121: 11-stage suite достиг сравнения `total_source_checks != 735`, но действительный счётчик не сохранён в ZIP. Не снижать строгий порог и не выдавать PASS без точного числа. Исторически native pilot source suite 735/735 на Linux.
3. Не перепроверять живую память V122: она повторно прошла. Сохранить native пилот source-only модель: `bg-eet-ru-native-hit-pilot-corrected-20261124`, `BG_EET_RU_THREAD_FRAME_BRIDGE_V4.lua` и `message_callsite_proof_v4.py`.
4. Следующая существенная работа: точный EEex JIT owner, Win64 wrapper ABI/XMM/SEH, per-Hit CItem on miss, связь CMessage с конкретной UI `combatLog` строкой. До доказательства — только оригинальный журнал. Native install только по отдельному typed approval, backup и rollback.

**Пользователю сейчас ничего запускать не нужно.** Не заменять рабочий V125 новыми версиями ради счётчиков. Главный критерий — работающий русский боевой журнал и достоверная атрибуция оружия.
