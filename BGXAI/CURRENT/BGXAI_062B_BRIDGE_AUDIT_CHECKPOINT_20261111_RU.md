# BGXAI 062B — bridge contract и аудит, 2026-11-11

**Статус: SOURCE ONLY, GAME UNCHANGED.** BGXAI 061 remains installed, one live guard success (approach / buff / kill). No new WeiDU or Lua installation.

## Важный вывод из фактических GitHub-исходников
Проверен `BGXAI/fox_new/experimental_059_guard_visibility_source_only/M_BX43.lua` как исторический источник bridge (не утверждать, что 059 установлен). `BGX52Bridge.prepare` уже итерирует portrait indices 1..5, проверяет F=ON, modal=0, одинаковую AREA и расстояние, сортирует кандидатов и записывает `BGX52_REQ_SLOT` **только одному** защитнику. Поэтому идея 062 о «ровно одном защитнике» в значительной мере уже реализована ранее; новый независимый арбитр в BCS/Lua дублировать опасно.

Проверен `BGXAI/fox_new/experimental_061_rescue_approach_source_only/BGX61_RECEIVER.baf`: 20 receiver blocks, включая 6 bounded `MoveToObject`, с `ActionListEmpty`, `ModalState(NONE)`, `InMyArea` и `Range(...,40)`. Подтверждение HP/класса/оружия/выполнения ручной команды из hook — **не доказано**. Рабочий 061 использует TTL=300 через точечно изменённый Lua, но точную установленную версию не заменять 059 candidate.

## Новый работающий исходник
`bridge_contract.py` — pure Python adapter, принимающий ТОЛЬКО явно подтверждённые наблюдения: Player slot 1..6, area, F, сознание, фактическое оружие, назначение роли, отсутствие ручного приказа, очередь, скрытность, измеренную дистанцию. Если атрибут неизвестен, перехват не разрешается. Движок/файлы игры/WeiDU не вызываются. 16/16 unittest PASS. К нему приложен прежний `team_policy.py`.

Архив SHA256 `b948c7a5ba6af443393a12321bf60807c6efce8fcb48d73e7a72c358b9a4607f`.
Library:
`/BALDURS_GATE_EET_AI/BUILD/BGXAI_062B_BRIDGE_AUDIT_SOURCE_ONLY/BGXAI_062B_BRIDGE_AUDIT_SOURCE_ONLY.zip`
`/BALDURS_GATE_EET_AI/BUILD/BGXAI_062B_BRIDGE_AUDIT_SOURCE_ONLY/README_RU.md`

## Next
1. Сопоставить реальный установленный M_BX43.lua 061 и контракт, не выдавая 059 candidate за live файл.
2. Исследовать безопасный механизм достоверного получения роли/оружия/cast/manual state в EEex без перехвата управления.
3. Оставить существующий BGX52Bridge единственным selector; интегрировать ТОЛЬКО подтверждённые eligibility checks и сохранение EPS executor.
4. Версионированный SHA-pinned preflight и source-only интеграционные тесты до любого нового пункта единого updater. Игра неизменна.
