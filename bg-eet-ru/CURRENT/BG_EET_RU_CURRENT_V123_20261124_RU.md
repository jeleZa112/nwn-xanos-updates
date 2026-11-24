# BG_EET_RU V123 — контрольная точка 24.11.2026

V123 merged to `bg-eet-ai` through PR #91, squash `b0ec08f3404729333d47e6733da711fc9697e896`.
CI run `45425205264`: Windows and Linux PASS. One updater `BG_EET_RU_UPDATE.cmd`; manifest release 123, SHA256 `2cb42999a50c8f8a8274fd894246edbadab674fe820ca447bae1b9f6ed138cbd`, 749971 bytes.

User V122 live memory snapshot: eight checks PASS, one process, EEex present, JIT owner not proven, ABI/miss-to-weapon/visible combat log row/gameplay HOLD. V121 native_control_flow failed; Linux objdump confirmed exact Hit SHA and 95 in-range direct branches, no escapes, one ret. V123 handles absent Windows objdump by exact-SHA pinned replay without claiming new local disassembly. Game modifications: zero. Native hook: not installed.

Next: one comprehensive source/reentrancy/item message correlation audit before any guarded native pilot; install only after typed approval, backup and rollback. Do not repeat existing V122 snapshot; no multiple CMD scripts. Preserve BGXAI/BG Voice RU.
