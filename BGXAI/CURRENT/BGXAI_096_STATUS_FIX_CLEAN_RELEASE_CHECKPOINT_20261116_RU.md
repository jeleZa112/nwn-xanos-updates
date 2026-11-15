# BGXAI 066S — восстановление status после rollback: SOURCE ONLY пакет (16.11.2026)

## Результат
- Исходная установленная версия BGXAI 066S: Lua SHA256 `50640902ec4c25a2c85e5088d7231678b54445a847b41743c476974236d1d70f`, BCS SHA256 `fb435d82e6c3e0ebea1d6a9532753921bd5411d70ac0677dc1fd8ec483380476`; пользователь ранее прислал `READ_ONLY_PREFLIGHT_PASS` пункта 93.
- Пакет `BGXAI_066S_IDLE_STATUS_FIX_SOURCE_ONLY_20261116.zip`, 63 674 байта, SHA256 `8d743bf25cb32e688b437b3856d475eed01c4a13e18c3d0efd763b480fe16230`, **23 файла**: 19 оригинальных + отдельно исправленный Python source, 3 regression tests в одном файле, README и независимый SHA manifest.
- Архив-основа из постоянной Library `BGXAI_066S_IDLE_GUARD_GUARDED_PILOT_SOURCE_ONLY.zip`: SHA256 `70ce25b2ef72ec47594d66d35b043daa76924f404f56ba5a1ca5f4f1be8dcce5`; **19/19 оригинальных файлов без изменения**.
- В кандидате только одна замена ветки `source_status()` для `LAST_066S`; при остаточном WeiDU staging выдаёт `stale_stage_detected=true` и сверяет последний WeiDU + исходные SHA. `preflight/install` по-прежнему fail-closed для занятого staging, и повреждённый Lua/BSC запрещает успешный status.
- Локальный прогон Python: прежние синтетические 15 + 3 новых адресных = **18 тестов PASS (0 failures / 0 errors)**. Содержимое ZIP проверено по SHA для **22/22** файлов, повторная распаковка в **чистый временный каталог** и перезапуск 18 тестов снова PASS. Использован фиктивный WeiDU runner, не реальная игра.
- Точная исходная поправка ранее сверена с Git blob SHA `77b40cf764ea274d140ab4f7b000722a513e8c78`. Предыдущий SOURCE ONLY workflow `.github/workflows/bgxai-idle-rollback-status-regression.yml` опубликован, но фактические GitHub Actions Windows CI результаты НЕ подтверждены.
- **Активный PIN НЕ обновляли**: `BGXAI/fox_new/BOOTSTRAP_PIN.json` всё ещё pin commit `9ad7249c768bc4770e5adb5b8582d8c0184e32b7`, script sha256 `bc4b176aaed83852e597cef8b2cc168b9732fbfa31bbb79ca6442b854351a466`. Игра, BCS, EPS 18.4, WeiDU и меню 1–96 не менялись.

## Следующая граница
Подтвердить GitHub Actions Windows PowerShell 5.1 AST/синтетический installer workflow и оценить безопасный выпуск без нарушения старого immutable pin; затем только с отдельным пользовательским разрешением запускать пункт 94 для обратимого пилота в игре. A/B проверить два F-охранника (ближний занят EPS, дальний свободен), защитную реакцию на реальное попадание, лечение, ручные приказы, бафы, песни барда, ловушки и rollback/status. Нельзя объявлять весь автономный ИИ готовым.

## Правило №7
Не ждать «+» для исследовательской работы в рамках активного ответа. Никаких самостоятельных модификаций установленной игры и обещаний фоновой работы.
