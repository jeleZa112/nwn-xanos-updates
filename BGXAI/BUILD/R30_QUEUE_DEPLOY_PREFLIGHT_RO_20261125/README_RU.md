# BGXAI R30 — диагностика возможности безопасного обновления пассивного R27

## 25.11.2026 — R30 подключён к единому обновлятору (CODE/CI PASS, пользовательский запуск ожидается)

**Новый пункт меню: `170 — R30 queue/deploy preflight READ ONLY`.** Он добавлен в уже существующий `BGXAI/BGXAI_SYNC.ps1`, не создан второй CMD и не изменён `BGXAI_UPDATE.cmd`. Существующий embedded bootstrap динамически читает `BOOTSTRAP_PIN.json`, скачивает immutable script и проверяет SHA/size; новый backend **79 979 байт**, SHA256 `10c9a7651096a45c3a5a694acf9800e9f651843321716438a4e37b6015245e42`, pinned immutable script commit `71b1d37db787a59ed16c8b92ac495314b3577e02`. Лимит текущего CMD — 80 000 байт, оставлен запас 21 байт.

Пункт 170 скачивает только два точных SHA-pinned source файла через существующий `Get-PinnedBytes`, проверяет их до и после staging, временно кладёт их в `%LOCALAPPDATA%\BGXAI_UPDATER`, запускает `py -3 R30 --game ... --candidate ...` и сохраняет единственный JSON в `%USERPROFILE%\\Documents\BGXAI_LIVE_REPORTS\BGXAI_R30_READONLY_*.json`. Временные файлы удаляются. Принятый exit code 2 означает честный HOLD и сохранённый отчёт, не успешную установку. Ни BCS, ни Lua, ни WeiDU, ни EPS, ни сейвы не меняются.

| Объект | Размер | SHA256 |
|---|---:|---|
| R30 read-only checker | 7 985 | `88582abf17e919b9441795b8559cfe85b858fd3083672431eb36b60ba78981bd` |
| R27 ACTION_CONTEXT_V3 candidate | 44 805 | `61744e9b4b5a5e6d15736980038c7a9dda1cf8c51e3fe16043cf9b4ceae6b929` |
| One-file PowerShell backend | 79 979 | `10c9a7651096a45c3a5a694acf9800e9f651843321716438a4e37b6015245e42` |

**Независимая проверка:**
- [CI 45555311800](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45555311800) SUCCESS Windows + Ubuntu: pin exact, R19 unchanged, R30/R27 V3 actual bytes and SHA, embedded CMD PowerShell 5.1 AST.
- [CI 45555311954](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45555311954) SUCCESS Windows + Ubuntu: PowerShell 5.1 parser, menu 170, existing dispatches 1–169 byte-for-byte unchanged.
- **CI is not user-PC runtime proof.** `R30` has not yet been run on the user's EET. A PASS still returns `SOURCE_AND_HISTORY_READ_ONLY_PASS_INSTALL_STILL_UNAUTHORIZED`; it is not permission to install or to replace the live R27.

**Следующее действие пользователя — ровно одно:** открыть прежний `BGXAI_UPDATE.cmd`, выбрать `170`, прислать полный `REPORT_FILE` JSON. Не запускать 165/167/168/169 и не вводить typed install consent. При HOLD — остановиться и анализировать только этот новый отчёт.

---

## Актуальный контракт после согласования V3 (25.11.2026)

**Текущий** неустановленный source-only R27+action context V3: SHA256 `61744e9b4b5a5e6d15736980038c7a9dda1cf8c51e3fe16043cf9b4ceae6b929`, 44805 байт; независимая сборка [CI 45456677110](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45456677110) PASS. Исторический V2 SHA `7ca77abeb94363c75cc58986db4427d9f93edba25e09764be35008c2f0e0600b`, встречающийся в таблице ниже, **устарел**; запрещено выдавать его за текущий.

R30 readonly-скрипт теперь закреплён на актуальном V3 SHA и дополнительно сверяет смысловые маркеры queue/action-context + `actionOriginVerified=false`, `manualEpsQueueVerified=false`. Его **12/12** Python checks (включая реальный текущий SHA+байты и отказ от устаревшей queue-only версии) проходят в [CI 45553690490](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45553690490) SUCCESS Windows/Linux. Файлы в будущем деплое не меняются автоматически; даже PASS означает только `SOURCE_AND_HISTORY_READ_ONLY_PASS_INSTALL_STILL_UNAUTHORIZED`. В единственный `BGXAI_UPDATE.cmd` R30 ещё не включён; игру не запускали и не модифицировали.

