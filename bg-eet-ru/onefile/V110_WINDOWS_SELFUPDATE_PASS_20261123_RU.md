# BG_EET_RU Windows V110 self-update result — 2026-11-23

- Confirmed by user's Windows console: `ОБНОВЛЕНО до v110; новый код запускается сейчас`, then `АКТУАЛЬНАЯ ВЕРСИЯ v110`.
- Result after earlier V109 size gate bug: V110 self-updater download succeeded, manifest SHA verification no longer STOP. Last release 718473 bytes and pinned SHA256 `2c73a1cbcea647f662989ba4988849872dab07129d05e9257e26f35e60e4f861`.
- Default READ ONLY path executed. Historical status: V101 installed, V102 prefight not installed, V103/104 HOLD, V105/106 installed observer. V107 `V107_STATIC_FINGERPRINT_READY_NATIVE_READ_HOLD` and external ZIP updated. V108 `V108_GUARDED_PREFLIGHT_PASS_NATIVE_UNINSTALLED`.
- **No game files written** during this run. V108 experimental native CItem RESREF observer **not installed**, no live weapon/launcher/ammo identification or missed attack/journal-row proof. Previous V106 live console transport proof only.
- Need distinct informed typed approval before experimental native memory reads (potential process crash despite `pcall`). If approved use only existing `BG_EET_RU_UPDATE.cmd --install-v108-native-read` and exact typed phrase `INSTALL_BG_EET_RU_V108_NATIVE_ITEM_READ`; make separate save first, close game. Then same CMD `--capture-v108-native-read`, a few melee and arrow attacks, one canonical ZIP. Exact rollback mode `--rollback-v108-native-read`.
- Do not rerun V107 or V106 captures, do not publish private user ZIP/console, or alter V101 FULL/BRIEF, BGXAI, BG Voice RU, TLK, UI, saves or EXE.
