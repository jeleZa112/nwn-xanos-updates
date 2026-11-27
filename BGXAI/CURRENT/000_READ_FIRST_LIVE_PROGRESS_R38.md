> **ОБЯЗАТЕЛЬНО ДЛЯ НОВОГО ЧАТА (27.11.2026):** сначала [единая короткая точка восстановления](00_RESUME_CURRENT.md) и [глобальный протокол RESUME-GATE](../../GLOBAL_PROJECT_RULES/GLOBAL_CROSS_CHAT_RESUME_V1_RU.md). Исторические «next» ниже не являются текущей командой. Проверить последний commit, реальные пользовательские отчёты и не повторять выполненное.

# 27.11.2026 — R39 EPS-FIRST ИСПРАВЛЕН, R40 LUA 22/22 ВЫПОЛНЕНЫ

**Последняя доказанная точка; ссылки ниже — история, не список команд для повтора.**

- **Исправлен существующий R39** (никаких новых конкурирующих веток): его 2 служебных BAF-блока `abort expired` и `warmup` ранее останавливали дальнейший просмотр правил EPS на срабатывании. В конце **только этих блоков** теперь `Continue()` (официальная семантика IE: последним действием разрешает проверять последующие блоки). **Активный одноразовый `XEquipItem` не изменён и не Continue.** Это CODE/OFFLINE, не доказанная приоритетность EPS в игре. Точный новый source-only BAF: **2079 байт SHA256 `7d57cecc77988764bff3de41379f71cabf8310b3b97dda91404f42555debd62c`**. Старый 2049B SHA `943c221684dde39662476f0514da48fadad6fc1ce90c565b5732afaa87673be8` архивный, НЕЛЬЗЯ использовать для новых пинов.
- **Точные тесты заново выполнены в доступном окружении**: R39 **21/21** Python; R40 **13/13** Python + **22/22** `texlua test_session_reset_v1.lua`. Не утверждать, что Lua 5.3/5.4/LuaJIT GitHub CI, EET native BAF и gameplay прошли.
- Из предыдущего R34/R3 **уже известен установленный `STAF01.ITM`**: `CURRENT_GAME_OVERRIDE`, SHA256 `c472bdf3a561144392249d45df67ae3b4e07d0faf5d30469177c318bc6857fd3`, itemType 26, flags 46, двуручный посох, min STR 5, отсутствует opcode319 среди пяти записанных equip effects (там opcode7). **Это НЕ доказывает kit/class/effects usability конкретного Джагана**. Не повторять старую R34.
- R38 installed и capture 34/34 остается прежним; V3 native (176) PASS ранее; R39 **в изменённых байтах** native не проверен, не установлен/не ARM; R40 source-only не установлен; `ordersSent=0`. Штатный one-file updater не менялся.
- **Следующий НЕПОВТОРНЫЙ функциональный этап**: точная native compile **2079-byte R39** + проверка actor/session-arming/loaded callback в установленном EEex, item usability kit, guarded release/backup/typed approval. До этого не активировать `XEquipItem`; не требовать старых отчётов.
- IESDP: https://gibberlings3.github.io/iesdp/scripting/actions/bgeeactions.htm (Continue последним), https://gibberlings3.github.io/iesdp/scripting/triggers/bgeetriggers.htm (ActionListEmpty — мгновенное состояние, не атрибуция).
- Глобальные воспроизводимые записи обновлены **в существующих** `/GLOBAL_PROJECT_RULES/METHOD_BGXAI_R39_TWO_STAGE_TIME_BOUNDED_XEQUIP_CANDIDATE_V1.json` и `METHOD_BGXAI_EEEX117_SESSION_LIFECYCLE_DISARM_BEFORE_BAF_V1.json`; прежние методы не продублированы.

---

> **НОВОЕ ГЛОБАЛЬНОЕ ПРАВИЛО 27.11.2026:** [ОБЯЗАТЕЛЬНЫЙ PRE-WORK GATE — прежде чем создавать очередную версию, проверить прежние решения](00_PRIOR_WORK_GATE_READ_FIRST.md). Любая новая реализация начинается с проверки уже сделанного, доказательств и недостающей дельты. Не повторять подтверждённые тесты.

