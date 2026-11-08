BG Voice RU -- VoxCPM2, local pilot 01 for IMOEN77A

Goal: check whether a NEW generation can deliver playful, bright Russian speech with the Rask75 timbre and distinct emotional directions for greeting / teasing / question / request.
This is NOT an exact automatic transfer of all English acting contours. It uses human-reviewed semantic directions, and preserves the real original English laugh as an independent clip.

Place is BG_RU_IMOEN_PROSODY_29 below bg_voice_release_v2. Your existing GitHub updater should deliver these files.

1. Close Baldur's Gate, OBS and GPU-heavy programs to maximize GPU free memory.
2. Double-click RUN_VOXCPM2_01.cmd. Initial --check does not install anything.
3. First run creates only .venv_voxcpm2 inside the pilot folder and installs free VoxCPM2. The official model weights can take several GB of storage, and the initial download requires internet. You will be asked to type YES before any installation.
4. If CUDA is available and the GPU has enough free memory, the script generates four Russian WAVs, joins them with the ORIGINAL English laughter (2.42-2.91s), and opens VOXCPM2_PILOT_01_OUTPUT/LISTEN_VOXCPM2_01.html.
5. For comparison, 3.5 is displayed only if the file exists in the pre-existing OUTPUT_LAUGH_35 directory. Keep your 3.9 B as external listening reference if not available locally.

Safety: No files in .venv_qwen, .tools/models, RVC_DATASETS or Baldur's Gate are written or overwritten. VoxCPM2 output and downloads go to a separate directory / Hugging Face cache. Existing output WAVs are not replaced.

GPU: Official estimate for VoxCPM2 is approximately 8 GB VRAM. On RTX 4060 8 GB this may fail with CUDA out-of-memory even after disabling torch.compile and the denoiser. This is not your fault and not a reason to reinstall Qwen. Try only one pilot, stop on errors, share the log.

API sources:
https://voxcpm.readthedocs.io/en/latest/usage_guide.html
https://voxcpm.readthedocs.io/en/latest/reference/api.html
https://voxcpm.readthedocs.io/en/latest/installation.html