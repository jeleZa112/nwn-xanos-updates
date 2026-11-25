# 26.11.2026 — R34 historical R33 aggregate fallback / READ ONLY

Реальный пользовательский запуск меню 173 с immutable `124add6624c4` завершился `R34_R33_NAMED_LOG_DIFFERS_AND_FAILS_FINGERPRINT`. Этот результат доказывает отказ конкретного локального журнала при сравнении, **а не** ошибочность ранее загруженного исходного журнала. Повторять R33, игровой бой, установку или старый пункт 173 не нужно.

Из Library заново прочитан оригинальный 8-событийный R33 журнал (схема, SESSION, seq, целостность профиля, слоты, 46 статов). Сопоставлен с реальным отчётом R28: `BOW05` имеет `proficiencyIdRaw=105`, а у Халида stat 105=0 (при stat 104=1 для длинных луков). Это историческая сверка разных дат, не утверждение об актуальном состоянии экипировки.

Добавлен узкий fallback в **тот же исходник R34**: сначала существующее точное локальное чтение; только при трёх явно названных проблемах местного R33 журнала доступен сохранённый минимум уже полученных исторических наблюдений. Он не содержит исходный приватный лог или actor ID, строго проверяется на совпадение всех полей, а результат помечается `HISTORICAL_R33_PROFILE_CURRENT_ITM_JOINED_RO_NO_SWITCH`, `historicalProfileOnly=true`, `sameBytesAsUserUploadedLogVerified=false`, `sessionTemporalAlignmentVerified=false`. Несоответствующие ITM по-прежнему не угадываются, а читаются из текущего `chitin.key`/`override`/BIFF через прежний SHA-pinned R3. Настоящий порядок ручных/EPS действий, альтернативный effective APR и право смены оружия остаются **НЕ подтверждены**, приказов ноль.

Релизные проверки завершены успешно: R34 active onefile Windows/Linux/PowerShell 5.1 3/3 PASS (https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45662096145), исторический R33 native/WeiDU 5/5 PASS (https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45662096366). Подтверждения нового R34 на пользовательском Windows пока нет. Новый SHA pinned: source `d40f7729ee84c576d08fe712b98adcd0704611def6385e976a50597b68c496c4`, backend 79 775 bytes SHA256 `9131e29da59b7d3a62651eab3ff7deee514da426cfbe6a1267b54444e9c6f59a`, immutable `1404112c2889561b99416e48a4ba06ab947c4fee`; original `BGXAI_UPDATE.cmd` не менялся. Historical first 172 menu handlers unchanged. CI завершён. Один новый READ ONLY запуск 173 возможен для свежего чтения ITM, но R33/бой/инсталляцию не повторять; не считать исторический профиль живым замером.

---

# BGXAI R34 — живой профиль R33 + актуальные ITM предметы, READ ONLY

## HOTFIX 25.11.2026 — R34 LIVE LOG PIN STOP (точный SHA верен, поиск был хрупким)

Пользователь при `BGXAI_UPDATE.cmd` (загружен `b678020a5dee`) выбрал меню 173, получил `R34 LIVE LOG PIN STOP`. По оригинальному пользовательскому файлу `BGXAI_R33_CONSOLE_20261125T161358491052Z.log` **реально пересчитан** SHA256 `d510da7e5c15d1579266b37a89fdf91ceff91622714a142e1c137376ec239538` (101981 байт). Следовательно, хардкод SHA был верен, но `HashFile` на ожидаемом локальном пути возвращал не этот хеш или пустую строку; отличить по старому STOP невозможно.

**Новая логика безопасного READ ONLY выбора входа**: только собственная папка `Documents\BGXAI_LIVE_REPORTS`; до 128 нерекурсивных `BGXAI_R33_CONSOLE_*.log`. Прежде всего точное совпадение SHA загруженного файла. Если байты изменены/переименован файл, допускается ровно один структурно корректный 8-event R33 session с совпадением уже известного профиля и экипировки Халида; статус `STRUCTURAL_R33_FINGERPRINT_ONLY_DIFFERENT_SHA`, `sameBytesAsUserUploadedLogVerified=false`. Файл вне папки не ищем, непроверенные symlink/junction не читаем, при неоднозначности/подмене возвращается JSON HOLD. Любая информация по alternative APR, происхождению приказа и безопасному переключению остаётся HOLD; auto switch OFF. Никакого нового тестового боя и reinstall.

