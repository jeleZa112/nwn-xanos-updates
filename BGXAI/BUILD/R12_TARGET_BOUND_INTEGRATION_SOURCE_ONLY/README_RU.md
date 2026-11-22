# BGXAI R12 target-bound V2 — source-only

Файлы внутри пакета для разработки и офлайн-тестов, НЕ для копирования в игру.

`BGXAI_WEAPON_R12_TARGET_BOUND_CROSSCHECK_V2.lua` — мост R9+R10+R11 target-bound+старый R12. Строго неисполняемый.
`BGXAI_EEEX_R11_STATIC_COMPAT_RO.py` — read-only статический инспектор установленного EEex, пока **не подключён** к единственному BGXAI_UPDATE.cmd.
`dependencies/` — закреплённые локальные зависимости тестов, **не новые копии для игры**.

Тесты автономны и не требуют доступа к игровой папке:
- Lua5.4: `test_r12_target_bound_v2.lua` — 35/35.
- Python3 unittest: `test_eeex_static_compat_ro.py` — 13/13.

На момент выпуска все прежние регрессионные тесты также PASS, всего 193/193.
Не изменять штатный updater, R1–R4, EPS или V6 без отдельного разрешения.
