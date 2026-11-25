# BGXAI R31 — расширение установленного R27 через ACTION_CONTEXT_V3

## АКТУАЛЬНО 25.11.2026 — menu171 уже подключён, не повторять интеграцию

**Новая точка продолжения (после прежних записей SOURCE ONLY):** существующий `BGXAI_UPDATE.cmd` не изменён; его `BGXAI_SYNC.ps1` уже содержит пункт **171 — R31 V3**. Манифест `BGXAI/fox_new/BOOTSTRAP_PIN.json` закрепил immutable commit `fe992a60a4c7880912270cfed27be59c6a0bf359`, `script_size=79941` (лимит 80000), SHA256 `c998ff6607ee3915b9cbb3c9b31955f715bee425b5ed882e04e1af1d515ed4aa`. Предыдущие dispatch 1–170 сохранены.

**R31 source-only полезная функциональность:** заменяющий кандидат старого R27, но не второй параллельный наблюдатель; один EEex listener, RAW `m_queuedActions.m_nCount`, снимки действия/derivedStats. Source Lua 47 550 байт SHA256 `5a1f6b32db920a005161734605c8b3273614a1318d8b1b57dac79ed022a00f38`, guarded Python 20 305 байт SHA256 `0ac97a702c4ac5919549a5a54cf9ef6a01a8fbd582273fc556fe9c82a60950ee`. Raw queue count=0 НЕ означает проверенную пустую очередь EPS/manual и не даёт права переключения оружия.

**CODE/TEST:** [независимый CI menu171 PIN + CMD + Windows PS5.1](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45561570321) — SUCCESS (Windows и Ubuntu); [R31 SOURCE/guarded/mock + PS5.1 и три Lua](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45561576119) — SUCCESS (Windows/Linux). Отдельные исторические workflows могут продолжать краснеть на ожидаемых старых пинах; это не повод объявлять общий CI полностью зелёным.

**DEPLOY R31=NO / LIVE R31=NO.** R30 real READ ONLY PASS показал WeiDU 150, R27 №149, R29 №150. Игра, V6, R27, R29, EPS и сейвы не изменены. Native WeiDU overlay в пользовательской EET ещё не проверен. Typed согласия на установку R31 нет.

**Ровно следующий пользовательский шаг:** прежний `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd` → **171** → **1 (RO preflight)**, затем передать новый `BGXAI_R31_PREFLIGHT_*.json` из `Documents\BGXAI_LIVE_REPORTS`. Не выбирать 171→2 (install), не применять старые R27/R29 rollback и не повторять 170. При HOLD — STOP, без автоматического повтора. Даже PASS не разрешает установку. Следующая разработка после отчёта — нативная проверка безопасности WeiDU, потом отдельное буквальное typed-согласие, один live-passive capture и только затем real alternate APR/effects для Weapon Priority.

---


**25.11.2026 — CODE/CI PASS, DEPLOY NO, LIVE NO.** Новый код является SOURCE ONLY. В игре ничего не менялось. Это не второй отдельный observer и не новая функция выбора оружия.

## Подтверждённая исходная сборка

- Пользователь запустил R30 пункт 170: READ ONLY PASS, 150 компонентов WeiDU, R27 = 149-й, R29 = последний (150-й).
- Старый установленный R27: SHA256 e5eb400c56ffb1bc23344a0cf30dcc724d8d18fc2752fabd1c2c63cdcca73735; в реальной игре ранее 24/24 callback.
- Неустановленный R27/V3 + ACTION_CONTEXT_V3: 44805 байт, SHA256 61744e9b4b5a5e6d15736980038c7a9dda1cf8c51e3fe16043cf9b4ceae6b929.
- R30 доказал 3/3 EEex/EPS source pins, но queueBindingLiveVerified=false, manualEpsOriginVerified=false, alternateEffectiveAPRVerified=false.

## Что реализовано

1. build_r31_v3_source_only.py: собирает кандидат из точно закреплённого V3 и R31_PASSIVE_BOOTSTRAP.lua, только В ПАМЯТИ. Не пишет на диск и не устанавливает.
2. R31_PASSIVE_BOOTSTRAP.lua: один пассивный EEex started-action listener, тот же ресурс M_BGXR27.lua для будущего заменяющего WeiDU-компонента. При старом зарегистрированном наблюдателе второй не создаётся. При отсутствии обязательного API — отказ от регистрации.
3. Проверяются raw queuedActions.m_nCount, engine action context, выбранное оружие, selected APR и производные stats — ровно возможности имеющегося V3. Все флаги права на команды остаются false.
4. test_r31_source_only.py и test_r31_runtime.lua: SHA, контракты, подмена, отсутствие команд, одиночный слушатель, непустая очередь, запрет дубля, отсутствие обязательного EEex API. Linux Lua 5.3/5.4/LuaJIT и Windows статические тесты.

