# BG Voice RU — actual Windows autoselection report audit (2026-11-23)

**This is the user's original Windows output, not a simulated test.** The full report is stored **privately** in shared ChatGPT Library; no private Windows paths, game dialogue, or audio files are committed to GitHub.

Original archive Library path:
`/BG_VOICE_RU/CURRENT/BG_VOICE_AUTO_RESULTS_REAL_WINDOWS_20261123.zip`
Original archive SHA256:
`c33339c556ae8b74987afb4677ddd2a33576b72702f6ed654bf0b864ffc22664`

Read-only safety audit archive:
`/BG_VOICE_RU/CURRENT/BG_VOICE_SELECTION_REAL_RUN_AUDITED_20261123.zip`
Audit SHA256:
`29aa96b0544cfe3486a083445d58aaad169a018dca58ee35d0ad4efed743ba5a`

## Confirmed source report values

- 7,206 unique Sound IDs; 14,412 WAV source entries **reported SHA-verified on Windows** (all VERIFIED; zero missing or hash mismatch). We do not have the original WAV bytes in this chat; this is a cross-check of the emitted report and per-file SHA in that report, not a rehash of Windows disk.
- Existing protected human choices: 58 = 23 Stable/Per_line preferences + 3 special prior WAVs + 32 HOLD/conflicts. Zero manual overrides in this run; no game approvals.
- Machine proposals: 4,183 LOW, 20 MEDIUM, 2,945 VERY_LOW. 1,563 of VERY_LOW carry `TIE_DEFAULT_STABLE_UNVERIFIED_QUALITY` (a fallback, not a genuine audition selection).
- 709 `VOICE_CONTENT_CONFLICT`, 288 unreviewed acting cases, 2,630 with fewer than 3 speaker anchors. Risk flags can overlap; not additive.
- **Critical retrospective calibration failure:** of 20 previous human picks, 13 were Per_line and 7 Stable. The selector predicted **Per_line on all 20**, coincidentally matching 13/20. Therefore this is **equal to a trivial always-Per_line baseline**, not validation of speaker/acting quality. All seven Stable preferences were missed.
- No new independent acting or speaker inference was run. No stress audit and no TTS regeneration was run.

## Non-negotiable production sequence

1. Preserve original report and human picks. Do not rerun the 14,412 SHA audit without reason.
2. Use `BG_VOICE_SELECTION_REAL_RUN_AUDITED_20261123.zip` as a **safety gate**. It keeps all machine hints but marks unvalidated choices as HOLD in a separate `safe_voice_choice` column; this is not an artistic selection.
3. **Next true improvement** must run new independent acoustic speaker/acting comparison against actual English reference WAVs and several same-character examples on Windows GPU/CPU. Test both human Stable and Per_line cases separately; never use the overall agreement alone as success.
4. Do not ask user to listen to 7,206 lines or manually transfer packages between chats. Do not start stress, CAPS regeneration, acting retakes or game install before voice selection.
5. Treat numeric metrics and synthetic/code PASS as QA evidence only, not the finished Russian voice release.
