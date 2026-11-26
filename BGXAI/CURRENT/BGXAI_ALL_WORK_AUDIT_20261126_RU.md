# CORRECTION 26.11.2026 — FACT CHECKED ENGINE SLOT MAP
Previous audit did not catch a critical bug: V1/V2 scanned slots 15–34 (20), but **BG(2)EE backpack is 18–33 (16)**; 15–17 quick item buttons, 34 magical weapon. The index 44–47 cited from `ITMSLOTS.2DA` is PSTEE-specific and must not be applied to EET. Correct V3 is source-only in `BGXAI/BUILD/WEAPON_INVENTORY_CORRECTED_V3_20261126/`, with post-backpack R37 raw action/selection/queue check, 13 local Lua 5.3 mock tests PASS, but NO game integration/real equipment move. Legacy V1/V2 scores/tests cannot justify future dispatch. A separate CI regex bug in V2 was fixed with a selftest. Original audit follows below as historical findings.

---

# BGXAI — сквозная ревизия наработок / продолжение 1.2 — 26.11.2026

## Охват и честность
- GitHub tree ветки `bg-eet-ai`: **1667 файлов в BGXAI/** (без .github workflows), полный tree обход; подтверждена сохранённая историческая инвентаризация 24.11 из **1584** исходников в старом снимке и более поздние добавления. Это **инвентаризация имён**, а не построчная ревизия всех 1667 файлов.
- Прочитаны master archive `BGXAI_ALL_CHATS_MASTER_ARCHIVE_20261124_RU.md` (восстановленная история, **не** дословные все чаты), `BGXAI_CANONICAL_HANDOFF_20261124_RU.md` и актуальные R37 LIVE, R29/V6, WEAPON_NEXT, V1 inventory, R37 source, V2 bridge, приоритеты V3, effects V4, APR V5, action continuity, range immunity and error rules. Приватные игровые журналы на диске пользователя не перечитаны. Нельзя заявлять «проанализированы абсолютно все строки всех чатов и файлов».
- Связанные Library документы и приватные PROOF необходимо считать отдельным provenance, не заменять их GitHub master archive; не публиковать приватное.

## Фактическая иерархия (не трактовать номера как последовательные релизы)
1. **LIVE/DEPLOY:** ранее F-guard 066S и жреческие/АОЕ пилоты (частичные LIVE свидетельства), V6 (2 блока DPLAYER, до одного дополнительного выстрела), R29 (WeiDU #150 по R30; фактический source action92 не атрибутирован), R37 пассивный callback 12/12, 0 orders. Важно: R37 НЕ доказал самостоятельный active Lua dispatch.
2. **SOURCE / OFFLINE TEST:** V3 scoring, V4 effects, V5 APR provenance/WSPATCK/CLSWPBON, Current Stats, NONINTERRUPT; R2/R4/R6/R27 refresh/081 очередь; R34 ITM/R32 2DA, consumer BAF V3; Inventory Prep V1 20 backpack slots; V2 bridge (created 26.11). Их модельные результаты НЕ означают effective альтернативные APR или разрешённую команду.
3. **Поведение ещё не закрыто:** выбор лучшего оружия для всей партии, реальная переэкипировка из рюкзака, weapon vs target immunity, ammo/launcher binding, проклятые/уникальные вещи, занятые quickslots; EPS/manual arbitration, безопасная граница текущего шестисекундного раунда/действия, альтернативные active buffs.
4. **Более широкий план:** дружественная агрессия/retaliation, safe AoE/web pathing, лечение иммунных существ, роли танк/вор/маг/жрец, экономия ресурсов, песни барда/координация магов. Различать старые тесты от полноценного gameplay PASS; фокус P0 оружие до переключения на новые ветви.

## Найденные ограничения и ошибки прежнего планирования
- Старый R29 зависел от необязательного RANGED7 несмотря на реально установленный V6; исправление уже документировано. Не возвращать V7/старый gate.
- Щит `SHLD03A` находился в offhand до/после смены на `SW1H04`; **не доказана отдельная команда переключения щита**.
- `actionRaw=92` — выбор оружия; но источник EPS / R29 не подтверждён. `queuedActionsRaw=0` не означает безопасного прерывания активной атаки; R37 `actionOrigin=UNKNOWN`.
- `APR raw 7` соответствует **1.5 APR**, `raw 2` — 2 APR; запрет на наивное сравнение 7 > 2 и двойной учёт специализации через WSPATCK.
- `XEquipItem` — выбор по resref, а не instance-id. V1 проверяет дубликаты только backpack+weapon quickslots; необходимо проверить также quiver/offhand/прочие слоты прежде чем разрешить действие. Для stack/uses/charges необходим строгий conservation. `FillSlot` запрещён.
- V2 bridge читает backpack дважды, но **не проводит вторую сквозную проверку R37 action/selected/queue ПОСЛЕ чтения backpack**. Поэтому стабильность callback на этот момент не доказана. Нельзя принимать V2 как готовый исполнитель либо уже подключённый R37.
- V2 пока только отдельный исходник без реального вызова из R37, тесты исходного файла добавлены; подтверждённого CI/run результатов V2 при этой ревизии нет. Не считать V2 LIVE.
- Существующий R37 capture стартов действий не является универсальным idle/event boundary; дополнительный читатель не доказывает, что можно безопасно вставить `XEquipItem` в середину 6-секундного боевого раунда.
- Нельзя превращать `*.Verified=true` в фактическую runtime-проверку: требуется происхождение доказательства, same-scene/fingerprint и closed-loop after-check.

## Следующий инженерный порядок без повторения наработок
1. Закрыть V2 как **source-only**: тесты в Lua5.3/5.4, исправить missing post-capture context recheck в source candidate, структурная проверка единственного listener, проверить V1+V2 совместно, не трогая installed R37.
2. Встраивать в копию исходника R37 на уровне того же `makeListener` только read-only, сохраняя исходный R33/R37 output и лимит/порядок событий. Сравнивать уже предусмотренные R2/R4/queue snapshots до/после; на дрейфе HOLD. Не запускать новый listener.
3. Подключить уже созданный V3/V4/V5/NONINTERRUPT `preview` к inventory candidate with strict provenance. Использовать R32/R34 ITM как статическое основание, не выдавать альтернативный APR за engine-confirmed.
4. Proof-пилот переноса в пустой разрешённый quickslot **только после** live-safe boundary/manual-EPS и полного консервационного протокола; занимать новые позиции WeiDU только с typed install, SHA, внешним backup, native preflight, last-only rollback. В игре пока не выполнять.
5. Полные quickslots отдельным этапом с реальным атомарным безопасным обменом, а не `FillSlot`, и не рисковать последним мечом/луком.

## Глобальные правила
- Один `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`; no side-updater. `BGXAI_SYNC.ps1` ограничение bootstrap 80 000 байт.
- Игру, сейвы, EPS, SCS, EEex, BG Voice RU, BG_EET_RU, UI не менять ради этой ревизии.
- CODE != TEST != DEPLOY != LIVE; LIVE A/B только после готовой новой функциональной поправки. Продолжать безопасный source-анализ без пользовательского `+`, не просить старые логи снова.
- По глобальной методике обучения фиксировать новые ошибки с evidence, воспроизводимой проверкой и результатом в едином реестре после проверки применимости; не выдавать пустой индекс за базу методов.

## Что НЕ проверено
Все строки 1667 файлов, пользовательские приватные игровые PROOF и сохранения, полный Library archive, реальные Windows-runtime условия и успешность нового V2 CI. Данные остаются OPEN/UNKNOWN до отдельной проверки.
