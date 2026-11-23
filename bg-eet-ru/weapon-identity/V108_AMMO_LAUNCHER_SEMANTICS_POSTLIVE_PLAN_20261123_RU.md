# BG_EET_RU — V108 post-LIVE: weapon / launcher / ammunition semantics (SOURCE ONLY)

Дата 2026-11-23. **Нет** новых Lua-хуков, новых установок, изменения игры или запуска Windows. Это проект следующей интерпретации при получении реального V108 callback.

## Новое доказательство (источники — публичные, не Windows LIVE)
1. **Подтверждение разработчика EEex.** На [Beamdog Forum, EEex, June 2020](https://forums.beamdog.com/discussion/71798/mod-eeex-v0-10-2-alpha/p33) Bubb описал запись **раздельных** `curWeaponIn` и `pLauncher` RESREF в расширенные поля damage effect под `EEEX_DAM`. В той старой реализации обсуждаются смещения x86; их **нельзя применять** к EET 2.6 x64. Но факт, что урон соотносится с двумя разными item identities, подтверждает необходимость не смешивать эти поля.
2. **Лук против боеприпаса.** [Beamdog forum Jan 2021](https://forums.beamdog.com/discussion/71798/mod-eeex-v1-3-1/p35): при выбранном оружии-луке с требуемыми стрелами «текущее оружие» в слоте может возвращать RESREF **боеприпаса**, а не лука; читать один current equipped slot недостаточно. Это сообщение про старый API и не гарантирует точной семантики `context.weapon` в V108.
3. **Идентичный callback.** [Tweaks Anthology](https://github.com/Gibberlings3/Tweaks-Anthology/blob/7649ced6cd25865874d787ec1a9abbc67b068729/cdtweaks/luke/lua/class/overwhelming_devastating_critical.lua) использует `EEex_Sprite_AddAlterBaseWeaponDamageListener`, `context.weapon.cResRef:get()` и `context.launcher`. Исходник работает с `Item_ability_st`, но не доказывает, что `weapon` всегда лук или всегда снаряд.

## Правила интерпретации будущих V108 событий
- `weapon_resref`: сохранить как **item, passed into damage callback**. Не подставлять название лука без сравнения с фактической экипировкой/ITM.
- `launcher_resref`: сохранить отдельно как **launcher, if present**. Если `launcher=nil`, не придумывать его.
- `ammo_resref`: **UNVERIFIED**, даже если `weapon_resref` выглядит как arrow/bolt. Доказать отдельно по ITM item category, способности и фактической экипировке на момент удара. Для метательных дротиков/кинжалов не создавать фиктивные «стрелы».
- `hit_miss`: callback damage нельзя автоматически считать источником промахов. `attackRoll` сам по себе не устанавливает попадание.
- `journal_row`: **UNVERIFIED** до независимой привязки атакующего, цели, последовательности и времени события к конкретной строке лога.
- **Никаких изменений FULL журнала**. Будущие BRIEF-only подписи лишь после LIVE+ITM validation.

## Компактный сценарий на Windows, если пользователь отдельно разрешит V108
1. Резервное сохранение и закрытие игры перед установкой. Запуск **только существующего** `BG_EET_RU_UPDATE.cmd --install-v108-native-read`; точная typed фраза из самого обновлятора; неподходящие SHA приводят к HOLD.
2. Через **тот же** CMD `--capture-v108-native-read`: одну-две атаки вблизи, потом одну-две атаки луком со стрелами. Закрыть игру для экспорта единого ZIP. Максимум 8 новых V108 образцов: не тратить на длительную стычку.
3. Сопоставить полученные `weapon_resref` и `launcher_resref` с **реальными** оборудованными предметами из сейва/скриншота. Разделить melee/ranged и data slot. Разбираем только наблюдаемый, не угадываем.
4. В следующих изолированных тестах — праща+пуля, арбалет+болт, бросковые дротики/кинжал и специальные луки с бесконечными боеприпасами; каждый кейс только если доступен у пользователя и не требует мешать BGXAI/Voice.
5. Если игра аварийно завершилась или инсталлятор SAFE_STOP, не делать ручных правок; использовать `--rollback-v108-native-read` с закрытой игрой и проверенным бэкапом.

## Состояние доказательств
- Windows: V107 STATIC PASS; V106 existing callback transport LIVE PASS (2 events).
- Current GitHub: V108 RELEASE + CI PASS, **not installed / no CItem LIVE**.
- Это исследование: SOURCE-ONLY, без новой версии релиза.
