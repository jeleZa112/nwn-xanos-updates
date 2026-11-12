# BGXAI 064 — работающий updater 72–76 опубликован (2026-11-12)

## Подтверждённые результаты пользователя
- EET v2.6.6.0 Lua console: `BGX64 AREACHECK true true`; реальная функция `EEex_UDEqual` сравнила области двух спутников без Lua ошибки. **Это не доказательство поведения из on-hit callback.**
- `BGXAI_UPDATE.cmd` пункт 68: WeiDU 061 last True, staged/live BCS+Lua SHA совпали. BCS `db0fcba4678b00defa2ed7887b57c0d4207effc064891aeb9a0d7dcc1a1a6b0b`; Lua `fd39d23dc722b549c2af1eaf065541b2ed358a9714f2636b8cab4e45fe7dcec5`.
- Пункт 71 в реальном Windows: 10/10 source VERIFY, `064_SOURCE_ONLY_PREFLIGHT_PASS`, installed game unchanged.
- PowerShell 5.1 parser of immutable 72–76 draft, user actual `BGXAI 064 SYNTAX PASS`.

## Выполнено после native SYNTAX PASS
- Проверен 064 guarded WeiDU package: все 10 pinned manifest files в Library и GitHub сверены; `python -m unittest discover -p 'test_064*.py' -q` **46/46 PASS** в изолированной модели установки и отката. Исходники сохраняют исходную Lua 061 и целевой Lua 064, изменяют только `override/M_BX43.lua` через WeiDU после backup.
- `BGXAI_SYNC_072_076_DRAFT.ps1` из commit `e497515d763e0de839e573bc32a4c9b4cc13ef2f` был разобран настоящим Windows PowerShell: SYNTAX PASS. После пяти обратимых блоков он строго восстанавливает предыдущий updater, сохраняя все старые пункты 1–71.
- Опубликован действующий `BGXAI/BGXAI_SYNC.ps1`, pinned immutable commit **`d66ae072c4a1466521d384c15fe5c0c1ed6205cc`**; SHA256 **`d246e6e286f760a1824c65e73e42ff2d8d29f5aa0fb46c1fb97409e04f06c1b1`**, размер **59433 байт**, Git blob `ffb7558caf39e8f640dc02386c37c536b4bf6fbf`.
- На новом immutable commit повторно проверены SHA256 и размеры **всех 10/10** исходников манифеста `BGXAI/fox_new/experimental_064_guarded_weidu_source_only/manifest.json`; script SHA/size также PASS.
- `BGXAI/fox_new/BOOTSTRAP_PIN.json` обновлён, commit **`ab215424045b9427eb027cdc9229fb62bc1f45b8`**, указывает на immutable updater commit и exact SHA/size; существующий пользовательский `BGXAI_UPDATE.cmd` сам подтягивает его. Никаких иных CMD не нужно.
- Новые меню: **72** скачать и проверить source; **73** скачать и read-only WeiDU preflight 061+064; **74** guarded install Lua-only с ручным токеном `INSTALL_BGXAI_064`, закрытыми игровыми процессами и внешним SHA-backup; **75** status; **76** rollback с `ROLLBACK_BGXAI_064`. **74 НЕ запускался.**
- В отличие от 68, меню 73 загружает исходники в `BGXAI_DEV/experimental_064_guarded`; не меняет `override`, WeiDU и установленную 061. Термин read-only относится только к игровым файлам, не всей папке.
- Реальная Windows установка 064 **ещё не тестировалась**. Готовность требует сначала **реальный пункт 73**; после PASS отдельно согласовать рискованную установку и закрыть игру. Автоматическое согласие на SOURCE разработки не отменяет подтверждения установки.

## Следующее действие
Попросить пользователя запустить **прежний `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd` и выбрать 73**, прислать полный вывод. Пункт 72 отдельно не нужен, потому что 73 сам скачает. Не просить повторять 68/71/EEex или переприсылать файлы. Если меню не обновилось/sha не совпала — STOP, безопасная диагностика. Пользователь просит автоматически продолжать все безопасные этапы после PASS в пределах одного ответа, но не обещать фоновые действия.