# 27.11.2026 — ПРОВЕРКА ИСТОРИИ ТЕСТОВ И УДАЛЕНИЕ ДУБЛЕЙ ИЗ ПЛАНА

**Этот блок — главный после позднего пользовательского вопроса «может уже всё проверено?»; исторические "next: repeat" ниже НЕ исполнять.** Перед R39/R40 была пропущена обязательная сверка модулей **071–085**, NONINTERRUPT, ранних игровым тестов и нативного пункта 176. Исправление плана ниже; текущую игру и старые тесты не повторять.

**УЖЕ ДОКАЗАНО / ПОВТОРЯТЬ НЕ НУЖНО:**
- **V3 native EET:** пользовательский `BGXAI_XEQUIP176_V3_RO_20261127T134903503792.json` уже показал `V3_NATIVE_TEMP_COMPILE_PASS_NO_INSTALL`, BAF SHA `996fd8896225ddbcd1ba2e260ca866acb70de09a6f91c9eb4338063fb7ae23e1`, BCS SHA `f6b14191fb1b6e9023dfaa9363809876578ffbea72d20c8b172a5a1c96bc3a85`, no install / no game writes. Старый 175 тоже PASS. НОВЫЙ R39 BAF не равен V3: его native compile по-прежнему НЕ подтверждён.
- **R37/R38 LIVE:** R38 установлен с backup; 34/34 согласованных live событий, 10 для одного actor Джагана с `STAF01` slot20 и пустым slot35, 24 штатно отсеяны как другой портрет, no equip/commands. V6 ранее успешно переключал лук→меч (лишние выстрелы снижены до 1), реальный action 105→92→134; не перепроверять. Это **не** доказательство XEquipItem.
- **NONINTERRUPT и выбор оружия:** прежние 22/22 NONINTERRUPT, 36/36 V3, 30/30 V4, 18/18 V5, 4/4 сквозных офлайн-теста (110/110), 439/439 в более широкой матрице. Учитывать тестовую модель, но НЕ объявлять engine idle/manual/EPS proven или приоритетный ранкер развернутым.
- **Очередь/источник действий:** старые `081` (action provenance UNKNOWN), `082` (765/765 fail-closed Lua assertions + 14 Python), `083` (реальные EEex v1.1.7 API + 50 Lua/10 Python/149 integration assertions), `084` (нативный `ActionListEmpty()` и EEex `EvalConditionalStringAsAIBase` по исходникам), `085` (31 BAF игровых правила 061/066S/067 уже содержали ActionListEmpty, F guard и modal). Нельзя снова изобретать пустую очередь, классифицировать `m_curScriptNum` как ручную команду или выдавать таймер R39 за engine idle.
- **Классы и ITM:** старый `071` parsed 15 159 CRE + 240 Lua/9 Python tests, но НЕ даёт текущую usable-by-kit; пользовательский `BGXAI_R34_NATIVE_PROF_20261126T002126164.json` уже извлёк текущий `STAF01.ITM` (`CURRENT_GAME_OVERRIDE`, SHA `c472bdf3...`, quarterstaff, two-handed, min STR 5), `characterCanEquipVerified=false`. Повторный скачивающий/декодирующий R34 не нужен. Ранее BCLAW живой тест показал, что временное магическое оружие может блокировать ручную экипировку.
- **Новая интеграционная проверка 27.11:** старый **085** применён локально к *только source* `BGXAI_R39_JAGAN_STAF01_SOURCE_ONLY.baf`: 3 блока, 1 с действием; **`BAF_STATIC_GATE_REVIEW` на блоке 2**, не game fail. Детали: отсутствует F guard по правилам 061/066S/067, `XEquipItem` не известен 085, имя TTL `BGXW3MAX` и отсутствие on-hit request закономерно не подходят к спецсхеме лечения 085. **085 не является универсальной спецификацией XEquip**: не вводить F guard или on-hit request автоматически, особенно пока F user guard отдельно OFF; подготовить отдельный валидатор типа item-transfer с reuse существующих общих барьеров.

