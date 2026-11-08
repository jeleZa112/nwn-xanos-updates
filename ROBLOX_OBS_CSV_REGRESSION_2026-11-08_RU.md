# Roblox OBS CSV — regression 2026-11-08 (V3.2.0 → V3.2.1)

Source: user-supplied `OBS_REPLAY_REPORT.txt` and `OBS_REPLAY_1FPS.csv` (192 samples, 191.27 sec). Video itself was not republished.

| Video stage (approx.) | V3.2.0 raw correct | V3.2.1 simulated from CSV |
|---|---:|---:|
| LOBBY | 10/11 | 10/11 |
| CREATION_MENU | 4/4 | 4/4 |
| LOBBY_COUNTDOWN_OR_PORTAL | 4/7 | 4/7 |
| LOADING | 6/8 | 6/8 |
| MATCH | 133/137 | 133/137 |
| DANGER_OR_DEFEAT | 0/20 | 20/20 |
| RESULTS | 4/5 | 4/5 |
| TOTAL | **161/192 (83.9%)** | **181/192 (94.3%)** |

Bug: two-patch `red_fog` around .091–.143 during defeat never reached old >.26 threshold. Ordinary battle can still have red fog up to .177, but retained `top_white>=.025` through 157s. Patch tests `red_fog>.08 and top_white<.012 and purple<.015`. This changes seconds 159–180 to DANGER; two early frames remain mismatched due approximate event annotation.

The three-sample FSM's last confirmed stage at t=191 is LOADING, because returning LOBBY is visible only at seconds 190 and 191. At least one additional frame is needed for confirmation. Do not misinterpret this as a failed game auto-return.

This is **a CSV-feature regression**, not a fresh run of the updated OpenCV classifier on the full MP4 and not a real-game test. Next: detect concrete pads and occupancy from outside the pad, avoid 45 sec on-pad idle, no blind movement, UNKNOWN inhibits controls.
