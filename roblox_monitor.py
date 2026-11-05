# Roblox background monitor - release 0.9.2
# Uses Windows Graphics Capture, processes frames only in RAM.
import os, sys, time, threading, traceback
from pathlib import Path

VERSION = "0.9.2"
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
                      space_in_core=None, enemies_approaching=None,
                      approach_protected=None, safe_to_expand=None, health=None):
    """Observed user tactic: core first, threat-triggered defense, expand outward when full.
    Returns a recommendation only; NEVER controls the game.
    """
    if not in_match: return "LOBBY:WAIT"
    if health is not None and health < .30: return "SURVIVE:ASSESS_SAFETY"
    if enemies_approaching is True and approach_protected is False:
        return "DEFENSE:BUILD_ON_APPROACH"
    if core_turrets is None: return "OBSERVE:COUNT_TURRETS"
    if money is None or turret_price is None: return "ECONOMY:READ_COST"
    if money < turret_price: return "ECONOMY:SAVE_AT_CORE"
    if core_turrets == 0: return "CORE:PLACE_FIRST"
    if space_in_core is None: return "OBSERVE:ASSESS_SPACE"
    if space_in_core: return "CORE:PLACE_MORE"
    if safe_to_expand is None: return "EXPAND:CHECK_SAFE_ROUTE"
    if safe_to_expand: return "EXPAND:STEP_OUT_PLACE_RETURN"
    return "EXPAND:WAIT_FOR_SAFE_MOMENT"

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


