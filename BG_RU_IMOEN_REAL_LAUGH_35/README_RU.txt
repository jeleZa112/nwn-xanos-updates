BG Voice RU 3.5 -- FIRST ACTUAL SOUND EDIT, not another acoustic report.

Two local output WAVs:
- IMOEN06__EN_LAUGH_RU_PARTS_35.wav
- IMOEN77A_EN_LAUGH_RU_PARTS_35.wav

The script reads already existing English game audio:
  bg_voice_release_v2\RVC_DATASETS\IMOEN\IMOEN06_.wav
  bg_voice_release_v2\RVC_DATASETS\IMOEN\IMOEN77A.wav
and Russian generated PARTS:
  bg_voice_release_v2\BG_RU_IMOEN_PROSODY_29\OUTPUT\IMOEN06__PARTS_29.wav
  bg_voice_release_v2\BG_RU_IMOEN_PROSODY_29\OUTPUT\IMOEN77A_PARTS_29.wav

HOW TO RUN: use BG_VOICE_UPDATE.cmd to install code-only version 3.5, then run
  BG_RU_IMOEN_REAL_LAUGH_35\RUN_LAUGH_35.cmd
The script does not call TTS, download models, or modify game/WAV originals.

THE IMPORTANT LIMITATION: short English original vocal bursts were selected using
amplitude and pauses; they have not been verified by a human ear for suitability.
Listen to new WAV and compare against original. The first clip in IMOEN06_ is
0.00-0.225 s; the isolated candidate in IMOEN77A is 2.42-2.91 s.
If it sounds different from the Russian voice, do not use it in game.

This version DOES NOT fix the Russian TTS's doubled syllables and DOES NOT make
the full Russian speech more playful/brighter. For that we need an emotion-
controllable TTS/voice-transfer model, e.g. VoxCPM2 as a separate experiment.

No Rask sample, English game original or generated WAV is uploaded to the GitHub
code repository. No overwrite is allowed for existing output WAVs.