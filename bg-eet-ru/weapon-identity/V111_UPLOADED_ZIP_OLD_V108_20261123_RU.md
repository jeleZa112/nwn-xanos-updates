# BG_EET_RU V111 — 2026-11-23 ZIP upload was previous V108, no new V111 report

The user's uploaded `SEND_TO_CHATGPT_BG_EET_RU(20261123-141847).zip` was inspected offline. **806843 bytes**, SHA256 `404e301e3765f0c4c5a84c0b5562dc59bddd6a51b4122dca3d8d759c57c6a8f0`, **125 unique entries, CRC PASS**. It is **byte-for-byte identical** to their previous 2026-11-23 V108 ranged-combat ZIP.

`54_V108_NATIVE_ITEM_RESREF_PILOT.json` still says `updater_version=110`, `mode=capture`, `status=V108_NATIVE_RESREF_CALLBACK_EVENTS_CAPTURED`, `event_lines=2`. **No `55_V111_ACTUAL_ITM_TLK_NAMES_READONLY.json`**.

Current GitHub release remains **V111** `ddfafd1d84c27277682916b2e7080e559351e54551d742e757b77cef2ce06fb2`, onefile source includes `--v111-item-audit` and two automatic default-call paths. SOURCE CI PASS, but Windows update/capture is **not established** by uploaded ZIP. Do NOT conclude the user didn't run updater: they may have uploaded an older copied file or an updater could have stopped before exporting ZIP. Distinguish these by exact CMD console output.

**Next action (no game needed):** Close game and InfinityLoader; invoke same `C:\Users\Drevo\Documents\BG_EET_RU\BG_EET_RU_UPDATE.cmd --v111-item-audit`. Confirm console reports `ОБНОВЛЕНО до v111` or `АКТУАЛЬНАЯ ВЕРСИЯ v111` and `V111: ...`. Then upload the **current canonical** `C:\Users\Drevo\Documents\BG_EET_RU\SEND_TO_CHATGPT_BG_EET_RU.zip`. If any STOP, request exact text and do not bypass SHA. No previous V108 combat tests repeated, no new game files modified.

Private JSON audit in Library `/BG_EET_RU/CURRENT/BG_EET_RU_V111_ARCHIVE_STALE_AUDIT_20261123.json`. No private ZIP published.
