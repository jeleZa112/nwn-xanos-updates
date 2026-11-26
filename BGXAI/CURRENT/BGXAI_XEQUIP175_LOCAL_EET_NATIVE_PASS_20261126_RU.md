# BGXAI — VERIFIED FIRST USER EET NATIVE READ-ONLY COMPILE, MENU175 — 2026-11-26

**Authoritative latest checkpoint; old 'user must now run 175' text is obsolete. DO NOT REQUEST ANOTHER MENU175 RUN.**

## User-provided actual EET evidence
Source file uploaded in conversation: `BGXAI_XEQUIP175_RO_20261126T141634522316.json`. The original user report was parsed directly, not inferred from filename. Exact report SHA256: `e3e6be76c6d92596ef5207c96aa8d3e2118327b9572632e89cd1cadde375a715` (hash of uploaded file, not copied into repository because local Windows paths appear in compiler tail). Automated contract checks PASS.

- `schema=BGXAI_XEQUIP_ONEFILE_175_READONLY_V1`
- `status=NATIVE_INERT_WEIDU_COMPILE_PASS_TEMP_ONLY`; `nativePreflightRequested=true`.
- `innerReport.status=NATIVE_WEIDU_COMPILED_TEMP_ONLY`, `nativeSymbolsAcceptedByCompiler=true`.
- User's exact pinned WeiDU sha256 `0d17e26e3f3ef5b36796eb0ee8ae73cb851d8b62c9702c2e224da2945caafb75`; compiler identifies **WeiDU 25100 / BG2 scripting style**.
- Synthetic source BAF: SHA256 `c368f2f14e0e2791ac2e876719d4f24d2b450d51662909416bbd094f73493457`, size 675 bytes, one trigger/action block, 2 actions; emitted BCS SHA256 `c1dd6879cadc9817d56d65c96a6bb06fb790095cd258abbf1774958685054670`, size **1030 bytes**.
- `watchedFilesChanged=false`, `temporaryOutputRemoved=true`, `ordersSent=0`, `newGameFilesWrittenByThisRunner=0`, `installPerformed=false`, `inertFalseGuard=true`, `nativeActionActuallyExecuted=false`.
- **Unproven by this test**: `wholeGameTreeChecked=false`, `engineBehaviorVerified=false`, `gameplayLiveVerified=false`, `manualEpsOriginVerified=false`, `itemTransferSemanticsVerified=false`, `safeActionBoundaryVerified=false`, `itemInstanceIdentityVerified=false`.
- `sourcePins` verified exactly four assets, anchored in immutable commit (see onefile pinned release documentation). No game overrides, scripts or save files changed in this test.

## Updated conclusion (CODE/TEST/DEPLOY/LIVE)
| Workstream | CODE | TEST | DEPLOY | LIVE |
|---|---|---|---|---|
| Onefile175 RO BAF compile probe | shipped | **real installed EET WeiDU 25100 PASS** | channel/menu yes, game scripts no | inert compiler only |
| Backpack 16-slot observer + scorer V3/V4/V5 and conservation model | available | source CI PASS | NOT INSTALLED for new observer/executor | NO |
| Actual `XEquipItem` transfer from backpack during idle | *not yet implemented as active guarded pilot* | NOT DONE | NO | NO |
| Combat autopick with APR/proficiency/poison/target immunity | source-only decision layers | partial offline | NO | NO |

## Official mechanics and false inference to avoid
IESDP BGEE `XEquipItem` (action 385) puts an item into requested slot, and `CheckItemSlot` / `HasItemSlot` can test exact observed source and empty destination. This does not guarantee unique-instance selection, item flags/charge preservation or uninterrupted engine action. Distinguish `EquipItemEx`: **it never moves item in inventory**, so it cannot replace `XEquipItem`. Avoid `FillSlot`, can destroy occupied target. References:
- https://iesdp.bgforge.net/scripting/actions/bgeeactions
- https://burner1024.github.io/iesdp/scripting/triggers/bgeetriggers.htm
- https://burner1024.github.io/iesdp/files/ids/bgee/slots.htm

## Next exact engineering milestone (NO user steps now)
**Build one-shot disposable-save native live proof of item movement, not another inert compiler test.** Reuse R29 typed guarded WeiDU installer infrastructure (external backups, exact live BCS SHA, last-only rollback) and V4/CONSERVATION_V1 postcondition. Must first get **genuine observed item resref in exactly one backpack slot 18..33**, a verified EMPTY class-permitted quickweapon slot 35..38 on a disposable save, stable actor and clean manual/EPS queue, no current battle or spellcast. Do not invent the item from sample `HAMM01`. Prioritize pilot outside combat; only after item conservation in a real game should automating combat APR/effects be attempted. No game installation, interactive game action, rollback, console spawn or second updater until next separate explicit typed user consent. If real item evidence cannot be obtained automatically, ask for **one focused inventory screenshot** only when needed (user already finished 175; never repeat it).

**Project rules**: one `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd` only, do not break V6/R29/R37/EPS/BG_EET_RU/BG Voice RU, no extra CMD, no losing pending attacks, guard all live changes with SHA/backups/WeiDU last-only. User asked that notification be sent only when his intervention is genuinely required.
