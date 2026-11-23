# BG_EET_RU — V115 static proof, V116 guarded Windows static callee check

- V68 archived four bounded function slices from installed x64 Baldur.exe, with EXE SHA `fc821a4806a0305b84fd85f1aad2bd472c8db642ed34b4494ae62351cae1c580`. Later V107 baseline has the same SHA. The game binary is NOT committed.
- V115 source-only analyzer checked a `Roll:%d` reference at RVA `0x39DADA` within function `0x39DA50`, a format call at `0x39DAF3`, attacker id moves at `0x39E7C9`, `0x39E7D6`, `0x39E7E7`, message-text construction at `0x39E80F` and dispatch call at `0x39E84B` resolved to `0x204C60`. Four separate sites in the damage function `0x38FBF0` call that same target. **18 synthetic corruption scenarios passed.**
- These bytes prove **same-function assembly of roll text and call to a shared target**; they do not prove the function's name, whether all misses go through it, that the result is appended to `combatLog[rowNumber]`, or that the exact CItem item is still available at dispatch.
- Upstream pinned EEex `InfinityLoader.db` gives a candidate `[CMessageHandler::AddMessage]`, `Pattern=4889742410574883EC20488B02`, `Operations=ADD -5`. This is a *candidate until actual installed EXE bytes are checked*.
- V116 Windows updater is SOURCE/CI PASS: **749567** UTF-8 bytes, SHA256 `a9bd14722aeb7d6e14ab1c62850298a95fdadab97c37b015a0f3759cc833ba12`, commit `bb4a87e8bdbc1f1fcca51f23460e13a180acd1fd`. It reads only installed PE64 section, exact RVA `0x204C60`, loader DB signature and pins exact EXE SHA. One canonical updater and one canonical ZIP. No game writes, no new hook. **Windows V116 is still pending**.
- No join or weapon attribution on misses is permitted without a reliable per-attack and row identity. Existing V101 FULL/BRIEF, V108, V111 and V112 are preserved. Roll/hit-only EEex context confirmed by upstream issue #86. PR #136 is unmerged and changes attack behavior; do NOT install it.

After user Windows V116 run, inspect `57_V116_DISPATCH_CALLEE_STATIC_READONLY.json`. `V116_SYMBOL_CMESSAGEHANDLER_ADDMESSAGE_MATCHED_STATIC_ONLY` would confirm static dispatch symbol, **not** log-row attribution. Any other status: read `hold_reason`, do not bypass SHA. No repeated gameplay test needed.

Upstream: https://github.com/Bubb13/EEex/issues/86 and https://github.com/Bubb13/EEex/pull/136.
