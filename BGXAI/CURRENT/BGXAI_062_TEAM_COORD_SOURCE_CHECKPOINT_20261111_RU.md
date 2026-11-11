# BGXAI 062 TEAM COORDINATION — SOURCE ONLY CHECKPOINT (2026-11-11)

Previous baseline: BGXAI 061 **INSTALLED**, one live guard episode **PASS** (approach → EPS buff → kill). No changes made to the user's live EET. The optional read-only option 68 output has not been supplied.

## Actual deliverable
Created standalone deterministic Python policy simulator `team_policy.py` and `test_team_policy.py`; all **15/15** unittest cases passed locally. Archive SHA256 `14e3acc1aa4fdc5c07968891c59b1eb9429929393cd56a95fe0db494e6e64728`.
Library: `/BALDURS_GATE_EET_AI/BUILD/BGXAI_062_TEAM_COORD_SOURCE_ONLY/BGXAI_062_TEAM_COORD_SOURCE_ONLY.zip`, alongside `README_RU.md`.

Logic: on confirmed hit with active TTL, choose exactly one eligible frontline guard (same area, conscious, melee capable, guard ON, <=40 feet), nearest first then Player slot. Ranged role holds distance, support stays with EPS. Manual orders, active action queues, stealth are never overridden. Reject invalid slots, no response to nonhostile/dead enemies or stale requests. No spells/items/AoE/actual BCS actions used; no false capability assumptions after respec.

## Boundary
This is a **policy simulator**, not a real game patch. No compiled BAF, EEex bridge, WeiDU preflight, or real-life 062 installation. **Do not announce 062 as live.** Existing auto-updater is the only future installation path.

## Next
Read-only mapping of actual party slots/roles/capabilities and 061 bridge to the simulated intents, static audit of EPS execution order, then guarded source-only BAF/EEex integration with simulated tests. Keep 061 unchanged until explicit consent for any replacement.
