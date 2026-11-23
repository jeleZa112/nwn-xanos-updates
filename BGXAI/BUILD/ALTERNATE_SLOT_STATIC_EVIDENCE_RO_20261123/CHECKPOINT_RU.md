# BGXAI — CHECKPOINT R16, 23.11.2026

## Подтверждено раньше

- TD15 `BGXTD15_INSTALLED_AWAITING_LIVE_TEST` был установлен с пользовательским согласием и внешним бэкапом; боевой LIVE-журнал R13.2 позже показал 4/4 события защитных статов, девять полей на каждое, ноль `HOLD`.
- R1/R2/R4 связаны офлайн в `WEAPON_SELECTED_EVIDENCE_BRIDGE_RO_20261123`: 4 выбранных атаки, APR лук+стрелы 2,0 (raw 2), меч 1,5 (raw 7), но источники ручной команды и EPS не удостоверены.
- Более ранняя реальная проверка R3 ITM/BIFF уже находится в Library под именем `BGXAI_WEAPON_NATIVE_ITM_R3.json`. **Не повторять** считывание этих ресурсов для одной этой офлайн-задачи.

## Выполнено в R16

- Новый source-only мост читает фактические снимки R2 (15) из последнего лога и исходный статический аудит R3 (пять предметов). Сверяет SHA реального журнала с отчётом выбранного оружия и SHA раннего R3.
- Для каждой доступной позиции: raw resref, статические базовые способности/эффекты/ограничения из R3, только реально выбранные APR-измерения, индивидуальные барьеры пригодности. Всего 9 позиций: 4 quickweapon, 4 ammo, 1 offhand.
- Зафиксирована возможная граница между состояниями боёв — рост количества `AROW01` с 19 до 20. Это **кандидат**, а не гарантированно подтверждённая загрузка сохранения.
- Выделены риски: нельзя пересчитать bowAPR из selected ammo APR; нельзя интерпретировать BOW05 opcode1 flat APR key2 как +2 атаки; меч `SW1H04` имеет on-hit opcode146, последствия не оценены; STAF01 и BOW05 двуручные при наличии щита, состояние экипировки неизвестно; R3 snapshot actor139135050 не равен R13.2 actor139266124.
- R16 не рейтинговый, не меняет игру, не устанавливается, не выдаёт право отдавать боевые команды. Все кандидаты имеют `priorityEligible=false`.

## Статусы и следующий этап

- TD15 CODE/TEST/DEPLOY/LIVE target raw defense = PASS для зарегистрированного случая.
- R16 CODE/LOCAL TEST = PASS, DEPLOY=NO, LIVE=NOT APPLICABLE, automatic switch=OFF.
- Следующий источник неопределённости — активный native снимок альтернативной quickslot ability/usable + launcher-ammo pair + эффектов и временных бафов. Использовать ранее созданные R3, V2/V3 advisory, V5 APR audit, noninterrupt planner; без дублирования скорера. Без установки/боёв, пока адаптер не готов.

Код: `BGXAI/BUILD/ALTERNATE_SLOT_STATIC_EVIDENCE_RO_20261123/`; результаты тестов и статус GitHub Actions см. в репозитории.

## Независимая проверка и публикация

- GitHub commit `53614b1245396994c9565a9d705c07c6a182e786` — опубликованы исходник, тесты, README, отчёт и контрольная точка; ни `BGXAI_UPDATE.cmd`, ни игровой Lua не менялись.
- Windows CI **28/28 PASS**; Ubuntu CI **28/28 PASS**, обе задачи завершены со статусом `success`.
- GitHub Actions https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45133051450
- Код также размещён в Library `/BALDURS_GATE_EET_AI/BUILD/ALTERNATE_SLOT_STATIC_EVIDENCE_RO_20261123`; контрольная точка — `/BALDURS_GATE_EET_AI/CURRENT/BGXAI_R16_ALTERNATE_SLOT_STATIC_BRIDGE_20261123_RU.md`.
- Реальный отчёт: `REAL_LOG_ALTERNATE_SLOTS_RO_V1.json`, 15 снимков R2, 5 raw ресурсов, 4 APR-снимка только выбранных слотов, один возможный reset/restock стрел. Его SHA256 `9de5dde86efa45a27a6e3f35e900bbe97a4744f5281f447bfd07bba2054afc55`.