# ------------ Demonstration recording (opt-in, V0.9) ------------
def training_mode():
    """Record a human demonstration, not automatic playing or input injection."""
    import csv
    import zipfile
    import datetime
    import queue
    import cv2
    import numpy as np
    from windows_capture import WindowsCapture, Frame, InternalCaptureControl

    # Capture callback only queues the most recent frame; encoder runs separately.
    # Bounding the queue avoids memory growth in long sessions.
    when = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    target = Path.home() / "Documents" / "RobloxBGDiagnostics" / "TRAINING" / when
    staging = target / "_staging"
    staging.mkdir(parents=True, exist_ok=True)
    log_file = target / "training.log"
    session_csv = target / "events.csv"
    options = {
        "interval_sec": 5.0,
        "max_width": 1280,
        "jpeg_quality": 72,
        "part_images": 25,
        "session_limit_mb": 120,
        "max_minutes": 240,
        "event_cooldown": 6.0,
    }
    def line(message):
        text = datetime.datetime.now().strftime("[%H:%M:%S] ") + str(message)
        print(text, flush=True)
        with log_file.open("a", encoding="utf-8") as fp:
            fp.write(text + "\n")
    line("TRAINING session " + when + " (no Roblox control or memory access)")
    line("5-second snapshots plus event frames; ZIP every 25 frames, max 120 MB.")
    line("STOP after loss: Ctrl+C in this window; wait for final ZIP part.")
    line("Output: " + str(target))
    with session_csv.open("w", newline="", encoding="utf-8") as fp:
        csv.writer(fp).writerow(["elapsed_s", "filename", "reason", "visual_difference"])
    (target / "READ_ME.txt").write_text(
        "Human gameplay demonstration. Screenshots are sampled, not continuous video.\n"
        "Visual change is NOT proof of purchase or turret placement.\n"
        "Send the ZIP parts plus training.log to ChatGPT, preferably one part at a time.\n"
        "Roblox must remain restored (not minimized), even behind Chrome.\n", encoding="utf-8")

    incoming = queue.Queue(maxsize=1)
    halt = threading.Event()
    captured = 0
    dropped = 0
    last_queued_at = -100.0
    saved = 0
    zipped = 0
    bytes_total = 0
    start = time.monotonic()
    last_baseline = -100.0
    last_event = -100.0
    prev_hud = None
    staged_names = []
    control_holder = []

    def flush_part():
        nonlocal zipped, bytes_total, staged_names
        if not staged_names:
            return
        part_number = zipped + 1
        final = target / ("TRAIN_%03d.zip" % part_number)
        temporary = target / ("TRAIN_%03d.tmp" % part_number)
        # Each ZIP is independently uploadable. Include per-frame metadata.
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_STORED) as archive:
            for name in staged_names:
                archive.write(staging / name, arcname="frames/" + name)
            archive.write(session_csv, arcname="events_full_session.csv")
            archive.write(target / "READ_ME.txt", arcname="READ_ME.txt")
        with zipfile.ZipFile(temporary) as archive:
            corrupt = archive.testzip()
            if corrupt is not None:
                raise RuntimeError("ZIP verification failed: " + str(corrupt))
        temporary.replace(final)
        bytes_total += final.stat().st_size
        zipped += 1
        for name in staged_names:
            (staging / name).unlink(missing_ok=True)
        staged_names = []
        line("Part saved: " + final.name + " / %.1f MB total" % (bytes_total/1048576))

    capture = WindowsCapture(
        cursor_capture=None, draw_border=None, monitor_index=None, window_name="Roblox"
    )

    @capture.event
    def on_frame_arrived(frame: Frame, capture_control: InternalCaptureControl):
        nonlocal captured, dropped, last_queued_at
        if halt.is_set():
            capture_control.stop()
            return
        captured += 1
        # Sample by elapsed time, independent of fluctuating capture frame rate.
        sampled_at = time.monotonic()
        if sampled_at - last_queued_at < 0.5:
            return
        last_queued_at = sampled_at
        try:
            if incoming.full():
                dropped += 1
                return
            incoming.put_nowait((sampled_at, frame.frame_buffer[:,:,:3].copy()))
        except queue.Full:
            dropped += 1

    @capture.event
    def on_closed():
        halt.set()
        line("Capture window closed.")

    def encode_worker():
        nonlocal saved, last_baseline, last_event, prev_hud
        try:
            while not halt.is_set() or not incoming.empty():
                try:
                    ts, frame = incoming.get(timeout=0.5)
                except queue.Empty:
                    continue
                elapsed = ts - start
                height, width = frame.shape[:2]
                if width > options["max_width"]:
                    scale = options["max_width"] / width
                    frame = cv2.resize(frame, (options["max_width"], round(height*scale)))
                h, w = frame.shape[:2]
                # Compare primarily the top and bottom HUD bands.
                top = cv2.resize(frame[:max(1,int(h*.22))], (120, 25))
                bottom = cv2.resize(frame[int(h*.75):], (120, 25))
                hud = np.concatenate([top, bottom], axis=0)
                hud = cv2.cvtColor(hud, cv2.COLOR_BGR2GRAY)
                score = float(cv2.absdiff(hud, prev_hud).mean()) if prev_hud is not None else 0.0
                prev_hud = hud
                baseline = elapsed - last_baseline >= options["interval_sec"]
                event = score >= 16.0 and elapsed - last_event >= options["event_cooldown"]
                if not (baseline or event):
                    continue
                reason = "interval" if baseline else "visual_change"
                if baseline:
                    last_baseline = elapsed
                if event:
                    last_event = elapsed
                filename = "t_%07.1fs_%s.jpg" % (elapsed, reason)
                ok, jpg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY,options["jpeg_quality"]])
                if not ok:
                    raise RuntimeError("JPEG encoder returned failure")
                (staging / filename).write_bytes(jpg.tobytes())
                staged_names.append(filename)
                saved += 1
                with session_csv.open("a", newline="", encoding="utf-8") as fp:
                    csv.writer(fp).writerow([round(elapsed, 1),filename,reason,round(score,2)])
                if len(staged_names) >= options["part_images"]:
                    flush_part()
                if bytes_total + sum((staging / n).stat().st_size for n in staged_names) >= options["session_limit_mb"]*1048576:
                    line("Storage limit reached. Stopping to preserve earlier ZIP parts.")
                    halt.set()
            flush_part()
        except Exception as exc:
            line("ENCODER ERROR: " + repr(exc))
            halt.set()
            # Raw staging files are left available for recovery.
        finally:
            line("Encoder finished.")

    worker = threading.Thread(target=encode_worker, daemon=False)
    worker.start()
    try:
        control = capture.start_free_threaded()
        control_holder.append(control)
        line("Capture active. Play yourself; stop with Ctrl+C when you finish or lose. Do not close CMD with X.")
        while not halt.is_set():
            if time.monotonic() - start > 60 * options["max_minutes"]:
                line("Time limit reached; finishing archive.")
                halt.set()
                break
            time.sleep(0.5)
    except KeyboardInterrupt:
        line("User requested stop; finalizing ZIP parts.")
        halt.set()
    except Exception:
        line("CAPTURE ERROR: " + traceback.format_exc())
        halt.set()
    finally:
        # Stop from capture callback to avoid Already borrowed race.
        halt.set()
        worker.join(timeout=90)
        if worker.is_alive():
            line("WARNING: encoder still active; wait for ZIP finalization.")
            worker.join()
        line("END: received=%d dropped=%d jpg=%d zip_parts=%d" % (captured,dropped,saved,zipped))
        line("Upload TRAIN_001.zip etc. with training.log. Reached wave and game speed are supplied by player.")
    return 0


