# BGXAI — Inventory Weapon Priority V4 corrected planner (2026-11-26)

## Real new code and purpose
**Model-based situational weapon candidate selection from the 16 true BG(2)EE backpack slots 18..33**, reusing V1's noninterrupting scoring contract, not writing another game observer. Takes corrected V3 raw backpack snapshot, R2-style quick weapon slots, other top-level equipped slots 0..17 and 34, externally modelled V3/V4/V5 utility/effect scores, target and context. Only recommends a *unique resref* to a *currently EMPTY, class-allowed* quick weapon slot; never overwrites. Validates whole top-level equipment visibility, excludes duplicate items in offhand, ammo/quick items, magic-weapon, other quickweapons, or backpack. No external item/container instance identity; bags-of-holding contents not enumerated.

This module is **ADVISORY ONLY**, cannot equip or generate LOCALS, cannot assert real per-alternative APR. All results mark `executable=false`, `ordersSent=0`, `inventoryMoveAuthorized=false`, `manualEpsOriginVerified=false`, `engineFinalAlternativeStatsVerified=false`, `itemTransferSemanticsVerified=false`. In particular, source-only boolean `scene.*Verified=true` is a *mock contract*, not live verification. It never modifies current game or action queue.

Evidence: IESDP BG(2)EE SLOTS.IDS `15-17` quick items, `18-33` backpack, `34` magical-weapon, `35-38` quickweapons. IESDP action 385 `XEquipItem` can target a slot, but does not guarantee unique *instance*, safe queue boundary or conserved inventory after action; `EquipItemEx` does not move item, `FillSlot` destroys target contents. No active command permitted.

## 28.11.2026 — минимальное согласование с уже существующим V3 (SOURCE ONLY)

PRIOR WORK GATE: V3 уже содержит проверенный на синтетических тестах special-case для *доказанно бесполезного* текущего оружия (иммунитет цели, 100% резист, отсутствие боеприпасов/дальности и прочие явно подтверждённые причины). V4 до этого сохранял обязательный порог max(2, 15%) даже при utility текущего оружия 0: слабая, но реально действующая альтернатива из рюкзака необоснованно отсекалась. В V4 исправлено только это расхождение, без нового переключателя, listener или команд.

Если V3-подобные `currentWeaponUnusableVerified=true` и `currentWeaponUnusableReason` указаны явно, V4 требует причину из закрытого списка, непротиворечивый current score <=0 и положительную utility альтернативы; порог тогда 0. Неизвестная/ложно заявленная причина или положительный score при доказанной бесполезности дают HOLD. При отсутствии таких сведений прежний hysteresis сохранён. Семь новых регрессионных сценариев добавлены в существующий `test_backpack16_priority_v4.lua`; выполнение реальной Lua/CI проверки ещё НЕ подтверждено в этой контрольной точке.

Ограничение: любой caller может передать `*Verified=true` как данные тестовой модели. Это НЕ нативное EEex-доказательство, и V4 по-прежнему всегда выдаёт `executable=false`, `dispatchAuthorized=false`, `inventoryMoveAuthorized=false`, `ordersSent=0`. Не устанавливать в игру по одному такому результату.

## 28.11.2026 — прямое соединение V3 → V4 (только модель, не игра)

Вместо дополнительного оценщика переиспользован **тот же V3 `scored_weapon`**: добавлен `V3.scoreBackpackCandidate(scene, weapon)` для одного оружия в настоящем слоте рюкзака 18–33 (без имитации, будто оно уже экипировано). Он оценивает персонажа и текущего врага, тип AC, сопротивления и итоговый *модельный* DPR; отсутствие APR, THAC0, эффектов/предметной совместимости или разные снимки дают HOLD. Он всегда возвращает только non-executable модель: `engineFinalAlternativeStatsVerified=false`, `dispatchAuthorized=false`.

В **существующий V4** добавлен `planWithV3(backpack,quick,other,scene,candidates,v3Scene,previous,v3)` — чистый компоновщик, вызывающий исходные `V3.preview`, `V3.scoreBackpackCandidate` и уже имеющийся `V4.plan`. Дважды связывает актёра с одной целью, требует одинаковый `snapshotId`/`tick`, проверяет реальный `resref` каждого quickslot против модельного V3, сохраняет `v3Next` для двухкадровой стабилизации. В этом пути `c.predictedUtility`, переданный вызывающим кодом, категорически отвергается: численная полезность выводится только из V3. Не изменяет исходные таблицы или игру. Внешний старый `plan` оставлен для совместимости, по-прежнему dry-run.

**Тесты:** ровно 6 новых в уже существующем `test_weapon_priority_lua_v3.lua` — на идентичном GitHub исходнике V3 локально на LuaTeX 5.3: **72/72 PASS**, SHA git blob совпали; 7 новых интеграционных сценариев в существующем `test_backpack16_priority_v4.lua` (в сумме 34), включая подмену score, смену цели, неизвестный APR, текущую иммунность и отсутствие диспатча. Регрессионный запускатор объединён с прежним V3/V4/V5 набором, ожидает **490** модельных проверок, а прежний GitHub workflow запускает его на push по файлам V4. **Интеграционные 7 новых сценариев прогнаны локально: 7/7 PASS на точных GitHub Lua исходниках V3 (blob `22e9a452f589a597ab38117a4c6df5f536cd721e`) и V4 (blob `e79ed0040a49be93e92cb9e2edc6ff2e39579c71`) с одноимённой локальной модельной обвязкой; точный полный GitHub-файл тестов V4 (34) и CI набор (490) НЕ подтверждены PASS** — не выдавать составленные тесты за исполненные.

**Главное незавершённое:** настоящий EEex-поставщик альтернативных APR, THAC0, повреждений/бафов и защиты *по одному игровому кадру*, а также реальный арбитраж EPS/ручной команды/раунда. Результаты `planWithV3` нельзя считать готовой игрой и подключать к `XEquipItem` без доказательств/typed install. R47 при HOLD не повторять. Обновлятор и игровые файлы не изменены.

## What this removes as a blocker
Previously V1 used **incorrect 15..34** backpack map and only checked duplicates in backpack+quickweapons; V4 corrects mapping, covers all top-level slots and strict no-overwrite, reuses existing external scorer. V4 is not yet plugged into R37 and is NOT actual automation; native EEex loaded ITM stats/provenance and execution transaction remain unproven.

## Status
CODE: new V4 pure Lua planner. TEST: `test_backpack16_priority_v4.lua` includes 20 synthetic positives/negatives; GitHub Actions Lua5.3/5.4/LuaJIT must be verified separately. DEPLOY/LIVE NO. No game files, scripts, one-CMD launcher or saves touched.
