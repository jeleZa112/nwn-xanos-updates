# BGXAI — безопасное продолжение после 93 PASS (16.11.2026)

## Исходное состояние

- Пользовательский READ_ONLY_PREFLIGHT_PASS для пункта 93, подтверждён baseline BGXAI 066S.
- Lua SHA256: `50640902ec4c25a2c85e5088d7231678b54445a847b41743c476974236d1d70f`.
- BCS SHA256: `fb435d82e6c3e0ebea1d6a9532753921bd5411d70ac0677dc1fd8ec483380476`.
- EET + SCS 35.21 + EEex 1.1.7 + EPS 18.4 / Insane. Игра не менялась.

## Найденная регрессия после успешного отката

`rollback()` допускает оставшийся WeiDU staging (`stage_allowed=True`), однако `source_status()` для 066S ранее вызывал `verify_baseline()` со строгим запретом staging. Поэтому после возврата из пилота статус мог завершиться `PILOT_STAGE_ALREADY_PRESENT`, хотя файлы игры и WeiDU были восстановлены.

## Фактически опубликовано SOURCE ONLY

Репозиторий `jeleZa112/nwn-xanos-updates`, ветка `bg-eet-ai`:

- `BGXAI/patchsets/eps_first_066s_idle_guard_pilot_guarded_installer_source_only/BGXAI_IDLE_GUARD_INSTALL_STATUS_FIX_SOURCE_ONLY.py` — отдельный кандидат, коммит `65997df9b50c55ed0778307e653f75b6106c7595`.
- `.../test_status_after_rollback_source_only.py` — три проверки: восстановленный статус, различие status/preflight, сохранение строгой проверки Lua SHA; коммит `0644d032cf48554737ae86bb5625aa9bc5101e7c`.
- `.github/workflows/bgxai-idle-rollback-status-regression.yml` — CI на ubuntu-latest и windows-latest, компиляция Python + прежние 15 unittest и новые тесты; коммит `60bf83440a2ccf3932877ec367086c49d3928ac1`.

**Точная повторная GitHub-проверка:** получены оригинал, новый кандидат и тест; новый исходник равен оригиналу с единственной заменой ветки `source_status()` для `LAST_066S`. Три новых тестовых метода присутствуют. `BOOTSTRAP_PIN.json` подтверждён неизменным: pinned commit `9ad7249c768bc4770e5adb5b8582d8c0184e32b7`, script SHA256 `bc4b176aaed83852e597cef8b2cc168b9732fbfa31bbb79ca6442b854351a466`.

## Ограничения

- Проверка точного изменения статически PASS, но запуск новых Python тестов и Windows CI **пока не подтверждён**; GitHub connector для commit workflow runs вернул пустой список, что не доказывает ни PASS, ни FAIL push workflow.
- Ни исходный рабочий инсталлятор, ни manifest, ни действующий однофайловый updater/boot pin, ни игра не изменены.
- Не разрешена установка 94 и не подтверждена эффективность охраны в живой игре.
- В тестах используются фиктивные ресурсы: mock-установщик не равен реальному WeiDU.

## Следующие действия

1. Получить и сверить CI Windows+Linux; при ошибке исправлять SOURCE ONLY и повторять тесты.
2. После PASS сделать контролируемый релиз с обновлением манифеста, хешей, тестом совместимости 1–96, однозначным rollback/status; только после этого рассматривать смену immutable pin.
3. Для игрового теста отдельно получить явное согласие, закрыть игру, обеспечить внешний SHA-verified backup. Провести A/B двух F-защитников с одним занятым и одним свободным; проверить ручные приказы, EPS, лечение, бафы, песни и ловушки; откатить при регрессии.
4. Не просить повторно WeiDU.log, scripts.zip или игровые архивы. Продолжать безопасную работу по правилу №7 без дополнительных «+».