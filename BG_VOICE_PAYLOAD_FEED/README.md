# BG Voice RU — общий источник пакетов

Это **отдельная ветка метаданных**, не конкурирующий обновлятор.

## Где брать актуальные данные

Машинный индекс: [manifest.json](./manifest.json)

Основные пакеты и состояние проекта хранятся в **общей Библиотеке ChatGPT**:
`/BG_VOICE_RU/CURRENT/`.

Второй чат может получить пакет самостоятельно, **без пересылки файла пользователем**:

1. Прочитать `manifest.json` из ветки `bg-voice-payloads`.
2. Найти точный `library_path` через инструменты Files (Library), не по догадке.
3. Получить байты файла, проверить `bytes` и SHA256.
4. Проверить `INTEGRATION_FOR_MAIN_UPDATER.md`, защитные правила и существующий рабочий `BG_VOICE_UPDATE.cmd`.
5. Подключать новые модули только с сохранением прежних функций и предварительными READ-ONLY тестами.
6. **Не требовать от пользователя пересылки каждого пакета**; оба чата имеют общий источник.

## Разделение ответственности

- **Голосовой чат:** пишет и публикует пакеты исправлений, изменяет только этот индекс.
- **Основной чат:** владеет `BG_VOICE_UPDATE.cmd`, интеграцией и единым производственным отчетом.
- **Пользователь:** не должен служить курьером между чатами.

Не обновлять и не перезаписывать код основного обновлятора из этой ветки.

## Статусы и безопасность

Статус `library_ready_host_integration_unverified` означает **не установлено** и **не подтверждена работа на Windows**. Синтез и подготовка WAV не разрешают установку в игру.

Утверждённые пользовательские решения неизменны:
`OH85856=V65`, `OH80404=V60`, `OH89888=BOTH_BAD`.

**Ограничение:** GitHub пока хранит *индекс*, а не ZIP-файлы. Windows CMD не может скачать их только по Library-пути. Для прямого автоматического скачивания на Windows основной чат должен опубликовать проверенные ZIP в доступном download-хранилище и добавить соответствующие HTTPS URL с хешами в манифест. До этого автоматизирован только **поиск и обмен между чатами**, не Windows-загрузка.

## Production continuation after V74: 613 + 24

After the main updater confirmed V70 420/420 staged and V70/QA_NEXT12 12/12 ready, additional data is published **without new updater or per-version manual ZIP transfer**:

- [Rolling source and tests](./rolling/README_RU.md)
- [SHA manifest](./rolling/MANIFEST.json)
- [613 stage-only selections](./rolling/VOICE_BACKED_613_STAGE_ONLY.csv)
- [24 independent voice A/B jobs](./rolling/NEXT24_VOICE_AB_SHA_GATED.csv)
- [Single imported worker](./rolling/BGVOICE_ROLLING_CONTINUATION.py)

Only the **main voice/video chat** may integrate with the existing one `BG_VOICE_UPDATE.cmd`, after verifying the pinned SHA256 values from [manifest.json](./manifest.json) and Windows preflight. Read-only source, independent staging/QA directories, existing one report ZIP, fail closed on missing WAV or hash mismatch, continue all safe other jobs. No automatic game install or artistic approval. **Actual Windows staging for these 613 has not been run.**
