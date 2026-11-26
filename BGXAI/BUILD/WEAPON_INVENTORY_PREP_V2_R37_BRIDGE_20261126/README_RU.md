# BGXAI — реальный следующий код после BGXAI 1.2, 26.11.2026

Сверены `WEAPON_NEXT_IMPLEMENTATION_GATE_20261126_RU.md`, Inventory Prep V1 и фактический `M_BGXR27_R37_SOURCE_ONLY.lua`. Последний уже имеет **один** `makeListener`, который получает sprite/action и производит R33/R37 read-only sample. Повторное подключение EEex listener запрещено.

## Реализовано в V2 (CODE, без установки)

`BGXAI_R37_BACKPACK_BRIDGE_RO_V2.lua` — независимый адаптер, вызываемый внутри существующего R37 callback ПОСЛЕ R27.observe и ДО emit. Дважды читает 15–34 через существующий V1 `inventory.observe(sprite)`, сравнивает raw resref/flags/use counts, проверяет actor+party и строгий read-only контракт R37, на расхождении HOLD. Не регистрирует hook, не изменяет R37, не создаёт файлов в игре, не отправляет команд, не выполняет `XEquipItem`. Это прототип точного соединения, **не live-подключение**.

### Необходимая встраиваемая последовательность

`local sample=R27.observe(sprite,action,p,deps.getActiveStats)` → `bridge.capture(sprite,sample,inventoryV1)` → существующие R36 capture/compare + emit. В исходном R37 запрещено менять старые строки JSON, порядок callback и успешную проверку R37 при ошибках нового модуля. Нужно отдельное source regression с mock sprite/item getter, включая drift между первым/вторым чтением, HOЛD, 0 orders и отсутствие второго listener. Затем protected install через тот же `BGXAI_UPDATE.cmd`, **только при отдельном typed подтверждении**.

## Найденная граница безопасности, которую нельзя обойти

`XEquipItem` выбирает предмет по resref, а не по уникальному instance-id. В V1 учитывались совпадения только в backpack+quickweapon; нужно ещё учитывать shield/offhand, ammo/quiver и все остальные доступные места хранения. Нельзя разрешать реальную команду на основании одного признака `candidate.usabilityVerified=true`, переданного вызывающей стороной. Требуется доказательство из runtime + ITM/2DA с привязкой к тому же снимку, в том числе класс/кит/дуал/STR, cursed/quest/identified, щит/двуручность, боеприпасы, эффекты, THAC0, APR и временные бафы.

### Безопасный исполнитель — пока заблокирован

Первая активная транзакция допускается только на реально пустой доступный weapon quickslot, с уникальным resref во **всём** актуальном снаряжении, с повторной сверкой до/после и подтверждённой границей игрового действия. Требуются item conservation по всем слотам, uses/flags/count, отсутствие ручного/EPS приоритета, штатное продолжение атаки. Полные quickslots — отдельный атомарный протокол с безопасным backup/rollback; `FillSlot`, `Stop`, `ClearActions` запрещены.

### Статус

CODE: V1 + новый V2 bridge; TEST: известные 18 V1 PASS, V2 ещё требует отдельного native Lua CI; DEPLOY: V2 НЕТ; LIVE: автоматическое перемещение из рюкзака НЕТ. V6, R29, R37 и game installation не тронуты. Следующий инженерный шаг — написать и запустить V2 native Lua tests, затем подключить его только к R37 source candidate без второго listener, после чего делать безопасный протокол XEquipItem.