**СОХРАНИТЬ БЕЗ ИНСТАЛЛЯЦИИ:** R39 (20 локальных Python tests, новая двухфазная BAF; native именно R39 не проверена), R40 (13 static PASS, 22 Lua mock cases ещё не доказаны выполнением, loaded/destroyed hooks upstream v1.1.7; callback ordering в сборке пользователя не проверен). Не выдавать их за новые игровые улучшения или пройденный LIVE.

**Реально незакрыто только для первого backpack→weapon пилота:** (1) подтверждение права Джагана использовать нынешний `STAF01` по актуальному kit/эффектам; (2) сохранённый session-bound arm со строгим сбросом и отдельной границей manual/EPS/current-action; (3) native compile **именно будущего активного** BAF + интеграция с уже установленными EPS/BCS; (4) typed approval, SHA/backup/WeiDU last-only, одно игровое испытание на расходном сохранении, контроль сохранения предмета/зарядов. Проверять только эти конкретные пробелы, переиспользуя 071/081–085/R34/R38. **Игра, WeiDU и один updater не менялись при этом историческом аудите.**

---

# 27.11.2026 — R40 EEex LIFECYCLE DISARM SOURCE-ONLY; ИГРА НЕ МЕНЯЛАСЬ

**Самая новая стадия, выше исторических записей ниже.** Реальный R38 установлен/уже захвачен, R39 source-only two-stage XEquipItem готов (20 локальных tests), **R40 source-only** решает узкую проблему *сохранённого actor-local ARM* через callbacks EEex v1.1.7. Исходники и тесты: `BGXAI/BUILD/R40_SESSION_RESET_SOURCEONLY_20261127/`; CI workflow `.github/workflows/bgxai_r40_session_reset_source_ci.yml`.

- Проверено чтением *официального tag* `Bubb13/EEex@v1.1.7`: `EEex_GameState_AddDestroyedListener`, `EEex_Sprite_AddLoadedListener`, `EEex_Sprite_GetLocalInt/SetLocalInt`. Это наличие интерфейса в исходнике, а **не** доказательство порядка callbacks в текущей пользовательской сборке.
- `M_BGXW3_SESSION_RESET_V1.lua` не регистрирует слушателей и не пишет в игру сам по себе. Только после отдельной защищённой явной активации он допускает два lifecycle callbacks, **без второго ActionStarted listener**; при loaded проверяет шесть actor-local полей и сначала обнуляет `BGXW3ARM` с readback, потом другие пять; при destroyed только сбрасывает временный Lua epoch.
- Текущие факты: **13/13 static tests PASS локально**; **22 Lua adversarial tests написаны, но ещё НЕ подтверждены выполнением**, CI запущен публикацией workflow (итог CI пока неизвестен). Не выдавать CI, native compile, DEPLOY или LIVE за PASS.
- **Существенные ограничения:** не доказан callback loaded до первого BAF script tick, нет current-session-only armer / защиты manual-EPS, не проверены actual installed `STAF01.ITM` и текущий kit/usability, R39 native EET BAF не скомпилирован, отдельного typed approval на установку нет. `armAuthorized=false`, `dispatchAuthorized=false`, `ordersSent=0`. Ни один игровой файл или единственный updater не менялся.
- **Никаких действий пользователя сейчас.** Не повторять R38 install/capture, меню175, old V3 и R37; продолжить доказательством order of callbacks + exact installed EEex APIs и ITM/kit из доступного read-only preflight, затем guarded release в существующий единственный `BGXAI_UPDATE.cmd` и единственная typed установка / тест на расходном сохранении.

---

# 27.11.2026 — R39 SOURCE-ONLY: КОД ДВУХФАЗНОГО XEquipItem ГОТОВ, GAMEPLAY НЕ МЕНЯЛСЯ

**Прочитать первым.** После реального R38 capture создан новый *активный по форме, но не установленный и не вооружённый* R39 BAF для одного посоха Джагана: `BGXAI/BUILD/R39_STAGED_XEQUIP_SOURCEONLY_20261127/`. Ветка `bg-eet-ai`. Существующие R37/R38, EPS, V6/R29, единственный `BGXAI_UPDATE.cmd`, WeiDU и сохранения не менялись.

