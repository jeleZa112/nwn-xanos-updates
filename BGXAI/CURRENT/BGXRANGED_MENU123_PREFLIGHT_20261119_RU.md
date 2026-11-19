# BGXAI — первый переход от тестов к живой проверке дальнего боя (19.11.2026)

## Факты
- Ветка: bg-eet-ai; единый CMD пользователя: C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd.
- Новый READ ONLY пункт **123 — Ranged fighter native EET preflight**. Не устанавливает BCS, Lua, WeiDU, не изменяет игру или сохранения.
- Исходники: BGXAI/patchsets/ranged_fighter_guarded_20261119/BGXRANGED_PREFLIGHT.py и BGX_RANGED_FIGHTER.baf, SHA256 из manifest_updater.json; версия 0.3.51-BGXRANGED-NATIVE-PREFLIGHT.
- PIN: BGXAI/fox_new/BOOTSTRAP_PIN.json закрепляет immutable commit 3f09232fb33ae3014fa6e2a757cb51363eabd916, BGXAI_SYNC.ps1 79325 байт, SHA256 dcb048d838d41fd59b1b56fae275737eb2001a44bed63a100840a646d69ac9b3. PIN update commit 4d3d991412250c59a3917bbac7496e6919dc0e21.
- Старые пункты меню 1–122 и их действия сохранены. Для соблюдения лимита 80000 байт сокращены только подписи устаревших пунктов 18–69; номера/обработчики не менялись.
- Файл preflight проверяет точные BGXP5 BCS, Lua, BGX120 PRIEST1 хеши; требует BGX120 последним WeiDU, BCS ровно 1170 блоков, BAF SHA, и компилирует один новый BAF с настоящим WeiDU в TEMP. Проверяет, что после объединения 1171 блоков старые 1170 сохранены байт-в-байт. Результат PASS или STOP; ничего не устанавливает.
- Сверены GitHub pinned manifest / immutable script / PIN; Windows PowerShell 5.1 AST и реальный EET WeiDU ещё **не подтверждены**. Не объявлять CI PASS без фактического workflow run.
- Статус: CODE=да, TEST=старый локальный кандидат 21/21; новый пункт GitHub static sync check=да; DEPLOY=НЕТ; LIVE=НЕТ.

## Следующее единичное действие на ПК
Открыть **существующий** BGXAI_UPDATE.cmd, выбрать **123**, скопировать весь итоговый вывод BGXRANGED_NATIVE_PREFLIGHT_PASS либо BGXRANGED_PREFLIGHT_STOP. Не запускать отдельный CMD/Python, не распаковывать ZIP в игру и не выполнять установку. При STOP не повторять без диагноза.

## Важные границы
Текущий пилот — **только чистый Fighter с уже выбранным дальнобойным оружием**. Не переключает оружие, не обходит AoE, не оценивает магическую защиту, мультиклассы, дуалы, воровский фланг, выживаемость фронтовика или отступление мага. Все эти требования зафиксированы в BGXAI_COMBAT_TACTICS_POLICY_20261119_RU.md. Не заявлять полный ИИ, пока игровая проверка этого не подтверждает.

Рабочие BGXP5 (лечение Жагана) и BGX120 (ограничение автоматического Entangle) оставлены без изменений. Ни одной прямой установки в EET не произведено.


## Обновление после реального 123 PASS — menus 124–126, 19.11.2026

Пользователь прислал реальный вывод единого BGXAI_UPDATE.cmd → 123:
- BGXRANGED_NATIVE_PREFLIGHT_PASS;
- old_bcs_sha256=cfc61cfdf7e6ff074a3c26b1e11996a29e6f58fa32d2ddc568866f458b7ac22a;
- 1170 исходных блоков → 1171, preserved_old_blocks=1170;
- candidate_sha256=49b553908e7b66ab85714e91dd27800cad2ec4a9c51d8860d24aeb67b3c461b3;
- game_modified=false.
Повторять 123 не нужно.

Опубликованы три новых пункта в прежнем единственном BGXAI_UPDATE.cmd:
- 124 — guarded install; дополнительная фраза INSTALL_BGXRANGED_FIGHTER_PILOT внутри Python; внеигровой SHA backup и WeiDU.
- 125 — установленный статус READ ONLY.
- 126 — guarded rollback, только последний WeiDU компонент и отдельная фраза ROLLBACK_BGXRANGED_FIGHTER_PILOT.

Ветка bg-eet-ai, immutable pin script commit 9f6a7a68a178ec084b2f4a3eaf86a54b2179fcd7, SHA256 e421d6bb4a3d07ea08fe783ab4aee8fd68ea3a10c02a93f0a2b346caa07310b1, 79073 bytes, pin update ed38a4fa9b80a4264a3e67cbcf9c844903f4c3fe. Source manifest 0.3.52-BGXRANGED-GUARDED (3 files) manifest commit 3a857c1813864ee9802e3f0581adca9413efcea5. Установщик внутри текущего SHA-pinned каталога, первая редакция исправлена по regex.

Windows Actions 44482553200 (PowerShell5.1 AST, one-file 1–126/74 source SHA, Python installer AST guards) SUCCESS; 44482553227 (single CMD stale pin regression) SUCCESS. Оба на commit 5e9d365b760da4d638d1e043227c666fba809432.

CODE=да; TEST=Windows CI PASS + real native EET compile 123 PASS; DEPLOY=НЕ УСТАНОВЛЕНО; LIVE=НЕ ПРОВЕРЕНО. Ни game override, ни BGXP5, ни BGX120 не трогали.

Следующее действие: при закрытой Baldur/InfinityLoader/WeiDU выполнить старый BGXAI_UPDATE.cmd → 124, внимательно прочесть защитные условия и отдельно ввести точную фразу лишь при намеренном согласии на экспериментальную установку. После установленного SHA-verification — 125 status, затем один контролируемый игровой тест Халида: лук выбран, запас стрел, F Guard ON, видимый враг дальше 4, HP Халида >75%; F OFF / близкий враг — новая команда атаки не должна запускаться. Жаган лечит без регрессии, ручные действия не перебиваются, враги в Web не должны притягивать персонажа внутрь; если начинается опасное преследование — остановка и guarded rollback 126. Не путать этот ограниченный pilot с полной политикой для дуалов, магов, воров, иммунитетов и AoE.
