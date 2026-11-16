# BGXAI BGXP3 — выпуск 0.3.40, 17.11.2026

## Пользовательская неисправность
В установленном BGXP2 AUTO/F ON Жаган самостоятельно применял «Повеление» и бил Шанка, но не применил подготовленное «Исцеление лёгких ран» при 2/6 HP Джейд. При 3/6 HP (50%) наступательная логика всё ещё разрешала начать атаку. Предыдущий режим HEALER уже проверен живым игровым тестом. Из-за ActionListEmpty, таймеров, видимости, других приоритетов не доказана единственная причина пропущенного лечения.

## Исправление
**BGXP3 AUTO attack buffer — консервативный и проверенный исходник.** Сохраняет первые 1157 из 1158 BCS-блоков; меняет шесть `!HPPercentLT(Player1..6,45)` в последнем блоке BGXP2 AUTO AttackOneRound на `!HPPercentLT(...,60)`. Это предотвращает новую *автоатаку данного блока*, когда HP любого союзника ниже 60% (при 3/6 HP Джейд новая автоатака не начнётся), оставляя старый лечащий BGXPR с порогом <45%. Не отменяет уже начатые действия и не гарантирует лечение при любой блокировке; повторно исследовать нужно только результат лечения, а не работу «Повеления». Command, SUPPORT, BATTLE, HEALER, Lua, EPS остаются неизменны.

## Реальный защищённый установщик и один CMD
- GitHub branch `bg-eet-ai`: `BGXAI/patchsets/priest_auto_attack_buffer_source_only_20261117/`, релизный `manifest_updater.json` 9 файлов, версия `0.3.40-BGXP3-AUTO-BUFFER`.
- Режимы `BGXP3_INSTALL.py`: status, preflight, install, rollback. Требует BGXP2 последним модом WeiDU, BCS SHA `583e0a5e78c6ae66ffc3c03b8811ade0168377660a6afc79b0859718d84a82eb`, Lua SHA `74ddc016e15fae3451bafe3039b299740c9d2efae8ecfb3e86badea257fa650c`, корректный BGXP2 proof и неизменную копию исходного BAF.
- Реальная native WeiDU-компиляция на пользовательских EET IDS и байт-в-байт сравнение всех 1157 BCS до любой записи. Внешний backup `Documents\BGXAI_PRIEST3_SAFE_BACKUPS`, явная авторизация через единый CMD, WeiDU BCS-only, отдельный rollback с восстановлением BGXP2.
- Единый `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd` **не изменён**; автоматически SHA-загружает новый `BGXAI/BGXAI_SYNC.ps1` из PIN `a48b8928749af7ac820cb6ac81304351bb0021ec`, 76126 байт, SHA256 `3b89aeab51c9df071a9ce017c4a2fa658749e90ccde5beb7b7349ca63e093574`.
- Новые пункты: **109** status, **110** read-only real EET preflight, **111** guarded install с `INSTALL_BGXP3_AUTO_BUFFER`, **112** rollback с `ROLLBACK_BGXP3_AUTO_BUFFER`. Старые пункты 1–108 сохранены. Нельзя использовать 107/108 для BGXP3.

## QA и честный статус
- Windows CI по BGXP3: **17/17 Python tests PASS**, включает полный mock WeiDU install/rollback, SHA источников, синтетический BCS.
- Windows PowerShell 5.1 AST + immutable onefile pin/manifest/menu 1–112: **PASS**.
- https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/43929738463
- https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/43930070458
- **Пользовательская игра не изменялась.** РЕАЛЬНЫЙ префлайт BGXP3 на пользовательской EET и игровое подтверждение эффективности еще не выполнены. Не называть это гарантированным окончательным лечением. Не обещать автоматическую установку без разрешения.

## Один следующий шаг для пользователя
Закрыть игру/InfinityLoader/WeiDU, запустить прежний BGXAI_UPDATE.cmd, выбрать 109 (статус), затем 110 (read-only EET compile). Если появляется `REAL_EET_COMPILE_READ_ONLY_PASS` и 1157 сохраняются, перейти к 111 с точной фразой `INSTALL_BGXP3_AUTO_BUFFER`. При STOP — никуда не устанавливать, передать вывод; 112 только для условного отката, если BGXP3 последний WeiDU. После установки один игровой тест AUTO: 3/6 HP и 2/6 HP Джейд, заученное Cure Light Wounds, F ON, общий AI ON, те же выключенные боевые EPS настройки. 
