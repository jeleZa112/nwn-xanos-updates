# BGXAI R13 — Runtime: SESSION/READY genuinely confirmed

Date: 23 November 2026. User uploaded real InfinityLoader console log `BGXAI_R13_CONSOLE_20261122T182425946839Z.log` (102 lines, 7108 bytes).

## Evidence
- Exactly one `[BGXTD13]` JSON SESSION: `{"schema":"BGXAI_R13_TARGET_DEFENSE_RUNTIME_RO","type":"SESSION","readOnly":true,"liveReadVerified":false,"weaponSwitchAuthorized":false}`.
- Exactly one `[BGXTD13]` JSON READY: `{"type":"READY","hookRegistered":true,"runtimeApiAuthenticated":false,"weaponSwitchAuthorized":false}`.
- Therefore **runtime Lua executed and event listener registered** in actual game. CODE/TEST/DEPLOY R13 and Lua load/registration LIVE confirmed. **Actual defense reading still NOT confirmed**, zero DEFENSE events (test only opened main menu). No auto weapon switching.
- Previous report file `BGXAI_R13_TARGET_DEFENSE_RAW.jsonl` being absent does not mean Lua failed: R13 reports through console fallback when no Lua file writer. Use existing 162->5 capture flow rather than guessing or reinstalling.
- Legacy startup from same log: BGXW2 SESSION+READY, BGXW4 SESSION+READY, BGXWP SESSION+READY, BGXFTRACE SESSION+READY. Do not repeat R1-R4 tests.
- Independent UI issue: `Error loading menu: [string "function variant00000000049BA2A0 () return pr..."]:1: ']' expected near 'icon'` plus 14 `UI string not found` messages; do not falsely attribute these to R13 or change unrelated UI/BG_EET_RU without separate investigation.
- Log contains main menu startup only; no fight occurred during capture. This is why there is no target defense evidence, not necessarily a broken listener.

## User next action — NO INSTALL
1. Close game/InfinityLoader if running.
2. Open same `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`, choose main `162` -> submenu `5` console capture RO.
3. Start/load the already-existing BGXAI test save. With ordinary weapon equipped, issue a few **separate** manual attacks against an actual enemy (not a friend); this is only to generate started-action events, not 8 hits.
4. Exit normally. Attach the **new** `C:\Users\Drevo\Documents\BGXAI_LIVE_REPORTS\BGXAI_R13_CONSOLE_<timestamp>.log`.
5. Parse `[BGXTD13]` DEFENSE events, HOLD reasons, and fields. If no DEFENSE, investigate action ID/selected slot filters against real R1-R4 started-action records; no reinstall/guesswork.

Avoid asking again for 160, 161, 162 preflight, installation, or another no-combat main menu test. User already ran these. Main metric remains autonomous safe weapon choice with exact effective APR, target defenses, EPS/manual action continuity; R13 is only a passive signal.
