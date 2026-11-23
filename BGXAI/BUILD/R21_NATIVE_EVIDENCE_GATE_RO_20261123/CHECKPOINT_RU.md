# BGXAI R21 — исходники без доступа к игре (23.11.2026)

**SOURCE CODE + LOCAL OFFLINE TEST PASS; CI not yet verified at publication. NO USER ACTION, NO GAME DEPLOY.**

## Результат
Реальный R20 пользовательский read-only отчёт `BGXAI_R20_EEEX_STATIC_20261123T183158663.json` (SHA256 `ac6fe71eb2aa7d17c8197cd34893ef47caa3ac957c8a66d4ea3c376490751cae`) подтверждает canonical LF source match для Resource/Sprite/Action из EEex v1.1.7. Он НЕ доказывает native pointer lifetime или работу API в конкретном runtime.

Проверена официальная **x64** документация EEex структуры `Item_Header_st` (114 байт) и `Item_ability_st` (56 байт), GitHub `Bubb13/EEex-Docs/source/EE Game Structures (x64)/Other/index.rst`. Подтверждено, что в upstream resource.lua формула `Item_Header_st.sizeof * abilityIndex` расходится с ожидаемым шагом 56 байт при индексах >0; для index1 +58 байт. Не утверждать runtime crash; DLL ABI и lifetime не проверялись.

**Новый чистый Python** `BGXAI_R21_EVIDENCE_GATE_RO.py` реализует fail-closed контроль происхождения R20 и ограниченного selected-attack scalar evidence. Не использует EEex, не читает игровые файлы, не регистрирует listener, не открывает Windows/WeiDU/движок, не выполняет действия. Он разрешает только статус `HOLD_NATIVE_POINTER_AND_ACTION_QUEUE` / `HOLD_STATIC_SOURCE_NOT_AUTHENTICATED`, всегда `KEEP_CURRENT_WEAPON_NO_DISPATCH`. Выбираемая сейчас APR-кодировка {raw 2 -> 2.0 APR, raw 7 -> 1.5 APR}; никакого прогнозирования APR альтернативных слотов. Опциональный sanitized snapshot — только кандидат текущего выбранного слота, без native event identity.

**28/28 LOCAL unittest PASS** по `test_r21_evidence_gate_ro.py`. Тесты включают подмену Git blob, некорректные статусы, missing false flags, fake EPS/alternatives/native authentication, raw APR, ammo/launcher alias. Новый workflow для независимых Windows и Linux offline CI опубликован отдельно; не объявлять SUCCESS, пока GitHub Actions не завершится.

## Source-only вариант для дальнейшего этапа
Официальный `EEex_Sprite_Hook_CheckBlockWeaponHit` получает `weaponAbility` прямо от движка; потенциально можно избежать manual `CItem.getAbility`. **Но регистрация listener может заблокировать урон при truthy return и не является началом действия**. Не вызывать/не ставить его до отдельного no-op протокола, подтверждения runtime safety и explicit typed user approval. Такой on-hit callback не даёт alt APR, provenance manual/EPS или полного effect fingerprint.

## Где работать дальше
Нужно изучить исходники `CResItem::Demand/Release` и ownership, безопасный event callback на уровне snapshot только в момент валидности ability; не менять R18 и не включать пассивную подписку без proof. Старый V1/V2/V5 ранкер и NONINTERRUPT сохранить. Проведённый R20 пункт 164 **не повторять**.

## Защитные флаги
`safeToCallGetAbility=false`; `safeToCallGetLauncher=false`; `safeToRegisterListener=false`; `weaponSwitchAuthorized=false`; `dispatchAuthorized=false`; `installAuthorized=false`.

Стадии: R21 CODE PASS; 28/28 LOCAL TEST PASS; independent CI pending; SOURCE DEPLOY tracked in GitHub/Library; GAME DEPLOY NO; LIVE NO.

Источники: `BGXAI/CURRENT/BGXAI_R20_USER_STATIC_AUDIT_PASS_20261123_RU.md`; `BGXAI/CURRENT/BGXAI_R21_NATIVE_ABILITY_STRIDE_SOURCE_AUDIT_20261123_RU.md`; GitHub Bubb13/EEex v1.1.7; Bubb13/EEex-Docs x64.
