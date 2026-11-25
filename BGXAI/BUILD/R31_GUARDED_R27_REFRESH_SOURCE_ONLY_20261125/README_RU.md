# BGXAI R31 — guarded R27 observer refresh after installed R29

**25.11.2026 — SOURCE / DESIGN ONLY. NOT INSTALLED. NO GAME WRITE.**

## Purpose

Upgrade the *existing* `override/M_BGXR27.lua` observer in place, preserving the one existing listener and its proven R2/R4 selected-state capture. The new WeiDU component is named **BGXR31** so it can be installed *after* the already installed BGXR29. It must not reinstall, uninstall, or reorder BGXR27 or BGXR29.

This is not a second observer. The candidate is the already-reviewed single-callback R27 refresh:
- candidate: `BGXAI/BUILD/R27_R2_IDENTITY_REFRESH_20261124/BGXAI_R27_R2_REFRESH_SOURCE_ONLY.lua`
- SHA256: `7ca77abeb94363c75cc58986db4427d9f93edba25e09764be35008c2f0e0600b`
- installed legacy R27: `override/M_BGXR27.lua`
- installed legacy SHA256: `e5eb400c56ffb1bc23344a0cf30dcc724d8d18fc2752fabd1c2c63cdcca73735`
- expected current WeiDU tail from R30: `~BGXR29/SETUP-BGXR29.TP2~ #0 #0 // BGXR29 fighter quickslot bow-to-sword rule`
- expected history: 150 components, R27 at 149, R29 at 150.

## What the refreshed observer adds

It composes the existing R2 and R4 reads with 081 V2 in the *same existing R27 callback*. It double-reads the raw x64 `m_queuedActions.m_nCount` around the capture and only emits a stable raw count if the current action and counts remain stable. It records raw action source/context without interpreting source names as player/EPS provenance.

The output remains strictly advisory/read-only:
- `queue_empty` is never promoted to verified empty;
- `actionOriginVerified=false`, `manualEpsQueueVerified=false`;
- no BCS/LOCALS write, no queue clear, no action dispatch, no weapon switch;
- raw count >0 may defer a future scorer; raw count 0 does not authorize a switch;
- alternate-slot effective APR/THAC0/damage/effects and launcher/ammunition pairing remain unverified.

## Required guarded deployment design (not implemented/authorized here)

1. Use only the existing `BGXAI_UPDATE.cmd`; do not enlarge the near-limit `BGXAI_SYNC.ps1` (79,979 bytes / 80,000 limit). Add the feature through the existing pinned external payload/manifest mechanism after independent size and SHA tests.
2. New WeiDU component BGXR31 must append after R29 and replace only `override/M_BGXR27.lua`. It must not uninstall/reinstall R27 or R29 and must preserve the existing BGXR29 TP2 history line.
3. Preflight requires exact game root, game/InfinityLoader/WeiDU closed, exact installed legacy R27 SHA, exact candidate SHA, exact R29-last history, unique R27/R29 entries, verified EPS/EEex identities, no reparse points, and sufficient disk space.
4. Before install, make and verify an external backup of `WeiDU.log`, `chitin.key`, the old R27 Lua, relevant WeiDU metadata, and a manifest with SHA256.
5. Typed consent must authorize *this exact* BGXR31 refresh. No implicit authorization from R30 PASS or a previous R27 token.
6. Post-install verify BGXR31 is last, R29 remains immediately before it, R27 history entry is unchanged, new Lua SHA equals candidate, and backup is readable.
7. Rollback is allowed only when BGXR31 is last, all installed and backup hashes match, and the exact typed rollback token is supplied. Rollback removes only BGXR31 and restores the exact prior R27 bytes. Never roll back R29 or R27 history.
8. Runtime capture is a separate opt-in test. A successful install is not a LIVE pass.

## Acceptance gates

- SOURCE: exact candidate SHA and static no-dispatch scan.
- TEST: candidate R27/081/NONINTERRUPT tests on Lua 5.3, Lua 5.4, LuaJIT; Python gate tests on Windows/Linux.
- DEPLOY: only after the guarded BGXR31 package and one-updater integration are reviewed and separately approved.
- LIVE: capture one normal game session; verify raw queue field readability/stability. If unavailable/unstable, report UNKNOWN and stop. No combat behavior is enabled.

## Explicit non-goals

No weapon scoring changes, no V3/V4/V5 rewrite, no R29 rewrite, no 066S/EPS change, no second listener, no automatic install, no gameplay dispatch. The user's live V6 and existing R29 behavior remain untouched.
