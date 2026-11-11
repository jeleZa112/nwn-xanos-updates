# BG EET RU — stable update metadata

This is a public **metadata-only** update channel for the user's independent, read-only
Baldur's Gate EET Russian **text** localization workflow.

* Current release: v18; the user's v18 text data is bundled **locally** in their
  one-time bootstrap archive and is not hosted in this public repository.
* `channel.json` is used by `BG_EET_RU_UPDATE.py` to check release versions.
* Future JSON-only release plans, if explicitly published, are verified by SHA-256
  and by per-StrRef source/replacement hashes, then scanned against both local TLK files.
* The updater does not download/execute remote Python or write into the game directory.
* User logs, screenshots, game binaries, and voice files must never be uploaded here.
* Language text uploads require separate publication decisions; the metadata file
  alone does not contain copyrighted game texts.

The persistent local report directory is `BG_EET_RU_REPORTS`, containing
one rolling log, last summary, last CSV preview, held entries and one shareable ZIP.