- Три BAF-блока: (1) просроченный arm → отказ, (2) одноразовый `XEquipItem("STAF01",Myself,SLOT_WEAPON0,EQUIP)` после второго полного набора проверок, (3) warmup с `ONE_ROUND` и `TWO_ROUNDS`. Исходное окно одноразовое, запрет самоустановки ARM, actor-local TAG прежнего V3. Подлинные GAM slot20→35 и runtime R38 actor identity (10 Jagan событий) не выдумывать и не переизмерять.
- **20/20 локальных Python tests PASS** и SHA exact generated BAF `943c221684dde39662476f0514da48fadad6fc1ce90c565b5732afaa87673be8` (2049 байт); CI workflow `.github/workflows/bgxai_r39_staged_xequip_source_ci.yml` опубликован, исход его запуска **здесь не подтверждён**.
- **Блокеры сохраняются:** ARM в actor LOCALS может пережить сохранение/перезагрузку → необходим независимый *session-bound*, fail-closed аутентификатор и отмена ARM до использования; таймер — cooldown, не доказательство непрерывной idle; manual/EPS origin и установленный `STAF01.ITM` + kit usability не проверены; точный native EET BAF не скомпилирован, backup/install approval не получены. **`dispatchAuthorized=false`, `ordersSent=0`, `installed=false`**, пользователь ничего не запускает.
- **Реальный следующий инженерный шаг:** session-only armer + invalidation через уже существующий R38 one-listener и item usability proof без второго слушателя, затем native compile, guarded install через тот же one-file updater после отдельной typed авторизации, один игровой тест на расходном сохранении. Не повторять R38 install/capture или старые RO проверки.

---

# 27.11.2026 — R38 REAL LOG REPLAY: ДЖАГАН НАЙДЕН, НО ДВИЖЕНИЕ НЕ РАВНО IDLE

**Наивысший приоритет, обновлено после фактического разбора исходного пользовательского журнала.** R38 установлен, предыдущий live capture завершён; НЕ повторять `176→4`/ `176→6`, native V3/175 или R37. Игра в этом исследовании не изменялась.

- Уже полученный приватный `BGXAI_R38_CONSOLE_20261127T081433673320Z.log` прочитан **построчно** (702973 байта). В четырёх каналах выровнены **34 события**; точные идентификаторы актёров и сырой лог не выносятся в публичный GitHub.
- **10** ID совпадений Джагана (`partyIndex=1`) относятся к **одному** runtime actor во всём capture; **24** `HOLD_WRONG_PORTRAIT_CONTEXT` относятся **только** к другому актёру (`partyIndex=2`). Это нормальный fail-closed фильтр, а не повод ещё раз захватывать лог.
- **НОВАЯ РЕАЛЬНАЯ ПРОБЛЕМА ДЛЯ ACTIVE XEquipItem:** у Джагана **5** событий с `actionRaw=23`, что по BG(2)EE IESDP означает **`MoveToPoint`**, в том числе с `queuedActionsRaw=0`; **4** наблюдения с непустой очередью. Нулевая очередь ≠ законченное движение; колбэк ActionStarted ≠ idle.
- **Подготовлен и выполнен на этом подлинном журнале новый SOURCE-ONLY коррелятор, 17/17 локальных негативных/положительных тестов PASS:** `BGXAI/BUILD/R38_REAL_CAPTURE_CONTEXT_GATE_V1_20261127/BGXAI_R38_RUNTIME_GATE_V1.py`, README и тесты в соседней папке; также сохранены в Library `/BALDURS_GATE_EET_AI/BUILD/BGXAI_R38_RUNTIME_GATE_V1/`.
- **Результат:** `HOLD_SAFE_IDLE_AND_SESSION_AUTHENTICATION_NOT_PROVEN`; runtime actor совпал в пределах capture, но подлинность сцепления с сохранением, ITM/kit-допустимость, manual/EPS origin и безопасный момент для команды **НЕ доказаны**. `armAuthorized=false`, `dispatchAuthorized=false`, `ordersSent=0`. Ни один установленный Lua/BCS, WeiDU, игра, сохранения и обновлятор не менялись.
- **Строго следующий функциональный шаг:** разработка независимой строгой границы idle/manual/EPS, подтверждения usability ITM/kit именно перед попыткой, затем только отдельное typed-разрешение и одноразовый охраняемый `STAF01` slot20→slot35 пилот на расходном сохранении. **Не удалять существующие защиты и не маркировать ACTION23 как idle.**
- Источник по действию 23: https://gibberlings3.github.io/iesdp/scripting/actions/bgeeactions.htm. Различать CODE/TEST/DEPLOY/LIVE и не возвращаться к историческим шагам ниже.

