# BGXAI R31 — расширение установленного R27 через ACTION_CONTEXT_V3

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

- SOURCE ONLY: никакого защищённого install/rollback к этому кандидату пока нет. Его нельзя вручную загружать в игру.
- Raw count >0 даёт только повод не трогать очередь; raw count=0 НЕ доказывает отсутствие ручного приказа/EPS; manual/EPS происхождение неизвестно.
- Ни один ALT APR/THAC0/урон не проверен на пользовательском runtime, полноценный Weapon Priority в игре не активирован.
- R29 находится ПОСЛЕ R27. Старый установщик R27 и его last-only rollback не использовать.

## Следующий шаг по P0

Создать новый защищённый WeiDU overlay-компонент ПОСЛЕ установленного R29, который заменяет содержимое M_BGXR27.lua, а не добавляет второй слушатель. Требуются точный installed baseline WeiDU/Lua/EEex/EPS и WeiDU binary, закрытая игра, внешний проверенный backup, last-only rollback нового компонента, отдельное буквальное пользовательское подтверждение. Только прежний BGXAI_UPDATE.cmd, без нового CMD/PowerShell. Backend BGXAI_SYNC.ps1 = 79979/80000 байт — прежде необходима безопасная переработка pinned backend и CI Windows PowerShell 5.1 без изменения существующих меню.

После санкционированного DEPLOY провести ОДИН реальный пассивный runtime-тест очереди. При невозможности прочитать binding — честный HOLD и никаких переключений оружия. Затем доделать effective APR/THAC0/эффекты альтернатив и ручной/EPS arbitration и соединить V5 → V4 → V3 → NONINTERRUPT → BAF.

Повторно запускать 165/167/168/169/170, R27/R28 и R29 не требуется.
