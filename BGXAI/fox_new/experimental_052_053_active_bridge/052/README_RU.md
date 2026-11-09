# BGXAI 052: Lua -> LOCALS -> BCS guard receiver (SOURCE ONLY)

**NO INSTALL / DO NOT COPY TO EET.** Current installed 049 + 042B remains untouched.

Strict validated source baseline for the future observer: BGXAI 049 M_BX43.lua SHA256 `a1c09d704bf66f054a2099c6496212573d56d185a550fb874fc1a35b1c739912`.

Architecture:

1. Real engine `NONPARTY_WEAPON_HIT_ON_PARTY` from 049 produces an advisory; 052 bridge checks identity and actual `BGX38_GUARD=1` using EEex's `getLocalInt`.
2. One eligible guardian is selected by distance to victim (raw screen coordinates) and portrait slot; Player1 excluded as a guardian, and extra `InPartySlot` BCS checks protect against sparse/mismatched slots. No role or current action origin is fabricated.
3. `setLocalInt()` writes **only** the selected guardian's request, last confirmed hit game tick and absolute expiry in game-time ticks. Request field is written last. Persisted 049 sequence is NOT used for dedup because Lua sequence restarts at 1 on save reload. `BGX52Bridge.enabled=false` by default.
4. BCS receiver uses `GlobalTimerNotExpired`, `ActionListEmpty()`, `ModalState(NONE)`, current F toggle, `InParty`, `See`/`Range`, and per-guardian cooldown before `ProtectObject`. It clears the request first, and separately clears stale and F-OFF requests.
5. Lua never invokes `ProtectObject`, `ClearActions`, queue APIs, or overwrites EPS BCS. No live installer exists.

### Confirmed sources

- EEex v1.1.7 `EEex_Sprite.lua`: `getLocalInt`, `setLocalInt`, `m_nModalState`.
- IESDP timers: 15 clock ticks per second and absolute game-clock timer values; `GlobalTimerNotExpired` reads timer local. Source: https://gibberlings3.github.io/iesdp/appendices/timers.htm
- MODAL.IDS: NONE=0, BATTLESONG=1, DETECTTRAPS=2, STEALTH=3, TURNUNDEAD=4, SHAMANDANCE=5. Source: https://gibberlings3.github.io/iesdp/files/ids/bgee/modal.htm
- IESDP: `ProtectObject(PlayerX,6)` is persistent protective behavior, so only launch when guard F is on and character fully idle.

### Known blockers before active installation

- No compiled / live EET WeiDU test; compilation against the **actual** BG EE IDS tables must succeed, without touching the installed game.
- The EEex hit callback's ability to write sprite LOCALS safely in production is **not** proven by source inspection. Need separate isolated hook test with actual game; no automatic promotion.
- `ActionListEmpty` and `ModalState(NONE)` alone cannot prove manual vs script origin or guarantee persistence/termination of `ProtectObject`. No automatic interruption or removal of manual orders is proposed.
- Raw Euclidean distance provides deterministic ranking, not actual reachability/line-of-sight; BCS enforces actual range/LOS but cannot retry alternative guardian if selected one fails. A later failover design would need bounded temporal logic.
- No time/expiration verification after save/reload or resting in actual game. Requests should expire on game-clock advance, but engine-level tests are required.
- Need exact compiled BGXAI042B baseline SHA gate, copy-only staging, verified WeiDU rollback and new source version, with explicit YES.

### Tests

`luatex --luaonly test_bridge_052.lua` executes Lua 5.3 offline mocks. `python -m pytest -q test_receiver_052.py` performs structural guard and regression checks.
