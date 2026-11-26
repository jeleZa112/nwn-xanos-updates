# BGXAI — P0 Weapon Inventory V3 → R37 same listener (26.11.2026)

## Why
After user confirmed to continue, validated authoritative BG(2)EE CRE and SLOTS.IDS: slots 15..17 quick items; **18..33 16 backpack**; 34 magical weapon. See https://gibberlings3.github.io/iesdp/files/ids/bgee/slots.htm and https://gibberlings3.github.io/iesdp/file_formats/ie_formats/cre_v1.htm. This supersedes V1/V2 15..34 scan. CRE file serialization item-slot ordering differs from EEex runtime indices; do not confuse them.

## CODE (actually committed, no EET writes)
1. Existing corrected V3 source `BGXAI/BUILD/WEAPON_INVENTORY_CORRECTED_V3_20261126/BGXAI_BACKPACK16_R37_RO_V3.lua`. Its exact mounted source 5726 bytes SHA256 `2c5fb45dc8d1de970c19e0763c8880a9bd1b33b1c10ea13ae5be64f9eab5203f`.
2. **New actual combined source candidate** `BGXAI/BUILD/R37_INVENTORY16_SINGLE_CALLBACK_SOURCEONLY_20261126/M_BGXR27_R37_INV3_SOURCE_ONLY.lua`, derived from already existing R37 single-listener source. The corrected V3 is embedded, not loaded with another listener. `R27.makeListener` contains one extra `pcall(R27.captureInventoryV3,...)` before legacy emit. V3's pre/post contextReader reuses original `before_after` + `Q81_CORE.observe`, not another actor-origin inference. Existing R33/R37 JSON contents preserved exactly. A new third `[BGXINV3]` bounded read-only status (0..16 present/empty, duplicateResref true/false/null, no full raw item dumps) follows each event, along with one session line.
3. Source-only runtime mock `test_r37_inv3_single_listener.lua`, unchanged legacy R37 seven-transition scenario plus backpack=1, inventory drift, queue drift and 0 action commands. Source structural test `test_r37_inv3_static.py`, workflow `.github/workflows/bgxai-r37-inv3-single-listener-ci.yml`.
4. **There is no NEW installer, no approved typed release, no modifications to installed R37, V6, R29, EPS, EET, BG Voice RU, BG_EET_RU or game saves.**

## VERIFIED TEST scope
- Local `luatex --luaonly` on exactly mounted V3 and test files `test_backpack16_r37_v3.lua`: **13/13 PASS**, real Lua interpreter and synthetic sprite fixtures. Test exact SHA256 `4be28476ebdbf2861da2036bc1569e85625495f1c69e9938b5449ea8acf42777`.
- A synchronous GitHub content diff/static proof on real GitHub source: 9/9 assertions passed; original R33/R37 JSON bodies byte-identical to baseline, exactly one hook site and one callback, one inventory capture, scanner 18..33, no inventory mutation actions.
- New complete ~69KB combined Lua candidate has **NOT YET been executed locally or in confirmed GitHub CI**. Workflow was committed to run Lua5.3/5.4/LuaJIT but run outcome could not be retrieved; do not report it as PASS. Native WeiDU/EET not run.
- `XEquipItem` exists as BGEE script action 385, but documentation does not prove unique instance selection, occupied slot behavior, no timing interruption, or transaction rollback; no safe active use now. `FillSlot` destroys existing target slot contents and is prohibited.

## Status matrix
- CODE: DONE single-listener composition; inventory V3 correction.
- TEST: V3 13 synthetic Lua PASS, integration 9 static PASS. **Composed native runtime test UNKNOWN**, GitHub Actions run not independently verified.
- DEPLOY: NO for V3 and composed candidate.
- LIVE: NO for new backpack observer/equip. Existing R37 game LIVE PASSIVE 12/12 preserved.

## Next exact gates
1. Confirm new CI and inspect Lua mock status; fix source-only failures immediately, without asking user to type '+'. Native R37 callback must emit original R33 then R37 then new inventory status, with one registration and 0 commands.
2. Prove actual EEex runtime backpack read and safe snapshot without unnecessary active game tests. If deployment is justified, use only exact typed onefile `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`, external backup, WeiDU last-only, strict native hash preflight; never write live without permission.
3. Reuse existing V3/V4/V5/NONINTERRUPT and R32/R34 for true per-target weapon scoring. Do not invent alternative effective APR, target effects, full instance identity or provenance flags. The novel gameplay feature is **automatically equipping the better backpack weapon**. First only empty permitted quickslot with post-move conservation proof, then occupied-slot swap separately.
4. Do not retune V6 to suppress an already committed shot; no Stop/ClearActions, respect APR, attack round, manual/EPS commands, poison/ammo/strength/shield.
