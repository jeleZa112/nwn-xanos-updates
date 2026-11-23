# BG_EET_RU — V108 first submitted ZIP, installation only (2026-11-23)

This checkpoint records the evidence **without publishing the user ZIP or any private console data**.

- Exact user upload: `SEND_TO_CHATGPT_BG_EET_RU(20261123-113118).zip`.
- SHA256: `3c2edd1284c3a2e02c6700eecaef06f0ef6c48adfd667315cf3b76b8f5c9aa39`.
- ZIP integrity: 125 unique entries, CRC PASS.
- `54_V108_NATIVE_ITEM_RESREF_PILOT.json`: version 110, **`mode=install`**, `V108_INSTALLED_NATIVE_CAPTURE_REQUIRED`, game writes reported during installation = 1; `errors=[]`. V108 candidate SHA256 `7e1b514a00085997ec15232fe0084f9cbd739cf9cc4526b81e7fb15e98161eb4`.
- There is **no `console_evidence`** in the V108 entry; `resref_verified=false`, `ammo_verified=false`, `misses_verified=false`, `journal_row_verified=false`.
- V107 static file still reports V106 baseline SHA; it is historical and does not fingerprint post-install V108 candidate. Do not infer V108 file was reverted from this.
- Old V106 entry preserves exactly 2 historical event observations but no weapon identities.
- This proves **install output**, not a new live V108 combat capture. Do not describe V108 game runtime behavior as PASS or FAIL.

## Correct next action

Use the **same canonical** `C:\Users\Drevo\Documents\BG_EET_RU\BG_EET_RU_UPDATE.cmd --capture-v108-native-read` with game and loader initially closed. This launches InfinityLoader and records bounded console output. Make 1–2 sword attacks and 1–2 bow shots, then exit game and verify that same canonical ZIP entry `54_` updates to `mode=capture`, status `V108_NATIVE_RESREF_CALLBACK_EVENTS_CAPTURED` or an informative HOLD. Do not repeat V106 or reinstall V108. If the user already ran `--capture` but entry remained install, request *the command window's final output* and diagnose rather than replay blindly. In event of native crash, do not retry without reviewing risk; use existing guarded rollback with typed approval if needed.

A detailed, user ZIP-derived offline report is stored privately in Library `/BG_EET_RU/CURRENT/BG_EET_RU_V108_ARCHIVE_AUDIT_20261123.json`.

No game files were accessed or modified during this offline review. Do not touch BGXAI, BG Voice RU, V101 FULL/BRIEF, TLK or saves.
