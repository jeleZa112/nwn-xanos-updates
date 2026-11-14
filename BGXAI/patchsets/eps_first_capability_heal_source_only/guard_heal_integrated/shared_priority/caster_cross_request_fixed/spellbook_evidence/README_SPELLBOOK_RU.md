# BGXAI 066S — EEex 1.1.7: чтение подготовленных заклинаний без изменения игры

**Статус:** SOURCE ONLY, НЕ УСТАНАВЛИВАТЬ. Игра остаётся на живой 066S, EPS 18.4 сохраняет исполнение атак, бафов, лечения и других действий.

## Что реализовано

В уже сохранённый `M_BX43_066S_CAPABILITY_CANDIDATE.lua` добавлен маленький read-only модуль `BGX66_EEEX117_SPELLBOOK_EVIDENCE.lua`. Он читает имеющиеся записи 1-го круга в полях `CGameSprite.m_memorizedSpellsPriest` и `m_memorizedSpellsMage` через `:getReference(0)` и `EEex_Utility_IterateCPtrList`; для записи сверяет `m_spellId:get()` и младший бит `m_flags`. Проверяются ресурсы **SPPR103** (`CLERIC_CURE_LIGHT_WOUNDS`) и **SPWI114** (`WIZARD_SHIELD`) — значения взяты из уже сохранённого пользовательского `SPELL_POLICY_CATALOG_469.csv` (EET `SPELL.IDS`, `SPL+TLK`), а не угаданы.

`BGX66SpellbookEvidence.read(actor, symbol)` возвращает структуру с `ready_count`, `book_record_read`, но принудительно `castable_now_proven=false`, `manual_order_origin_proven=false`, `queue_empty_proven=false`, `class_kit_dual_active_proven=false`. Никаких `Spell`, `Attack`, `ClearActions`, очередей действий, записи LOCALS, флагов памяти и новых слушателей событий. Неизвестный тип заклинания, недоступная книга, отсутствующий EEex API или некорректные данные → `nil` (не выдавать ложное «готово»).

При наличии **отдельного доверенного** `S.capabilityVerifier` ему передаётся **третьим аргументом** эта ограниченная информация; старые двухаргументные функции совместимы. `S.requireMemorizedEvidence=false` по умолчанию; если **отдельно** включить строгую проверку, отсутствие читаемой свободной записи запрещает запрос, но наличие записи всё равно **не разрешает** запрос без отдельного `capabilityVerifier`. Никакое включение не выполняется автоматически. Для шаманов/чародеев, которые могут применять заклинания без обычной подготовки, отрицательная проверка книги **не доказывает отсутствия способности**: их механика требует отдельной проверки; опциональный строгий режим пока НЕ использовать для них.

Встроен только фрагмент чтения; прежние две проверки пересекающихся BCS-запросов и приоритет срочного лечения сохранены из предыдущей версии SOURCE ONLY. Старые ограничения `ActionListEmpty()` и порядок EPS не меняются. Никакой автоматизации на основе сырого события начала действия: EEex 1.1.7 не доказывает происхождение ручных приказов.

## Подтверждённые API и источники

- Официальный `Bubb13/EEex`, **tag `v1.1.7`**: `EEex/copy/EEex_scripts/EEex_Utility.lua`, Git blob `f10ed5e25ff0c03bc63507d04263f96daae60e7b`, функция `EEex_Utility_IterateCPtrList` (чтение узлов CPtrList).
- Официальный `EEex_Trigger.lua` blob `80da96ed5dc7cbcaa726631a3542ecafa533ec6f`: `EEex_Trigger_EvalConditionalStringAsAIBase` затрагивает `m_pendingTriggers`; специально **НЕ используется**.
- `Gibberlings3/Tweaks-Anthology` `cdtweaks/luke/lua/class/spontaneous_casting.lua` blob `74ad408872f9e45a9d27e0b578134e1bed80d2b9`: считывание `m_memorizedSpellsPriest`, `m_spellId`, `m_flags` и bit0. Из примера **не перенесены операции записи**.

## Проверка пакета

Распаковать в пустую папку, НЕ рядом с игрой. При наличии Python 3 и библиотеки `liblua5.4`:

```bash
python verify_spellbook_release.py
python run_extended_regression.py
texlua parse.lua M_BX43_066S_EEEX_BOOK_EVIDENCE_CANDIDATE.lua
```

Исходная 066S 18/18; обновлённый кандидат 74/74 (исторические, охрана, лечение, BCS-коллизии и новая книга заклинаний). Всё выполняется на Lua 5.4 **mock EEex**, без игрового движка. Проверка исходников и хешей отдельно. Не является доказательством, что EEex в установленной EET предоставляет нужные структуры в бою, что дуал имеет активную магию или что система безопасно перехватывает команды игрока.

## Следующий реальный барьер

Для включения боевого управления нужны подтверждённые в реальном EET: статус текущей очереди EPS, происхождение ручного приказа, активность старого класса у дуала, ограничения колдовства, совместимость идентификаторов BCS-цели. До этого `T.capabilitySourceVerified=false`, `T.capabilityVerifier=nil`, `S.capabilityVerifier=nil`, `S.requireMemorizedEvidence=false`. Не устанавливать ни в `override`, ни через WeiDU; установленный 066S не трогать.
