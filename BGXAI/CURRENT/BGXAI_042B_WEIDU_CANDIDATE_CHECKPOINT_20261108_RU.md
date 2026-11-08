# BGXAI 042B — прототип безопасной WeiDU-инсталляции (НЕ релиз)
Дата 2026-11-08. **Боевой BGXAI 041 остаётся без изменений**, меню `BGXAI_UPDATE.cmd` тоже не менялось. Установка 042B пока не предложена пользователю.

## Реально сделано

На проверенном `BDDEFAI.BCS` 2 229 760 bytes (SHA256 `86d80953be464a3f10da8e1dc031b907801860b7f1f15b3ea6fb9d25e485f3f5`) создан SOURCE ONLY кандидат 042B:
- 11 защитных CR-блоков `ProtectObject` переставлены раньше двух обычных EPS autoattack.
- Только две ветви обычной атаки поменяли скомпилированный action ID `3 Attack` на `105 AttackOneRound`, который заканчивается через раунд (IESDP). 1055 других блоков оставлены по содержимому побайтно как были.
- Офлайн preview: 1057 блоков, 2 229 764 bytes, SHA256 `8602e8853a9c0e8b1bd5733021e6dd9c9ac73e03beb6c9900ef6ebd09dacb9a0`.

Дополнительно создан **отдельный источник будущего установщика** `BGXAI42_INSTALL.py` и `setup-BGX42.tp2`, работающие только по explicit YES и при BGX41-last:
- preflight exact game path / EPS / BGX41-last / source hash / no collision / no game or loader processes;
- external backup в `Documents/BGXAI42_SAFE_BACKUPS`: BCS, WeiDU.log, chitin.key, TLK;
- stage нового BCS только после бэкапа; локальный имеющийся Windows WeiDU устанавливает TP2 `COPY`, формируя WeiDU backup; проверка контрольной суммы и WeiDU.log;
- uninstall только с BGX42-last, exact output hash, через WeiDU, без ручного неопределённого восстановления.

Локально успешно **50/50** офлайн-тестов приоритета + **20/20** mock-WeiDU тестов установщика = **70/70 PASS**. Исходный code/TP2 ZIP проверен CRC. ZIP `/mnt/data/BGXAI_042B_WEIDU_INSTALL_CANDIDATE_SOURCE_ONLY.zip`, 13 180 байт, SHA256 `680626326454e175afde9d3e5851da0b883f3025b3467aed4664e686eb42eee8`.

**Реальная компиляция/установка WeiDU 25100 на EET Windows и игровые эффекты ещё не проверены**, поэтому это **НЕ готовый установочный релиз**, а только кандидат для дальнейшей структурной проверки. Не давать команд для ручного копирования или запуска.

## Сохранение и следующий этап

Постоянная Library: `/BALDURS_GATE_EET_AI/BUILD/BGXAI_042B_WEIDU_CANDIDATE/` — исходники, тесты, ZIP и результаты. Код может быть опубликован отдельно на GitHub `BGXAI/fox_new/experimental_042b_installer_source/` **без BCS**, а статус нужно добавить в `BGXAI/CURRENT/HANDOFF_LATEST_RU.md` и `WORK_LOG_RU.md`. Пользователь не должен повторно загружать BCS и остальные 45 тысяч ресурсов, они сохранены.

Следующий технический шаг: независимая проверка команд WeiDU/TP2 и программы Windows, только затем добавление opt-in пункта через старый `BGXAI_UPDATE.cmd` (первоначально status/download; installation требует проверку и YES) и один игровой тест при EPS autoattack ON и F Guard ON, плюс проверка песни барда. Историческая проблема подробного русского журнала бросков (`Extra Combat Info`) отдельно не закрыта.