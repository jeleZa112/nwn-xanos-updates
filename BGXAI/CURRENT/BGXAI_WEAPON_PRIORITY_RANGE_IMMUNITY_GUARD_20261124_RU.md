# BGXAI — безопасный выбор оружия: дистанция, иммунитеты, происхождение боеприпасов

Дата: **24.11.2026**. Ветка `bg-eet-ai`, каталог `BGXAI/patchsets/ranged_fighter_guarded_20261119`. **SOURCE ONLY: DEPLOY NO, LIVE NO** для описанных изменений.

## Новая полезная логика

1. Если дальний quickslot имеет **достоверно** `inRange=false`, то он не требует *гипотетических* APR, THAC0, среднего урона и полного on-hit effect breakdown, чтобы быть исключённым из оценки **текущей цели**. Выбор оружия по другому слоту допустим только как необязательная READ-ONLY рекомендация, если тот другой слот имеет полные подтверждённые эффективные характеристики. При смене цели/дистанции результат нужно рассчитывать заново.
2. Для такого исключения должны быть доказаны **наличие оружия в слоте, режим дальнего боя, выбранная цель, актуальность снимка, корректность боеприпасов**. Три промежуточных слоя V4, V5 и Current Stats **не освобождают** от собственного APR/эффектов при `ammoVerified=false`, отсутствии `ammoCount` или неизвестной модели боеприпасов. V3 также отклоняет такой неполный снимок.
3. `immuneDamageTypes` теперь обязан быть **сплошным массивом без повторов**, значениями которого могут быть только `SLASHING`, `PIERCING`, `CRUSHING`, `MISSILE`. Именованные таблицы `{SLASHING=true}`, смешанные ключи, пропуски, дубликаты и неизвестные типы возвращают `IMMUNITY_SET_INCOMPLETE`, а не игнорируют иммунитет. Существующий формат массива сохраняется.
4. **Никаких игровых приказов.** V3/V4/V5, мост статистики и NONINTERRUPT остаются без `SelectWeaponAbility`, `Attack`, `ClearActions`, `SetGlobal`, Lua file IO или EEex action dispatch. Все ответы `executable=false`, `dispatchAuthorized=false`.

## Пакетная проверка в данном обращении

На локальном LuaTeX (режим Lua-only): **145 отдельных Lua-проверок** (V3 53, V4 34, V5 25, NONINTERRUPT 22, интеграция 11) плюс **288 детерминированных сочетаний состояния** (дальность true/false/unknown × боеприпасы 0/20/unknown × полные/неполные характеристики × иммунитеты 4 вида × ручной приказ/EPS заняты/свободны × верная/подменённая цель): **433/433 PASS**. Также Python `--static-only` проверяет запрет игровых команд в пяти advisory-модулях.

Проверено: два последовательных такта, отсутствие мутации входного снимка, запрет команд, стабильность при неизвестных полях, корректная идентификация слота, стоп при подмене цели, непрерывание текущего приказа. **Эти 433 — offline тесты и комбинации данных, не игровые A/B-проверки или новые нативные EEex вызовы.** Новая GitHub CI должна отдельно подтвердить Lua5.3 на Ubuntu и статический код на Windows; её статус не считать PASS до явной проверки завершённого run.

## Необходимый следующий реальный рубеж

- R27 LIVE observer 24/24 и R28 native ITM 4/4 **уже выполнены** — не повторять 165→5/6 или старые 158–165. R27 подтверждает лишь текущий selected APR и сырые quickslots; R28 читает статические предметы, не предоставляет APR альтернатив в текущих бафах.
- Безопасный обёрточный native API для получения `CItem:getAbility()`/`sprite:getLauncher()` и времени жизни pointers в установленном EEex1.1.7 **не доказан**; этот путь не вызывать. `EEex_Action_Execute...Instantly` не применять для `SelectWeaponAbility` (undefined behavior вне `INSTANT.IDS`).
- **Следующий безопасный кодовый этап:** исследовать реальный источник provenance manual/EPS очереди и подтверждённое alt-slot effective APR, затем связать существующие оценщик V3/V4/V5 + NONINTERRUPT + уже написанный ограниченный `BGXAI_WEAPON_SLOT_CONSUMER_V3.baf`. Запрещено подставлять synthetic `verified=true` и устанавливать producer без доказательства безопасности.
- Установленные BGXRANGED6, R27, EPS18.4, EET/SCS/EEex, единый `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`, BG_EET_RU, BG Voice RU и сейвы оставлены без изменений. Любая будущая установка потребует отдельного typed разрешения, SHA preflight, внешнего backup, WeiDU last-only и LIVE A/B.

## Контрольные исходники SHA256 (до публикации)

- V3 `decf24ef567688e56a80a9e265f88391b7fd7c3668b67c9d3ea05d500d87fe75`
- V4 `c0cb4a5189d0a237acf92554198270ef33f0ab843bba6099a47debd5f218b460`
- V5 `b7f601cf71654500eb3115fb1e32acbf5cfd51b1f416af9877594f53c04c73c5`
- Current Stats `11cf8255e94f57ad3b9d798b389e242c8074b7b671217f49a5e4b976669291b1`
- Suite `028be2ebe3ec1874dd67dd4f521400ce51b2e29d4ea0e264c19e80d42269821e`
- Matrix `5ee2e2a9c57c17340e2c81f7d8faeee0d904a0d59065e5f5593efb325074080c`

## CI и непосредственное исследование следующего блокера (подтверждено после публикации)

**Публикация:** GitHub `bg-eet-ai`, commit `aded00f36c4f92540df03bf38ffe08a751d08946` — атомарно опубликовано 12 файлов. Независимый GitHub Actions run [`45321005280`](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45321005280): **completed / success**, `behavior-native-lua` **SUCCESS** (145 отдельных Lua-тестов + 288 состояний), `windows-static-no-game` **SUCCESS**. Не путать с другим workflow `bgxai-wtasight-enemy-guard.yml` (раньше уже завершался `failure` и по этому коммиту снова `failure`); он относится к прежней инфраструктуре и не входит в данный 433-пакет. Не объявлять все workflow репозитория зелёными.

**Продолжение после PASS без запроса `+`:** проверен подлинный `EEex/copy/EEex_scripts/EEex_Action.lua` upstream `v1.1.7`.
- `EEex_Action_AddSpriteStartedActionListener(func)` регистрирует слушателя начала действия, но фактический `EEex_Action_LuaHook_OnAfterSpriteStartedAction(sprite)` вызывает `listener(sprite, sprite.m_curAction)` **без доказанного поля источника действия**. Он подтверждает `action` и `sprite`, а не то, было ли действие ручным, инициированным EPS или BGXAI. Источник: https://github.com/Bubb13/EEex/blob/v1.1.7/EEex/copy/EEex_scripts/EEex_Action.lua#L174-L190 и #L326-L340.
- `EEex_Action_QueueResponseStringOnAIBase` *добавляет* команды в очередь; `EEex_Action_ExecuteResponseStringOnAIBaseInstantly` не поддерживает обычные не-INSTANT.IDS действия и не должен применяться к переключению. `ActionListEmpty()` в BAF не доказывает, что нет непрерывного ручного приказа / текущей атаки.
- Поэтому **не регистрировали никаких новых слушателей, не активировали producer, не трогали BAF/BCS/EEex**. Следующий инженерный путь ограничен: доказать происхождение очереди и effective APR альтернатив с поддерживаемыми событиями/native фактами либо оставить `KEEP_CURRENT_WEAPON_NO_DISPATCH`. Одно и то же исследование старого R21/R23 заново не повторять.