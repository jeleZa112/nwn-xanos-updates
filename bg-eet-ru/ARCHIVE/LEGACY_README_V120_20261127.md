> **ТЕКУЩАЯ ТОЧКА ДЛЯ НОВОГО ЧАТА:** [00_RESUME_CURRENT.md](CURRENT/00_RESUME_CURRENT.md). Опубликованная версия берётся из [onefile/release.json](onefile/release.json), а локальная установка — из последнего пользовательского отчёта. На 27.11.2026 manifest = **V160**, источник/CI PASS, установка V160 и LIVE не подтверждены. Старый текст о V120 ниже — история. [Обязательное правило восстановления](../GLOBAL_PROJECT_RULES/GLOBAL_CROSS_CHAT_RESUME_V1_RU.md).

> **НОВОЕ ГЛОБАЛЬНОЕ ПРАВИЛО 27.11.2026:** [ОБЯЗАТЕЛЬНЫЙ PRE-WORK GATE — запрет на повтор уже выполненных задач](CURRENT/00_PRIOR_WORK_GATE_READ_FIRST.md). Любая новая реализация начинается с проверки уже сделанного, доказательств и недостающей дельты. Не повторять подтверждённые тесты.

# BG EET RU — current entry point

**Active project:** Russian **text** localization of the installed Baldur's Gate EET game, including the combat log. BG Voice RU and BGXAI are separate projects. This file is public project metadata; do not publish private user ZIPs, game binaries, logs, or saves.

## Historical one-file updater reference (snapshot from 2026-11-24)

- Branch: `bg-eet-ai`
- Authoritative active release: [`onefile/release.json`](onefile/release.json). Always inspect this manifest and the current user ZIP before trusting an older handoff/checkpoint.
- Only canonical user-side updater: `BG_EET_RU_UPDATE.cmd` in the local `Documents/BG_EET_RU` directory. Published source: [`onefile/BG_EET_RU_UPDATE.cmd`](onefile/BG_EET_RU_UPDATE.cmd).
- Historic documented version: **V120**, **NOT CURRENT**; check live `onefile/release.json` (V160 when verified on 2026-11-27), read-only comprehensive combat-log audit. Default run writes results to the **same existing external ZIP**, `SEND_TO_CHATGPT_BG_EET_RU.zip`, entry `58_FULL_SPECTRUM_STATIC_AUDIT.json`; it does **not** install a new hook or modify game files.
- Confirmed offline CI on 2026-11-24: [one-file updater selftest PASS](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45314789280); [V108/V109 compatibility PASS](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45314938483).
- **Windows V120 audit remains unverified in this repository.** GitHub/CI PASS is not Windows or gameplay PASS. The prior V116 message-dispatch symbol match is static only.

## Latest substantiated engine findings

- V108/V111: weapon/launcher identifiers and names observed for particular *damage* events. A damage-only callback does not establish miss events.
- V112: the UI reads `combatLog[rowNumber]`; no immutable ID shared with an individual attack roll has been established.
- V115/V116: attack-roll text creation in installed `Baldur.exe` leads to an `AddMessage` call at RVA `0x204C60`, confirmed by the installed EEex loader signature. This **does not prove** a particular `combatLog` row, weapon, ammunition, or miss.
- V120: further static investigation packaged into one SHA-pinned read-only audit. Do not attach a weapon name to a journal line on the basis of the last event, timestamp, actor name or assumed event order.

**Historical next evidence for V120 (already superseded):** one normal Windows run of the existing updater (game and InfinityLoader closed), then inspect `58_FULL_SPECTRUM_STATIC_AUDIT.json` from the existing report ZIP. No combat test is required for this read-only pass. A future game-changing installation needs separate explicit authorization, exact SHA, backup and verified rollback.

## Historical channel (not the active onefile version)

`channel.json` and its old **v18** metadata belong to the earlier text-update channel. They must not be used as the status of the current V120 one-file updater. Earlier project files remain historical evidence rather than the active release manifest.

## Independent analysis of actual Windows V120 ZIP — 2026-11-24

A user-provided private archive was inspected locally (129 entries, ZIP CRC PASS; no game writes). Its `58_FULL_SPECTRUM_STATIC_AUDIT.json` reports `STATIC_EVIDENCE_COLLECTED_RUNTIME_JOIN_HOLD`, zero errors, unchanged EXE baseline. **This is a real Windows STATIC PASS, not gameplay/journal row identity PASS.**

Independent local verification rehashed **30 bounded function fragments** from that report and correlated them with the archived V68 attack-function bytes:

- At attack RVA `0x39E7D9`, the message constructor stores vtable RVA `0x597CD0`; it copies the formatted text into the message's offset `+0x18`.
- The same attack function calls `CMessageHandler::AddMessage` at RVA `0x204C60`; within that method, virtual slot `+0x8` classifies/routes messages. The 5 earlier dispatch calls remain validated.
- In the captured message vtable, **slot 6** points to RVA `0x2110B0` (message-processing method candidate). It passes the message's name `+0x10`, text `+0x18`, and color/parameters `+0x20` to another function via an independently verified call at RVA `0x21113B` targeting **`0x2EEFE0`**.
- **The body of `0x2EEFE0` was not in the V120 evidence.** The queue-to-slot6 delivery semantics and append into `combatLog[rowNumber]` have not been proven; there is no immutable attack-to-journal-row token or verified weapon identity for misses. No UI weapon injection is authorized.

The next meaningful SOURCE ONLY step is to inspect `0x2EEFE0` and the corresponding row-append semantics using verified existing evidence; do not re-run V92–V120 or infer identity from timestamps/actor IDs. No new runtime hook or game change was installed by this independent audit. Preserve this conclusion when starting a new chat.
