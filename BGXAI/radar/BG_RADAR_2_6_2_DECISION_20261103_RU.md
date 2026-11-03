# BGXAI — BG Radar Overlay: version audit and architecture decision

Date: 2026-11-03.

## Verified
- The user's two screenshots show installed BG Radar Overlay **2.0.8.0**, file date 2026-08-06, Options refresh rate **300 ms**. UI shows character filtering, buffs, borderless, fonts and locale `ru_ru`; it does NOT show a data export or API option.
- Official upstream `tapahob/BG2RadarOverlay` latest GitHub **release** at check time: **2.6.2.0**, published 2026-10-01 22:19:50 UTC (October 2 in Amsterdam). Release: https://github.com/tapahob/BG2RadarOverlay/releases/tag/2.6.2.0 . Release asset `BG.Radar.Overlay.2.6.2.0.7z` (67,640,564 bytes). This is not a claim about the version installed on the user's Windows computer.
- Developer release notes: performance improvement from 30%+ load on a single core to approximately 2% (author's figures, not measured on user's PC), 200 ms default refresh; diagnostic performance tab; better class/kit recognition. v2.5.0.0 added translated classes/kits/effects, visual improvements and inventory/steal preview. v2.6.1.0 added OPTIONAL Twitch integration, which should stay disabled for BGXAI; streaming/paid creature-spawn features are unrelated to the user's AI project.
- New version is useful as the **player-facing overlay**, but cannot be assumed to offer an accessible BGXAI local JSON/IPC/API stream. Stock Options on v2.0.8 confirms no such switch; upstream current source has not provided a validated exporter. A planned schema and passing JS tests are NOT a working software integration.

## Architecture decision
- BG Radar must **NOT be a required BGXAI runtime dependency**. Main autonomy, visible-target evidence, action-control permissions and trap/route safety should use EEex + in-game engine state. Radar can remain an OPTIONAL independent visual diagnostic tool for comparing buffs/resistances and troubleshooting magical effectiveness and tank weapon posture.
- Keep `BGXRADAR_FUSION_V01.js` and `BGXRADAR_EVIDENCE_GATE_V02.js` as offline design/tests only. Do not create a DLL injection, invasive memory hook, second game loader or automatic private/public telemetry dependency merely to reuse Radar. Investigate exporter only if EEex is proven insufficient in specific fields and a privacy-safe local read-only adapter can be verified.
- Never treat Radar access to game memory, previously unseen enemies or traps as a license for automated cheating/safety; EEex visibility, actually discovered trap, proven route, and manual-vs-AI command origin must remain explicit.

## Next practical step
1. Optionally install Radar 2.6.2.0 into a **new separate folder** with the original v2.0.8.0 kept for rollback; backup `config.cfg`; do not enable Twitch integration or game-mutating features; keep conservative refresh 200-300 ms until performance checked.
2. Prioritize verifying EEex 0.7.3 observer on actual runtime, then native actor/kit/effects/action-origin/target data. No Radar export integration work until one specific missing EEex capability is demonstrated.
3. No change to game updater, live monitor, BAF/BCS/WeiDU, NWN main, or player's save files.

Sources: User screenshots in this chat; official GitHub release metadata retrieved 2026-11-03, project-specific `BGXAI/CURRENT/HANDOFF_LATEST_RU.md` and prior Radar integration tests. All unverified integration points remain labeled pending.