# BGXAI R23 — переиспользование выбора оружия и защиты EPS, аудит реальных исходников (23.11.2026)

## Назначение

После R22 пользователь снова подтвердил **автопродолжение при PASS**. Обязательное правило обновлено в `BGXAI/CURRENT/BGXAI_AUTO_CONTINUE_RULE_20261122_RU.md`; не требовать `+` и не завершать работу в середине доступного безопасного этапа. НЕТ разрешения на активную игровую установку.

## Проверено: 15/15 статических условий PASS

На branch `bg-eet-ai` через GitHub подключение прочитаны подлинные исходники:

| Существующий компонент | Git blob | Реальный вывод |
|---|---|---|
| `BGXAI_WEAPON_NONINTERRUPT_PLAN_V1.lua` | `f72726af797f05e2330b57d5a71c05ee5a43fadd` | `M.step` принимает внедрённый read-only scorer; все возвращаемые состояния `ordersSent=0`, `dispatchAuthorized=false`, `actionQueueCleared=false`, `currentActionPreserved=true`; проверки ручной/EPS очереди обязательны; изменение бафа инвалидирует только совет |
| `BGXAI081_ACTION_PROVENANCE_READONLY.lua` | `1a366f0600c140f7757bb7780ab26ea4f59ff74f` | `queue_empty=nil`, `action_origin=UNKNOWN`; даже `actionID==0` не разрешает диспетчеризацию |
| `BGXAI082_QUEUE_GUARD_BRIDGE.lua` | `4f89a15b26e258179806e4474596d3e74dd6aaba` | принудительный HOLD `HOLD_NO_ENGINE_DISPATCH`, не позволять оптимистичной фикстуре переписать `origin_verified=false` |
| `BGXAI_WEAPON_PRIORITY_LUA_V3.lua` | `caa3b136f1a27c60908a436b567cf6ae406a5cc5` | уже есть `M.preview`; SOURCE ONLY, но требует `COMPLETE_EFFECTIVE_SNAPSHOT`, доказанных целей/боеприпасов и полного состава |
| `BGXAI_WEAPON_CURRENT_STATS_BRIDGE.lua` | `c4903911f47293a44b0de62ee736268a19f172da` | `M.audit` требует allActiveEffectsObserved, буфы и пересчёт APR/THAC0/урона **каждого** альтернативного слота; synthetic `verified=true` нельзя приравнять к игре |

Дополнительно проверены обязанности V4 `bcf88726f8de62242f89293fb8afc706ae4e6e26` (on-hit и active-effect provenance) и V5 `95a854a374a1308735b74ecf15a06543f53fe12c` (класс/kit/proficiency APR и источник). Число **15/15** означает только *проверку исходного кода статическими утверждениями*, не 15 новых игровых боёв и не native Lua tests. Манифест: `BGXAI/BUILD/R23_EXISTING_PIPELINE_SOURCE_AUDIT_20261123/R23_SOURCE_GATE_VERDICT.json`.

## Строгая граница достоверности

1. R20: `UPSTREAM_V117_LF_EQUIVALENT_STATIC_ONLY` — установленный Lua-исходник EEex найден, но DLL ABI и API-lifetime не доказаны.
2. R13.2/R4: ранее LIVE прочитаны текущие selected APR, selected slot и некоторые target raw поля. **Не** наблюдали в реальном времени APR другого слота и полный список effects.
3. R3: проверенные ITM/SPL/2DA из **ранней** игровой сессии, использовать как исторический статический справочник; R17: изменения количества стрел около событий, без нативного доказательства launcher/ammo пары и shot count.
4. R21: `HOLD_NATIVE_POINTER_AND_ACTION_QUEUE`, R22: `SOURCE_CHAIN_MATCHED_LIFETIME_HOLD`; оба запрещают `getAbility/getLauncher`, callbacks, commands.
5. `NONINTERRUPT` гарантирует отсутствие команд **только в своей чистой функции**; не доказывает свободную очередь EPS или ручных команд в runtime. Нельзя передавать fabricated `scene.activity.source=INDEPENDENTLY_AUDITED...`, `provenEpsFree=true` или `allActiveEffectsObserved=true` на основании пожелания/мока.

## Рабочее решение после PASS

**НЕ создавать второй ранкер, queue guard или ещё один формальный HOLD-движок.** Для следующей функциональной source-only интеграции требуются только adapters/provenance от реальных данных к имеющемуся `V3.preview + V4/V5 + NONINTERRUPT.step`. На текущих реальных данных ни один разрешительный adapter заполнить нельзя; **до верификации остаётся `KEEP_CURRENT_WEAPON_NO_DISPATCH`**.

Новая gameplay capability НЕ запущена; `CODE=SOURCE AUDIT PASS`, `TEST=15/15 STATIC CHECK PASS`, `DEPLOY=NO`, `LIVE R23=NO`. Ранее реально работающий TD15/R13.2 не трогать; R20/164 не повторять, игре/сейвам/EPS/WeiDU/обновлятору не наносить изменений.

## Следующий безопасный блок

Рассмотреть неинвазивный **read-only offline** способ получить точную пару weapon ability + launcher/ammo из native ITM без `item.pRes.pHeader` (и сопоставить с R3/R17), сохраняя явные `STATIC_CANDIDATE` vs `LIVE_VERIFIED`. Источник должен давать отдельный независимый сигнал, а не повторять отрицательный тест. Нельзя выдавать офлайн расчёт прогнозного APR за runtime alternate APR. Для любого нового игрового EEex hook/deploy требуется отдельное явное typed согласие после audit и backup. Без new engine evidence не разрешать переключение.

Политика пользователя: автоматически продолжать полезные безопасные шаги после PASS **в этом текущем обращении**, не в фоне.
