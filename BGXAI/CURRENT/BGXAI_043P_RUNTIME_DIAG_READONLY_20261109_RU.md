# BGXAI 043-P — read-only runtime Lua check (2026-11-09)

043-P confirmed installed/last via live WeiDU option 21, all hashes and rollback verified. Last screenshot after dialogue showed autopaused `ЗАМЕЧЕН ВРАГ`, not actual `Attack` action. Don't repeat Shank fight, don't reinstall 20, don't alter BCS/042B. EEex docs verify `override/M_*.lua` auto-loading and `Infinity_DisplayString` screen output; Lua observer source has global `BGX43Probe`, `.installed`, `.events`, `.errors`, `.firstNoticeShown`.

## Single next user step, no new mod install

In game, with Lua console already enabled, press Ctrl+Space, paste this read-only Lua expression and Enter:

```lua
Infinity_DisplayString("043P loaded=", tostring(BGX43Probe~=nil), " listener=", tostring(BGX43Probe and BGX43Probe.installed), " hits=", tostring(BGX43Probe and #BGX43Probe.events or 0), " notice=", tostring(BGX43Probe and BGX43Probe.firstNoticeShown), " err=", tostring(BGX43Probe and BGX43Probe.lastError))
```

It merely reads Lua memory and shows one status string. `loaded=true, listener=true` means module and callback registered; `hits=0` before an actual attack is expected; `hits>0` demonstrates attack observer; `notice=false` may simply mean no event. If console disabled, don't edit user settings blindly: ask for that one fact and prepare isolated read-only diagnostic hotkey addon with verified rollback (no BCS overwrite). Record results after user test. Underlying `Infinity_DisplayString` is on-screen text, not necessarily combat log. Sources official EEex docs (M_ modules, Infinity_DisplayString) and current 043P source.

**Project:** 042B retained, 043P passive; real live Lua callback unverified; Python intercept/cover planning model offline only. Next active patch must guard manual inputs/spells/bard and use opt-in WeiDU rollback.
