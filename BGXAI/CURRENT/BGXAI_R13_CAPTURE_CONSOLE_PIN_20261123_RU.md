# BGXAI — R13 no JSONL after two LIVE runs: read-only console capture published

Date: 23 Nov 2026. User ran game through InfinityLoader.exe, tested original R13 then short-resource repair R13.1/BGXTD14. No `BGXAI_R13_TARGET_DEFENSE_RAW.jsonl` appeared. User correctly rejected repeated game/install instructions.

## Root-cause distinction (important)
The installed Lua `M_BGXD13.lua` attempts `io.open(os.getenv('USERPROFILE')..'\\Documents\\BGXAI_LIVE_REPORTS\\BGXAI_R13_TARGET_DEFENSE_RAW.jsonl', 'a')` and otherwise silently outputs `[BGXTD13]` through `Infinity_Log` / `print`. Enhanced Edition UI Lua bootstrap does not normally open io/os/package (IESDP https://gibberlings3.github.io/iesdp/file_formats/ie_formats/lua_globals.htm). Thus **missing JSONL does not prove failed Lua resource loading or listener registration**. Previous assumption that renaming alone would solve absent report was unproven. Capture console instead of installing another Lua.

## Fix without changing game
The same `BGXAI_UPDATE.cmd`, menu `162`, now offers **5=capture InfinityLoader console (RO)** in addition to old 1..4. All old 1..162 top-level menu actions unchanged; old `M_BGXD13.lua` byte-for-byte unchanged. `162->5` checks game/installed shortfix proof/SHA, absence of running game, starts existing InfinityLoader.exe with stdout/stderr redirected to uniquely named external `C:\\Users\\Drevo\\Documents\\BGXAI_LIVE_REPORTS\\BGXAI_R13_CONSOLE_<UTC>.log`, waits for launcher exit. **Only open main menu and exit; no combat or re-install needed**. Return file or STOP reason.

- Immutable release commit: `7c4e3cdae47f7ecd4bf25b3e216f617ecfa21002`
- PIN promotion commit: `141e7c74f90f0dbe371369afcd4d0e2e8528bd04`
- New `BGXAI_SYNC.ps1` 79,535 bytes, SHA256 `7380e82cec9f7e67728e0cfcb6eb448c5223d71bf17aae14cfdb0474bd9f69e2`.
- `BGXAI_R13_SHORTNAME_GUARDED.py` 16,539 bytes SHA256 `dda4eaac2e5b55d1e5fb80812e078455af15fd50e622004fc631d6b2f1afeb71`.
- `M_BGXD13.lua` unchanged SHA256 `c0fb928001d5fb042a935302270df73130bed9576d331b2e4b41f27ee0244511`.
- Windows GitHub Actions CI https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45052041947 **54/54 PASS**, native PowerShell 5.1/7 AST PASS; no actual game launched in CI.
- CODE/TEST/DEPLOY tool: PASS. R13 shortfix INSTALLED per user's assertion, but full WeiDU success output not pasted. R13 runtime registration still UNVERIFIED. Weapon selection dispatch stays forbidden.
- **Next action once**: User closes any currently running game/loader; launches existing CMD -> **162 -> 5**, waits for the main menu to appear, exits normally; uploads resulting `BGXAI_R13_CONSOLE_*.log` or pastes STOP JSON. No 160, 161, 162 preflight/reinstall, no combat or manual script. Diagnose actual console content before any further game changes.

If console file empty, that is HOLD and requires another diagnostic strategy; do not invent success or install another R13 variant.
