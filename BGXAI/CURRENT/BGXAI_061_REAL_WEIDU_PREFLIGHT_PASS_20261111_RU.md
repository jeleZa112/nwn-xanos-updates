# BGXAI 061 — реальная предпроверка WeiDU пройдена

Дата: 2026-11-11. Проект: BGXAI / EET Foxx + EPS 18.4 + SCS 35.21 + EEex 1.2.0. Пользователь запустил прежний единый автообновлятор `BGXAI_UPDATE.cmd`, пункт **66** (READ ONLY).

## Подтверждённый вывод программы

- Семь файлов `BGX61_RECEIVER.baf`, `generate_baf.py`, `BGXAI61_BUILDER.py`, `BGXAI61_INSTALL.py`, `test_061.py`, `test_061_install.py`, `README_RU.md` скачаны и проверены.
- `BGXAI 061 - REAL WeiDU BAF + Lua-TTL read-only preflight (NO INSTALL)`.
- Установлен последним WeiDU компонент `~BGX60\SETUP-BGX60.TP2~ #0 #0 // BGXAI 060 verified-hit direct defense (BCS-only)`.
- Исходный BCS SHA256: `038b41c529fb45bb75528722577beef7b474e1ce55e280dc5fca4d6ed9e72841`.
- Исходный Lua SHA256: `35e450b6600f0fc65d47e535126a52e0303c360033307fa920776faec3f581ab`.
- Реальный WeiDU успешно скомпилировал BAF, Lua TTL patch валидирован. Новый BCS SHA256: `db0fcba4678b00defa2ed7887b57c0d4207effc064891aeb9a0d7dcc1a1a6b0b`.
- Новый Lua SHA256: `fd39d23dc722b549c2af1eaf065541b2ed358a9714f2636b8cab4e45fe7dcec5`.
- `old_blocks=1071`, `removed_060_blocks=14`, `inserted_061_blocks=20`, `final_blocks=1077`.
- `eps_unchanged=true`, `old_eps_guards_unchanged=true`, `existing_lua_056_unchanged=false` (ожидаемо: TTL увеличен до 20 секунд).
- Итог: `BGXAI 061 - preflight PASS; installed 060 unchanged.`

## Следующий разрешённый шаг

Через **тот же** автообновлятор `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd` после закрытия игры/InfinityLoader выбрать **67** для установки 061. Подтверждение вводит пользователь: `INSTALL_BGXAI_061`. Проверки и внешний SHA-подтверждённый backup выполняются установщиком. После успеха — пункт **68**, read-only статус и только затем один контрольный игровой бой, проверяющий подход охранника с расстояния. При ошибке `STOP` — не повторять и не откатывать без анализа результата.

**Текущий факт на момент этого файла: установлен BGXAI 060; BGXAI 061 ещё НЕ установлен.** Не путать успешный preflight с установкой или проверкой в бою. Только существующий автообновлятор, без отдельных CMD/ZIP/ручного override.