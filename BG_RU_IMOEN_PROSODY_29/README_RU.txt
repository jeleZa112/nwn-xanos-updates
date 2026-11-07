BG Voice RU 2.9 -- GitHub code-only release.
Place the BG_VOICE_UPDATE.ps1 updater in bg_voice_release_v2, then run BG_VOICE_UPDATE.cmd.
The updater fetches these scripts only; Rask voices are NEVER uploaded to public GitHub.
Keep BG_RU_IMOEN_BATCH_26 intact: RASK75_LONG.wav and B_LONG_XVECTOR_APPROVED.wav are used locally.
The Qwen environment .venv_qwen and cached .tools/models/qwen3-ru-stress-cf are reused.
Then run BG_RU_IMOEN_PROSODY_29\RUN_PROSODY_29.cmd.
Optional originals: put IMOEN06_.wav, IMOEN77A.wav, IMOEN79A.wav, IMOEN79B.wav into BG_RU_IMOEN_PROSODY_29\ORIGINAL_EN.
WHOLE and PARTS are diagnostic variants, NOT verified original-prosody-transfer.
Originals and existing WAV are never overwritten. No installation, no game changes.
