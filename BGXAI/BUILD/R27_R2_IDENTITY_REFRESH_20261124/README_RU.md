# BGXAI — R27 + актуальный R2: контроль изменений экипировки внутри одного события

## Дополнение 25.11.2026 — x64 raw очередь действий: 081 V2 включён в R27 SOURCE ONLY

**Текущая неустановленная кандидатная сборка:** SHA256 `7ca77abeb94363c75cc58986db4427d9f93edba25e09764be35008c2f0e0600b`. Более ранние SHA в следующих исторических разделах сохранены как архивные; **их не следует использовать для нового деплоя**. Исторический установленный игровой R27 всё ещё SHA256 `e5eb400c56ffb1bc23344a0cf30dcc724d8d18fc2752fabd1c2c63cdcca73735`; ни его BCS, ни WeiDU не изменены.

Тот же сборщик теперь SHA-проверяет `BGXAI081_ACTION_PROVENANCE_QUEUE_V2.lua` и включает его в единую R27 Lua-функцию. Безопасное прямое чтение `CGameAIBase.m_queuedActions.m_nCount` дважды до и дважды после R2/R4: при одинаковом действии и стабильном значении 0..512 выдаёт `queueSnapshotStable` и `queuedActionsRaw`; иначе `nil`. В JSON явно `actionOriginVerified=false` и `manualEpsQueueVerified=false`, даже если raw count 0. Второй слушатель не регистрируется. NONINTERRUPT только **откладывает пересчёт** при count>0, не делает игровой switch.

Независимый [CI 45447222518](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45447222518) Windows/Linux SUCCESS (77/77 R27 Lua на трёх рантаймах, 9/9 Python, 081 441 assertion на каждом, V3 442 сценария). **CODE/TEST PASS, DEPLOY NO, LIVE NO**, и x64 Lua binding `m_nCount` в конкретной пользовательской EET ещё не подтверждён. [Подробный контрольный файл](../../CURRENT/BGXAI_QUEUE_081_R27_NONINTERRUPT_20261125_RU.md).

---

## Дополнение после интеграции R4 стабильных derivedStats (24.11.2026)

**Актуальный исходник R27 refresh** теперь SHA256 `18d1780a5b83b953f31f441cf81a1af489fc21b37e0e2ced05cc0261ec26008c`, предыдущий SHA `149fcf0e5079bb6f2ac0ca1bbd24fd10b46fea2f6422acabd42093be970e974e` в историческом разделе ниже относится к прежнему неустановленному кандидату. Установленный игровой `M_BGXR27.lua` не изменён.

Добавлен источник `R4_CORE.observeStableDerived`: `EEex_Sprite_GetActiveStats` в официальном v1.1.7 может возвращать `m_tempStats` при `m_bAllowEffectListCall==0`. Для чтения текущего выбранного APR в source-only R27 теперь требуются флаг ==1 и стабильные 68 полей R4 в двух чтениях; action/selection проверяются и после второго getter. Неустойчивая выборка → `R4_DERIVED_STATS_NOT_STABLE`, без команды и без прерывания текущего действия. Сериализуются `selectedDerivedStatsDoubleReadConsistent` и `r4Status`, чтобы R6 мог исключать такой кэш.

Тесты: R4 **49/49**, R27 **65/65**, R6 **14/14** на каждом Lua 5.3/5.4/LuaJIT; Python R27 **8/8**, Windows static PASS. [GitHub CI 45443795441](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45443795441) SUCCESS. Разбор и исходники: [R4 Derived Stats Stability](../WEAPON_V3_R4_DERIVED_STATS_STABILITY_20261124/README_RU.md).

**CODE/CI PASS; DEPLOY=NO; GAME LIVE=NO; ALL-ALTERNATE EFFECTIVE APR=NOT VERIFIED.** Старую локальную проверку и игровой захват не повторять.

---

Дата: 24 ноября 2026 года. **CODE PASS / ЛОКАЛЬНЫЕ TEST PASS / DEPLOY NO / GAME LIVE NO.**

## Зачем это сделано

24 ноября исправлен `BGXAI_WEAPON_SLOTS_R2_READONLY.lua`: теперь он замечает замену оружия, колчана и offhand при одинаковых количествах зарядов. Но исходник уже установленного `override/M_BGXR27.lua` **содержит встроенный старый R2** (`e5eb400c56ffb1bc23344a0cf30dcc724d8d18fc2752fabd1c2c63cdcca73735`). Кроме того, исторический R27 делал один снимок R2 и не вызывал `R2.compare`. То есть прежний R2-фикс не мог влиять на то, что установленный R27 пишет в журнал.

Этот source-only кандидат переиспользует те же R2, R4 и исходный R27 listener tail. Два `R2.observe_sprite` в рамках одного вызова слушателя окружают уже имеющийся `R4.observe`. Действие, выбранное оружие и индекс способности проверяются до и после; `R2.compare` проверяет все четыре оружейных слота, четыре колчана и offhand. Изменение приводит к `HOLD_SINGLE_CALLBACK_NO_DISPATCH`, а не устаревшему совету. Отчёт добавляет raw offhand и `rawInventoryDoubleReadConsistent=true` при успешном повторном чтении. Этот флаг говорит только об одинаковых **наблюдавшихся** raw полях; не о том, что нативные адреса/ability/все эффекты подтверждены.

## Файлы

- `build_r27_r2_refresh_ro.py` — детерминированная сборка, SHA256 проверка всех исходных модулей и исходного установленного R27. Не копирует в игру. 
- `BGXAI_R27_R2_REFRESH_SOURCE_ONLY.lua` — составной **неустанавливаемый** read-only Lua, без bootstrap/WeiDU/hooks/команд. SHA256 `149fcf0e5079bb6f2ac0ca1bbd24fd10b46fea2f6422acabd42093be970e974e`.
- `test_r27_refresh_runtime.lua` — 49 Lua-проверок, включая 33 прежних R27 и 16 новых утверждений.
- `test_r27_r2_refresh_ro.py` — 8 тестов pin, старого SHA, отсутствия dispatch и tamper.

## Не сделано и не утверждается

- **Нет** нового игрового механизма переключения оружия, альтернативного effective APR/THAC0/урона, доказанной связки ammo/launcher или происхождения manual/EPS очереди.
- **Нет** обновления установленного `M_BGXR27.lua`; исходный V6, EPS 18.4, BG_EET_RU, BG Voice RU и сохранения не затронуты.
- **Нет** нового пользовательского CMD или предложения установить R27 повторно. Для будущего внедрения потребуется отдельная полная guarded upgrade/rollback стратегия и явное typed-согласие, только если она действительно нужна для полного V3, а не ради этой защиты.

## Смысл для P0

Закрыта кодовая ошибка связи R2→R27: будущие R27 события больше не смогут выдавать неподтверждённый raw снимок за стабильный, если замечено изменение слота. **Главный P0 не закрыт:** подлинный engine-effective APR и эффекты всех альтернативных quickslots на один момент времени, проверка ammo/launcher и безопасная manual/EPS граница перед подключением существующего V3/V4/V5/NONINTERRUPT/BAF.
