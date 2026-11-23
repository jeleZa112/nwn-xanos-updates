# BGXAI R22 — Native Demand/GetAbility lifetime, ownership and on-hit source audit PASS (23.11.2026)

## Настоящий статус

**CODE:** SOURCE ONLY PASS. **TEST:** локальные 40/40 PASS; Windows 40/40 PASS и Ubuntu 40/40 PASS; SHA256/source-only gate PASS — независимые GitHub Actions https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45174251662 (jobs проверены: completed/success). **SOURCE RELEASE:** коммит `36306fd6726fade035a7d84d857933bc772bb02c` в `bg-eet-ai`. **GAME DEPLOY:** нет. **R22 LIVE:** нет.

Последний подтверждённый LIVE в игре: R13.2/TD15 (4 DEFENSE-события, 9 raw полей одной цели). Последний реальный read-only user scan: R20, `UPSTREAM_V117_LF_EQUIVALENT_STATIC_ONLY` (нет нового задания меню164).

## Выполнено

- Source-only модуль `BGXAI/BUILD/R22_NATIVE_OWNERSHIP_SOURCE_RO_20261123/BGXAI_R22_NATIVE_OWNER_AUDIT_RO.py`, 10 проверяемых source-критериев, всегда fail-closed: `SOURCE_CHAIN_MATCHED_LIFETIME_HOLD` или `SOURCE_DRIFT_OR_INCOMPLETE_LIFETIME_HOLD`.
- Публичный минимальный excerpt-контракт `R22_UPSTREAM_EXCERPTS_VERIFIED_20261123.json`; источники независимо прочитаны через подключённый GitHub, по их Git blob SHA. Эти excerpt-фрагменты не равны полным исходникам и не доказывают runtime DLL ABI.
- Синтетические негативные регрессии `test_r22_native_owner_audit_ro.py`, SHA256 manifest и read-only GitHub workflow `.github/workflows/bgxai-r22-native-ownership-source-ci.yml`.
- Вердикт `R22_SOURCE_ONLY_VERDICT.json`: все 10 source checks matched, `status=SOURCE_CHAIN_MATCHED_LIFETIME_HOLD`, `actualDemandReleaseLifetimeProven=false`, `safeToReadNativeAbilityFields=false`, `safeToRegisterListener=false`, `weaponSwitchAuthorized=false`, `dispatchAuthorized=false`.
- Все исходники и тесты сохранены в Library `/BALDURS_GATE_EET_AI/BUILD/R22_NATIVE_OWNERSHIP_SOURCE_RO_20261123/` и в GitHub.

## Новое конкретное исследование

1. C++ InfinityLoader `EEex.cpp` в нескольких боевых путях вызывает `curWeaponIn->Demand();` непосредственно перед `curWeaponIn->GetAbility(curAttackNum)`. Это не доказывает, что автоматический Lua `CItem.getAbility` безопасен: его upstream код `EEex_Resource.lua` обращается напрямую к `item.pRes.pHeader:getAbility(abilityIndex)` и использует подозрительный stride `Item_Header_st.sizeof` вместо `Item_ability_st.sizeof`.
2. Для EEex x64 documented sizes 114/56: смещение index1 +58 байт в source expression, но нет доказательства конкретного DLL ABI/игрового краша. Не патчить EEex.
3. C++ `checkBlockWeaponHit` передаёт `pWeaponAbility` в Lua, но `EEex_Sprite_Hook_CheckBlockWeaponHit` при truthy результате слушателя даёт `return true`, что по официальной patch documentation **блокирует base weapon damage/on-hit effects**. `EEex_Utility_TryIgnore` возвращает успешный результат callback, значит нельзя считать такой hook пассивным по умолчанию. Более того on-hit слишком поздно для решения, **каким оружием атаковать до начала атаки**.
4. В публичной docs есть `CItem::Demand()` и `CItem::GetAbility()`, но нет проверенного contract ownership/release по всему runtime и API bridge. Отказ от новых обращений к `pRes.pHeader`, `pAbilities`, `item:getAbility`, `sprite:getLauncher` до доказательств.

## Жёсткие инварианты и следующие шаги

**Все проверки/действия fail-closed:** `safeToCallGetAbility=false`, `safeToCallGetLauncher=false`, `safeToRegisterListener=false`, `safeToReadNativeAbilityFields=false`, `installAuthorized=false`, `dispatchAuthorized=false`, `weaponSwitchAuthorized=false`. Даже 40/40 PASS доказывает только корректность **офлайн-проверяющего**, не игровой ИИ.

Следующая автономная source-only работа, не повторяя R3/R13/R20:
- Изучить существующий `BGXAI_WEAPON_NONINTERRUPT_PLAN_V1.lua` / V1,V2,V5/ranged и источник `EEex_Action_AddSpriteStartedActionListener` для границы сохранения ручной/EPS очереди; **не писать новый ранкер**, не авторизовать queue writes.
- Разработать интеграционный offline контракт `KEEP_CURRENT_WEAPON` при любом отсутствии причинно достоверных данных, учитывая selected APR raw2=2.0, raw7=1.5 и source identity из R3 без переноса APR между слотами. Проверить, что нельзя предложить weapon switch без полного эффекта/launcher pairing/manual origin.
- Не просить пользователя запускать новый боевой тест, пункт 164, installer или отдельный CMD. Менять игру только при заранее полученном новом отдельном typed consent и независимом preflight.

## Источники

- https://github.com/Bubb13/EEex/blob/v1.1.7/EEex/copy/EEex_scripts/EEex_Resource.lua
- https://github.com/Bubb13/EEex/blob/v1.1.7/EEex/copy/EEex_scripts/EEex_Sprite.lua
- https://github.com/Bubb13/EEex/blob/v1.1.7/EEex/copy/EEex_scripts/EEex_Utility.lua
- https://github.com/Bubb13/EEex/blob/v1.1.7/EEex/copy/EEex_scripts/EEex_Sprite_Patch.lua
- https://github.com/Bubb13/InfinityLoader/blob/master/EEex-Core-Shared-Files/source/EEex.cpp
- https://github.com/Bubb13/EEex-Docs/blob/master/source/EE%20Game%20Structures%20(x64)/Other/index.rst
