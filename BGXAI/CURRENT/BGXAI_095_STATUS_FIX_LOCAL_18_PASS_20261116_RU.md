# BGXAI — SOURCE ONLY локальная регрессия статуса после отката: 18 PASS (16.11.2026)

Использован сохранённый в Library `BGXAI_066S_IDLE_GUARD_GUARDED_PILOT_SOURCE_ONLY.zip` (19 файлов). Одна замена ветки `source_status()` восстановлена точно из исходника, Git blob SHA `77b40cf764ea274d140ab4f7b000722a513e8c78` совпал с опубликованным `BGXAI_IDLE_GUARD_INSTALL_STATUS_FIX_SOURCE_ONLY.py`.

В Linux/Python локально выполнены 15 старых `test_guarded_installer.py` unittest и три адресных теста на восстановленный кандидат: mock install→rollback→status, stale stage status vs preflight, tampered Lua fail-closed. **18 run, 0 failures, 0 errors, OK.**

Это тесты синтетической игры, не Windows CI, не реальный WeiDU и не игровое доказательство. GitHub Actions Windows/Linux результат пока не подтверждён. Активные `BGXAI_UPDATE.cmd`, `BOOTSTRAP_PIN.json`, WeiDU/BCS/Lua/EPS в игре не изменены. Установленная версия 066S, пользовательский пункт 93 READ_ONLY_PREFLIGHT_PASS.

Следующее: подтверждённый CI, полный SHA-релиз и регрессия меню 1–96. Установка только по отдельному согласию. Правило №7: продолжать безопасную работу в активном ходе без запроса `+`, не обещая работу в фоне.