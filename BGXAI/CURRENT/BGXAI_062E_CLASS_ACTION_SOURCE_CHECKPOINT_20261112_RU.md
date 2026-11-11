# BGXAI 062E — Class and Action Read-Only source, 2026-11-12

**Implementation completed and verified. NOT INSTALLED.** Game BGXAI 061 remains user-confirmed live positive (approached, EPS buffed, killed attacker), unmodified.

## Concrete artifacts
Library: `/BALDURS_GATE_EET_AI/BUILD/BGXAI_062E_CLASS_ACTION_READONLY/`
ZIP SHA256: `a69404f1b1b357cb16ac4b651dd0e9043159edd43c3e2b24c87ed1028404264d`
GitHub sources: `BGXAI/fox_new/experimental_062e_class_action_source_only/`:
- `BGX62E_CLASS_ACTION_PROBE.lua` — no auto-run; bounded Player portrait scan 0..5, pcall x64 read-only `obj.m_typeAI.m_Class`, `obj.m_curAction.m_actionID`, F/modal; no writes and no listener
- `class_action_contract.py` — schema and provenance validator; treats all inferred combat capabilities and manual/queue state as UNKNOWN and never grants interception
- `test_class_action_contract.py` and `test_probe_lua_safety.py`, README

Regression tests: **84/84 PASS** on local Python 3.13, including prior 062B/C/D modules. Exact UTF-8 contents of all five GitHub source files verified against Library-backed file contents in this turn. No Lua interpreter or game runtime available; this is static+synthetic, not an EEex live proof.

Source evidence: Beamdog EEex x64 transition example `sprite.m_typeAI.m_Class`; current action field `m_curAction.m_actionID` already present in historical BGXAI 059 source. Class ID after respec/dual is NOT a proof of usable abilities. Action ID zero is NOT a proof no pending manual/EPS queue actions. No live role/equipment data is invented.

## User global rule
**On positive verification, continue next available safe task within same invocation without asking for '+'**. Work on existing one-file updater only when integration is safe; do not generate user commands for separate ad hoc installers. Stop for explicit opt-in before actual game mutation.

## Next
Read-only documentation/source validation of current equipment and EEex action ownership, then source-only capability mapping tied to existing `BGX52Bridge.prepare` (which already elects exactly one guardian), no duplicate selector. Do not change installed BGXAI 061 without guarded WeiDU preflight and consent.
