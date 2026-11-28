## ПРОВЕРЕННАЯ ПОПРАВКА: ЕДИНЫЙ ЗАПУСК ЕЩЁ НЕ ДОСТИГНУТ (28.11.2026)

**Фактический статус: PARTIALLY_UNIFIED / NOT FULLY INTEGRATED.** Прежнее требование «один постоянный обновлятор» — **цель и запрет на размножение пользовательских запусков**, а не доказательство, что весь проект уже подчиняется одному файлу.

- Основной штатный пользовательский запуск: `BG_VOICE_UPDATE.cmd`; часть IWINTRO R34/V5, MINSC48 и ранних видео-пилотов всё ещё требует отдельных `INSTALL_*.py`, `APPLY_AND_RUN_ONCE.ps1` или старых `START_*.cmd` для подготовки/патча. **Не утверждать «всё проходит через CMD»**, пока не подтверждены actual dispatcher + Windows test для каждого модуля.
- Действующие аргументы для некоторых задач (например, `--iwintro-full`, `--minsc48-espeech-ro`) не означают, что их **первоначальная установка/исправление** автоматически происходит через CMD.
- Публичный `BG_VOICE_UPDATE.cmd` на ветке `bg-voice-ru` сейчас содержит старый PowerShell launch chain через `VOICE_UPDATER_46.ps1` (исходный размер 1318 B) и **не является доказанной копией** актуального встроенного Python-обновлятора пользователя. Ранее реальный Windows-обновлятор имел иные SHA/режимы. **Нельзя перезаписывать его кодом из старой ветки.**
- **До изменения настоящего updater:** получить/сверить фактические bytes+SHA текущей рабочей Windows-версии; составить coverage-map: направление → текущий главный CMD mode → внешний bootstrap/installer → статус проверенного подключения. Затем встраивать *только отсутствующие* маршруты в существующий единственный entrypoint с SHA-пинами, бэкапом, откатом и smoke-test, по одному безопасному дельта-изменению.
- Внутренние Python/PowerShell worker допустимы; **недопустимо требовать от пользователя запуска дополнительных отдельных CMD/PS1/Python при обычной работе**. Разовые миграции допускаются только если существующий updater технически нельзя обновить безопасно, с честным объяснением и явным согласованием. Не трогать принятые WAV, игру или модели.
- Отчёты: различать `SOURCE_ONLY`, `WINDOWS_RUNTIME`, `USER_ENTRYPOINT_INTEGRATED` и `GAME_INSTALLED`. Глобальный известный-ошибочный guard в CI **не считается** интегрированным в пользовательский updater.

**Не создавать второй универсальный updater, не объединять CMD самостоятельных проектов BGXAI / BG_EET_RU / BG Voice RU.** Для BG Voice RU один entrypoint, много внутренних задач.

---

# BG Voice RU — правило непрерывного продолжения (2026-11-22)

## Основное правило

После каждого успешно пройденного безопасного этапа ассистент **сразу выполняет следующий безопасный этап в том же обращении** и не просит у пользователя «+», подтверждения продолжения или повторного запуска без конкретной причины.

Если текущий шаг успешно выполнен, но следующий требует доступа к реальным WAV, Python/TTS-модели на Windows, человеческого слухового решения или разрешения на установку в игру, ассистент честно указывает фактический блокер. **Недоступность игры не блокирует все другие независимые безопасные этапы**: они выполняются параллельно, когда есть достоверные входные файлы.

## Что считать успехом

Всегда различать:
- CODE READY — код опубликован, не был запущен на ПК пользователя;
- LOCAL TEST PASS — пройден локальный изолированный тест;
- WINDOWS RUN PASS — реальный запуск подтверждён присланным Windows-отчётом;
- HUMAN APPROVED — пользователь действительно выбрал голос или одобрил текст;
- GAME INSTALLED — установка в игру выполнена с отдельным согласием и проверена.

Техническая калибровка WAV, совпадение SHA256 и безошибочный ASR сами по себе **не утверждают** голос, эмоцию, ударения или смысл перевода.

## Ограничения

