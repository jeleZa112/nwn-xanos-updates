# BG_EET_RU — V108 second uploaded ZIP is byte-identical (2026-11-23)

The user uploaded a new filename `SEND_TO_CHATGPT_BG_EET_RU(20261123-121934).zip`, after previously sending `SEND_TO_CHATGPT_BG_EET_RU(20261123-113746).zip`.

Offline comparison of **both exact uploaded byte streams** confirms:
- Both **806857 bytes**, SHA256 `5db3cf19d88f5fa9a213565cb202dc5722da81021274da9bf5056c3c98587be0`, **byte-for-byte identical**.
- ZIP integrity **125 unique entries, CRC PASS**.
- V108 report still `mode=capture`, `status=V108_NATIVE_RESREF_CALLBACK_EVENTS_CAPTURED`, `event_lines=2`, and the original two lines both `weapon_resref=SW1H04`, `launcher_resref=NOT_CITEM_USERDATA`.
- No **new** ranged bow or projectile identification. This is a stale/repeated **report content**, but it **does not prove** whether the user performed an additional game run or hit an enemy; the file may not have been regenerated, may have been copied from the wrong directory, or a capture attempt may have failed before report replacement.

**Next action:** Don't reinstall V108 or have user repeat combat blindly. Ask for *the most recent updater command window's final output*, especially `V108:` status and whether capture was attempted; verify the exact canonical report path `C:\Users\Drevo\Documents\BG_EET_RU\SEND_TO_CHATGPT_BG_EET_RU.zip` and its timestamp. One canonical updater and one canonical ZIP; all prior V106/V107 live tests remain valid; no game changes in this audit.

Private comparison audit stored locally/Library as `BG_EET_RU/V108_DUPLICATE_ZIP_AUDIT_20261123.json`. Do not publish user ZIP or console to GitHub.
