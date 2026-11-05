# Roblox background monitor - release 0.8.0
# Uses Windows Graphics Capture, processes frames only in RAM.
import os, sys, time, threading, traceback
from pathlib import Path

VERSION = "0.8.0"
DURATION = int(os.environ.get("ROBLOX_DURATION", "120"))
SAMPLE_INTERVAL = 0.5
ROOT = Path.home() / "Documents" / "RobloxBGDiagnostics" / "CURRENT"
ROOT.mkdir(parents=True, exist_ok=True)
LOG = ROOT / "monitor.log"
CSV = ROOT / "monitor.csv"
SUMMARY = ROOT / "summary.txt"
for path in (LOG, CSV, SUMMARY):
    if path.exists():
        path.unlink()

def note(line):
    message = time.strftime("[%H:%M:%S] ") + str(line)
    print(message, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(message + "\n")


# Strategy policy is embedded so the existing one-file updater remains sufficient.
def strategy_decision(in_match, money=None, turret_price=None, core_turrets=None,
                      core_limit=3, frontline_ok=None, core_protected=False,
                      perimeter_coverage=None, health=None):
    if not in_match: return "LOBBY:WAIT"
    if health is not None and health < .30: return "SURVIVE:RETREAT"
    if frontline_ok is False: return "DEFENSE:REINFORCE_FRONT"
    if core_turrets is None: return "OBSERVE:TURRET_COUNT_UNKNOWN"
    if core_turrets == 0:
        if money is None or turret_price is None: return "FIRST:OBSERVE_PRICE"
        return "FIRST:PLACE_TURRET" if money >= turret_price else "FIRST:SAVE"
    if core_turrets < core_limit:
        if money is None or turret_price is None: return "CORE:OBSERVE_PRICE"
        return "CORE:PLACE_NEXT" if money >= turret_price else "CORE:HOLD_BEHIND_TURRETS"
    if frontline_ok is None or not core_protected: return "CORE:VERIFY_AND_PROTECT"
    if perimeter_coverage is None: return "PERIMETER:SCOUT_APPROACHES"
    return "MAINTAIN:REPAIR" if perimeter_coverage >= 1.0 else "PERIMETER:EXPAND"

# Visual detection and independent controls are NOT implemented yet.
# No gameplay decisions are executed in this monitoring release.


# Conservative HUD heuristics: these are NOT OCR and never assert exact balances.
# Coordinates describe proportions of the captured Roblox client image.
def hud_signals(raw_frame):
    height, width = raw_frame.shape[:2]
    if height < 250 or width < 400:
        return "UNKNOWN", 0.0, 0.0
    # A bright green bar in bottom-center is one possible in-match health indicator.
    # Ignore the bottommost band containing the Windows taskbar or Roblox hotbar.
    zone = raw_frame[int(height * .76):int(height * .88),
                     int(width * .35):int(width * .67), :3]
    if not zone.size:
        return "UNKNOWN", 0.0, 0.0
    # BGRA captured by WindowsCapture. Screen proportions can vary across UIs.
    blue, green, red = zone[:,:,0], zone[:,:,1], zone[:,:,2]
    green_mask = (green > 135) & (green > red * 1.45) & (green > blue * 1.45)
    green_fraction = float(green_mask.mean())
    # Count rows with a contiguous-enough horizontal green health bar.
    row_fraction = green_mask.mean(axis=1)
    bar_strength = float(row_fraction.max()) if len(row_fraction) else 0.0
    mode = "POSSIBLE_MATCH" if bar_strength > .52 and green_fraction > .035 else "UNCONFIRMED"
    return mode, round(green_fraction, 4), round(bar_strength, 4)

# Explicitly opt in to a single 0.2-second background 'W' test via environment.
# This is NOT enabled by the normal one-file updater. It never takes input focus.
def try_background_key_test():
    import ctypes
    win = ctypes.windll.user32
    hwnd = win.FindWindowW(None, "Roblox")
    if not hwnd:
        return "NO_ROBLOX_WINDOW"
    if win.IsIconic(hwnd):
        return "SKIPPED_MINIMIZED"
    if win.GetForegroundWindow() == hwnd:
        return "SKIPPED_ROBLOX_IS_FOREGROUND"
    # WM_KEYDOWN/UP are advisory messages. A Roblox game may reject them.
    WM_KEYDOWN, WM_KEYUP, VK_W = 0x0100, 0x0101, 0x57
    down = win.PostMessageW(hwnd, WM_KEYDOWN, VK_W, 0x00110001)
    time.sleep(.2)
    up = win.PostMessageW(hwnd, WM_KEYUP, VK_W, 0xC0110001)
    return "POSTED_NOT_PROVEN" if down and up else "POSTMESSAGE_FAILED"

note(f"Roblox monitor {VERSION}, RAM-only analysis, {DURATION} sec")
note("HUD detection is heuristic: no OCR; exact health/money/waves not yet available.")
note("Policy loaded: first turret -> grouped core -> protected perimeter; observation only")
try:
    import numpy as np
    from windows_capture import WindowsCapture, Frame, InternalCaptureControl
except Exception as exc:
    note("DEPENDENCY ERROR: " + str(exc))
    note("Run: py -3 -m pip install --user windows-capture==2.0.1 numpy opencv-python")
    sys.exit(2)

stats = {"received": 0, "analyzed": 0, "changes": 0, "last": 0.0, "errors": 0, "left": 0.0, "center": 0.0, "right": 0.0, "possible_match": 0, "hud_mode": "UNCONFIRMED", "hud_strength": 0.0}
lock = threading.Lock()
start = time.monotonic()
previous = None
last_sample = 0.0
stopping = threading.Event()
with CSV.open("w", encoding="utf-8") as f:
    f.write("elapsed_sec,frames,motion_score,changed,left_motion,center_motion,right_motion,hud_mode,hud_strength\n")

capture = WindowsCapture(cursor_capture=None, draw_border=None,
                         monitor_index=None, window_name="Roblox")

@capture.event
def on_frame_arrived(frame: Frame, control: InternalCaptureControl):
    global previous, last_sample
    if stopping.is_set():
        control.stop()
        return
    with lock:
        stats["received"] += 1
    now = time.monotonic()
    if now - last_sample < SAMPLE_INTERVAL:
        return
    last_sample = now
    try:
        # The frame is never written to disk, and only a tiny downsample remains.
        image = frame.frame_buffer[::16, ::16, :3]
        current = image.copy()
        hud_mode, green_fraction, hud_strength = hud_signals(frame.frame_buffer)
        motion = 0.0
        if previous is not None and previous.shape == current.shape:
            motion = float(np.abs(current.astype(np.int16) -
                                  previous.astype(np.int16)).mean())
        region_motion = [0.0, 0.0, 0.0]
        if previous is not None and previous.shape == current.shape:
            difference = np.abs(current.astype(np.int16) - previous.astype(np.int16))
            width = current.shape[1]
            boundaries = [0, width // 3, 2 * width // 3, width]
            for index in range(3):
                piece = difference[:, boundaries[index]:boundaries[index+1], :]
                region_motion[index] = float(piece.mean()) if piece.size else 0.0
        previous = current
        changed = int(motion > 1.5)
        with lock:
            stats["analyzed"] += 1
            stats["changes"] += changed
            stats["last"] = motion
            stats["left"], stats["center"], stats["right"] = region_motion
            stats["hud_mode"] = hud_mode
            stats["hud_strength"] = hud_strength
            stats["possible_match"] += int(hud_mode == "POSSIBLE_MATCH")
            count = stats["received"]
        with CSV.open("a", encoding="utf-8") as f:
            f.write(f"{now-start:.1f},{count},{motion:.3f},{changed},{region_motion[0]:.3f},{region_motion[1]:.3f},{region_motion[2]:.3f},{hud_mode},{hud_strength:.3f}\n")
    except Exception as exc:
        with lock:
            stats["errors"] += 1
        note("FRAME ERROR: " + str(exc))

@capture.event
def on_closed():
    note("Capture closed")

try:
    note("Roblox should be restored, not minimized. You may cover it with Chrome.")
    controller = capture.start_free_threaded()
    if os.environ.get("ROBLOX_BG_CONTROL_TEST") == "1":
        def single_control_probe():
            if not stopping.wait(15):
                note("BACKGROUND W TEST: " + try_background_key_test())
        threading.Thread(target=single_control_probe, daemon=True).start()
    def watchdog():
        if not stopping.wait(DURATION):
            # A stop request from another thread can race with the Rust capture callback
            # and cause 'Already borrowed'. Let the next frame callback stop the session.
            stopping.set()
    threading.Thread(target=watchdog, daemon=True).start()
    controller.wait()
except KeyboardInterrupt:
    stopping.set()
    try:
        controller.stop()
    except Exception:
        pass
except Exception:
    note("CAPTURE ERROR:\n" + traceback.format_exc())
    stats["errors"] += 1
finally:
    elapsed = max(0.001, time.monotonic() - start)
    report = (f"Version: {VERSION}\nDuration: {elapsed:.1f}s\n"
              f"Frames received: {stats['received']}\n"
              f"Frames analyzed: {stats['analyzed']}\n"
              f"Scene changes: {stats['changes']}\n"
              f"Last motion by regions: {stats['left']:.2f}/{stats['center']:.2f}/{stats['right']:.2f}\n"
              f"Possible-match samples (heuristic): {stats['possible_match']}\n"
              f"Last HUD status: {stats['hud_mode']}\n"
              f"Last HUD strength: {stats['hud_strength']:.3f}\n"
              f"Input test: {'enabled' if os.environ.get('ROBLOX_BG_CONTROL_TEST') == '1' else 'disabled'}\n"
              f"Errors: {stats['errors']}\n"
              f"Screenshots saved: 0\n")
    if stats["received"] == 0:
        report += "WARNING: zero frames received. Keep Roblox restored.\n"
    SUMMARY.write_text(report, encoding="utf-8")
    note(report.replace("\n", " | "))
    note("Results folder: " + str(ROOT))