# Menu stays in the *same downloaded Python file*.
# No new CMD files are necessary.

# === V1.0 Lobby assistant: conservative foreground-only workflow ===
def lobby_helper():
    """Detect a known lobby menu, choose Hard mode and click Create when armed.
    It never starts Roblox, walks the avatar to the pad, or clicks in the background.
    """
    import ctypes
    import queue
    import cv2
    import numpy as np
    from windows_capture import WindowsCapture, Frame, InternalCaptureControl
    from ctypes import wintypes
    print("\nLOBBY HELPER V1.0")
    print("Known sequence from your recording: step onto creation pad, 1 player, Hard, Create.")
    print("Only tested visually against one supplied 1280x687 reference frame.")
    print("1 = observe only (safe)")
    print("2 = allow clicks ONLY while Roblox is the focused window")
    selection = input("Mode [1]: ").strip()
    armed = selection == "2" and input("Type YES to enable clicking: ").strip() == "YES"
    if armed:
        print("You must manually enter the purple creation pad and focus Roblox.")
        print("Program clicks hard difficulty, then Create, only if menu matches.")
        print("WARNING: cursor may move during clicks; don't use mouse at same time.")
    else:
        print("Observation mode: no mouse actions.")
    u = ctypes.windll.user32
    hwnd = u.FindWindowW(None, "Roblox")
    if not hwnd:
        print("Roblox window was not found.")
        return 1
    out = Path.home() / "Documents" / "RobloxBGDiagnostics" / "LOBBY"
    out.mkdir(parents=True, exist_ok=True)
    log_path = out / "lobby.log"
    frames = queue.Queue(maxsize=1)
    stop = threading.Event()
    state = "SEARCH_PAD"
    last_emit = ""
    last_click_time = 0.0
    modal_frames = 0
    next_action = "HARD"
    started = time.monotonic()

    def write(message):
        line = time.strftime("[%H:%M:%S] ") + str(message)
        print(line, flush=True)
        with log_path.open("a", encoding="utf-8") as fp:
            fp.write(line + "\n")

    write("Lobby helper v1.0; armed=" + str(armed))
    write("Clicks are strictly foreground-only and require detected creation menu.")

    def green_red(frame, relative_box):
        h, w = frame.shape[:2]
        x1, y1, x2, y2 = relative_box
        block = frame[int(y1*h):int(y2*h), int(x1*w):int(x2*w), :3]
        if not block.size:
            return (0.0, 0.0)
        hsv = cv2.cvtColor(block, cv2.COLOR_BGR2HSV)
        green = ((hsv[:,:,0] >= 35) & (hsv[:,:,0] <= 90) &
                 (hsv[:,:,1] > 65) & (hsv[:,:,2] > 55)).mean()
        red = ((((hsv[:,:,0] < 12) | (hsv[:,:,0] > 169)) &
                (hsv[:,:,1] > 100) & (hsv[:,:,2] > 65))).mean()
        return float(green), float(red)

    def recognize(frame):
        create_green,_ = green_red(frame, (.35,.80,.49,.94))
        one_green,_ = green_red(frame, (.35,.65,.415,.81))
        _,cancel_red = green_red(frame, (.50,.80,.66,.94))
        hard_green,_ = green_red(frame, (.665,.67,.755,.73))
        is_modal = create_green > .15 and one_green > .20 and cancel_red > .035
        return is_modal, hard_green > .14, (create_green,one_green,cancel_red,hard_green)

    def click_window_point(relx, rely, frame_w, frame_h):
        if u.GetForegroundWindow() != hwnd or u.IsIconic(hwnd):
            return "SKIPPED_NOT_FOREGROUND"
        rect = wintypes.RECT()
        if not u.GetWindowRect(hwnd, ctypes.byref(rect)):
            return "FAILED_GET_WINDOW_RECT"
        width, height = rect.right-rect.left, rect.bottom-rect.top
        if abs(width/frame_w - height/frame_h) > .12:
            return "SKIPPED_WINDOW_ASPECT_RATIO_MISMATCH"
        px = int(rect.left + width * relx)
        py = int(rect.top + height * rely)
        old = wintypes.POINT()
        u.GetCursorPos(ctypes.byref(old))
        u.SetCursorPos(px, py)
        u.mouse_event(0x0002,0,0,0,0)
        time.sleep(.07)
        u.mouse_event(0x0004,0,0,0,0)
        u.SetCursorPos(old.x,old.y)
        return "CLICK_SENT_NOT_YET_VERIFIED"

    capture = WindowsCapture(cursor_capture=None,draw_border=None,
                             monitor_index=None,window_name="Roblox")
    @capture.event
    def on_frame_arrived(frame: Frame, control: InternalCaptureControl):
        if stop.is_set():
            control.stop()
            return
        if frames.full():
            return
        try:
            # The only copied image is the latest and is discarded immediately.
            frames.put_nowait(frame.frame_buffer[:,:,:3].copy())
        except queue.Full:
            pass

    @capture.event
    def on_closed():
        stop.set()

    controller = None
    try:
        controller = capture.start_free_threaded()
        write("Started. Step onto the creation pad manually.")
        while not stop.is_set() and time.monotonic()-started < 180:
            try:
                frame = frames.get(timeout=.5)
            except queue.Empty:
                continue
            h,w = frame.shape[:2]
            is_modal, hard_selected, confidence = recognize(frame)
            if is_modal:
                modal_frames += 1
                new_state = "CREATION_MENU"
            else:
                modal_frames = 0
                new_state = "CREATION_CONFIRMED_OR_MENU_CLOSED" if state == "CREATION_MENU" else "SEARCH_PAD"
            if new_state != state:
                state = new_state
                write("STATE " + state + " features=" + str(tuple(round(x,3) for x in confidence)))
            if next_action == "WAIT_FOR_COUNTDOWN" and not is_modal:
                write("Creation dialog disappeared after Create. Verify countdown/game start.")
                break
            if not armed or modal_frames < 3 or not is_modal:
                continue
            if time.monotonic()-last_click_time < 2.0:
                continue
            if next_action == "HARD" and not hard_selected:
                action = click_window_point(.71, .702, w,h)
                write("Hard select: " + action)
                last_click_time = time.monotonic()
                if action.startswith("CLICK_SENT"):
                    next_action = "VERIFY_HARD"
            elif next_action == "VERIFY_HARD":
                if hard_selected:
                    write("Hard selection appears active; will create lobby next.")
                    next_action = "CREATE"
                else:
                    write("Hard selection not confirmed; stopping automation.")
                    break
            elif next_action == "HARD" and hard_selected:
                write("Hard selection already present.")
                next_action = "CREATE"
            elif next_action == "CREATE" and hard_selected:
                action = click_window_point(.42,.87,w,h)
                write("Create attempt: " + action)
                last_click_time = time.monotonic()
                if action.startswith("CLICK_SENT"):
                    next_action = "WAIT_FOR_COUNTDOWN"
        write("Stopped. Last state=" + state + ", next_action=" + next_action)
    except KeyboardInterrupt:
        write("User stopped lobby helper.")
    except Exception:
        write("ERROR: " + traceback.format_exc())
    finally:
        stop.set()
        if controller is not None:
            try:
                controller.stop()
            except Exception:
                pass
    return 0
# === End lobby assistant ===

def run_mode_prompt():
    print("")
    print("ROBLOX V0.9.2 - choose mode:")
    print("  1 = monitor 120 seconds (no screenshots)")
    print("  2 = LEARN human gameplay (5-second JPEGs, ZIP parts)")
    print("  3 = LOBBY assistant (observe / confirmed foreground clicks)")
    try:
        choice = input("Choose 1 or 2 [1]: ").strip()
    except EOFError:
        choice = "1"
    return choice

selected_mode = run_mode_prompt()
if selected_mode == "2":
    raise SystemExit(training_mode())
if selected_mode == "3":
    raise SystemExit(lobby_helper())

# ------------ End demonstration recording ------------

note(f"Roblox monitor {VERSION}, RAM-only analysis, {DURATION} sec")
note("HUD detection is heuristic: no OCR; exact health/money/waves not yet available.")
note("Policy loaded: core turrets -> defend when enemies approach -> step out and place when core is full; observation only")
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
