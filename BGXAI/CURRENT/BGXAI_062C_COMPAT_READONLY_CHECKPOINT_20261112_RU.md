# BGXAI 062C — READ-ONLY compatibility auditor (2026-11-12)

## Result
Continuation of 062B, working 061 unchanged. Built genuine offline artifact:
- `compat_audit.py`: SHA-locked check for exact 061 source BAF / installed BCS / installed Lua, if supplied. Missing files => NOT_SUPPLIED, mismatched SHA => BLOCKED. Source BAF static audit: 20 receiver rules 2 cleanup / 6 immediate / 6 approach / 6 protect; ActionListEmpty, ModalState, InMyArea, TTL and range gates; checks for ClearActions/ActionOverride and accidental request-clear on approach.
- `test_compat_audit.py`: 13 tests PASS. Copied existing 062B policy and bridge tests, 16 PASS. **29/29 total** Python tests PASS.
- `README_RU.md` documents limitations, operator instructions and no game writes.

## Distribution
Library `/BALDURS_GATE_EET_AI/BUILD/BGXAI_062C_COMPAT_READONLY/`
ZIP SHA256 `cb0161d2b2f2a27a96f07fbdb1b48e0d1d0c49f37350a9b667a103645316eee4`.
No additional updater option, game process, WeiDU execution, or actual game-file hash scan happened in this turn. No 062C installation.

## Architecture constraints
- 061 live reported PASS for one guardian: approach → EPS buff → kill. Retain as baseline.
- Historical Lua selector `BGX52Bridge.prepare` already chooses only one F=ON guardian; 062 policy must NOT introduce a second selector.
- Critical data unavailable at runtime: reliable role/class after respec, equipped weapon, manual queue/stealth. All such claims remain unknown; fail closed.
- Source BAF static checks do NOT prove live EEex or installed file verification. User has not supplied updater option 68 output.

## Next
Assess real EEex APIs read-only for class/kit/current equipment and manual action state before designing a role-based patch. Preserve existing single-updater rule; never install source-only 062C.
