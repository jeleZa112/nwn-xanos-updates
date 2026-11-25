# BGXAI R33 menu172 — исправление STOP remote source path blocked (25.11.2026)

Факт пользователя: обычный `BGXAI_UPDATE.cmd` с pinned `f383ad5ca351` успешно стартовал, но при выборе **172** остановился `Remote source path blocked: BGXAI/BUILD/R33_R31_REUSE_PROF_SNAPSHOT_RO_20261125/R33_GUARDED_SOURCE_ONLY.py`. **Игра и WeiDU не менялись, R31 остаётся установлен.**

Причина: старая функция `Get-PinnedBytes` включала R31, но не R33 в строгий список разрешённых префиксов. Исправлено добавлением только `BUILD/R33_R31_REUSE_PROF_SNAPSHOT_RO_20261125`, защита от `..` сохранена. Старые пункты 1–171 byte-exact, единственный CMD не менялся.

**Pinned immutable backend:** `BGXAI/BGXAI_SYNC.ps1`, 79 920 байт, SHA256 `7e3c3cc69ce865ff197a5238564757a2c01df71950f56018590f5fa2c38b2417`, commit `29e7dee1cae6dea41bb11f9286debca2e047f0a5`; `BGXAI/fox_new/BOOTSTRAP_PIN.json` обновлён в commit `6403c3597f804c5dd9c3f2f3a206353824531e6f`.

**Проверки:** [R33 hotfix release CI 45649212023](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45649212023) SUCCESS 5/5 (exact пути R33 и SHA из pin, Windows/Linux, PowerShell 5.1, WeiDU 251). [R33 source CI 45649260839](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45649260839) SUCCESS 3/3. CODE/TEST/RELEASE PASS; R33 DEPLOY/LIVE NOT DONE.

**Далее:** один повтор запуска обычного `BGXAI_UPDATE.cmd` → **172 → 2** после закрытия игры, отдельное буквальное `INSTALL_BGXAI_R33_PASSIVE_PROF_AFTER_R31` при запросе. Встроенный preflight проверит R31-last/SHA, внешний backup; никаких дополнительных RO-запусков. Если STOP — никаких повторных попыток, прислать вывод/отчёт. Если INSTALL PASS — прислать один `BGXAI_R33_INSTALL_*.json`. Не считать R33 автоматическим выбором оружия.
