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

## Следующий шаг пользователя и безопасная параллельная работа
- **Пользователь:** один раз запустить существующий `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd` -> **164**; приложить `C:\Users\Drevo\Documents\BGXAI_LIVE_REPORTS\BGXAI_R20_EEEX_STATIC_*.json` либо точный STOP. Игру запускать не надо; пункт 164 только читает файлы и пишет отчёт вне игры.
- **Разработка без новых игровых действий:** source-only сверить определения runtime `sizeof`, исследовать официальный безопасный способ получить/удержать заголовок способности без прямого `pRes.pHeader` и зафиксировать проверяемый no-dispatch контракт. При отсутствии доказательств продолжать HOLD, без пассивного native runtime pilot.
- **R21 CODE:** только аналитический документ; **R21 OFFLINE TEST:** не запускался как новый набор; **DEPLOY/LIVE:** NO. R20 релиз/CI уже PASS, но R20 USER STATIC SCAN NOT RUN.

## Ссылки
- EEex source: https://github.com/Bubb13/EEex/blob/v1.1.7/EEex/copy/EEex_scripts/EEex_Resource.lua
- IESDP: https://iesdp.bgforge.net/file_formats/ie_formats/itm_v1.htm
- R20: `BGXAI/CURRENT/BGXAI_R20_ONEFILE_MENU164_20261123_RU.md`
