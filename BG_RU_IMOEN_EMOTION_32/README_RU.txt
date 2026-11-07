BG Voice RU 3.2 — original EN emotion2vec+ analysis

1. Run SETUP_EMOTION_32.cmd once: installs a separate Python 3.11/3.12 CPU environment; never changes Qwen, Applio or game files.
2. Place your original IMOEN.zip beside VOICE_MANIFEST.csv in bg_voice_release_v2, unless RVC_DATASETS\\IMOEN already holds the source WAV.
3. Run RUN_EMOTION_32.cmd: REAL neural inference on IMOEN06_, IMOEN77A, IMOEN79A, IMOEN79B. It will download official iic/emotion2vec_plus_base weights once.
4. Open REPORTS\\LISTEN_EMOTIONS_PILOT4.html and EMOTIONS_PILOT4.csv.
5. Only after checking the pilot, run RUN_EMOTION_32.cmd --all (102 source WAV).

WARNING: 9 emotion labels are rough model hypotheses, not objective acting truth. 'Hа!' laughter, rasp, slyness and brightness require separate acoustic / human verification. Nothing automatically changes synthesized Russian WAV; model only gives director notes.
Official model: https://huggingface.co/emotion2vec/emotion2vec_plus_base