---

**Статус: SOURCE ONLY, READ ONLY. Это не установщик и не новая игровая функция.**

## Зачем создан

Реальный R27 уже установлен, но после него могли ставиться другие компоненты WeiDU. Старый `BGXAI_R27_GUARDED.py` содержит условие `TD15_LAST` и пригоден только для исторического этапа. Нельзя пытаться переустановить его, автоматически откатывать или переписывать `override/M_BGXR27.lua`.

Выполнен узкий *новый* шаг к разрешённой установке нового пассивного наблюдателя, который включает R2/R4/081 и смотрит raw число действий из `m_queuedActions.m_nCount`, не вмешиваясь в игру.

## Файлы

- `BGXAI_R30_QUEUE_DEPLOY_PREFLIGHT_RO.py` — **только читает** пользовательские `WeiDU.log`, исходный `override/M_BGXR27.lua`, **точные** установленные `EEex_Action.lua`, `EEex_Sprite.lua`, `EPS core_base.tph`, и предоставленный source-only кандидат `BGXAI_R27_R2_REFRESH_SOURCE_ONLY.lua`.
- `test_r30_queue_deploy_preflight_ro.py` — 10 тестов: фактическая позиция R27 в логе, дубликаты и R30, неверные хеши, пропавшие файлы, reparse point, неправильный кандидат, запрещённые игровую функцию/хук, отсутствие файловых записей.

Точно зафиксированные SHA256 из сохранённых пользовательских отчетов:

| Объект | SHA256 |
|---|---|
| Старый установленный R27 Lua | `e5eb400c56ffb1bc23344a0cf30dcc724d8d18fc2752fabd1c2c63cdcca73735` |
| Новый **неустановленный** source-only кандидат R27 + 081 V2 | `7ca77abeb94363c75cc58986db4427d9f93edba25e09764be35008c2f0e0600b` |
| Установленный EEex Action Lua | `7a64c157418f503e914c4fb3083c97f017e70c9787024fcac779f162c86f20da` |
| Установленный EEex Sprite Lua | `4813ae620f0b472903848018d66488805db7ba2012e065019f4ea5f2a6afab28` |
| EPS `core_base.tph` | `1da3e226645367aa4cc8ba3ff8c1f14627df5ccd3c3e0852941c256b5301e776` |

## Ограничения и гарантии

**Не исполнять отдельно на ПК пользователя:** пока этот модуль не встроен в **единственный** `BGXAI_UPDATE.cmd`, никакого дополнительного CMD/PowerShell от пользователя не просить. Предназначен для интеграции в будущую проверку R30 через тот же обновлятор.

- Считывает весь WeiDU.log в порядке установки; предыдущий R27 **не обязан** быть последним, но должен встречаться ровно раз. Не путает предыдущее `R27` с текущей верхушкой стека. Не делает откат и не меняет компоненты.
- Пропавшие/изменённые/большие файлы, junction/symlink, неавторизованный кандидат, незнакомая структура WeiDU → HOLD без записи.
- Наличие ожидающих действий ещё не проверено в реальной EET; привязка EEex `m_nCount` — SOURCE ONLY. Даже если preflight вернул `SOURCE_AND_HISTORY_READ_ONLY_PASS_INSTALL_STILL_UNAUTHORIZED`, **это НЕ разрешение устанавливать**, **НЕ проверка runtime** и **НЕ доказательство происхождения EPS/ручных приказов**.
- Отдельного активного файла с bootstrap/WeiDU install для обновления R27 пока **нет**, потому что нельзя безопасно обещать noninterrupt исполнитель до проверки состояния stack и правила перекрытия/rollback. Внешние бэкапы, last-only rollback и typed согласие остаются обязательными.

## Следующая задача

Встроить именно этот read-only аудит в существующий пункт обновлятора без его дублирования, затем **один** реальный статусный отчёт с текущим порядком WeiDU; только после этого проектировать last-only новый компонент WeiDU с заменой `override/M_BGXR27.lua`, SHA-guarded внешним бэкапом и пользовательским typed согласием. При неизвестном R29 — HOLD, а не предположение об установке.
