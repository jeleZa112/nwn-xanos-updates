# BGXAI R13.1 — установлен, ожидается проверка во время игры

Подтверждённый вывод пользователя (22.11.2026, UTC):
- Использован единственный штатный обновлятор C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd, PIN f97c57b95e5725962ba509dfea61850e225e8e47.
- Пользователь выбрал 161 -> 3 и ввёл точный INSTALL_BGXAI_R13_PASSIVE_TARGET.
- Статус инсталлятора: BGXTD13_INSTALLED_AWAITING_LIVE_TEST.
- SHA256 установленного M_BGXTDEF13.lua: 5c77a460d6b429cec6f9f81e7bf6883ee1f59474cfb95778091ab769302ef414.
- Внешний backup: C:\Users\Drevo\Documents\BGXAI_BACKUPS\PRE_BGXTDEF13_20261122T170836264834Z
- Установка: 2026-11-22T17:08:37.949702+00:00.
- gameplayResourcesModified=true (в отличие от preflight), weaponSwitchAuthorized=false.
- Теперь DEPLOY=YES, LIVE OBSERVATION=NOT YET PROVEN; нельзя утверждать, что R13 читает AC и резисты в игре.
- Не повторять 160, 161->2 или 161->3, пока нет причины. Не устанавливать B3AttackInfo.
- Следующий шаг пользователя: через обычный InfinityLoader загрузить тестовое сохранение, несколько раз дать отдельные команды атаки по **враждебной** цели, нормально выйти из игры и прикрепить C:\Users\Drevo\Documents\BGXAI_LIVE_REPORTS\BGXAI_R13_TARGET_DEFENSE_RAW.jsonl. Файл используется runtime R13 (статический анализ исходника). Если файл отсутствует — сообщить и проверить console fallback; не переустанавливать.
- ВАЖНО: EEex_Action_AddSpriteStartedActionListener фиксирует начала действия, НЕ удары/APR. Поэтому 8 взмахов на одном непрерывном приказе не гарантируют 8 JSONL записей. Любые SESSION, READY, DEFENSE и HOLD важны для диагностики; "TARGET_RAW_DEFENSE_FIELDS_CANDIDATE_ONLY" не означает доказанный шанс попадания.
- R13 пишет только raw target AC, AC modifiers, crushing/piercing/slashing/**missile** resistances. Никакой команды персонажам, никакого автоматического переключения оружия; EPS/V6 логика неизменна.
- В файл LIVE RESULTS не придумывать значения из offline fixtures. Анализировать фактические JSONL записи и, если нужно, корректировать обнаруженные блокеры. Правило автопродолжения BGXAI сохраняется: безопасную работу выполнять без ожидания '+', но при необходимости действия пользователя давать точные шаги. Нет фонового исполнения после ответа.
