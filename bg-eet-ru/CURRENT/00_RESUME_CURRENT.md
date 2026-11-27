# BG_EET_RU — ЕДИНСТВЕННАЯ КАНОНИЧЕСКАЯ ТОЧКА ВОССТАНОВЛЕНИЯ

<!-- RESUME_GUARD_BG_EET_RU_RELEASE_VERSION=161 -->
<!-- RESUME_GUARD_BG_EET_RU_RELEASE_SHA256=cbce7f0fdb519d6f5642d420d70f198f97d6479b6259c0709abf5a157e64238b -->

**Сверено:** 2026-11-27. **Версию опубликованного исходника** всегда перепроверять по [release.json](../onefile/release.json) (на момент сверки **V161**), а установленное у пользователя — только по его последним ZIP/console/status. Старые `V153–V160 READ_FIRST` и README — исторические, не «следующий шаг».

## Доказанные факты
- **CODE:** V161 `V161_WEIDU_DRIFT_GUARD_AND_PINNED_OFFLINE_CACHE_FIX`, [PR #125](https://github.com/jeleZa112/nwn-xanos-updates/pull/125), merged commit `f2c0bc7ca0131734ddff30e0c0d4aae48f638ce5`. Один прежний `BG_EET_RU_UPDATE.cmd`; релизный SHA256 `cbce7f0fdb519d6f5642d420d70f198f97d6479b6259c0709abf5a157e64238b`, **749994 байта**. При V161 берётся фактический текущий SHA `WeiDU.log`, сохраняются все другие точные пины EEex/UI/TLK/EXE. Кэш Python/Lua SHA-проверяемый и вне игры, сокращён сетевой таймаут.
- **TEST:** локально **19/19** Python+Lua model PASS; GitHub Actions V160 hit-only guarded source после изменений **Windows+Linux PASS**, включая updater selftest. Это не игровой PASS.
- **DEPLOY:** пользовательский `SEND_TO_CHATGPT_BG_EET_RU(6).zip` (148 записей, CRC PASS) подтверждает **V159 installed** по `77_V159_BATCH.json`; `78_V160_HIT_ONLY.json` содержит **`V160_SAFE_STOP`, `BASELINE_SHA_MISMATCH:WeiDU.log`**, остановка **до typed approval**. Ни V160, ни V161 установка на ПК из этих данных **не подтверждена**.
- **СЕТЬ:** отдельное сообщение пользователя `Автообновление: ОФЛАЙН / ОШИБКА: URLError; текущий файл сохранён` — это сбой проверки/скачивания релиза, а не причина V160 SAFE_STOP, который дошёл до SHA preflight. Не смешивать.
- **LIVE:** V161 gameplay не проверен. V160/V161 hit-only добавляет **отдельное уведомление при событии базового эффекта урона**, а не точное соответствие weapon+ammo+hit/miss строке `combatLog`. Промахи не покрывает.
- **УЖЕ СДЕЛАНО, НЕ ПОВТОРЯТЬ:** V159 TLK install, V153 UI, прежние V108 наблюдения и 105–160 пройденные этапы; не делать дополнительные массовые EN-аудиты без доказанных видимых английских строк; не начинать новый updater, hook или альтернативный журнал.
- **Текущая защита:** единственный `C:\Users\Drevo\Documents\BG_EET_RU\BG_EET_RU_UPDATE.cmd`; игра, InfinityLoader и WeiDU должны быть закрыты перед guarded installation. SHA/backup/rollback/typed consent обязательны.

## Ровно следующая дельта
1. Сначала проверить более поздний пользовательский отчёт — возможно V161 уже проверен в другом чате; **не требовать старый ZIP снова**.
2. Если нового доказанного результата нет, действующая версия исходника V161 должна пройти **проверку через существующий CMD** (11→9, READ ONLY), затем guarded 11→10 по явному typed approval; если сеть опять недоступна, обновлять **тот же** CMD строго по официальному проверенному SHA, не вводить второй updater.
3. Только при подтверждённой установке — один контролируемый gameplay тест удара мечом/стрелой, затем работать над **доказанными видимыми EN→RU** и точным combatLog-сопоставлением. При SAFE_STOP сохранить точную reason, не повторять наугад и не откатывать V159.

**Источники:** [release.json](../onefile/release.json), [PR #125](https://github.com/jeleZa112/nwn-xanos-updates/pull/125), [правила RESUME](../../GLOBAL_PROJECT_RULES/GLOBAL_CROSS_CHAT_RESUME_V1_RU.md) и [PRE-WORK](../../GLOBAL_PROJECT_RULES/GLOBAL_PRIOR_WORK_GATE_V1_RU.md). Полный пользовательский ZIP/приватные игровые файлы не публиковать. После каждого нового реального события обновлять **только этот** краткий текущий статус и подтверждающие функциональные записи, не плодить `00_Vnn_READ_FIRST`.

**Приоритет версий:** если `release.json` или новые результаты отличаются от этого файла, `RESUME DRIFT` → сперва обновить и согласовать текущую запись, не выполнять устаревшие команды.
