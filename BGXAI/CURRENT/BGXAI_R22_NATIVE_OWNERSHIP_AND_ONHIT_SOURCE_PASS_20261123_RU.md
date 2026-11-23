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


## Последующая source-only сверка существующего EPS/manual noninterrupt (без нового модуля)

После R22 CI прочитаны **настоящие существующие исходники**, а не воспроизведённая логика:

- `BGXAI/patchsets/ranged_fighter_guarded_20261119/BGXAI_WEAPON_NONINTERRUPT_PLAN_V1.lua`: функция `step(scene,previous,scoreReadOnly)` сохраняет текущее действие; `dispatchAuthorized=false`, `ordersSent=0`, `actionQueueCleared=false` при всех результатах. При изменениях бафа/стата инвалидирует только совет; `PENDING_REFRESH_TICKS=5` относится к *кэшу рекомендации*, не к задержке действий. `model_safe_window` проверяет ряд `provenNoManualOrder`, `provenEpsFree`, `provenActionBoundary`, `provenNoQueuedAction` и согласование snapshot/tick; эти поля **не доказаны реальным R4 или R13**, даже если synthetic scene может их утверждать. При favorable flags результат только `ADVISORY_SAFE_BOUNDARY_OBSERVED_NO_DISPATCH`, **никогда не dispatch**.
- `BGXAI/fox_new/experimental_081_eeex_action_provenance_readonly_source_only/BGXAI081_ACTION_PROVENANCE_READONLY.lua`: читает `m_curAction.m_actionID` в `pcall`, явно возвращает `queue_empty=nil`, `eps_queue_empty_verified=false`, `action_origin='UNKNOWN'`, `safe_to_dispatch=false`; `arbitrate()` возвращает HOLD даже для action ID 0. Нельзя объявлять очередь свободной из одного ID.
- `BGXAI/fox_new/experimental_082_eps_080_081_failclosed_integration_source_only/BGXAI082_QUEUE_GUARD_BRIDGE.lua`: принудительно выставляет `action_state.verified=false`, `origin_verified=false`, `queue_empty=nil`, `idle=false`; `review()` даёт `HOLD_NO_ENGINE_DISPATCH` и нулевые orders/local writes, несмотря на оптимистичную фикстуру.
- Реально существующий `test_weapon_noninterrupt_integration_v1.lua` уже проверяет сценарии смены fingerprint бафа, сохранения pending-плана и невозможности ранжировать альтернативу при непроверенных stat evidence. Это **ранее существовавшие тесты**, их не пересчитывать как новые 40 R22.

**Инженерное решение:** не делать новую очередь, новый ранкер или новый интерпретатор EPS. Следующая ограниченная работа — составить проверяемый мост *источника доказательства* (`R4 selected snapshot / R3 static ITM / R17 ammo` -> `V3.preview + V4/V5` -> `NONINTERRUPT.step` только advisory) без synthetic `verified=true` и без нарушения ESP/EPS. Пока настоящих данных для alt APR, launcher/ammo и происхождения ручной команды нет, результат `KEEP_CURRENT_WEAPON_NO_DISPATCH`. Реальная live безопасность переключения НЕ доказана; дальнейших игровых действий сейчас нет.
