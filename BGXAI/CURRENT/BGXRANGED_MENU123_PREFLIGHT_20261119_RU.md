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
