# BGXAI R21 — статический аудит stride и lifetime Item_ability_st (23.11.2026)

## Стадия
**SOURCE AUDIT ONLY.** Новые игровые файлы, Lua, WeiDU, EPS, SCS, BG Voice RU, BG_EET_RU и сохранения не изменялись. Никаких новых команд на Windows пользователю не требуется. R18 НЕ установлен, auto weapon switch остаётся OFF.

## Проверенные источники
- Установленная ранее базовая игровая телеметрия: TD15/R13.2, четыре DEFENSE-события, девять полей, без HOLD. Отчёт: `BGXAI/CURRENT/BGXAI_R13_2_LIVE_DEFENSE_PASS_APR_20261123_RU.md`.
- R18 source-only: `BGXAI/BUILD/R18_EEEX_NATIVE_LINK_RO_20261123/BGXAI_R18_EEEX_ADAPTER_CANDIDATE.lua` и `BGXAI_R18_NATIVE_LINK_PROBE_RO.lua`; 58/58 mock CI (предыдущий этап).
- R19: `BGXAI/BUILD/R19_INSTALLED_EEEX_STATIC_RO_20261123/BGXAI_R19_INSTALLED_EEEX_AUDIT_RO.py` — сравнение SHA/методов, но НЕ безопасность указателей.
- Официальный EEex тег `Bubb13/EEex v1.1.7`, Git blob SHA `EEex_Resource.lua:5ecd3c2f9e9bcc6cbd317653fc057a06d956916b`, строки 164–173; `EEex_Sprite.lua:b2d8d930c47785737bd30dad08e9f35a9d859578`, строки 916–926.
- IESDP ITM V1: главный файловый заголовок 114 (0x72) байт; запись extended ability 56 (0x38) байт. Это размеры файлового формата; соответствие runtime `sizeof` должно быть отдельно подтверждено.

## Новая source-level находка
В upstream `EEex_Resource_GetItemAbility(itemHeader, abilityIndex)`:
```lua
if itemHeader.abilityCount <= abilityIndex then return end
return EEex_PtrToUD(EEex_UDToPtr(itemHeader) + itemHeader.abilityOffset + Item_Header_st.sizeof * abilityIndex, "Item_ability_st")
```
Функция `CItem.getAbility` вызывает её через `item.pRes.pHeader:getAbility(abilityIndex)`. Выражение адресации использует **`Item_Header_st.sizeof`**, а не `Item_ability_st.sizeof`. Если native определения совпадают с файловым форматом 114/56, для `abilityIndex > 0` расчёт отличается от ожидаемого на `58 * abilityIndex` байт. Для `abilityIndex=0` данная конкретная ошибка шага не проявляется, **но lifetime заголовка всё равно неизвестен**.

Ещё один наблюдаемый риск: проверяется верхняя граница `abilityIndex`, но внутри upstream helper не видно проверки `abilityIndex >= 0`. R18 пока проверяет неотрицательность на своём уровне; это не основание запускать native pointer path.

**Статус находки: SUSPECTED_NATIVE_ABILITY_STRIDE_MISMATCH; НЕ заявлять подтверждённый runtime-crash или конкретный дефект установленного EEex.** R19 проверяет присутствие этих callsites, а не правильность адресации. Успешный R19 SHA match поэтому не снимает блокер.

## Жёсткие защитные инварианты
1. `safeToCallGetAbility=false`, `safeToCallGetLauncher=false`, `safeToRegisterListener=false`, `weaponSwitchAuthorized=false`, `installAuthorized=false`. Никаких испытаний подозрительного метода на реальной игре.
2. `pcall` в кандидате R18 не является гарантией защиты от native access violation и не доказывает lifetime `CResItem.pHeader`.
3. Не исправлять `Bubb13/EEex` или игровые файлы локальной подменой; сначала установить точные native определения `Item_Header_st.sizeof` и `Item_ability_st.sizeof`, затем получить безопасный upstream-supported API/проверенный ресурсный handle и доказать его lifetime.
4. Запретить переключение до подтверждения ID текущего действия, способности, пары launcher/ammo, effect fingerprint, APR **альтернативных** слотов и сохранения ручной/EPS очереди.
5. Не дублировать ранкер V1/V2/V5 и NONINTERRUPT. Не повторять прежние бои и прочитанные R3/R13 логи.

