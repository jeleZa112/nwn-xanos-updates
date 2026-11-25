# BGXAI R34 — живой профиль R33 + актуальные ITM предметы, READ ONLY

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
