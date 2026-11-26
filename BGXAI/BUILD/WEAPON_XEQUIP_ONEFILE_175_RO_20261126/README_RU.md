# BGXAI — one existing updater menu 175, read-only native XEquipItem preflight

**No second updater.** The one and only user-facing program remains `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`. This source-only coordinator can be fetched by a SHA-checked new menu item of its already-proven PowerShell script `BGXAI_SYNC.ps1`.

Current status **not yet exposed to the pinned onefile** until staged updater CI is successful and `BOOTSTRAP_PIN.json` is updated. Current simulator only performs offline source checks; no EET installation.
The coordinator obtains four allowlisted files over HTTPS raw/CDN at the **same immutable 40-hex Git commit** authenticated by the onefile bootstrap and validates each against exact byte count and SHA256 from real GitHub Actions run 45772696537:
- pinned existing native WeiDU compile backend,
- source-only inert BAF generator (`IF False()`),
- read-only preflight wrapper,
- explicit `EXAMPLE_ONLY_NOT_USER_EET.json` sample data.

Stages external temp file tree matching backend's required relative module path, then invokes the preflight as a subprocess, returning one report in `Documents/BGXAI_LIVE_REPORTS`. Default: source-only with no game access; `--native-readonly` requires closed game and compiles **only to a temporary external WeiDU directory**, checks watched game hashes before/after, never installs or issues an action. Inert sample `HAMM01` is NOT observed in user's EET.

Source-only CI must prove offline dependency pins, fake game path source PASS, native fake game HOLD, no item move or game file write, generated single `False()` clause. Only afterwards release new onefile menu175 with strict existing menu 1–174 preservation, <=80,000 bytes, Windows PowerShell 5.1 AST and pinned bootstrap two-phase update. Do NOT remove `False()` and call it gameplay.

After native compile, actual auto-equip still needs safe EPS/manual boundary, real in-game instance uniqueness, disposable save, post-move conservation, and separate typed consent.
