## 2026-11-13 — USER REAL WINDOWS MENU 83 PASS; 066S NOW READY FOR SEPARATE USER-AUTHORIZED INSTALL 84

- User's latest live output: BGXAI 066S menu 83 completed successfully. All 29 immutable SHA-pinned sources VERIFIED. Real installed-EET baseline: `INSTALLED_064_VERIFIED`; last WeiDU `~BGX64\\SETUP-BGX64.TP2~ #0 #0`; BCS SHA256 `db0fcba4678b00defa2ed7887b57c0d4207effc064891aeb9a0d7dcc1a1a6b0b`; Lua SHA256 `bfee5278b5b69b1fb4a02e3fea321082b0238407789df83ec6bd2f78d7e19f4b`.
- Real WeiDU compilation using installed user's EET IDS: compiled fragment BCS SHA256 `907425a828363fb6d748d3dda40269ea28cf642c66b3f3a815a61c75305a5de3`; merged candidate BCS SHA256 `fb435d82e6c3e0ebea1d6a9532753921bd5411d70ac0677dc1fd8ec483380476`; Lua candidate SHA256 `50640902ec4c25a2c85e5088d7231678b54445a847b41743c476974236d1d70f`.
- Patch output: `BCS_PATCH_VERIFIED`, old_blocks=1077, new_blocks=11, total_blocks=1088, `existing_bcs_blocks_byte_exact=true`, insertion_before_old_block=1052 (1-based). `authorized_to_install=false`, `BGXAI066S PRECHECK PASS. Existing 064 remains installed.` **No installation took place**.
- Final exact-source GitHub Actions run **43281782034** passed **Windows and Linux**, updater Windows parser+SHA run **43281781501 SUCCESS**. Active pin `BGXAI/fox_new/BOOTSTRAP_PIN.json` points to immutable source commit `cdcadd5266af044e0c4d73d0b63812d55cdf45a9`, unchanged Windows-verified `BGXAI/BGXAI_SYNC.ps1` SHA256 `8c1f5c4030098e014ce0f3ca108b7edce153a4868d2f9d8ea8458dc1dc0b7ab1`, 66909 bytes.
- Immediate boundary: Only user can authorize install on own Windows. NEXT: close Baldur and InfinityLoader, run existing `BGXAI_UPDATE.cmd`, select **84**, type exact `INSTALL_BGXAI_066S` ONLY if explicitly authorizing game modifications. Installer revalidates live 064, stages exact Lua+BCS, writes external SHA-verified backup, WeiDU installs. On success, run **85** read-only status, return both outputs/backup path; then single live game test for actual mage/cleric response. If STOP, DO NOT blindly repeat, and do not run 86 without examining result. No need to repeat menu 83 or earlier checks. Rollback menu 86 requires exact `ROLLBACK_BGXAI_066S` with strict last-WeiDU verified backup.
- This is only a guarded **early prototype** with Cure Light Wounds and Shield conditions, not full autonomous SCS/Insane AI. Do not claim spell performance proven until live test.

# BGXAI 066S — устранено ошибочное ожидание 1065 блоков в пункте 83

Дата: 13.11.2026. Проект: BGXAI EET Foxx / EPS 18.4 / EEex / SCS. Состояние рабочей игры: **подтверждённая BGXAI 064, не изменена**.

## Реальная ошибка (скриншот пользователя, опция 83)

```
BGXAI 066S SOURCE SYNC DONE. Live scripts and WeiDU unchanged.
BGXAI 066S real EET IDS + BCS preflight: READ ONLY, no WeiDU installation.
BGXAI066S STOP: BCS_BLOCK_COUNT_1077_EXPECTED_1065
BGXAI STOP: BGXAI066S REAL EET IDS preflight STOP 2
```

