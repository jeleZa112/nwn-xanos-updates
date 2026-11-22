# BGXAI — EEex R11 static compatibility V3, READ ONLY

Исправление диагностики пункта 160 по реальному выводу пользователя (22.11.2026).

## Что подтвердил пользователь

В установленной игре `C:\Games\BG_EET_FOXX_NEW` присутствуют `override/M___EEex.lua`, `EEex_scripts/EEex_Action.lua`, R1 `M_BGXWP.lua`, R2 `M_BGXW2.lua`, R4 `M_BGXW4.lua`. `EEex_scripts/B3AttackInfo.lua` отсутствует. Скрипт V2 ошибочно выдавал `HOLD_STATIC_COMPAT_INCOMPLETE` и код 3, вызывая `BGXAI STOP: 160 STOP`.

## Изменение V3

B3AttackInfo — **дополнительная опциональная функция EEex**, в официальном `EEex_Modules.lua` она по умолчанию отключена. Отсутствие файла не доказывает неисправность основного EEex. V3 возвращает статус `CORE_STATIC_PRESENT_OPTIONAL_ATTACK_INFO_ABSENT_R11_UNVERIFIED` и код возврата 0, **только когда все пять обязательных элементов (bootstrap, action, R1, R2, R4) присутствуют и проходят статическую проверку**. Путь `attack_info` указывается с `error=FILE_MISSING` и `missingOptionalModules=['attack_info']`.

Если опциональный файл присутствует, но повреждён, является ссылкой, имеет неверную кодировку или не содержит ожидаемых вызовов, остаётся `HOLD_STATIC_COMPAT_INCOMPLETE` и ненулевой код. Любое повреждение обязательных файлов также HOLD.

Оба результата успешной статической проверки (`STATIC_CALLSITES_FOUND_RUNTIME_NOT_PROVEN` и новый optional-absent) всё равно имеют **runtimeApiAuthenticated=false**, **r11RuntimeEligible=false**, **weaponSwitchAuthorized=false**, **installAuthorized=false**. Нельзя устанавливать Attack Info, EEex или R11 автоматически из-за этого отчёта; нельзя утверждать, что live GetWeaponHitChance существует.

Выполнены 34/34 локальных теста Python. Новых меню, скриптов запуска или игровых изменений нет. Для доставки требуется обновить SHA закреплённого скрипта того же единственного обновлятора, подтвердить Windows PowerShell AST и прежние пункты 1–159. До обновления PIN не объявлять LIVE.