---

# 27.11.2026 — НОВЕЙШАЯ КОНТРОЛЬНАЯ ТОЧКА: R38 УЖЕ УСТАНОВЛЕН, CAPTURE ПОЛУЧЕН

**Эта запись приоритетнее ВСЕХ следующих исторических указаний о том, что R38 не установлен или что нужно выполнить 176→4.** В более позднем чате 27.11 пользователь подтвердил успешную установку R38. Предыдущий `R38_PREFLIGHT_PASS_NO_INSTALL` относится к состоянию ДО установки.

- **DEPLOY:** отчёт установки `R38_PASSIVE_INSTALLED_AWAITING_RUNTIME`, создан внешний backup; R38 установлен. Точный итоговый номер компонента WeiDU из недавних данных здесь не установлен, не дописывать его по предположению.
- **REAL CAPTURE:** 34/34 события согласованы во всех четырёх потоках `[BGXR27]/[BGXR37]/[BGXINV3]/[BGXID]`, ошибок формата 0, приказов 0. Статусы `[BGXID]`: 10 × `RUNTIME_JAGAN_INVENTORY_MATCH_READONLY_NO_ARM`, 24 × `HOLD_WRONG_PORTRAIT_CONTEXT`. Джаган и его `STAF01` в рюкзаке наблюдались при пустом целевом оружейном слоте.
- **Важное толкование:** проверка `ID_CORE.capture` ожидает `partyIndex=1`, поэтому `HOLD_WRONG_PORTRAIT_CONTEXT` у событий других актёров **может быть штатным фильтром**, а не багом. Код `BGXAI_R38_GUARDED_FROM_R37.py` выставляет `runtimeActorIdentityVerified=False` безусловно; даже 10 совпадений **не удостоверяют** session/saved-GAM identity.
- **НЕТ РЕЗУЛЬТАТА AUTO-EQUIP:** `XEquipItem` не выполнялся, `armAuthorized=false`, `dispatchAuthorized=false`, `ordersSent=0`. Успешный capture — доказательство наблюдения, а НЕ переноса предмета.
- **Никаких действий пользователя сейчас:** не повторять установку R38, `176→4`, `176→6`, `175`, V3 native, R37 status или R38 preflight. Сначала исправить/дополнить только *реально отсутствующее* доказательство runtime/session actor identity, ITM/class usability и безопасной idle/manual/EPS границы; не удалять защиту портрета на основании одного счётчика HOLD.
- **Следующий функциональный рубеж:** единственная guarded одноразовая попытка `STAF01` из `SLOT_MISC5 (20)` в пустой `SLOT_WEAPON0 (35)` для Джагана на расходном сохранении. Только после проверки вышеперечисленных предпосылок, отдельного typed-согласия на активный патч, SHA + внешнего backup + WeiDU last-only. Рабочие R37/R38, EPS 18.4, V6/R29, сейвы, BG_EET_RU и BG Voice RU сохранять.
- **Единый канал:** `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`; текущий опубликованный bootstrap pin `0a791e1d92aefd70d42d80b5d79b2dac9b3997a0` (это состояние GitHub, не утверждение о локальной загрузке ПК). Не создавать второго обновлятора.

**Правило передачи:** source/CI/native/DEPLOY/LIVE разделять. Если будущая переписка видит ниже `R38 NOT INSTALLED`, это исторический текст, который уже отменён этим блоком.

---

# 27.11.2026 — ИСПРАВЛЕНА РЕАЛЬНАЯ ОШИБКА 176: ENTER → СТАРЫЙ V3 + СБОЙ СЕТИ

**Эта запись приоритетнее старого описания меню ниже. Пользователь уже предоставил все необходимые проверки R37, V3 и R38 preflight. НЕ повтораять их.**

