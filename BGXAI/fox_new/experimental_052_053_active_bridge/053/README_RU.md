# BGXAI 053: read-only compatibility gate for future BGXAI 052

**Source-only / no installation**. This is a stand-alone Python preflight that inspects the EET install but never writes files or edits `WeiDU.log`.

Verifies exact SHA256 of the live known-good BGXAI 042B compiled `BDDEFAI.BCS`, BGXAI 049 Lua observer `M_BX43.lua`, BGXAI 044 short module `M_BX44.lua`, verifies BGX49 is the last WeiDU component, and checks `chitin.key` presence. Wrong game copy, unrecognized newer mod, changed hash, or missing file => `REVIEW_DO_NOT_INSTALL`.

Use `python verify_053_baseline.py --game <EET root>` **only if specifically directed later**. The user does not need to run it now. It does not compile or install the 052 active bridge. Its `BASELINE_OK_SOURCE_ONLY` verdict does not authorize installation by itself.

Runs 7 tests with temporary fixture folders. Repo needs actual Win WeiDU, IDS tables, and isolated clone compilation before any active BCS release.
