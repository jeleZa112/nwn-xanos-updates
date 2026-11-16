# BGXAI — точка восстановления BGXP3 на 17.11.2026

## Готовность
- **BGXP3 ГОТОВ К ПОЛЬЗОВАТЕЛЬСКОМУ READ-ONLY PREFLIGHT И ОТДЕЛЬНОЙ ЗАЩИЩЕННОЙ УСТАНОВКЕ** через старый `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`. Не выдавать source-only за установленный игровой мод.
- База на ПК пользователя (последнее подтверждение): BGXP2 `BGXP2_INSTALLED_VERIFIED`, `BDDEFAI.BCS` SHA256 `583e0a5e78c6ae66ffc3c03b8811ade0168377660a6afc79b0859718d84a82eb`, 1158 блоков; Lua SHA256 `74ddc016e15fae3451bafe3039b299740c9d2efae8ecfb3e86badea257fa650c`.
- Пакет BGXP3 (рабочий интегрированный релиз): `BGXAI/patchsets/priest_auto_attack_buffer_source_only_20261117/`. SHA-verified релиз 9 файлов, установленный `BGXP2` необходим как LAST WeiDU.
- Существующий CMD обновляется через закреплённый SHA скрипта `BGXAI_SYNC.ps1`, с 112 пунктами. PIN `BGXAI/fox_new/BOOTSTRAP_PIN.json`: script SHA256 `3b89aeab51c9df071a9ce017c4a2fa658749e90ccde5beb7b7349ca63e093574`, size 76126, pinned immutable commit `77ac0440f56950851797a24e598079de477f7d08`.
- **Меню:** 109 статус (read-only), **110 реальная компиляция EET/IDS (read-only)**, **111 guarded install**, 112 guarded rollback. Точная отдельная install-фраза `INSTALL_BGXP3_AUTO_BUFFER`, откат `ROLLBACK_BGXP3_AUTO_BUFFER`.
- Единый updater AST + SHA 47/47 + menu 1–112 CI PASS https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/43930037458.
- BGXP3 Windows synthetic source/BCS install+rollback **17/17 PASS** https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/43929738463.
- Рабочую игру ChatGPT не изменял. Пользователю необходимо: **с закрытой игрой/InfinityLoader** запустить свой старый CMD, выбрать 110, только при `REAL_EET_COMPILE_READ_ONLY_PASS` выбрать 111 и ввести точную install-фразу. При ошибке НЕ повторять автоматически; показать вывод. Не использовать 107/108 для BGXP3.

## Что исправляет, чего не обещает
- BGXP3 изменяет **только последний из 1158 BCS блоков**: в блоке `AUTO AttackOneRound` шесть проверок `!HPPercentLT(PlayerN,45)` заменяются на `!HPPercentLT(PlayerN,60)`. Прежние 1157 блоков обязаны остаться байт-в-байт одинаковыми. Lua, EPS и HEALER неизменны.
- Новый AUTO не начинает собственную атакующую команду уже при 3/6 HP Джейд (50%), оставляя возможность старому BGXPR лечить при <45%. Но **это не гарантированное исправление всех причин пропуска лечения**: старый BGXPR требует `ActionListEmpty`, HaveSpell, See, Range, таймеры/слот; уже начатую атаку и EPS/ручную очередь BGXP3 не отменяет.
- Игровой тест на реальной EET ещё не сделан. Не утверждать, что лечение уже исправлено.
- Ранее пользователь подтвердил, что режим BATTLE самостоятельно применил `Command` на Шанка, AUTO использовал Command и атаковал, но не лечил Джейд при 2/6 HP, хотя Cure Light Wounds был подготовлен. Старые тесты HEALER/Command не дублировать.
- В репозитории также появился параллельный черновой `BGXAI/patchsets/priest_auto_guarded_20261117/`; **не путать его с интегрированным релизом через единый CMD**, который находится в `priest_auto_attack_buffer_source_only_20261117`.

## Безопасность и следующие шаги
Установка только с typed authorization, обязательной native EET preflight, внешним проверенным бэкапом и WeiDU rollback если BGXP3 последний. После установочного отчёта проверить AUTO при падении здоровья союзника, отличить ongoing AttackOneRound от новой атаки, затем устранить недостатки экстренного лечения отдельным проверенным инженерным этапом без `ClearActions` и необоснованных вмешательств в ручные приказы.
