# BGXAI 067: ранний F-перехват + приоритет лечения, исходники проверены; игра 066S

Дата: 2026-11-13. Живой эпизод: Шанк попал по Jade, на скриншоте 2/6 ОЗ, пользователь сообщил, что лечение прошло при 1 ОЗ, а бой включился только после него. Идентичность источника лечения по одному скриншоту не доказана.

## Доказанная причина отсутствия своевременной F-защиты в 066S

- Исходный `BGX66Team` классически разрешает создание боевого `BGX52_REQ_SLOT` только для классов Fighter (2), Paladin (6), Ranger (12).
- По прошлой диагностике у пользователя F=ON у P1 Mage и P3 Cleric, P2 Bard F=OFF, P0 Fighter — герой (слот 0 исключён). При таком составе **нет подходящего для 066S боевого охранника**, хотя жрец может получить запрос на лечение при HP<45% после подтверждённого оружейного попадания.
- 066S отправляет активную оборону только после успешного попадания: защитить ДО первого удара она принципиально не может. Последующая обычная атака другого сценария не доказывает работу боевой охраны.

## BGXAI 067 — конкретное безопасное изменение

- Новый `BGX67_PREHIT_GUARD.lua` обрабатывает сохранённое событие уже установленного наблюдателя EEex, когда враг **начал реальное действие атаки с явно разрешённым числовым целевым ID персонажа партии**. Если объект цели не разрешён, действие не подтверждено, область отличается — fail closed, без действий.
- Выбор F=ON защитника: свободный, здоровый (>50% HP) боец/паладин/следопыт в приоритете; если их нет, разрешён жрец/друид/шаман. Маг и бард не отправляются в ближний бой. Если союзник уже ниже 45% HP, резервный жрец **не назначается** для ранней атаки, чтобы не задерживать лечение.
- Новый BAF 8 блоков (2 cleanup, 6 коротких `AttackReevaluate(NearestEnemyOf(PlayerN),30)`) с `ActionListEmpty`, F, TTL, `See`, `Range`, `InMyArea`; **никаких** `ClearActions` или автоматического расхода новых заклинаний. Блоки вставляются после 11 блоков лечения 066S, так что приоритет лечения сохраняется.
- Установщик `BGXAI67_INSTALL.py` требует точные **уже установленные 066S**, SHA live Lua/BCS, последнюю WeiDU BGX66S, неизменное staged и внешнюю SHA-верифицированную копию; true game root зафиксирован, два файла через WeiDU, точное доказательство отката к 066S, не к 064.

## Отдельные подтверждения

- 64 локальных unit/mock теста PASS: нативный Lua 5.4, role/target/health/duplicate guards, BCS 1088→1096, моделирование 066S→067 WeiDU install/rollback, отказ при SHA/drift/занятой игре.
- Manifest `34/34` источника SHA256 PASS; ZIP CRC PASS SHA256 `bf679bde38983662515475d5cda3587c460ea09dd15b8ed26ff91e65acd6173e`.
- GitHub Actions `43290956256` — **Windows + Linux SUCCESS**: Lua и установочные тесты, официальный WeiDU 251 BAF+TP2 с **синтетическими IDS**. Ошибка CRLF, первоначально обнаруженная в Windows CI, исправлена в генераторе `generate_067_baf.py` явным LF.
- GitHub Actions `43291099607` — **Windows SUCCESS**: native PowerShell AST, SHA и список `34/34`, сохранность пунктов 1–86, добавление 87–91. DRAFT SHA256 `f7452cb7757e6bac074655cabd0c17dac701c07660707ce2496deda433bc5a48`, 70582 байта.
- Active updater `BGXAI/BGXAI_SYNC.ps1` exact-bits-draft Git blob `7e76b3d16c38c4d305d72688ee1293f72d11a65e`, immutable commit `b238eec6c929d0c908d61c09353bf26a41c461f9`.
- `BGXAI/fox_new/BOOTSTRAP_PIN.json` updated in commit `4a506e3117df0d58ee6994da1a8fd66cbe5b67dc`, pinned script above. **No game modification**.

## Один прежний обновлятор

- 87: source sync (34 SHA, NO INSTALL)
- 88: READ ONLY real installed EET IDS/BCS and 066S baseline check
- **89:** guarded direct install, still runs entire real-EET preflight after separate exact typed `INSTALL_BGXAI_067`; backs up both files and uses WeiDU only after checks. Hence **88 is not mandatory as a separate action**; avoid duplicate user tests.
- 90: READ ONLY status 067/066S.
- 91: guarded rollback 067→066S, separate exact `ROLLBACK_BGXAI_067` and last WeiDU checks.

**State as of this checkpoint:** user installed BGXAI **066S** (BCS SHA `fb435d82e6c3e0ebea1d6a9532753921bd5411d70ac0677dc1fd8ec483380476`, Lua SHA `50640902ec4c25a2c85e5088d7231678b54445a847b41743c476974236d1d70f`, WeiDU BGX66S last), current backup `C:\Users\Drevo\Documents\BGXAI66S_SAFE_BACKUPS\PRE_INSTALL_20261112T185323009666Z`. **067 SOURCE PREPARED ONLY, NOT INSTALLED; no live confirmation of early response.** User can continue 066S without running test again. If user chooses 067, close game and InfinityLoader, existing updater option 89, type exact token; if success one realistic in-game test. This is not a complete SCS AI and never guarantees stopping the first attack; event target resolution can fail closed.

Global rules v6 and fast-optimal: autonomously proceed safe coding/CI/source, no request for `+`; user participates only at real game installation/test.