## Следующее действие после фактического R20 скана

Пользовательский R20/164 **уже выполнен**. Нового действия для пользователя на этом source-only этапе нет. Дальнейший R21 — только static investigation безопасной native-структуры и жизненного цикла ресурса без установки, listener или переключения оружия.

## Ссылки
- EEex source: https://github.com/Bubb13/EEex/blob/v1.1.7/EEex/copy/EEex_scripts/EEex_Resource.lua
- IESDP: https://iesdp.bgforge.net/file_formats/ie_formats/itm_v1.htm
- R20: `BGXAI/CURRENT/BGXAI_R20_ONEFILE_MENU164_20261123_RU.md`

## 23.11.2026 — ПРОВЕРЕНО ПОСЛЕ ПОЛУЧЕНИЯ R20 / R21 SOURCE AUDIT V2

**R20 пользовательский скан выполнен, повторять пункт 164 не нужно.** Отчёт `BGXAI_R20_EEEX_STATIC_20261123T183158663.json`, 3162 байт, SHA256 `ac6fe71eb2aa7d17c8197cd34893ef47caa3ac957c8a66d4ea3c376490751cae`. Итог `UPSTREAM_V117_LF_EQUIVALENT_STATIC_ONLY`: все три файла `EEex_Resource.lua`, `EEex_Sprite.lua`, `EEex_Action.lua` present+callsites+canonical LF match, точные raw byte hash не совпали. Bootstrap Lua существует. Отчёт прямо запрещает `getAbility`, `getLauncher`, нового listener и weapon switching. Полный **санитизированный** checkpoint: `BGXAI/CURRENT/BGXAI_R20_USER_STATIC_AUDIT_PASS_20261123_RU.md`. Не публиковать неочищенные пользовательские логи.

**Доказательства предполагаемого дефекта шаговой адресации стали сильнее:**
- Официальный EEex `v1.1.7` и `v1.3.1` дают **тот же Git blob** `EEex_Resource.lua` `5ecd3c2f9e9bcc6cbd317653fc057a06d956916b`. В функции spell counterpart строка 160 корректно применяет `Spell_ability_st.sizeof * index`, а item counterpart строка 166 использует **`Item_Header_st.sizeof * index`** для возврата `Item_ability_st`.
- Документация EEex *engine-x86 Other Structures*, именно **engine structures**, а не только IESDP файловые заголовки, показывает поля `Item_Header_st` от 0x00 до 0x71 (0x72=114 байт) и `Item_ability_st` от 0x00 до 0x37 (0x38=56 байт). Дополнительно генератор InfinityLoader `Core-Shared-Files/generate_bindings/in/packing.txt` для обеих структур задаёт packing=1. Это подтверждает ожидаемую разницу шагов **58 байт × abilityIndex**, если бинарные binding-типы пользователя соответствуют данным определениям.
- В `EEex-Core-Shared-Files/source/EEex.cpp` upstream C++ в пути обработки атак сначала выполняет `curWeaponIn->Demand()`, затем `curWeaponIn->GetAbility(curAttackNum)`. Это показывает использование **движкового C++ GetAbility с Demand**, но **не доказывает**, что Lua wrapper `CItem.getAbility` безопасен, что ресурс держится достаточно долго, или что вызовы можно переносить в R18.
- В документации EEex отдельно предупреждено: форматы на диске не обязательно 1:1 соответствуют структурам памяти. Поэтому **actual installed DLL/native struct ABI and pointer lifetime still UNVERIFIED**. Отчёт R20 проверял Lua-исходники, не DLL. Физический runtime crash не заявлять.

