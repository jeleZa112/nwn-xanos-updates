# BGXAI — ONEFILE MENU175 XEquipItem NATIVE COMPILE READ ONLY — PINNED RELEASE (26.11.2026)

**The source-only/native-readonly onefile updater phase is now RELEASED.** It is NOT an installed item-transfer feature.

## Channel and supply chain — independently verified
- Sole user entry: `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd` unchanged.
- New `BGXAI/BGXAI_SYNC.ps1`: EXACT size **79973** bytes (old 79832), hard bootstrap maximum 80000; SHA256 `81cedf0d90d1d9651183416ce9c1b11ffc148a3df79963e33b065b3c166d4467`; immutable script commit **`5c5ead4af8c144db44e9e99c5052475ccd0c6944`**.
- Channel `BGXAI/fox_new/BOOTSTRAP_PIN.json` updated to exactly this script commit / SHA / size, pin-update commit **`269969aa53e2b6ec79b8480a6f6aa0ef7489fe49`**. Unmodified embedded CMD validates all three before launch.
- Added `'175'` branch (SHA-checked, staged single Python module) to original menu; old **1–174 handlers byte-for-byte unchanged**. Compressed only the menu's display banner for size, restored exact `BGXAI ONE-FILE UPDATER` phrase to preserve existing Windows smoke CI. Protected `Get-PinnedBytes` allowlist extended ONLY to `BGXAI/BUILD/WEAPON_XEQUIP_ONEFILE_175_RO_20261126`.
- Child Python `BGXAI/BUILD/WEAPON_XEQUIP_ONEFILE_175_RO_20261126/BGXAI_XEQUIP_ONEFILE_175_RO_V1.py` **8527 bytes**, SHA256 **`5bbc5d5444562346df7e2766d5eee97f60b1e2a33a2c5a074272697c1ee4e2b0`**. Menu175 checks both before executing in external `%LOCALAPPDATA%\BGXAI_UPDATER` cache with GUID filename, then deletes it.
- Child fetches exactly 4 allowed dependencies pinned with SHA256 and size at SAME immutable commit, from raw GitHub/jsdelivr CDN, stages them in temp **outside GAME**, runs ONLY `BGXAI_XEQUIP_NATIVE_PREFLIGHT_RO_V1.py --native-readonly`. The native wrapper pins and delegates to existing temp compile backend `BGXAI_WEAPON_NATIVE_COMPILE_PREFLIGHT_RO.py` and watches game file hashes before/after; native execution requires closed game and pinned WeiDU SHA.
- Actual generated BAF uses **unconditional `False()`** ahead of all real triggers, including exact source backpack `CheckItemSlot`, empty weapon destination `!HasItemSlot`, action idle and `XEquipItem(...,EQUIP)`. Therefore it cannot equip a real item or send actions. Sample HAMM01 is **synthetic**, not a verified current game item. `nativeWeiDUCompileVerified` remains NO until the user's actual EET reports it.

## Evidence: real independent GitHub CI
1. [Onefile supply chain and preserved R37 — 45773666116](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45773666116) **SUCCESS on Ubuntu + Windows**; actual logs: `PASS new immutable bootstrap pinned`, `R37_MENU174_SCRIPT_BYTES=79973`, `PASS Windows PowerShell 5.1 full parse`.
2. [New 175 staged script — 45773666102](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45773666102) **SUCCESS on Ubuntu + Windows**, 174 byte-exact old handlers, size 79973, same SHA256 `81ced...`, PS5.1 AST, 11 offline Python contract cases.
3. [Historical R34 source and startup smoke — 45773665999](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45773665999) **SUCCESS**, now preserves exact R34 historical baseline instead of wrongly demanding that current onefile forever equal old 79775-byte source.
4. [Coordinator offline E2E after CRLF fix — 45772958289](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45772958289) **SUCCESS Windows + Linux**, 11 offline tests each. Earlier 45772890620 FAILURE was **Windows CRLF Git checkout conversion** invalidating pinned SHA, fixed with `git config --global core.autocrlf false` BEFORE checkout; no relaxation of hash check. This reproducible bug/solution is worth cross-project method recording.
5. [Native source-only preflight wrapper — 45772130570](https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45772130570) **SUCCESS**, 11+9 Python contract tests; does NOT claim a real EET native compile.

Other *historical* workflows may still FAIL because they hardcode an older pinned entire updater and are not current authority. Do not claim all repo CI green; do not weaken current exact gates. The BG_EET_RU strict join workflows are unrelated and have independent failures. Existing game V6/R29/R37 etc unchanged.

## USER ACTION NOW NEEDED (first new real EET native compile proof)
User should CLOSE Baldur's Gate, InfinityLoader, WeiDU and launch ONLY their existing `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`, choose **175**, no external scripts and no in-game fight. In `Documents\BGXAI_LIVE_REPORTS` it creates `BGXAI_XEQUIP175_RO_YYYYMMDDTHHMMSSffffff.json` with full success or HOLD; send this JSON **and the console output if error** to chat. If STOP, do not manually retry or force it.
The action **compiles an inert BAF to an external temporary location**, checks all watched EET files unchanged, does not install anything, does not change inventory, does not require a disposable save yet.

## Four-tier status
| Capability | CODE | TEST | DEPLOY | GAME LIVE |
|---|---|---|---|---|
| Source-only V3/V4 read-only inventory scorer | yes | independent Lua CI PASS | no | no |
| Pure top-level item conservation postcondition | yes | Lua CI PASS | no | no |
| ONEFILE updater menu 175 read-only native compiler | yes | GHA Windows+Linux PASS | **yes, source-only menu and channel** | **native user EET test pending** |
| Real autonomous backpack→quickweapon equipment transfer | inert-only scaffold | no real EET A/B | no | no |

**Next after actual EET run:** inspect `nativeSymbolsAcceptedByCompiler`, `watchedFilesChanged`, engine ACTION/TRIGGER/SLOTS/XEQUIP resolution and BCS hash. If native compile PASS and no watched changes, build a separate typed and reversible **disposable save** proof of one unique real backpack weapon, one empty quickslot, safe EPS/manual action boundary, conservation of full inventory. Never remove the `False()` gate in the current source nor auto-install without proof and separate explicit typed consent. Avoid another iteration of old Khalid V6/R37 tests.
