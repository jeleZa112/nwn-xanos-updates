# BGXAI 042B — Hotfix option 16 (2026-11-09)

User ran option 16 after confirmed 042B real Windows install. Python rejected unsupported `--status` with argparse code 2, before modifying any game resource. **Installed 042B is unchanged.**

Root cause: common PowerShell RunRelease passed `--status`, but `BGXAI42_INSTALL.py` uses zero-argument mode for read-only status. Updated only `BGXAI/BGXAI_SYNC.ps1`: special-case `042B / --status` to invoke `py -3 $installerPath` without extra flag. All other release invocations preserved (including 041, install 15, rollback 17).

Hotfix dispatcher commit `a4566faa59d726f6fb59b035f139e5867f917a56`, 21636 bytes, SHA256 `c25eb4610d02f133f28cbd8e023b547b4092e293e938dfbb02103117748c4c7b`. `BOOTSTRAP_PIN.json` updated in commit `50ec67f1f33c7642b7424313885a45f672261738`. Ten static checks passed. No PowerShell runtime available here; **not yet verified on Windows**.

Next single action: existing `C:\Games\BG_EET_FOXX_NEW\BGXAI_UPDATE.cmd`, confirm `verified pinned script a4566faa59d7`, select **16**, paste output. Expect `STATUS: 042B INSTALLED; verified rollback backup:`. No reinstall/rollback/BCS copying. Game test later, after status.