Установщик правильно остановился **до установки**, без изменения игры. Причина была в нашем ошибочном макете: он исходил из 056 (8 блоков приёмника после позиции 1031) и 1065 всего. Но в действительности 061 заменила 14 блоков 060 на 20 новых и привела к 1077 блокам. Установленная 064 — Lua-only на базе 061, её BCS сохранился без изменений, что подтверждено точным SHA256.

## Внесённое исправление

- Файл `BGXAI66S_BCS_PATCH.py`: `PIN_064_BLOCKS=1077`, `OLD_RECEIVER_START=1031`, `OLD_RECEIVER_BLOCKS=20`, `SPLICE_AT=1051`; ожидаемо 1077 + 11 = **1088** BCS блоков.
- Проверяет точный SHA256 текущего BCS 064 `db0fcba4678b00defa2ed7887b57c0d4207effc064891aeb9a0d7dcc1a1a6b0b`, структуру 20 правил 061 по action ID, ключ `BGX52_REQ_SLOT` и маркеры `BGX61_LAST_BRANCH`, полную побайтную сохранность 1077 старых BCS-блоков и доказательство обратного получения 064 BCS после удаления 11 новых.
- `test_066s_installer_mock.py`: синтетическая 1077-блочная модель текущей 061/064, контроль точной вставки и восстановления, 3 дополнительные отрицательные регрессионные проверки.
- Обновлены `README_RELEASE_RU.md`, SHA/size для 29 source files в `manifest.json` и `manifest_updater.json`, проверены одноимённые реальные GitHub sources.
- **42/42 локальных тестов PASS** (18 native Lua EEex-мок + 24 BCS/installer/WeiDU-мок) и `verify_release.py` **29/29 PASS**, `build_066s.py` воспроизвёл Lua SHA `50640902ec4c25a2c85e5088d7231678b54445a847b41743c476974236d1d70f`.
- GitHub CI run `43281218691` **SUCCESS Linux + Windows** на основной починке 1077 (предыдущая строгая проверка компилированного маркера). Финальная мини-правка проверки ключа по подтверждённому коду 061: `b'BGX52_REQ_SLOT'` вместо необоснованно строгого `b'LOCALSBGX52_REQ_SLOT'`, локальные 42 теста снова PASS. CI полного последнего коммита `43281782034`/`43281781501` — статус проверять перед окончательной рекомендацией.
- `BGXAI/fox_new/BOOTSTRAP_PIN.json` repo commit `970bd9c3040bc70d7722cddfd381d63232893ef4` теперь указывает на immutable исправленный SOURCE commit **`cdcadd5266af044e0c4d73d0b63812d55cdf45a9`**. `BGXAI/BGXAI_SYNC.ps1` **байт-в-байт тот же** из успешно проверенной Windows-версии, SHA256 `8c1f5c4030098e014ce0f3ca108b7edce153a4868d2f9d8ea8458dc1dc0b7ab1`, размер 66909 байт. 82–86 неизменны, опасная старая 079 заблокирована.
- Source-only release zip исправлен, SHA256 **`624ec946a9fa83bd24cd6a1d52483ff027a4c8e2dc6ece714bb4ec1a561bb731`** (CRC PASS) и сохранён в Library `/BALDURS_GATE_EET_AI/BUILD/BGXAI_066S_GUARDED_INSTALLER_SOURCE_ONLY/`.

## Следующая граница и задача пользователя

**Только после положительного CI** — повторить пункт **83** из прежнего `BGXAI_UPDATE.cmd` с закрытыми Baldur и InfinityLoader. Это первая полезная проверка реальной EET после устранения дефекта, не повторять 78 и не искать старые архивы. В результате ожидаются `old_blocks=1077`, `new_blocks=11`, `total_blocks=1088` и отсутствие записи в game `authorized_to_install=false`. Настоящая компиляция IDS и точный merged SHA могут быть подтверждены только на ПК пользователя. Пункт 84 (реальная установка) требует собственного явного подтверждения пользователя и verified external backup; 85 статус; 86 откат. **Никогда не устанавливать автоматически.**
