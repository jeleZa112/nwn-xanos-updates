BG Voice RU 3.2 -- emotion2vec+ BASE, real English source-based mood analysis

Install: double-click the existing BG_VOICE_UPDATE.cmd in bg_voice_release_v2.
Then open BG_RU_IMOEN_PROSODY_29 and run RUN_EMOTION_32.cmd.
It will find original English WAV in RVC_DATASETS/IMOEN or a local IMOEN.zip.
First run creates ONLY a separate .venv_emotion32, installs FunASR/ModelScope
and downloads the official iic/emotion2vec_plus_base weights. No Qwen changes.
Do not use VPN-bypass scripts or any Rask subscription workaround.

First run: 4 English originals (IMOEN06_, IMOEN77A, IMOEN79A, IMOEN79B).
Then RUN_ALL_102_32.cmd: all 102 English originals, resuming cached profiles.

Outputs in ANALYSIS:
- ACTING_PROFILES_32.csv (real model scores + suggested directing instructions)
- RESULTS_EMOTION_32.json (reproducible scores, timing, source SHA256)
- REPORT_EMOTION_32.html (individual phrase profiles)
- RUN_EMOTION_32.log (failures/progress)

Emotion labels: angry, disgusted, fearful, happy, neutral, other, sad,
surprised, unknown. The model CANNOT infer sarcasm, laughter, breathiness,
raspiness, pitch styling or exact acting performance as distinct labels.
Scores are model outputs, not certainty; manual original listening is crucial.
Approved B_LONG_XVECTOR voice and generated Russian PARTS are never overwritten.
No original WAV is uploaded to public GitHub. No game resources are modified.