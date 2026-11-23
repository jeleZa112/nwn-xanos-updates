# BGXAI R21 — безопасный офлайн-контроль доказательств, 23.11.2026

## Что подтверждено — не перепутать стадии

- **Последний LIVE в игре:** TD15/R13.2, ранее подтверждённые 4 события и 9 raw защитных полей одной цели. Игра, EPS, SCS, WeiDU, сохранения, BG_EET_RU и BG Voice RU этим этапом **не менялись**.
- **R20 user-read-only scan PASS:** пользовательский `BGXAI_R20_EEEX_STATIC_20261123T183158663.json`, SHA256 `ac6fe71eb2aa7d17c8197cd34893ef47caa3ac957c8a66d4ea3c376490751cae`, `UPSTREAM_V117_LF_EQUIVALENT_STATIC_ONLY`. Верифицирует source equivalence для трёх Lua-модулей установленного EEex, **не DLL ABI/lifetime/runtime**. Повторять menu164 НЕ нужно.
- **Новая находка x64:** официальный EEex-Docs `source/EE Game Structures (x64)/Other/index.rst` указывает `Item_Header_st` total 114 и `Item_ability_st` total 56. Официальный EEex tag v1.1.7 и v1.3.1 `EEex_Resource.lua` использует в item helper `Item_Header_st.sizeof*abilityIndex` вместо ожидаемого `Item_ability_st.sizeof*abilityIndex`: расхождение `58*index` для index>0. Проблема **SOURCE-LEVEL**, не подтверждённый runtime crash.
- **Новые R21 CODE / LOCAL TEST:** Python `BGXAI_R21_EVIDENCE_GATE_RO.py`, чистый evaluator без IO/EEex/runtime/actions; тесты `test_r21_evidence_gate_ro.py` **28/28 PASS локально**.
- **Независимое CI:** Windows **28/28 PASS**, Ubuntu **28/28 PASS**, SHA256 policy/source-only permission gate **PASS** в https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45168525535. Успех run подтверждён через GitHub jobs с выполненными соответствующими этапами.
- **R21 реальный R20 verdict:** `BGXAI/BUILD/R21_NATIVE_EVIDENCE_GATE_RO_20261123/R21_REAL_R20_GATE_VERDICT.json` (санитизированный, без raw пользовательского файла/путей) → `sourceStaticMatched=true`, `status=HOLD_NATIVE_POINTER_AND_ACTION_QUEUE`, `weaponSwitchAuthorized=false`, `dispatchAuthorized=false`, `nextAction=KEEP_CURRENT_WEAPON_NO_DISPATCH`. `currentSelectionScalarValid=false` означает отсутствие **необязательного текущего скалярного snapshot** в R20 и не ошибку R20.
- Новый код и тесты в **GitHub** и Library `/BALDURS_GATE_EET_AI/BUILD/R21_NATIVE_EVIDENCE_GATE_RO_20261123/`; `SHA256_MANIFEST.json` также сохранён в GitHub. Единственный Windows updater `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd` **не изменялся**. **GAME DEPLOY R21=NO, R21 LIVE=NO.**

## Шесть оставшихся блокеров

1. `ITEM_ABILITY_STRIDE_SOURCE_MISMATCH` — upstream item helper wrong stride for index >0 (source x64 documentation, native DLL runtime sizes not read).
2. `NO_NATIVE_RESOURCE_LIFETIME_PROOF` — работа с `CItem.pRes.pHeader` / CItem:getAbility() unsafe; Lua `pcall` не гарантирует защиту от invalid pointer.
3. `NO_AUTHENTICATED_LAUNCHER_AMMO_PAIR` — snapshot стрел + наличие лука ещё не native аутентификация.
4. `NO_ALTERNATE_SLOT_APR` — выбранный APR raw2=2.0, raw7=1.5; неизвестен эффективный APR **невыбранных** слотов.
5. `NO_COMPLETE_ACTIVE_EFFECT_FINGERPRINT` — 8 derived stats != полный список эффектов/бафов.
6. `NO_MANUAL_EPS_ACTION_QUEUE_BOUNDARY` — provenance команд игрока / EPS и стабильная неперерывающая граница не подтверждены.

## Новый source-only путь без прямой арифметики

EEex v1.1.7 `EEex_Sprite_Hook_CheckBlockWeaponHit` принимает engine-provided `weaponAbility` вместе с атакующим, целью и item. В движковом C++ callback есть native `Item_ability_st*`. Но **on-hit callback не является ранним событием принятия решения** и блокирующий listener при truthy return может отменить damage/on-hit effects. `safeToRegisterListener=false`; без отдельного no-op/ownership proof и typed user approval **не ставить** новый hook. Дополнительно `CResItem` в официальных x64 docs содержит `pAbilities` по offset 0x58 и `pHeader` 0x68, а C++ upstream использует `curWeaponIn->Demand(); curWeaponIn->GetAbility(...)`; ни одно из этих наблюдений не даёт безопасный Lua lifetime API автоматически.

## Следующая автономная работа

Исследовать исходники native `CItem::Demand/GetAbility/Release` и доступность engine-provided ability **только внутри** достоверного callback без хранения указателя. Альтернативно развивать только статические R3/R17 и выбранные R4/R13 измерения; статус HOLD. Нельзя переустанавливать TD15, звать пользователя на повторный бой, менять updater, копировать новый Lua в игру, включать auto-switch, пересоздавать уже действующий V1/V2/V5 ранкер или NONINTERRUPT.

**Текущие разрешения:** `safeToCallGetAbility=false`, `safeToCallGetLauncher=false`, `safeToRegisterListener=false`, `installAuthorized=false`, `weaponSwitchAuthorized=false`, `dispatchAuthorized=false`.

## Ссылки

- Код/тесты: `BGXAI/BUILD/R21_NATIVE_EVIDENCE_GATE_RO_20261123/`
- CI https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45168525535
- Источники: https://github.com/Bubb13/EEex-Docs/blob/master/source/EE%20Game%20Structures%20(x64)/Other/index.rst
- Source: https://github.com/Bubb13/EEex/blob/v1.1.7/EEex/copy/EEex_scripts/EEex_Resource.lua
- Source: https://github.com/Bubb13/EEex/blob/v1.1.7/EEex/copy/EEex_scripts/EEex_Sprite.lua
