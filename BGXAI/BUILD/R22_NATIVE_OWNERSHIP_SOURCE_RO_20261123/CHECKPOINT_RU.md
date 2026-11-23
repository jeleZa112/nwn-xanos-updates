# BGXAI R22 — Demand/GetAbility ownership + engine-provided hit ability source audit

**Дата:** 23.11.2026. **Стадия: CODE SOURCE ONLY; LOCAL TEST 40/40 PASS. CI:** проверять только по реальным запускам GitHub Actions, а не по одному факту отправки workflow. **Game deploy NO / LIVE R22 NO.**

Предыдущий R21 офлайн evidence gate 28/28 PASS Windows+Linux, R20 installed EEex static scan PASS, TD15/R13.2 LIVE для четырёх событий одной цели остаются без изменений. Не запускать menu164 повторно.

## Новые доказательства, отличающиеся от R21

1. В исходниках InfinityLoader C++ `curWeaponIn->Demand();` непосредственно предшествует `curWeaponIn->GetAbility(curAttackNum);`. Это факт порядка вызова; **не подтверждает** RAII/Release, успешность Demand, lifetime или перенос в Lua. Документация функции CItem::Demand не содержит гарантий. В Lua EEex v1.1.7 `CItem.getAbility` напрямую вызывает `item.pRes.pHeader:getAbility` без Demand.
2. C++ `checkBlockWeaponHit` передаёт `pWeaponAbility` в Lua через `tolua_pushusertype` и ожидает boolean. Lua `BlockWeaponHit` использует `EEex_Utility_TryIgnore` и при truthy return блокирует удар; patch-документация прямо фиксирует `false -> no change`, `true -> block weapon damage and on-hit effects`. Следовательно это **не безопасный pre-attack observation hook по умолчанию**, даже если Lua-код только планируется как наблюдатель. До отдельного proof **регистрации listener нет**.
3. Подтверждён x64 источник 114/56 и ошибочный stride в Item getAbility, смещение index>0 на 58*index; у установленной EEex Lua исходники в R20 LF-equivalent upstream. Native ABI/DLL и runtime-crash не подтверждены.

## Доставленные файлы

- `BGXAI_R22_NATIVE_OWNER_AUDIT_RO.py`: 10 проверок источников, жёсткий HOLD при любом результате. Вход только в виде source snippets и скалярного документированного размера; никаких native вызовов, регистрации listener, установок, записи игры или порядка действий.
- `R22_UPSTREAM_EXCERPTS_VERIFIED_20261123.json`: краткие excerpts и SHA Git blob, первичные full blobs прочитаны через GitHub connector. Отдельно публичные anchors; эти excerpts сами не верифицируют full source, так как нет полного хэша содержимого в них.
- `test_r22_native_owner_audit_ro.py`: 40/40 локальных тестов, включая source drift и всех gates off.
- `R22_SOURCE_ONLY_VERDICT.json`: результат baseline `SOURCE_CHAIN_MATCHED_LIFETIME_HOLD` (все 10 критериев совпали; game dispatch всё ещё запрещён).
- `SHA256_MANIFEST.json`: SHA256 и bytes, проверяемые независимым CI на Windows/Linux.
- `.github/workflows/bgxai-r22-native-ownership-source-ci.yml`: read-only CI, 40 тестов + SHA/policy.

## Принцип решения

Нельзя скрытно патчить EEex, делать `CItem:Demand()` вручную, обращаться к `pAbilities`/`pHeader` или ставить on-hit listener без доказанной работы и разрешения на установку. Сохраняем существующий работающий TD15, EPS, R4 selected-only и ранкер V1/V2/V5 + NONINTERRUPT. Нет проверенных alt APR, full effects или EPS/manual queue. Следующий безопасный источник решений: офлайн документы ITM/R3, текущая selected-only R4 телеметрия, и source-only анализ EPS/manual action queue. Не создавать дублирующий ranking framework.

**Источники:**
- https://github.com/Bubb13/EEex/blob/v1.1.7/EEex/copy/EEex_scripts/EEex_Resource.lua
- https://github.com/Bubb13/EEex/blob/v1.1.7/EEex/copy/EEex_scripts/EEex_Sprite.lua
- https://github.com/Bubb13/EEex/blob/v1.1.7/EEex/copy/EEex_scripts/EEex_Utility.lua
- https://github.com/Bubb13/EEex/blob/v1.1.7/EEex/copy/EEex_scripts/EEex_Sprite_Patch.lua
- https://github.com/Bubb13/InfinityLoader/blob/master/EEex-Core-Shared-Files/source/EEex.cpp
- https://github.com/Bubb13/EEex-Docs/blob/master/source/EE%20Game%20Structures%20(x64)/Other/index.rst
- https://github.com/Bubb13/EEex-Docs/blob/master/source/EE%20Game%20Classes%20(x86)/CItem/index.rst
