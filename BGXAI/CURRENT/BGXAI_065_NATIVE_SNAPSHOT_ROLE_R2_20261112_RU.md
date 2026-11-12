# 12.11.2026 — BGXAI 065-R2: реальная проверка snapshot PASS, модель ролевой охраны SOURCE ONLY

## Реальная EET пользователя

В игровой Lua-консоли с включённой проверкой `m_id`, координат, F и modal получено:

- P0: id=true, x=2930,y=591, F=0, modal=0, area=true; ранее class 2, hp 14/14.
- P1: id=true, x=3176,y=546, F=1, modal=0, area=true; ранее class 1, hp 14/14.
- P2: id=true, x=3192,y=582, F=0, modal=0, area=true; ранее class 5, hp 6/6.
- P3: id=true, x=3092,y=561, F=1, modal=0, area=true; ранее class 3, hp 8/8.
- P4/P5: `absent`. Идентификаторы пустых слотов теперь безопасно отбрасываются; прежние `API_ERROR` для пустых не означают отказ класса/ОЗ.

Интерпретация классов по CLASS.IDS: 2 Fighter, 1 Mage, 5 Bard, 3 Cleric. Реальные class/HP, позиции/F/modal/наличие area подтверждены, **не** подтверждены реальные object ID числом, проверки каждой пары `EEex_UDEqual`, наличие memorized spells или боевой API до попадания.

## Новая SOURCE ONLY R2

Проблема исходного 065: любой F guard мог попасть в список primary melee, даже Mage и Cleric. Создан отдельный `BGXAI65_ROLE_COORDINATION_R2.lua` на основе неизменного P.plan 065, разделяющий frontline и support-роли. Для пользователя с P1 Mage F1 + P3 Cleric F1, P0/P2 F0: для угрозы P2 модель не предлагает ни одного melee перехватчика; предлагает два **пассивных** support кандидата (P1 контролировать при наличии возможности, P3 лечение/защита при наличии возможности). Никаких приказов и расходов ресурсов нет. Если классы/киты после respec другие — классификацию нужно обновлять по текущим capability, не по стартовому NPC шаблону.

Тесты в настоящем Lua 5.4 на моках: BGXAI 065 baseline 42/42 PASS, R1 10/10 PASS, R2 19/19 PASS, **71/71 PASS**. Уровень доказательности: модельная Lua логика, не активный combat engine. Старые рабочие BCS/Lua 064, pinned updater, установка WeiDU и игра не менялись. **064 остается установленной**, 065/R2 не установлены.

Исходники: `/BALDURS_GATE_EET_AI/BUILD/BGXAI_065_ROLE_COORDINATION_R2_SOURCE_ONLY/` (Library); GitHub `BGXAI/fox_new/experimental_065_role_coordination_r2_source_only/` (ветка `bg-eet-ai`).

Следующий реальный предел: безопасное подтверждение доударного target resolver и фактических capabilities EPS/EEex, без выдумывания цели/заклинаний. Не проводить активных записей в EET до отдельного явного разрешения, точного backup+rollback 064. Не спрашивать повторно WeiDU/scripts/архивы.
