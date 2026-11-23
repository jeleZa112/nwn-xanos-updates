# BG_EET_RU — V106 LIVE PASS; V107 source-only checkpoint

Дата: 23 ноября 2026. Получен файл пользователя `SEND_TO_CHATGPT_BG_EET_RU(20261123-065415).zip`.
Аудит архива непосредственно в контейнере: размер 805327 байт, 123 уникальных ZIP-вложения, `testzip()=None`, ZIP SHA256 `b8a0146abd78265731841779cc8357d3e863936313fb7813c9eba947d1da6d42`.

## Фактический V106 результат из 52_V106_WEAPON_CONSOLE_BRIDGE.json

- `updater_version=106`, `mode=capture`, `status=V106_CAPTURE_COMMAND_COMPLETE`, `game_files_written=0`, `exit_code=0`, `errors=[]`.
- V105 baseline module SHA256 `c72793b590142dd8ae36a78eb364d5e2d2437150f8bf9c744a15f862099cde9d`.
- Installed V106 module SHA256 `4130359dc7778e816ad2bbf1cca20152e48fa9df4907d6411a793c0754e09bc6`.
- Console log `C:\Users\Drevo\Documents\BG_EET_RU\BG_EET_RU_V106_CONSOLE_20261123T065251571753_0000.log`, 121165 bytes, SHA256 `08f12c3f97f4f77bbc880f862c187e9ea5f5c12ed8421367ea0958c64160c292`.
- `matching_lines_total=4`: one `SOURCE_LOADED`, one `START true LISTENER_REGISTERED`, **two** `EVENT` rows.
- Event 1: `attackRoll:number:20`, `isCritical:boolean:false`, `isLeftHand:boolean:false`, `ability,attacker,effect,target,weapon:userdata`, **no launcher key**.
- Event 2: `attackRoll:number:15`, `isCritical:boolean:false`, `isLeftHand:boolean:false`, `ability,attacker,effect,target,weapon:userdata` and **`launcher:userdata`**.
- `runtime_weapon_resref_proven=false`, `ammunition_resref_proven=false`, `miss_event_coverage_proven=false`, `combat_journal_correlation_proven=false`.
- Legacy `51_V105_WEAPON_OBSERVER_BRIDGE.json` after V106 is only status: V105 installed, V105 io.open-based file export absent; this is not a V106 failure.

**Verdict:** V106 LIVE capture transport confirmed, including two real callbacks with different launcher-field presence. Do not claim two hits, a bow, ammo, launcher identity, character identity, or specific combat log correlation from these two events. Raw CItem userdata was not retained; only the label "userdata" was serialized.

## V107 read-only development

- See `BG_EET_RU_V107_CITEM_IDENTITY_SOURCE_ONLY.lua`, main `bg-eet-ai`. Uninstalled, disabled-by-default, no auto hook registration, no file writes.
- Native Lua 5.4 source-only test PASS https://github.com/jeleZa112/nwn-xanos-updates/actions/runs/45127648484.
- Investigate CItem `cResRef:get()` only with explicit runtime guard and independently verified installed EEex structure. Official EEex x64 CItem structure includes inherited CResHelper and its `cResRef`; flattening of baseclass fields in SWIG binding suggested by `item.pRes` in upstream EEex source, but exact CItem item.cResRef runtime binding **not proved**.
- Native userdata access may crash the engine even under Lua pcall; no automatic native reads. Differentiate projectile/weapon CItem from launcher CItem and determine ammunition independently.
- No change to the existing updater release manifest: **V106 remains installed** on user side; V107 is **SOURCE ONLY**, not released/deployed into the game.
- Full journal untouched; existing V101 and separate BGXAI/BG Voice RU untouched. V102 is still preflight-only.

## Next gate

1. Design V107 guarded observer read strategy with exact ABI proof, backup and restoration via same `C:\Users\Drevo\Documents\BG_EET_RU\BG_EET_RU_UPDATE.cmd`; stop if native read safety cannot be assured.
2. Do NOT have user rerun V106 event-capture test solely to re-prove a known PASS.
3. Only after real dynamic per-attack `weapon RESREF` and `launcher RESREF` evidence may model infer actual item names; ammunition recognition still requires its own proof. Misses and combat log row correlation must be separately verified.
4. No automatic game modifications; require typed consent before installation.
