# BGXAI — контрольная точка: первый реальный рюкзак → оружейный слот (27.11.2026)

**Текущий статус:** `REAL_GAM_VERIFIED + V3_LOCAL_ARM_SOURCE_TESTED + HOLD_LIVE_ACTOR_ID/ITM/NATIVE_DEPLOY`.

Предыдущий этап: 175 (инертный native compile) PASS, V2 одноразовый генератор Python 15/15 + BCS merge 16/16 GitHub CI Win/Linux, real-GAM read-only PASS, V2 неправильная привязка `actorId` через одну позицию partyIndex, весь live transfer NOT VERIFIED. Не повторять 175.

Новое в этом продолжении:

1. Повторно сверены первичные байты пользовательского `BALDUR(1).gam` SHA `7e926634c0972e90e25c975a18c9bf34b96f4d85184195c630555fdd43f7e19c`, 185732 байта; данные Джагана `STAF01` slot20 → пустой slot35 (снимок сейва, не реального игрового сеанса).
2. Написан новый **реальный активируемый исходник** V3. Не трогает save, EXE, BCS. Вырезаны общий `GLOBAL` arm и ложное поле `actorId` из манифеста; условия arm/tag/try индивидуальны для `Myself` (`LOCALS`). Первая попытка должна погасить все разрешающие метки **до** `XEquipItem`; не сбрасываются действия/атаки. Снято предположение, что позиция в группе = уникальный runtime actor.
3. Повторная сверка настоящего GAM против манифеста и детерминированный BAF (аудит SHA и отрицательные флаги). 24/24 новых автономных теста PASS в Linux контейнере с настоящим GAM; включены отрицательные проверки и сбойные варианты. **Windows и Linux GH Actions V3 CI: run [45940953098](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45940953098) COMPLETED SUCCESS; по 20 PASS + 4 SKIP без приватного GAM на ОС; Linux/Windows static guard PASS.**
4. Выводимый BAF — только исходник, никогда не устанавливается/не активируется и сам не выставляет arm=1. Нельзя выдавать `LOCALS` как уже действующую безопасную actor authentication: отдельный live actor armer ещё требуется. Нет компиляции живого V3 WeiDU, нет BCS merge/backup, нет игровой проверки.

Исходники для продолжения: `BGXAI_XEQUIP_LOCAL_ARM_SOURCE_V3.py`, `verify_candidate_ro.py`, `BGXAI_REAL_JAGAN_MANIFEST_V3.json`, `test_local_arm_v3.py`, `README_RU.md`, `BGXAI_REAL_JAGAN_BUILD_AUDIT_AND_BAF_V3.json`.

**Следующий приоритет:** read-only/Source-only actor identity plan для существующего R37 (один callback), без активного dispatcher. Только после доказанного live actor/ITM/session/queue preflight и отдельного typed user approval разрешается guarded installer через существующий CMD. Не просить у пользователя снова GAM и не повторять старую компиляцию 175.