Фактический новый запуск пользователя:
`verified pinned script 35708d0594c8`; `Choice 176`; после приглашения `R38 choice [1]:` нажат **Enter**, поэтому по ошибке запустился старый V3 BAF и завершился `HOLD_PINNED_DOWNLOAD_OR_HASH_FAILURE:TimeoutError,URLError`. Это сетевой отказ скачивания старых V3-файлов, **не отказ WeiDU, не установка R38 и не повреждение рабочего R37**; `ordersSent=0`, `newGameFilesWrittenByThisRunner=0`.

**ИСПРАВЛЕНИЕ УЖЕ ОПУБЛИКОВАНО:** основной однокомандный `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd` теперь закреплён на PowerShell commit `0a791e1d92aefd70d42d80b5d79b2dac9b3997a0`, script SHA256 `51822d75ed0644ec10ee28af47141f1c38b40900e5a7409af9c319790037683b`, **79 996 байт**; обработчик 176 SHA256 `c97fd9c22001395c5d3740cc20061f9ff6f62dc3819031bd95469f1d1f654b9c`, 19 784 байта. Подменю при **пустом Enter/0 выходит без действий**; `1` — только явная повторная V3 (не нужна); `4` — защищённая установка пассивного R38, внутри неё по-прежнему требуется ручная typed-фраза. Для R38 добавлен **SHA256-проверяемый постоянный кэш** в `%LOCALAPPDATA%\BGXAI_UPDATER\VERIFIED_SOURCES_R38` и третий RAW/CDN hostname `fastly.jsdelivr.net` после raw.githubusercontent.com/cdn.jsdelivr.net. Проверки source + Windows/Linux и PowerShell 5.1: [исправление Enter+cache](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45962206276), [точный staged PowerShell 5.1](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45962342644). **Не заявлять, что текущая сеть на ПК пользователя гарантированно работает:** старые временно скачанные исходники не сохранены, пока после этого выпуска новый кэш не наполнится.

**Следующий реальный шаг, без повторного preflight:** при закрытой игре, если пользователь готов устанавливать пассивный наблюдатель, выполнить `BGXAI_UPDATE.cmd` → `176` → **явно 4** → вручную ввести требуемый токен `INSTALL_BGXAI_R38_PASSIVE_IDENTITY_AFTER_R37`. Ничего не устанавливать автоматически; при STOP/HOLD не повторять. После INSTALL PASS — один реальный capture через `176 → 6`. Пока **R38 NOT INSTALLED** и `XEquipItem` не работает.

**Системная ошибка, которую нельзя повторять:** не создавать дефолт, который вызывает закрытый дорогостоящий тест; не стирать после каждого запуска единственные SHA-проверенные загруженные исходники; не пересоздавать проекты и сотни CI/отчётов вместо изменения игрового поведения. Не запрашивать старые отчёты, 175, native V3 или R38 preflight повторно.

---

# BGXAI — ЕДИНАЯ АКТУАЛЬНАЯ ТОЧКА: ПЕРЕХОД К ИГРОВОМУ РЕЗУЛЬТАТУ

**Дата: 27.11.2026. Прочитать перед любыми действиями с BGXAI.** Этот файл является приоритетным указателем над историческими отчётами, старыми handoff и многостраничными журналами тестирования.

## Последний подтверждённый факт пользователя (НЕ ТРЕБУЕТ ПОВТОРА)

Получен **реальный preflight установленной EET** `BGXAI_R38_PREFLIGHT_20261127T072940349855Z.json`:

- `schema=BGXAI_R38_R37_PASSIVE_IDENTITY_GUARDED_V1`
- **`status=R38_PREFLIGHT_PASS_NO_INSTALL`**
- `weiduComponents=153`, последний компонент R37; `weiDULogSha256=3f838e42236898b63cacb3256e9fff4bcea1b9f2273baba4baff27e8883f4538`.
- Исходник пассивного R38 (R37+INV3+ID) `sourceSha256=958a3b7b8bd26840d62df63ad8b89d12a01a6ef97b446f7e7a969503afd0e19c`, `sourceBytes=78927`.
- Контрольный R37 в игре `override/M_BGXR27.lua` `SHA256=5ece282270f0e6a1fa7a6086b7f13c57c77de98759637efa4b2ab0cc1e5744d6`.
- Контроль `WeiDU.log`, R31/R33/R37 proofs, EEex, EPS, DPLAYER, BDDEFAI, `chitin.key` — без отклонений (см. оригинальный пользовательский JSON, **не публиковать пользовательские папки или приватный сейв**).
- `installed=false`, `typedInstallApproved=false`, `gameModified=false`, `ordersSent=0`, `dispatchAuthorized=false`, `armAuthorized=false`.

