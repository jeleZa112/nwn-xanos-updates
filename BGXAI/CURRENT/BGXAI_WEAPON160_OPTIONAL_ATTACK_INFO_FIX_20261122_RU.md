# BGXAI — 160, исправление отсутствующего дополнительного модуля Attack Info

Дата: 22 ноября 2026. Результат пользователя: пункт 160 V2, статус `HOLD_STATIC_COMPAT_INCOMPLETE`, отсутствует только `EEex_scripts/B3AttackInfo.lua`, а `EEex_Action.lua`, загрузчик, R1, R2, R4 присутствуют. `BGXAI STOP: 160 STOP` был следствием слишком строгой диагностики.

Официальная EEex `EEex/copy/EEex_scripts/EEex_Modules.lua` содержит `["B3AttackInfo"] = false`, а `EEex/EEex.tp2` включает Attack Info как отдельный дополнительный модуль. Нельзя считать отсутствие этого модуля неисправностью базовой EEex или принуждать пользователя его устанавливать.

## Исправление V3

- `BGXAI_EEEX_R11_STATIC_COMPAT_RO_V3.py` — чистая статическая READ ONLY диагностика. Если отсутствует только B3AttackInfo.lua, возвращает `CORE_STATIC_PRESENT_OPTIONAL_ATTACK_INFO_ABSENT_R11_UNVERIFIED` и код 0. В консоли отчёт сохраняет `error=FILE_MISSING`, `missingOptionalModules=["attack_info"]`, `selectedHitChanceApiStaticEvidence=false`, `r11RuntimeEligible=false`, `runtimeApiAuthenticated=false`, `weaponSwitchAuthorized=false`.
- Если отсутствует или повреждён обязательный загрузчик, `EEex_Action.lua`, R1, R2 или R4 — `HOLD_STATIC_COMPAT_INCOMPLETE` и ненулевой код. Если B3AttackInfo присутствует, но имеет ошибки/подмену/неподходящий код — тоже HOLD.
- Никаких игровых команд, хуков, автопереключения и установки R11. V6, EPS, сохранения и старая команда запуска не меняются.
- `BGXAI_SYNC.ps1` V3 меняет от ранее опубликованного V2 **только одну строку обработчика 160**: путь сканера, размер 8301 и SHA256 `4bf4e2a981a6602da02ba53dc3e5601fd69bb2f408c64d880c208f1a19bf83f4`. Размер самого обновлятора остаётся **79943 байта**.
- Windows CI [run 45042971825](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45042971825): **8/8 точных тестов предыдущих действий, 34/34 теста сканера, PowerShell 5.1 и 7 AST — PASS**. SHA256 скрипта по Windows CI: `b7e62b0e1fba2a6f6730508c02718da2c56211b1f98344adbb135735abfe9697`.
- Следующий пользовательский шаг **после закрепления PIN**: запустить тот же `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`, выбрать **160**, прислать результат. Если отсутствует только AttackInfo, ожидание: `CORE_STATIC_PRESENT_OPTIONAL_ATTACK_INFO_ABSENT_R11_UNVERIFIED`; **не** `HOLD`. Из этого не следует, что методы R11 доступны в runtime.
- Не заставлять заново выполнять предыдущие R1–R4 проверки; учитывать журнал, не просить `+` на каждый безопасный этап.

CODE/TEST: PASS. RELEASE PIN: выполняется отдельно. LIVE V3: не проверен. R11/R12: NOT DEPLOYED, no weapon switch.
