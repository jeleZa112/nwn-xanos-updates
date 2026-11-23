# BG_EET_RU — V110 legacy downloader size-limit fix / checkpoint

**Date:** 2026-11-23. SOURCE+CI+RELEASE only; user-side V110 install not yet observed.

## Reported user failure
- User launched normal `C:\Users\Drevo\Documents\BG_EET_RU\BG_EET_RU_UPDATE.cmd`; text displayed `Автообновление: STOP: скачанный источник не прошёл SHA256`, followed by V101/V102/V103/V104/V105/V106/V107 status and `V107_STATIC_FINGERPRINT_READY_NATIVE_READ_HOLD | game writes: 0`.
- Actual previous V107 `published_update()` source reads only **750001 bytes**, then checks `10000<len(new_source)<=750000 and sha256 match`. All three failure types share one message. Latest published V109 source was **771451 bytes** (GitHub contents size). Thus the 750000-byte cap is sufficient to explain the observed error; no user-side tampering, cryptographic SHA mismatch, or game corruption proved by this message.
- User remained on V107. The V107 static report was already previously Windows LIVE PASS. Do not repeat those tests.

## Corrective release V110
- Published in single existing repo path `bg-eet-ru/onefile/BG_EET_RU_UPDATE.cmd`, branch `bg-eet-ai`, source+manifest commit `83341ba6ff15028f6c1f1baa181fe5504ee08ca5`.
- Source size exactly **718473 bytes**, 52978 bytes smaller than V109, below existing V107's hard 750000-byte download limit. Only Python source indentation outside literal multiline strings was compacted; no embedded Lua payloads or game logic changed. SELF_VERSION updated 109→110.
- New SHA256 **`2c73a1cbcea647f662989ba4988849872dab07129d05e9257e26f35e60e4f861`**, exactly pinned in `bg-eet-ru/onefile/release.json`, version 110, `game_writes_allowed=false`. SHA verification not weakened.
- CI workflow `.github/workflows/bg-eet-ru-onefile-selftest.yml` now uses checkout depth 2 and validates `<=750000` bytes, SHA manifest, **Python AST equivalence against V109** except SELF_VERSION, then full original integrated selftests.
- CI PASS: `45162208803` (legacy byte cap + AST equivalence + full selftest), `45162207962` (V106 regression), `45162208091` (V105 source), `45162290563` (V108 guarded native source, synthetic install/rollback and state transitions, workflow version updated at commit `4bd8352324fd901224cc7bcd3075dd03f1dd9c8c`).
- Links: https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45162208803 and https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45162290563
- Game writes **0** for this release preparation. V108 native CItem observer was **not** installed or tested LIVE. Existing V106 captured event transport remains the only proved gameplay observation.

## Next USER action
1. Close Baldur's Gate / InfinityLoader.
2. Double-click the same canonical updater `C:\Users\Drevo\Documents\BG_EET_RU\BG_EET_RU_UPDATE.cmd` (no extra scripts or manual replacements).
3. Expect auto-update `ОБНОВЛЕНО до v110` (or `АКТУАЛЬНАЯ ВЕРСИЯ v110` if already there), then read-only status and no game writes.
4. If still STOP SHA, report the exact first update message; don't bypass SHA, don't install/rollback observers just to resolve this.
5. Only after Windows V110 status confirmed may user consider separately approved experimental V108 CItem native install. The native crash risk is still real, `pcall` is not a memory safety mechanism.

## Permanent rules
- One updater, one ZIP. Save all data in GitHub and Library, but don't upload user log ZIP to public GitHub.
- Never conflate SOURCE/CI/RELEASE/Windows preflight/INSTALLED/LIVE, nor touch BGXAI, BG Voice RU, saves, EXE/TLK/UI.MENU or existing FULL/BRIEF translations.
- Do not repeat already successful V92–V107 gameplay tests; read-only and source-only gaps remain distinct.
