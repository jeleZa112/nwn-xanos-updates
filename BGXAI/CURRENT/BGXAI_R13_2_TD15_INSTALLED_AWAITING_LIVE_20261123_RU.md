# BGXAI R13.2 / TD15 — user-confirmed WeiDU install, awaiting in-game test

Date: 2026-11-23 UTC. User executed the single updater `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`, menu **163 -> 3**, typed `INSTALL_BGXAI_R13_HOLD_DIAGNOSTIC` and provided full output.

Verified by user's installer proof:
- `status=BGXTD15_INSTALLED_AWAITING_LIVE_TEST`
- `schema=BGXAI_R13_HOLD_DIAG_INSTALL_PROOF_V1`
- `installedUtc=2026-11-23T06:43:29.490462+00:00`
- `sourceSha256=040a5df62c84363fd0d566c9509636efba7721439afcc90c72758da094e7f5f8`
- `previousSourceSha256=c0fb928001d5fb042a935302270df73130bed9576d331b2e4b41f27ee0244511`
- `externalBackup=C:\Users\Drevo\Documents\BGXAI_BACKUPS\PRE_BGXTD15_20261123T064327635691Z`
- `gameplayResourcesModified=true`, `weaponSwitchAuthorized=false`
- Correctly distinguish **DEPLOY=CONFIRMED, LIVE READ=NOT YET CONFIRMED**.
- Do not repeat preflight or installation. Do not alter this installed Lua manually.

Next single user-side action: close game, run same CMD -> **163 -> 5** (read-only InfinityLoader console capture; old 162->5 cannot run after TD15 due WeiDU-last guard). The capture automatically launches InfinityLoader, writes `C:\Users\Drevo\Documents\BGXAI_LIVE_REPORTS\BGXAI_R13_2_CONSOLE_<UTC>.log`. Load existing **BGXAI test save**, use just **1–3 separate, safe** weapon or fist attacks against enemy, avoiding lethal risk; exit normally; attach the new .log. If capture produces `BGXTD15_STOP` or `BGXTD15_CAPTURE_EMPTY_HOLD`, paste status and do not repeat blindly. Do not ask for old JSONL. Inspect `[BGXTD13]` `DEFENSE` events, `reason`, raw actor/target/slot and 9 defense fields; correct based on actual observations. This is the first relevant real live test of R13.2, NOT another preflight.
Repository release `575de4837a8adfdb4db8bc7a8d6503619829c4b7`, pin promotion `476efec9855f81f41f0bbc6b77ac14579de17fc7`; Windows CI `45125194435`. Previous real battle was adequate: three HOLD, slot10 fist / slot12 ammo. Main functionality disabled: no weapon auto-switch, no action queue modifications.
