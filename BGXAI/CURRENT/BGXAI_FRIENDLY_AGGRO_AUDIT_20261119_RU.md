# BGXAI — аудит атаки союзника после включения Party AI, 19.11.2026

## Подтвержденное наблюдение
При уроне от Джахейры по Халиду с выключенным Party AI, затем включении Party AI, Халид автоматически атакует Джахейру. На скриншотах видно сообщение «Халид: атакует цель: Джахейра» и HP Халида 4/13. Другая проверка показала автоматическое переключение дальнего и ближнего оружия, но опасную реакцию на союзника. Это реальная игровая регрессия безопасности, а не пройденный тест автономной тактики.

## Аудит установленных модов
Найден ранее загруженный WeiDU(20261119-070635).log: EEex 1.2.0, SCS 35.21, EPS 18.4, модули BGX38/39/56/60/61/66S/TEAM, BGXP2/3/5, BGX120. Время файла раньше последних установок Ranged V1/V2/V3, поэтому он не является точной текущей инвентаризацией.

## Подозреваемые источники
- BGX39 source BGXAI/fox_new/release_039/BGX39/team_guard_fallback.baf: есть ProtectObject(PlayerN,6); сам авторский комментарий указывает, что эта команда может сохраняться без автоматической отмены.
- BGX60 source BGXAI/fox_new/experimental_060_direct_response_source_only/BGX60_RECEIVER.baf: AttackReevaluate(LastAttackerOf(PlayerN),30), но явно стоит !InParty(LastAttackerOf(PlayerN)) и !Allegiance(...,GOODCUTOFF). Поэтому нельзя автоматически объявить 060 причиной.
- BGX61 source BGXAI/fox_new/experimental_061_rescue_approach_source_only/BGX61_RECEIVER.baf: аналогичные фильтры !InParty и !Allegiance. Нельзя автоматически объявить 061 причиной.
- BGXRANGED V3 source BGXRANGED_V3_MELEE_HANDOFF.baf: AttackOneRound(NearestEnemyOf(Myself)) без дополнительного !InParty(target), но эта ветка требует HP > 75%. На скриншоте при 4/13 она не должна активироваться. Источник нападения на Джахейру остаётся неустановленным.
- EPS 18.4 или vanilla engine script LastAttackerOf / stored target остаются гипотезами. В истории EPS есть упоминания ошибочных атак нейтралов; это не доказывает именно текущий случай.
- Party AI OFF→ON может восстановить обработку прежней цели/LastAttacker. Поведение требует проверки фактического BCS и владельца выдаваемого действия.

## Safety acceptance
1. Автоматические атаки не выбирают действующего члена партии даже после дружественного удара, независимо от его видимости, EA и запомненного LastAttacker.
2. С настоящим врагом рядом AI продолжает атаковать только врага.
3. Не применять массовое ClearActions и не удалять рабочие лечение BGXP5, EPS и BGX120.
4. Не устанавливать новые военные блоки, пока не выяснено происхождение агрессии.

## Следующий инженерный шаг
READ ONLY аудит актуального override/BDDEFAI.BCS с нативным WeiDU декомпилятором или доказанным парсером, группировка действий Attack/AttackReevaluate/ProtectObject и их предикатов InParty/Allegiance, учёт порядка блоков и реального WeiDU.log/назначенного персонального AI скрипта Халида. Текущий документ диагностика, не установленный hotfix.


## Реализация read-only проверки 19.11.2026

Добавлен самостоятельный **BGX_FRIENDLY_AGGRO_AUDIT_READONLY.py** в SHA-подписанный release source manifest 0.3.57-BGXAGGRO-READONLY. Существующий BGXAI_UPDATE.cmd использует тот же immutable bootstrap и теперь содержит пункт **135 — Friendly aggro audit (READ ONLY)**. Старые пункты 1–134 и их обработчики сохранены. Сокращены подписи части прежних пунктов меню, потому что у BGXAI_SYNC.ps1 жёсткий предел около 80 КБ.

- Источник: BGXAI/patchsets/ranged_fighter_guarded_20261119/BGX_FRIENDLY_AGGRO_AUDIT_READONLY.py; SHA256 926bc0fafb15617cc11e63587589e92e62fbd75e81d5afb65820799c757a3b85.
- Pinned script commit **39faabe04d74f8bb21c728e5db9435f0d7bca19c**; размер 79847 байт, SHA256 **2b7e9b574ed0071668f3a026acbb9531ae51fcbd28b0026151ad29c9d47855c5**; PIN commit 4119b2a0d9e50e899b7970aec38c6292b5817ec3.
- Проверяет реальную BDDEFAI.BCS: хеш, BCS envelope, блоки, последнюю WeiDU компоненту; копирует BCS и WeiDU во временный каталог, декомпилирует BCS -> BAF **только во временной папке**, сверяет количество блоков; изучает Attack/AttackReevaluate/AttackOneRound/ProtectObject и LastAttacker/NearestEnemy, наличие InParty/Allegiance target guards, записывает JSON в Documents/BGXAI_LIVE_REPORTS (или Documents, если папки нет). Выводит первые 15 наиболее подозрительных блоков + путь полного JSON.
- Это эвристическая разметка, не доказательство исполнившегося блока; пока нельзя автоматически объявить виновника.
- GitHub Windows CI 44525952608 — **SUCCESS**, проверка PowerShell 5.1 AST, канала, SHA и меню 1–135. Исходные тесты парсера/блоков 44525423579 — **SUCCESS**. **На пользовательской EET ещё не запускалось.**
- Следующее действие **одно**: закрыть игру/InfinityLoader, запустить текущий единственный BGXAI_UPDATE.cmd, выбрать 135; прислать текст TOP_SUSPECT_BLOCKS и/или JSON из указанного REPORT_FILE. Не запускать новые установки 132/дружественный боевой тест. По отчёту выбрать точечное безопасное исправление и подготовить автоматическую проверку после инсталляции.
