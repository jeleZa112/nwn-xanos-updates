# BGXAI R20 — один обновлятор, пункт 164, EEex R19 static READ ONLY (23.11.2026)

## Результат
**R20 CODE PASS / независимые OFFLINE CI PASS / источник опубликован и SHA PIN установлен. На компьютере пользователя пункт 164 ЕЩЁ НЕ ЗАПУСКАЛСЯ. LIVE API и нативная безопасность CItem НЕ ДОКАЗАНЫ.**

В пользовательском едином `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd` появляется новое меню **164 — Installed EEex R19 static audit (READ ONLY)**. Публичный Windows CMD не менялся: он скачивает новый `BGXAI_SYNC.ps1` из immutable PIN и проверяет SHA256/размер до исполнения. Новых пользовательских CMD/ZIP/PS1 не требуется.

- Release immutable commit: `bdff49dfb908798c9979cfe7e42f5179dd43c6c4`.
- PIN promotion: `2a6ffc89213541175773502bf8a2d6ae303a06f1`.
- `BGXAI_SYNC.ps1`: 79 871 байт, SHA256 `913756757e54479f3e50ddd3d5068b58826220b7988f579bacaa6787e7715fcc` (лимит 80 000 соблюдён).
- R19 Python external copy under allowed `BGXAI/patchsets/ranged_fighter_guarded_20261119/BGXAI_R19_INSTALLED_EEEX_AUDIT_RO.py`: 11 013 байт, SHA256 `7426faaa18c1a7bb9a8437ee0733854bed0f868a419e96593c58c7ec71451300`, совпадает с R19 source-only BUILD.
- Old `BGXAI_SYNC.ps1`: 79 631 байт, SHA256 `f5b9d565de595ffea0e04c26f3194152445a26743aa47348694b883cdd9ec8e0`; тест восстанавливает его **точно до байта** обращением только коротких имён внутренних переменных и удалением единственного нового пункта 164. Весь старый функционал 1–163 сохранён; параметр `-GameRoot` публично прежний.

## Проверки
1. R20 source candidate: https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45158098180 — **PASS**, 10 регрессионных тестов R20 + 36 тестов R19 на Windows и Linux, WinPS 5.1/PS7 AST PASS.
2. Main branch release: https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45158331773 — **PASS**, тот же R20/R19 source/AST.
3. Independent whole-channel PIN check: https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45158872134 — **PASS**, 8/8 проверок CMD→SHA PIN→новый PS1→R19 на Windows и Ubuntu, встроенный CMD PowerShell 5.1 AST PASS.
4. Main regression after PIN: https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45158872340 — **PASS**.

**Оговорка:** старые workflows `BGXAI one-file EPS first SHA`, `WTASIGHT` и `056` содержат устаревшие сравнения с прежними снимками CMD/имён переменных; их промежуточные красные CI не следует называть успешными. Они не заменяют упомянутые независимые R20-тесты. Не менять старый CMD, старые игровые модули или необоснованно ослаблять чужие тесты только ради зелёного статуса.

## Поведение пункта 164
1. Из pinned release получить R19 Python через уже существующий `Get-PinnedBytes` и ограниченный allowlist. Проверить SHA256 + точный размер; создать его временную копию только в `%LOCALAPPDATA%\BGXAI_UPDATER`, повторно проверить SHA.
2. Исполнить `py -3` с единственным точным `--game C:\Games\BG_EET_FOXX_NEW`. R19 читает только известные `EEex_scripts/EEex_Resource.lua`, `EEex_Sprite.lua`, `EEex_Action.lua`, `override/M___EEex.lua`, `chitin.key`. Никаких игровых действий или инъекций, никаких WeiDU.
3. Автоматически записать UTF-8 JSON (PowerShell 5.1 может ставить BOM) **вне игры**: `C:\Users\Drevo\Documents\BGXAI_LIVE_REPORTS\BGXAI_R20_EEEX_STATIC_<UTC timestamp>.json`; напечатать JSON и `REPORT_FILE=<path>`. Код завершения 2 / `HOLD` — допустимый диагностический результат, НЕ разрешение переходить к LIVE. Временный .py из кэша удаляется.
4. При ошибке SHA, PIN, неподдерживаемом пути или опасной ссылке — STOP. Не делать auto-retry и не устанавливать ничего.

## Что подтверждает и чего не подтверждает
R19 различает точный оригинал EEex v1.1.7, эквивалентный по LF/CRLF вариант, локальный вариант с нужными вызовами и HOLD при пропавших/испорченных файлах. **Ни один из результатов не доказывает безопасную продолжительность жизни `CItem.pRes.pHeader` или валидность `Item_ability_st` во время `sprite:getLauncher`.** `safeToCallGetAbility=false`, `safeToCallGetLauncher=false`, `weaponSwitchAuthorized=false`, `installAuthorized=false` остаются НЕИЗМЕННО.

TD15 R13.2 в игре установлен и ранний LIVE-тест 4/4 события / 9/9 полей защиты успешен. R16–R19 — только source-only/offline. Автоматическое переключение оружия выключено; BG Voice RU, BG_EET_RU, EPS, SCS, сохранения и WeiDU не трогались.

## Одно действие пользователя
Закрыть игру (для статического R19 не нужно её запускать). Запустить **ТОТ ЖЕ** `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`, выбрать **164**, дождаться его завершения, прикрепить **один новый** `BGXAI_R20_EEEX_STATIC_*.json` из `C:\Users\Drevo\Documents\BGXAI_LIVE_REPORTS`. Не нужны бой, preflight, WeiDU, новая версия updater или дополнительные команды. Если возникнет STOP, прислать текст STOP; повторять вслепую нельзя.

Далее: оценить реальные установленные EEex-скрипты; точное совпадение является только СТАТИЧЕСКИМ подтверждением. Следующий R21 — исключительно анализ безопасной готовности native CItem/ability, без разрешения включить R18 автоматически.