1. **Один постоянный** BG_VOICE_UPDATE.cmd. Развитие модулей через существующий GitHub-манифест, pinned commit + SHA256, самотест, кеш, безопасный откат. Не заставлять скачивать CMD ради каждого исправления.
2. Один основной отчёт SEND_TO_CHATGPT_BG_VOICE_RU.zip в FULL_PRODUCTION; добавлять новые результаты туда без потери старых файлов.
3. Никаких изменений в исходных WAV, игровых файлах, BGXAI, BG_EET_RU и сохранениях без отдельного явного разрешения.
4. Все ручные решения имеют приоритет над машинными. Не повторять уже отвергнутые A/B; не переписывать ранее одобренные реплики.
5. Источники оригинального английского звука должны подтверждаться по **точному ID реплики**, не по похожему голосу другого персонажа.
6. Ошибка одного WAV = индивидуальный HOLD + checkpoint, остальная очередь продолжается.
7. При отсутствии исходника не сочинять перевод и не утверждать частично сведённый видеоролик завершённым.
8. Основная метрика — законченные и проверенные 7206 реплик и полные видеозаставки, а не количество отчётов и версий.
9. Сформулировав возможность продолжить безопасно, выполнить работу сразу, а не завершать ответ предложением продолжения или запросом «+».

## Текущая очередь на 2026-11-22

V70: 7206 ID, 14412 исходных русских WAV; 420 в техническом staging, 52 строки ручных блокировок. 6 известных проблем Pilot20 — REWORK, CEFALD18 — HOLD по длительности. Прежние 12 A/B не повторять.

Видеозаставки: 37 черновых групп / 63 английских ASR-сегмента, JSON SHA256 87d18d68ce2be6236e2bdb468dc0275c7f5f257714643b5cf9013c48f87a9ee4. Утверждены 15 выборов WAV, 22 группы ещё без окончательного WAV, из них 3 с ранее одобренной голосовой пробой. Оригинальный ZIP полного сценария пока не верифицирован, английская ASR и точные тайминги ещё не подтверждены. Продолжать проверку текста и восстановление аудио безопасно; не устанавливать незаконченные ролики.


## CPU/GPU PIPELINE RULE 2026-11-23 — утверждено пользователем

- В озвучке видеозаставок CPU предварительно читает и SHA-проверяет следующий EN WAV **параллельно с GPU-синтезом текущей реплики**, а CPU завершает проверку, PCM-кодирование и атомарное сохранение предыдущего RU WAV параллельно с очередной GPU-генерацией.
- **Одна CUDA-модель, один GPU вызов `model.generate` в один момент времени**. Ограниченные очереди: до одного EN prefetch и одного RU postprocess. RTX 4060 Laptop 8 GB: без второй модели, без неконтролируемого GPU-параллелизма, preflight свободной памяти.
- Не менять голоса, тексты, английские источники, seed, CFG, шаги синтеза, эмоции, качество, ручные решения и SHA утверждённых WAV. HOLD одной реплики не останавливает остальные, checkpoint/idempotent, без установки в игру.
- Встроено в **Movie Core 1.10.0** (source SHA256 `36948065f0b27cbd0fc5628c151770df0e0110ef3b7cf5c1ef63c255797086ef`), один существующий CMD и один общий ZIP. Тесты только с mock CUDA; **производительность и стабильность на реальной RTX 4060 ещё не подтверждены**. Не требовать отдельных запусков исключительно ради теста конвейера.


## CINEMATIC TEXT FIRST — 2026-11-23

- Stop production of movie RU TTS from **DRAFT_NOT_APPROVED** and **EN_ASR_UNVERIFIED**. Movie Core 1.6 and 1.9 used an ASR-based Russian draft whose literary quality and context had not been approved: do not repeat this mistake even if technical WAV QA passes.
- For INTRO15F and SODCIN01, **recover and compare the previously user-approved Russian subtitle texts before any new voice generation**. Per 2026-11-19 project state, user chose to retain existing Shadow of Amn Russian translation unchanged and approved SoD subtitles. The actual subtitle lines are not in the current 37-group script; do not infer them from ASR or overwrite them.
- For IWINTRO, verify original English transcript, names in game's localization, narrative continuity, and **natural literary Russian** before Shtorm. Never generate the ASR-broken IWINTRO_G09/G10; treat INTRO15F_G06+G07 as one contiguous sentence.
- SHA-lock accepted voice takes SODCIN01_G08, IWINTRO_G02, IWINTRO_G13; their good voice is not approval of their current Russian wording. Retain 7 REWORK_STRESS decisions, old WAV and approved narrator identity. Do not alter game, movies, English/master WAV or other projects.
- Read Library /BG_VOICE_RU/CURRENT/BG_VOICE_RU_MOVIES_37_LITERARY_QA_SOURCE_FIRST_20261123.csv and .../BG_VOICE_RU_CINEMATIC_TEXT_FIRST_RULE_20261123.md for the source-first editorial queue. All 17 newly suggested prose changes are editorial DRAFTS, not automatic replacements or permissions to synthesize.
- Next productive task is **exact subtitle-source reconciliation plus English/source-confirmed literary script**, not another test CMD or mass stress retakes.


