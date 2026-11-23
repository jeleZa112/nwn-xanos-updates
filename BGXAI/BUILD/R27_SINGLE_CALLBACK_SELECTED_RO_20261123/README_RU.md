# BGXAI R27 — пассивный кандидат единого события R2 + R4 (SOURCE ONLY)

**Цель:** заменить эвристику соседства двух журналов R2/R4 одним вызовом *обоих существующих наблюдателей* внутри одной функции обработчика начала действия. R27 не меняет оружие, не пишет LOCALS/BCS, не вмешивается в EPS и не вызывает подозрительный `item:getAbility()` или `getLauncher()`.

## Реально сделано

- `build_r27.py` из **неизменённых оригиналов** `BGXAI_WEAPON_SLOTS_R2_READONLY.lua` и `BGXAI_WEAPON_ACTIVE_R4_READONLY.lua` генерирует самодостаточный `BGXAI_R27_SINGLE_CALLBACK_SELECTED_RO.lua`. Обе оригинальные SHA256 проверяются до композиции; оригиналы остаются в `BGXAI/patchsets/ranged_fighter_guarded_20261119/` — их не копируют в релиз для установки.
- `R27.observe(sprite, action, partyIndex, getActiveStats)` вызывает *те же* `R2_CORE.observe_sprite` и `R4_CORE.observe` на **том же Lua-объекте sprite и action**, проверяет scalar actor/action/slot/ability до и после чтения, сравнивает ответы, извлекает только **APR текущего выбранного слота**.
- Отдельная `R27.makeListener({portraitIndex,getActiveStats,emit})` возвращает **замыкание-кандидат** для будущей интеграции. **Никакой регистрации EEex при загрузке нет.** В R27 добавлен ограниченный JSON-форматтер `toConsoleJson` и `prepareConsolePilot`, принимающий **переданный** вывод `emitString`; нет автоматического игрового writer-а, монтирования, WeiDU или изменений единого обновлятора.
- Можно получить одну ограниченную строку `BGXR27` с идентификатором текущего выбранного слота, выбранным APR и 8 сырыми слотами R2; `prepareConsolePilot` только готовит, **не регистрирует**.
- Любое расхождение, нестабильность или неизвестный APR вызывает `HOLD_SINGLE_CALLBACK_NO_DISPATCH`. Даже успешная выборка содержит `nativeEventTokenAuthenticated=false`, `alternativeAPRVerified=false`, `completeActiveEffectsVerified=false`, `launcherAmmoPairVerified=false`, `epsManualQueueVerified=false`, `engineSessionVerified=false`, `weaponSwitchAuthorized=false`, `dispatchAuthorized=false`, `ordersSent=0`.

## Проверки

```bash
python BGXAI/BUILD/R27_SINGLE_CALLBACK_SELECTED_RO_20261123/build_r27.py
python -m unittest discover -s BGXAI/BUILD/R27_SINGLE_CALLBACK_SELECTED_RO_20261123 -p 'test_r27_source.py' -v
lua5.4 BGXAI/BUILD/R27_SINGLE_CALLBACK_SELECTED_RO_20261123/test_r27_single_callback.lua
```

R27 не устанавливался в EET, не регистрировал callback в живом EEex; Lua mock не доказывает безопасность версии установленной DLL. Он устраняет архитектурный **дублирующий** callback/лог и создаёт точный градуируемый прототип следующей минимальной пассивной диагностики, но только **после отдельного typed разрешения** и полноценного preflight/backup/rollback через **существующий** `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`.

## Важный блокер и план безопасного живого опыта

Для реального пилота нужен **отдельный installer-integration patch**, который до установки проверит SHA источников, закрытие игры, внешнюю резервную копию, WeiDU last-only rollback и отсутствие конфликтующих R2/R4 в новой точке регистрации; после типизированного подтверждения установит только пассивный callback с ограничением 64 событий и одним выходным журналом. В настоящем выпуске нет auto-registration или installation package. Сразу после установки повторно проверять выбранное оружие, боеприпасы и бафы на пользователе без специальных повторных 158/164; **не** использовать эти данные для автоматического выбора оружия без последующей защиты альтернативного APR и ручной/EPS очереди.

## Отдельный кандидат игрового модуля, без установки

Дополнительно создан **`M_BGXR27.lua` (8-символьный game RESREF)** — строго детерминированная композиция проверенных R2/R4 и пассивного bootstrap `R27_AUTHORIZED_PILOT_BOOTSTRAP.lua`. Он **зарегистрирует** слушатель EEex **если его загрузить в игре**, поэтому **не загружать и не копировать в override без явного typed согласия и предварительно проверенного старого единого обновлятора**. На этапе исходников он нигде не устанавливается. Слушатель ограничен 64 наблюдениями, пишет только `Infinity_Log` или `print`, имеет один маркер `SESSION` и одну JSON-строку на запущенное действие. Не делает оружейных команд, не заявляет engine-session/event identity и не может вычислить APR другого слота. В mock проверяется и одноразовая регистрация, и ограниченный вывод.

Ближайший следующий этап — безопасная интеграция **этого точного файла** через существующий `BGXAI_UPDATE.cmd`: прежде чем что-либо копировать, установить новый охраняемый пункт с источником, pinned SHA, проверкой закрытой игры, внешним backup, WeiDU-last-only rollback и отдельным typed разрешением. Сейчас такой пункт **ещё не установлен**.
