# BGXAI 168: реальный отчёт + независимый аудит EEex/EPS (24.11.2026)

## Результат пользовательского запуска

Файл `BGXAI_AUTO_BATCH_RO_20261124T073318947435Z.json`, schema `BGXAI_AUTO_BATCH_RO_V1`.

- Status: **SAFE_READONLY_BATCH_COMPLETE_GAMEPLAY_HOLD**; 10 стадий; 512 синтетических fail-closed сочетаний, 50 Python-тестов (3 пропущены: 2 native POSIX-only и 1 batch), 108 source BAF assertions.
- `sourcePin`: PASS_PINNED_SOURCE; BAF SHA256 `92b8b1d3393a286d4d69f38b9542651acb429f8ef6627051195c7a1a95c09f30`.
- `nativeWeiDU`: PASS_PRIOR_NATIVE_COMPILE_REUSED_HISTORICAL_ONLY. Реальный предыдущий Windows/EET BCS 10550 bytes, SHA256 `10426a2262e79553e861d464bdcf89d82a0fc91498dfb02c430c9b1fb02ef929`. В этом запуске компиляция не повторялась.
- `processes`: PASS_NO_KNOWN_GAME_PROCESS; `gameAfter`: PASS_WATCHED_GAME_FILES_UNCHANGED (7 файлов). **Это не проверка всего дерева игры.**
- `installPerformed=false`, `gameFilesChanged=false`, `localsWritten=0`, `ordersSent=0`, `dispatchAuthorized=false`, `weaponSwitchAuthorized=false`, `gameplayLiveVerified=false`.
- `hasSafetyHold=false` означает, что защитные тесты не заблокированы; **это НЕ значит что готово LIVE**. Именно `runtimeProof.status=HOLD_LIVE_ORIGIN_AND_ALT_STATS_NOT_PROVEN`.

## Шесть сохраняющихся блокеров (не скрывать)

1. ALTERNATE_QUICKSLOT_EFFECTIVE_APR_THAC0_DAMAGE_UNDER_CURRENT_BUFFS.
2. ENGINE_LAUNCHER_AMMO_PAIR_AND_TARGET_EFFECTS.
3. MANUAL_ORDER_VS_EPS_VS_AI_ORIGIN_PROVEN.
4. NONINTERRUPT_ACTION_RECOVERY_AND_QUEUE_BOUNDARY_PROVEN.
5. FRESH_TARGET_AND_EQUIPMENT_IDENTITY_PROVEN.
6. AUTHENTICATED_PRODUCER_AND_INSTALL_ROLLBACK.

## Аудит существующих исходников, без запуска игры и установки

**EEex v1.1.7 (не новый публичный v1.3):** `Bubb13/EEex` `EEex/copy/EEex_scripts/EEex_Action.lua`, git blob `e7543274ed066b5abe3c58262105212f208d1595`: `EEex_Action_AddSpriteStartedActionListener` существует; `m_curAction` читается в движковом callback, однако нет показанного им признака происхождения команды «игрок / EPS / BGXAI». `EEex/copy/EEex_scripts/EEex_Sprite.lua`, git blob `b2d8d930c47785737bd30dad08e9f35a9d859578`: `EEex_Sprite_GetActiveStats` (current selected actor) есть; не доказан безопасный одновременный APR для *невыбранного* оружия. Эти факты **не дают разрешения** изменять BCS или действие.

**Публичные источники EPS** `SarahG-579462/Enhanced-Powergaming-Scripts` branch `main` (это НЕ подтверждённый SHA установленного EPS 18.4!):
- `enhanced-powergaming-scripts/baf/normal/mocore.baf` blob `0f5528cea5c8396a7244a1f39fd04144eab64dd8`: семь `ActionListEmpty()`.
- `enhanced-powergaming-scripts/lib/core_base.tph` blob `5aa3fa37155cd61154bce24e347d614157f6cb90`: 54 `ActionListEmpty()`, 435 вхождений `MO_SpellCast` (включая чтения/записи таймера).
- Они показывают, что EPS сам управляет очередью/планированием; нельзя выводить «окно для BGXAI» только из `ActionListEmpty()`, `m_actionID` или `m_curScriptNum`. Сначала сравнить ***реально установленный*** EPS 18.4/35.21, не переиспользовать без доказательств `MO_SpellCast` как универсальный origin-token.

## Решение для следующего изменения

Не запускать прежние 165/R27, R28, 167 или 168 повторно без нового предмета проверки. Следующая полезная версия **той же программы/единого updater**, а не второй CMD, должна:
- READ-ONLY за один запуск сверить SHA установленного EPS и EEex source, найти реально используемые action-priority predicates, определить какие данные доступны в установленном EEex; при неизвестных деталях выдавать HOLD, а не true.
- Реальные APR/ALT slot и provenance безопасно измерять **только специально разработанным passive observer** после независимого source audit; не менять выбор оружия во время заклинаний, лечения или атаки.
- Только после честного подтверждения всех шести условий, отдельного typed согласия на установку, полного внешнего backup и WeiDU-last отката рассматривать **один** LIVE A/B.
- Не обещать фоновый запуск Windows: ChatGPT не имеет непрерывного доступа к компьютеру пользователя. Перепроверка/сбор данные выполняется программой при его запуске.

**CODE/CI и SOURCE audit — да; новая V3 DEPLOY/LIVE — нет.**
