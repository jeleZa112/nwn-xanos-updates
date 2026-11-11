# BGXAI 061 — пункт 68, реальная read-only проверка PASS (2026-11-12)

Пользователь прислал прямой вывод `BGXAI_UPDATE.cmd`.

- `Last WeiDU: ~BGX61\SETUP-BGX61.TP2~ #0 #0 // BGXAI 061 move-to-hit-ally with bounded TTL (BCS + Lua)`
- `061 is LAST: True`; `060 is LAST: False`
- `061 BCS staged SHA matches live: True`; `061 Lua staged SHA matches live: True`
- Installed BCS SHA256: `db0fcba4678b00defa2ed7887b57c0d4207effc064891aeb9a0d7dcc1a1a6b0b`
- Installed Lua SHA256: `fd39d23dc722b549c2af1eaf065541b2ed358a9714f2636b8cab4e45fe7dcec5`
- Status ended with `BGXAI: update/status action completed.` No error.

**Verified:** WeiDU 061 is last, staged/live BCS and Lua identical by SHA, correct known pinned hashes. The external backup was **not** re-verified by option 68. Prior user confirmed one successful live episode (approach, buff, kill). Do not ask user to rerun 68, send archives, or fight Shank again for this check.

**Development status:** 064 same-ARE Lua fix is SOURCE ONLY, 170/170 offline tests PASS in previous stage. Working 061 and original `BGXAI_SYNC.ps1` / bootstrap pin remain unchanged. Draft read-only updater menu 70/71 is **NOT ACTIVE**. To activate it safely, require native Windows PowerShell parser/runtime validation of draft, then pin new source manifest/updater. Live installation of 064 needs separate explicit opt-in, WeiDU preflight and external verified backup. Continue non-destructive work without waiting for '+' according to global rule.