## 2026-11-23: verified original 37-group archive and onscreen-caption distinction

- Original `BG_VOICE_RU_NEXT3_FULL_SCRIPT_AND_BATCH_V1_20261121.zip` **RECOVERED** from Library, exact SHA256 `de4887fb5d9ecec7f04637d5f46517c39d3dbc6e3dfd3f9e6da194b60a93396e`, 17 ZIP entries CRC PASS. Original `SCRIPT_GROUPS_DRAFT.json` SHA256 `87d18d68ce2be6236e2bdb468dc0275c7f5f257714643b5cf9013c48f87a9ee4`; all 37 groups / 63 EN ASR segments. Three previously approved narrator pilot WAV hashes match both recovered archive and 2026-11-23 real Windows report.
- **Correct earlier oversimplification** about approved Russian subtitles for `INTRO15F` and `SODCIN01`: available prior A/B videos show already approved **on-screen opening quotations** (Alaúndo and Plutarch) in the first 40s/36s. The inspected film segments do **not** establish 18 previously approved Russian voice-over subtitle lines. Preserve original on-screen text unchanged, but do not block literary translation work on all 18 narrator groups solely awaiting such unproven approved transcripts. Beyond inspected video windows, no claim of absent subtitles.
- Primary source crosswalk and the corrected finding: Library `/BG_VOICE_RU/ЭТАЛОН_ЭЛИОТ/ELIOT_MOVIE_37_SOURCE_TEXT_CROSSWALK_20261123.csv` and `ELIOT_MOVIE_SOURCE_RECOVERY_AND_SUBTITLE_CORRECTION_20261123.md`, master `/BG_VOICE_RU/ЭЛИОТ_ЭТАЛОН_BG_VOICE_RU.md` v1.1.
- **Keep TTS gated on verified English meaning and a final literary Russian voice-over script**. The original JSON and EN ASR are drafts, not a validated verbatim original; IWINTRO_G09/G10 and INTRO15F_G06/G07 still require source/timing QA. Human voice approvals remain SHA-locked; no source/game writes.


## 2026-11-23 ELIOT v1.3 — IWD2 written narration evidence @2000201

- Verified a publicly readable **written witness**, not an acoustic transcription: `The-Gate-Project/IWD_EET_End/iwd_eet_end/lang/en_US/chapters.tra`, resource `@2000201`, Git blob `726befad08b9315fdb369cbc87e1476221f8bab9`. Written narration matches sequence/content of user's `IWINTRO_G01-G10` ASR, correcting Kaldahar→Kuldahar; Isallor/Izalor→Iselore; Burn/Bernd Shander→Bryn Shander; Albrecht Densmoor→Ulbrec Dinnsmore; `messenger yourself`→`a messenger south` (SINGULAR messenger); Luscan→Luskan. The odd conditional about fate and Bryn Shander really is present in the written text: preserve the meaning.
- User WAV `VIDEO/EN_REFERENCE_19/IWINTRO_G09_EN_DNR_ASR_WINDOW.wav`, SHA `ee1e6d627a0e5434` prefix; G10 source WAV SHA `66bbc841d9d3d9f0` prefix; both present in latest Windows report. No one in this turn manually listened to WAV: DO NOT mark `AUDIO_VERIFIED`.
- `ЭЛИОТ — ЭТАЛОН` library master v1.3: `/BG_VOICE_RU/ЭЛИОТ_ЭТАЛОН_BG_VOICE_RU.md`. Detailed ten-line literary narrator script, timing and annotations: `/BG_VOICE_RU/ЭТАЛОН_ЭЛИОТ/ELIOT_IWINTRO_VERIFIED_WRITTEN_SOURCE_RU_SCRIPT_v1_3_20261123.md`. Machine register: `ELIOT_MOVIE_37_SOURCE_TEXT_CROSSWALK_v1_3_20261123.csv` (37 rows, 10 new written-source-supported literary candidates, 27 previous preserved). Archived v1.2 before update.
- The written witness ends at G10, so G11-G19 still need written/audio confirmation. Literary Russian drafts are not final TTS approvals. All `tts_allowed=false`; accepted takes, 7 human rework decisions, exact WAV source, game, V70, BGXAI, BG_EET_RU unchanged.
