# BGXAI R22 — аудит владения ресурсом и безопасной передачи способности (SOURCE ONLY)

Дата 23.11.2026. **Ничего не устанавливать.** Код предназначен исключительно для автономных офлайн-проверок; не является игровым модом. `BGXAI_UPDATE.cmd`, EEex, EPS, WeiDU, сейвы, BG_EET_RU и BG Voice RU не меняются.

## Новые исходные факты

1. В источнике `Bubb13/EEex v1.1.7`, `EEex_Resource.lua` `CItem.getAbility` разыменовывает `item.pRes.pHeader` без вызова `Demand` и без известных условий lifetime. В смежном `EEex_Resource_GetItemAbility` вычисляет адрес записи `Item_ability_st` по ошибочно выглядящему stride `Item_Header_st.sizeof * index`. В x64 документации указано 114 против 56 байт; для index 1 отклонение равно 58 байт. Нельзя утверждать crash в текущей игре, не подтвердив runtime ABI.
2. В `Bubb13/InfinityLoader`, `EEex-Core-Shared-Files/source/EEex.cpp`, в нескольких фрагментах C++ движковый `CItem::Demand()` вызывается перед `CItem::GetAbility()`. Это **наблюдаемый порядок**, а не доказательство достаточности `Demand`, согласованной пары `Release`, безопасности при другом потоке или корректности Lua привязки. Документация EEex CItem::Demand перечисляет функцию, но не описывает контракт времени жизни; `CItem::Release` не установлен в пределах проверенных источников, не делать вывод о его существовании или отсутствии во всей сборке.
3. C++ `checkBlockWeaponHit` передаёт в Lua `pWeaponAbility` как `Item_ability_st`, а Lua `EEex_Sprite_Hook_CheckBlockWeaponHit` помещает его в `listenerContext`. `EEex_Utility_TryIgnore` возвращает результат слушателя, после которого truthy в `BlockWeaponHit` даёт `return true`; официальный `EEex_Sprite_Patch.lua` поясняет: `false` не меняет поведение, `true` блокирует базовый урон и эффекты оружия. Следовательно **регистрация чужого listener — потенциальное боевое изменение**, а не безусловно безвредный read-only action. Native lifetime `pWeaponAbility` внутри callback не подтверждён, даже если он сформирован движком.
4. Событие on-hit не равно pre-attack: нет данных по другим слотом, APR, резистам или действиям EPS. Его нельзя использовать как полноценную систему выбора оружия.

## Новый код

- `BGXAI_R22_NATIVE_OWNER_AUDIT_RO.py`: чистая функция `inspect(source_fragments, documented_sizes, verified_blobs)` проверяет десять source-предикатов. Обязательное состояние `SOURCE_CHAIN_MATCHED_LIFETIME_HOLD` либо `SOURCE_DRIFT_OR_INCOMPLETE_LIFETIME_HOLD`. Нет разрешений на native вызовы, регистрацию, установку, смену оружия или вмешательство в игру **даже при PASS**.
- `R22_UPSTREAM_EXCERPTS_VERIFIED_20261123.json`: минимальные зафиксированные excerpts по проверенным через GitHub коннектор файлам, с Git blob sha и ссылками. Они НЕ являются полной копией исходников, а hash-pins в JSON сами по себе не доказывают подлинность; полные первичные файлы проверены отдельно по соединению GitHub. Содержимое можно сверить вручную.
- `test_r22_native_owner_audit_ro.py`: 40 автономных тестов (положительный baseline и отрицательные изменения stride, Demand, callback, listener-result, pins, структурных размеров, типовой отказ).
- `R22_SOURCE_ONLY_VERDICT.json`: детальный вывод скрипта на фиксированных фрагментах; все разрешения FALSE.
- `SHA256_MANIFEST.json`: контрольные суммы файлов, проверяются CI на Windows и Ubuntu.

## Как проверить только в репозитории (не в игре)

```console
cd BGXAI/BUILD/R22_NATIVE_OWNERSHIP_SOURCE_RO_20261123
python -m unittest -v test_r22_native_owner_audit_ro.py
```

Игрока **не просить** повторять `164`, игровые бои или переустановки. Следующие безопасные задачи: пройти source-аудит состояния очереди EPS/manual и существующего NONINTERRUPT, пересмотреть стратегию получения альтернативных APR через офлайн ITM + live selected APR, избегая native pointer. R22 не подтверждает full effects, launcher/ammo, alternates и происхождение команд; auto switch OFF.