Контрольная сборка: 47550 байт, SHA256 5a1f6b32db920a005161734605c8b3273614a1318d8b1b57dac79ed022a00f38.
GitHub CI SUCCESS: https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45559891283

## Непреодолённые ограничения

- Есть исходный защищённый сценарий WeiDU, но он не интегрирован и не проверен нативно на пользовательской EET. Вручную загружать Lua или запускать сценарий нельзя.
- Raw count >0 даёт только повод не трогать очередь; raw count=0 НЕ доказывает отсутствие ручного приказа/EPS; manual/EPS происхождение неизвестно.
- Ни один ALT APR/THAC0/урон не проверен на пользовательском runtime, полноценный Weapon Priority в игре не активирован.
- R29 находится ПОСЛЕ R27. Старый установщик R27 и его last-only rollback не использовать.


## Дополнение — защищённая схема WeiDU R31 (CODE/CI, не DEPLOY)

- В GitHub добавлен точный готовый кандидат M_BGXR27_R31_SOURCE_ONLY.lua, 47 550 байт, SHA256 5a1f6b32db920a005161734605c8b3273614a1318d8b1b57dac79ed022a00f38.
- R31_GUARDED_SOURCE_ONLY.py создаёт новый компонент BGXR31 ПОСЛЕ R29 вместо переустановки R27. Только будущая разрешённая операция заменит override/M_BGXR27.lua; штатные R27/R29 записи остаются. Старый R27 installer/rollback не используется.
- Префлайт проверяет зафиксированный WeiDU.log SHA 3cec176f9e6eab721f7aa931c29e7e0d7a4a0d70fab346cffbbb4ae58960e0d6, R27 №149, R29 №150, старый Lua, EEex/EPS, исходник R31, native WeiDU и закрытую игру. Любое расхождение — HOLD.
- Только при буквальном вводе INSTALL_BGXAI_R31_PASSIVE_V3_AFTER_R29 предусматриваются внешний SHA backup, новая WeiDU-запись и проверка, что BDDEFAI.BCS/DPLAYER.BCS и EPS/EEex остались прежними. При ошибке — STOP, без автоотката.
- Откат требует отдельного буквального ROLLBACK_BGXAI_R31_PASSIVE_V3_ONLY, точного PROOF, целого внешнего backup и обязательного R31 ПОСЛЕДНИМ. Никакого отката R29 или R27.
- Тест test_r31_guarded_source_only.py проверяет source pin, read-only baseline, ошибки истории, синтетическую установку, запрет rollback при последующем компоненте и синтетический возврат R29/V6 без изменения их файлов. Это НЕ нативная проверка WeiDU в игровой сборке.
- Код защищённого сценария пока только в GitHub. Он НЕ встроен в единый Windows BGXAI_UPDATE.cmd. Запуск отдельных CMD/PowerShell/Python пользователю не назначать.

**Отсутствующие доказательства перед DEPLOY:** действительная совместимость нового TP2/WeiDU с установленной EET, работа на игровом ПК, полномочия замены после R29, исполнимый bootstrap, gameplay LIVE queue. Ни один CODE/CI PASS не разрешает установку.

## Следующий шаг по P0

Создать новый защищённый WeiDU overlay-компонент ПОСЛЕ установленного R29, который заменяет содержимое M_BGXR27.lua, а не добавляет второй слушатель. Требуются точный installed baseline WeiDU/Lua/EEex/EPS и WeiDU binary, закрытая игра, внешний проверенный backup, last-only rollback нового компонента, отдельное буквальное пользовательское подтверждение. Только прежний BGXAI_UPDATE.cmd, без нового CMD/PowerShell. Backend BGXAI_SYNC.ps1 = 79979/80000 байт — прежде необходима безопасная переработка pinned backend и CI Windows PowerShell 5.1 без изменения существующих меню.

После санкционированного DEPLOY провести ОДИН реальный пассивный runtime-тест очереди. При невозможности прочитать binding — честный HOLD и никаких переключений оружия. Затем доделать effective APR/THAC0/эффекты альтернатив и ручной/EPS arbitration и соединить V5 → V4 → V3 → NONINTERRUPT → BAF.

Повторно запускать 165/167/168/169/170, R27/R28 и R29 не требуется.
