# BGXAI R27 — готовый исходный кандидат однократного пассивного наблюдения (23.11.2026)

## Четыре статуса

- **CODE:** SOURCE-ONLY READY — `BGXAI/BUILD/R27_SINGLE_CALLBACK_SELECTED_RO_20261123/` в GitHub `bg-eet-ai` и в библиотеке.
- **TEST:** independent GitHub Actions run **45204633757** completed SUCCESS: Windows **18/18** Python source/SHA, Ubuntu **18/18** Python + **33/33** Lua один callback + **11/11** Lua simulation bootstrap = **62/62**; SHA256 manifest и исходные R2/R4 пройдены. Предыдущая CI ошибка была от ошибочной публикации текста сообщения инструмента вместо test_r27_source.py, исправлено точным восстановлением; последний прогон чистый.
- **DEPLOY:** NO — **M_BGXR27.lua не устанавливался в игру**.
- **LIVE:** NO — новых игровых наблюдений R27 нет. Последний LIVE — ранее установленный TD15/R13.2 и уже проведённые R2/R4 эксперименты. R20/menu164 повторять не требуется.

## Функциональная новизна

- В одном callback-е начатого действия выполняются **неизменённые** оригинальные `BGXAI_WEAPON_SLOTS_R2_READONLY.lua` и `BGXAI_WEAPON_ACTIVE_R4_READONLY.lua` на одинаковом `sprite,action`; сверяются персонаж, действие, selected slot/ability **до/после** чтения. Это устраняет необходимость **эвристически** стыковать два раздельных лога R2 и R4 для следующего эксперимента. Композитор использует exact SHA256 обоих старых модулей; старые оригиналы НЕ переписаны.
- Извлекаются текущий выбранный APR raw key, STR, THAC0, haste, базовые raw данные четырёх quickweapon и четырёх quiver slots. Неизвестное или изменившееся состояние → `HOLD`.
- Подготовлен **восьмизначный game resource** `M_BGXR27.lua`, SHA256 `e5eb400c56ffb1bc23344a0cf30dcc724d8d18fc2752fabd1c2c63cdcca73735`. Этот файл **при загрузке в игре зарегистрирует** пассивный EEex listener, поэтому его нельзя устанавливать без отдельного typed согласия. В репозитории и Library он хранится **только как source-only staged candidate**, нет автоматической загрузки или изменения original updater. В mock подтверждена единожды выполненная регистрация и одна JSON строка `BGXR27` на действие (максимум 64).
- **Нет** доступа `item:getAbility`, `getLauncher` или `EEex_Resource_Demand`; **нет** игровых приказов, записи LOCALS/BCS, переключения оружия, сброса очереди, изменений EPS 18.4, сейвов или иных проектов.

## Что ещё НЕ доказано

Selected-only APR НЕ равен эффективному APR всех альтернативных слотов. Нельзя подтверждать полный список эффектов, native engine event/session identity, launcher/ammo pair или доказанно свободную EPS/manual очередь по одним raw полям. `weaponSwitchAuthorized=false`, `dispatchAuthorized=false` остаются принудительными. Source CI PASS НЕ является GAME LIVE PASS.

## Единый следующий реальный шаг

Для практического **живого** read-only пилота нужна отдельная явная авторизация пользователя **на добавление guarded пункта в существующий `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd` и последующую установку только `M_BGXR27.lua`**. Прежде чем устанавливать: сверить Game root и manifest SHA, закрытые game/InfinityLoader/WeiDU процессы, актуальный WeiDU.log и last-only overlay, полноценную проверяемую внешнюю backup, восстановление при STOP, отсутствие конфликтов; никаких изменений BCS/EPS. Установку проводить только через единственный updater после отдельного точного typed токена в самой программе; новые CMD/ZIP не создавать. Далее один короткий обычный игровой опыт, один лог R27 и анализ. **На данный момент этого нового пункта updater ещё нет и установка не происходила.**

**Правило проекта:** после безопасного PASS продолжать следующий доступный безопасный шаг в текущем обращении, не просить `+`. Останавливаться на явном разрешении для игрового deploy, недоказанном runtime API или невозможной безопасности, не обещать фоновой работы.

## Ссылки

- R27 code and tests: https://github.com/jeleZa112/nwn-xanos-updates/tree/bg-eet-ai/BGXAI/BUILD/R27_SINGLE_CALLBACK_SELECTED_RO_20261123
- R27 independent CI success: https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45204633757
