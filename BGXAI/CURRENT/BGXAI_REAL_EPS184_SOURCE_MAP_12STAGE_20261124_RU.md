# BGXAI installed EPS/EEex audit, source-specific EPS arbitration map (24 Nov 2026)

## Real user evidence; no re-runs required
Received `BGXAI_AUTO_BATCH_RO_20261124T142906654787Z.json`: `SAFE_READONLY_BATCH_COMPLETE_GAMEPLAY_HOLD`, 11 stages, 59 Python unit cases (4 skipped), 512 synthetic conservative-action cases, 108 BAF source guards, 7 watched game files unchanged. No installs, no LOCALS writes, no game actions; source-only, gameplay not verified.

**Five real installed sources identified:**
- `enhanced-powergaming-scripts/lib/core_base.tph` 1,306,562 bytes, SHA256 `1da3e226645367aa4cc8ba3ff8c1f14627df5ccd3c3e0852941c256b5301e776`, 212 literal `ActionListEmpty()`, 1116 literal `MO_SpellCast`.
- `enhanced-powergaming-scripts/baf/normal/mocore.baf` 198,436 bytes, SHA256 `775a58cb980f72141f3b3aaaffd6a9548710385bf1765a9dc7b115c2d538ef4c`, 13 queue, 13 timer.
- `enhanced-powergaming-scripts/baf/accelerated/mocore.baf` 206,807 bytes, SHA256 `983004031967b6be6bb9c2aeeb2af91360f3b61795db409a5bbc5f20e6e4965c`, 12 queue, 11 timer.
- `EEex/copy/EEex_scripts/EEex_Action.lua` 12,441 bytes, SHA256 `7a64c157418f503e914c4fb3083c97f017e70c9787024fcac779f162c86f20da`. **EXACT match** with the existing R27 guard baseline `BGXAI_R27_GUARDED.py`; one listener registration declaration.
- `EEex/copy/EEex_scripts/EEex_Sprite.lua` 61,992 bytes, SHA256 `4813ae620f0b472903848018d66488805db7ba2012e065019f4ea5f2a6afab28`; three `EEex_Sprite_GetActiveStats` mentions.
- `EEex/EEex_scripts/` alternative paths absent. Does not mean hook is missing; source is in `copy` directory and R27 was previously observed live.
Installed source bytes differ from earlier public EPS main branch, therefore do NOT substitute publicly fetched EPS source for installed 18.4. The 11-stage report does not prove EPS version 18.4 from source alone nor actual current script selection.

## New completed CODE, no game deployment

Within the **same menu 168, same 5-file SHA-pinned manifest**, added one **12th** step `epsSourcePriorityMap` to `BGXAI_AUTO_BATCH_RO_V1.py`. It analyzes the very sources that the 11th inventory located, verifies they have the same SHA during scanning, and statically extracts conservative literal `IF/THEN/END` BAF blocks. For each of three installed EPS BAF/TPH files it counts:
- Blocks with `ActionListEmpty()` trigger and `MO_SpellCast` trigger (alone and jointly)
- Blocks containing spell/item and attack action signatures, including potential source-level orders lacking explicit queue guard
- Unexpected reuse of `BGXW3_REQ` namespace as a strict hold
- Source identity and known EEex action hook SHA match against actual R27 installer.
Outputs ONLY compact counts and relative names, NO source contents, and never evaluates BAF/WeiDU macros or claims selected EPS profile is known.

**Protective limits:** bounded 3MB per source, SHA recheck across stages, symlink/junction denial, no game mutations, `manualVsEpsOriginVerified=false`, `alternativeQuickslotEffectiveAprVerified=false`, `actionBoundaryVerified=false`, `dispatchAuthorized=false`, `ordersSent=0`. Literal source patterns are NOT verified compiled order or runtime order provenance. Native V3 BAF still uninstalled.

**New release pinned commit:** `ad183bfd8c0814273cde149bc51ecd77afe4344b`, exactly unchanged single backend `BGXAI_SYNC.ps1` 79,935 / 80,000 bytes. New 168 module source SHA256 `1c95d3c191351621e7d9d83ea0bb2582e095e188e2427c77263ca4007bab14f0`, test SHA256 `8b5aad25ac0267852eff87942e02e02e4c64ac8ead8b330fe9412121fd831a46`; manifest updated with same 5 filenames.

**Independent CI SUCCESS both Windows and Ubuntu:** https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45416254693 ; **45 batch tests + 21 native tests**, 12-stage end-to-end PASS, PS5.1 syntax PASS. Linux also **439/439 x three Lua runtimes**. Local 45+21 and end-to-end passed. Do not describe these as gameplay PASS.

## NEXT actual gameplay work

The six engine gates remain HOLD: alternate-slot *effective* APR/THAC0/damage with current buffs; verified currently-selected launcher+ammo+target effects; authenticated player/EPS/AI origin; safe noninterrupt recovery and queue boundary; stable target/equipment; authenticated request producer+WeiDU-last rollback+typed deployment. Source-only static priority map cannot independently settle those. The next *substantive* implementation is a typed-consent passive runtime observer that records verified engine target+action queue evidence without orders, plus an EPS-aware arbitration producer after evidence is available. Do not create another command/updater: use same menu 168 and one JSON. Do not request repeating R27/R28/167. It is reasonable to run updated 168 ONCE later to capture **new** installed-source logic map, not to replay old diagnostics.

**CODE+CI pass; newly authorized weapon switching 0; live V3 gameplay unproven.**