**РЕЛИЗ:** `BGXAI/BGXAI_SYNC.ps1` 79 775 B SHA256 `9b44a5cf6ffd83c97c17c49ac9533b102bcdef7a004da4840636762a91cb2db5`, immutable `124add6624c4cfd054b2cee61f37d5af5f093bea`. BOOTSTRAP_PIN обновлён, старые пункты 1..172 нетронуты. [R34 исходники Windows+Linux 22/22 PASS](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45660217453); [R34 active CI 3/3 PASS, включая PS5.1 запуск до меню](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45660513142); [R33 historical guard regression 5/5 PASS](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45660551436). Это код и CI, новый выпуск **на ПК пользователя ещё не запускался**.

**Единственное действие пользователя:** закрыть игру и InfinityLoader → старый `BGXAI_UPDATE.cmd` → дождаться `verified pinned script 124add6624c4 (SHA256 OK)` → **173** → прислать один `BGXAI_R34_NATIVE_PROF_*.json`. Если STOP, прислать JSON c причиной, без повторных запусков.

---


**Дата:** 25.11.2026. **Реализация:** `BGXAI_R34_NATIVE_PROF_BRIDGE_RO.py` + существующий, SHA-pinned `BGXAI_WEAPON_NATIVE_ITM_R3_RO.py`. В единый `BGXAI_UPDATE.cmd` добавлен пункт **173**. **Никакой установки в игру: WeiDU, BCS, Lua, сохранения, EPS, BG Voice RU, BG_EET_RU не изменяются.**

## Задача

Связать ровно 8 реальных R33 событий из `BGXAI_R33_CONSOLE_20261125T161358491052Z.log` (SHA256 `d510da7e5c15d1579266b37a89fdf91ceff91622714a142e1c137376ec239538`) с собственными реальными ITM файлами текущей EET. Не нужно заново запускать R33 или игру. Модуль проверяет установленный `override/M_BGXR27.lua` и `BGXR33/PROOF.json`, обрабатывает старый конкретный LOG как исторические наблюдения и **заново** читает `chitin.key`, `override`, BIFF ITM из игры. 

Сопоставляет `proficiencyIdRaw` (ITM 0x31) с `proficiencyStat89to134Raw`, выделяет именно нижние 3 бита активных пунктов; помечает `0` только у известной профессии `89..134`, неизвестные типы не объявляет непрофессиональными. Сохраняет значения атак, типы, возможность лука/стрел, эффекты, исходные SHA ITM. Статус является источниковым соединением, **не** удостоверением итогового APR альтернативного слота или идентичности предмета на момент записи R33.

## Один пользовательский шаг

Закрыть игру/InfinityLoader/WeiDU → открыть **тот же** `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd` → выбрать **173**. Обновлятор загрузит код R34 и уже проверенный R3 из одного immutable git commit, сверит SHA256, сверит ранее присланный LOG по SHA и создаст ОДИН JSON в `C:\Users\Drevo\Documents\BGXAI_LIVE_REPORTS\BGXAI_R34_NATIVE_PROF_*.json`. Прислать JSON, при STOP — одну ошибку, **не** переустанавливать R33. Ручные Python/PowerShell/второй CMD не нужны.

## Доказательства и ограничения

- SOURCE Python CI: [R34 native Windows+Linux test](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45654109664) SUCCESS на синтетических ITM, настоящий R3-парсер, все команды запрещены.
- Onefile stage CI: [R34 3/3 menu173 stage](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45654490721) SUCCESS (Windows+Ubuntu SHA, 172 старых обработчика byte-identical, Windows PS5.1 AST + параметр `-Lit`, встроенный `gc`).
- Active release CI: [R34 3/3 immutable onefile pin](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45654676537) SUCCESS.
- Один основной CMD без изменений; новый backend `BGXAI/BGXAI_SYNC.ps1` 79 935 байт SHA256 `c900e8aa6c4ec92bcb80cac1624cf1d6caa477dc961dd137555508e14e9d1f78`, pin commit `38c7d2ee3bfc7a50631bb3375e5c1ee2141c0d7d`.

**GAMEPLAY SWITCH HOLD:** `actionSourceReadStatus=ACTION_SOURCE_POINTER_UNAVAILABLE` в LIVE R33 8/8; `classRowVerified=false`, `actorPipsVerified=false`, `alternateEffectiveAPRVerified=false`, `completeActiveEffectsVerified=false`. Сначала сверить реально установленный тип/профиль BOW05; затем per-slot effective APR + eligibility + binding и безопасный noninterrupt момент. **R34 не отправляет ни одного приказа и ничего не переключает.**
