# BG_EET_RU V108 — LIVE bow/arrow CItem RESREF pair — 2026-11-23

**Source:** user uploaded `SEND_TO_CHATGPT_BG_EET_RU(20261123-132905).zip`. The raw user archive and logs are not published.

The ZIP was 806843 bytes, SHA256 `404e301e3765f0c4c5a84c0b5562dc59bddd6a51b4122dca3d8d759c57c6a8f0`, 125 unique entries, all CRC PASS. `54_V108_NATIVE_ITEM_RESREF_PILOT.json` records `updater_version=110`, `mode=capture`, `V108_NATIVE_RESREF_CALLBACK_EVENTS_CAPTURED`, `v106_capture_process_status=V106_CAPTURE_COMMAND_COMPLETE`, `errors=[]`, `game_files_written=0`, `event_lines=2`.

Two **new** logged V108 events both returned `weapon_resref=AROW01` and `launcher_resref=BOW05`. Prior different ZIP at 11:37:46 had two `weapon_resref=SW1H04`, `launcher_resref=NOT_CITEM_USERDATA`. Therefore in an actual ranged damage callback, EEex item CItem RESREF reads distinguish **ammo** from **launcher**. Public BG catalogs map `AROW01` to normal Arrow and `BOW05` to Short Bow, while `SW1H04` is standard Long Sword; names in the user's modded EET must still be verified from local ITM/TLK, not assumed from public names.

**Verified:** actual V108 native item RESREF pair for ranged event, no reported runtime errors, correct ZIP and distinct new capture. **Not verified:** local item type or strref; all ranged weapon types; misses; attribution to a specific combat journal line; actual UI result. The V108 report intentionally retains `resref_verified=false`, `ammo_verified=false`, `misses_verified=false`, `journal_row_verified=false`. These flags are conservative schema fields, not a contradiction of the printed pair.

**Next safe action:** no repeat bow/melee gameplay test. Research/build SOURCE ONLY READ ONLY local ITEM lookup `override/ITM` and `chitin.key+BIF` respecting override priority, with TLK strref -> actual displayed Russian name and safe HOLD for unsupported resource formats. Separately research a supported attack/miss event mechanism and an unambiguous journal-row correlation; do not infer these from the damage listener. Avoid new native crash-risk experiment until justified. Leave V108 installed as-is and preserve V101 FULL/BRIEF, game, BGXAI and BG Voice RU.

Private detailed comparison kept in Library `/BG_EET_RU/CURRENT/BG_EET_RU_V108_LIVE_RANGED_PAIR_AUDIT_20261123.json`. One user-updater `BG_EET_RU_UPDATE.cmd`, one ZIP report.