**ИТОГ: нативная проверка активного V3 BAF (пункт 176) уже была PASS; R37 status PASS; R38 source + Windows/Linux CI PASS; R38 read-only preflight на настоящей EET PASS. Это ЗАКРЫТЫЕ проверки.**

## СЛЕДУЮЩЕЕ ДЕЙСТВИЕ: РЕАЛЬНАЯ РАБОТА, НЕ НОВЫЕ ТЕСТЫ

1. **R38 installation**: закрыть игру/InfinityLoader; пользоваться **ТОЛЬКО** существующим `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`; проверить загрузчик `verified pinned script 35708d0594c8`; выбрать **176 → 4 (install)**. Установщик проводит собственную свежую защитную проверку и запросит **от пользователя** точную typed-фразу `INSTALL_BGXAI_R38_PASSIVE_IDENTITY_AFTER_R37`. Не вводить автоматически и не считать предыдущую просьбу «делай» согласием на изменение файлов игры.
2. Если установка отчитается `R38_PASSIVE_INSTALLED_AWAITING_RUNTIME` и WeiDU №154 — **НЕ предлагать повторную проверку пунктов 175, 176→1, 174→3, 176→2**. Перейти к однократному capture **176 → 6**, в игре загрузить нужный сейв с Джаганом, затем закрыть игру. Получить связанный журнал `[BGXR27]/[BGXR37]/[BGXINV3]/[BGXID]` (сбой/отсутствие событий фиксировать как результат, а не повод к десятку синтетических тестов).
3. Только по результатам реального capture проверять runtime identity, состояние инвентаря `STAF01` slot20 и slot35, механизм idle/action ownership/ITM usability; при данных HOLD — разрабатывать **ровно один необходимый диагностический шаг**, а не перезапускать программу тестирования.
4. **R38 не выполняет XEquipItem**; однократный guarded equip pilot с отдельным одобрением — следующий реальный функциональный milestone, не объявлять его готовым раньше живого переноса и проверки сохранности предметов.

## ЖЁСТКИЙ АНТИ-ПОВТОРНЫЙ РЕГЛАМЕНТ

- Не делать новые глобальные тесты «на всякий случай». Оставить уже полученные PASS закрытыми; повторять проверки только при **изменённом контролируемом исходнике, выявленной новой конкретной ошибке, запросе пользователя или изменении игры**.
- `CI_PASS` != `NATIVE_PASS` != `INSTALL_PASS` != `LIVE_BEHAVIOR_PASS`. Не подменять игровые результаты числом синтетических тестов.
- **Одна ветка исполнения в момент времени**, не перескакивать на R29/V6/другие задачи без реального блокера.
- Сохранить EPS, SCS, EEex, BG_EET_RU, BG Voice RU, сейвы, рабочие R29/V6. Один обновлятор, никаких новых CMD, Stop/ClearActions/FillSlot, автоматической «очистки» WeiDU.
- При отказе `HOLD/STOP` не делать auto retry и не запускать установку без typed approval.
- После каждого реального действия обновить именно этот файл в 5–10 строках, а не создавать очередной многостраничный handoff как единственную актуальную точку.
- **Главный KPI — конкретное улучшение поведения ИИ в игре**, не количество версий и отчётов.

## Зафиксированная версия

- Единый обновлятор: `BGXAI_UPDATE.cmd`; PowerShell script pinned commit `35708d0594c8b50e58fea5c7386b0f0bf0d6b5db`, 79 998 байт, SHA256 `d56ef12a986e2eb0628618b14d4d20b32ae5666fa0784a8d9444b06d7488a163`.
- Release CI `45956688461`: Windows 106/106 и Linux 106/106 тестов (исходники и установочная логика, **НЕ live install**).
- Историческая точка с подробностями: `BGXAI/CURRENT/BGXAI_R38_BATCH_RELEASE_HANDOFF_20261127_RU.md`.
