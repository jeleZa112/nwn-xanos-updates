BG Voice RU 3.4 -- comparison of original English emotion vs Russian WHOLE and PARTS.

1. Run existing BG_VOICE_UPDATE.cmd in bg_voice_release_v2.
2. Run BG_RU_IMOEN_PROSODY_29\RUN_COMPARE_EN_RU_34.cmd.

The script reuses saved English analysis (ANALYSIS\RESULTS_EMOTION_32.json)
and the already downloaded local emotion2vec+ weights. It will NOT download
or install any model. Russian WAVs are read from BG_RU_IMOEN_PROSODY_29\OUTPUT;
optional OUTPUT.zip can also be found in the BG project root. Eight expected WAVs:
IMOEN06__WHOLE_29.wav, IMOEN06__PARTS_29.wav, IMOEN77A_WHOLE_29.wav,
IMOEN77A_PARTS_29.wav, IMOEN79A_WHOLE_29.wav, IMOEN79A_PARTS_29.wav,
IMOEN79B_WHOLE_29.wav, IMOEN79B_PARTS_29.wav.

Outputs:
ANALYSIS\COMPARE_EN_RU_34\LISTEN_EN_RU_34.html
ANALYSIS\COMPARE_EN_RU_34\EN_RU_EMOTION_COMPARISON_34.csv
ANALYSIS\COMPARE_EN_RU_34\RU_EMOTION_CACHE_34.json

Files are incremental: old completed scores are reused. The script copies
WAV into report AUDIO folder, never modifies originals. The model is a nine-
label emotional classifier; it does not detect laughter, sarcasm, huskiness,
or verify acting fidelity. English segment boundaries are only approximate.

To revisit an existing report without the model, run:
.venv_emotion32\Scripts\python.exe COMPARE_EN_RU_34.py --report-only
