# BGXAI — Read-only actual game save inventory reader (GAM V2.0 + CRE V1.0)

**Real source evidence without an extra game launcher**. The standard Baldur's Gate save directory contains `BALDUR.GAM` alongside `BALDUR.SAV`. This pure Python reader can inspect an uploaded COPY of `BALDUR.GAM` **in the chat**; it never edits saves/game, requires no installed Lua and no new `BGXAI_UPDATE.cmd` menu.

Based on published IESDP BG2EE `GAMEV2.0` party table `0x20/0x24` (NPC entry 0x160, CRE offset at +0x4, size at +0x8, name at +0xC0), and CRE `V1.0` `0x2B8` slot table, `0x2BC` item records, `0x2C0` count, 20-byte records. The 40 CRE entries are **not in SLOTS.IDS order**: inventory 1..16 are entries 21..36, corresponding to runtime SLOTS.IDS 18..33. Quickweapons are CRE entries 9..12, corresponding to SLOTS.IDS 35..38. Read flags/charges from **actual per-item table**, not guessed from display names.

Reject unsupported `GAMEV2.1`/CRE versions, invalid indexes, duplicate item table references, out-of-bounds, unreferenced rows. In particular EET's GAME version must be inspected before assuming this parser works. No game runtime actorId or class/kit slot capacity is proven from a save. No unique-instance identity across bags, runtime manual/EPS state, current action or class restrictions is proved. Even a valid saved item can be stale compared with active game; no game-install authorization results.

For later: user can upload just a **copy** of an existing disposable save's `BALDUR.GAM` from `save/<slot>/`, not the full save archive. Use it to select a genuine expendable weapon `resref` from an actual companion backpack and ensure destination appears empty; still separately confirm in game.

Docs: https://gibberlings3.github.io/iesdp/file_formats/ie_formats/gam_v2.0.htm and https://gibberlings3.github.io/iesdp/file_formats/ie_formats/cre_v1.htm

CODE YES; synthetic tests need independent CI. GAME MODIFICATION NO.
