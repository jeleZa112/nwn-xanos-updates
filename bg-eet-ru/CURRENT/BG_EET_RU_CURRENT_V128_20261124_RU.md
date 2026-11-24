# BG_EET_RU — V128, подтверждённое исправление самопроверки на существующем кеше (24.11.2026)

## Реальная пользовательская ошибка (из консольного вывода, не из ZIP)
Попытка автообновления через единственный `C:\Users\Drevo\Documents\BG_EET_RU\BG_EET_RU_UPDATE.cmd` скачала `_BG_EET_RU_UPDATE_PENDING.cmd`, но `--selftest` завершился:

```
File "_BG_EET_RU_UPDATE_PENDING.cmd", line 8126, in v121_selftest
  assert v121_snapshot(game,Path(d)/'missing.zip') is None
AssertionError
```

После отказа обновления старая версия повторила 14 ранее выполненных read-only аудитов (`V124 ONE RUN: COMPLETED_WITH_HOLDS`), новых игровых изменений не было. Не повторять такой прогон ради диагностики.

### Корневая причина
`v121_selftest()` использовал временную игру `TemporaryDirectory`, **но** `v121_snapshot()` использовал глобальный `WORKDIR` пользовательского проекта; в `Documents\BG_EET_RU\.BG_EET_RU_AUTOFIX_CACHE\V120_EVIDENCE_PINNED.zip` уже есть ранее закешированный pinned V120 архив. `v121_snapshot` правильно возвращает путь, нарушая тестовое `is None`. Чистый GitHub CI это не воспроизводил. Нельзя удалять пользовательский V120 кеш ради прохождения неверного теста.

### Исправление V128
В `v121_selftest` перед тестовым вызовом `v121_snapshot` переменная `WORKDIR` временно указывает на изолированную подпапку `TemporaryDirectory`; в `finally` старый путь всегда восстанавливается. Производственный кеш, ZIP, игровые файлы и приоритеты UI-наблюдателя не затронуты. Добавлен `test_v128_selftest_live_cache.py`:
- непосредственно запускает `BG_EET_RU_UPDATE.cmd --selftest` со специально заполненным кешем пользователя и требует `SELFTEST: PASS`, не трогая оригинальный sentinel;
- имитирует исключение `v121_snapshot`, проверяет восстановление `WORKDIR`;
- проверяет нормальный тест после исключения.

## Публикация и CI
PR #98 merged `c35c352a5fa02125c7a4935567ef14d9b3e64d99` в `bg-eet-ai`.
CI `45439389344`: **windows-latest PASS**, **ubuntu-latest PASS**. Включает новый пользовательский occupied-cache regression, V127 source-loader cache, прежние 14-stage and V122 preflight, selftest.

Единственный файл обновления `bg-eet-ru/onefile/BG_EET_RU_UPDATE.cmd`: `SELF_VERSION=128`, 749896 байт (предел 750000), SHA256 `57cf8e75f4fbdead1d3dbebd4f4ed86201bfe581ee7f71578129af73c4ce55a3`; manifest `release.json` version=128, SHA согласован. Установка на Windows пользователя **ещё не подтверждена**. Все действия в репозитории/CI, в игру без согласия не записано.

## Пользовательский путь
1. Закрыть Baldur.exe и InfinityLoader.exe.
2. Запустить **существующий** `C:\Users\Drevo\Documents\BG_EET_RU\BG_EET_RU_UPDATE.cmd` с доступом к GitHub. Он должен получить V128, пройти самопроверку и перейти в новое меню. Если версия не стала 128, приложить только текст статуса обновления, **не запускать вручную новые версии/дополнительные CMD**.
3. В меню выбрать `2`, затем строго `INSTALL_BG_EET_RU_V126_VISIBLE_ROW_OBSERVER`; только при точном SHA UI.MENU, закрытой игре, внешнем backup и текущих preflight. Читает/изменяет только UI.MENU, не EXE/TLK/сейвы/BGXAI/Voice RU. Если `SAFE_STOP`, прислать `SEND_TO_CHATGPT_BG_EET_RU.zip` без попыток форсирования.
4. При успехе повторно запустить тот же CMD, пункт `4` — InfinityLoader capture, бой + промах, выйти из игры, прислать один ZIP (entry `63_V126_VISIBLE_ROW_OBSERVER.json`).
5. Возврат `UI.MENU`: пункт `3` с точной rollback-фразой, после закрытия игры.

**Важно:** V128 исправляет только самообновление и изоляцию теста. Пассивный UI-наблюдатель V126 остаётся экспериментальным до реального игрового запуска; недостаёт native `Hit()` → конкретный `CMessage` → `combatLog` join. Не утверждать, что оружие на промахах теперь в журнале.
