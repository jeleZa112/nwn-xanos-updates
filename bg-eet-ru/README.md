# BG EET RU — current entry point

**Active project:** Russian **text** localization of the installed Baldur's Gate EET game, including the combat log. BG Voice RU and BGXAI are separate projects. This file is public project metadata; do not publish private user ZIPs, game binaries, logs, or saves.

## Active one-file updater (as of 2026-11-24)

- Branch: `bg-eet-ai`
- Authoritative active release: [`onefile/release.json`](onefile/release.json). Always inspect this manifest and the current user ZIP before trusting an older handoff/checkpoint.
- Only canonical user-side updater: `BG_EET_RU_UPDATE.cmd` in the local `Documents/BG_EET_RU` directory. Published source: [`onefile/BG_EET_RU_UPDATE.cmd`](onefile/BG_EET_RU_UPDATE.cmd).
- Current published version: **V120**, read-only comprehensive combat-log audit. Default run writes results to the **same existing external ZIP**, `SEND_TO_CHATGPT_BG_EET_RU.zip`, entry `58_FULL_SPECTRUM_STATIC_AUDIT.json`; it does **not** install a new hook or modify game files.
- Confirmed offline CI on 2026-11-24: [one-file updater selftest PASS](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45314789280); [V108/V109 compatibility PASS](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45314938483).
- **Windows V120 audit remains unverified in this repository.** GitHub/CI PASS is not Windows or gameplay PASS. The prior V116 message-dispatch symbol match is static only.

## Latest substantiated engine findings

- V108/V111: weapon/launcher identifiers and names observed for particular *damage* events. A damage-only callback does not establish miss events.
- V112: the UI reads `combatLog[rowNumber]`; no immutable ID shared with an individual attack roll has been established.
- V115/V116: attack-roll text creation in installed `Baldur.exe` leads to an `AddMessage` call at RVA `0x204C60`, confirmed by the installed EEex loader signature. This **does not prove** a particular `combatLog` row, weapon, ammunition, or miss.
- V120: further static investigation packaged into one SHA-pinned read-only audit. Do not attach a weapon name to a journal line on the basis of the last event, timestamp, actor name or assumed event order.

**Next actual evidence needed:** one normal Windows run of the existing updater (game and InfinityLoader closed), then inspect `58_FULL_SPECTRUM_STATIC_AUDIT.json` from the existing report ZIP. No combat test is required for this read-only pass. A future game-changing installation needs separate explicit authorization, exact SHA, backup and verified rollback.

## Historical channel (not the active onefile version)

`channel.json` and its old **v18** metadata belong to the earlier text-update channel. They must not be used as the status of the current V120 one-file updater. Earlier project files remain historical evidence rather than the active release manifest.
