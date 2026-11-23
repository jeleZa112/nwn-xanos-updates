# BGXAI R20 — реальный статический аудит EEex выполнен пользователем 23.11.2026

## Вход / происхождение
- Пользовательский файл: `BGXAI_R20_EEEX_STATIC_20261123T183158663.json`; байт: **3162**, SHA256 **ac6fe71eb2aa7d17c8197cd34893ef47caa3ac957c8a66d4ea3c376490751cae**. Исходный JSON остаётся в пользовательском чате; **не публиковать его целиком** и не переносить неочищенные отчёты в публичный GitHub.
- Меню: единственный `BGXAI_UPDATE.cmd -> 164` (READ ONLY). R20 release `bdff49dfb908798c9979cfe7e42f5179dd43c6c4`, SHA pinned script `913756757e54479f3e50ddd3d5068b58826220b7988f579bacaa6787e7715fcc` (79 871 байт), PIN `2a6ffc89213541175773502bf8a2d6ae303a06f1`.
- Статус отчёта: **`UPSTREAM_V117_LF_EQUIVALENT_STATIC_ONLY`**, `fixtureMode=false`, `installedGameFilesInspected=true`, `readOnly=true`, `gameModified=false`, `gameplayActionsSent=0`.
- Это **подтверждённый пользовательский запуск статического сканера**, но не игровой runtime-тест методов.

## Реальные результаты
| Узел | present | callsites | exact bytes | canonical LF match | normalized Git blob SHA |
|---|---|---|---|---|---|
| EEex_Resource.lua | true | true | false | **true** | `5ecd3c2f9e9bcc6cbd317653fc057a06d956916b` |
| EEex_Sprite.lua | true | true | false | **true** | `b2d8d930c47785737bd30dad08e9f35a9d859578` |
| EEex_Action.lua | true | true | false | **true** | `e7543274ed066b5abe3c58262105212f208d1595` |

- `allRequiredLuaScriptsPresent=true`, `allStaticMethodCallsitesPresent=true`, `allInstalledFilesCanonicalLFUpstream=true`, `allInstalledFilesExactUpstream=false`.
- `override/M___EEex.lua` найден, `bootstrap.present=true`; это наличие bootstrap-файла, **не доказательство запуска функций в текущем процессе**.
- Каноническое совпадение трёх Lua-скриптов соответствует **исходному tag v1.1.7**, но НЕ устанавливает номер всего установленного пакета EEex, DLL, native ABI или корректность API.
- Разница raw Git blob SHA соответствует нормализации BOM/CRLF/LF, как считает сканер; **это не повод переписывать установленные Lua-файлы**.

## Запреты / условия
Сканер вернул:
- `apiPresentAtRuntimeVerified=false`;
- `nativeResourceLifetimeVerified=false`, `nativeAbilityPointerSafe=false`, `nativeLauncherReturnSafe=false`;
- `safeToCallGetAbility=false`, `safeToCallGetLauncher=false`, `safeToRegisterListener=false`;
- `alternateSlotAPRVerified=false`, `fullActiveEffectsFingerprintVerified=false`;
- `weaponSwitchAuthorized=false`, `dispatchAuthorized=false`, `installAuthorized=false`.

Все 5 blockers остаются: `NO_LIVE_POINTER_LIFETIME_PROOF`, `CITEM_GETABILITY_UNGUARDED_PRES_HEADER_DEREFERENCE`, `GETLAUNCHER_REQUIRES_VALID_NATIVE_ABILITY_HANDLE`, `STATIC_API_PRESENCE_DOES_NOT_ESTABLISH_RUNTIME_SAFETY`, `ACTIVE_EFFECTS_AND_ACTION_QUEUE_UNVERIFIED`.

## Сводная стадия
- R20 CODE PASS / independent CI PASS / **USER READ-ONLY SCAN PASS**.
- TD15/R13.2 игровой LIVE — ранний PASS для 4 событий и 9 сырых защитных полей **одной цели**, не обобщать на другие цели.
- R18/R19 engine candidate не установлен. R20 не доказывает безопасность native API. Автоматическая смена оружия остаётся **OFF**.
- **Не запрашивать повтор пункта 164, R3, R13 боёв, перенастройку EEex, переустановку или новый ZIP/CMD.**

## Новая блокирующая находка R21
Официальный Lua `EEex_Resource_GetItemAbility` в v1.1.7 **и v1.3.1** имеет `Item_Header_st.sizeof * abilityIndex` при вычислении `Item_ability_st`. В документации engine-x86 EEex размер `Item_Header_st` выводится из полей до 0x72 = 114, `Item_ability_st` до 0x38 = 56. При соответствии бинарной ABI разница для индекса >0 — `58 * index`. **Это source-level риск и не доказывает runtime crash**. Индекс 0 не снимает lifetime/pRes риск. Статическая нормализация R20 подтверждает, что установленный `EEex_Resource.lua` содержит именно этот upstream код.

Первый более безопасный native-кандидат: upstream engine C++ выполняет `CItem::Demand()` перед `CItem::GetAbility()`; не объявлять Lua-эквивалент доступным/безопасным без отдельной source ABI и lifetime-проверки. Сохранить R18 как SOURCE ONLY/HOLD; дальнейшая работа — только source-only анализ альтернативного непотенциально опасного наблюдения, существующего R4/R13, EPS/manual, alt APR и launcher/ammo, без runtime pointer calls.

## Следующая работа
R21: проверить native ABI/packing, ownership Demand/Release, правомерность альтернативного безопасного пути и границу EPS/manual на исходниках. Отдельное разрешение и Win+game guarded pilot требуются **только после** устранения настоящих блокеров, не сейчас.

Источники:
- https://github.com/Bubb13/EEex/blob/v1.1.7/EEex/copy/EEex_scripts/EEex_Resource.lua
- https://eeex-docs.readthedocs.io/en/engine-x86/EE%20Game%20Structures%20(x86)/Other/index.html
- https://github.com/Bubb13/InfinityLoader/blob/master/EEex-Core-Shared-Files/source/EEex.cpp
- `BGXAI/CURRENT/BGXAI_R21_NATIVE_ABILITY_STRIDE_SOURCE_AUDIT_20261123_RU.md`.
