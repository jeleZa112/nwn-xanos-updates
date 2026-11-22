# BGXAI 162 — опубликовано исправление 8-символьного Lua-имени R13

Дата: 23.11.2026, время Москвы/Новосибирска уточняется отдельно. Последний пользовательский факт: он подтвердил запуск через **InfinityLoader**, но JSONL R13 в `BGXAI_LIVE_REPORTS` после боя отсутствует. НЕ просить повторять бой и установленную R13.1.

В коде прежнего R13.1 источник `override/M_BGXTDEF13.lua` с resref `M_BGXTDEF13` (12 символов), что превышает 8-символьный лимит Infinity Engine. Синтаксис/предыдущие Lua unit tests могли быть PASS, но движок не обязан автозагружать такой файл. Установленный исходный модуль в игре нельзя удалять вручную. Новый компонент `BGXTD14` через WeiDU добавляет только `override/M_BGXD13.lua` с resref длиной 8 и защитой от повторной регистрации. Исходный R13 остаётся установленным и неизменным.

## Статусы
- V3/R13.1 старый игровой install: `BGXTD13_INSTALLED_AWAITING_LIVE_TEST`, SHA256 `5c77a460d6b429cec6f9f81e7bf6883ee1f59474cfb95778091ab769302ef414`, backup `C:\Users\Drevo\Documents\BGXAI_BACKUPS\PRE_BGXTDEF13_20261122T170836264834Z`.
- BGXTD14 исправление: **CODE PASS / CI PASS / DEPLOY NO / LIVE NO**. Не утверждать, что исправление успешно заработало в реальном игровом Lua.
- Обновлятор: одна пользовательская точка `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`. Прежние пункты 1–161 сохранены побайтово при обратном переименовании внутренних переменных. Меню 162: `Fix R13 Lua 8-char name (READ ONLY default / guarded)`, вложенное 1=status RO, 2=preflight RO, 3=install только с точным токеном `INSTALL_BGXAI_R13_SHORTNAME_FIX`, 4=rollback только с токеном `ROLLBACK_BGXAI_R13_SHORTNAME_FIX`.
- Release commit: `dec88235c0231feca2238aa1e59025b6a6b78ac5`; PIN promotion commit: `796eefd64187d1c7ad8c9f8ffac6aebf6f885c81`.
- Обновлятор 79 529 байт, SHA256 `7f3baca4f34ed800069d2f6d6201fe68d93572c815f70cbed069ee983a8749cf`, проверен GitHub после публикации.
- Guarded installer SHA256 `21096246bbfe5647c6441ff34e22b2b50d6ae3e1f030536167041d76531d8b92`, новый Lua SHA256 `c0fb928001d5fb042a935302270df73130bed9576d331b2e4b41f27ee0244511`.
- GitHub CI run `45050119039`: 12/12 menu regression, 35/35 guarded installer tests, Lua 5.4 startup/singleton smoke, Windows PowerShell 5.1 and 7 AST PASS.

## Следующее действие пользователя
Закрыть игру/InfinityLoader (если они ещё запущены), запустить **тот же** `BGXAI_UPDATE.cmd`, выбрать **162 → 2 (READ ONLY preflight)**, прикрепить полный результат/status. Ожидается `BGXTD14_SHORTNAME_PREFLIGHT_PASS_NO_INSTALL`. Не выбирать 3 до проверки нового отчёта и отдельного согласия. Не копировать/переименовывать файлы вручную, не повторять 160/161 и бой. После PASS пользователь может отдельно согласиться на установку 162→3; это требует точного typed токена, внешней SHA-проверенной резервной копии и WeiDU last-only. После установки проверить появление SESSION/READY до боя, только затем DEFENSE.

Правило продолжения: безопасные работы самостоятельно, необходимость действия пользователя формулировать конкретно, без просьбы `+`.
