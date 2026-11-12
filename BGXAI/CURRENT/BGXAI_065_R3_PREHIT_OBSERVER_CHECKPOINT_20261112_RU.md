# BGXAI 065-R3: доступ к существующему onStarted-диагностическому объекту 064

Проверена структура эталонного `M_BX43_064_BASELINE_READONLY.lua` (SHA256 `bfee5278b5b69b1fb4a02e3fea321082b0238407789df83ec6bd2f78d7e19f4b`). Там уже присутствуют `BGX43Probe.lastAttack` (в том числе `m_actionID`, `target1` / `target2` / `sprite_target`, `target_source`, `reason`) и `lastWeaponHit`, а также счётчики. Чтение через игровую консоль не требует изменения установленной Lua и не регистрирует дополнительных слушателей.

Подготовлен `BGXAI65_PREHIT_STATUS_READONLY.lua`, сценарий только читает эти уже присутствующие поля. Нативные Lua 5.4 тесты 6/6 PASS; полный текущий суммарный счёт source-only тестов 42+10+19+6 = 77/77 PASS. Реальное действие action-start на установленной EET и достоверность цели **НЕ ПРОВЕРЕНЫ** — одни mock-тесты этого не доказывают. `reason=recorded` в уже выполненном onStarted означает кандидатное наблюдение, но не временную гарантию перехвата до удара и не подтверждение действий врага.

Game: BGXAI 064 installed and previously single-F guard live-confirmed; neither 065, R2 nor R3 installed. No changes WeiDU, M_BX43.lua, BDDEFAI.BCS, updater, backups or saved games. Source-only library: `/BALDURS_GATE_EET_AI/BUILD/BGXAI_065_PREHIT_STATUS_R3_SOURCE_ONLY/`, GitHub: `BGXAI/fox_new/experimental_065_prehit_status_r3_source_only/` branch `bg-eet-ai`.

Следующая настоящая граница: в обычном бою при желании выполнить read-only строку из `BGXAI65_PREHIT_STATUS_READONLY.lua` в уже действующей Lua-консоли и оценить `BGX65PRE`. Не просить повторять CLASS/HP/F/AREA/Шанк или присылать архивы. До real runtime-доказательства нельзя активировать prehit interception. Изменения игры — только отдельное согласование + SHA-бэкап + откат к 064.