**Решение:** оставляем `R18 CItem:getAbility` и `sprite:getLauncher` в HOLD без игры. Не патчить upstream/локальный EEex, не инициировать upgrade, не пробовать чтение способности даже при index 0 без lifetime-guard; `pcall` не защищает от C++ access violation. Использовать уже проверенные R4/R13 READ ONLY selected slot, selected APR, target raw как узко допустимые наблюдения, НЕ как доказательство alt APR, item effect state, launcher-pair или происхождения EPS/manual.

**Следующая техническая работа без новых запросов пользователю:** исследовать возможность **подтверждённого движком** безопасного API/события с готовой валидной ability-парой, без прямой адресной арифметики и без нарушения очереди; если такого API нет — использовать только статические ITM/R3 и ограниченную выбранную телеметрию R4, статус HOLD. Запрет auto dispatch и switching до полноценного доказательства. Никаких повторов 164/бой/WeiDU.

**Статус:** R20 USER STATIC PASS; R21 UPSTREAM STRIDE MISMATCH REPRODUCED AT SOURCE LEVEL; R21 NEW GAME CODE/DEPLOY/LIVE NONE; all switch authorization fields remain FALSE.

Источники:
- https://github.com/Bubb13/EEex/blob/v1.1.7/EEex/copy/EEex_scripts/EEex_Resource.lua
- https://github.com/Bubb13/EEex/blob/v1.3.1/EEex/copy/EEex_scripts/EEex_Resource.lua
- https://eeex-docs.readthedocs.io/en/engine-x86/EE%20Game%20Structures%20(x86)/Other/index.html
- https://github.com/Bubb13/InfinityLoader/blob/master/Core-Shared-Files/generate_bindings/in/packing.txt
- https://github.com/Bubb13/InfinityLoader/blob/master/EEex-Core-Shared-Files/source/EEex.cpp


## 23.11.2026 — безопасная альтернатива для дальнейшего source-only исследования

Из **официального EEex v1.1.7**, `EEex_Sprite.lua` строки 1042–1056: `EEex_Sprite_Hook_CheckBlockWeaponHit(attackingSprite,targetSprite,weapon,weaponAbility)` формирует `listenerContext` с `attackingSprite`, `targetSprite`, `weapon`, `weaponAbility` — этот `weaponAbility` **передаётся движком на этапе проверки попадания**, поэтому в самом callback не нужен `item:getAbility(index)` и ручная адресная арифметика. Но это **не runtime proof** и не событие начала действия; оно может приходить после выбора оружия. Метод `EEex_Sprite_AddBlockWeaponHitListener` добавляет callback в реестр. В v1.1.7 **любой truthy return слушателя приводит к `return true` из CheckBlockWeaponHit**, что может отменить повреждение/эффекты. **Никогда не регистрировать такой listener без отдельного согласия, no-op contract, read-only ограничений и защищённых тестов.** Вариант для будущего: `ENGINE_SUPPLIED_ABILITY_ON_HIT_ONLY`; даже при безопасном событии он не доказывает альтернативные слоты, APR, время решения или launcher/ammo из других процессов.

Приоритет исследования:
1. Сначала использовать уже установленный источник R4/R13 (без новых native pointers) и офлайн R3/R17 контракт; запрет на dispatch.
2. Для native альтернативы проверить жизненный цикл `weaponAbility` только **внутри** callback и факт его передачи из engine; не сохранять/логировать pointer, не обращаться за пределами вызова.
3. Раздельно проверить `weapon` (что именно передано в слот боеприпаса), launcher/ammo и источник действия; не делать вывод о launcher из наличия оружия в quickslot.
4. Пока указанные условия не подтверждены **`safeToRegisterListener=false`**, никакой установки, ручных/C++ вызовов, switch или нового боя.

Source refs:
- https://github.com/Bubb13/EEex/blob/v1.1.7/EEex/copy/EEex_scripts/EEex_Sprite.lua#L992-L1056
- https://github.com/Bubb13/InfinityLoader/blob/master/EEex-Core-Shared-Files/source/EEex.cpp
