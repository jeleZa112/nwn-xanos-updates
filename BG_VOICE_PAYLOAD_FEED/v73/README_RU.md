# BG Voice RU V73 — калибровка автоматического выбора

**Не новый обновлятор.** Импортируемый модуль для основного `BG_VOICE_UPDATE.cmd`. Работает с уже опубликованным V70 и его `06_CALIBRATION_REVIEW_96.csv`. Никаких новых моделей не скачивает и Shtorm не запускает.

Зачем: 420 из V70 — только предварительные предложения. До допуска нужны примеры для выявления систематических ошибок в голосе, полноте речи, ударении, смехе и актёрской подаче.

Шесть сбалансированных волн по 16 реплик из 96 проверочных: массовые кандидаты, актёрская игра, неполнота речи и акустические аномалии. Работает с точными WAV путями, проверяет SHA256 обоих русских дублей и отдельно точное имя EN. Отсутствующие файлы — HOLD, обработка остальных продолжается.

## Для интегратора основного обновлятора

```python
from BGVOICE_V73_CALIBRATION_WORKER import run_from_main_updater
report = run_from_main_updater(
    payload_dir=V70_EXTRACTED_DIRECTORY,
    output_root=FULL_PRODUCTION_REPORT_DIRECTORY,
    russian_root=RUSSIAN_WAV_TWO_VERSIONS_DIRECTORY,
    english_root=EXACT_EN_REFERENCE_DIRECTORY,
    batch_index=0,
    mode='stage',
)
```

После полного префлайта и сбора результатов объединить `OPEN_REVIEW.html`, все скопированные WAV и `QA_RESULT.json` внутрь **существующего** `SEND_TO_CHATGPT_BG_VOICE_RU.zip`. Никакого второго CMD/ZIP. Вся работа в отдельной папке `FULL_PRODUCTION/V73_CALIBRATION_BATCH_01`.

**Статусы:** preflight и staged — не human approved, не install ready. Пользовательские решения V65 по `OH85856`/`OH80404` и обе плохие `OH89888` защищены. Анализ Shtorm/Whisper/Zipformer не повторяется. Не меняем игру, исходные WAV, BGXAI и BG_EET_RU.

Калибровочные решения сохранять после прослушивания, переносить в общую БД **только после проверки Sound ID и SHA**. Автоматическое одобрение всех 420 запрещено.