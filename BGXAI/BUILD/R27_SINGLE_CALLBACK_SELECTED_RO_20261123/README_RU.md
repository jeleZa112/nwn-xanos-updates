# BGXAI R27 — пассивный кандидат единого события R2 + R4 (SOURCE ONLY)

**Цель:** заменить эвристику соседства двух журналов R2/R4 одним вызовом *обоих существующих наблюдателей* внутри одной функции обработчика начала действия. R27 не меняет оружие, не пишет LOCALS/BCS, не вмешивается в EPS и не вызывает подозрительный `item:getAbility()` или `getLauncher()`.

## Реально сделано

- `build_r27.py` из **неизменённых оригиналов** `BGXAI_WEAPON_SLOTS_R2_READONLY.lua` и `BGXAI_WEAPON_ACTIVE_R4_READONLY.lua` генерирует самодостаточный `BGXAI_R27_SINGLE_CALLBACK_SELECTED_RO.lua`. Обе оригинальные SHA256 проверяются до композиции; оригиналы остаются в `BGXAI/patchsets/ranged_fighter_guarded_20261119/` — их не копируют в релиз для установки.
- `R27.observe(sprite, action, partyIndex, getActiveStats)` вызывает *те же* `R2_CORE.observe_sprite` и `R4_CORE.observe` на **том же Lua-объекте sprite и action**, проверяет scalar actor/action/slot/ability до и после чтения, сравнивает ответы, извлекает только **APR текущего выбранного слота**.
- Отдельная `R27.makeListener({portraitIndex,getActiveStats,emit})` возвращает **замыкание-кандидат** для будущей интеграции. **Никакой регистрации EEex при загрузке нет.** В `R27` нет игрового writer-а, монтирования, WeiDU или изменений единого обновлятора.
- Любое расхождение, нестабильность или неизвестный APR вызывает `HOLD_SINGLE_CALLBACK_NO_DISPATCH`. Даже успешная выборка содержит `nativeEventTokenAuthenticated=false`, `alternativeAPRVerified=false`, `completeActiveEffectsVerified=false`, `launcherAmmoPairVerified=false`, `epsManualQueueVerified=false`, `engineSessionVerified=false`, `weaponSwitchAuthorized=false`, `dispatchAuthorized=false`, `ordersSent=0`.

## Проверки

```bash
python BGXAI/BUILD/R27_SINGLE_CALLBACK_SELECTED_RO_20261123/build_r27.py
python -m unittest discover -s BGXAI/BUILD/R27_SINGLE_CALLBACK_SELECTED_RO_20261123 -p 'test_r27_source.py' -v
lua5.4 BGXAI/BUILD/R27_SINGLE_CALLBACK_SELECTED_RO_20261123/test_r27_single_callback.lua
```

R27 не устанавливался в EET, не добавлял callback к живому EEex; Lua mock не доказывает безопасность версии установленной DLL. Он устраняет архитектурный **дублирующий** callback/лог и создаёт точный градуируемый прототип следующей минимальной пассивной диагностики, но только **после отдельного typed разрешения** и полноценного preflight/backup/rollback через **существующий** `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`.

## Важный блокер и план безопасного живого опыта

Для реального пилота нужен **отдельный installer-integration patch**, который до установки проверит SHA источников, закрытие игры, внешнюю резервную копию, WeiDU last-only rollback и отсутствие конфликтующих R2/R4 в новой точке регистрации; после типизированного подтверждения установит только пассивный callback с ограничением 64 событий и одним выходным журналом. В настоящем выпуске нет auto-registration или installation package. Сразу после установки повторно проверять выбранное оружие, боеприпасы и бафы на пользователе без специальных повторных 158/164; **не** использовать эти данные для автоматического выбора оружия без последующей защиты альтернативного APR и ручной/EPS очереди.
