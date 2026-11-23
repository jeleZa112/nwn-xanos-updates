# BGXAI CURRENT — 2026-11-23 — SOURCE_ONLY мост R13.2 + R4/R1/R2 + APR

- R13.2 (TD15) **установлен и LIVE-проверен** на одном противнике. 4 `DEFENSE`, все 9 сырых защитных полей доступны, 0 HOLD. Ранее получены подтверждения WeiDU/внешнего backup и INIT/READY. Нет необходимости снова запускать бой.
- Изучены ранее существующие `BGXAI_WEAPON_CHOICE_ADVISORY_V1.js`, `BGXAI_WEAPON_PRIORITY_ENGINE_V2.js`, `BGXAI_WEAPON_TRAITS_ADVISORY_V1.js`, `BGXAI_WEAPON_NONINTERRUPT_PLAN_V1.lua`, `BGXAI_WEAPON_LIVE_PAIR_R1_R2_READONLY.py`. Новый алгоритм ранжирования не создавался; существующие сохраняются.
- Добавлен **неустанавливаемый офлайн-мост** `BGXAI_WEAPON_SELECTED_EVIDENCE_BRIDGE_RO_V1.py`. Учитывает реально совместимые по последовательности строки R13, R2, R4, R1, сверяет код атаки, actor, slot, APR R1/R4, 9 сырых защитных полей. Близость строк ≠ авторизованная нативная привязка, поэтому все записи — только кандидаты.
- Результат по реальному журналу SHA256 `cebfa573df8fc9e5180ec8cbcfc8b67a865a12c6381394d5dcd511cdf7500945`: seq1–3 slot12/APR raw2=2, seq4 slot35/APR raw7=1.5, 4/4 кандидата, ноль HOLD. Смена оружия произведена игроком, НЕ BGXAI.
- Тесты: **22/22 локальных PASS** (17 bridge + 5 существующий decoder). Никаких игровых файлов, WeiDU, скриптов, сохранений, EPS и BG_EET_RU/BG Voice RU не изменялось.
- Доавтоматический режим: `CODE=YES, OFFLINE TEST=PASS, DEPLOY=NO, BRIDGE LIVE=NOT APPLICABLE, WEAPON AUTO-SWITCH=OFF`. Текущее оружие наблюдается, а APR альтернативных слотов остаётся неподтверждённым. Все выходы содержат `dispatchAuthorized=false`.
- Далее без участия пользователя: исследовать подлинный нативный формат ITM ability и launcher+ammo для каждого слота; не добавлять ранжирование, пока неизвестны пригодность и полный набор эффектов. Сначала SOURCE_ONLY и тесты.

## Независимые тесты
- Windows GitHub CI 22/22 PASS и Ubuntu GitHub CI 22/22 PASS (всего 44 исполнения; одинаковые тесты на двух ОС).
- CI run: https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45130836924
- Комплексный исходник и отчёт: `BGXAI/BUILD/WEAPON_SELECTED_EVIDENCE_BRIDGE_RO_20261123/`.
- Шаг выполнен только в CODE/TEST: никакой установки или новой версии CMD, текущий TD15 LIVE состояние не изменено.
