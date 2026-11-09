# Roblox background monitor - release 3.6.8
# Uses Windows Graphics Capture, processes frames only in RAM.
import os, sys, time, threading, traceback
from pathlib import Path

VERSION = "3.6.8"
DURATION = int(os.environ.get("ROBLOX_DURATION", "120"))
SAMPLE_INTERVAL = 0.5

def verified_roblox_hwnd():
    """Return ONLY the real game-client HWND; never a browser tab about Roblox.

    windows_capture window_name is substring-based. ChatGPT/browser titles
    containing 'Roblox' were accidentally captured in V3.4.1-V3.4.2.
    Exact title plus owning executable verification is required before WGC.
    This function is Windows-only and called only by live capture modes.
    """
    import ctypes
    from ctypes import wintypes
    win=ctypes.WinDLL("user32",use_last_error=True)
    win.FindWindowW.argtypes=(wintypes.LPCWSTR,wintypes.LPCWSTR)
    win.FindWindowW.restype=wintypes.HWND
    win.GetWindowThreadProcessId.argtypes=(
        wintypes.HWND,ctypes.POINTER(wintypes.DWORD))
    win.GetWindowThreadProcessId.restype=wintypes.DWORD
    win.IsWindow.argtypes=(wintypes.HWND,)
    win.IsWindow.restype=wintypes.BOOL
    win.IsIconic.argtypes=(wintypes.HWND,)
    win.IsIconic.restype=wintypes.BOOL
    hwnd=win.FindWindowW(None,"Roblox")
    if not hwnd or not win.IsWindow(hwnd):
        raise RuntimeError(
            "CAPTURE_BLOCKED_NO_GAME_WINDOW: launch the real Roblox game "
            "and leave its window open; browser titles do not count.")
    if win.IsIconic(hwnd):
        raise RuntimeError(
            "CAPTURE_BLOCKED_MINIMIZED: restore the actual Roblox game window.")
    pid=wintypes.DWORD()
    if not win.GetWindowThreadProcessId(hwnd,ctypes.byref(pid)) or not pid.value:
        raise RuntimeError("CAPTURE_BLOCKED_NO_GAME_PROCESS_ID")
    kernel=ctypes.WinDLL("kernel32",use_last_error=True)
    kernel.OpenProcess.argtypes=(wintypes.DWORD,wintypes.BOOL,wintypes.DWORD)
    kernel.OpenProcess.restype=wintypes.HANDLE
    kernel.CloseHandle.argtypes=(wintypes.HANDLE,)
    kernel.CloseHandle.restype=wintypes.BOOL
    kernel.QueryFullProcessImageNameW.argtypes=(
        wintypes.HANDLE,wintypes.DWORD,wintypes.LPWSTR,
        ctypes.POINTER(wintypes.DWORD))
    kernel.QueryFullProcessImageNameW.restype=wintypes.BOOL
    process=kernel.OpenProcess(0x1000,False,pid.value)
    if not process:
        raise RuntimeError("CAPTURE_BLOCKED_GAME_PROCESS_UNVERIFIED")
    try:
        image_path=ctypes.create_unicode_buffer(32768)
        length=wintypes.DWORD(len(image_path))
        if not kernel.QueryFullProcessImageNameW(
                process,0,image_path,ctypes.byref(length)):
            raise RuntimeError("CAPTURE_BLOCKED_GAME_EXE_UNVERIFIED")
        exe=image_path.value.rsplit("\\",1)[-1].lower()
    finally:
        kernel.CloseHandle(process)
    if exe not in ("robloxplayerbeta.exe","robloxplayer.exe",
                   "windows10universal.exe"):
        raise RuntimeError(
            "CAPTURE_BLOCKED_NOT_GAME_EXE: "+exe+
            "; refusing to capture Chrome/other app.")
    return int(hwnd)

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
                      approach_protected=None, safe_to_expand=None, health=None,
                      turret_affordable=None):
    """Observed user tactic: core first, threat-triggered defense, expand outward when full.
    Returns a recommendation only; NEVER controls the game.
    """
    if not in_match: return "LOBBY:WAIT"
    if health is not None and health < .30: return "SURVIVE:ASSESS_SAFETY"
    if enemies_approaching is True and approach_protected is False:
        return "DEFENSE:BUILD_ON_APPROACH"
    if core_turrets is None: return "OBSERVE:COUNT_TURRETS"
    # Cost changes when turrets are built or destroyed: never hardcode $240.
    if turret_affordable is False: return "ECONOMY:SAVE_AT_CORE"
    if turret_affordable is not True:
        if money is None or turret_price is None: return "ECONOMY:READ_COST"
        if money < turret_price: return "ECONOMY:SAVE_AT_CORE"
    # A green price alone is NOT permission to press Z or place a turret.
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

def turret_price_color_signal(raw_frame):
    """Observe dynamically priced Z turret, without OCR or clicks.

    RED = currently unaffordable, GREEN = appears affordable;
    UNKNOWN = indeterminate. No numeric price or purchase is inferred.
    Prices can rise after building and fall after a turret is destroyed.
    """
    import cv2
    import numpy as np
    h,w=raw_frame.shape[:2]
    if h<400 or w<900:
        return "UNKNOWN",0.0,0.0
    frame=raw_frame[:,:,:3]
    band=frame[int(h*.20):int(h*.45),int(w*.934):int(w*.983)]
    if band.size==0:
        return "UNKNOWN",0.0,0.0
    hsv=cv2.cvtColor(band,cv2.COLOR_BGR2HSV)
    hue,sat,val=cv2.split(hsv)
    blue=(hue>82)&(hue<111)&(sat>125)&(val>105)
    row_density=blue.mean(axis=1)
    rows=np.flatnonzero(row_density>.34)
    start=None
    count=0
    prev=-10
    required=max(4,int(round(4*w/1280)))
    for y in rows:
        if int(y)==prev+1:
            count+=1
        else:
            count=1
            start=int(y)
        if count>=required:
            break
        prev=int(y)
    else:
        return "UNKNOWN",0.0,0.0
    top=int(h*.20)+start
    y1=max(0,top-int(3*w/1280))
    y2=min(h,top+int(24*w/1280))
    roi=frame[y1:y2,int(w*.951):int(w*.991)]
    if roi.size==0:
        return "UNKNOWN",0.0,0.0
    hsv=cv2.cvtColor(roi,cv2.COLOR_BGR2HSV)
    hue,sat,val=cv2.split(hsv)
    red=(((hue<12)|(hue>170))&(sat>110)&(val>95)).mean()
    green=(((hue>=35)&(hue<=92))&(sat>90)&(val>95)).mean()
    red,green=float(red),float(green)
    if green>.08 and green>red*1.7:
        return "GREEN",round(red,3),round(green,3)
    if red>.07 and red>green*1.7:
        return "RED",round(red,3),round(green,3)
    return "UNKNOWN",round(red,3),round(green,3)


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
        cursor_capture=None, draw_border=None, monitor_index=None, window_hwnd=verified_roblox_hwnd()
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




# === V2.2: in-match movement probe. No blind combat/turret actions. ===
def battle_pilot(build_once=False, require_corner=False):
    """One opt-in, foreground-only short WASD calibration in an existing match.

    This is a controlled input probe, NOT an autonomous strategy. It records
    before/after images, releases every key, and will not touch upgrades.
    """
    import ctypes
    import queue
    import zipfile
    import cv2
    import numpy as np
    from windows_capture import WindowsCapture, Frame, InternalCaptureControl

    if require_corner and not build_once:
        raise ValueError("Corner safety gate requires turret mode")
    folder = (Path.home() / "Documents" / "RobloxBGDiagnostics" /
              ("TURRET_CORNER" if require_corner else
               "TURRET" if build_once else "BATTLE"))
    folder.mkdir(parents=True, exist_ok=True)
    log_path = folder / "battle.log"
    events = []
    def log(message):
        record = time.strftime("[%H:%M:%S] ") + str(message)
        print(record, flush=True)
        with log_path.open("a", encoding="utf-8") as fp:
            fp.write(record + "\n")
        events.append(record)

    win = ctypes.WinDLL("user32", use_last_error=True)
    win.SetProcessDPIAware()
    win.FindWindowW.argtypes=(ctypes.c_wchar_p,ctypes.c_wchar_p)
    win.FindWindowW.restype=ctypes.c_void_p
    win.GetForegroundWindow.restype=ctypes.c_void_p
    win.IsIconic.argtypes=(ctypes.c_void_p,)
    win.IsIconic.restype=ctypes.c_int
    win.GetAsyncKeyState.argtypes=(ctypes.c_int,)
    win.GetAsyncKeyState.restype=ctypes.c_short
    hwnd=win.FindWindowW(None,"Roblox")
    if not hwnd:
        print("BATTLE: Roblox window not found. Start the game first.")
        return 2
    print("\nROBLOX "+("GUARDED CORNER TURRET" if require_corner else
                         "ONE-TURRET PILOT" if build_once else
                         "BATTLE PILOT")+" V"+VERSION)
    print("Open an EXISTING MATCH in Roblox; do not use in the lobby.")
    if build_once:
        print("Move to your safe main defensive position before starting.")
        if require_corner:
            print("Requires SAFE_CORNER_CALIBRATION.zip from V2.8 F10 marking.")
            print("Checks 4 fresh frames: calibrated corner AND GREEN Z price.")
        else:
            print("After YES and F8: wait for Z price to turn GREEN on 4 frames.")
        print("At most ONE Z press is allowed; game may spend currency.")
        print("No movement, no aiming, no repeated purchases.")
    else:
        print("This ONE run tests a single 0.15-second W movement only.")
        print("Stand on wide safe ground away from edges first.")
    print("Requires foreground Roblox. F8 = start once; F10 = cancel.")
    print("F9 opens Roblox developer console: do NOT use F9.")
    print("No gamepad or Arduino. Chrome may cover Roblox: observation pauses")
    print("input while unfocused and resumes only after returning to Roblox.")
    print("No key is ever sent to Chrome; only foreground Roblox receives Z.")
    consent=input(("Confirm ONE potential in-game Z purchase: type YES [default NO]: "
                   if build_once else
                   "Confirm movement probe: type YES [default NO]: ")).strip().upper()
    if consent not in ("YES","ДА"):
        print("No input performed.")
        return 0
    # Do not accidentally bundle screenshots from a previous failed run.
    for filename in ("battle.log","pilot_summary.txt","BATTLE_PILOT.zip",
                     "TURRET_PILOT.zip","CORNER_TURRET_PILOT.zip",
                     "turret_before.jpg","turret_after.jpg",
                     "turret_observation_start.jpg","turret_gate_blocked.jpg",
                     "probe_before.jpg","probe_after_W.jpg","probe_after_S.jpg",
                     "probe_after_A.jpg","probe_after_D.jpg"):
        (folder/filename).unlink(missing_ok=True)

    class MOUSEINPUT(ctypes.Structure):
        _fields_=[("dx",ctypes.c_int32),("dy",ctypes.c_int32),
                  ("mouseData",ctypes.c_uint32),("dwFlags",ctypes.c_uint32),
                  ("time",ctypes.c_uint32),("dwExtraInfo",ctypes.c_void_p)]
    class KEYBDINPUT(ctypes.Structure):
        _fields_=[("wVk",ctypes.c_uint16),("wScan",ctypes.c_uint16),
                  ("dwFlags",ctypes.c_uint32),("time",ctypes.c_uint32),
                  ("dwExtraInfo",ctypes.c_void_p)]
    class HARDWAREINPUT(ctypes.Structure):
        _fields_=[("uMsg",ctypes.c_uint32),("wParamL",ctypes.c_uint16),
                  ("wParamH",ctypes.c_uint16)]
    class INPUTUNION(ctypes.Union):
        _fields_=[("mi",MOUSEINPUT),("ki",KEYBDINPUT),("hi",HARDWAREINPUT)]
    class INPUT(ctypes.Structure):
        _anonymous_=("data",)
        _fields_=[("type",ctypes.c_uint32),("data",INPUTUNION)]
    if ctypes.sizeof(INPUT)!=40 or ctypes.sizeof(KEYBDINPUT)!=24:
        log("STOP_INVALID_INPUT_ABI: INPUT=%d KEYBD=%d" %
            (ctypes.sizeof(INPUT),ctypes.sizeof(KEYBDINPUT)))
        return 2
    win.SendInput.argtypes=(ctypes.c_uint32,ctypes.POINTER(INPUT),ctypes.c_int32)
    win.SendInput.restype=ctypes.c_uint32

    def foreground():
        return win.GetForegroundWindow()==hwnd and not win.IsIconic(hwnd)
    def pressed(vk):
        return bool(win.GetAsyncKeyState(vk)&0x8000)
    def user_is_moving():
        # Do not buy while the user is moving, aiming or jumping.
        return any(pressed(vk) for vk in
                   (0x57,0x41,0x53,0x44,0x20,0x10))
    def key(scan,down):
        ev=INPUT()
        ev.type=1  # INPUT_KEYBOARD
        ev.ki.wVk=0
        ev.ki.wScan=scan
        ev.ki.dwFlags=0x0008 | (0 if down else 0x0002)  # SCANCODE + optional UP
        ctypes.set_last_error(0)
        count=win.SendInput(1,ctypes.byref(ev),ctypes.sizeof(INPUT))
        if count!=1:
            log("KEY_INPUT_ERROR scan="+hex(scan)+
                " down="+str(down)+" WinError="+str(ctypes.get_last_error()))
        return count==1

    # Calibration is manually labelled by the user on the safe defensive
    # corner. This is visual camera similarity, NOT proof of world coordinates.
    # Require multiple independent reference matches, then consecutive frames.
    # If the scene changes, we refuse to place a turret.
    corner_refs=[]
    corner_orb=None
    corner_matcher=None
    if require_corner:
        calib=(Path.home()/"Documents"/"RobloxBGDiagnostics"/"ROUTE"/
               "SAFE_CORNER_CALIBRATION.zip")
        if not calib.is_file():
            log("CORNER_CALIBRATION_MISSING: "+str(calib))
            print("Run menu 7 at the defensive corner and press F10 once.")
            return 2
        corner_orb=cv2.ORB_create(nfeatures=900,fastThreshold=10)
        corner_matcher=cv2.BFMatcher(cv2.NORM_HAMMING)
        def corner_descriptors(image):
            h,w=image.shape[:2]
            if h<260 or w<400:
                return None
            if w!=1100:
                image=cv2.resize(image,(1100,round(h*1100/w)),
                                 interpolation=cv2.INTER_AREA)
                h,w=image.shape[:2]
            crop=image[int(h*.08):int(h*.73),int(w*.08):int(w*.91)]
            gray=cv2.cvtColor(crop,cv2.COLOR_BGR2GRAY)
            pts,desc=corner_orb.detectAndCompute(gray,None)
            return desc
        try:
            with zipfile.ZipFile(calib) as z:
                if z.testzip():
                    raise ValueError("CRC failed")
                if "MANUAL_MARK.txt" not in z.namelist():
                    raise ValueError("missing explicit F10 mark")
                names=sorted(x for x in z.namelist() if
                             x.startswith("corner_") and x.endswith(".jpg"))
                if len(names)!=5:
                    raise ValueError("expected exactly 5 saved views")
                for name in names:
                    raw=np.frombuffer(z.read(name),dtype=np.uint8)
                    frame=cv2.imdecode(raw,cv2.IMREAD_COLOR)
                    if frame is None:raise ValueError("bad image "+name)
                    desc=corner_descriptors(frame)
                    if desc is None or len(desc)<45:
                        raise ValueError("weak reference "+name)
                    corner_refs.append(desc)
        except (OSError,ValueError,zipfile.BadZipFile,cv2.error) as exc:
            log("CORNER_CALIBRATION_INVALID: "+repr(exc))
            return 2
        log("CORNER_CALIBRATION_LOADED: "+str(len(corner_refs))+" real views.")
    def corner_signal(frame):
        if not require_corner:
            return True,0,[]
        desc=corner_descriptors(frame)
        if desc is None or len(desc)<40:
            return False,0,[]
        counts=[]
        for ref in corner_refs:
            try:
                pairings=corner_matcher.knnMatch(desc,ref,k=2)
                counts.append(sum(1 for pair in pairings if
                                  len(pair)==2 and
                                  pair[0].distance<.70*pair[1].distance))
            except cv2.error:
                counts.append(0)
        votes=sum(1 for n in counts if n>=45)
        return votes>=3 and max(counts,default=0)>=65,votes,counts

    frames=queue.Queue(maxsize=1)
    stop=threading.Event()
    capture=WindowsCapture(cursor_capture=None,draw_border=None,
                           monitor_index=None,window_hwnd=verified_roblox_hwnd())
    @capture.event
    def on_frame_arrived(frame: Frame, control: InternalCaptureControl):
        if stop.is_set():
            control.stop()
            return
        try:
            img=frame.frame_buffer[:,:,:3].copy()
            if frames.full():
                try:frames.get_nowait()
                except queue.Empty:pass
            frames.put_nowait(img)
        except (queue.Full,ValueError):
            pass
    @capture.event
    def on_closed():
        stop.set()

    def get_frame(timeout=4):
        deadline=time.monotonic()+timeout
        while not stop.is_set() and time.monotonic()<deadline:
            try:
                return frames.get(timeout=min(.4, max(.05,deadline-time.monotonic())))
            except queue.Empty:
                pass
        return None
    def resize_frame(frame):
        h,w=frame.shape[:2]
        if w<=1000:return frame
        return cv2.resize(frame,(1000,round(h*1000/w)))
    def save_frame(frame,filename):
        out=folder/filename
        cv2.imwrite(str(out),resize_frame(frame),[cv2.IMWRITE_JPEG_QUALITY,75])
        return out

    def looks_like_creation_menu(img):
        # The lobby chooser has 4 white number tiles AND green Create + red
        # Cancel buttons at fixed normalized locations. Only block on all.
        h,w=img.shape[:2]
        def area(r):
            x1,y1,x2,y2=r
            return img[int(y1*h):int(y2*h),int(x1*w):int(x2*w)]
        digits=[(.369,.716,.396,.785),(.449,.716,.476,.785),
                (.529,.716,.556,.785),(.609,.716,.636,.785)]
        hits=0
        for region in digits:
            z=area(region)
            if z.size==0:continue
            b,g,r=[z[:,:,k].astype(np.int16) for k in range(3)]
            white=(b>165)&(g>165)&(r>165)&(
                np.maximum(np.maximum(b,g),r)-np.minimum(np.minimum(b,g),r)<80)
            hits+=int(float(white.mean())>.025)
        def color_fraction(region,color):
            z=area(region)
            if z.size==0:return 0.0
            hsv=cv2.cvtColor(z,cv2.COLOR_BGR2HSV)
            hh,ss,vv=cv2.split(hsv)
            if color=="green":
                return float(((hh>=35)&(hh<=90)&(ss>95)&(vv>80)).mean())
            return float((((hh<12)|(hh>170))&(ss>100)&(vv>90)).mean())
        create=color_fraction((.359,.833,.481,.914),"green")
        cancel=color_fraction((.519,.833,.642,.914),"red")
        return hits==4 and create>.07 and cancel>.07

    log(("TURRET_PILOT_START" if build_once else "BATTLE_PROBE_START")+
        ": waiting for F8 in Roblox; F10 cancels.")
    if build_once:
        log("PILOT_RULE: dynamic HUD affordability; one Z maximum "+
            "after 4 verified GREEN readings"+(
                " AND 4 SAFE_CORNER frames." if require_corner else "."))
        if require_corner:
            log("CORNER_GATE_ON: never buy at UNKNOWN camera angle.")
    else:
        log("PROBE_SAFETY: choose open safe ground, no edge. Only W 150ms; no building.")
    started=time.monotonic()
    controller=None
    try:
        controller=capture.start_free_threaded()
        prior_f8=False
        while time.monotonic()-started<180 and not stop.is_set():
            if pressed(0x79):  # F10
                log("BATTLE_PROBE_CANCELLED_F10")
                return 0
            f8=pressed(0x77) # F8
            if f8 and not prior_f8 and foreground():
                break
            prior_f8=f8
            time.sleep(.05)
        else:
            log("BATTLE_PROBE_TIMEOUT_OR_CLOSED")
            return 0
        if not foreground():
            log("STOP_FOREGROUND_REQUIRED")
            return 0
        baseline=get_frame()
        if baseline is None:
            log("STOP_NO_FRAME")
            return 2
        if looks_like_creation_menu(baseline):
            log("STOP_LOBBY_DETECTED: enter the match before movement.")
            return 2
        if float(np.mean(baseline))<18:
            log("STOP_BLACK_LOADING_SCREEN: retry after match finishes loading.")
            return 2
        if build_once:
            # No blind periodic Z spam. Each green signal is supported by 4
            # separate fresh frames, while Roblox owns the foreground.
            # One Z press maximum, even if the price remains green afterward.
            green_frames=0
            safe_frames=0
            last_report=0.
            last_verify=0.
            last_blocked_frame=0.
            paused_for_focus=False
            tried=False
            save_frame(baseline,"turret_observation_start.jpg")
            log("TURRET_DIAGNOSTIC_SAVED: turret_observation_start.jpg "+
                "(before any possible Z; may show camera/affordability mismatch)")
            result_code="TIMEOUT_WAITING_FOR_GREEN"
            deadline=time.monotonic()+240
            while not stop.is_set() and time.monotonic()<deadline:
                if pressed(0x79):
                    result_code="CANCELLED_F10"
                    log("TURRET_CANCELLED_F10")
                    break
                if not foreground():
                    if not paused_for_focus:
                        log("TURRET_PAUSED_NO_FOCUS: Chrome/other window active; "+
                            "no inputs will be sent.")
                        paused_for_focus=True
                    green_frames=0
                    safe_frames=0
                    # Keep the capture alive, but never accumulate readiness
                    # while Roblox is behind another application.
                    time.sleep(.20)
                    continue
                if paused_for_focus:
                    paused_for_focus=False
                    green_frames=0
                    safe_frames=0
                    last_verify=time.monotonic()
                    # Discard previously cached frames from when Roblox was
                    # covered so only fresh gameplay evidence can arm the key.
                    try:
                        while True:frames.get_nowait()
                    except queue.Empty:
                        pass
                    log("TURRET_RESUMED_FOCUS: readiness reset; "+
                        "require four new GREEN+corner frames.")
                    time.sleep(.33)
                    continue
                img=get_frame(timeout=2)
                if img is None:
                    green_frames=0
                    continue
                if time.monotonic()-last_verify<.32:
                    continue
                last_verify=time.monotonic()
                if looks_like_creation_menu(img):
                    result_code="LOBBY_DETECTED"
                    log("TURRET_STOP_LOBBY_DETECTED")
                    break
                signal,red_score,green_score=turret_price_color_signal(img)
                at_corner,votes,corner_scores=corner_signal(img)
                if user_is_moving():
                    green_frames=0
                    safe_frames=0
                    continue
                if at_corner:
                    safe_frames+=1
                else:
                    safe_frames=0
                if signal=="GREEN" and at_corner:
                    green_frames+=1
                else:
                    green_frames=0
                now=time.monotonic()
                if now-last_report>=6:
                    log("TURRET_WAIT price="+signal+
                        " stable_green="+str(green_frames)+
                        " stable_corner="+str(safe_frames)+
                        " votes="+str(votes)+
                        " matches="+str(corner_scores)+
                        " red="+str(red_score)+" green="+str(green_score))
                    last_report=now
                # Save a fresh diagnostic before failure/timeout if the gate
                # cannot arm. Previous pilot had *zero* screenshots on RED.
                if (now-last_blocked_frame>=20 and
                    (signal!="GREEN" or (require_corner and not at_corner))):
                    save_frame(img,"turret_gate_blocked.jpg")
                    last_blocked_frame=now
                    log("TURRET_GATE_EVIDENCE: turret_gate_blocked.jpg "+
                        "price="+signal+" corner_votes="+str(votes))
                if green_frames<4 or (require_corner and safe_frames<4):
                    continue
                # Do not issue a key if the window changed focus after the
                # evidence frame or if user cancelled.
                if not foreground() or pressed(0x79) or user_is_moving():
                    # Never send Z on an inconclusive/transition frame.
                    green_frames=0
                    safe_frames=0
                    log("TURRET_READY_RESET: focus/cancel/movement "+
                        "changed before action; no key sent.")
                    if pressed(0x79):
                        result_code="CANCELLED_F10"
                        break
                    continue
                save_frame(img,"turret_before.jpg")
                log("TURRET_Z_READY: 4 consecutive GREEN frames; "+
                    ("4 visual SAFE_CORNER frames (viewpoint only)." if require_corner
                     else "position assumed safe."))
                tried=True
                down=key(0x2c,True)  # US scan-code Z
                if not down:
                    result_code="Z_SENDINPUT_FAILED"
                    log("TURRET_Z_INPUT_FAILED")
                    break
                try:
                    end=time.monotonic()+.10
                    while time.monotonic()<end:
                        if pressed(0x79) or not foreground() or stop.is_set():
                            log("TURRET_Z_CANCEL_DURING_KEY_F10")
                            break
                        time.sleep(.01)
                finally:
                    key(0x2c,False)
                result_code="Z_SENT_GAME_UNVERIFIED"
                log("TURRET_Z_SENT_ONCE: keyboard event accepted, "+
                    "turret spawn or currency spend NOT YET VERIFIED")
                time.sleep(.9)
                aft=get_frame(timeout=3)
                if aft is not None:
                    save_frame(aft,"turret_after.jpg")
                    after_signal,after_red,after_green=turret_price_color_signal(aft)
                    log("TURRET_POST_Z: price="+after_signal+
                        " red="+str(after_red)+" green="+str(after_green)+
                        "; color change alone is NOT proof of placement")
                break
            log("TURRET_PILOT_END status="+result_code+
                " sent_once="+str(tried))
            (folder/"pilot_summary.txt").write_text(
                "One-turret pilot V"+VERSION+"\n"+
                "Dynamic price; 4 stable green frames; ONE Z only.\n"+
                "No moving, attacking, mouse clicks, or automatic repeat.\n"+
                ("Uses calibrated SAFE_CORNER scene, not coordinates.\n"
                 if require_corner else
                 "Position must be set by user in this experimental release.\n")+
                "Status: "+result_code+"\n"+
                "Z_SENT_GAME_UNVERIFIED means game outcome is unknown.\n"+
                "Observe-only while Roblox is not the foreground window.\n"+
                "A GREEN price alone is not safe position confirmation.\n",
                encoding="utf-8")
        else:
            save_frame(baseline,"probe_before.jpg")
            log("BATTLE_PROBE_ARMED: ONE W key calibration 150ms; no shooting/building.")
            actions=(("W",0x11,.15),)
            previous=baseline
            results=[]
            for label,scan,seconds in actions:
                if not foreground() or pressed(0x78) or stop.is_set():
                    log("STOP_FOCUS_LOST_OR_F10 before="+label)
                    break
                down=key(scan,True)
                if not down:
                    log("STOP_CANNOT_SEND_KEY "+label)
                    break
                try:
                    end=time.monotonic()+seconds
                    while time.monotonic()<end:
                        if not foreground() or pressed(0x78) or stop.is_set():
                            log("STOP_DURING_KEY "+label)
                            break
                        time.sleep(.02)
                finally:
                    key(scan,False)
                # Wait a moment for frame/camera response; no shared held keys.
                time.sleep(.55)
                next_frame=get_frame(3)
                if next_frame is None:
                    log("STOP_NO_NEW_FRAME_AFTER "+label)
                    break
                save_frame(next_frame,"probe_after_"+label+".jpg")
                a=resize_frame(previous)
                b=resize_frame(next_frame)
                if a.shape==b.shape:
                    # Exclude HUD strips: logs only a rough scene-change metric,
                    # NOT verified character displacement.
                    y1,y2=int(a.shape[0]*.20),int(a.shape[0]*.75)
                    motion=float(cv2.absdiff(a[y1:y2],b[y1:y2]).mean())
                else:
                    motion=-1.
                log("KEY_SENT key="+label+" held_ms="+str(int(seconds*1000))+
                    " scene_change="+str(round(motion,2))+
                    " (not proof of movement)")
                results.append((label,round(motion,2)))
                previous=next_frame
            log("BATTLE_PROBE_END: "+str(results)+
                "; saved frames="+str(len(results)+1))
            (folder/"pilot_summary.txt").write_text(
                "Roblox battle motion pilot V"+VERSION+"\n"+
                "Foreground-only; 1 scan-code pulse (W 150ms); no purchases.\n"+
                "Scene change does NOT prove movement or correct controls.\n"+
                "Results: "+repr(results)+"\n"+
                "Upload battle.log and probe_before/after JPGs for UI mapping.\n",
                encoding="utf-8")
    except KeyboardInterrupt:
        log("BATTLE_PROBE_CTRL_C")
    except Exception:
        log("BATTLE_PROBE_ERROR "+traceback.format_exc())
        return 2
    finally:
        stop.set()  # capture callback stops itself; no borrowed-frame stop race
    # One uploadable bundle: source images + precise event log + summary.
    bundle=folder/("CORNER_TURRET_PILOT.zip" if require_corner else
                   "TURRET_PILOT.zip" if build_once else "BATTLE_PILOT.zip")
    filenames=(("battle.log","pilot_summary.txt",
                "turret_observation_start.jpg","turret_gate_blocked.jpg",
                "turret_before.jpg","turret_after.jpg") if build_once else
               ("battle.log","pilot_summary.txt","probe_before.jpg",
                "probe_after_W.jpg"))
    with zipfile.ZipFile(bundle,"w",compression=zipfile.ZIP_DEFLATED) as z:
        for filename in filenames:
            item=folder/filename
            if item.exists():
                z.write(item,arcname=filename)
    with zipfile.ZipFile(bundle) as z:
        corrupt=z.testzip()
        if corrupt:
            log("ZIP_VALIDATION_FAILED "+str(corrupt))
            return 2
    log("BUNDLE_READY: "+str(bundle))
    log("Output: "+str(folder))
    return 0


# === Visual route checkpoints, sourced from the user's existing ROUTE_DEMO.zip. ===
# No guessing from raw WASD timings; this is the safety sensor for future routes.
def route_visual_observer():
    """Conservative route camera-position recognizer, READ-ONLY.

    Loads the already recorded route frames from Documents. Classifies only
    scenes strongly matching the demonstrated view, NOT world coordinates.
    Unknown/ambiguous views are rejected. Does not press ANY Roblox keys.
    """
    import zipfile
    import queue
    import ctypes
    import re
    import json
    import cv2
    import numpy as np
    from windows_capture import WindowsCapture, Frame, InternalCaptureControl

    root=Path.home()/"Documents"/"RobloxBGDiagnostics"/"ROUTE"
    source=root/"ROUTE_DEMO.zip"
    out=root/"VISUAL_ROUTE_REPORT.txt"
    calibrated=root/"SAFE_CORNER_CALIBRATION.zip"
    if not source.is_file():
        print("ROUTE_VISION: existing ROUTE_DEMO.zip not found: "+str(source))
        print("No movements attempted; route recording must exist first.")
        return 2
    stages=("START","TURN_TO_RAMP","RAMP_BASE","RAMP_ASCENT",
            "RAMP_TOP","CORNER_APPROACH","SAFE_CORNER")
    indexes=((0,1),(2,3),(4,),(5,),(6,),(7,8),(9,10))
    which={i:label for label,ids in zip(stages,indexes) for i in ids}
    orb=cv2.ORB_create(nfeatures=800,fastThreshold=10)
    matcher=cv2.BFMatcher(cv2.NORM_HAMMING)
    def descriptor(img):
        h,w=img.shape[:2]
        if h<250 or w<400:
            return None
        # Match saved reference frames at the same pixel scale.
        # Original demo is 1100px wide; WGC live images can be 1649/1920px.
        if w!=1100:
            img=cv2.resize(img,(1100,max(1,round(h*1100/w))),
                           interpolation=cv2.INTER_AREA)
            h,w=img.shape[:2]
        region=img[int(.08*h):int(.73*h),int(.08*w):int(.91*w)]
        gray=cv2.cvtColor(region,cv2.COLOR_BGR2GRAY)
        _points,desc=orb.detectAndCompute(gray,None)
        return desc
    def match_count(query,reference):
        if query is None or reference is None or len(query)<6 or len(reference)<6:
            return 0
        try:
            pairs=matcher.knnMatch(query,reference,k=2)
            return sum(1 for p in pairs if len(p)==2 and
                       p[0].distance < .70*p[1].distance)
        except cv2.error:
            return 0
    references=[]
    try:
        with zipfile.ZipFile(source) as package:
            if package.testzip():
                raise ValueError("ZIP CRC check failed")
            items=[name for name in package.namelist() if
                   re.fullmatch(r"route_(\d{2})_\d{3}\.\ds\.jpg",name)]
            for name in sorted(items):
                index=int(re.search(r"route_(\d{2})_",name).group(1))
                if index not in which:
                    continue
                raw=np.frombuffer(package.read(name),dtype=np.uint8)
                image=cv2.imdecode(raw,cv2.IMREAD_COLOR)
                if image is None:
                    continue
                desc=descriptor(image)
                if desc is None or len(desc)<35:
                    continue
                references.append((index,which[index],desc))
    except (OSError,ValueError,zipfile.BadZipFile) as exc:
        print("ROUTE_VISION_REFERENCE_ERROR: "+repr(exc))
        return 2
    if len(references)<9:
        print("ROUTE_VISION: insufficient reference frames (need 9+, have "+
              str(len(references))+"). No movement.")
        return 2
    def load_safe_calibration():
        """Load only user-marked real Roblox scenes; never synthesize a label."""
        if not calibrated.is_file():
            return 0
        items=[]
        try:
            with zipfile.ZipFile(calibrated) as z:
                if z.testzip():
                    raise ValueError("bad calibration ZIP CRC")
                files=sorted(name for name in z.namelist()
                             if re.fullmatch(r"corner_\d\d\.jpg",name))
                if len(files)<3 or len(files)>8:
                    raise ValueError("expected 3-8 reference frames")
                for filename in files:
                    raw=np.frombuffer(z.read(filename),dtype=np.uint8)
                    decoded=cv2.imdecode(raw,cv2.IMREAD_COLOR)
                    if decoded is None:continue
                    desc=descriptor(decoded)
                    if desc is None or len(desc)<45:continue
                    items.append(desc)
        except (OSError,ValueError,zipfile.BadZipFile) as exc:
            print("ROUTE_CALIBRATION_INVALID: "+repr(exc))
            return 0
        if len(items)<3:
            print("ROUTE_CALIBRATION_TOO_FEW_USABLE_IMAGES: "+str(len(items)))
            return 0
        for i,desc in enumerate(items):
            references.append((100+i,"SAFE_CORNER",desc))
        return len(items)
    restored=load_safe_calibration()
    def classify(desc,except_index=None):
        per_stage={stage:0 for stage in stages}
        for index,stage,ref in references:
            if index==except_index:
                continue
            per_stage[stage]=max(per_stage[stage],match_count(desc,ref))
        ordered=sorted(per_stage.items(),key=lambda item:item[1],reverse=True)
        first,n=ordered[0]
        other=ordered[1][1]
        # Weak coincidences and ties are never treated as positioning.
        label=first if n>=35 and n>=2.0*max(1,other) else "UNKNOWN"
        return label,n,other
    # Always validate against the old archive before trying live observation.
    checks=[]
    for index,stage,ref in references:
        label,n,other=classify(ref,except_index=index)
        checks.append("%02d %-16s other_frame=%-16s good=%3d second=%3d"%
                      (index,stage,label,n,other))
    report=[
        "ROBLOX route visual anchors V"+VERSION,
        "Reference ZIP: "+str(source),
        "Reference frames: "+str(len(references)),
        "Additional user-marked corner views: "+str(restored),
        "This is visual scene matching, NOT localization or route navigation.",
        "Never replay original timed key spans near a platform edge.",
        "Other-frame cross-check (same screenshot excluded):",
        *checks,
    ]
    def log(message):
        line=time.strftime("[%H:%M:%S] ")+message
        print(line,flush=True)
        report.append(line)
    log("VISION_READY: "+str(len(references))+
        " reference images, model does not control Roblox.")
    log("CAMERA_NOTE: SAFE_CORNER in previous session was UNKNOWN after "+
        "camera rotation; will NOT lower match thresholds.")
    log("CALIBRATION_OPTION: at the SAFE CORNER, keep Roblox foreground "+
        "and press F10 ONCE to add this camera view (no movement sent).")
    if restored:
        log("CALIBRATION_RESTORED: "+str(restored)+" extra reference frames.")
    frames=queue.Queue(maxsize=1)
    stop=threading.Event()
    cap=WindowsCapture(cursor_capture=None,draw_border=None,
                       monitor_index=None,window_hwnd=verified_roblox_hwnd())
    @cap.event
    def on_frame_arrived(frame: Frame,control: InternalCaptureControl):
        if stop.is_set():
            control.stop()
            return
        try:
            latest=frame.frame_buffer[:,:,:3].copy()
            if frames.full():
                try:frames.get_nowait()
                except queue.Empty:pass
            frames.put_nowait(latest)
        except (ValueError,queue.Full):
            pass
    @cap.event
    def on_closed():
        stop.set()
    ui=ctypes.WinDLL("user32",use_last_error=True)
    ui.FindWindowW.argtypes=(ctypes.c_wchar_p,ctypes.c_wchar_p)
    ui.FindWindowW.restype=ctypes.c_void_p
    ui.GetForegroundWindow.restype=ctypes.c_void_p
    ui.IsIconic.argtypes=(ctypes.c_void_p,)
    ui.IsIconic.restype=ctypes.c_int
    ui.GetAsyncKeyState.argtypes=(ctypes.c_int,)
    ui.GetAsyncKeyState.restype=ctypes.c_short
    hwnd=ui.FindWindowW(None,"Roblox")
    def foreground():
        return bool(hwnd and ui.GetForegroundWindow()==hwnd and
                    not ui.IsIconic(hwnd))
    def stop_key():
        # F10 is not used by this observer for any game control.
        return bool(ui.GetAsyncKeyState(0x79)&0x8000)
    def mark_corner():
        # Human labels the known destination by pressing F10 there.
        # Never label an unknown scene based on low-confidence matching.
        if not foreground():
            log("CORNER_MARK_SKIPPED: Roblox must be foreground.")
            return False
        collected=[]
        for i in range(5):
            if stop.is_set() or not foreground():
                log("CORNER_MARK_ABORTED: capture ended or focus was lost.")
                return False
            try:
                current=frames.get(timeout=1.2)
            except queue.Empty:
                log("CORNER_MARK_ABORTED: no fresh Roblox frame.")
                return False
            h,w=current.shape[:2]
            if w>1100:
                current=cv2.resize(current,(1100,round(h*1100/w)),
                                   interpolation=cv2.INTER_AREA)
            d=descriptor(current)
            if d is None or len(d)<45:
                log("CORNER_MARK_ABORTED: insufficient visible scene texture.")
                return False
            ok,jpg=cv2.imencode(".jpg",current,
                                [cv2.IMWRITE_JPEG_QUALITY,78])
            if not ok:
                log("CORNER_MARK_ABORTED: JPEG encode failed.")
                return False
            collected.append((current,d,jpg.tobytes()))
            time.sleep(.22)
        # Require sufficient cross-frame matches so a blank/loading screen,
        # occluded UI or rapid camera turn cannot become a reference.
        cross=[match_count(collected[i][1],collected[i+1][1])
               for i in range(4)]
        if min(cross)<40:
            log("CORNER_MARK_REJECTED: unstable view cross_matches="+str(cross))
            return False
        tmp=calibrated.with_suffix(".tmp")
        try:
            with zipfile.ZipFile(tmp,"w",zipfile.ZIP_DEFLATED) as z:
                for i,(_,_,jpg) in enumerate(collected):
                    z.writestr("corner_%02d.jpg"%i,jpg)
                z.writestr("MANUAL_MARK.txt",
                           "F10 confirmed by player at the defensive corner.\n"
                           "No map coordinates or path are inferred.\n"
                           "This is a visual viewpoint reference only.\n")
            with zipfile.ZipFile(tmp) as z:
                if z.testzip():raise ValueError("bad saved ZIP")
            tmp.replace(calibrated)
        except (OSError,ValueError,zipfile.BadZipFile) as exc:
            log("CORNER_MARK_SAVE_FAILED: "+repr(exc))
            return False
        references[:]=[(i,stage,desc) for i,stage,desc in references if i<100]
        for i,(_,desc,_) in enumerate(collected):
            references.append((100+i,"SAFE_CORNER",desc))
        log("CORNER_MARK_SAVED: 5 user-confirmed views, cross_matches="+
            str(cross)+" location="+str(calibrated))
        return True
    controller=None
    start=time.monotonic()
    last_sample=0.
    last_print=0.
    last_stage="UNKNOWN"
    consecutive=0
    stable_points=[]
    previous_f10=False
    marked_this_run=False
    try:
        controller=cap.start_free_threaded()
        log("VISION_WATCH: observe restored Roblox for up to 90 seconds.")
        log("No mouse/keyboard injection and no new route demonstration.")
        while not stop.is_set() and time.monotonic()-start<90:
            f10=stop_key()
            if f10 and not previous_f10 and not marked_this_run:
                if mark_corner():
                    marked_this_run=True
                    last_stage="UNKNOWN"
                    consecutive=0
                    log("CALIBRATION_ACTIVE: continuing visual comparison.")
            previous_f10=f10
            try:img=frames.get(timeout=.08)
            except queue.Empty:continue
            now=time.monotonic()
            if now-last_sample<.65:continue
            last_sample=now
            stage,n,runnerup=classify(descriptor(img))
            if stage==last_stage:
                consecutive+=1
            else:
                consecutive=1
                last_stage=stage
            if stage!="UNKNOWN" and consecutive>=3:
                if not stable_points or stable_points[-1]!=stage:
                    stable_points.append(stage)
                    log("VISUAL_CHECKPOINT "+stage+" matches="+str(n)+
                        " alternative="+str(runnerup))
            elif now-last_print>8:
                log("VISION_CHECK: "+stage+" matches="+str(n)+
                    " alternative="+str(runnerup)+
                    " stable_frames="+str(consecutive))
                last_print=now
        log("VISION_DONE: observed="+repr(stable_points))
        log("CALIBRATION_STATUS: saved_this_run="+str(marked_this_run)+
            " previously_loaded="+str(restored))
        log("Automation disabled: cannot infer safe direction from frame labels.")
    except KeyboardInterrupt:
        log("VISION_STOP_REQUESTED")
    except Exception:
        log("VISION_ERROR "+traceback.format_exc())
        return 2
    finally:
        stop.set()
        try:
            out.write_text("\n".join(report)+"\n",encoding="utf-8")
            print("ROUTE_REPORT: "+str(out))
        except OSError as exc:
            print("ROUTE_REPORT_WRITE_ERROR "+repr(exc))
    return 0


def route_demo(destination="corner"):
    """Record ONE short route from game spawn to corner OR main lobby to creation pad.

    No injection, no AI movement, no background key logging. Samples only
    W/A/S/D/Space/Shift while Roblox is the foreground window and F8 arms it.
    F10 ends the walk. In lobby mode, also observe whether the creation modal opens.
    One ZIP contains key spans and sampled frames; no game inputs are sent.
    """
    import ctypes
    from ctypes import wintypes
    import queue
    import threading
    import csv
    import zipfile
    import cv2
    from windows_capture import WindowsCapture, Frame, InternalCaptureControl

    is_lobby=destination=="lobby"
    root=(Path.home()/"Documents"/"RobloxBGDiagnostics"/
          ("LOBBY_PAD_ROUTE" if is_lobby else "ROUTE"))
    root.mkdir(parents=True,exist_ok=True)
    stamp=time.strftime("%Y%m%d_%H%M%S")
    folder=root/stamp
    folder.mkdir(parents=True,exist_ok=True)
    log_path=folder/"route.log"
    def log(message):
        line=time.strftime("[%H:%M:%S] ")+str(message)
        print(line,flush=True)
        with log_path.open("a",encoding="utf-8") as out:out.write(line+"\n")

    ui=ctypes.WinDLL("user32",use_last_error=True)
    ui.SetProcessDPIAware()
    ui.FindWindowW.argtypes=(ctypes.c_wchar_p,ctypes.c_wchar_p)
    ui.FindWindowW.restype=ctypes.c_void_p
    ui.GetForegroundWindow.restype=ctypes.c_void_p
    ui.IsIconic.argtypes=(ctypes.c_void_p,)
    ui.IsIconic.restype=ctypes.c_int
    ui.GetAsyncKeyState.argtypes=(ctypes.c_int,)
    ui.GetAsyncKeyState.restype=ctypes.c_short
    hwnd=ui.FindWindowW(None,"Roblox")
    if not hwnd:
        print("ROUTE: Roblox window not found.")
        return 2
    def focused():return ui.GetForegroundWindow()==hwnd and not ui.IsIconic(hwnd)
    def down(vk):return bool(ui.GetAsyncKeyState(vk)&0x8000)
    print("\nROBLOX "+("MAIN LOBBY TO CREATION PAD" if is_lobby else
                       "BATTLE ROUTE DEMO")+" V"+VERSION)
    if is_lobby:
        print("Start in the COMMON LOBBY after the game returns you there.")
        print("F8: start recording; walk ONCE to the purple CREATION PAD.")
        print("F10 immediately at the purple pad; NO standing or waiting on it.")
        print("If the pad is occupied, stand there and wait naturally.")
        print("Never guess that a pad is free: only the creation GUI proves it.")
    else:
        print("Start a match; stand at the initial spawn point.")
        print("F8 begins; walk ONCE to the defensive corner; F10 stops.")
    print("Records W/A/S/D/SPACE/SHIFT and optional mouse deltas.")
    print("No programmatic clicks, movements, purchases or auto-creation.")
    print("F9 opens Roblox console; DO NOT press F9.")
    if input("Record this ONE route? Type YES [default NO]: ").strip().upper() not in ("YES","ДА"):
        return 0
    frame_queue=queue.Queue(maxsize=1)
    stop=threading.Event()
    cap=WindowsCapture(cursor_capture=None,draw_border=None,
                       monitor_index=None,window_hwnd=verified_roblox_hwnd())
    @cap.event
    def on_frame_arrived(frame: Frame,control: InternalCaptureControl):
        if stop.is_set():
            control.stop()
            return
        try:
            img=frame.frame_buffer[:,:,:3].copy()
            if frame_queue.full():
                try:frame_queue.get_nowait()
                except queue.Empty:pass
            frame_queue.put_nowait(img)
        except (queue.Full,ValueError):
            pass
    @cap.event
    def on_closed():stop.set()
    def frame():
        latest=None
        while True:
            try:latest=frame_queue.get_nowait()
            except queue.Empty:break
        return latest
    def save(img,index,elapsed):
        if img is None:return None
        h,w=img.shape[:2]
        if w>1100:img=cv2.resize(img,(1100,round(h*1100/w)))
        name="route_%02d_%05.1fs.jpg"%(index,elapsed)
        if not cv2.imwrite(str(folder/name),img,[cv2.IMWRITE_JPEG_QUALITY,65 if is_lobby else 72]):
            return None
        return name
    keys={"W":0x57,"A":0x41,"S":0x53,"D":0x44,
          "SPACE":0x20,"SHIFT":0x10}
    log("ROUTE_WAIT_F8: F8 starts, F10 stops; no game input sent.")
    started=None
    spans=[]
    screenshots=[]
    active={}
    last_save=-99.
    last_sample=None
    max_duration=65. if is_lobby else 50.
    arrival_marked=False
    # Focus-scoped diagnostics for the user's REAL mouse movements only.
    # WH_MOUSE_LL events may not contain Roblox raw-camera deltas. In that
    # case mouse.csv can be empty and a route cannot safely be replayed.
    mouse_samples=[]
    mouse_lock=threading.Lock()
    mouse_hook_ready=threading.Event()
    mouse_hook_meta={"thread_id":0,"installed":False}
    class MSLLHOOKSTRUCT(ctypes.Structure):
        _fields_=[("pt",wintypes.POINT),("mouseData",wintypes.DWORD),
                  ("flags",wintypes.DWORD),("time",wintypes.DWORD),
                  ("dwExtraInfo",ctypes.c_size_t)]
    HOOKPROC=ctypes.WINFUNCTYPE(ctypes.c_ssize_t,ctypes.c_int,
                                wintypes.WPARAM,wintypes.LPARAM)
    ui.SetWindowsHookExW.argtypes=(ctypes.c_int,HOOKPROC,ctypes.c_void_p,wintypes.DWORD)
    ui.SetWindowsHookExW.restype=ctypes.c_void_p
    ui.CallNextHookEx.argtypes=(ctypes.c_void_p,ctypes.c_int,wintypes.WPARAM,wintypes.LPARAM)
    ui.CallNextHookEx.restype=ctypes.c_ssize_t
    ui.UnhookWindowsHookEx.argtypes=(ctypes.c_void_p,)
    ui.UnhookWindowsHookEx.restype=wintypes.BOOL
    ui.GetMessageW.argtypes=(ctypes.POINTER(wintypes.MSG),ctypes.c_void_p,
                             wintypes.UINT,wintypes.UINT)
    ui.GetMessageW.restype=ctypes.c_int
    ui.PostThreadMessageW.argtypes=(wintypes.DWORD,wintypes.UINT,
                                    wintypes.WPARAM,wintypes.LPARAM)
    ui.PostThreadMessageW.restype=wintypes.BOOL
    kernel=ctypes.WinDLL("kernel32",use_last_error=True)
    kernel.GetCurrentThreadId.restype=wintypes.DWORD
    kernel.GetModuleHandleW.argtypes=(wintypes.LPCWSTR,)
    kernel.GetModuleHandleW.restype=ctypes.c_void_p
    def collect_mouse():
        last=None
        last_at=-10.0
        @HOOKPROC
        def listener(code,wparam,lparam):
            nonlocal last,last_at
            try:
                if code>=0 and int(wparam)==0x0200 and focused():
                    data=ctypes.cast(lparam,ctypes.POINTER(MSLLHOOKSTRUCT)).contents
                    if data.flags & 1:
                        return ui.CallNextHookEx(None,code,wparam,lparam)
                    x,y=data.pt.x,data.pt.y
                    elapsed=time.monotonic()-started
                    if last is not None and 0<=elapsed<=50.5:
                        dx,dy=x-last[0],y-last[1]
                        # Ignore cursor recenter warps; sample <=50 Hz.
                        if (dx or dy) and abs(dx)<250 and abs(dy)<250 and elapsed-last_at>=.02:
                            with mouse_lock:
                                if len(mouse_samples)<2500:
                                    mouse_samples.append((round(elapsed,3),dx,dy))
                            last_at=elapsed
                    last=(x,y)
                else:
                    last=None
            except Exception:
                pass
            return ui.CallNextHookEx(None,code,wparam,lparam)
        hook=None
        try:
            mouse_hook_meta["thread_id"]=int(kernel.GetCurrentThreadId())
            hook=ui.SetWindowsHookExW(14,listener,kernel.GetModuleHandleW(None),0)
            mouse_hook_meta["installed"]=bool(hook)
            mouse_hook_ready.set()
            if hook:
                message=wintypes.MSG()
                while not stop.is_set():
                    if ui.GetMessageW(ctypes.byref(message),None,0,0)<=0:break
                    ui.TranslateMessage(ctypes.byref(message))
                    ui.DispatchMessageW(ctypes.byref(message))
        except Exception as exc:
            log("MOUSE_CAPTURE_ERROR "+repr(exc))
        finally:
            mouse_hook_ready.set()
            if hook:ui.UnhookWindowsHookEx(hook)
    mouse_thread=None
    def stop_mouse():
        if mouse_thread is not None and mouse_thread.is_alive():
            tid=mouse_hook_meta["thread_id"]
            if tid:ui.PostThreadMessageW(tid,0x0012,0,0)  # WM_QUIT
            mouse_thread.join(timeout=2.5)
    controller=None
    try:
        controller=cap.start_free_threaded()
        deadline=time.monotonic()+180
        prior=False
        while not stop.is_set() and time.monotonic()<deadline:
            if down(0x79):
                log("ROUTE_ABORTED_BEFORE_START_F10")
                return 0
            now=down(0x77)
            if now and not prior and focused():
                started=time.monotonic()
                mouse_thread=threading.Thread(target=collect_mouse,name="RobloxRouteMouse",daemon=True)
                mouse_thread.start()
                mouse_hook_ready.wait(timeout=2.0)
                log("ROUTE_MOUSE_HOOK installed="+str(mouse_hook_meta["installed"]))
                log("ROUTE_RECORDING_START: keyboard + mouse deltas; Roblox foreground only.")
                break
            prior=now
            time.sleep(.05)
        if started is None:
            log("ROUTE_TIMEOUT_NO_F8")
            return 0
        while not stop.is_set():
            elapsed=time.monotonic()-started
            if down(0x79):
                arrival_marked=True
                log(("LOBBY_PAD_ARRIVAL_F10" if is_lobby else
                     "ROUTE_FINISHED_F10")+" elapsed=%.2fs"%elapsed)
                break
            if elapsed>=max_duration:
                log("ROUTE_MAX_DURATION_REACHED")
                break
            if not focused():
                log("ROUTE_STOP_FOREGROUND_LOST elapsed=%.2fs"%elapsed)
                break
            pressed={k for k,vk in keys.items() if down(vk)}
            for k in list(active):
                if k not in pressed:
                    spans.append((k,round(active.pop(k),3),round(elapsed,3)))
            for k in pressed:
                if k not in active:active[k]=elapsed
            if last_sample is None or elapsed-last_save>=(.70 if is_lobby else 1.8):
                current=frame()
                if current is not None and len(screenshots)<(95 if is_lobby else 26):
                    name=save(current,len(screenshots),elapsed)
                    if name:screenshots.append((round(elapsed,2),name))
                    last_save=elapsed
                    last_sample=current
            time.sleep(.033)
        elapsed=time.monotonic()-started
        for k,v in active.items():spans.append((k,round(v,3),round(elapsed,3)))
        final_frame=frame()
        if final_frame is not None and len(screenshots)<(95 if is_lobby else 26):
            name=save(final_frame,len(screenshots),elapsed)
            if name:screenshots.append((round(elapsed,2),name))
        with (folder/"keys.csv").open("w",encoding="utf-8",newline="") as out:
            writer=csv.writer(out)
            writer.writerow(["key","start_seconds","end_seconds","duration_seconds"])
            for k,a,b in sorted(spans,key=lambda x:x[1]):
                writer.writerow([k,a,b,round(b-a,3)])
        stop_mouse()
        with (folder/"mouse.csv").open("w",encoding="utf-8",newline="") as out:
            writer=csv.writer(out)
            writer.writerow(["elapsed_seconds","mouse_dx","mouse_dy"])
            with mouse_lock:writer.writerows(mouse_samples)
        log("ROUTE_MOUSE_SUMMARY samples="+str(len(mouse_samples))+
            " installed="+str(mouse_hook_meta["installed"])+
            " NOTE: captured mouse is not confirmed camera yaw.")
        # User confirms Roblox ejects players who stand on this pad.
        # Capture only the immediate F10 arrival frame: NO wait.
        wait_records=[]
        if is_lobby:
            arrival=frame()
            if arrival is not None:
                h,w=arrival.shape[:2]
                if w>1100:
                    arrival=cv2.resize(arrival,(1100,round(h*1100/w)))
                if cv2.imwrite(str(folder/"pad_arrival.jpg"),arrival,
                               [cv2.IMWRITE_JPEG_QUALITY,72]):
                    wait_records.append((0.0,"pad_arrival.jpg",
                                         "ARRIVAL_ONLY__OCCUPANCY_UNKNOWN"))
                    log("PAD_ARRIVAL_FRAME_SAVED: no wait; Roblox may eject player.")
            with (folder/"pad_observations.csv").open(
                    "w",encoding="utf-8",newline="") as out:
                writer=csv.writer(out)
                writer.writerow(["seconds_after_arrival","filename","observation"])
                writer.writerows(wait_records)
            log("PAD_NO_WAIT: user confirmed standing on pad triggers ejection.")
        with (folder/"screenshots.csv").open("w",encoding="utf-8",newline="") as out:
            writer=csv.writer(out)
            writer.writerow(["elapsed_seconds","filename"])
            writer.writerows(screenshots)
        (folder/"README.txt").write_text(
            ("LOBBY_PAD_ROUTE" if is_lobby else "ROUTE_DEMO")+" V"+VERSION+"\n"+
            ("Manual route from common lobby spawn to purple creation pad.\n"
             "F10 marks arrival: game may eject player; NO WAIT.\n"
             "No GUI means UNKNOWN (could be occupied OR not reached).\n"
             if is_lobby else
             "Manual demonstration from match spawn to defensive corner.\n")+
            "W/A/S/D/SPACE/SHIFT while Roblox foreground.\n"+
            "F8 starts, F10 marks destination; F9 opens developer console.\n"+
            "No game input is sent; mouse.csv is diagnostic only.\n"+
            "Timed route is NOT a safe autonomous route without orientation,\n"+
            "collision, occupancy and recovery checks.\n",
            encoding="utf-8")
        bundle=root/("LOBBY_PAD_ROUTE.zip" if is_lobby else "ROUTE_DEMO.zip")
        tmp=root/("LOBBY_PAD_ROUTE.tmp" if is_lobby else "ROUTE_DEMO.tmp")
        with zipfile.ZipFile(tmp,"w",compression=zipfile.ZIP_DEFLATED) as z:
            for item in folder.iterdir():
                if item.is_file():z.write(item,arcname=item.name)
        with zipfile.ZipFile(tmp) as z:
            bad=z.testzip()
            if bad:raise RuntimeError("ROUTE_ZIP_CORRUPT: "+bad)
        tmp.replace(bundle)
        log("ROUTE_SUMMARY key_intervals=%d frames=%d mouse_samples=%d"%(
            len(spans),len(screenshots),len(mouse_samples)))
        log("ROUTE_BUNDLE_READY: "+str(bundle))
        return 0
    except KeyboardInterrupt:
        log("ROUTE_CTRL_C")
        return 0
    except Exception:
        log("ROUTE_ERROR "+traceback.format_exc())
        return 2
    finally:
        stop.set()
        stop_mouse()


# Menu stays in the *same downloaded Python file*.
# No new CMD files are necessary.

# === V1.0 Lobby assistant: conservative foreground-only workflow ===

# === Life-cycle visual states checked against user's 2026-11-08 OBS session. ===
def lifecycle_scene_hint(img):
    """Conservative VISUAL hint only: never authorize a click/move by itself.

    Trained on the user's 191s OBS recording. Colors/text geometry can change
    between Roblox versions, aspect ratios, camera angles and OBS crop.
    Returns UNKNOWN unless multiple visual cues agree. No OCR or memory access.
    """
    import cv2
    import numpy as np
    h,w=img.shape[:2]
    if h<280 or w<500:
        return "UNKNOWN",{}
    img=img[:,:,:3]
    def patch(box):
        x1,y1,x2,y2=box
        return img[max(0,round(y1*h)):min(h,round(y2*h)),
                   max(0,round(x1*w)):min(w,round(x2*w))]
    def colored(box,color):
        p=patch(box)
        if p.size==0:return 0.
        hh,ss,vv=cv2.split(cv2.cvtColor(p,cv2.COLOR_BGR2HSV))
        if color=="purple":mask=(hh>=122)&(hh<=170)&(ss>=48)&(vv>=75)
        elif color=="orange":mask=(hh>=5)&(hh<=28)&(ss>=115)&(vv>=115)
        elif color=="blue":mask=(hh>=90)&(hh<=132)&(ss>=50)&(vv>=15)&(vv<130)
        elif color=="green":mask=(hh>=36)&(hh<=94)&(ss>=85)&(vv>=85)
        elif color=="cyan":mask=(hh>=83)&(hh<=102)&(ss>=125)&(vv>=95)
        elif color=="white":mask=(ss<45)&(vv>165)
        elif color=="red":mask=((hh<12)|(hh>170))&(ss>110)&(vv>90)
        else:return 0.
        return float(mask.mean())
    def frame_color(box,color):
        x1,y1,x2,y2=box
        thick=.009
        boxes=((x1,y1,x2,y1+thick),(x1,y2-thick,x2,y2),
               (x1,y1,x1+thick,y2),(x2-thick,y1,x2,y2))
        return max(colored(z,color) for z in boxes)
    scores={
      "brightness":float(np.mean(img)),
      "purple":colored((.25,.37,.75,.78),"purple"),
      "left_green":colored((0,.20,.065,.67),"green"),
      "top_white":colored((.39,.03,.62,.09),"white"),
      "result_blue":colored((.35,.26,.65,.75),"blue"),
      "result_orange":colored((.37,.80,.63,.90),"orange"),
      "lobby_gold":colored((0,.45,.13,.64),"orange"),
      "lobby_cyan":colored((.36,.81,.67,.99),"cyan"),
    }
    # A fullscreen reddish defeat overlay may contain misleading HUD colors.
    # Require red dominance in two *separate* parts of the image so a single
    # red turret/button cannot be mistaken for the loss overlay.
    def red_fog(box):
        p=patch(box)[::3,::3,:3].astype(np.int16)
        if not p.size:return 0.
        b,g,r=p[:,:,0],p[:,:,1],p[:,:,2]
        return float(((r>100)&(r>g+34)&(r>b+28)).mean())
    scores["red_fog"]=min(red_fog((.12,.12,.48,.82)),
                          red_fog((.52,.12,.88,.82)))
    if scores["brightness"]<44:
        return "LOADING",scores
    if scores["result_blue"]>.37 and scores["result_orange"]>.18:
        return "RESULTS",scores
    # OBS regression 2026-11-08: defeat fog was ~.09-.14, while ordinary
    # battle effects reached .18 but kept the top HUD text visible.
    # Require BOTH two-region fog and HUD disappearance; color alone is unsafe.
    if (scores["red_fog"]>.08 and
        scores["top_white"]<.012 and scores["purple"]<.015):
        return "DANGER_OR_DEFEAT",scores
    digits=((.369,.716,.396,.785),(.449,.716,.476,.785),
            (.529,.716,.556,.785),(.609,.716,.636,.785))
    white_digits=0
    for box in digits:
        p=patch(box)
        if p.size==0:continue
        b,g,r=[p[:,:,i].astype(np.int16) for i in range(3)]
        mask=(b>165)&(g>165)&(r>165)&(
            (np.maximum(np.maximum(b,g),r)-
             np.minimum(np.minimum(b,g),r))<80)
        white_digits+=float(mask.mean())>.025
    scores["digits"]=int(white_digits)
    if (scores["purple"]>.11 and white_digits==4 and
        frame_color((.359,.833,.481,.914),"green")>.08 and
        frame_color((.519,.833,.642,.914),"red")>.08):
        return "CREATION_MENU",scores
    if scores["purple"]>.32:
        return "LOBBY_COUNTDOWN_OR_PORTAL",scores
    if scores["lobby_gold"]>.09 and scores["lobby_cyan"]>.011:
        return "LOBBY",scores
    # A MATCH requires *both* the independent green side HUD and
    # top-center white HUD. A single color cue was too permissive.
    if (scores["left_green"]>.10 and scores["top_white"]>.025
        and scores["red_fog"]<.20):
        return "MATCH",scores
    if scores["purple"]>.09 and scores["red_fog"]<.20:
        return "LOBBY",scores
    return "UNKNOWN",scores


class LifecycleGate:
    """Evidence-only phase tracker. NEVER authorizes keyboard or mouse input.

    Three consecutive samples and plausible transitions are required.
    UNKNOWN disarms immediately; a persistent unexpected jump resets rather
    than silently skipping the missing transition.
    """
    ALLOWED = {
        'UNKNOWN': {'LOBBY','CREATION_MENU','LOBBY_COUNTDOWN_OR_PORTAL',
                    'LOADING','MATCH','DANGER_OR_DEFEAT','RESULTS'},
        'LOBBY': {'CREATION_MENU','LOBBY_COUNTDOWN_OR_PORTAL','LOADING'},
        'CREATION_MENU': {'LOBBY','LOBBY_COUNTDOWN_OR_PORTAL','LOADING'},
        'LOBBY_COUNTDOWN_OR_PORTAL': {'LOBBY','CREATION_MENU','LOADING'},
        'LOADING': {'LOBBY','MATCH','RESULTS'},
        'MATCH': {'DANGER_OR_DEFEAT','RESULTS','LOADING'},
        'DANGER_OR_DEFEAT': {'MATCH','RESULTS','LOADING'},
        'RESULTS': {'LOADING','LOBBY'},
    }
    def __init__(self):
        self.state='UNKNOWN'
        self.candidate='UNKNOWN'
        self.hits=0
        self.last_at=None

    def observe(self, raw, now):
        """Returns (confirmed_state, optional_event). No actions."""
        event=None
        if self.last_at is not None and now-self.last_at>3.0:
            if self.state!='UNKNOWN':
                event='STALE_CAPTURE '+self.state+' -> UNKNOWN'
            self.state='UNKNOWN'
            self.candidate='UNKNOWN'
            self.hits=0
        self.last_at=now
        if raw==self.candidate:
            self.hits+=1
        else:
            self.candidate=raw
            self.hits=1
        if raw=='UNKNOWN':
            if self.hits>=2 and self.state!='UNKNOWN':
                event='UNCERTAIN '+self.state+' -> UNKNOWN'
                self.state='UNKNOWN'
            return self.state,event
        if raw==self.state:
            return self.state,event
        if self.hits<3:
            return self.state,event
        if raw in self.ALLOWED.get(self.state,set()):
            old=self.state
            self.state=raw
            return self.state,'TRANSITION '+old+' -> '+raw
        if self.hits==3:
            event='REJECTED '+self.state+' -> '+raw+' (missing intermediate state)'
        if self.hits>=8:
            event='RESYNC_REQUIRED '+self.state+' -> UNKNOWN; persistent '+raw
            self.state='UNKNOWN'
            self.candidate='UNKNOWN'
            self.hits=0
        return self.state,event


def replay_obs_video():
    """Offline 1fps regression of user's EXISTING 2026-11-08 OBS clip.

    Does not launch/capture/control Roblox, and does not copy the video.
    Outputs only a small CSV and event report under RobloxBGDiagnostics.
    """
    import csv
    import cv2
    source=input("Path to existing 2026-11-08 OBS MP4 (Enter=auto-search): ").strip().strip('"')
    if not source:
        filename="2026-11-08 12-05-36.mp4"
        candidates=(Path.home()/filename,
                    Path.home()/"Videos"/filename,
                    Path.home()/"Desktop"/filename,
                    Path.home()/"Downloads"/filename,
                    Path.home()/"Documents"/filename,
                    Path.home()/"Videos"/"Captures"/filename)
        source=str(next((p for p in candidates if p.is_file()),""))
        if source:print("VIDEO_FOUND:",source)
    if not Path(source).is_file():
        print("VIDEO_NOT_FOUND: no game input; keep the old file unchanged.")
        return 2
    capture=cv2.VideoCapture(source)
    if not capture.isOpened():
        print("VIDEO_NOT_DECODABLE")
        return 2
    fps=capture.get(cv2.CAP_PROP_FPS)
    nframes=capture.get(cv2.CAP_PROP_FRAME_COUNT)
    duration=nframes/fps if fps>0 else 0
    if not 20<=duration<=600:
        capture.release()
        print("VIDEO_DURATION_UNEXPECTED:",duration,"seconds (expected 191)")
        return 2
    root=Path.home()/"Documents"/"RobloxBGDiagnostics"/"OBS_REPLAY"
    root.mkdir(parents=True,exist_ok=True)
    report=root/"OBS_REPLAY_REPORT.txt"
    csvpath=root/"OBS_REPLAY_1FPS.csv"
    gate=LifecycleGate()
    events=[]
    exact=0
    total=0
    # The expected timeline applies ONLY to the specific 191.27s clip.
    check_timeline=185<=duration<=196
    def expected(t):
        if t<8:return "LOBBY"
        if t<12:return "CREATION_MENU"
        if t<19:return "LOBBY_COUNTDOWN_OR_PORTAL"
        if t<24:return "LOADING"
        if t<161:return "MATCH"
        if t<181:return "DANGER_OR_DEFEAT"
        if t<186:return "RESULTS"
        if t<189:return "LOADING"
        return "LOBBY"
    try:
        with csvpath.open("w",newline="",encoding="utf-8-sig") as f:
            writer=csv.writer(f)
            writer.writerow(("sec","expected_video","raw","guarded",
                             "brightness","red_fog","purple","left_green",
                             "top_white","event"))
            for sec in range(min(600,int(duration)+1)):
                capture.set(cv2.CAP_PROP_POS_MSEC,sec*1000.)
                ok,frame=capture.read()
                if not ok:
                    events.append(f"{sec:03d}s VIDEO_DECODE_FAILURE")
                    continue
                raw,detail=lifecycle_scene_hint(frame)
                guarded,event=gate.observe(raw,float(sec))
                truth=expected(sec) if check_timeline else "NO_GROUND_TRUTH"
                if check_timeline:
                    total+=1
                    exact+=int(raw==truth)
                writer.writerow((sec,truth,raw,guarded,
                       round(detail.get("brightness",0),2),
                       round(detail.get("red_fog",0),3),
                       round(detail.get("purple",0),3),
                       round(detail.get("left_green",0),3),
                       round(detail.get("top_white",0),3),event or ""))
                if event:
                    events.append(f"{sec:03d}s {event} raw={raw}")
        lines=["ROBLOX_OBS_REPLAY_V"+VERSION,
               "Input video was only READ (not copied/published).",
               f"Video duration={duration:.2f}s fps={fps:.2f} samples={total if check_timeline else 'unscored'}",
               "Heuristic timestamp labels are approximate, not manually verified for every frame.",
               f"Raw exact video labels={exact}/{total} ({100*exact/total:.1f}%)" if check_timeline and total else
                 "Different clip length: per-frame ground-truth comparison disabled.",
               f"LAST_GUARDED={gate.state} LAST_RAW={gate.candidate} samples={gate.hits}/3",
               "End-of-video can cut off the final 3-sample lobby confirmation; this is not a failed auto-return.",
               "KNOWN LIMITATION: no verified repeat path from returned lobby.",
               "No keyboard/mouse clicks or purchases were attempted.",
               "EVENTS:"]+events
        report.write_text("\n".join(lines)+"\n",encoding="utf-8")
        print("\n".join(lines[:7]))
        print("Report:",report)
        print("CSV:",csvpath)
        return 0
    except Exception:
        print("OBS_REPLAY_ERROR:",traceback.format_exc())
        return 2
    finally:
        capture.release()


# === Roblox PAD SCOUT V3.3: offline geometry survey, no Roblox input ===

def pad_scout_candidates(raw):
    """Find candidate violet portal surfaces; NEVER infer available/occupied.

    Input: a BGR/BGRA frame. Return (candidate boxes, preview BGR) at 960px width.
    Candidate ids are ephemeral and must not be interpreted as world locations.
    """
    import cv2
    import numpy as np
    if raw is None or raw.ndim!=3 or raw.shape[0]<250 or raw.shape[1]<400:
        return [],None
    h,w=raw.shape[:2]
    dest_w=960
    scene=cv2.resize(raw[:,:,:3],(dest_w,max(1,round(h*dest_w/w))),
                     interpolation=cv2.INTER_AREA)
    H,W=scene.shape[:2]
    hsv=cv2.cvtColor(scene,cv2.COLOR_BGR2HSV)
    # Saturated pink-purple pads only in main scene. HUD and menu masks excluded.
    purple=cv2.inRange(hsv,(119,68,72),(173,255,255))
    purple[:int(H*.14),:]=0
    purple[int(H*.84):,:]=0
    purple[:,:int(W*.04)]=0
    purple[:,int(W*.96):]=0
    purple=cv2.morphologyEx(purple,cv2.MORPH_CLOSE,
                            np.ones((5,9),dtype=np.uint8))
    purple=cv2.morphologyEx(purple,cv2.MORPH_OPEN,
                            np.ones((3,3),dtype=np.uint8))
    count,labels,stats,_=cv2.connectedComponentsWithStats(purple,8)
    candidates=[]
    for i in range(1,count):
        x,y,bw,bh,area=[int(k) for k in stats[i]]
        if area<max(95,int(W*H*.00017)) or bw<20 or bh<12:
            continue
        if bw>W*.57 or bh>H*.52 or bw/bh>9 or bh/bw>5:
            continue
        # Reject areas obviously overlapping the on-screen creation menu;
        # the calling function also marks those frames as NOT_FOR_PAD_PICKING.
        cx=(x+bw*.5)/W
        cy=(y+bh*.5)/H
        density=area/max(1,bw*bh)
        candidates.append({'x':x,'y':y,'w':bw,'h':bh,
                           'x_center':round(cx,4),'y_center':round(cy,4),
                           'density':round(float(density),3),'area':area,
                           'status':'UNVERIFIED'})
    # Larger contiguous colored regions first. At most 12 visually reviewable.
    candidates.sort(key=lambda z:(-z['area'],z['x'],z['y']))
    return candidates[:12],scene


def pad_scout_offline():
    """Create a compact portal-evidence ZIP from the EXISTING OBS video.

    No game launched, no input or foreground requirements, no usernames OCR'd,
    no private footage uploaded anywhere by this script.
    """
    import csv
    import cv2
    import zipfile
    import json
    import traceback
    import shutil
    video=input('Existing OBS 2026-11-08 12-05-36.mp4 (Enter=auto-find): ').strip().strip('"')
    if not video:
        name='2026-11-08 12-05-36.mp4'
        paths=(Path.home()/name,Path.home()/'Videos'/name,
               Path.home()/'Desktop'/name,Path.home()/'Downloads'/name,
               Path.home()/'Documents'/name,
               Path.home()/'Videos'/'Captures'/name)
        video=str(next((p for p in paths if p.is_file()),''))
    if not video or not Path(video).is_file():
        print('PAD_SCOUT_VIDEO_NOT_FOUND. Source MP4 was not changed.')
        return 2
    cap=cv2.VideoCapture(video)
    if not cap.isOpened():
        print('PAD_SCOUT_VIDEO_OPEN_FAILED')
        return 2
    try:
        fps=cap.get(cv2.CAP_PROP_FPS)
        count=cap.get(cv2.CAP_PROP_FRAME_COUNT)
        duration=count/fps if fps>0 else 0.
        if not 185<=duration<=196:
            print('PAD_SCOUT_EXPECTED_ORIGINAL_191_SEC_CLIP. Found',round(duration,1))
            return 2
        folder=Path.home()/'Documents'/'RobloxBGDiagnostics'/'PAD_SCOUT'
        folder.mkdir(parents=True,exist_ok=True)
        target=folder/'PAD_SCOUT_OLD_VIDEO.zip'
        # The original video has portal overview only at 0-7sec and after
        # respawn near 189-191sec. Two menu frames are negative controls.
        sample_seconds=(0,2,4,5,6,7,9,11,188,189,190,191)
        index=[]
        rows=[]
        artifacts=[]
        for second in sample_seconds:
            cap.set(cv2.CAP_PROP_POS_MSEC,second*1000.)
            ok,frame=cap.read()
            if not ok:
                rows.append((second,'DECODE_FAILED',0,'','','','',''))
                continue
            stage=('LOBBY_OVERVIEW' if second<8 else
                   'MENU_NEGATIVE_CONTROL' if second<12 else
                   'RETURN_LOADING_OR_LOBBY')
            proposals,preview=pad_scout_candidates(frame)
            if preview is None:
                continue
            for idx,p in enumerate(proposals,1):
                p['frame_second']=second
                p['candidate_index']=idx
                rows.append((second,stage,idx,p['x'],p['y'],p['w'],p['h'],p['density']))
                cv2.rectangle(preview,(p['x'],p['y']),
                              (p['x']+p['w'],p['y']+p['h']),(0,255,255),2)
                cv2.putText(preview,str(idx),(p['x'],max(16,p['y']-3)),
                            cv2.FONT_HERSHEY_SIMPLEX,.55,(0,255,255),2)
            cv2.rectangle(preview,(0,0),(preview.shape[1],32),(0,0,0),-1)
            cv2.putText(preview,('TIME %03d  '%second+stage+'  STATUS UNKNOWN'),
                        (7,23),cv2.FONT_HERSHEY_SIMPLEX,.57,(255,255,255),1)
            ok,encoded=cv2.imencode('.jpg',preview,[cv2.IMWRITE_JPEG_QUALITY,68])
            if ok:
                artifacts.append(('view_%03ds.jpg'%second,encoded.tobytes()))
            index.append({'sec':second,'stage':stage,'candidates':len(proposals)})
        if not artifacts:
            print('PAD_SCOUT_NO_DECODABLE_FRAMES')
            return 2
        import io
        out=io.StringIO()
        writer=csv.writer(out)
        writer.writerow(('second','video_stage','candidate_id','x','y','w','h','purple_density'))
        writer.writerows(rows)
        guide=('ROBLOX PAD SCOUT '+VERSION+'\n'
               'Offline detection only. No Roblox commands were issued.\n'
               'Purple shape != free or occupied portal. ALL statuses UNKNOWN.\n'
               'Boxes and ids are relative to each frame, not stable pad IDs.\n'
               'Images may contain other player names: keep archive private.\n'
               'At video 9,11s the lobby menu is deliberately NEGATIVE CONTROL.\n'
               'Goal: identify distinct creation-pad signs and text for calibration.\n'
               'No autonomous route until pad status and camera pose verified.\n')
        tmp=target.with_suffix('.tmp')
        with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr('README.txt',guide)
            z.writestr('pad_candidates.csv',out.getvalue().encode('utf-8-sig'))
            z.writestr('pad_index.json',json.dumps(index,ensure_ascii=False,indent=2))
            for filename,payload in artifacts:z.writestr(filename,payload)
        with zipfile.ZipFile(tmp) as z:
            bad=z.testzip()
            if bad:raise ValueError('BAD_ZIP_ITEM '+bad)
        tmp.replace(target)
        print('PAD_SCOUT_READY: '+str(target))
        print('Frames='+str(len(artifacts))+' candidates='+str(len(rows)))
        print('NO GAME INPUT. Free vs occupied is NOT YET proven.')
        return 0
    except Exception:
        print('PAD_SCOUT_ERROR '+traceback.format_exc())
        return 2
    finally:
        cap.release()
# === End PAD SCOUT V3.3 ===


# === V3.4.0 PAD SIGNS: limited text-sign templates from previous OBS frames ===
# Templates contain ONLY the game's fixed Ready/Countdown labels, NO player names.
# This recognizer does NOT establish world coordinates, occupancy or permission to move.
_PAD_SIGN_TEMPLATES = [
    ('READY', 171, 28, 'c-oDa36NX$eaCC<CF$Mw|Nrho=U$RldmD4O9Y~lIh9<z2v@T@06Y#-$FRi_YO|WT!qy<U~Av6@46av&_n1%wKj8oV`0xr;)7%0YO+4XvFtyWq|@40^&ZKh+>nS5q6(i{Es|9{`_|9|g&zq;w`o#{k#V`EcO;{PF?Zfi>+lBg<TSs~kYLKPgxMp#y)IhjnhrCL!5s!JwXTbkn0cuT4^k!njLI;(Vbb+)&)#v{>aG!}1aNwg-;7PP0%4vr35V&O3QwmLW(-86KB8tx7lz3o?S{pK}~KK#JF2M!##XS~YZDjUZW6BFa(V`F3EBg2{Dfq~5MaAu^!o+_EqiLtSXv60cS@k-t3=;)rz@W|Lc^uvAVr(^r8+<o`{iSfN78N|pQR6L4a6Z`h<uS|f-M#uLI4Gv}Y>_J0k&N4hSIDi<u?tuq?a)sTsb-XWPs}Rai(yJ&{{?D;2LkJat<v5z*IbIM%Q4pjmB2=KFDH1@VpgI76B=92COv|b?9lcdCbrqs|o)<(^ELX}ERn=4tp`tlNj;V~zeF4w1G({p{yU%3CcRE{l$21wrnxQG6icw|bSXIx8l~s{tS&Cvwil!N+^7;ZKRaQ;?i>Z-V^b=7KWld2v-9Ss|R0%njCIbLDq*X%iUkKH7y)v1usj|c|Y(*pbz5>TGXQkHR1k)hi*R|C;drlQKY8A&)!nzbzK`RV4>q@9q;WblWWr<gV0;MvPFG>-jPH{1zp5g^eGzf*aI1@sR7fsf%XhMP{tw$6NgqtI}p{Y$u$O@TJ*?>9&X;IS^)ZVkFZ`!t?*`{ghqDeQ9a=psnyub-!kU>2qa16&8oNSOJ{}Ya>o+~vj3l^_Kkwv>(2N6kTNYOAg#UOw}vvQpg45fUS&DYlWLx5{!X$gd)HpiPr6sQsqB>@^bRBXa*Yk{=VtVSc2pg>WGa<pX-1|WhoL#qi9sFo=Ue8QH{((}4M21v%w*3k_F%P|<-kV;^5J;P!@bqwWPsem_Hc||dTnBP<wJkE!bjWW#w-jT5ShK>V=CO?}_VH9g!-v7*G=|iBa8ZQZEge4_bro%ET$s&VhaWnwUSaUP9(K1yo`=$_-Sz44-4FXvt4G0ufv6@)b(#=>z3pkW0V_WXHUZ;7HC4>#BfgoFl;l#_1E}ttEYL-E_Jow57(;xii-6yeR+~8>r=oZ1Lfz;#qg_7sy(n^i|^nWjVtKO*ur9=!#wbe!)hD_Fy&{ZWs-83CTv%(IbqG3&poNaR`f>UvkLQ5;^D%w$sZ9%jTY)6HvENC(%0Qzs2j$FdhGT?~cNewXdSde(d(crmKm8i*s-kEZKF}J+D;G-N>wJg9(PB<8RV%b}s`{eZ>2kV(f=e$zx#QQ%Ic@aR;usM+qI=U)JVTEJSEkZ<>ilSKYq!Nv28oC$6L8L_hCMMI2?#Kd=(Uz2raHA#bjWJo&Mb5y3)TCR!geK8tNpDES1C*b}gD-uFR2VX(&=sE@Uwhz1cYd8n$UH^!JVQo&?9C^<WA}Yc+9VN)TXMyt``a6WI%QKvRA)7j0xBsuEUcxV#L{Gt)?y)%5)4kWn`upA8HJMr9IfNJR$qhabwd$>!ut(dY`{!|fDJSdYYv?*wgSjtGP@y_@{<9M@E`h;4G`93Rz6rL-BNq$`rM~JyFPjA<NrB%@FGIjMsuaxgN^~~eE4IfwcAuPBGv<p8vDULG|>O*k%u^F)2wjA51)SGpPzq<Wzu&aoqGC)mKx!E4?p|VzaIMOKi-cimw)G%?;hHwkR1J&|M1*1Pu_Q36adz~;rX`@k6aZn%-ZiQXH~_Z{R+7um24mbEarddOQgzN*cM(mT?~P(^VubT$hh}ZY297>Fd1au@mBsNJ6}9}8PA?r$-gq?tscIX<eI15-x4j~SaY)!&>^sYP<9sz#hKvsldikCRDOUGX5I3Ku6x|g)oyv$Ef(CRzp;Jt%(|N|xu5;qtd0Hsa&fuf9&KVU;lSE_02e9B4*u>AfTU7^z$=cStLFd>C!nvK&f{uZF}F}h4i(qEM-Jx;zftPv%B5m{-dmlHH!QBsl}d}=i4Qd+k}G_|P$!m)tH9!UDEwl{edEPfp9oK_ufP4!qL;lf^61O&71ozt{mI|?j<35%MpkFt+b}toU+*7%&s(~j-;?(i?|*xJ`u&J6v_1Pjem~9OvVd<8q#G!-SFQ7<+H%;zbA{h>da|%`svdkko4-A1O=ff3>b=D?yHa2MV5R(ro4hISpb(q&X0FlfqBm9h_*~Xq<77@!;9J?L+Ztos?rHC+f=^^izw))3ZN;S$35A{c^2?ZUvpfHmNX&RAsrpGT`<2kKa`rNvc_&-CRu+fcV|cx25+wC|NELt;ZC_b?ST+*tD>FnhS|pMehP}eUO*7tfo!@_ddHv4X?7~cKyk^8JJ;b$mrQ<iDiHmED!~=l8S)BbdnhX3>Ih)~H^@YMbX-gcs#rYWgXUl~Hn8>&@Gf<m7lRf@Xe)_4J_9bsA5U+bCH}@A5`R(G1fJ66ZhCffLe*Ok%0^(m6+?zBbQO=#>dQMM&qJz-ACrcU3oBKct!9j2F5&fh)$yu8wmU8>ZxSRX*zltxvwYY}vm4GEDORINU4m|X(*C)p16)&eoT0u6y0y+JcS$DfY(XKmBVda&N+%wDb|1Ms$xV*5*!FOcc@5@y3$JbF>5ElV+zEtg8sg@InzELb~){JC1H%+E<u4^{<e&$Z!D|}SWOMl?|(QGy&9Vz7FH2GMuJO;#-;>z55^P3B~id2UFkF}*+cs6)={q(`+nx6dpng}A8JH6zm=x5i;53$OHOP`<C@EPySWfxDDX7+b^i=K%${Jb!~O=tYAe?$P1lDPWwq-y6$Rq@{MpLCCkikT`cpR6-~J@1Y?7oNy^?ZLgS_hk6WV_vo!+wHAB*Kp~==`%^g%#{kIdwic1atz>s6g*ta-^R(t6>j;H&blXZ<>xge6<f_`g$Q@8o1Y@s`_|kSo!YfCC+JP1OXc?iM+%=0%UvJ4Yn`g_bnd0C$VSlQ`CUC<sm>l+b>|OAz)Iy8Kd%>WoGz{$n>$r{76gT(*)vBzEuMMK5Mq;SGfS)4sW+prt+cxIYd<$vTIEzugzW1`Dg#aKy`{COck=Gcm6~XT-f`!790QZH?($*RJ#vxAte1|x{`za)>H++Q<7?ipmfh@=z~Dc2%Qp)Oi?Q<WA(a;j3x#JQ8gHd?OA8nXeCueTl$&~ir9t3=U$~yT_-aCGP<v0F@Mhh&n}TdSw>0}FHOi^gW#9;$s2pBgx&wJwsJt=jx`j`#poEkqEU#xd8M%Yk3Z?b=6MxDw;PW$HY2BNDo^7hxIXC64O&yN;DDlJTkFUUGg5Zhsr23<}VcL$Rf(`c%V^{TE-y}E&7rpvh7aNe%y1u#V){9l1CF-%*)dM$vB}|jN$cL^P?z>c`L?M3FoqwK`<ged&b&QrZg1M~!_B75XEYbMd*uiZH#k5s5bxq&3;h?|=oNr`yUDKulk-F(SyGMp^-U1|5<dWM4c7N3lBAecQW0y&>5*rL`P$$zqlCOO&oRkzGicr;!jjl3+8P!O}P&rn&6%j(7Q$itt)dxuuCwW;F@Bog?L{PL09zEk(7FltMl=ZMh`w5Pv1e7U&z#CA~Vl7c48jqS#jkf7{P!s}~BB_w3ky(ML$xwr|<3Nmnkl?WZ!%>{(h!ihU7`c%$@EQ!NIQMU1Rt;OoaT=Djk(E^20-_O#SkbTo49B!IWS8Yi5<wY5qJtE#=qTg><VhK5MWUtxprV>#MU*sEgtjenf)R~6cC0ZZ1G^>cSh_6G$e33i;mFD;hNfA%Xoo|l8EHxChOWqpgj~A@VdXRkT3`cyvaSjd$9$X*dm)BKuY@wdGiDW5QF&gLSpw<;Bk<_C!SXzZa!%0i$B}=hQ5ZxYgQ&GA39$@HLc9b8N+JnCz=I6QLuC1(&Y^r|pz#``kw`oqacG_n1Za+;1(8Qj3bd)uHXp?kmP3J!!&t`eXILDdB}Nf|+rTIKxJIA;!$g0~Ff1n$4Lf3$a3qYJffWv;9B!DF6Ls`TH&8@{l{^Shm(f(Ji5e{{niaCc4(gJvp+t(L85$3*SW{y()D|<$cxzMW3pa$8K~|9^QYx<7FrAQX8CvBs3B}Pzh2x+g$$BNzQplqO>QEf2!q9;BC2zg3`>tC|MPO)_<2N#}z)5Hav1lns5%R2vf)C5HSRF=?c)%YdNX#D~QM9Cj^%xIDhUO&{wRx5id353OC|`<|h%H&#*(lA};aIG)$&gPXNrI#~9z}DO!qEvUre&HG#c&LP5y(B!R6_%<f=X}~II2n=sRp!f?~^b3<KYJ%xTo^>!B~Hlq0IP!?~ab_%?yp~+rM{caQDE-_`cD>UBd%?J9hL9j}8tF4QGb>?;7kM7@3&J+%-6~cmH?CGlQAY(cyu?{#|<~?j9TJ&rJ01*}s1@li71uUtj+~f8Vam$l%VMLwoo3?H<}QHnDGi->!ktv7x(mjg60Hh6eh!j}GkGwR6Yr%+4L#x9`}w{f;}U3~sx5<gr^X=-isQD3wg5JG;9&H&@wmL1!w})!Wm1K~Fl>(cQDTr!$>QraRN=_O70u&i2mk-ky$BYfHMbE1gJoU3hUvYg<Qqdw06Mdvi~FTYGOuBH7u~)!x>DsuEonZRt$3rn|bkntQjT+b_Hzv2{y#N4l-O`{K<#o4eB;n|piPTUtB2+mr2`9i3gBZK;l~j&v&7nyhk3d~>|XN^ITwzs4vDas'),
    ('READY', 169, 27, 'c-obhX>e3!y2op(rbZn^3<)7yr}wk(OP_Q4bY}%2AZidDK?cVS<Qgsn*|KyxA%rZQq{&LQ?j#Vh2nZA|qu$aQ9UZUU>p18XT4;c<B!oanLXxIC9q-#Apu^~g`>#s(hdh1W-+7+reV_kZU0nlIU9}I$U0LBOD|NYR_ct}S+^e>x7Efbib^ewu+a0;vHvPx?7hc_6Q(xauS5sA0U0oge`xouIBX@<XIDgmHtXXZ}k(IOawe2}2u1c_8W#!DOrF)Bt9NC4HwT+(Ew)Qr!$J^@hc)gy6s`6}y)0vx{om>4&pbftO+TJ_^>fF3#2LR0gpc#AW>gyW+zo6Sfpj)@+l+J>>L#vhm(A?}j?%GE0&p=xNs4FY?Ht7DsHHnLt+H7gb$w^5`iHV6xqCIt$vM6O~+LA?&EMNA>vb40NOViSpB`--&wLi9mWf(anfoBzgwj`varP)(vwdfut%{(pv$Yzx-qHsr|C<?qFDNB>nQkL6NW>!tG+ieMoMYg9bUsc%JeyDYSPm{O3-P^psVo$Ck&yfQ_pI_<fbnPnMSLkw;m6es2mR6OO7w>n~R=CQ`UFDUbi~#N1SLH6Qbi3ST&iu;iVrM~Nev!kur>LUZRWU2~J*um#tF5iAsi^}gcUORC{UleJt8!miQBhHCeNAyF3{<qL)?HCm*Vx{(eVyk(NBf&CA<(A!io)Ey5NJ;BisLW9WU`GD8HS;0ilT6oGVw~XRkbQIPm#36B1y8WC{|gdNi~6h^g4{^Ndz+@6eU>2pJnP_grO*k0AVNsnG8CeVOBc5UZ>R>%&cm&Fd|QbI0S}(j7Ef@1#97sB2R10!Fo?yo2RkPwc9ZRn(J^_IZonXh(c!`48uI9P>jej94jcQqSzRQ<#=8YRF1MrBpi+!HL+TKOxVH*9Z4}9LC%W0M^;5q<d7thXKC=pv!ZC4BuIu6d6X1VRTjj_lEo5QQL)>T7N>VS+R|Cq)(t>g8fwb&0cdVcj>Gwmlql+r7SSMuqJePSDhUakDq1W850+4@Han0_q=-~50%D_C1=S;_2(uQIWW_2fv$EbJk{}2i$1xlWWmFFmc~?5E&S)lOJBOkS5907pR*eRj;#f}9H>9<{-qPl2X>D!ZUtN-yHv^hi@F{D?6Kp7I3uQA@0+!&6v7#0-khDop%2tx1K~s<fCSs56J&-$(2)o~~=;eLyQ1S7gt`v^V3cp978+e}QI6>eTintpVio;Nhq~l4OSxHRRhr&3pMM;8HY^s`&up`UcSbw0h#p`XV+qXB=qPf|*&fV`zERLXvNzbt?8|qU7Dl#iizVqRS|9w0&krz3u3estnCF%I38@}LQ@mTED&jOP-r<bsVMYh^x@mB=8VJ4>(iKDRDWHkLGqrnIvi)b7>KKP+X&ZZQCFwhQywDgs%rpCrMI-9+o##(n#&g~Y>FMNw+L`C8lF7&3M4M52%`TW&ezR|$>(qvYaLpk9Y693rm8^7^w&HZzBou8hbIQOw?Hn0|v!<b*u?2FG-1MDX=GAjrM*k%O75KjN0?;lza$AmU9iV%V%S`@ixZP(G-hPGypry&IDybZeN%{xsFqDhbdjOGM#$Js!3{`ja%pkc(O*v#l6Ixld&ezo~`Fa-Bbf09W?&(qI;5L?J7P&gTd$qBe2CI)!`W=%Y0v?b}{ljfPi&Cv_=@g@ReV0nHdPdps8@PUVPIvs|@8Hi+(#R;rq_)-+uUSuevD8ULMsF5{yb3<2iTl)b|Q&VkOfiqP3?7X6~yP&swks^7)ARi9Ak7KujxqQspj$xnw{l(mZF9!a1S@x@nIqZq6S9U(XabsAR`IT$^T48bjciZd~joU{qjEoG`M5xCGeG_k`=uQs~4_=;_Jgl+@#{C1QlIFzjKj#YsPH&3S&{<#K8akVyON=^x;XV2;C<#ENS<t4o_I6KGV@>HSsPo@INdi_#@vA@qGJhcG#Klj?Ze0!xo{2(&!SRWa>q9Gvn#svq*GGrnohNO$J|+J4n<?K;0%qlxCPycNqwV&0eZhf|sn6z~@=skK2?h_v4h;Qp@yys)=HLHiI{5Y9r~5M^w+~H!-4`6nLSpMD_vn8PYLOJH>ew;^+Sbz4P*t2i1DfO9>-wqmv$bbs8Xdj$qTMtYbl^J!zWNBKe>jUDx*ja-o*Eszui(ew-rE0}9^1fd8}R)$JJ5f1GcL;9OMwdotOj`@FyPTTMyEERy0XAXCPut+`R3X4pN)<`2UYpbFMzHGUsb=Hyof0uPn|LITPL%zJD?cJi2zg$fp#{vwzal2?speCZ-eF+m)`{q9U`HFn6dJ!{G;~7h+uFt|HhDyP>9P@-RK3MI}AQJ>O=GVmzUqK4qxedaCcysI5RReoyUNQvF_Hm!)Qo&H{jEoq~1VJ47?#Qxn8e(`|98Nze27~b(s$bZXNn)>MUyx2HY`r=hzLals#TxzY9unpz?}pn+5eYH`Z6|&dYZ=a&vMEN-BP~nZR`6MA^ohT%%(s8-6Y5AU>KHjgC#cJoZs^aJ-gK_xL8CIy5+{)BPqG{9IQuar2-455^~7gD95X7@W?fOr{U6j%e8Vqv!sPt=JS8eo=zHyxDi@%N-LFAJ2X7((v%~jjL&o2hTetxF|5Ogh=``dpDyv#alp&s<yl>jh(<mfy&pq@*Q_TEAN6*)a~!(X63*9XIQ=A2fthAnYu>X=!vQJIir0i4EmDsQ8r`j3OiSGqyM0B$2H&gm+l)M-^H*3zrOdz&SiGE%YXe55xMCvgR$o)ee3zyxBhwR;^3uILlwGK-!0L8X5tg+#&|u<wq5b1LPVL#d=IG2o|icT+T7GoQ<|4M1M1jaTKTih1f~OO(nX-}1a4-cDGPm5dyVV9pL&1UiEC4TL>s62S0;ZmF}PsikAv?qr6W@ttQnJj|8wC1pF<#NX5CcqPYe>5*+22F`nLblv$C|)=U)f$KlELFzv%0sFPiaBZVuu2S^t&apT6!-fBEWIpC;<BlOOQE0tzbMP*dW_xdZBck3tDaVNjH2ScZVKu~EAMfxpNRbHe%pIdh}jV>hn_ZnnVpAp_(6SAu<8Vxb*pe;o5qoz_8llL0pt?mwT$&^WVhe6$23QG3m0|Af!it{4+ChsW2F&wu;<*-78U8<#uD13~|_V6bm9_UOlf@saWVM~(6Qfj$Vd9N+{49M~z571hNrZf|WZ@7eEdt}An90o#<5mF3t|UUkwg(+I}PGDV<fZA?^zY3HdoGZw^B$Xj1*j`^MV^6=PK4t~M>FzcbQ$<Mc;5f5?YeLr6FsygEn6;)3|T2IXyMx>DB?tSTm#2c`z&#(V2%NV&50Ve1P_SuWyz5DsMpY`_jz^@!U($iJ;C!+>h;T;=3ycC5k#UIp0gc1sj9&BZCMoqR`u#MY~)V8%YwKUb1I<s@YT*?CHeR<UzMqU*eo`GosG3w&A+WW&b5fM=_^M9|8j)>D}!tYzC37fkxE^>ip-UG4mks3L2&Ya)e4@@3HgTad92nj>HK=G^r;dzORgD?|fRe?EV1V$g5a%$lCqfq9TpO(WWO_UBZEr8;p<09ui97EHX5G@K2I1*79GMj)K<|N>PRp&<cpUd`pn;NQ13mo}{A=m8OTT%TEcnuo|qNAfC7e;CHCSF7t`jM2RRIA0Vg3-Iw!dfL$jCP)xBB1D4)&gMyW-w?V*@~D&yMQ7ja7mylur(2<lWZVCCIe2H1>9)naXRnpxxUk9hTl%&Fug_(hiVMbR!Lf{(1{6n45b1m0ZvAephT-xpeZ(aMdq&8vI}?SIkL89WMu9LwP-<!yQYVVjfgYpH2TP>7_AuxX^@yCl!j&0B&ZC<2^J!5et2|TjB1lPOcQN1XySD`6Qt8|R-U)Xn3WYJniWYqs2#<y7Mx2^NGV0N;Jl#9tekQ3^rgOP2{K@ShJdvYs)?c#=operAQR;TQ^;ij%W9@Evk5ZCM};*f=d6A;d;R9k85>^O@Sotyo9iqr+gF>BlM)^l6&V&`f-qW8?1_skX1kgysw-@E0eIxNc?%6FtH`X#GlWs2Gch(<_uxbEI81_<kT?tjzas^k0?`OCFgVLutgO+DnQWAVnNW*fMHveU;U*Z;#cEN^Od+H|8gW|^4<W2T05b*blo5Dooi<);BKY*TupQ2Ij@Pzq-n8+RjBVf!l9ylPs;XODzd?wLjEqOMI=u<TDVpU8LKClnW3@!&Ly-%Nh!M3&B&DPP=Sa~|csvBbBpUOu2nJs0HU;hlpme|}C^nl-AgNT&h^UKXh@_J&7CMR4D2bBYibFWKd4O9OgJ292&nI&<0wt#khze#mn29JH4>L4I$cqkGx9r-u&9QY;#>SUl+^}UQ04>;CQB(gU{bXT#*TDlF-CbQ>Jx5QRJap`McSldpfrH*djfYM)dykzs)^n))=<$O+Cl0r?9qvAMq`kGX<G_)wp2M$qb@m+TJkry7xTovrn;nOGI*y#|Za;ebNOyb3$=8n_@f?5Sn@hvrecRXDd+EZ!x$^^{TL%Yv2fjbnaiXXF*xTMtPiI$mcTZ1OM|*2WoA+RMM}3KX_wKz_&ay&hUiP-k?T$SThjVu^0A0V;@$w&@`NMN-Rz1CT%~NaFrLS4NYKfH>)wJ}dSEZ+?KmO#CtAN1g>StEiEo$nLM-r^6z$ZPi>Y3HgJhf`(zrUnM*Q7oB+&_9RUpU*_ck%qWzVml9c;!^@W6!R9GW5{&Cmvt1V#V@Q)xIeGnLn;w{oEF3tJe!0iKnTqx;ST-!wF2Yv#_M1s^<RywY%|C'),
    ('BUSY', 142, 27, 'c-lQzd2Aflecrj=+_U$6-%IZDSaL}&B~rXZinPe(O^T#sRX(IxmK94@oH&kr1aXemNgLRIB(RY<&Ve*`(!yvEJ4oOJDbU)jl(bP4!BuUY6e;e(z0aBHBW3j)V1U7U^WOKq-|zhnwTfpc002SYJHYM(pd3zUSiLP8Z0|I16rfm*$>wkv^cp3{P!vwG9Lq2)Mxz)YFq|MsKmdU6EJHFJ&+-6+Uuw0*Vz#PrLT7h3+bnI(dR`z^Mn<ht8Vod`0ia3RH8?fq;939Z7>eA(eHI9M4;V_KsEXxTyT5Or8AlKlkQ4;m6H-QZ=b{+oz|w%B37%jCrAo!_9Ejx9I=x=c;sgo|R<GOP)KMg_viQu}h}&r}a-4=BIZmeo7_qyTH9iz)P*mghLLw**XomO{=zS0r3N$>ybGnvJGYK$?<7r5UVHlc%j41d9Pz0K#cc?2J;ogD4Js~|5h}Bvg5L$-9X|vVic6rSlEAURAj&AY!Z2_0rD!^~8hJfnfIEo5RmjM8Z0qD+Accr+89df%5LZApnGl&@jCYO=p5tO7!NM=`;-Kl`#RXStH<7Oz85NsVtEG#9uZ3K$ZI-AR7cj!3^!*xc7&E_()lvZd8X^1^>o8W2k_+4I;R<D9<5Ew~fIJF}J0gVC4>{<%{6yQ@(EF8vp%1h81y-DEEd&b$BK$0YZ>m8Ba(W&|6-j*gBXXs%6#O&O{{BW2i2;S`R`&?cdR2CSVez(hS<!K||(Q2ZmXML={tH~c|54xR30%Pc%LjsD#Nt7^!eE0Ss03@V96bi-vTZ%+ADimNwl%X*J;P4+n(ll)}8Vx!X$KaeZHZnOgH$T*`A(dQYa$#|1{?KF`9+1{KTu!^o$Wzc4Y%ZJCX`pa5+7!?b(}`xfX(XcKjSiDZy`#mhk1{;R16A9>vHREPzBc#08D)h?h@?;hsuwVgN(~2St<4R+z+u+103-D+BeToP%SR6$Ffl47JhiwmHN80A$pOHbJwA`uZ&lLJ$~L#n<}owCjI}hI>4iju?ON^EW3*naS7Rtm!bv!9w%aJu(4811p`(xpK~V^cu?Pa-g8%{{Gzi_@%+ZJ!!x+>puo$Eh(CGtCm&4=JqNtAOo1Z$oI<+)6p;r;CV`+YQdh+O6rxGIstHsr1wL7&qMggzMYE^1<K+RcO0XaSqWMZ@Xl`4wSns^j5gsfH!bp|Xx4dBKf7+^@C<QW9T5FVuvTtHwb0Vv8tlDsq60Y@}G-on!;t063UN3b>Q@iaMk7;m~~$ERiw9z8T|6lg|RURXOcH9ym%MoHZ7ZgKZ}HSoTZM#qk&ObpNmomPvX=a^U7IXR~12)$OvlUk40WK;1DhtUZz?b!6#t_uqY%b*&Bgt|}!f~YkBp?LxLI{GPtj@Dw7Kynxkoc@5>9`M<%8tCPmduC;MZE-xYWG6_0PmE12uO40)bcK3*A2>KWF*_FT2q}RYv-|930u^*_x5;7D^ty%C`EeX|uv)Jf<-M*Z9R}>p9zBKGhUdpVf93=Zt%Dyv`iPBIt5}4gcWxPu?7V=#$zefY6w;F{3Iw&<;dO<Zy&e-laax!@I=k}F+{{V~NvTwa78mAb=I16S7ay4EOH8dM*5>yQ$4sOE-I`$mp+h|(OCZpy<DGqbXw+sF1RApjRc4On)fT5ogIS{e;cEJZmV$J0a&8UEg3>Go<1$Jk9Bri#A>7kSA~dRJwIm97Uu%=kYqhpS3?#{`SC{$*=8h*O!qEAdk%i^)y}iSeE%BkH#MHn*TeKxQzBJZmK~W0hOo9~+_(-jz+3XKAw*+`hr_uAk67g9Xf;YNstbk|@N=hurPzV*Bm+Qv_f!GZ`Fc07Y1FZ%~&=uqfhe1ao0*q3DW=FKm=di0_(8t+@)kh8=JusH&=Wxsx?AqJEH=tEo!z2BD?LG1CV8AQDtffVP60V03oXcxrQQqzfc3TKkhr@h@0bXZTVki#t4TfqcgsX4M&?v0BUd<hb+Hk(<)1MhLV<e)qvO$EUEUq90U0U${&Dj%sd@7I4YH~N(G<L1p+T&iF-ru!w>hY0g1P=!S@j;KS+0Yq?=(|iLkC6gmm^^Z7-U3%4y;|CG@aSv@%9Hv|t#$tw9-B2I7^Q4JaPsVOlt!S_3OL#)XDTob16#4&cof0=zPp*u)v~`BMUc}{_JWaSGNn5wZTQ45w~HI%omV5yCTrx`zgF|xMX~x%(dmiN4{xRGnGX_bjmF&B*Zb_Ic)6v+w~?w(I`p>q_e+J0_(m%Wmb2U6`(aTOZy(k<oRPk_b7iUcMh}V|`b$cx=Wl<f6N48TF`W=^-sVvrH<t7ABEZhcwTxWJRsKZaXXI3xL3M>{`Md@DO}$dt5=(^_TwY)38}-~)p^?m_G~SMnDy4O)u~{Exfogbq^jrDzjX<xhUaTJ(&{F>{NyVI0e$UK2D5gtNsxED>N7z>HUq6z{RVno=mYLcXvuSao_Kyfnv^q6^k!AV44=-I>FUXZCyTbRc@6RoMrC!^LF)voOZc|23kxGZ+k>M+EEgb%Ns&SPzS-d|;iNAdD*Oj|B48&`Nt>jB*{;gcSpu*{3eDI}YBiS<+%-pFTCAc?J(wpP`Ka$gr+a69yn}7QJKO_s%YlQu+s`#^!m4BAg^T7M{wI<I`>f&YK3U%~aKH1vJ734yuQmt0zw3s4@acWOe&K%dT-H}rq#!2aor;Wk=ofKtwqEKtNd`9KPY^KNXTx08FmduKkztv&~vZ6GiwROhh=SsEfLC)Q16i?W6o6?PatZ?S$`gcta=kv)Po%)-p(kBk~YCU&Q&z(w%uP78Sma#7<>zACJW6?=VQWoV*X}ciT%Jmgkz^T6dR<a<ME01dy<ovB~o&91tDJ_9WbMMQ)O^WrcI-^%3Nhyu0K3C4)K)S`O*oSl2M*a3P;ojv$$B|;H@%m>z*QjkTkv{RRbp7&w-4HA98W!p$84rby$+<ETmHtQC+T6TeEWG2lIue!3ABmp~#k(fjM%A^-?e&?xvG%^aTw383WB-y%%Xb=O`6-3(;)X1z@)@Zzq2wOBRLF@p#Y)}?1XZQHP0=r8t2dC*%J$t!Us%7DEWX$?w6?N$;&;Vrbv;?nG*0e6Al?yElGw=R-tAhf7uWsK>0{NDgbYd-Zr*LA%X0mvUG2S3)<sEre@`IRAMetZ<&vya(3l}B*Ny?=S90#{33^@3JV7%{zpZWNrCQ_GaZ+EB#OH?FD&i+r6p2XdzcV7w7c2j(4Ho6h!yN0pUZ|c)Oidq}A3d48Bj&1&d~){Dcuw5@?3d1*J$df2#EC*ybjKrKlEigGur6i3cK-Ye=bxU8?i(LE{@GuY%BlVF?y)xCAIq|=P*4hEp;UiFVU{-<eG23Hru;>OR9HriKYy-V6qmpw`NB00>A6yrl#1B7QvPL=@tJDwW3A;sCFzx>w&iQp^~u$>+2yswm~rr_vtLLxN~dOr*9)6pjqV?v+S5IGB6+RYGv4&WWcH#ExL&*YqIc5o4K{h4{+1c{;9WU0y*D=A9zUO!3kaz~Tm?CGNXy72>H9CgAy<k|;xN%Ux~<I_F?|l5uI0DC@^=@c@>a-kA(s}P#7)mu(szjPw{zv~*MI!q<;rF2_@U+bndQZp9SD}I_1c4r`@UJL-~Qg?&%Awp`oP0A@$$tl|3u1&$5pm3*Be)Ue){xVFSR3c*Is|@`FCzfTMzX{2ctt>>vEA+(6ml&<Q^n#UlXNNIdx4+Jq=TqxjpRk+!D7}5Yr#!j9mX%lJ0niH^jz&w1?GCRqA)SuJ}9Ix>(ND{}4BfFE7p}R+dH_BxcK0D-W&qMSfGRrAm#)pL<%C8r7`0E*8qa=Q%3!t|V>dMDfFJ)z74St$Iyr{4~_l8I6Ww4e5$af#BMWZ1zz^G571+Qtq{HB-2m8gk|WAd8{|9+edh0^>SMJ;HfwBxBM%);>Cwr9KPqaiyyeUnBc3q^vBt^hjhw)vkQxJD|0>)SH~`GWKS*ZYn%A{EBWfypI>R)dpg~?{9aP}=uNAC(1NtQdMTH?cJ=Ej=J@;7^_qC~-2Q!|gL~u6PK~P-!7-c(`MOw`u&}t#2oT;3vjw8+=x;W~HBKF;V}zlo2^NJ$qx0aR)72NX5*k7PqwP_5U}DjN2{;!&xUe!eGcs&}eE=+p>Apa0Z-+2)#O(}gz(OOPQQIck+x863w`fs~q3gkT#N&^J%%*|W9=kpg8yXrM9c+eO1P^vgE?8md0Sc>86^9@U%$sy%DCRb{^^Q`w1F=z<l3~!k-j)Ndw$2V817Lp>3&%r&aJL21+u6>M+10rRdYvTf31PQEGR&U%%=qfuz|bBocT}o~NNm7wh0PnH*6x&<vG#pk?tu<hxXl-8jo2d{T|<-m{txJ~VRH'),
    ('BUSY', 135, 25, 'c-mE#32+?Mna8W|?&)KW?zwt;?)#pe`;_L;jONl|$?|<*d@LBJh;1by1jvSkB}<lofep!KNhnyhydkc_ggAjX964CBUL1!C#5e{6wqtzASh8fv8qKgR%9Tp~Ro(TfU%&VL-uHd)y>D`Ia`KCN_Uzi!%7pzl<dfu;6!bV;Au-^PJ_I7ss2C21g27-Y6b=Ofe!tffl|}>t9*0+Y``k{4$LDiet*!uXb~**#Vi%*WvG&B!NTD*adZO8%&5M39ok^uEZi{bZ!{~6m(Ha^VT``u9`6Y_UJ9e!uM{GKk=7v-^WVKk_iDG}+Xf#<}UY}&iZZQc4gJ3cVdYw+MRH`(*L9f*b7PCRasY8*l*J^P`^0`V$48@~@&gtV_dfuE^yK^L%-jsG5j8=<Df;2n(S8mwSZnv8C!CGy@+KFY1T`OaHnxts_hF};*mIdRK!r+U=F$}{ghG8g@z)%E+AykIL5F#VxtcsHQSiMQ$Xqn7twHXvNCkQ&bO(EB@Jgeae4#7};qR%E%MR*z`WH5vw5G3Q%!z-$lVm=*@ijnZ=-YAO#BO|0v@b3i^B#O!fD=Jxr5$S;;NNQjhtyGXWt?sYYvsN0HsSOq*OTe(f>M*jjQYYwKULEhY3M{KbIT(jY3dLy(ArKj>!cmHZWNINbTyHfSje4Weh{gP0-Ff#|SVhp3!~lVEkOUbB!cdF=K}`Ccz(KVN!ZDP<QIa7P2#LCit%<6il_O$(d~{Vwfl)4lkuy;k;IvtdN<wL|!)vmfFKYAY4SE=0<TNNlXxtdEL(D){4pR`y@SbF`);}<@rdp_v){5D$+<H?%qrgEBWn?&rfm#rQAQS`<P5}y>5|l%@3?*bZAvd^`8XknmV7jqxb;ZPh;`rJ%^#LV=I&^Ng6(B6UMsML|7~@l|%h0Kup4IqTJMX-$S@HVxh-{!{gu*u$5KyuM%4{L0E}1MhYV~G$usSe#Th5J;1Pm@a1EeH>NTPKl2oi|dtOB(Zim0S`GI}HDvsf7g9UtAeZOf=tj;6N`w%6{E)4b6e<yaX73wDPV$Mpd#RB7`42^Oi|zB%XirJC7+qzqd%lEclzF&YP9m=q#?l~O8S?T=^6`M&Yd-Mj396mpGh8AQo0XN1&3NCY83(h?I`P_7ja5M~?^Ptd57(j>OIHN19xh=ZKv(N_QX$c~#gms0+af~F|5lS2ueMGr-*e4|gla#hCSc5w`E%hdexMok0S2Hh}D!Whj8o<zZ2SzY2;n=4n#e_<QXDKIG-dOd}a0Ho1E42<Fk03!f~yKNergXAQwR10>i*5p$$RJ1)YyrL~oXgD_h<=_43^`E`<>tioWq%tX*!BJ@^ks7x_bV8Y=d~_%k%=MQiOh!|pWe+D=nzLvj5Rqc83{{8PxqPWSFkJOziX%J6j1&linC{v44*{_IwZA+?1ArU@09u9sfXQxQG=z!<LDpjR#!OP=;o!ziYqxH&$ss;@=OeHG@|`1Z9eerdJ*%T3pX6?i#S~sGrnhp@{((|upfy}6)V38(hPs#0ppSie@%cLKljA7s&E!(GflAshW}?khVQ0~e$rx$zzv#U}1H{SROBe>o2}*zfk|a<f%z-dwU{Hge4H~p+5W@Z0)%kc_twquN#`{jb`{PHSJAB~V4VOYNvT6bVI2JIlTAbuUt$4mYQmxbn?;0C)CcQB9&8ssfyD!%YCM81f-k?9<Slx8#T;f`rxGO12n-HaupLY*X0C4>Bi-7#$w>y^~V^rTc@fE;w?C2<5J~%gfWIONRzd!f>ROjVHd1&96EAMV+)Tuph9)I?cAN=fzf1HRp?m98|`z?TD-;?8)dcVtP{r!=0A}VG!?Y((rd3P-q*Dwp8t_r_*ZEwwtfzfaN;mY)$r0;8|dxtlq5-;w_Ita)l<-r?M|LbIZf9M<p%Gb`HTbh0Xcy<0sAT&R_o_%%k;>EKcq&@sQi;EZL&oJymbMq&<S2iQs;=do-fA6<mzh{?$dwlWqvAJut(sN(E<E6!^kBsJ>xl}&CeqDX6ToJRSLMprVQpeDKbm|9j5=Zx3?|nS?fZ?Iu)T!>tl5lOegdrs)D*wgxPNz51J9R(?PH2^HT=>X$@WM}(@w1(lAdbQ7y4}qny?7zCzS9E(=N9*9o|r#Qn%s?hfBxb#_piUTWM8;GXnA6OTl49?|E8%fP1kO{R}{mkR?+9R26OF{FI(R@x4`w?G532X4Y<$tzUQ}j3YR|~q90niU0B+ku@fi`W6+_c^QX=n?|t%u639RJ$L{=lz`owxJ&#}LHO$s8y>)E<lSzVITA(&BF3N9NTF@g~7rXq>xIMJ(kw@cqU)er9Gxg>h7rPHM_kDYx8(!?}_^+=g8o@|9CEBg&)L<bHuI=qjt8$aG?;sd5+4(RMX_vP5dT+jc`qG2c83_Xi38f5srTae+X!`Twet6(w=g{-LB`9!e=}ND6Ie{FWIsMr5^>tiv@dUZ!`c>?{t5a(IhMAeZiB+-n5A1*P@!=Q$VQ=Tk{&$WZ+!}xCfGchKxVPn{@0Kz`D4xuELX}V~9*GooT)G%*JaX<wCZqiJE1y=%wcM9`Q;)rU^f%kROJ7Xea3u)9^nr7S008*Y{L}hFou`0@&zxrf=cap}xqN<ItM`G^_2JAq@;kjB3#%@6__4X}P1HXvT*_3M^?y0|+H?Q;jotT6o;)$?!(H*n!~1sm?w`F-`NrX<-B_;W3xSx=>9K_C`N-AjYW(2B-Th@xYQFcdO`ohUo*glfMA&;(!oXAr1gH;pj%YaO^k@G;d~fRHYv(^Z4=B-yuF&hQik$2H`pr(~U+<ooyT!Dv+f^9;yL<Lm*Jkf`jNIHDTC;s?>z4O!H~ebx<o@3tbqaImub-aoy@Z?Jzq6FcCgP>E&!BO~21nzL=dZu|%(YL8p8mN1+1dI3`{?`5mlv+QaO963!`w0kBx51Nfm1&L0L9Un$FbD;>8S_botA@m-c>$(Y6Sh^^{cO(IP;}n&K+&CTNXc1n94u=bNBe8N^!-iRz?)m!ONd)OeGG_bvhq=*v^?FA9f$|WZ3qPDy4u)h~({pkYBN)B$k5DFLjUKMY>{EU-qZ7pY?vC?ECI)cj0J%^2{;@14}1nIP1c2z#Vb`ARyu>U;tns5$6QI696?Jfl?}e&>V=VAXuOEnsXwFP@zhDYdehKkX(+rTXZmL^`i9b(ihCE+hs5Ta?|k2vdz&bu<6ai$#manz$p&eL9$x$hD}b9k=uDsh{>h{L!Q3dvaaQ-Myh5|6u6<kmOb%4uP^NNa2N+5m_dw2#E^g?OehqHgwzmh=o{;|v7|H<M`gZBsXUTat7aCyF6A0ZKq!k?$~(5!2irFdCX<Pv*r!Gz9EJ7ip>ki^@9|jTsbt6<$hR}u;?9&^x={fTf|su)82md7PbQfR`BG*~4iKmz9gRc+JPMP6c-U#xkfcgF=FJR3FenVdx^S#fj7GHo{H@W?XTvcV<}=k|E?+H)PM60MPO~UPV6Z+_9UNWREG9gjU@Vm_R0dt%(5-1F3PYb;2c%4u1i^pB;Kfog;3<R@974jHgcu5XbQnxf7K=(w!;l6+I3=WvX3cU6MHQN~l{UjPM`D7@>I^#>NRf&9VlFWm@!D+;my1DQ0z>#zvmq72_4aUIT8tzzxm-f@tO?mrsmMeyf~4dW4*x9%B=;0cL3b?a@Q@fNcY0k;s~SfLoKxX48Ad>sbd;x9iyMXnG1pqtAI320k_2?ofogNK<R%sQkRzz|CvzDow046GmM~C5${ER4+U<ICWI*B&L;g(4m(lAHsRE=}-fT1TEQ$P0PyoW3%%wzsB$lT^fM)et4M(Fes*q|k2mn>6N)F@x=J-mJB0V-bGQMJ150S76r;L$&xj$mDaOsHK%Zh<aQQEmdX}t)JV8*n;<BwJb`l<ufdZSi|1uQP-{{v4&T15'),
    ('BUSY', 119, 24, 'c-j?~iE|U@8OFV*cBPfHl2*60x~0{9-?uEumSjsl0Aqtqh&fV@gaQE?QpmxTP@vPKB}da_Xfs38G+~$ynWmGb%|Vhjg-+6G3pfD+1QVbbY-8D2qRRIVJm34g^FGf{q3AfdZPoMJEtXB`YN?=>@zw1Eqsx}9S~;|G`LY#j9$MOCmg?GjJG)2ogMDkOo1#UPR-<ubOYPZG%$3MQQ(bB?Z4}ZHlTysc)N-{*ucyRDi%Ku!Nl8r16Hro_Tp^bTDTzd;_a?*9ctR&dGfoYyqC_&GMs4Ja1xh31@Psm@8e=j$LlLi4LrE=+O5>&t27`j($&_+2r8Js#3WL$)@iDqUIMxv`*_<u|?WMIUqixBE)70H#Qz%4oimw#vgXR9-N<LNUC=@FTMpg_D_7-Jw4~GSU2pa=I2*hCy#$mHCzEtB%i}*aDSRy2NILbm1wt!^e0AC<6D+DaINFt_SR7mUfa*VPnY+72W(Mkjc4u)_slZ`}05*AG27z7d^sLgbDX5!(nhcR0nPDeVOPC2Ct4g?bf46$JtgdrG$5R4}vg=(uxLJCBbfIwgXz+^_VSwtY#KxxP?MG2*b*5ELyQK@AxTg_40WGY%KqjaqaP!L907{)>ggN%(JT!?aac9$!)-g0{^;PW^byTj!*;2?mr0g%f9V3-A?5Q_!L400}CERm7~PpnWXxEu(fvprqyE}XQN`bYXK9D+7zXaXU18l4(rYi!|uvCF4XD@+^$BXE-eR}_<6ecVD4Y(9&xb2^;ibS9U}rc=peG8zte5srdIuz)sROB%vJ1VB)jwySwUiAYUxg=)se$OH&#=o;$l%VCtEx3|BiC95)MRa_QVZ8Rtdt=8gOBF=<`a=DhPl2f>wfu+3#*qG4bc*{bm#qDrK5)rF2n8<Zhx{HPOELQ;V*=#P-21#(34Wa-DKoYZwR!Av}vb9K`&#9(Zn6_h4@8X(JW*K~7u;SAg{PAees1izaDv}?z)3!3*8y4zx2Fl}9%j{->I_~FcLke7oqnIv`ibk{9s7`P3L{rIFt=e7Tz&u1@*JFUDo!gQnz?SKl%H`4sc}gzA)w(@aos8g{%frJ<7Rn{e!qtPz7IxPbFCAP^N~i@&3K!BYTg*?DJsg@=aNRZ`VK5McL5q?mHb|mv2<=aW{jqp3<aPUFQI|0kP2~_aj;_D-1W)wxx9b3$L;)!P$UwC<rH~3K+%63S4SZv3+P)QQmS-3>9q+5=4T+9wz9%9J*ySJ>l)!p32dC{?9!D%>(|Qo0l|Q*qSMVXpp|jum+gOyRGo9+TB?D5AFXeZ5td2+o#!$iT#y$`@a{n<2Uzc}t#8L-IqFx)RSvrj4!JsT0Habylb#S19iuereH8`|+6;6`bpiq}>=k=_y6NDv}S2z(%S5*RPWx(Qp-<?dhxmSMJobki3+(x?wasvu`s*v_}dwd;O?qP_90PAk;=ks2f*o1u6Y))<kUcX$Vu3sn(UcWN^jh)sVx%>6p7?t_7K6`!y!twPpTXQd7Uanp@)3~vhd!Tu#S$_qy{-Zv5J}x<P@A~*6fW^c4=cetlfGc!*CW-)fHFEm${O9iNm!@xSH$OSQBt3DfC9Bxjn7KIKoZ8rS=%MXbr|@I<*6{A#NF-hu`lRtAw)mTw=Nj|m^K);lojOOd`5Pt<7LPR6GynZE{n1t8>FJ~8D-*-NySR2|eRF=z(7N02azJYuAD@h<QdZ($O}{{`NIZZ4ovowJyB`go9QVCA`{QGC`ydn|*Ux@+{GB^DS24+vPwREoGxhg2Uzw!QRR?e0*(DOqd`NvUPF|nmfn!r4&^0`LZO54lBRl3k*gMuN9lo<qd*JNqX5*=&w@$ch5C3Iuv9pt5(D9oUlh3WadY6HDn$+E!F>7e&<cANRZFrxZoW1>~4?;lXvDy77{BnJxWvu@6Sc77|zJ00LlpJsV`H#~(l!kLBuv>T7-!&!N|1>M8G57YZnR?@)m6KoY+PFIKTw|;4$n3hwdr$9p^#>9C{!_PqZlJSX{mhN_bXKjq(&!Wrm}Ba$t(H18adFq)CjtlN&s_aD451*lZE8P{|LfV^i)MCK?_Oa8+|0<S8_uy))t4s@vVPfk6u2=%y*2yP%9#sll<A4bfB3=0wHv=U@5%PM4mXZIdGD<M_fsRXn$*47nQs2i9P}kOj5YS9{IM<HefMZqk<tEj`k*ggynZ_ED7fCZweh|A(N-V=oA2y_z+X&kG)~{2ywKzdfuij4T<Dd#YxDDuk4}%51yj>t_F}zxt5ZsZ7nG~M!}V?8(MEmxZ?+fj&d**uC|dN@)ZA?U;_-X)*IpCYeY+d==GP~+yC<5>*%M~kF+5S9xgCDJdG7vs&hd%I4fpOq2*lF*EL>ERP@$QXiBty<q71?QWij-@QByHu*;28%YCSU0vuagBjS!*gKq=x`szR~SmMu~DZ|5KLI1rD+x?$@A7H`3}*I(W9_#=Jsp$!kz;ucq?XK=V=veVM=sx?_!(YI|yHre-JSF-aF5C*|kdbc`;B-(HiKm{Nmv?ueKkkhQ=sR&+sP;YW5A=ns*+U+ut&Fd=}5ebZel)F;xd~JMG%$OM*mtg{o=y_~YOc_+>YF%NoiK2KMz9yEBx~*D!d){lZ$1;&{dsijVTkZiM07DTLj-wFHZ{;xnumKL!p7RBY7NJszYs0yy*T{uPi^URKzxSo%Zyq_YrQ1wkFd()Te3hLs6-p5x8wEvR$Lfg4q2<V}u6T@5Kp+6Jwb5)Mmh>}>(ctigf=;V9-C29ErvShpfUr3%sMP^n6y)PTE0iV4T0WX6n2dZj<4Y$Tv;aXQ%)p*gXWoDJ{nP(Eb!@qp&*!n^@uX3~#`pxqFwPhg>+kd`Gr3IGNhtIEF__PV5tTogO?6~^4vWcY4W^@3W2n1WZ10B<n8g(e*l>$2fbSoIAOPFdv!LBqOjs$Fz-VLiQXUH8%4ZL~^Y_nBfAZO9fBMyutVC`qbSG0fST5z0bU2Z(#TKPq3v0zhPikR+r|c{sPzw(f7NaGQPA3bwfXmL<+-_GOInWW#LMWn=OT=OU4&ngH0U!c^AdVqj?My_w;|z(YwL+BuLb(LDw*B+5x1RawyC+`ST22bo9kr1{xr4`rAru#TeBN3l8}BX`a<R&W(Wpx2R<>A0=non6u2>@5yRaCKd97B5%jNdyRSpnAS_jR-F%W2Lxs9}z3qX8*FjFY`^FbZS5(pszX~7msg$ItEKl#Few@(~i-xa|mLyM}p!jPP-BnTKKc|;}<4(5u%-X+UN7A>oo8LwE15W!3+?Tkmgk?-LmmkRs*!C)j1X>WZAL@^X>L)Z`-09wUB007q#iDk;UgpCv`xkRfQ`6PhF%bk1P`@_K>zwpMc-jtusDff5m_|3<o+0#EGPzuDPVP`t!&*e6(@5+RFhjI}o!~un=l+oyj`{bm|mQ1$Tt)p5>IujB5{{a`W?g0'),
]

def _pad_sign_hints_reference(raw):
    """Locate READY_SIGN and COUNTDOWN_SIGN in 960x540-normalized Roblox view.

    The messages describe the sign, not the true pad availability. Screens with
    altered FOV, clipping, lighting or camera motion may yield UNKNOWN. Never
    authorize input solely from this detector.
    """
    import base64
    import zlib
    import cv2
    import numpy as np
    from functools import lru_cache
    if raw is None or len(raw.shape)<3:
        return []
    H,W=raw.shape[:2]
    if H<300 or W<500 or not (.48 <= H/W <= .62):
        return []
    view=cv2.resize(raw[:,:,:3],(960,540),interpolation=cv2.INTER_AREA)
    gray=cv2.cvtColor(view,cv2.COLOR_BGR2GRAY)[40:165,:]
    hits=[]
    for label,tw,th,encoded in _PAD_SIGN_TEMPLATES:
        template=np.frombuffer(zlib.decompress(base64.b85decode(encoded)),
                               dtype=np.uint8).reshape((th,tw))
        for step in range(8):
            scale=.73+.07*step
            tile=cv2.resize(template,None,fx=scale,fy=scale,
                            interpolation=cv2.INTER_AREA)
            if tile.shape[0]>gray.shape[0] or tile.shape[1]>gray.shape[1]:
                continue
            heat=cv2.matchTemplate(gray,tile,cv2.TM_CCOEFF_NORMED)
            cutoff=.61 if label=='READY' else .62
            ys,xs=np.where((heat>=cutoff)&
                (heat==cv2.dilate(heat,np.ones((15,41),np.uint8))))
            for y,x in zip(ys,xs):
                hits.append((float(heat[y,x]),label,int(x),int(y+40),
                             int(tile.shape[1]),int(tile.shape[0])))
    hits.sort(reverse=True)
    results=[]
    for confidence,label,x,y,w,h in hits:
        mid_x=x+w/2;mid_y=y+h/2
        if any(abs(mid_x-(r['x']+r['w']/2))<=75 and
               abs(mid_y-(r['y']+r['h']/2))<=35 for r in results):
            continue
        results.append({'status':('READY_SIGN' if label=='READY' else 'COUNTDOWN_SIGN'),
                        'confidence':round(confidence,3),
                        'x':x,'y':y,'w':w,'h':h,
                        'center_x':round(mid_x/960,3),
                        'relative_side':('LEFT' if mid_x<345 else
                                         'RIGHT' if mid_x>615 else 'CENTER'),
                        'availability':'UNVERIFIED'})
        if len(results)>=7:
            break
    results.sort(key=lambda r:r['center_x'])
    return results


# === ROBLOX V3.5.1: alternative READY sign for current live client ===
# Template cropped only from the game's on-screen label 'Лобби готово!'.
# No player names, avatars or other screenshots are embedded.
_LIVE_READY_V351_SHAPE=(22,126)
_LIVE_READY_V351_DATA=(
    'c-mc-c~nzZ8o>WncCx%RZ%YE%h<SiW_Jt5Yr;0Pv8P3?EJ)?*QG-'
    'BNc2OTXgomyLa3IQw(E-f>T)q>PzMB5%aOFN28TPvbHR(q@pC>WCOzqu~~iv1l<&dodT-rxPc@8*6a8_LScN=ixsf#Txgd`ziODo'
    'KhY2!i5xmZZ5jEHO2R!!Xhdac~01NoER_N=3(E1)k?r6h#r3A~Q85B_$P+_)Ja7R46b)F2k`c&eXip(u5rSnI*e|lI)~{D5>3JWj'
    'GEeifbC3s+n@tb9QQmT~bq|5|d?QWTa=LN#cZi_N=7%NSZK-qM|0niqvA&YQ%DrE*?ADF@XthKYSL0-6}?N-'
    '~k%EL32C`hfCOL5;5h+Y1MO~Q<OY;8p)U@QxeLxed{Q+0xzJfuqpzRr>CYYUYqO>1bm^$1R|0xD3KkLVppDz0zA4_!KuzjgZ@fJK'
    '=U|mW&xyqNa3pDOy`}XGAG5!$!VDx7)8(wg`b2^FhQV5Oop_n>6vmRLBAA|7YB-MjS%^G5J0O^W@d0Y1xjUYWFq_m$8$pUvx&py='
    'm_wbLdmd7xm+p%l_{6YWHOaX!RvWUrO1@U!D$7Vl`X?llV%~3XQig6r_H9-'
    'ij?&9j4tTI1u8iyX?9YQf=cZ8<q(ceo8>(G&9oVSVHCgn@AvmF+iBt~{O327FB@3u6kM&StTd{aR|mTUeAmr0S(5$qty{MSo8*RL'
    '-`&5tRr%||ThjLrmDG-'
    '#_wIIZY1r{wgM;68T9iubsk`^TTAof~hoF@bD1wrX#iU$S84}Q8Gd_eGO$dNumW{yZ2n?C<?_g{!79GeVZ=eB0zbd3U;B(IZ2yUB'
    'E;<E=J78&a@T!D$lv9aydV-'
    'o<e@r&GBk=Ud0Xg8tjhv83ufXnHY8xVN_BTE(7+pwPDQLR`Ol_yatrZQv<1d56#U;!`LmDk{#f{Iai4Zjah+mDUIeqsp5I*&YsLm'
    '0BlP5|7_L3Z5$^ob&0AA44te-'
    '>`%Tb7K$u{l}!KSGyrXKbuI`#PM=XoZ2aMi^aEa2>wPBoD+^2|UX&EEku@PibW+KM)X?#3GC!+4DwW4})EUKJp&yCa5pqGBX5!Ch'
    '5=M3eyf>1V^LO_7gaRor8WYwKNu)PtO~MMx3mM@p8iQ7#h|6@Zj|KPxj!Sz*RZc2oEjHp6GG`%|x+J%aPp`u+j%%5RcovW3Y+GK7'
    ')Sl9@Ox}1sKo_!3Lh{hOgD_@c8b%UX*!_T5Ujff+zamA4=whSZuLm--{EQVbo8W?n9e!9VQ+|$KPbH!KF-'
    'M8;p4PUtO{atYl}V<;>DhponL_g-$A-d2txpX=(_L%Kr(S9B~!SP<`+LM_hsPbUOg-Sr2zC27|$j?5v(U4Yx&V8$9u4S%+aCLoJI'
    '&R?6K^V?k{{TofB&WYGn<At=Idml4#zL}KZus(Q|DQlE^%E39Ov$rCUddM6TFBW#I0-'
    'MZ@uG^p#IJ*{sTfkq73zscSNcSNIc(ypl-kG0ng!siB^Z5Z}*JSxcbmp+XB=+s|_bB;g8#uimYCz?V(KsPR&i*(DG$;30$c002LU'
    '_hO%3qh1I82%lD=){REqZ-{d(b$(}milNy8i>SuF#ZZt4|i-1yS4Ct@OOPdf$7i_h{4crb#v^)vArsRSa=5|=<#|?-'
    'w&~g=(95d_3k*D-'
    'EU<z58!JVx}8{NhJ9H`plkotW78Uq<rjOH9KGe>xl<eStxkL1{&T%=xCJ?`+1cB(PgKz_b~KQt()PWg+wI8TbtEJ@T{iQ|?vD?Z7'
    'C7wUn;nbNNLJ}+Kl_(*if8LP+S?B=*P?z^)7`Vzf~!>xp9b+s`*d6QeTZZ6Oa-'
    '5<7mWtfT&Kr9SG3rCKEKB|*KEmmatc<>kR*lbMH6zeu+W@qcY2&QF(=nycRB2HjRwm+l#F>=Dm|SM7*ZjV6R01MxI%%hQUoTKDM&'
    '`EK~0lM+|1K<wkm`!0E&}QI+x4i_INx+9>3S?_xgRlB5#q;VbJN+8jVJ}+0_Pv-sX0D+|q04)9rG*oGz!s>2Nq~wj3=@s|5zN2$G'
    'hX2}99SpgzlKHG;sgKPx*Q45D8E$7QPYXfco5=PCC2{eIMK{XVbTF;BD<8Z{cNTC!&s7G`O5dYw*Zc6+_v#17ofJW&*L=jIyqx-'
    '6~K(MeJzbt8JFoffoeWaoZXcFpTPWEZr&)+8<E_7$TpA7@?`dY@;lMfxdwj>{@AQe#tFf0DbM+C*m)?YY?+WS6QW*(qv9=rmd)e$'
    'k=C|5SF?ak|iC)LZgxPO%_QoHM6%QF)xj<@3=ub52g#{9KDDnsZF197l=QWHgyfX8$h`3l=PxFHvSg1<~t`-eOy>#i-'
    'L|XX|pzW^;~Cr%!-'
    '#r89`)9JASIG8&C~y}@9NW2!i1+ZYZvw;euqq$P|7M?UEK>lB@>tt~BW?;mYzl?E*>t)0g^!r_*daQpi+IDY(SxEaxM^vHW{t>LE'
    'Trlw};?fAnuP3TFut*x~sEGgp8!*SkOpSN+R+i5E;t*R(0^0{9O)~-'
    'RUMTBbRqweEfxS|66*Hz;4p_90*dJ#HsUXOqIssz>5)hkz4mAj;4x3F?aso(3g*{oJivA?LuX|p?=2#4Knx7h<_sFQi)rE)l3E?1'
    '(;Rr?xuglcR5^xDZon>KBzJ9zfO#lF5vh|8Bd{;+M!hPnei@7C9E-'
    '?rh^^>vM>dv=6E>+066YwqpsJ%i}!>F)lhIaCu2u3r6CS4+dTx?t6c6)WquZr;2pxN3E<1`(7t8Qk8mb>oJ$XlmUW6rdEGv{K`~-'
    '8=pdYiz%c'
)


def _live_ready_v351_template():
    import cv2
    import numpy as np
    import zlib
    import base64
    from functools import lru_cache
    # Read-only template initialized once per process.
    return np.frombuffer(zlib.decompress(base64.b85decode(
        ''.join(_LIVE_READY_V351_DATA))),dtype=np.uint8).reshape(
        _LIVE_READY_V351_SHAPE)


# === V3.5.8: narrow READY template from original private gameplay screenshot ===
# Only the cropped game UI label is embedded, no usernames or avatars.
_LIVE_READY_V358_SHAPE=(18,120)
_LIVE_READY_V358_DATA=(
    'c-mc+dvH|c6~O;3CUiIZy!U?h{n*FdU9!6gVYBa7;>aI@bfz+W_!wvv9I-'
    '9fDzpV1gea}!z(}oH+GIB&I)*?oBwz^0s8}nnP^c|7$q*G2$a9n3d;aTpcay;Q+nJqnXYO}@_dDl)=QR7D{sm@}>a^ReHXA}DX_p'
    'Vp0l-TP>v*$(gI8%@5Cop*Ff2<`7_tIE&<tCFVHldG5wcV-u^eNt*eLt2KiiJPGJ?R-'
    'gxzdhUY&kcE29WD>?IJQNZZF6z}V;OcxC_x;}_O*`U-'
    'v#uEK(>j2_WC6slQJR#zKLH3Uu4EJbv~M|M#}q|IztUcKCC!tcT~?t}Ti{|7*%ZKfJgwa^^9wN%`nr5Ij#x>!7TKS^_f&0=LZtJz'
    'FrEvhk_O(qk=SVUE@GnN`t8G^P_E|-b;e%1GuEn8N-%wRMc?qg(Iwb5Af4xA-Ks;a8$zN#uKqRX#Z`yq6w&jV1b_3`Ut<L9F^IRO'
    '9o(Z&rbNA<vkpKRRVW!UYb-6FB?X1^1A=~JVlqc`8Sc#nKDKC;ucepKgXj}5hqjDOoH8i+1@J@Rgy%@*nVcKplDM#_Ew-bNy#u#r'
    'Y|May`m;7NHa0Kxuj8YU-'
    'T#7m4qVGc^ygVYTu6rl7)2<6}t?*0k*pATo*^)JxoW;;EfLGiX$c;U&JB7jyn%^xgk;{~mca$SKtXTFAyjDZ_4e+#BJSc(0xjTLZ'
    'ZIF6}kafz}TG>f{|dJV1xemD)giCZx9R;~d1$YGc{)H(wP?AU8M220+4pO4$6&294c!f?HJ{Ve2FY2`Q^cJ3_AKI9yPZo^w})zAW'
    'y4+k&9B@^|kwn-'
    'E?p5^$mw)`DF0`sWsT{#Q8S=&_@AaB77B)SM^nPGUDLZ86LOdEW@WxBNFeUD)6AHZc9J*v&Grb833m!LL5VGZfO4K30Y7(4OR^j_'
    'i|T(S^*;C6uBTiPh%m3Y5PTK0ALudVFO%)vIn{wZ8yZ^34PJOhK$Fl-gj3AiS<!JW~sdSPgVEJ-T%k^*@a`fcoknzmN=wh-'
    'iVFqNgeU&CL7K`4%u3j5j1@S%y^4pT|tp)-vlr+e8YE&C<>4GFq8I0c7jGy-jwe?luy4nhxg4mx?_Q#eVt;ZwZlSs1ESRdogSa&G'
    'Q83<c0{VJhtiPrxf2daN}6ge5VfJ*8ZM0skJDT>AlhAzJ?oqpT>c!%F@9F?YQs_$gQRQb%EO%fWf=DRD<}`Zv30;CIrtxtSfiCgC'
    'MJ_Fi{94?}*BXTd8!TG0Obs~d1$b%iJ46<%;%g~1<pYhy9@Ae@Z+UYlL}^HTARXTE_RLOeC!V`dl9yr5;_s^D~Og%VOd7d0pqyA+'
    'Q!P=b<n!N=1lia5CFCtIQL7`qdO8>5lN&^73CH#B$;PJ;$R4?An46WYs+NUj;dNx8Gl?!E$Au{75wqBrni&<4YtGzR}R<37W&_jv'
    'mn6_4i!=T6c-'
    'SK#&2?>|@97!B9IcKXz73DH6*drtNJF~HF4^DmO#)%ksaL?T+>()r6kEFSi4?(P560}atg@IZd8f#PhjTz~sIB=EcP`F!gW3Wca='
    'di(wmASC9+^IPl--bF2I6<lgSb$jY#$#}iLHk?jplj(Y2ZC#wVauP#P2-gJ>W-'
    '7GG7mUP`v9RA8h(zMi$V$~+y9y^@l}s6ptjJOplZC{6oU~i4RzmNZc8l3cv5HI(6w6iG>Y|q8%*Yjwr{c+EGLy`vQd#^<XHuDTRC'
    'T%}S(f#NEUBtHl1wBM349y=PsHQ#SUeVuMWWGg*r(7)5?S2ZDH;zDfkpHp2q9jPMUm&eQ(l3uVcf|$eq=h?l+I?e%}vcsnRGH13i'
    'v}FSym+7>kNe)vRh|GB9%&2+=*CyFc_?BsPnj74uxlQFN5cYK;P@7MMc71{yXKB6khS_+eoFGnwl%Da^O1!t})|Y^!nnBBC8J}F?'
    '3g(h{=`V7l_n3W$e{!qR%aa?%6IaVXxk-aGLLymuv9VHK?^-)#Xe-uzG=v+vRjRluXv+cB@WBk(HIHu!2)AJ7Y~cI4v1WI#?d5ay'
    'VY+am)IE<{eIlQxTTHV?<Ql_+j|{Wt?tl0eMaD;qI<{K9_6jI)429Mc!*~&*u*xJJNx{A7{S3>*%|=91h+&b}vVd<l8XqN4h#Y+H'
    '*K+ZNm%8(OvQ#9s1Ms<@hRB;n0p1{|9#P8%q'
)

def _live_ready_v358_template():
    import base64, zlib, numpy as np
    from functools import lru_cache
    return np.frombuffer(zlib.decompress(base64.b85decode(
        ''.join(_LIVE_READY_V358_DATA))),dtype=np.uint8).reshape(
            _LIVE_READY_V358_SHAPE)
# === End V3.5.8 extra reference ===


# Roblox UI-only "Создание лобби..." templates, two captured sizes.
# The data contain no avatar, no account name, no full screenshot.
_PAD_CREATING_TEMPLATES = (
    (21, 161, (
        'c-'
        'pO&`)?Fg6vq=aQA0F}!j|26Y<FjOXLq`fncbPWgALUfP#eXFuNEXCl!s!iEoiG$g=nph2#O+6p=w*7{9wRmeNeCl43DaPtU&4R'
        '_WPH3?#zM&SVhY>-MMEvGv|EfoOACT=do=&|ATtGUr$dD|NX0WPER|!=Qr(ZWoOALi>%Z3{}6LLSLKnp26NoQ`3-'
        'ii>fhgfLuEW?T6lj0c&~cOD4(!1k<K+vtNFZiUWDoJl_^f=uM&xKzPwe`#lU0#RLL@$9zPY)()0_*Gfn3rsN8QA3z!O6%R9TO$'
        '+APCJDbmGu}Vrs8{66zSF`D+@2qT{-TZcP<0MEa#<coxxb<r0g80Ji6a4OP^=Y$J?t5-'
        'TzvW@@dyMIKPq}7$>O%OEPxGfnP^_g$SyfH(khZ3(hHIEPE;q3$RjsjU%;`D}hHg4c=Qo)d-'
        'R2oesA;PVYA3ZsLepwYIyKZd2hm;x4nMglu4P&37z#U^ZW3b5(lZt{SSDju2Fy|3?-'
        'PV2w?`aZZ0+lR!${lyrSJ58xL!*;&b&5P^Gqjv!?wP@_nefYG<CLwon%L+WgDH(+ALAu*(x(rTC}78HJ0?URlVVDuIGX*Bd+V~'
        'e?60C!URSxz04Q1nDr>I=8`KUjWMyk^CqU-9UZZXeAaqkQ=C#|J7#v2Cw{Unvf8b{3DYsxxfZr-'
        '&QiB5rTI*pLP2yIfQ^|JU<u0>fDrTdxR)1rsSv!!ro>!soEs-=Q?-'
        '=9J;2~xBi;*qSioer%<6#kmaq@FzvAi={TjH@Yo*{Jp#NoHObPC4S=|qGr88Z??!&-'
        '4nq!_AX#SkeA_Q0zoW;O1na2sRs*eEV?32K!4<E&0*?Vo^JMsiEcogW}42*<UdCV9Ni+`5QmekF_y4lZ>*?4|B`jd_WVGr;g@+'
        'v6ZK$EFlKYKaQp(o$M(OHTMn7QUkv0(}&fdHpgEPwqJU?UGDOJf+GF>56da6PX8<_5+HkP`i+7=8tKh^lfZE>jMdalps@bmgeb'
        '0b|9AfLy_0K=YOX3fGcz9t1Y%S~op45O$(JV2crO0VB8cb5G!ao?O6X$6Y{$AB!cR+Vw?UrixTtp%rM(F?!i{0&L83@+W+M;y{'
        '3jBlI=|*!2PO{{)!aPC+cUEaYsh%?PkF6W=&WG`FUM$I<S%fcoMojCU8#0W9FNcL^{-'
        '=M!UNV+Td<D*F^lJ`NaYqxoRFfXgV0%(dqHh9f~1{M`eb#7I{qz%<tyV81UGmFq(Eb{{F)v%spXBuh0k>*R&NN)`ups6rmYk!y'
        'xLz^Qu|y;=suM3$OO7K`}pN>Qv5`SxY`Kf|vw2NWr9y^+KwU`4!yzKBMx`e^!jpw_zfB#!YC0}GoupfbN+V!GU{=uBBq@3pc_9'
        'MW|Z^g#1d`GPg`4|@8MNlav7Uo<W307hqi2W)=iZ6N=^<&zk0+EOlYQDBXy0AG~15n%Eq;QjlSbhz7VbT6<~C%`GOnhtB%7H~W'
        'j`hu2=)hAFe*!&XquAr&>W}E|lbzKVwTu?$wRvN;n!fq+yu`G8K2n788s^q9wvE@~B3$AgOf4ldeRjoKJWs5f!1+j#aA_sh)0}'
        'hGlw+N8MesM4NN60Vrf1!?vd0LM28$F-(HFo-#Yjq`9{3X}Qr)*wglM!G8Z?GSu0qWv=tu}6QKtE~D9H02Yp+f$Xy6Z)s+B-'
        'h_(Y&}3*?J^D{z<JuPZmc=6eJONFF&-'
        'tad)32_YQt8G4rdzrN)B6f!lMbhX!}a%n&yW<qz&i7&P1Fe!u6AB&*)EjaIs(@$vXbe=U8(=+T`=Mt9w<Qs7X-'
        '{_&sR;CsrzPfsM-tv?RbGB#Fhu%cVBH|CjTz&WI<nODu2arG=gl7uQrR83lbYC@6}vz#X2Hc67IHd1AoDk*6_5;1a0i28(%8r>'
        'G5t)nKS@PcTH7*=g}a|%a^)2h+59PMLKNmAYA+fGzVs^K=59+5&dG-kr#1kHtTIKzx;f!L$|P>vZvZk_??^Ua>^s}e*>OxpID'
        '--e5TJ896Lp$Ye&zAi74{sQlk{MG'
    )),
    (26, 88, (
        'c-'
        'm!_i&GQl8i)UYPN#DeH5alWAy*Pm<f4J%4XSh0R*Of+3e6^Av)SF;NV3;t$pr!t2n2#vsCs&tsU2tPRNGUXR)o`f#$KlN%<0tH'
        'V})4%lJkDMFm2~N%x*5bdG_7k_wD<UP9;+;kYbY=F-'
        'p=5HRQu_R+L0GnMfpthlk_CDsf;q9wl(x=MN}^)Z?*eB*M@sju+DzS(ej+L<fUuRSRN1El?qbA^kplhzD;np{V{$ECN@>Rc#=w'
        'UJkqr6=8Wn0_{j9EplWqD5f^Ol9(bWh9-'
        'SpZ%B|NPSM5`q8l3+X#Dqj<LXUBkvGnwax)`xMik;?kl;7H5JMtJ(G=V#9)ogI!?7q3iA2z*5RF8`K`(e!F}ZO+(MXt~Sym}m&'
        'ZGq~M3N+%1Sbc7sk9I#X`1qTy*^eHg+we8256drJ-kI?_~`X|p<W;mVANz#40MFsj6o8T5Ce&{$eZFtmJHE!2x16AygZ5xj0^z'
        'ojg2A)LF`k-G1VJI^$w#^1Ff8qqzE}g1eFxxd)xPTJbQNSZfk4Z+0xSH@pSF&?C5Amv~8e%*xlT+bLTFF-JOUIpnZ4ip1q!~?('
        'TL%MlnFSArvpy{MpRp)MROVVq#*vSS+5OnwpvhrZ$-'
        'T6Q$y~Lh1Y_rBTFKsdW1&k%*CA9|2w{H<k?89WJNYWHy@{jF{2kbT+wNE?1Ksuvu+3n^oN@FZKqbv7rIe>I_y>J%+)T7QIfVSG'
        'e8$`fJBu8zfaPT{vhnY1@uj3}%zjh?&9bayNt60VwWG6tNL7?3({7tPg(tZJpI(X*3%2s`#$+<cU{L5XcKbAg@00%XeRF(bsL)'
        ')$K4j>g($<r%8{Qw3uFtX^iz+vtDPm+e{jbw%)M4PG7%rBkb}%8a-'
        '8~G3Yc<iPd5PmUrO;=LR4KI;nasmM45eqqTB(+VR1iutr#3rnF<9&uqWb6I!af-'
        '7&hPtK2O*9E~?tS6yd5xp}PZ**9NzU;Xi6b=zm{#YH_z4(`vj`Z7GjBuS8pmns}Iduj*G4Kt5U|5*0lT-kEH@?};>%>UM33shE'
        'itjSMTi$7P_{m#~(<Inn^mS=zU{(9h}Yqzc*`>k(HUc0Avg11TWrU(M2Z-`ESm@4cy+t&%L;rbUZ-'
        '1?~N?FZW){OuoE+jk4=q1yB3;Qi_5KR<lHvPY~3{=K&reSZA-bLvU!rCaYTwAK389({aoI}EnL*kEm1?TM1;si5dYBAG;9-'
        'PDtN56`ZD_*A%d{XeJHXTJaB%+njsLbX?OD?4iM3M>6<)%RNTUtVje9az5quRB{mz5m~V(~s|erK|m2ycd0J{b8Jb>~ya7z%xu'
        'Buc&zUna!HRc(cY6Xy1Cu=MWzzx!PZk9zE0Kw|Bk1)$i;)S=T*u-'
        '13(<OxprR>$$Vr^u}{X^!10{v}*kJ&XaE6*8YwrpWeB;2UQ!QXl8b5OklV-VCI@IBZe6;6U-'
        '$4`<V9Y7MsoCw7XnRr`_qWqrGX%OE13IXt!bpn2lJY#cFAUX<)Wk;jp8r2?lSulO&XK!*i9{*=hIZdDMvzlAO!u;*qSxu-ROpP'
        '#7I8<O_Kqm(Qo5F($J)Swbg5GuR-P%jH#Wo<5DrB`F5HbCrtU>Dj-'
        '3AJEg&bEvns@0G)cU+L@ZL$B!FCLPcZUheHf=k42f@X#jk12`47Ue`%t2t5=~Z*_idu9BoEI^@T_-'
        'Z#(TXg$ehvm<Gald@1qPRdB41c-'
        'rVH)g<7(SgCifdL$r0JYb}I9Mv6VT%GUFhK;$_d>NgKVKeAQfU404h{^ZSS~%19g%sK%Zz|m7BiwsALe#-'
        'u{;UhL7bpa=Y)Ew1dF^#%d!C?2=f=dWiDR00P1SBEJH=<OghJ<xHLqUfrg(Mfr2F|jeaBuVsE$GbtK8*10cpjA*c!(GR34)95i'
        ')76gVz61f4gicrRVLbn)U_AYXvG(IC!F=3qIIrQ|T1k+Zq1m<B1&^TJuH+wBP^<48M5Ltg|+&{*@37&7y`SS*#GdyZuiG_$m{w'
        '79s4<jB4NslYf+6=gn=;3YYmm64a{VMRIN@pxL<1gv?mP-M&HnN7;m6L5**cyWAM?c3AS=ku2@Uw&J4FDmZ0E-'
        'cK?SLZ8}rHNby0#RavrU(BHMBou+Q)8-'
        'e_WzmropSl=)hk!7fcp<}HI=!!x!K8r%%dCRU|EIn<dn7We5F#EL#X>dP(eq~4leRP4DOyn'
    )),
)

def _pad_creating_sign_hints(raw):
    """Recognize CREATING_SIGN only; never infer a free pad from this."""
    import base64, zlib, cv2, numpy as np
    if raw is None or len(raw.shape)<3: return []
    H,W=raw.shape[:2]
    if H<300 or W<500 or not .46<=H/max(W,1)<=.68: return []
    view=cv2.resize(raw[:,:,:3],(960,540),interpolation=cv2.INTER_AREA)
    region=cv2.cvtColor(view,cv2.COLOR_BGR2GRAY)[35:270,:]
    hits=[]
    for h,w,chunks in _PAD_CREATING_TEMPLATES:
        tpl=np.frombuffer(zlib.decompress(base64.b85decode(''.join(chunks))),
                          dtype=np.uint8).reshape((h,w))
        for scale in (.82,.88,.94,1.0,1.06,1.12):
            tile=cv2.resize(tpl,None,fx=scale,fy=scale,
                            interpolation=cv2.INTER_AREA)
            if tile.shape[0]>=region.shape[0] or tile.shape[1]>=region.shape[1]:continue
            heat=cv2.matchTemplate(region,tile,cv2.TM_CCOEFF_NORMED)
            ys,xs=np.where((heat>=.83)&
                           (heat==cv2.dilate(heat,np.ones((9,25),np.uint8))))
            for y,x in zip(ys,xs):
                hits.append((float(heat[y,x]),int(x),int(y+35),
                             int(tile.shape[1]),int(tile.shape[0])))
    hits.sort(reverse=True)
    result=[]
    for score,x,y,w,h in hits:
        cx=x+w/2;cy=y+h/2
        if not .04<cx/960<.96:continue
        if any(abs(cx-(d['x']+d['w']/2))<65 and
               abs(cy-(d['y']+d['h']/2))<40 for d in result): continue
        result.append(dict(status='CREATING_SIGN',confidence=round(score,3),
                           x=x,y=y,w=w,h=h,center_x=round(cx/960,3),
                           relative_side=('LEFT' if cx<345 else
                                          'RIGHT' if cx>615 else 'CENTER'),
                           availability='BUSY_OR_CREATING'))
        if len(result)>=4:break
    return result


def pad_sign_hints(raw):
    """Read old + current READY text from the *verified* Roblox WGC frame.

    Both detections only describe an on-screen sign. They do not prove
    occupancy, walkability, menu availability, or player orientation.
    """
    import cv2
    import numpy as np
    old=_pad_sign_hints_reference(raw)
    if raw is None or len(raw.shape)<3:return old
    H,W=raw.shape[:2]
    if H<300 or W<500 or not (.46<=H/max(W,1)<=.68):return old
    try:
        view=cv2.resize(raw[:,:,:3],(960,540),interpolation=cv2.INTER_AREA)
        gray=cv2.cvtColor(view,cv2.COLOR_BGR2GRAY)
        # UI signs in both the recorded OBS and live Roblox screenshots.
        region=gray[24:275,:]
        source=_live_ready_v351_template()
        hits=[]
        # Small distant signs (the 2026-11-09 live lobby screenshot)
        # render at ~0.60x the saved 126px text template. Do not loosen
        # similarity globally; small-scale candidates require >=0.80.
        for scale in (.59,.60,.61,.62,.72,.79,.86,.93,1.,1.07,1.14,1.21,1.28,1.35):
            tile=cv2.resize(source,None,fx=scale,fy=scale,
                             interpolation=cv2.INTER_AREA)
            if tile.shape[0]>=region.shape[0] or tile.shape[1]>=region.shape[1]:
                continue
            heat=cv2.matchTemplate(region,tile,cv2.TM_CCOEFF_NORMED)
            ys,xs=np.where((heat >= (.80 if scale<.70 else .72))&
                (heat==cv2.dilate(heat,np.ones((9,25),np.uint8))))
            for y,x in zip(ys,xs):
                hits.append((float(heat[y,x]),int(x),int(y+24),
                             int(tile.shape[1]),int(tile.shape[0])))
        # The exact 2026-11-09 failure screenshot has a READY label at
        # ~0.64 of original text size. The old low-scale trials stop at
        # .62, while .72+ is too large. This independent in-game-only
        # template has been checked against menu/loading negative frames.
        secondary=_live_ready_v358_template()
        for scale in (.59,.60,.61,.62,.63,.64,.645,.65,.66,.67,.68):
            tile=cv2.resize(secondary,None,fx=scale,fy=scale,
                             interpolation=cv2.INTER_AREA)
            if tile.shape[0]>=region.shape[0] or tile.shape[1]>=region.shape[1]:
                continue
            heat=cv2.matchTemplate(region,tile,cv2.TM_CCOEFF_NORMED)
            ys,xs=np.where((heat>=.78)&
                (heat==cv2.dilate(heat,np.ones((9,25),np.uint8))))
            for y,x in zip(ys,xs):
                hits.append((float(heat[y,x]),int(x),int(y+24),
                             int(tile.shape[1]),int(tile.shape[0])))
        hits.sort(reverse=True)
        signs=list(old)
        for confidence,x,y,w,h in hits:
            cx=x+w/2
            cy=y+h/2
            if not .04<cx/960<.96:continue
            conflict=False
            duplicate_index=None
            for i,sign in enumerate(signs):
                dx=abs(sign['center_x']-cx/960)
                sy=sign.get('y',-1000)+sign.get('h',0)/2
                if dx<.095 and abs(cy-sy)<42:
                    if sign['status']!='READY_SIGN':conflict=True
                    else: duplicate_index=i
            if conflict:continue
            item=dict(status='READY_SIGN',confidence=round(confidence,3),
                      x=x,y=y,w=w,h=h,
                      center_x=round(cx/960,3),
                      relative_side=('LEFT' if cx<345 else
                                     'RIGHT' if cx>615 else 'CENTER'),
                      availability='UNVERIFIED')
            if duplicate_index is not None:
                if signs[duplicate_index]['confidence']<item['confidence']:
                    signs[duplicate_index]=item
                continue
            signs.append(item)
            if len(signs)>=7:break
        # "Создание лобби..." is BUSY/CREATING, NOT READY. The label may
        # replace READY as another player claims the same pad.
        creating=_pad_creating_sign_hints(raw)
        for busy in creating:
            signs=[p for p in signs if not
                   (p.get('status')=='READY_SIGN' and
                    abs(p.get('center_x',-9)-busy['center_x'])<.075 and
                    abs(p.get('y',-900)-busy['y'])<45)]
            signs.append(busy)
        signs.sort(key=lambda a:a.get('center_x',0))
        return signs
    except (cv2.error,ValueError):
        return old

# === End alternate live sign ===


def pad_sign_decision(hints):
    """Advisor only. No camera yaw, world position or movement output."""
    ready=[h for h in hints if h['status']=='READY_SIGN']
    busy=[h for h in hints if h['status']=='COUNTDOWN_SIGN']
    if not hints:
        return 'UNKNOWN: no confirmed pad signs; no movement'
    if any(a['relative_side']==b['relative_side'] for a in ready for b in busy):
        return 'AMBIGUOUS_SIGNS_IN_SAME_SCREEN_ZONE: no movement'
    center_ready=[h for h in ready if h['relative_side']=='CENTER']
    center_busy=[h for h in busy if h['relative_side']=='CENTER']
    if center_ready and center_busy:
        return 'CONFLICT: center signs overlap; no movement'
    if center_ready:
        return 'CENTER_READY_SIGN: needs verified facing and route; no movement'
    if center_busy and any(h['relative_side']=='RIGHT' for h in ready):
        return 'CENTER_COUNTDOWN_RIGHT_READY_SIGN: needs turn calibration; no movement'
    if ready:
        return 'READY_SIGN_OFF_AXIS: needs verified route; no movement'
    return 'ONLY_COUNTDOWN_SIGNS: wait outside pads; no movement'


def pad_sign_replay():
    """Review old PAD_SCOUT_OLD_VIDEO.zip without launching Roblox."""
    import zipfile
    import csv
    import io
    import cv2
    import numpy as np
    import json
    base=Path.home()/'Documents'/'RobloxBGDiagnostics'/'PAD_SCOUT'
    default=base/'PAD_SCOUT_OLD_VIDEO.zip'
    source=input('Existing PAD_SCOUT_OLD_VIDEO.zip (Enter=default): ').strip().strip('"')
    source=Path(source) if source else default
    if not source.is_file():
        print('PAD_SIGN_SOURCE_MISSING: '+str(source))
        return 2
    base.mkdir(parents=True,exist_ok=True)
    output=base/'PAD_SIGN_EVIDENCE_V34.zip'
    rows=[];summary=[]
    try:
        with zipfile.ZipFile(source) as z,zipfile.ZipFile(output,'w',
                compression=zipfile.ZIP_DEFLATED) as out:
            if z.testzip():
                print('PAD_SIGN_BAD_ZIP_CRC')
                return 2
            imgs=sorted(n for n in z.namelist() if
                n.startswith('view_') and n.endswith('s.jpg'))
            if len(imgs)<3 or len(imgs)>100:
                print('PAD_SIGN_UNEXPECTED_FRAME_COUNT')
                return 2
            for filename in imgs:
                second=int(filename.split('_')[1][:-5])
                raw=np.frombuffer(z.read(filename),dtype=np.uint8)
                img=cv2.imdecode(raw,cv2.IMREAD_COLOR)
                if img is None:
                    summary.append(filename+' undecodable')
                    continue
                signs=pad_sign_hints(img)
                decision=pad_sign_decision(signs)
                for item in signs:
                    rows.append([second,item['relative_side'],item['status'],
                                 item['confidence'],item['center_x'],
                                 item['availability']])
                summary.append('%03ds: '%second+', '.join(
                    f"{s['relative_side']}:{s['status']}({s['confidence']:.2f})"
                    for s in signs)+(' / '+decision))
                # Only draw game sign regions. Data remains on user's own PC.
                frame=cv2.resize(img,(960,540))
                for item in signs:
                    x,y,w,h=[item[key] for key in ('x','y','w','h')]
                    color=(30,220,40) if item['status']=='READY_SIGN' else (10,130,240)
                    cv2.rectangle(frame,(x,y),(x+w,y+h),color,2)
                    cv2.putText(frame,item['status'],(x,max(14,y-7)),
                                cv2.FONT_HERSHEY_SIMPLEX,.42,color,1,cv2.LINE_AA)
                encoded=cv2.imencode('.jpg',frame,[cv2.IMWRITE_JPEG_QUALITY,73])[1]
                out.writestr('classified_'+filename,encoded.tobytes())
            buf=io.StringIO();writer=csv.writer(buf)
            writer.writerow(['second','relative_side','sign','confidence','normalized_x',
                             'actual_availability'])
            writer.writerows(rows)
            out.writestr('pad_signs.csv',buf.getvalue())
            out.writestr('PAD_SIGN_STATUS_REPORT.txt',
                'ROBLOX PAD SIGN V3.4 / READ ONLY\n'
                'No game input. This is screen-relative label recognition, not occupancy verification.\n'
                'READY_SIGN does not prove a free slot, safe approach or an open menu.\n'
                'Do not navigate by fixed keys or screen X without calibrated camera pose.\n'
                'Do not stand on an occupied pad.\n'
                +'\n'.join(summary)+'\n')
        print('PAD_SIGN_REVIEW_READY: '+str(output))
        for row in summary:
            print(row)
        return 0
    except Exception:
        print('PAD_SIGN_REPLAY_ERROR '+traceback.format_exc())
        return 2


def pad_sign_live_observer():
    """Read-only live sign diagnostics: small private ZIP, no game controls.

    Keep the original CSV output; add 3 low-resolution captures so a zero-hit
    result can be diagnosed without another full OBS recording.
    """
    import queue
    import csv
    import ctypes
    import cv2
    import zipfile
    import io
    from windows_capture import WindowsCapture,Frame,InternalCaptureControl

    root=Path.home()/'Documents'/'RobloxBGDiagnostics'/'PAD_SCOUT'
    root.mkdir(parents=True,exist_ok=True)
    output=root/'PAD_SIGN_LIVE_REPORT.csv'
    bundle=root/'PAD_SIGN_LIVE_DIAGNOSTICS.zip'
    cap=WindowsCapture(cursor_capture=None,draw_border=None,
                       monitor_index=None,window_hwnd=verified_roblox_hwnd())
    queue_frames=queue.Queue(maxsize=1)
    stop=threading.Event()

    @cap.event
    def on_frame_arrived(frame:Frame,control:InternalCaptureControl):
        if stop.is_set():
            control.stop()
            return
        try:
            image=frame.frame_buffer[:,:,:3].copy()
            if queue_frames.full():
                try:queue_frames.get_nowait()
                except queue.Empty:pass
            queue_frames.put_nowait(image)
        except (queue.Full,ValueError):
            pass

    @cap.event
    def on_closed():
        stop.set()

    win=ctypes.WinDLL('user32',use_last_error=True)
    win.FindWindowW.argtypes=(ctypes.c_wchar_p,ctypes.c_wchar_p)
    win.FindWindowW.restype=ctypes.c_void_p
    win.GetForegroundWindow.restype=ctypes.c_void_p
    win.GetAsyncKeyState.argtypes=(ctypes.c_int,)
    win.GetAsyncKeyState.restype=ctypes.c_short
    hwnd=win.FindWindowW(None,'Roblox')
    def pressed():
        return bool(hwnd and win.GetForegroundWindow()==hwnd and
                    win.GetAsyncKeyState(0x79)&0x8000)

    print('PAD SIGNS V'+VERSION+': READ ONLY. NO WASD/MOUSE.')
    print('No OBS required. F10 in Roblox stops; 6-10 seconds is enough.')
    controller=None
    start=time.monotonic()
    last=0.0
    last_note=None
    saved=[]
    rows=0
    error=None
    try:
        controller=cap.start_free_threaded()
        with output.open('w',newline='',encoding='utf-8-sig') as fp:
            writer=csv.writer(fp)
            writer.writerow(['elapsed','signs','advice','frame_width',
                             'frame_height','aspect_h_over_w',
                             'scene_hint','detection_reason'])
            while not stop.is_set() and time.monotonic()-start<120:
                if pressed():
                    break
                try:
                    img=queue_frames.get(timeout=.5)
                except queue.Empty:
                    continue
                now=time.monotonic()
                if now-last<.85:
                    continue
                last=now
                H,W=img.shape[:2]
                elapsed=round(now-start,1)
                ratio=H/max(1,W)
                scene,_features=lifecycle_scene_hint(img)
                signs=pad_sign_hints(img)
                if W<500 or H<300:
                    reason='FRAME_TOO_SMALL'
                elif not .48<=ratio<=.62:
                    reason='ASPECT_OUTSIDE_TEMPLATE_RANGE'
                elif not signs:
                    reason='NO_SIGN_TEMPLATE_MATCH'
                else:
                    reason='SIGN_CANDIDATES'
                description=';'.join(
                    f"{s['relative_side']}:{s['status']}:{s['confidence']}"
                    for s in signs)
                advice=pad_sign_decision(signs)
                writer.writerow([elapsed,description,advice,W,H,
                                 round(ratio,4),scene,reason])
                rows+=1
                # Three bounded images from the exact WGC frames. This is the
                # only local image evidence, never uploaded or published by code.
                if ((len(saved)==0) or
                    (len(saved)==1 and elapsed>=3.0) or
                    (len(saved)==2 and elapsed>=7.0)):
                    preview=cv2.resize(img,(960,540),interpolation=cv2.INTER_AREA)
                    ok,encoded=cv2.imencode('.jpg',preview,
                                             [cv2.IMWRITE_JPEG_QUALITY,62])
                    if ok:
                        saved.append(('live_%02d.jpg'%len(saved),
                                      encoded.tobytes(),elapsed,scene,reason))
                current_note=reason+' '+description+' scene='+scene
                if current_note!=last_note:
                    print('PAD_SIGNS '+current_note+' | '+advice,flush=True)
                    last_note=current_note
        print('PAD_SIGN_LIVE_REPORT: '+str(output))
    except KeyboardInterrupt:
        print('PAD_SIGNS_CANCELLED: saving collected diagnostics')
    except Exception:
        error=traceback.format_exc()
        print('PAD_SIGN_LIVE_ERROR '+error)
    finally:
        stop.set()
        if controller is not None:
            try:controller.stop()
            except Exception:pass
    # Finalize evidence even when every recognition result was UNKNOWN.
    try:
        tmp=root/'PAD_SIGN_LIVE_DIAGNOSTICS.tmp'
        with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED) as z:
            if output.is_file():
                z.write(output,arcname='PAD_SIGN_LIVE_REPORT.csv')
            meta=[
                'ROBLOX PAD SIGN LIVE DIAGNOSTICS V'+VERSION,
                'Source: 3 scaled Windows Graphics Capture frames (max).',
                'No game keys or mouse clicks sent by this mode.',
                'Screenshots are PRIVATE: they may show other players or UI.',
                'Do NOT post this ZIP publicly on GitHub.',
                'UNKNOWN => no movement. READY_SIGN alone is NOT a free slot.',
                'Samples logged: '+str(rows),
                'Snapshots captured: '+str(len(saved)),
                'Error: '+(error or 'none'),
            ]
            for name,jpeg,at,scene,reason in saved:
                z.writestr(name,jpeg)
                meta.append('%s at %.1fs scene=%s reason=%s'%(name,at,scene,reason))
            z.writestr('DIAGNOSTICS_README.txt','\n'.join(meta)+'\n')
        with zipfile.ZipFile(tmp) as check:
            bad=check.testzip()
            if bad:
                raise RuntimeError('Corrupt diagnostic ZIP member: '+bad)
        tmp.replace(bundle)
        print('PAD_SIGN_DIAGNOSTIC_BUNDLE: '+str(bundle))
        if not saved:
            print('NO_FRAMES_CAPTURED: check Roblox not minimized.')
    except Exception:
        print('PAD_SIGN_BUNDLE_ERROR '+traceback.format_exc())
        return 2
    return 2 if error else 0


# === End V3.4 PAD SIGNS ===


def lifecycle_observer():
    """Observe start/menu/load/match/defeat/return without any Roblox input."""
    import queue
    import ctypes
    import cv2
    from windows_capture import WindowsCapture,Frame,InternalCaptureControl
    root=Path.home()/"Documents"/"RobloxBGDiagnostics"/"LIFECYCLE"
    root.mkdir(parents=True,exist_ok=True)
    log_file=root/"LIFECYCLE_REPORT.txt"
    loglines=["ROBLOX V"+VERSION+" lifecycle observer",
              "Video-derived VISUAL HINTS: not verified coordinates.",
              "State transitions are observations; no keys or mouse clicks."]
    def log(event):
        line=time.strftime("[%H:%M:%S] ")+event
        loglines.append(line)
        print(line,flush=True)
    frames=queue.Queue(maxsize=1)
    stop=threading.Event()
    cap=WindowsCapture(cursor_capture=None,draw_border=None,
                       monitor_index=None,window_hwnd=verified_roblox_hwnd())
    @cap.event
    def on_frame_arrived(frame:Frame,control:InternalCaptureControl):
        if stop.is_set():
            control.stop()
            return
        try:
            latest=frame.frame_buffer[:,:,:3].copy()
            if frames.full():
                try:frames.get_nowait()
                except queue.Empty:pass
            frames.put_nowait(latest)
        except (queue.Full,ValueError):
            pass
    @cap.event
    def on_closed():
        stop.set()
    ui=ctypes.WinDLL("user32",use_last_error=True)
    ui.GetAsyncKeyState.argtypes=(ctypes.c_int,)
    ui.GetAsyncKeyState.restype=ctypes.c_short
    ui.FindWindowW.argtypes=(ctypes.c_wchar_p,ctypes.c_wchar_p)
    ui.FindWindowW.restype=ctypes.c_void_p
    ui.GetForegroundWindow.restype=ctypes.c_void_p
    hwnd=ui.FindWindowW(None,"Roblox")
    def stop_pressed():
        # Only used if Roblox has focus: avoids reacting to other apps.
        return bool(hwnd and ui.GetForegroundWindow()==hwnd and
                    ui.GetAsyncKeyState(0x79)&0x8000)
    print("LIFECYCLE OBSERVER: read-only; no game control; up to 15 min.")
    print("F10 stops observer while Roblox is in foreground.")
    controller=None
    first=time.monotonic()
    last_check=0.
    gate=LifecycleGate()
    image_count=0
    try:
        controller=cap.start_free_threaded()
        while not stop.is_set() and time.monotonic()-first<900:
            if stop_pressed():
                log("STOP_F10")
                break
            try:
                img=frames.get(timeout=.5)
            except queue.Empty:
                continue
            now=time.monotonic()
            if now-last_check<.8:continue
            last_check=now
            state,details=lifecycle_scene_hint(img)
            committed,event=gate.observe(state,now)
            if not event:
                continue
            log(event+" raw="+state+" brightness="+
                str(round(details.get("brightness",0),1))+
                " red_fog="+str(round(details.get("red_fog",0),3)))
            if image_count<35:
                out=img
                h,w=img.shape[:2]
                if w>1100:
                    out=cv2.resize(img,(1100,round(h*1100/w)))
                name="state_%02d_%s.jpg"%(image_count,state)
                cv2.imwrite(str(root/name),out,[cv2.IMWRITE_JPEG_QUALITY,73])
                image_count+=1
        log("FINISHED: last_stable="+gate.state+
            " screenshots="+str(image_count))
    except KeyboardInterrupt:
        log("INTERRUPTED")
    except Exception:
        log("ERROR "+traceback.format_exc())
        return 2
    finally:
        stop.set()
        try:
            log_file.write_text("\n".join(loglines)+"\n",encoding="utf-8")
        except OSError as exc:
            print("LIFECYCLE_WRITE_ERROR "+repr(exc))
        print("LIFECYCLE_REPORT: "+str(log_file))
    return 0


def lobby_helper():
    """Guided lobby creation from the already-open Roblox creation pad.

    Uses Windows Graphics Capture frames, OpenCV HSV tests, client-area
    coordinates, verified state transitions, and explicitly foreground-only
    mouse input. No memory injection or hidden background input.
    """
    import ctypes
    import queue
    import cv2
    import numpy as np
    from ctypes import wintypes
    from windows_capture import WindowsCapture, Frame, InternalCaptureControl

    ui = ctypes.windll.user32
    ui.SetProcessDPIAware()
    hwnd = ui.FindWindowW(None, "Roblox")
    if not hwnd:
        print("LOBBY ERROR: Roblox window not found.")
        return 1

    folder = Path.home() / "Documents" / "RobloxBGDiagnostics" / "LOBBY"
    folder.mkdir(parents=True, exist_ok=True)
    logfile = folder / "lobby.log"
    print("\nROBLOX LOBBY BOT V"+VERSION)
    print("Target: City Landscape / 1 player / Hard / Create")
    print("Bot will click only if the Roblox window is focused.")
    print("You must first walk onto the purple creation pad.")
    print("The window can be observed from the background, but clicks require focus.")
    print("1 = observe only; 2 = enable real lobby clicks")
    mode = input("Select mode [1]: ").strip()
    enabled = mode == "2" and input("Confirm YES: ").strip().casefold() in ("yes", "да", "da")
    print("ARMED=" + str(enabled) + "; switch to Roblox. Ctrl+C = STOP.")
    q = queue.Queue(maxsize=1)
    stop = threading.Event()
    start = time.monotonic()
    max_wait_seconds=max(150,min(1800,int(os.environ.get(
        "ROBLOX_LOBBY_WAIT_SECONDS","900"))))
    last_update = 0.
    last_wait_note=-30.
    menu_confirmed_once=False
    pending_match_logged=False
    match_confirmations=0
    modal_seen = 0
    stage = "WAIT_MENU"
    last_features = None
    pending_step = None
    pending_before = None
    previous_stage = ""
    action_time = 0.
    retries = 0
    menu_closed = 0

    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
    class RECT(ctypes.Structure):
        _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                    ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

    def log(msg):
        line = time.strftime("[%H:%M:%S] ") + str(msg)
        print(line, flush=True)
        with logfile.open("a", encoding="utf-8") as fp:
            fp.write(line + "\n")

    def patch(frame, x1,y1,x2,y2):
        h,w = frame.shape[:2]
        return frame[max(0,int(y1*h)):min(h,int(y2*h)),
                     max(0,int(x1*w)):min(w,int(x2*w)),:3]

    def colormask(area, kind):
        if area.size == 0:
            return 0.
        hsv = cv2.cvtColor(area, cv2.COLOR_BGR2HSV)
        h,s,v = cv2.split(hsv)
        if kind == "green":
            mask = (h>=35)&(h<=90)&(s>95)&(v>80)
        elif kind == "red":
            mask = ((h<12)|(h>170))&(s>100)&(v>90)
        elif kind == "yellow":
            mask = (h>=18)&(h<=42)&(s>100)&(v>90)
        else:
            return 0.
        return float(mask.mean())

    def border_color(frame, rect, kind):
        x1,y1,x2,y2 = rect
        pad=.009
        segments = [patch(frame,x1,y1,x2,y1+pad),
                    patch(frame,x1,y2-pad,x2,y2),
                    patch(frame,x1,y1,x1+pad,y2),
                    patch(frame,x2-pad,y1,x2,y2)]
        return float(max(colormask(z,kind) for z in segments))

    def scan(frame):
        # Selected city map has a YELLOW outline, 1-player has GREEN.
        # Selected HARD uses a RED outline (not green); NORMAL has a
        # GREEN selected border. These are separate mutually exclusive modes.
        # This is not proof of GUI state without real post-click changes.
        create = border_color(frame,(.359,.833,.481,.914),"green")
        cancel = border_color(frame,(.519,.833,.642,.914),"red")
        players1 = border_color(frame,(.346,.672,.416,.805),"green")
        players2 = border_color(frame,(.426,.672,.496,.805),"green")
        players3 = border_color(frame,(.505,.672,.575,.805),"green")
        players4 = border_color(frame,(.583,.672,.655,.805),"green")
        city = border_color(frame,(.347,.517,.496,.647),"yellow")
        cave = border_color(frame,(.505,.517,.653,.647),"yellow")
        normal = border_color(frame,(.666,.620,.757,.670),"green")
        hard = border_color(frame,(.666,.674,.757,.720),"green")
        hard_red = border_color(frame,(.666,.674,.757,.720),"red")
        # The old color-only test mistook lobby scenery for the creation dialog.
        # Four large WHITE digits (1/2/3/4) must exist at the four slot centers.
        # A missing digit invalidates the whole dialog, even if color ROIs match.
        digit_boxes = [(.369,.716,.396,.785),(.449,.716,.476,.785),
                       (.529,.716,.556,.785),(.609,.716,.636,.785)]
        white_digits=[]
        for box in digit_boxes:
            roi=patch(frame,*box)
            if roi.size == 0:
                white_digits.append(0.0)
                continue
            b,g,r=[roi[:,:,i].astype(np.int16) for i in range(3)]
            white=((b>165)&(g>165)&(r>165)&
                   ((np.maximum(np.maximum(b,g),r)-np.minimum(np.minimum(b,g),r))<80))
            white_digits.append(float(white.mean()))
        # No clicks unless all four player-count digits are visible.
        count_digits=sum(1 for value in white_digits if value > .025)
        modal = create>.08 and cancel>.08 and count_digits == 4
        return modal,dict(create=create,cancel=cancel,p1=players1,
                p2=players2,p3=players3,p4=players4,city=city,cave=cave,normal=normal,hard=hard,
                hard_red=hard_red,digits=count_digits)

    # SendInput is the supported Windows synthetic input API. It still may
    # be ignored by Roblox; success means OS accepted the event, not the game.
    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long),
                    ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong),
                    ("time", ctypes.c_ulong), ("dwExtraInfo", ctypes.c_void_p)]
    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort),
                    ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong),
                    ("dwExtraInfo", ctypes.c_void_p)]
    class INPUTUNION(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]
    class INPUT(ctypes.Structure):
        _anonymous_ = ("data",)
        _fields_ = [("type", ctypes.c_ulong), ("data", INPUTUNION)]

    def send_mouse_flag(flag):
        event=INPUT()
        event.type=0
        event.mi=MOUSEINPUT(0,0,0,flag,0,None)
        return int(ui.SendInput(1,ctypes.byref(event),ctypes.sizeof(INPUT)))

    def send_scan_key(scan, extended=False):
        # Physical scan codes: backslash=0x2B, left=0x4B, enter=0x1C.
        # Roblox documents UI navigation: backslash, arrows, enter.
        if ui.IsIconic(hwnd) or ui.GetForegroundWindow()!=hwnd:
            return False
        flags=0x0008 | (0x0001 if extended else 0)
        down=INPUT()
        down.type=1
        down.ki=KEYBDINPUT(0,scan,flags,0,None)
        up=INPUT()
        up.type=1
        up.ki=KEYBDINPUT(0,scan,flags|0x0002,0,None)
        count1=int(ui.SendInput(1,ctypes.byref(down),ctypes.sizeof(INPUT)))
        time.sleep(.09)
        count2=int(ui.SendInput(1,ctypes.byref(up),ctypes.sizeof(INPUT)))
        return count1==1 and count2==1

    def nav_focus_scores(frame):
        # Blue/cyan UI-navigation outline is distinct from green active selection.
        # Look for NEW blue edge pixels relative to a pre-navigation baseline.
        rectangles=[
            (.346,.672,.416,.805),(.426,.672,.496,.805),
            (.505,.672,.575,.805),(.583,.672,.655,.805)]
        scores=[]
        for x1,y1,x2,y2 in rectangles:
            pad=.008
            strips=[patch(frame,x1,y1,x2,y1+pad),
                    patch(frame,x1,y2-pad,x2,y2),
                    patch(frame,x1,y1,x1+pad,y2),
                    patch(frame,x2-pad,y1,x2,y2)]
            total=0.0
            for area in strips:
                if area.size==0: continue
                hsv=cv2.cvtColor(area,cv2.COLOR_BGR2HSV)
                h,s,v=cv2.split(hsv)
                total=max(total,float(((h>=88)&(h<=130)&(s>90)&(v>105)).mean()))
            scores.append(total)
        return scores

    def send_mouse_move(px,py):
        # Emit an actual mouse MOVE event that game engines can receive.
        vx,vy=ui.GetSystemMetrics(76),ui.GetSystemMetrics(77)
        vw,vh=ui.GetSystemMetrics(78),ui.GetSystemMetrics(79)
        if vw<=0 or vh<=0: return 0
        xx=max(0,min(65535,round((px-vx)*65535/max(1,vw-1))))
        yy=max(0,min(65535,round((py-vy)*65535/max(1,vh-1))))
        ev=INPUT()
        ev.type=0
        ev.mi=MOUSEINPUT(xx,yy,0,0xC001,0,None)
        return int(ui.SendInput(1,ctypes.byref(ev),ctypes.sizeof(INPUT)))

    def click_legacy(relx,rely,frame):
        # Independent legacy mouse_event route. Do NOT enable UI Navigation.
        # A return only means Windows processed the injection call.
        if ui.IsIconic(hwnd) or ui.GetForegroundWindow()!=hwnd:
            return "SKIP_NOT_FOREGROUND"
        bounds=RECT()
        if not ui.GetClientRect(hwnd,ctypes.byref(bounds)):
            return "ERROR_CLIENT_RECT"
        width,height=bounds.right-bounds.left,bounds.bottom-bounds.top
        frame_h,frame_w=frame.shape[:2]
        extra_y,extra_x=frame_h-height,frame_w-width
        if not (0<=extra_y<=90 and 0<=extra_x<=50):
            return "ERROR_GEOMETRY"
        x=int(relx*frame_w-extra_x/2)
        y=int(rely*frame_h-extra_y)
        if not (0<=x<width and 0<=y<height):
            return "ERROR_TARGET_OUTSIDE_CLIENT"
        p=POINT(x,y)
        if not ui.ClientToScreen(hwnd,ctypes.byref(p)):
            return "ERROR_CLIENT_TO_SCREEN"
        if not ui.SetCursorPos(p.x,p.y):
            return "ERROR_SET_CURSOR"
        time.sleep(.22)
        actual=POINT()
        ui.GetCursorPos(ctypes.byref(actual))
        if abs(actual.x-p.x)+abs(actual.y-p.y)>6:
            return "ERROR_CURSOR_DRIFT"
        if ui.GetForegroundWindow()!=hwnd:
            return "ERROR_FOCUS_LOST"
        ui.mouse_event(0x0002,0,0,0,0)
        time.sleep(.22)
        state=bool(ui.GetAsyncKeyState(0x01) & 0x8000)
        ui.mouse_event(0x0004,0,0,0,0)
        log("LEGACY_MOUSE_TRACE target=(%d,%d) down_state=%s" %
            (p.x,p.y,str(state)))
        return "INPUT_SENT_UNVERIFIED"

    def click_window_message(relx,rely,frame):
        # Diagnostic alternate Windows GUI input path. Some games consume
        # only hardware/raw input, so this is an experiment, not a guarantee.
        if ui.IsIconic(hwnd) or ui.GetForegroundWindow()!=hwnd:
            return "SKIP_NOT_FOREGROUND"
        rect=RECT()
        if not ui.GetClientRect(hwnd,ctypes.byref(rect)):
            return "ERROR_CLIENT_RECT"
        width=rect.right-rect.left
        height=rect.bottom-rect.top
        frame_h,frame_w=frame.shape[:2]
        delta_y=frame_h-height
        delta_x=frame_w-width
        if not (0<=delta_y<=90 and 0<=delta_x<=50):
            return "ERROR_GEOMETRY"
        x=int(relx*frame_w-delta_x/2)
        y=int(rely*frame_h-delta_y)
        if not (0<=x<width and 0<=y<height):
            return "ERROR_TARGET_OUTSIDE_CLIENT"
        pt=POINT(x,y)
        if not ui.ClientToScreen(hwnd,ctypes.byref(pt)):
            return "ERROR_CLIENT_TO_SCREEN"
        if send_mouse_move(pt.x,pt.y)!=1:
            return "ERROR_SENDINPUT_MOVE"
        time.sleep(.25)
        if ui.GetForegroundWindow()!=hwnd:
            return "ERROR_FOCUS_LOST"
        lparam=(x & 0xFFFF)|((y & 0xFFFF)<<16)
        moved=ui.PostMessageW(hwnd,0x0200,0,lparam)
        time.sleep(.13)
        down=ui.PostMessageW(hwnd,0x0201,0x0001,lparam)
        time.sleep(.18)
        up=ui.PostMessageW(hwnd,0x0202,0,lparam)
        log("WM_INPUT_TRACE client=(%d,%d) screen=(%d,%d) move=%d down=%d up=%d" %
            (x,y,pt.x,pt.y,moved,down,up))
        return "INPUT_SENT_UNVERIFIED" if moved and down and up else "INPUT_REJECTED"

    def click(relx,rely,frame):
        # Coordinates in recognizer are normalized to the whole WGC frame.
        # On this PC the captured frame is 1920x1030 while the client
        # area is 1920x1001 (the extra 29 pixels are the title bar).
        if ui.IsIconic(hwnd) or ui.GetForegroundWindow()!=hwnd:
            return "SKIP_NOT_FOREGROUND"
        rect=RECT()
        if not ui.GetClientRect(hwnd,ctypes.byref(rect)):
            return "ERROR_CLIENT_RECT"
        width=rect.right-rect.left
        height=rect.bottom-rect.top
        frame_h,frame_w=frame.shape[:2]
        offset_y=frame_h-height
        offset_x=frame_w-width
        if offset_y<0 or offset_y>90 or offset_x<0 or offset_x>50:
            log("STOP_INPUT_GEOMETRY frame=%dx%d client=%dx%d delta=%dx%d" %
                (frame_w,frame_h,width,height,offset_x,offset_y))
            return "ERROR_GEOMETRY"
        # Translate a WGC frame point into the client area.
        client_x=int(relx*frame_w-offset_x/2)
        client_y=int(rely*frame_h-offset_y)
        if not (0<=client_x<width and 0<=client_y<height):
            return "ERROR_TARGET_OUTSIDE_CLIENT"
        p=POINT(client_x,client_y)
        if not ui.ClientToScreen(hwnd,ctypes.byref(p)):
            return "ERROR_CLIENT_TO_SCREEN"
        before=POINT()
        ui.GetCursorPos(ctypes.byref(before))
        if send_mouse_move(p.x,p.y)!=1:
            return "ERROR_SENDINPUT_MOVE"
        time.sleep(.27)
        actual=POINT()
        ui.GetCursorPos(ctypes.byref(actual))
        drift=abs(actual.x-p.x)+abs(actual.y-p.y)
        log("CURSOR_TRACE before=(%d,%d) target=(%d,%d) actual=(%d,%d) drift=%d frame=%dx%d client=%dx%d" %
            (before.x,before.y,p.x,p.y,actual.x,actual.y,drift,
             frame_w,frame_h,width,height))
        if drift>7:
            log("STOP_INPUT_CURSOR_MOVED: Roblox or other software changed cursor position")
            return "ERROR_CURSOR_DRIFT"
        if ui.GetForegroundWindow()!=hwnd:
            return "ERROR_FOCUS_LOST"
        if send_mouse_move(p.x,p.y)!=1:
            return "ERROR_SENDINPUT_MOVE_BEFORE_PRESS"
        time.sleep(.09)
        down=send_mouse_flag(0x0002)
        time.sleep(.28)
        up=send_mouse_flag(0x0004)
        time.sleep(.55)
        after=POINT()
        ui.GetCursorPos(ctypes.byref(after))
        log("INPUT_TRACE target=(%d,%d) after=(%d,%d) SendInput=%d/%d" %
            (p.x,p.y,after.x,after.y,down,up))
        return "INPUT_SENT_UNVERIFIED" if down==1 and up==1 else "INPUT_REJECTED"


    # V1.9: Arduino Leonardo / Micro with USB HID and serial COM control.
    # Only an explicitly configured COM device can receive mouse commands.
    import re
    hid_port=os.environ.get("ROBLOX_HID_PORT","").strip().upper()
    backend=os.environ.get("ROBLOX_INPUT_BACKEND","SYNTHETIC").strip().upper()
    if backend not in ("SYNTHETIC","TOUCH","HID","SOFTWARE"):
        log("INPUT_BACKEND_INVALID: "+backend+"; observe only")
        enabled=False
    if backend=="HID":
        try:
            import serial
            from serial.tools import list_ports
        except ImportError:
            log("HID_DEPENDENCY_MISSING: install once using py -m pip install pyserial")
            enabled=False
        else:
            if not hid_port:
                candidates=[entry.device for entry in list_ports.comports()
                            if entry.vid in (0x2341,0x2A03,0x1B4F)]
                if len(candidates)==1:
                    hid_port=candidates[0].upper()
                    log("HID_AUTO_PORT "+hid_port+"; firmware identity still verified")
                elif len(candidates)>1:
                    log("HID_AMBIGUOUS: set ROBLOX_HID_PORT to one COM port")
                    enabled=False
                else:
                    log("HID_NOT_FOUND: plug in flashed Arduino Leonardo/Micro "+
                        "or set ROBLOX_HID_PORT explicitly. Observe only.")
                    enabled=False
    if backend=="HID" and hid_port and not re.fullmatch(r"COM[1-9][0-9]{0,2}",hid_port):
        log("HID_INVALID_PORT: expected COM1..COM999; observe only")
        enabled=False
    if backend=="HID" and not hid_port:
        enabled=False
    if backend=="SYNTHETIC":
        try:
            api_check=ctypes.WinDLL("user32",use_last_error=True)
            for name in ("CreateSyntheticPointerDevice",
                         "InjectSyntheticPointerInput",
                         "DestroySyntheticPointerDevice"):
                getattr(api_check,name)
            log("SYNTH_API_AVAILABLE: Windows pointer functions found. "+
                "Game reception not yet verified.")
        except (AttributeError,OSError) as exc:
            log("SYNTH_API_UNAVAILABLE: "+repr(exc))
            enabled=False
    if backend=="TOUCH":
        try:
            touch_check=ctypes.WinDLL("user32",use_last_error=True)
            getattr(touch_check,"InitializeTouchInjection")
            getattr(touch_check,"InjectTouchInput")
            log("TOUCH_API_AVAILABLE: Windows touch functions found. "+
                "Roblox handling of synthetic touch is not yet verified.")
        except (AttributeError,OSError) as exc:
            log("TOUCH_API_UNAVAILABLE: "+repr(exc))
            enabled=False
    if mode=="2" and not enabled:
        log("NO_INPUT: backend="+backend+" is not ready; no clicks sent.")
        if backend=="HID":
            print("HID mode needs a flashed Arduino Leonardo/Micro.")
            print("Install driver: py -m pip install pyserial")
        else:
            print("Input mode disabled; recheck ROBLOX_INPUT_BACKEND.")
        return 2
    log("INPUT_BACKEND="+backend+
        (" (Windows touch injection, no extra hardware)" if backend=="TOUCH" else ""))

    # Pure Windows touch injection, no Arduino, no third-party drivers.
    # Based on winuser.h POINTER_TOUCH_INFO and InjectTouchInput. Do NOT
    # enter Roblox UI Navigation or interfere with its WASD bindings.
    class TOUCH_POINT(ctypes.Structure):
        _fields_=[("x",ctypes.c_int32),("y",ctypes.c_int32)]
    class TOUCH_RECT(ctypes.Structure):
        _fields_=[("left",ctypes.c_int32),("top",ctypes.c_int32),
                  ("right",ctypes.c_int32),("bottom",ctypes.c_int32)]
    class POINTER_INFO(ctypes.Structure):
        _fields_=[
            ("pointerType",ctypes.c_uint32),("pointerId",ctypes.c_uint32),
            ("frameId",ctypes.c_uint32),("pointerFlags",ctypes.c_uint32),
            ("sourceDevice",ctypes.c_void_p),("hwndTarget",ctypes.c_void_p),
            ("ptPixelLocation",TOUCH_POINT),
            ("ptHimetricLocation",TOUCH_POINT),
            ("ptPixelLocationRaw",TOUCH_POINT),
            ("ptHimetricLocationRaw",TOUCH_POINT),
            ("dwTime",ctypes.c_uint32),("historyCount",ctypes.c_uint32),
            ("InputData",ctypes.c_int32),("dwKeyStates",ctypes.c_uint32),
            ("PerformanceCount",ctypes.c_uint64),
            ("ButtonChangeType",ctypes.c_uint32)]
    class POINTER_TOUCH_INFO(ctypes.Structure):
        _fields_=[("pointerInfo",POINTER_INFO),
                  ("touchFlags",ctypes.c_uint32),
                  ("touchMask",ctypes.c_uint32),
                  ("rcContact",TOUCH_RECT),
                  ("rcContactRaw",TOUCH_RECT),
                  ("orientation",ctypes.c_uint32),
                  ("pressure",ctypes.c_uint32)]
    touch_state={"initialized":False}
    def click_touch(relx,rely,frame):
        # Foreground only; do not move the mouse cursor.
        if ui.IsIconic(hwnd) or ui.GetForegroundWindow()!=hwnd:
            return "SKIP_NOT_FOREGROUND"
        rect=RECT()
        if not ui.GetClientRect(hwnd,ctypes.byref(rect)):
            return "ERROR_CLIENT_RECT"
        fw,fh=frame.shape[1],frame.shape[0]
        cw,ch=rect.right-rect.left,rect.bottom-rect.top
        extra_x,extra_y=fw-cw,fh-ch
        if not (0<=extra_x<=50 and 0<=extra_y<=90):
            log("TOUCH_GEOMETRY frame=%dx%d client=%dx%d" %
                (fw,fh,cw,ch))
            return "ERROR_TOUCH_GEOMETRY"
        cx=int(relx*fw-extra_x/2)
        cy=int(rely*fh-extra_y)
        if not (0<=cx<cw and 0<=cy<ch):
            return "ERROR_TOUCH_OUTSIDE_CLIENT"
        target=POINT(cx,cy)
        if not ui.ClientToScreen(hwnd,ctypes.byref(target)):
            return "ERROR_TOUCH_CLIENT_TO_SCREEN"
        if not (ctypes.sizeof(POINTER_INFO)==96 and
                ctypes.sizeof(POINTER_TOUCH_INFO)==144):
            log("TOUCH_ABI_MISMATCH info=%d touch=%d" %
                (ctypes.sizeof(POINTER_INFO),ctypes.sizeof(POINTER_TOUCH_INFO)))
            return "ERROR_TOUCH_ABI"
        try:
            touch_api=ctypes.WinDLL("user32",use_last_error=True)
            initialize=touch_api.InitializeTouchInjection
            initialize.argtypes=(ctypes.c_uint32,ctypes.c_uint32)
            initialize.restype=ctypes.c_int
            inject=touch_api.InjectTouchInput
            inject.argtypes=(ctypes.c_uint32,ctypes.POINTER(POINTER_TOUCH_INFO))
            inject.restype=ctypes.c_int
            if not touch_state["initialized"]:
                ctypes.set_last_error(0)
                if not initialize(1,3):  # TOUCH_FEEDBACK_NONE
                    code=ctypes.get_last_error()
                    log("TOUCH_INIT_FAILED WinError="+str(code))
                    return "ERROR_TOUCH_INIT"
                touch_state["initialized"]=True
            contact=POINTER_TOUCH_INFO()
            contact.pointerInfo.pointerType=2  # PT_TOUCH
            contact.pointerInfo.pointerId=0
            contact.pointerInfo.ptPixelLocation=TOUCH_POINT(target.x,target.y)
            contact.pointerInfo.pointerFlags=0x10006  # DOWN|INRANGE|INCONTACT
            contact.touchMask=0x07  # area, orientation, pressure
            contact.orientation=90
            contact.pressure=512
            contact.rcContact=TOUCH_RECT(target.x-3,target.y-3,
                                         target.x+3,target.y+3)
            contact.rcContactRaw=contact.rcContact
            if ui.GetForegroundWindow()!=hwnd:
                return "ERROR_TOUCH_FOCUS_LOST"
            ctypes.set_last_error(0)
            if not inject(1,ctypes.byref(contact)):
                log("TOUCH_DOWN_FAILED WinError="+str(ctypes.get_last_error()))
                return "ERROR_TOUCH_DOWN"
            time.sleep(.085)
            contact.pointerInfo.pointerFlags=0x40000  # POINTER_FLAG_UP
            ctypes.set_last_error(0)
            if not inject(1,ctypes.byref(contact)):
                log("TOUCH_UP_FAILED WinError="+str(ctypes.get_last_error()))
                return "ERROR_TOUCH_UP"
            log("TOUCH_SENT screen=(%d,%d) client=(%d,%d) status=UNVERIFIED" %
                (target.x,target.y,cx,cy))
            return "INPUT_SENT_UNVERIFIED"
        except (AttributeError,OSError) as exc:
            log("TOUCH_API_UNAVAILABLE "+repr(exc))
            return "ERROR_TOUCH_UNSUPPORTED"

    # Windows 10 1809+ software synthetic TOUCH device.
    # This is independent of the legacy InjectTouchInput API, which returned
    # ERROR_INVALID_PARAMETER (87) on the user's Windows laptop.
    class POINTER_TYPE_UNION(ctypes.Union):
        _fields_=[("pointerInfo",POINTER_INFO),
                  ("touchInfo",POINTER_TOUCH_INFO)]
    class POINTER_TYPE_INFO(ctypes.Structure):
        _fields_=[("type",ctypes.c_uint32),
                  ("info",POINTER_TYPE_UNION)]
    def click_synthetic(relx,rely,frame):
        if ui.IsIconic(hwnd) or ui.GetForegroundWindow()!=hwnd:
            return "SKIP_NOT_FOREGROUND"
        rect=RECT()
        if not ui.GetClientRect(hwnd,ctypes.byref(rect)):
            return "ERROR_CLIENT_RECT"
        fw,fh=frame.shape[1],frame.shape[0]
        cw,ch=rect.right-rect.left,rect.bottom-rect.top
        dx,dy=fw-cw,fh-ch
        if not(0<=dx<=50 and 0<=dy<=90):
            log("SYNTH_GEOMETRY_INVALID frame=%dx%d client=%dx%d"%
                (fw,fh,cw,ch))
            return "ERROR_SYNTH_GEOMETRY"
        cx=int(relx*fw-dx/2)
        cy=int(rely*fh-dy)
        if not(0<=cx<cw and 0<=cy<ch):
            return "ERROR_SYNTH_POINT"
        screen=POINT(cx,cy)
        if not ui.ClientToScreen(hwnd,ctypes.byref(screen)):
            return "ERROR_SYNTH_CONVERSION"
        # x64 POINTER_TYPE_INFO has an 8-byte aligned anonymous union.
        if ctypes.sizeof(POINTER_TYPE_INFO)!=152 or POINTER_TYPE_INFO.info.offset!=8:
            log("SYNTH_ABI_INVALID size=%d offset=%d"%
                (ctypes.sizeof(POINTER_TYPE_INFO),POINTER_TYPE_INFO.info.offset))
            return "ERROR_SYNTH_ABI"
        device=None
        try:
            api=ctypes.WinDLL("user32",use_last_error=True)
            create=api.CreateSyntheticPointerDevice
            inject=api.InjectSyntheticPointerInput
            destroy=api.DestroySyntheticPointerDevice
            create.argtypes=(ctypes.c_uint32,ctypes.c_uint32,ctypes.c_uint32)
            create.restype=ctypes.c_void_p
            inject.argtypes=(ctypes.c_void_p,
                             ctypes.POINTER(POINTER_TYPE_INFO),ctypes.c_uint32)
            inject.restype=ctypes.c_int
            destroy.argtypes=(ctypes.c_void_p,)
            destroy.restype=None
            ctypes.set_last_error(0)
            device=create(2,1,3) # PT_TOUCH, one contact, no feedback
            if not device:
                log("SYNTH_CREATE_FAILED WinError="+str(ctypes.get_last_error()))
                return "ERROR_SYNTH_CREATE"
            contact=POINTER_TYPE_INFO()
            contact.type=2
            touch=contact.info.touchInfo
            touch.pointerInfo.pointerType=2
            touch.pointerInfo.pointerId=0
            # Microsoft's synthetic pointer API documents screen positions
            # relative to the top-left corner of the virtual screen.
            origin_x=ui.GetSystemMetrics(76) # SM_XVIRTUALSCREEN
            origin_y=ui.GetSystemMetrics(77) # SM_YVIRTUALSCREEN
            px,py=screen.x-origin_x,screen.y-origin_y
            touch.pointerInfo.ptPixelLocation=TOUCH_POINT(px,py)
            touch.pointerInfo.pointerFlags=0x10006
            touch.touchMask=0x7
            touch.orientation=90
            touch.pressure=512
            touch.rcContact=TOUCH_RECT(px-3,py-3,px+3,py+3)
            touch.rcContactRaw=touch.rcContact
            if ui.GetForegroundWindow()!=hwnd:
                return "ERROR_SYNTH_FOCUS"
            ctypes.set_last_error(0)
            if not inject(device,ctypes.byref(contact),1):
                log("SYNTH_DOWN_FAILED WinError="+str(ctypes.get_last_error())+
                    " x="+str(px)+" y="+str(py))
                return "ERROR_SYNTH_DOWN"
            time.sleep(.07)
            touch.pointerInfo.pointerFlags=0x40000
            ctypes.set_last_error(0)
            if not inject(device,ctypes.byref(contact),1):
                log("SYNTH_UP_FAILED WinError="+str(ctypes.get_last_error()))
                return "ERROR_SYNTH_UP"
            log("SYNTH_SENT point=(%d,%d) status=UNVERIFIED"%(px,py))
            return "INPUT_SENT_UNVERIFIED"
        except (AttributeError,OSError) as exc:
            log("SYNTH_API_UNAVAILABLE "+repr(exc))
            return "ERROR_SYNTH_API"
        finally:
            if device:
                try:
                    destroy(device)
                except Exception as exc:
                    log("SYNTH_DESTROY_NOTE "+repr(exc))

    def usb_hid_mouse_click(relx,rely,frame):
        # USB serial commands go to a genuine HID board, not Windows SendInput.
        if ui.IsIconic(hwnd) or ui.GetForegroundWindow()!=hwnd:
            return "SKIP_NOT_FOREGROUND"
        rect=RECT()
        if not ui.GetClientRect(hwnd,ctypes.byref(rect)):
            return "ERROR_CLIENT_RECT"
        fw,fh=frame.shape[1],frame.shape[0]
        cw,ch=rect.right-rect.left,rect.bottom-rect.top
        dx_frame,dy_frame=fw-cw,fh-ch
        if not (0<=dx_frame<=50 and 0<=dy_frame<=90):
            return "ERROR_HID_GEOMETRY"
        cx=int(relx*fw-dx_frame/2)
        cy=int(rely*fh-dy_frame)
        if not (0<=cx<cw and 0<=cy<ch):
            return "ERROR_HID_POINT"
        target=POINT(cx,cy)
        if not ui.ClientToScreen(hwnd,ctypes.byref(target)):
            return "ERROR_HID_CLIENT_TO_SCREEN"
        link=None
        try:
            import serial
            # Native-USB boards can reboot when the COM port opens.
            # Handshake prevents accidentally using a different serial device.
            link=serial.Serial(port=hid_port,baudrate=115200,
                               timeout=.65,write_timeout=.65)
            def command(word,expected):
                link.reset_input_buffer()
                link.write((word+"\n").encode("ascii"))
                link.flush()
                answer=link.readline().decode("ascii","replace").strip()
                if answer!=expected:
                    raise RuntimeError("HID command "+word.split()[0]+
                                       " response="+repr(answer))
            found=False
            for _ in range(7):
                try:
                    command("HELLO","ROBLOX_HID_V1")
                    found=True
                    break
                except RuntimeError:
                    time.sleep(.3)
            if not found:
                raise RuntimeError("HID handshake failed: check firmware and port")
            command("ARM ROBLOX_HID_V1","OK ARMED")
            last_error=1000000
            stagnant=0
            reached=False
            for iteration in range(80):
                if ui.GetForegroundWindow()!=hwnd:
                    raise RuntimeError("Roblox lost focus during HID motion")
                current=POINT()
                if not ui.GetCursorPos(ctypes.byref(current)):
                    raise RuntimeError("GetCursorPos failed")
                ex,ey=target.x-current.x,target.y-current.y
                error=abs(ex)+abs(ey)
                if error<=5:
                    reached=True
                    break
                if error>=last_error-1:
                    stagnant+=1
                else:
                    stagnant=0
                if stagnant>=10:
                    raise RuntimeError("HID pointer did not converge")
                last_error=error
                mx=max(-65,min(65,ex))
                my=max(-65,min(65,ey))
                command("MOVE %d %d"%(mx,my),"OK MOVE")
                time.sleep(.035)
            if not reached:
                raise RuntimeError("HID pointer target timeout")
            if ui.GetForegroundWindow()!=hwnd:
                raise RuntimeError("Roblox lost focus before HID click")
            command("CLICK","OK CLICK")
            log("HID_CLICK_SENT target=(%d,%d) port=%s; game confirmation pending" %
                (target.x,target.y,hid_port))
            return "INPUT_SENT_UNVERIFIED"
        except Exception as error:
            log("HID_ERROR "+str(error))
            return "ERROR_HID_DEVICE"
        finally:
            if link is not None:
                try:
                    link.write(b"DISARM\n")
                    link.flush()
                except Exception:
                    pass
                try:
                    link.close()
                except Exception:
                    pass

    capture = WindowsCapture(cursor_capture=None,draw_border=None,
                             monitor_index=None,window_hwnd=verified_roblox_hwnd())

    @capture.event
    def on_frame_arrived(frame: Frame, control: InternalCaptureControl):
        if stop.is_set():
            control.stop()
            return
        if q.full():
            return
        try:
            q.put_nowait(frame.frame_buffer[:,:,:3].copy())
        except queue.Full:
            pass

    @capture.event
    def on_closed():
        stop.set()

    # V2.1.3: strict sequential steps. Retry ONLY the last unconfirmed step.
    # Never re-click an earlier option after moving on, to avoid toggling it off.
    controller = None
    step_names = ("city","one","hard","create")
    step_points = {"city":(.400,.585),"one":(.382,.745),
                   "hard":(.710,.707),"create":(.420,.870)}
    step_index = 0
    retries = {name:0 for name in step_names}
    stable_count = 0
    previous_result = None
    awaiting_confirmation = False
    last_click = 0.0
    menu_present_count = 0
    menu_absent_count = 0
    completed = False
    # Stable synthetic taps work in Roblox, but a single tap can be missed.
    # Retry only UNCONFIRMED settings, with a strict per-setting upper bound.
    # CREATE itself is never repeated automatically.
    attempt_limits = ({"city":2,"one":3,"hard":2,"create":1}
                      if backend=="SYNTHETIC" else
                      {"city":1,"one":1,"hard":1,"create":1}
                      if backend in ("HID","TOUCH") else
                      {"city":2,"one":2,"hard":2,"create":1})
    manual_prompted = False
    last_gate_note = 0.0
    ready_override_logged = False
    nav_phase = "off"
    nav_step_at = 0.0
    nav_count = 0
    nav_baseline = None
    nav_last_scores = None
    drift_events=0
    freeze_until=0.0
    evidence_dir = folder / "LAST_CLICK"
    evidence_dir.mkdir(parents=True,exist_ok=True)
    evidence_pending = None
    player_selection_before = None
    def player_selected(feat):
        values=[feat["p1"],feat["p2"],feat["p3"],feat["p4"]]
        indices=[i+1 for i,v in enumerate(values) if v>.15]
        return indices[0] if len(indices)==1 else 0
    def selected_flags(feat):
        return {
            "city": feat["city"]>.15 and feat["cave"]<.12,
            "one": player_selected(feat)==1,
            # Hard is highlighted RED; normal is highlighted GREEN.
            # Require red on Hard AND no green on Normal to avoid mistaking
            # a hovered-but-unselected Hard tile for the chosen difficulty.
            "hard": feat["hard_red"]>.18 and feat["normal"]<.12
        }
    log("Lobby v"+VERSION+" start; armed="+str(enabled))
    log("PAD_AVAILABILITY_RULE: do not infer occupied/free from absent GUI; "+
        "wait until the FOUR player tiles AND Create/Cancel appear.")
    log("WAIT_WINDOW_SECONDS="+str(max_wait_seconds)+
        " (default 900s to allow other player to leave the pad)")
    log("Strict sequence CITY -> ONE -> HARD(RED BORDER) -> CREATE")
    log("SYNTHETIC retries: up to 3 verified attempts for ONE, 2 for HARD; "+
        "CREATE strictly once. Alternate safe points inside the same tile.")
    log("HARD_CHECK requires red hard border + normal green not selected")
    log("Before/after click evidence in "+str(evidence_dir)+"; JPEG overwritten per step.")
    try:
        controller=capture.start_free_threaded()
        while not stop.is_set() and time.monotonic()-start < max_wait_seconds:
            try:
                frame=q.get(timeout=.5)
            except queue.Empty:
                continue
            if time.monotonic()-last_update < .30:
                continue
            last_update=time.monotonic()
            modal,features=scan(frame)
            if evidence_pending is not None and time.monotonic()-last_click >= .9:
                label=evidence_pending
                reduced=cv2.resize(frame,(960,round(frame.shape[0]*960/frame.shape[1])))
                cv2.imwrite(str(evidence_dir / ("after_"+label+".jpg")),reduced,
                            [cv2.IMWRITE_JPEG_QUALITY,70])
                log("EVIDENCE_SAVED after_"+label+".jpg; captured frame after click")
                evidence_pending=None
            if not modal:
                menu_present_count=0
                previous_result=None
                stable_count=0
                now_wait=time.monotonic()
                if not completed and step_index<3 and now_wait-last_wait_note>=30:
                    log("WAIT_PAD_CREATION_GUI: no complete creation menu. "+
                        "Possible reasons: pad occupied, player not on pad, "+
                        "or lobby/loading UI. Occupancy UNKNOWN; no clicks.")
                    last_wait_note=now_wait
                    if ui.GetForegroundWindow()==hwnd:
                        reduced=cv2.resize(
                            frame,(960,round(frame.shape[0]*960/frame.shape[1])))
                        cv2.imwrite(str(evidence_dir/"wait_pad_menu.jpg"),reduced,
                                    [cv2.IMWRITE_JPEG_QUALITY,65])
                if step_index==3 and awaiting_confirmation:
                    # A disappearing Create dialog is NOT match confirmation:
                    # the real video has a portal countdown + loading transition.
                    if not pending_match_logged:
                        log("CREATE_DIALOG_CLOSED: observing game HUD; "+
                            "DO NOT assume start from closed menu.")
                        pending_match_logged=True
                    scene,metrics=lifecycle_scene_hint(frame)
                    match_confirmations=(match_confirmations+1
                                         if scene=="MATCH" else 0)
                    if match_confirmations>=3:
                        completed=True
                        log("MATCH_CONFIRMED: three fresh in-game HUD frames "+
                            "after Create, no input sent after Create.")
                        break
                    if time.monotonic()-last_click>45:
                        log("STOP_CREATE_UNVERIFIED: HUD never confirmed within "+
                            "45s; do not repeat Create.")
                        break
                continue
            menu_absent_count=0
            menu_present_count+=1
            if menu_present_count<4:
                continue
            if not menu_confirmed_once:
                menu_confirmed_once=True
                log("PAD_CREATION_GUI_CONFIRMED: four player tiles + Create/Cancel "+
                    "stable; menu is available, proceed with guarded configuration.")
            flags=selected_flags(features)
            if previous_result==flags:
                stable_count+=1
            else:
                stable_count=1
                previous_result=flags.copy()
            if stable_count<3:
                continue
            # A verified screen state is authoritative. The earlier sequential
            # bookkeeping can lag after rapid real input / transient UI frames.
            # Never bypass selection verification or send Create twice.
            if all(flags.values()) and retries["create"]==0 and step_index<3:
                if awaiting_confirmation and time.monotonic()-last_click<1.2:
                    continue
                log("ALL_SETTINGS_VERIFIED: CITY/ONE/HARD simultaneously selected; "+
                    "advance to CREATE from step="+step_names[step_index]+
                    " flags="+str(flags))
                step_index=3
                awaiting_confirmation=False
                previous_result=None
                ready_override_logged=True
            if step_index>=3 and awaiting_confirmation:
                # We have sent Create. Do not click anything else.
                if time.monotonic()-last_click>12:
                    log("STOP: Create was sent, dialog stayed open. No auto-repeat.")
                    break
                continue
            if not enabled or ui.GetForegroundWindow()!=hwnd:
                if all(flags.values()) and time.monotonic()-last_gate_note>5:
                    log("CREATE_BLOCKED_INPUT_GATE enabled="+str(enabled)+
                        " foreground="+str(ui.GetForegroundWindow()==hwnd)+
                        " step="+step_names[step_index])
                    last_gate_note=time.monotonic()
                continue
            # Do not interpret transitional UI frames as permanent loss of
            # earlier selections; finish checking pending click first.
            if awaiting_confirmation and time.monotonic()-last_click<3.0:
                continue
            earlier=step_names[:step_index]
            missing=[k for k in earlier if not flags[k]]
            if missing:
                drift_events+=1
                log("CONFIG_DRIFT: previous selection no longer confirmed; "+
                    "missing="+str(missing)+" current="+str(flags)+
                    " count="+str(drift_events))
                if drift_events>2:
                    log("STOP: too many configuration changes; no unsafe Create")
                    break
                # Re-check the earliest missing configuration step, and allow
                # exactly one new click for that setting. Never click Create
                # until all three settings are simultaneously verified.
                step_index=step_names.index(missing[0])
                retries[missing[0]]=0
                awaiting_confirmation=False
                nav_phase="off"
                nav_count=0
                nav_baseline=None
                manual_prompted=False
                previous_result=None
                stable_count=0
                freeze_until=time.monotonic()+1.25
                continue
            if time.monotonic()<freeze_until:
                continue
            key=step_names[step_index]
            if key=="create":
                if not all(flags.values()):
                    log("STOP: not all selections verified, will not Create: "+str(flags))
                    break
                if time.monotonic()-last_click<1.5:
                    continue
                # Button centre from observed lobby GUI: x=0.420, y=0.872
                # in the full WGC window (not desktop taskbar coordinates).
                # One deliberate attempt only; never press twice blindly.
                target=(.420,.872)
                log("CREATE_READY flags="+str(flags)+" backend="+backend+
                    " target="+str(target)+
                    " frame="+str(frame.shape[1])+"x"+str(frame.shape[0])+
                    " foreground="+str(ui.GetForegroundWindow()==hwnd))
                reduced=cv2.resize(frame,(960,round(frame.shape[0]*960/frame.shape[1])))
                cv2.imwrite(str(evidence_dir / "before_create.jpg"),reduced,
                            [cv2.IMWRITE_JPEG_QUALITY,70])
                if backend=="SYNTHETIC":
                    result=click_synthetic(*target,frame)
                elif backend=="TOUCH":
                    result=click_touch(*target,frame)
                elif backend=="HID":
                    result=usb_hid_mouse_click(*target,frame)
                else:
                    result=click(*target,frame)
                if result=="INPUT_SENT_UNVERIFIED":
                    evidence_pending="create"
                retries[key]+=1
                last_click=time.monotonic()
                awaiting_confirmation=True
                log("ACTION CREATE result="+result+" selected="+str(flags))
                if result!="INPUT_SENT_UNVERIFIED":
                    log("STOP: OS did not accept Create")
                    break
                continue
            if flags[key]:
                # Confirm current choice from fresh frame readings before advancing.
                if awaiting_confirmation:
                    log("STEP_VERIFIED: "+key+" after attempt="+str(retries[key]))
                else:
                    log("STEP_ALREADY_SELECTED: "+key)
                awaiting_confirmation=False
                manual_prompted=False
                nav_phase="off"
                step_index+=1
                stable_count=0
                previous_result=None
                continue
            if awaiting_confirmation:
                if time.monotonic()-last_click<3.0:
                    continue
                if key=="one":
                    now_player=player_selected(features)
                    log("PLAYER_STATE_BEFORE_AFTER before="+str(player_selection_before)+
                        " after="+str(now_player)+
                        " p="+str([round(features["p"+str(i)],3) for i in range(1,5)]))
                    if now_player!=player_selection_before and now_player!=1:
                        log("STOP: click changed player setting to unexpected state; no blind retry")
                        break
                log("STEP_NOT_CONFIRMED: "+key+" attempt="+str(retries[key])+
                    " features="+str({k:round(v,3) for k,v in features.items()}))
                awaiting_confirmation=False
            if retries[key]>=attempt_limits[key]:
                if not manual_prompted:
                    log("INPUT_UNCONFIRMED step="+key+" backend="+backend+
                        " attempts="+str(retries[key])+
                        " limit="+str(attempt_limits[key])+
                        " - no further automated input; observation only.")
                    manual_prompted=True
                continue
            if awaiting_confirmation is False and retries[key]>0 and not manual_prompted:
                log("RETRY_UNCONFIRMED step="+key+
                    " next_attempt="+str(retries[key]+1)+
                    " selected="+str(flags)+
                    " limit="+str(attempt_limits[key]))
            if time.monotonic()-last_click<1.0:
                continue
            if key=="one":
                player_selection_before=player_selected(features)
                log("PLAYER_BEFORE_CLICK selected="+str(player_selection_before))
            retries[key]+=1
            reduced=cv2.resize(frame,(960,round(frame.shape[0]*960/frame.shape[1])))
            cv2.imwrite(str(evidence_dir / ("before_"+key+".jpg")),reduced,
                        [cv2.IMWRITE_JPEG_QUALITY,70])
            # Alternate across INSIDE points of the same button, never a
            # neighbouring player slot. User's 00:43 log showed 4 still
            # selected after a sent touch on 1, so verify before each retry.
            if key=="one":
                one_targets=((.367,.703),(.381,.741),(.392,.767))
                target=one_targets[min(retries[key]-1,len(one_targets)-1)]
            elif key=="hard":
                hard_targets=((.713,.686),(.707,.705))
                target=hard_targets[min(retries[key]-1,len(hard_targets)-1)]
            elif key=="city":
                city_targets=((.400,.585),(.415,.585))
                target=city_targets[min(retries[key]-1,len(city_targets)-1)]
            else:
                target=step_points[key]
            method="SENDINPUT" if retries[key]==1 else "LEGACY_MOUSE_EVENT"
            if backend=="HID":
                method="USB_HID_LEONARDO"
            elif backend=="TOUCH":
                method="WIN32_TOUCH"
            elif backend=="SYNTHETIC":
                method="WIN32_SYNTHETIC_POINTER"
            log("INPUT_METHOD step="+key+" attempt="+str(retries[key])+
                " method="+method+" frame_target="+str(target))
            if backend=="SYNTHETIC":
                result=click_synthetic(*target,frame)
            elif backend=="TOUCH":
                result=click_touch(*target,frame)
            elif backend=="HID":
                result=usb_hid_mouse_click(*target,frame)
            else:
                result=(click(*target,frame) if retries[key]==1
                        else click_legacy(*target,frame))
            last_click=time.monotonic()
            awaiting_confirmation=(result=="INPUT_SENT_UNVERIFIED")
            if awaiting_confirmation:
                evidence_pending=key
            stable_count=0
            previous_result=None
            log("STEP_CLICK: "+key+" attempt="+str(retries[key])+
                " result="+result+" before="+str(flags))
            if not awaiting_confirmation:
                log("STOP: OS rejected click")
                break
        if not completed and time.monotonic()-start>=max_wait_seconds:
            log("LOBBY_WAIT_TIMEOUT: no independently confirmed match; "+
                "pad may still be occupied or unreachable.")
        log("END lobby; dialog_disappeared="+str(completed)+
            "; attempts="+str(retries)+
            "; match start not independently confirmed")
    except KeyboardInterrupt:
        log("STOP requested by user.")
    except Exception:
        log("ERROR "+traceback.format_exc())
    finally:
        stop.set()
        if controller is not None:
            try:
                controller.stop()
            except Exception as exc:
                log("Capture stop note: "+str(exc))
    return 0
# === End lobby assistant ===


# === ROBLOX V3.5 AUTOPILOT: single-window, bounded, visual-feedback controller ===
# This module is embedded in roblox_monitor.py BEFORE run_mode_prompt().
# It uses the existing verified_roblox_hwnd, pad_sign_hints,
# lifecycle_scene_hint and turret_price_color_signal functions.
# No additional Python file or CMD is needed on the user's computer.

class AutoPilotVisualReadyLock:
    """Fail-closed LK optical-flow follower for a previously verified READY sign.

    Text-template matching is used to CREATE this lock, not to keep it alive.
    Only points inside the original sign rectangle are followed. Camera motion
    may change the text scale, but flow must remain spatially coherent. A
    visual-only lock NEVER establishes pad availability or menu state.
    """
    MAX_FALLBACK_PULSES = 6

    def __init__(self):
        self.reset()

    def reset(self):
        self.prev_gray = None
        self.points = None
        self.xy = None
        self.hits = 0
        self.fallback_pulses = 0
        self.last_quality = 0.0

    @staticmethod
    def grayscale(frame):
        import cv2
        if frame is None or len(frame.shape) < 3:
            return None
        h,w = frame.shape[:2]
        if h < 300 or w < 500 or not .46 <= h / max(w,1) <= .68:
            return None
        view = cv2.resize(frame[:,:,:3], (960,540), interpolation=cv2.INTER_AREA)
        return cv2.cvtColor(view,cv2.COLOR_BGR2GRAY)

    def seed(self, frame, sign):
        import cv2,numpy as np
        if not sign or sign.get('status') != 'READY_SIGN' or \
           float(sign.get('confidence',0)) < .65:
            return False
        gray=self.grayscale(frame)
        if gray is None:return False
        try:
            x,y,w,h=[int(sign[k]) for k in ('x','y','w','h')]
        except (KeyError,ValueError,TypeError):return False
        x1=max(1,x-6);y1=max(22,y-4)
        x2=min(959,x+w+6);y2=min(265,y+h+4)
        if x2-x1<45 or y2-y1<12 or x2-x1>250:return False
        mask=np.zeros_like(gray,dtype=np.uint8)
        mask[y1:y2,x1:x2]=255
        points=cv2.goodFeaturesToTrack(gray,maxCorners=90,qualityLevel=.008,
                                       minDistance=3,mask=mask,blockSize=3)
        if points is None or len(points)<12:return False
        self.prev_gray=gray
        self.points=points.astype(np.float32)
        self.xy=(float(x+w/2),float(y+h/2))
        self.hits=0
        # Preserve the movement budget when the same READY target is reacquired.
        # reset() begins a new budget only after target selection/reselection.
        self.last_quality=0.0
        return True

    def match(self, frame):
        import cv2,numpy as np
        if self.prev_gray is None or self.points is None or self.xy is None:
            return None
        gray=self.grayscale(frame)
        if gray is None:return None
        start=self.points
        opts=dict(winSize=(31,31),maxLevel=3,
                  criteria=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,30,.008))
        new,status,_=cv2.calcOpticalFlowPyrLK(self.prev_gray,gray,start,None,**opts)
        if new is None or status is None:
            self.hits=0;return None
        back,valid_back,_=cv2.calcOpticalFlowPyrLK(gray,self.prev_gray,new,None,**opts)
        if back is None or valid_back is None:
            self.hits=0;return None
        p0=start.reshape(-1,2)
        p1=new.reshape(-1,2)
        pback=back.reshape(-1,2)
        fb=np.linalg.norm(pback-p0,axis=1)
        good=(status.reshape(-1)>0)&(valid_back.reshape(-1)>0)&(fb<=2.8)
        if int(good.sum())<12 or float(good.mean())<.52:
            self.hits=0;return None
        old=p0[good];cur=p1[good]
        delta=cur-old
        dx,dy=np.median(delta,axis=0)
        spread=np.linalg.norm(delta-np.array([dx,dy]),axis=1)
        keep=spread<=7
        if int(keep.sum())<12 or float(keep.mean())<.70:
            self.hits=0;return None
        dx,dy=np.median(delta[keep],axis=0)
        cx,cy=self.xy
        tx,ty=float(cx+dx),float(cy+dy)
        if not (25<tx<935 and 30<ty<245 and abs(dx)<95 and abs(dy)<75):
            self.hits=0;return None
        # Reject large texture jumps or inconsistent sign trajectories.
        if np.median(spread[keep])>4.5:
            self.hits=0;return None
        self.xy=(tx,ty)
        self.points=cur[keep].reshape(-1,1,2).astype(np.float32)
        self.prev_gray=gray
        self.hits+=1
        self.last_quality=round(float(keep.sum()/len(p0)),3)
        if self.hits<2 or self.fallback_pulses>=self.MAX_FALLBACK_PULSES:
            return None
        return {'status':'VISUAL_READY_FLOW',
                'center_x':round(tx/960,3),
                'confidence':self.last_quality,
                'availability':'UNVERIFIED'}

    def used_fallback_pulse(self):
        if self.fallback_pulses>=self.MAX_FALLBACK_PULSES:return False
        self.fallback_pulses+=1
        return True


class AutoPilotPadReselect:
    """Do not chase a pad after it becomes busy or the tracked sign jumps.

    This is a screen-relative, bounded reacquisition; NOT world navigation.
    No command to Roblox is emitted by this policy.
    """
    def __init__(self):
        self.reselections=0
        self.lost_reacquisitions=0
        self.busy_frames=0
        self.lost_frames=0
        self.lost_since=None
        self.excluded_x=None
        self.excluded_until=0.0

    def reset(self):
        self.__init__()

    def candidates(self, signs, now):
        # Exclude the previous abandoned label only while standing still.
        # Keep BUSY signs to prevent choosing an overlapping READY false hit.
        if self.excluded_x is None or now>=self.excluded_until:
            return signs
        return [s for s in signs if s.get('status')!='READY_SIGN'
                or abs(s.get('center_x',-9)-self.excluded_x)>.13]

    def check(self, signs, target_x, now):
        if target_x is None:
            return ('RESELECT', None, 'NO_LOCKED_TARGET')
        countdown=[s for s in signs if
                   ((s.get('status')=='COUNTDOWN_SIGN' and
                     s.get('confidence',0)>=.72) or
                    (s.get('status')=='CREATING_SIGN' and
                     s.get('confidence',0)>=.83)) and
                   abs(s.get('center_x',-9)-target_x)<.105]
        if countdown:
            self.busy_frames+=1
            self.lost_frames=0
            self.lost_since=None
            if self.busy_frames>=2:
                return ('RESELECT',None,'TRACKED_PAD_BUSY_OR_COUNTDOWN')
            return ('WAIT',None,'BUSY_SIGN_NEEDS_CONFIRMATION')
        self.busy_frames=0
        ready=[s for s in signs if s.get('status')=='READY_SIGN'
               and s.get('confidence',0)>=.65
               and not any(((b.get('status')=='COUNTDOWN_SIGN' and
                              b.get('confidence',0)>=.64) or
                             (b.get('status')=='CREATING_SIGN' and
                              b.get('confidence',0)>=.83)) and
                           abs(s.get('center_x',-9)-b.get('center_x',-8))<.115
                           for b in signs)]
        near=[s for s in ready if
              abs(s.get('center_x',-9)-target_x)<=.19]
        if near:
            self.lost_frames=0
            self.lost_since=None
            x=min(near,key=lambda s:abs(s.get('center_x',0)-target_x))['center_x']
            return ('TRACK',x,'SAME_SIGN_NEARBY')
        # A completely different READY sign is NOT a continuation of the
        # locked pad. Pause and get a new stable target while not moving.
        # A single WGC frame may omit the label after WASD, from player
        # occlusion, camera motion, or resizing. This does NOT prove a pad
        # was occupied. Stay motionless for at least 5 seconds and require
        # >=7 sampled misses before considering another pad.
        if self.lost_since is None:
            self.lost_since=now
        self.lost_frames+=1
        if self.lost_frames>=7 and now-self.lost_since>=5.0:
            return ('RESELECT',None,'READY_UNSEEN_FOR_5S')
        return ('WAIT',None,'READY_TEMPORARILY_HIDDEN')

    def begin_reselection(self, old_x, now, reason):
        """Differentiate unobserved labels from *confirmed* occupied pads.

        Lost READY can be caused by player occlusion/camera perspective:
        it must NOT consume the limited BUSY-pad retry count. Do not move
        during reacquisition, and cap each cause independently.
        """
        occupied=(reason=='TRACKED_PAD_BUSY_OR_COUNTDOWN')
        if occupied:
            if self.reselections>=2:
                return False
            self.reselections+=1
            self.excluded_x=old_x
            self.excluded_until=now+9.0
        else:
            if self.lost_reacquisitions>=3:
                return False
            self.lost_reacquisitions+=1
            # Don't ban an unverified sign; it might still be the only
            # available pad or simply hidden from the current camera angle.
            self.excluded_x=None
            self.excluded_until=0.0
        self.busy_frames=0
        self.lost_frames=0
        self.lost_since=None
        return True


class AutoPilotPolicy:
    """Pure state/decision policy; unit-testable without Windows or Roblox."""
    def __init__(self):
        self.target_x = None
        self.last_x = None
        self.no_progress = 0
        self.move_actions = 0
        self.move_seconds = 0.0
        self.menu_index = 0
        self.menu_tries = {}
        self.menu_confirmations = 0
        self.last_menu_action = 0.0
        self.create_sent = False
        self.in_match_hits = 0
        self.ready_history = []
        self.sign_misses = 0
        self.match_index = 0
        self.turret_actions = 0
        self.last_turret_at = 0.0
        self.stage = 'DISCOVER'
        self.stage_since = 0.0

    def reset_lobby(self, now):
        self.target_x = None
        self.last_x = None
        self.no_progress = 0
        self.move_actions = 0
        self.move_seconds = 0.0
        self.ready_history = []
        self.sign_misses = 0
        self.stage = 'DISCOVER'
        self.stage_since = now
        self.menu_index = 0
        self.menu_tries = {}
        self.menu_confirmations = 0
        self.last_menu_action = 0.0
        self.create_sent = False
        self.in_match_hits = 0
        self.turret_actions = 0
        self.last_turret_at = 0.0

    def ready_sign(self, signs):
        """Lock onto a visible READY sign 3 of 6 frames (allow brief flicker).

        Each movement still needs a *fresh* target detection. A countdown
        sign within 0.115 screen-width blocks candidate movement.
        """
        strong=[s for s in signs if s.get('status')=='READY_SIGN'
                and s.get('confidence',0)>=.65]
        busy=[s for s in signs if
              (s.get('status')=='COUNTDOWN_SIGN' and
               s.get('confidence',0)>=.64) or
              (s.get('status')=='CREATING_SIGN' and
               s.get('confidence',0)>=.83)]
        current=[]
        for s in strong:
            x=s.get('center_x',-1)
            if not .04<x<.96:continue
            if any(abs(x-b.get('center_x',-2))<.115 for b in busy):
                continue
            current.append((x,s.get('relative_side','UNKNOWN')))
        self.ready_history.append(current)
        self.ready_history=self.ready_history[-6:]
        if len(self.ready_history)<3 or not current:return None
        candidates=[]
        for x,side in current:
            matches=[]
            for old in self.ready_history:
                near=[o for o in old if o[1]==side and abs(o[0]-x)<=.13]
                if near:matches.append(min(near,key=lambda a:abs(a[0]-x))[0])
            if len(matches)>=3 and max(matches)-min(matches)<=.18:
                # The historical average is ONLY for stability checking.
                # Use the current sign position for actual movement. The
                # 06:48:45 live log had current x=.634 but locked x=.504,
                # causing a misleading forward command.
                candidates.append((x,side))
        if not candidates:return None
        candidates.sort(key=lambda row:(abs(row[0]-.5),row[0]))
        self.sign_misses=0
        return candidates[0][0]

    def lobby_movement(self, x, now):
        """Choose at most one short key pulse; stop on ambiguous progress."""
        if self.move_actions>=34 or self.move_seconds>=12 or now-self.stage_since>45:
            return ('HALT','LOBBY_LIMIT_REACHED',0.0)
        if self.last_x is not None and self.stage == 'ALIGN':
            if abs(x-.50)>abs(self.last_x-.50)+.025:
                self.no_progress+=1
            elif abs(x-.50)<abs(self.last_x-.50)-.012:
                self.no_progress=0
            elif abs(x-self.last_x)<.007:
                self.no_progress+=1
            if self.no_progress>=4:
                return ('HALT','ALIGNMENT_NOT_IMPROVING',0.0)
        self.last_x=x
        if abs(x-.5)>.11:
            self.stage='ALIGN'
            duration=.18 if abs(x-.5)<.20 else .26
            key='D' if x>.5 else 'A'
        else:
            self.stage='APPROACH'
            duration=.22
            key='W'
        self.move_actions+=1
        self.move_seconds+=duration
        return ('KEY',key,duration)

    @staticmethod
    def menu_flags(features):
        """Same selection semantics as the previously tested lobby helper."""
        vals=[features.get('p1',0),features.get('p2',0),
              features.get('p3',0),features.get('p4',0)]
        active=[i for i,v in enumerate(vals) if v>.15]
        # Check the ACTUAL short bottom edge of the map tile, not the
        # whole map panel. Old ROIs sampled the neighboring cave card and
        # were contaminated by other yellow rectangles. Video frames 009
        # and 011 both have City selected and hard changes between frames.
        city=features.get('city_bottom_gold',features.get('city',0))>.18
        cave=features.get('cave_bottom_gold',features.get('cave',0))>.12
        # The active Hard button is red-filled in real OBS frames; checking
        # only a 3-pixel top border falsely rejected that button.
        hard=features.get('hard_center_red',
             features.get('hard_top_red',features.get('hard_red',0)))>.045
        normal=features.get('normal_top_green',features.get('normal',0))>.12
        return {'city':city and not cave,
                'one':active==[0],
                'hard':hard and not normal}

    def menu_next(self, features, now):
        """Return (click, x, y, reason), or no-click/wait/halt decision."""
        flags=self.menu_flags(features)
        steps=('city','one','hard')
        # Aim at the middle of the actual buttons, away from their edges.
        targets={'city':(.400,.585),'one':(.382,.727),
                 'hard':(.710,.678),'create':(.420,.850)}
        if self.create_sent:
            return ('WAIT',None,None,'CREATE_ALREADY_SENT')
        if now-self.last_menu_action<1.1:
            return ('WAIT',None,None,'UI_SETTLE')
        for i in range(self.menu_index):
            if not flags[steps[i]]:
                return ('HALT',None,None,'VERIFIED_SETTING_CHANGED_'+steps[i])
        if self.menu_index<3:
            step=steps[self.menu_index]
            if flags[step]:
                self.menu_confirmations+=1
                if self.menu_confirmations>=3:
                    self.menu_index+=1
                    self.menu_confirmations=0
                return ('WAIT',None,None,'CONFIRM_'+step)
            self.menu_confirmations=0
            if self.menu_tries.get(step,0)>=1:
                return ('HALT',None,None,'UNVERIFIED_CLICK_'+step)
            self.menu_tries[step]=self.menu_tries.get(step,0)+1
            self.last_menu_action=now
            x,y=targets[step]
            return ('CLICK',x,y,'SET_'+step)
        if not all(flags.values()):
            return ('HALT',None,None,'MENU_FLAGS_INCONSISTENT')
        self.menu_confirmations+=1
        if self.menu_confirmations<3:
            return ('WAIT',None,None,'VERIFY_ALL_BEFORE_CREATE')
        self.create_sent=True
        self.last_menu_action=now
        x,y=targets['create']
        return ('CLICK',x,y,'CREATE_ONCE')


class AutoPilotRoute:
    """Use ONLY recorded user input spans, with live scene and ORB checkpoints.

    The archive can be missing or have unusable mouse data; then the route is
    unavailable and movement stops rather than guessing a path near the ramp.
    """
    def __init__(self):
        self.steps=[]
        self.references=[]
        self.idx=0
        self.ready=False
        self.note='ROUTE_DEMO_NOT_FOUND'
        self.orb=None
        self.matcher=None

    def load(self):
        import zipfile, csv, io, re, cv2, numpy as np
        source=Path.home()/'Documents'/'RobloxBGDiagnostics'/'ROUTE'/'ROUTE_DEMO.zip'
        if not source.is_file():return False
        try:
            with zipfile.ZipFile(source) as z:
                if z.testzip():raise ValueError('ZIP CRC')
                if 'keys.csv' not in z.namelist():
                    self.note='KEY_TIMING_MISSING';return False
                rows=list(csv.DictReader(io.StringIO(z.read('keys.csv').decode('utf-8-sig'))))
                spans=[]
                for row in rows:
                    key=row.get('key','').upper()
                    if key not in ('W','A','S','D','SPACE','SHIFT'):continue
                    a,b=float(row['start_seconds']),float(row['end_seconds'])
                    if a<0 or b<=a or b>40 or b-a>10:raise ValueError('INVALID_KEY_TIMING')
                    spans.append((a,b,key))
                if not spans: self.note='EMPTY_ROUTE_KEYS';return False
                total=max(x[1] for x in spans)
                # Camera-motion replay is not calibrated. Do not replay risky
                # route if it relied on substantial mouse movement.
                if 'mouse.csv' in z.namelist():
                    moves=list(csv.DictReader(io.StringIO(z.read('mouse.csv').decode('utf-8-sig'))))
                    total_mouse=0
                    for m in moves:
                        total_mouse+=abs(float(m.get('mouse_dx',0)))+abs(float(m.get('mouse_dy',0)))
                    if total_mouse>80:
                        self.note='CAMERA_ROTATION_NOT_CALIBRATED'
                        return False
                # Discretize recorded key spans into 150ms time slices.
                # Do not merge different keys: diagonal timing matters.
                dt=.15
                self.steps=[]
                t=0.0
                while t<total:
                    active=tuple(sorted(k for a,b,k in spans if a<t+dt/2<b))
                    if active:self.steps.append((round(t,2),active,min(dt,total-t)))
                    t+=dt
                names=sorted(n for n in z.namelist() if
                             re.fullmatch(r'route_\d\d_\d+\.\ds\.jpg',n))
                if len(names)<9:
                    self.note='TOO_FEW_ROUTE_IMAGES';return False
                self.orb=cv2.ORB_create(nfeatures=800,fastThreshold=10)
                self.matcher=cv2.BFMatcher(cv2.NORM_HAMMING)
                for name in names:
                    index=int(name.split('_')[1])
                    if index not in (0,1,2,3,9,10):continue
                    img=cv2.imdecode(np.frombuffer(z.read(name),dtype=np.uint8),cv2.IMREAD_COLOR)
                    if img is None:continue
                    desc=self.describe(img)
                    if desc is not None and len(desc)>=30:self.references.append((index,desc))
                if len(self.references)<4:
                    self.note='INSUFFICIENT_VISUAL_ROUTE_ANCHORS';return False
                self.ready=True
                self.note='READY_VISUAL_ROUTE_REPLAY'
                return True
        except Exception as exc:
            self.note='ROUTE_INVALID_'+type(exc).__name__
            return False

    def describe(self,img):
        import cv2
        h,w=img.shape[:2]
        if h<250 or w<400:return None
        if w!=1100:
            img=cv2.resize(img,(1100,round(h*1100/w)),interpolation=cv2.INTER_AREA)
            h,w=img.shape[:2]
        roi=img[int(.08*h):int(.73*h),int(.08*w):int(.91*w),:3]
        _,d=self.orb.detectAndCompute(cv2.cvtColor(roi,cv2.COLOR_BGR2GRAY),None)
        return d

    def classify(self,img):
        if not self.references:return 'UNKNOWN',0
        descriptor=self.describe(img)
        if descriptor is None or len(descriptor)<20:return 'UNKNOWN',0
        counts={}
        for idx,ref in self.references:
            try:
                knn=self.matcher.knnMatch(descriptor,ref,k=2)
                n=sum(1 for pair in knn if len(pair)==2 and pair[0].distance<.70*pair[1].distance)
            except Exception:n=0
            counts[idx]=max(n,counts.get(idx,0))
        first=max((counts.get(i,0) for i in (0,1)),default=0)
        corner=max((counts.get(i,0) for i in (9,10)),default=0)
        if corner>=35 and corner>first*1.8:return 'SAFE_CORNER',corner
        if first>=35 and first>corner*1.8:return 'START',first
        return 'UNKNOWN',max(counts.values(),default=0)



class AutoPilotReturnGate:
    """Pure phase recovery policy for a game that automatically returns to lobby.

    Never issues input. A confirmed game HUD is required before recognizing a
    defeat/return, and multiple independent samples are required for recovery.
    If the HUD disappears and no legitimate lobby appears, wait safely then
    terminate rather than continuing to press Z or replay WASD in the lobby.
    """
    def __init__(self):
        self.danger_hits=0
        self.loading_hits=0
        self.lobby_hits=0
        self.last_match_at=None
        self.wait_since=None

    def reset(self):
        self.danger_hits=0
        self.loading_hits=0
        self.lobby_hits=0
        self.last_match_at=None
        self.wait_since=None

    def observe(self,stage,scene,now,confirmed_matches):
        if confirmed_matches<1 or stage not in (
                'MATCH_ROUTE','MATCH_DEFEND','WAIT_FOR_RETURN'):
            return None
        self.danger_hits=self.danger_hits+1 if scene=='DANGER_OR_DEFEAT' else 0
        self.loading_hits=self.loading_hits+1 if scene=='LOADING' else 0
        self.lobby_hits=self.lobby_hits+1 if scene=='LOBBY' else 0
        if scene=='MATCH':
            self.last_match_at=now
        if self.lobby_hits>=4:
            return 'RETURNED_LOBBY'
        if stage=='WAIT_FOR_RETURN':
            if self.wait_since is None:self.wait_since=now
            if now-self.wait_since>100:
                return 'RETURN_TIMEOUT'
            return None
        if self.danger_hits>=3 or self.loading_hits>=3:
            self.wait_since=now
            return 'WAIT_FOR_RETURN'
        if self.last_match_at is not None and now-self.last_match_at>18:
            self.wait_since=now
            return 'WAIT_FOR_RETURN'
        return None

class AutoPilotMotionGuard:
    """Verify screenshot motion after short user-authorized WASD pulses.

    Camera-relative ORB motion is NOT proof of reaching a destination.
    Its purpose is only to stop repeated blind input when world geometry
    stays frozen or visual evidence cannot be evaluated. No game commands.
    """
    def __init__(self):
        import cv2
        self.cv2=cv2
        self.orb=cv2.ORB_create(nfeatures=650,fastThreshold=12)
        self.matcher=cv2.BFMatcher(cv2.NORM_HAMMING)
        self.before=None
        self.no_motion=0
        self.uncertain=0
        self.last_result=None

    def describe(self,frame):
        import cv2
        if frame is None or len(frame.shape)<3:return None
        H,W=frame.shape[:2]
        if W<500 or H<300:return None
        view=cv2.resize(frame[:,:,:3],(960,540),interpolation=cv2.INTER_AREA)
        region=cv2.cvtColor(view[70:350,70:890],cv2.COLOR_BGR2GRAY)
        keypoints,desc=self.orb.detectAndCompute(region,None)
        return keypoints,desc

    def arm(self,frame):
        self.before=self.describe(frame)

    def verify(self,frame):
        import numpy as np
        if self.before is None:return 'NO_PENDING',0.,0
        before=self.before
        self.before=None
        after=self.describe(frame)
        if before is None or after is None or before[1] is None or after[1] is None:
            self.uncertain+=1
            self.last_result=('UNKNOWN',0.,0)
            return self.last_result
        ka,da=before
        kb,db=after
        if len(da)<20 or len(db)<20:
            self.uncertain+=1
            self.last_result=('UNKNOWN',0.,0)
            return self.last_result
        try:
            matched=self.matcher.knnMatch(da,db,k=2)
            pairs=[(p[0].queryIdx,p[0].trainIdx) for p in matched
                   if len(p)==2 and p[0].distance<.70*p[1].distance]
            if len(pairs)<16:
                self.uncertain+=1
                self.last_result=('UNKNOWN',0.,len(pairs))
                return self.last_result
            displacement=float(np.median([
                np.hypot(ka[i].pt[0]-kb[j].pt[0],ka[i].pt[1]-kb[j].pt[1])
                for i,j in pairs]))
            if displacement<1.7:
                self.no_motion+=1
                self.last_result=('NO_MOTION',round(displacement,2),len(pairs))
            else:
                self.no_motion=0
                self.uncertain=0
                self.last_result=('MOTION',round(displacement,2),len(pairs))
            return self.last_result
        except cv2.error:
            self.uncertain+=1
            self.last_result=('UNKNOWN',0.,0)
            return self.last_result

    def stop_reason(self):
        if self.no_motion>=3:return 'NO_BACKGROUND_MOTION_AFTER_3_KEYS'
        if self.uncertain>=4:return 'CANNOT_VERIFY_MOTION_4_TIMES'
        return None

    def reset(self):
        self.before=None
        self.no_motion=0
        self.uncertain=0
        self.last_result=None


def autopilot_disable_console_selection():
    """Disable Windows QuickEdit only during real autopilot sessions.

    Classic conhost prepends 'Select'/'Выбрать' to its title when the
    console is in mark mode. This can pause a running Python process.
    Keep Ctrl+C and normal console output enabled.
    """
    try:
        import ctypes
        from ctypes import wintypes
        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.GetStdHandle.argtypes=(wintypes.DWORD,)
        kernel.GetStdHandle.restype=wintypes.HANDLE
        kernel.GetConsoleMode.argtypes=(wintypes.HANDLE,
                                        ctypes.POINTER(wintypes.DWORD))
        kernel.GetConsoleMode.restype=wintypes.BOOL
        kernel.SetConsoleMode.argtypes=(wintypes.HANDLE,wintypes.DWORD)
        kernel.SetConsoleMode.restype=wintypes.BOOL
        h=kernel.GetStdHandle(0xFFFFFFF6) # STD_INPUT_HANDLE = -10
        mode=wintypes.DWORD()
        if not h or not kernel.GetConsoleMode(h,ctypes.byref(mode)):
            return False
        # ENABLE_EXTENDED_FLAGS required to modify ENABLE_QUICK_EDIT_MODE.
        desired=(mode.value|0x0080)&~0x0040
        return bool(kernel.SetConsoleMode(h,desired))
    except (OSError,AttributeError,ValueError):
        return False


def autopilot_minimize_console():
    """Auto-minimize CMD after YES; preserve logging in AUTOPILOT_LOG.txt."""
    try:
        import ctypes
        from ctypes import wintypes
        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        u=ctypes.WinDLL('user32',use_last_error=True)
        kernel.GetConsoleWindow.restype=wintypes.HWND
        u.IsWindowVisible.argtypes=(wintypes.HWND,)
        u.IsWindowVisible.restype=wintypes.BOOL
        u.IsIconic.argtypes=(wintypes.HWND,)
        u.IsIconic.restype=wintypes.BOOL
        u.ShowWindow.argtypes=(wintypes.HWND,ctypes.c_int)
        u.ShowWindow.restype=wintypes.BOOL
        hwnd=kernel.GetConsoleWindow()
        if not hwnd or not u.IsWindowVisible(hwnd) or u.IsIconic(hwnd):
            return 0
        u.ShowWindow(hwnd,6)  # SW_MINIMIZE
        return int(hwnd)
    except (OSError,AttributeError,ValueError):
        return 0


def autopilot_restore_console(hwnd):
    """Show the same CMD window again when the autopilot finishes."""
    if not hwnd:return
    try:
        import ctypes
        from ctypes import wintypes
        u=ctypes.WinDLL('user32',use_last_error=True)
        u.ShowWindow.argtypes=(wintypes.HWND,ctypes.c_int)
        u.ShowWindow.restype=wintypes.BOOL
        u.ShowWindow(hwnd,9)  # SW_RESTORE
    except (OSError,AttributeError,ValueError):
        pass


class AutoPilotInput:
    """Foreground-only press/click; never send input to a browser."""
    VK_F10=0x79
    SCANS={'W':0x11,'A':0x1e,'S':0x1f,'D':0x20,
           'Z':0x2c,'SPACE':0x39,'SHIFT':0x2a}
    def __init__(self,hwnd):
        import ctypes
        from ctypes import wintypes
        self.ctypes=ctypes
        self.u=ctypes.WinDLL('user32',use_last_error=True)
        self.hwnd=hwnd
        self.u.GetForegroundWindow.restype=wintypes.HWND
        self.u.SetForegroundWindow.argtypes=(wintypes.HWND,)
        self.u.SetForegroundWindow.restype=wintypes.BOOL
        self.u.IsIconic.argtypes=(wintypes.HWND,)
        self.u.IsIconic.restype=wintypes.BOOL
        self.u.GetAsyncKeyState.argtypes=(ctypes.c_int,)
        self.u.GetAsyncKeyState.restype=ctypes.c_short
        self.u.SetProcessDPIAware()
        class MOUSEINPUT(ctypes.Structure):
            _fields_=[('dx',ctypes.c_long),('dy',ctypes.c_long),
                      ('mouseData',ctypes.c_ulong),('dwFlags',ctypes.c_ulong),
                      ('time',ctypes.c_ulong),('dwExtraInfo',ctypes.c_void_p)]
        class KEYBDINPUT(ctypes.Structure):
            _fields_=[('wVk',ctypes.c_ushort),('wScan',ctypes.c_ushort),
                      ('dwFlags',ctypes.c_ulong),('time',ctypes.c_ulong),
                      ('dwExtraInfo',ctypes.c_void_p)]
        class UNION(ctypes.Union):
            _fields_=[('mi',MOUSEINPUT),('ki',KEYBDINPUT)]
        class INPUT(ctypes.Structure):
            _anonymous_=('data',)
            _fields_=[('type',ctypes.c_ulong),('data',UNION)]
        self.MOUSEINPUT,self.KEYBDINPUT,self.INPUT=MOUSEINPUT,KEYBDINPUT,INPUT
        self.u.SendInput.argtypes=(ctypes.c_uint,ctypes.POINTER(INPUT),ctypes.c_int)
        self.u.SendInput.restype=ctypes.c_uint
        self.u.GetClientRect.argtypes=(wintypes.HWND,ctypes.c_void_p)
        self.u.ClientToScreen.argtypes=(wintypes.HWND,ctypes.c_void_p)
        self.u.SetCursorPos.argtypes=(ctypes.c_int,ctypes.c_int)

    def focused(self):
        return bool(self.u.GetForegroundWindow()==self.hwnd and
                    not self.u.IsIconic(self.hwnd))
    def focus_game_once(self):
        """Only after explicit YES: bring the verified game HWND to foreground.

        Do NOT steal focus back later: clicking another app must always pause
        control. Win32 may deny activation, in which case the user can click
        Roblox manually, and no keys/clicks are sent until it is foreground.
        """
        if self.focused():
            return True
        if self.u.IsIconic(self.hwnd):
            return False
        self.u.SetForegroundWindow(self.hwnd)
        until=time.monotonic()+1.5
        while time.monotonic()<until:
            if self.focused():
                return True
            time.sleep(.10)
        return self.focused()
    def stop_pressed(self):
        return bool(self.u.GetAsyncKeyState(self.VK_F10)&0x8000)
    def _send_key(self,key,up=False):
        if not self.focused():return False
        ev=self.INPUT();ev.type=1
        ev.ki=self.KEYBDINPUT(0,self.SCANS[key],0x0008 | (0x0002 if up else 0),0,None)
        return self.u.SendInput(1,self.ctypes.byref(ev),self.ctypes.sizeof(self.INPUT))==1
    def keys(self,keys,duration):
        if isinstance(keys,str):keys=(keys,)
        keys=tuple(k for k in keys if k in self.SCANS)
        if not keys or not 0.04<=duration<=.33 or not self.focused():return False
        down=[]
        try:
            for k in keys:
                if not self._send_key(k):return False
                down.append(k)
            time.sleep(duration)
            return self.focused()
        finally:
            for k in reversed(down):
                # Release even if focus changed, preventing stuck keys.
                ev=self.INPUT();ev.type=1
                ev.ki=self.KEYBDINPUT(0,self.SCANS[k],0x0008|0x0002,0,None)
                self.u.SendInput(1,self.ctypes.byref(ev),self.ctypes.sizeof(self.INPUT))

    def click(self,relx,rely,frame):
        import ctypes
        from ctypes import wintypes
        class POINT(ctypes.Structure):
            _fields_=[('x',ctypes.c_long),('y',ctypes.c_long)]
        class RECT(ctypes.Structure):
            _fields_=[('left',ctypes.c_long),('top',ctypes.c_long),
                      ('right',ctypes.c_long),('bottom',ctypes.c_long)]
        if not self.focused():return False
        rect=RECT()
        if not self.u.GetClientRect(self.hwnd,ctypes.byref(rect)):return False
        w,h=rect.right-rect.left,rect.bottom-rect.top
        fh,fw=frame.shape[:2]
        extra_y,extra_x=fh-h,fw-w
        if not (w>300 and h>300 and 0<=extra_x<=50 and 0<=extra_y<=90):return False
        x=int(relx*fw-extra_x/2);y=int(rely*fh-extra_y)
        if not (0<=x<w and 0<=y<h):return False
        p=POINT(x,y)
        if not self.u.ClientToScreen(self.hwnd,ctypes.byref(p)):return False
        if not self.u.SetCursorPos(p.x,p.y):return False
        time.sleep(.12)
        if not self.focused():return False
        def mouse(flag):
            ev=self.INPUT();ev.type=0
            ev.mi=self.MOUSEINPUT(0,0,0,flag,0,None)
            return self.u.SendInput(1,ctypes.byref(ev),ctypes.sizeof(self.INPUT))==1
        down=mouse(0x0002)
        time.sleep(.12)
        up=mouse(0x0004)
        return down and up




def autopilot_spawn_grate_hint(frame):
    """Conservative landmark for the recorded distant lobby spawn, not a pad.
    This only authorizes a few observation-verified W pulses. It never
    declares a FREE pad or overrides occupied signs.
    """
    import cv2,numpy as np
    if frame is None or len(frame.shape)<3:return False
    H,W=frame.shape[:2]
    if W<500 or H<300 or not .46<=H/max(W,1)<=.68:return False
    view=cv2.resize(frame[:,:,:3],(960,540),interpolation=cv2.INTER_AREA)
    gray=cv2.cvtColor(view,cv2.COLOR_BGR2GRAY)
    # The near spawn ramp has a distinctive black floor grate.
    # All crops contain only game scenery, no player names or chat text.
    grate=gray[400:475,290:620]
    dark=float(np.mean(grate<80))
    bright=float(np.mean(grate>170))
    edges=float(np.mean(cv2.Canny(grate,80,160)>0))
    return (.30<dark<.64 and bright<.12 and .09<edges<.30)

class AutoPilotBackgroundInput(AutoPilotInput):
    """Experimental HWND-addressed WM input, never OS-global SendInput.

    Roblox may ignore posted messages because it can read raw device state.
    Never claim a posted message proves gameplay input; the existing WGC
    visual/motion guards must verify the result or stop.
    """
    VK={'W':0x57,'A':0x41,'S':0x53,'D':0x44,
        'Z':0x5A,'SPACE':0x20,'SHIFT':0x10}

    def __init__(self,hwnd):
        super().__init__(hwnd)
        from ctypes import wintypes
        self.u.IsWindow.argtypes=(wintypes.HWND,)
        self.u.IsWindow.restype=wintypes.BOOL
        self.u.IsWindowVisible.argtypes=(wintypes.HWND,)
        self.u.IsWindowVisible.restype=wintypes.BOOL
        self.u.PostMessageW.argtypes=(wintypes.HWND,self.ctypes.c_uint,
                                      wintypes.WPARAM,wintypes.LPARAM)
        self.u.PostMessageW.restype=wintypes.BOOL

    def focused(self):
        # Meaning in this subclass: the verified game target is still usable.
        # Do NOT require GetForegroundWindow()==hwnd.
        return bool(self.u.IsWindow(self.hwnd) and
                    self.u.IsWindowVisible(self.hwnd) and
                    not self.u.IsIconic(self.hwnd))

    def focus_game_once(self):
        # Explicitly NEVER call SetForegroundWindow for background mode.
        return self.focused()

    def _post(self,msg,vk,lp):
        return bool(self.focused() and
                    self.u.PostMessageW(self.hwnd,msg,vk,lp))

    def keys(self,keys,duration):
        if isinstance(keys,str):keys=(keys,)
        keys=tuple(k for k in keys if k in self.VK)
        if not keys or not .04<=duration<=.33 or not self.focused():
            return False
        down=[]
        try:
            for key in keys:
                scan=self.SCANS[key]
                if not self._post(0x0100,self.VK[key],1|(scan<<16)):
                    return False
                down.append(key)
            time.sleep(duration)
            return self.focused()
        finally:
            for key in reversed(down):
                scan=self.SCANS[key]
                self._post(0x0101,self.VK[key],1|(scan<<16)|0xC0000000)

    def click(self,relx,rely,frame):
        from ctypes import wintypes
        class RECT(self.ctypes.Structure):
            _fields_=[('left',self.ctypes.c_long),
                      ('top',self.ctypes.c_long),
                      ('right',self.ctypes.c_long),
                      ('bottom',self.ctypes.c_long)]
        if not self.focused():return False
        rect=RECT()
        if not self.u.GetClientRect(self.hwnd,self.ctypes.byref(rect)):
            return False
        w,h=rect.right-rect.left,rect.bottom-rect.top
        fh,fw=frame.shape[:2]
        extra_y,extra_x=fh-h,fw-w
        if not (w>300 and h>300 and 0<=extra_x<=50 and 0<=extra_y<=90):
            return False
        x=int(relx*fw-extra_x/2)
        y=int(rely*fh-extra_y)
        if not (0<=x<w and 0<=y<h):return False
        xy=((y&0xffff)<<16)|(x&0xffff)
        if not self._post(0x0200,0,xy):return False
        if not self._post(0x0201,1,xy):return False
        time.sleep(.08)
        return self._post(0x0202,0,xy)


def autopilot_menu_features(frame):
    """Locate the creation menu at varying vertical UI positions.

    The old menu was calibrated on a 960x540 OBS frame, but live Roblox WGC
    is 1920x1030 and game UI is shifted. Scan a bounded vertical range and
    require *independent* City/card, player, Create/Cancel and difficulty
    signals; do not infer an open menu just from four white digits.

    Returns positions in the historical 960x540 coordinate system plus
    `ui_shift`, the signed pixel correction (960x540 coordinates) for clicks.
    """
    import cv2
    import numpy as np
    if frame is None or len(frame.shape)<3:
        return False, {}
    h,w=frame.shape[:2]
    if h<300 or w<500 or not .46<=h/w<=.68:
        return False, {}
    view=cv2.resize(frame[:,:,:3],(960,540),interpolation=cv2.INTER_AREA)
    best=None
    for shift in (0,-4,4,-8,8,-12,12,-16,16,-20,20,-24,24,-28,28,-32,32):
        if shift:
            src=cv2.warpAffine(view,
                 np.float32([[1,0,0],[0,1,-shift]]),(960,540),
                 flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
        else:
            src=view
        hsv=cv2.cvtColor(src,cv2.COLOR_BGR2HSV)
        hue,sat,val=cv2.split(hsv)
        green=(hue>=35)&(hue<=90)&(sat>95)&(val>80)
        gold=(hue>=18)&(hue<=42)&(sat>100)&(val>90)
        red=((hue<12)|(hue>170))&(sat>75)&(val>60)
        def avg(mask,x1,y1,x2,y2):
            roi=mask[y1:y2,x1:x2]
            return float(roi.mean()) if roi.size else 0.0
        def borders(mask,x1,y1,x2,y2):
            p=5
            return max(avg(mask,x1,y1,x2,y1+p),
                       avg(mask,x1,y2-p,x2,y2),
                       avg(mask,x1,y1,x1+p,y2),
                       avg(mask,x2-p,y1,x2,y2))
        # Player tiles, independent of Create button below the tiles.
        # These narrow strips correspond to the green selected outline.
        players=[]
        for x1,x2 in ((333,400),(409,477),(483,551),(559,630)):
            players.append(max(avg(green,x1,352,x2,361),
                               avg(green,x1,357,x1+5,414),
                               avg(green,x2-5,357,x2,414)))
        digit_boxes=((354,386,380,424),(431,386,457,424),
                     (508,386,534,424),(585,386,611,424))
        digits=0
        for x1,y1,x2,y2 in digit_boxes:
            pix=src[y1:y2,x1:x2].astype(np.int16)
            white=(pix.min(2)>165)&((pix.max(2)-pix.min(2))<80)
            digits+=int(float(white.mean())>.025)
        city=avg(gold,340,334,450,343)
        cave=avg(gold,510,330,623,338)
        normal=avg(green,645,333,724,348)
        hard=avg(red,645,358,724,375)
        create=borders(green,344,450,462,494)
        cancel=borders(red,498,450,617,494)
        cancel_bottom=avg(red,505,468,615,474)
        cancel_strength=max(cancel,cancel_bottom/.7)
        good=(digits==4 and create>.14 and cancel_strength>.10
              and max(players)>.15 and max(city,cave)>.08
              and max(normal,hard)>.03)
        score=(min(create/.15,2)+min(cancel_strength/.10,2)
               +min(max(players)/.4,2)+min(max(city,cave)/.15,2)
               +min(max(normal/.25,hard/.10),2)-abs(shift)*.01)
        features={
            'city_bottom_gold':city, 'cave_bottom_gold':cave,
            'city':city,'cave':cave,'p1':players[0],
            'p2':players[1],'p3':players[2],'p4':players[3],
            'normal_top_green':normal,'hard_center_red':hard,
            'hard_top_red':hard,'normal':normal,'hard_red':hard,
            'create':create,'cancel':cancel,
            'cancel_bottom_red':cancel_bottom,'digits':digits,
            'ui_shift':shift,'menu_confidence':round(score,3),
        }
        # Always prefer a verified menu over an unverified candidate.
        key=(int(good),score)
        if best is None or key>best[0]:
            best=(key,good,features)
    return best[1],best[2]


def autopilot_mode():
    """Single capture controller: pad->menu->match->route->turret->return.

    Experimental executable controller, NOT claimed in-game verified.
    F10 stops. Caps all movements; errors halt instead of improvising.
    """
    import queue, ctypes, csv, traceback
    import cv2
    from windows_capture import WindowsCapture,Frame,InternalCaptureControl
    root=Path.home()/'Documents'/'RobloxBGDiagnostics'/'AUTOPILOT'
    root.mkdir(parents=True,exist_ok=True)
    logfile=root/'AUTOPILOT_LOG.txt'
    events=[]
    def log(s):
        line=time.strftime('[%H:%M:%S] ')+str(s)
        print(line,flush=True)
        events.append(line)
        with logfile.open('a',encoding='utf-8') as fp:fp.write(line+'\n')
    logfile.write_text('ROBLOX AUTOPILOT V'+VERSION+'\n',encoding='utf-8')
    print('AUTOPILOT: lobby -> City / 1 / Hard -> match -> route -> turrets -> repeat.')
    background_mode=os.environ.get('ROBLOX_BG_INPUT','1')!='0'
    print('EXPERIMENTAL '+('BACKGROUND WM input (unverified by Roblox)' if
          background_mode else 'FOREGROUND SendInput')+'. F10 STOP.')
    # Protect running automation from accidental conhost text-selection pause.
    if autopilot_disable_console_selection():
        log('CONSOLE_QUICKEDIT_DISABLED')
    else:
        log('CONSOLE_QUICKEDIT_NOT_AVAILABLE')
    if input('Type YES once to enable game control [NO]: ').strip().upper()!='YES':
        log('NOT_ARMED');return 0
    try:
        hwnd=verified_roblox_hwnd()
        io=(AutoPilotBackgroundInput(hwnd) if background_mode
            else AutoPilotInput(hwnd))
        log('INPUT_BACKEND='+('POSTMESSAGE_BG_EXPERIMENTAL' if background_mode
                            else 'SENDINPUT_FOREGROUND'))
    except Exception as e:
        log('GAME_WINDOW_FAILED '+repr(e));return 2
    q=queue.Queue(maxsize=1)
    stop=threading.Event()
    cap=WindowsCapture(cursor_capture=None,draw_border=None,
                       monitor_index=None,window_hwnd=hwnd)
    @cap.event
    def on_frame_arrived(frame:Frame,control:InternalCaptureControl):
        if stop.is_set():control.stop();return
        try:
            img=frame.frame_buffer[:,:,:3].copy()
            if q.full():
                try:q.get_nowait()
                except queue.Empty:pass
            q.put_nowait(img)
        except (queue.Full,ValueError):pass
    @cap.event
    def on_closed():stop.set()
    brain=AutoPilotPolicy()
    visual_ready=AutoPilotVisualReadyLock()
    pad_reselect=AutoPilotPadReselect()
    motion=AutoPilotMotionGuard()
    return_gate=AutoPilotReturnGate()
    route=AutoPilotRoute()
    route.load()
    controller=None
    begin=time.monotonic()
    last_sample=0.0
    last_action=0.0
    last_frame_at=begin
    last_focus_note=begin-10
    spawn_approach_steps=0
    spawn_approach_enabled=False
    last_phase=''
    menu_visible=0
    menu_candidate_since=None
    match_visible=0
    result_visible=0
    lobby_visible=0
    price_green=0
    wait_until=0.0
    halt_reason=None
    stage='WAIT_FOR_GAME'
    stage_since=begin
    progress_last=None
    route_since=None
    route_started=False
    pad_attempts=0
    last_pad_report_at=begin-10
    last_pad_pause_at=begin-10
    last_pad_pause_reason=None
    last_live_frame=None
    console_hwnd=0
    def reselect_pad(why,now):
        # No blind step to the next visible sign. Stop, preserve the overall
        # movement budget, and require three fresh READY samples.
        nonlocal wait_until,menu_candidate_since
        old_x=brain.target_x
        if not pad_reselect.begin_reselection(old_x,now,why):
            log('PAD_RESELECT_EXHAUSTED reason='+why+
                ' busy='+str(pad_reselect.reselections)+
                ' lost='+str(pad_reselect.lost_reacquisitions))
            return False
        motion.reset()
        visual_ready.reset()
        brain.target_x=None
        brain.last_x=None
        brain.no_progress=0
        brain.sign_misses=0
        brain.ready_history=[]
        brain.stage='DISCOVER'
        # Keep brain.move_actions, move_seconds and stage_since: retries may
        # not bypass the original 34-step/12-second/45-second cap.
        menu_candidate_since=None
        wait_until=now+1.2
        transition('LOBBY','PAD_RESELECT '+why,now)
        log('PAD_RESELECT reason='+why+' old_x='+str(old_x)+
            ' confirmed_busy='+str(pad_reselect.reselections)+'/2'+
            ' visual_reacquire='+str(pad_reselect.lost_reacquisitions)+'/3')
        return True

    def transition(next_stage,why,now):
        nonlocal stage,stage_since,last_phase
        if stage!=next_stage:
            log('STATE '+stage+' -> '+next_stage+' : '+why)
            stage=next_stage;stage_since=now;last_phase=''
    try:
        if background_mode:
            log('BACKGROUND_WINDOW_TARGET_VERIFIED: no focus stealing, '+
                'no global mouse or keyboard. WGC must verify all effects.')
        else:
            console_hwnd=autopilot_minimize_console()
            log('CONSOLE_MINIMIZED='+str(bool(console_hwnd)))
            if io.focus_game_once():
                log('ROBLOX_FOREGROUND_AUTO_OK')
            else:
                log('ROBLOX_FOREGROUND_AUTO_DENIED: click game window once; '+
                    'no game commands until focus is confirmed')
        controller=cap.start_free_threaded()
        log('CAPTURE_GAME_HWND='+str(hwnd)+' ROUTE='+route.note)
        while not stop.is_set() and time.monotonic()-begin<7200:
            now=time.monotonic()
            if io.stop_pressed() and io.focused():
                halt_reason='USER_F10';break
            if not io.focused():
                # Alt+Tab pauses every game input without discarding the run.
                # After the initial YES, never steal focus from another app.
                if now-last_focus_note>=10:
                    log('GAME_FOCUS_PAUSED: Roblox not foreground; '+
                        'all input suspended until Roblox is active again')
                    last_focus_note=now
                time.sleep(.15)
                continue
            try:frame=q.get(timeout=.4)
            except queue.Empty:
                if now-last_frame_at>8:
                    halt_reason='CAPTURE_STALLED';break
                continue
            last_frame_at=now
            last_live_frame=frame
            if now-last_sample<.45:continue
            last_sample=now
            scene,info=lifecycle_scene_hint(frame)
            modal,feat=autopilot_menu_features(frame)
            if modal:scene='CREATION_MENU'
            # Only the four-digit + button-color visual modal guard may
            # confirm the creation dialog; lifecycle hints are not sufficient.
            if modal:menu_visible+=1
            else:menu_visible=0
            if scene=='MATCH':match_visible+=1
            else:match_visible=0
            if scene=='RESULTS':result_visible+=1
            else:result_visible=0
            if (scene in ('LOBBY','LOBBY_COUNTDOWN_OR_PORTAL') and not modal
                    and stage not in ('WAIT_MATCH','MENU')):
                lobby_visible+=1
            else:lobby_visible=0
            if scene!=last_phase:
                log('SCENE '+scene+' stage='+stage)
                last_phase=scene
            if modal and menu_visible>=3 and stage not in ('MENU','WAIT_MATCH'):
                transition('MENU','creation dialog confirmed',now)
                brain.menu_index=0;brain.menu_tries={}
                brain.menu_confirmations=0;brain.create_sent=False
            if result_visible>=2:
                transition('RESULTS_WAIT','defeat/results seen',now)
            recovery=return_gate.observe(stage,scene,now,brain.match_index)
            if recovery=='RETURNED_LOBBY':
                motion.reset()
                visual_ready.reset()
                pad_reselect.reset()
                brain.reset_lobby(now)
                spawn_approach_steps=0
                spawn_approach_enabled=False
                return_gate.reset()
                transition('LOBBY','four verified lobby frames after a match',now)
                log('RETURN_COMPLETE: lobby cycle resumed without new game input')
                continue
            if recovery=='WAIT_FOR_RETURN':
                motion.reset()
                transition('WAIT_FOR_RETURN','game HUD gone/defeat/loading verified',now)
                log('RETURN_WAIT: no movement or turret presses until lobby confirmed')
                continue
            if recovery=='RETURN_TIMEOUT':
                halt_reason='RETURN_TIMEOUT_NO_VERIFIED_LOBBY';break
            if match_visible>=3 and stage in ('WAIT_MATCH','MENU','WAIT_FOR_GAME'):
                brain.match_index+=1
                return_gate.reset()
                transition('MATCH_ROUTE','in-game HUD verified',now)
                route_started=False;route_since=now;route.idx=0
                brain.turret_actions=0;brain.last_turret_at=0.0
            if stage=='WAIT_FOR_GAME':
                if lobby_visible>=3:
                    visual_ready.reset()
                    pad_reselect.reset()
                    brain.reset_lobby(now)
                    spawn_approach_steps=0
                    spawn_approach_enabled=False
                    transition('LOBBY','lobby seen',now)
                elif match_visible>=3:
                    brain.match_index+=1
                    return_gate.reset()
                    transition('MATCH_ROUTE','already in match',now)
                elif now-stage_since>25:
                    halt_reason='INITIAL_SCENE_UNKNOWN';break
                continue
            if stage=='RESULTS_WAIT':
                if lobby_visible>=3:
                    visual_ready.reset()
                    pad_reselect.reset()
                    brain.reset_lobby(now)
                    spawn_approach_steps=0
                    spawn_approach_enabled=False
                    return_gate.reset()
                    transition('LOBBY','auto-return to lobby',now)
                elif now-stage_since>90:
                    halt_reason='RESULTS_RETURN_TIMEOUT';break
                continue
            if stage=='WAIT_FOR_RETURN':
                # Results and even loading screens can be skipped by Roblox.
                # Recovery gate above accepts only 4 positive lobby samples.
                continue
            if stage=='LOBBY':
                if scene not in ('LOBBY','LOBBY_COUNTDOWN_OR_PORTAL'):
                    if now-stage_since>20:
                        halt_reason='LOBBY_SCENE_NOT_CONFIRMED';break
                    continue
                if now<wait_until:continue
                signs=pad_sign_hints(frame)
                if now-last_pad_report_at>=3:
                    h,w=frame.shape[:2]
                    log('PAD_HITS '+str([(s['status'],s['center_x'],s['confidence'])
                         for s in signs[:7]])+' frame='+str(w)+'x'+str(h))
                    last_pad_report_at=now
                # Exclusion applies to only READY after abandoning a pad.
                # Occupied signs are retained for ready_sign's busy veto.
                target=brain.ready_sign(pad_reselect.candidates(signs,now))
                if target is None:
                    # The last verified user screenshot is the distant spawn:
                    # READY text is too small/occluded to match from here.
                    # Only on the known grate scene, allow a tiny, bounded
                    # forward route while WGC verifies each physical shift.
                    if (not spawn_approach_enabled and
                            spawn_approach_steps==0 and
                            autopilot_spawn_grate_hint(frame)):
                        spawn_approach_enabled=True
                        log('SPAWN_GRATE_CONFIRMED: bounded W approach enabled')
                    if spawn_approach_enabled and spawn_approach_steps<12:
                        if motion.before is not None:
                            kind,shift,features=motion.verify(frame)
                            log('SPAWN_MOTION '+kind+' shift='+str(shift)+
                                ' features='+str(features))
                            if motion.stop_reason():
                                halt_reason='SPAWN_'+motion.stop_reason();break
                        if now-last_action>=.65:
                            motion.arm(frame)
                            if not io.keys('W',.22):
                                halt_reason='SPAWN_FORWARD_INPUT_REJECTED';break
                            spawn_approach_steps+=1
                            last_action=time.monotonic()
                            log('SPAWN_APPROACH W 0.22s step='+
                                str(spawn_approach_steps)+'/12')
                        continue
                    if spawn_approach_enabled and spawn_approach_steps>=12:
                        halt_reason='SPAWN_READY_NOT_FOUND_AFTER_12_STEPS'
                        break
                    if now-stage_since>12:
                        # PRIVATE image for a real gameplay run, not a new test mode.
                        try:
                            small=cv2.resize(frame,(960,540),interpolation=cv2.INTER_AREA)
                            cv2.imwrite(str(root/'AUTOPILOT_LAST_LOBBY.jpg'),small,
                                        [cv2.IMWRITE_JPEG_QUALITY,60])
                        except Exception:pass
                        halt_reason='READY_SIGN_NOT_STABLE_12S';break
                    continue
                brain.target_x=target
                spawn_approach_enabled=False
                motion.reset()
                visual_ready.reset()
                locked=[z for z in signs if
                        z.get('status')=='READY_SIGN'
                        and abs(z.get('center_x',-9)-target)<.10]
                if locked:
                    strong=max(locked,key=lambda z:z.get('confidence',0))
                    visual_ready.seed(frame,strong)
                pad_reselect.excluded_x=None
                transition('LOBBY_NAV','ready sign stable, approaching with feedback',now)
                # Preserve the total time limit across reselections. Reset
                # only on the first target of this lobby cycle.
                if brain.move_actions==0:
                    brain.stage_since=now
                brain.last_x=None
                continue
            if stage=='LOBBY_NAV':
                # First frame of the pad's creation dialog is not an error.
                # Wait for three consecutive verified modal frames without
                # movement or clicks. Reject persistent false positives.
                if scene=='CREATION_MENU':
                    if menu_candidate_since is None:
                        menu_candidate_since=now
                        log('MENU_CANDIDATE: modal='+str(modal)+
                            ' digits='+str(feat.get('digits'))+
                            ' create='+str(round(feat.get('create',0),3))+
                            ' cancel='+str(round(feat.get('cancel',0),3)))
                        try:
                            small=cv2.resize(frame,(960,540),interpolation=cv2.INTER_AREA)
                            cv2.imwrite(str(root/'AUTOPILOT_MENU_CANDIDATE.jpg'),small,
                                        [cv2.IMWRITE_JPEG_QUALITY,62])
                        except Exception:pass
                    if now-menu_candidate_since>6.0:
                        halt_reason='MENU_CANDIDATE_NOT_CONFIRMED_6S';break
                    continue
                menu_candidate_since=None
                if scene not in ('LOBBY','LOBBY_COUNTDOWN_OR_PORTAL'):
                    halt_reason='LOBBY_NAV_UNKNOWN_SCENE';break
                if now-last_action<.65:continue
                if motion.before is not None:
                    kind,shift,features=motion.verify(frame)
                    log('NAV_MOTION '+kind+' shift='+str(shift)+
                        ' features='+str(features))
                    if motion.stop_reason():
                        halt_reason='PAD_'+motion.stop_reason();break
                # Advance optical flow on EVERY sampled navigation frame.
                # Merely running the follower after a text miss loses the
                # intermediate frames needed for perspective/zoom changes.
                visual_flow=visual_ready.match(frame)
                signs=pad_sign_hints(frame)
                status,x,why=pad_reselect.check(signs,brain.target_x,now)
                if status=='WAIT':
                    # Only for a temporarily absent READY label: try to
                    # match the exact recently seen badge locally in WGC.
                    # Never use visual fallback when countdown is suspected.
                    local=(visual_flow
                           if why=='READY_TEMPORARILY_HIDDEN' else None)
                    if (local is not None and
                            local.get('confidence',0)>=.60 and
                            abs(local['center_x']-brain.target_x)<.18 and
                            visual_ready.fallback_pulses<
                                visual_ready.MAX_FALLBACK_PULSES):
                        action,key,unused=brain.lobby_movement(
                            local['center_x'],now)
                        if action=='HALT':
                            halt_reason=key;break
                        motion.arm(frame)
                        if not io.keys(key,.12):
                            halt_reason='VISUAL_FALLBACK_INPUT_FAILED';break
                        visual_ready.used_fallback_pulse()
                        last_action=time.monotonic()
                        log('NAV_VISUAL_FALLBACK '+key+
                            ' x='+str(local['center_x'])+
                            ' confidence='+str(local['confidence'])+
                            ' pulse='+str(visual_ready.fallback_pulses)+'/'+
                                str(visual_ready.MAX_FALLBACK_PULSES))
                        continue
                    if why!=last_pad_pause_reason or now-last_pad_pause_at>=3.0:
                        log('PAD_PAUSE '+why+' target_x='+str(brain.target_x))
                        last_pad_pause_at=now
                        last_pad_pause_reason=why
                    continue
                last_pad_pause_reason=None
                if status=='RESELECT':
                    if not reselect_pad(why,now):
                        halt_reason='PAD_RESELECT_LIMIT_'+why;break
                    continue
                brain.target_x=x
                seen=[z for z in signs if z.get('status')=='READY_SIGN'
                      and abs(z.get('center_x',-9)-x)<.07]
                if seen:
                    visual_ready.seed(frame,max(seen,
                        key=lambda z:z.get('confidence',0)))
                action,key,duration=brain.lobby_movement(x,now)
                if action=='HALT':
                    halt_reason=key;break
                motion.arm(frame)
                if not io.keys(key,duration):
                    halt_reason='GAME_KEY_NOT_CONFIRMED_BY_WIN32';break
                last_action=time.monotonic()
                log('NAV '+key+' '+str(duration)+' x='+str(round(x,3))+
                    ' steps='+str(brain.move_actions))
                if brain.move_actions>=34:
                    halt_reason='PAD_MENU_NOT_OPEN_AFTER_34_STEPS';break
                continue
            if stage=='MENU':
                if not modal:
                    if brain.create_sent:
                        transition('WAIT_MATCH','create dialog closed',now)
                    elif now-stage_since>8:
                        halt_reason='CREATION_DIALOG_LOST';break
                    continue
                if menu_visible<3:continue
                if now-last_action<.6:continue
                action,x,y,why=brain.menu_next(feat,now)
                if action=='HALT':halt_reason=why;break
                if action=='CLICK':
                    # The detected UI can shift up to ~32px vertically in
                    # 960x540 coordinates relative to the old OBS footage.
                    # Apply exactly that offset also to all menu clicks.
                    actual_y=y+float(feat.get('ui_shift',0))/540.0
                    if not io.click(x,actual_y,frame):
                        halt_reason='MENU_CLICK_NOT_SENT_'+why;break
                    log('MENU_ACTION '+why+' ui_shift='+str(feat.get('ui_shift',0))+
                        ' (not proof of click effect)')
                    last_action=time.monotonic()
                    if why=='CREATE_ONCE':
                        transition('WAIT_MATCH','create once sent; await match HUD',now)
                continue
            if stage=='WAIT_MATCH':
                if match_visible>=3:
                    brain.match_index+=1
                    return_gate.reset()
                    transition('MATCH_ROUTE','match confirmed after create',now)
                    route_since=now;route.idx=0;route_started=False
                    brain.turret_actions=0;brain.last_turret_at=0.0
                elif now-stage_since>75:
                    halt_reason='CREATE_NOT_CONFIRMED_IN_GAME';break
                continue
            if stage=='MATCH_ROUTE':
                if scene in ('DANGER_OR_DEFEAT','RESULTS','LOADING'):
                    continue
                if scene!='MATCH':
                    if now-stage_since>12:
                        halt_reason='MATCH_SCENE_LOST_DURING_ROUTE';break
                    continue
                if route.ready:
                    tag,score=route.classify(frame)
                    if tag=='SAFE_CORNER':
                        log('CORNER_CONFIRMED matches='+str(score))
                        transition('MATCH_DEFEND','reached defensive corner',now)
                        continue
                    if route.idx==0 and tag!='START':
                        if now-stage_since>10:
                            halt_reason='MATCH_START_POSE_UNMATCHED';break
                        continue
                    # A recorded route that still shows the START viewpoint
                    # after multiple commands has not demonstrated progress.
                    if route.idx>=16 and tag=='START':
                        halt_reason='ROUTE_NO_VISUAL_PROGRESS';break
                    if now-last_action<.46:continue
                    if motion.before is not None:
                        kind,shift,features=motion.verify(frame)
                        if route.idx%4==0:
                            log('ROUTE_MOTION '+kind+' shift='+str(shift)+
                                ' features='+str(features))
                        if motion.stop_reason():
                            halt_reason='ROUTE_'+motion.stop_reason();break
                    if route.idx>=len(route.steps):
                        halt_reason='ROUTE_FINISHED_WITHOUT_CORNER_CONFIRMATION';break
                    t,keys,duration=route.steps[route.idx]
                    motion.arm(frame)
                    if not io.keys(keys,duration):
                        halt_reason='ROUTE_KEY_FAILED';break
                    route.idx+=1;last_action=time.monotonic()
                    if route.idx%10==0:log('ROUTE_STEP '+str(route.idx)+'/'+str(len(route.steps)))
                    if now-stage_since>45:
                        halt_reason='ROUTE_TIMEOUT';break
                else:
                    halt_reason='ROUTE_UNAVAILABLE_'+route.note;break
                continue
            if stage=='MATCH_DEFEND':
                if scene!='MATCH':continue
                tag,score=route.classify(frame)
                if tag!='SAFE_CORNER':
                    halt_reason='DEFENSIVE_CORNER_LOST';break
                if brain.turret_actions>=12:continue
                if now-brain.last_turret_at<5:continue
                cost,red,green=turret_price_color_signal(frame)
                price_green=(price_green+1) if cost=='GREEN' else 0
                if price_green<4:continue
                if not io.keys('Z',.10):
                    halt_reason='TURRET_KEY_FAILED';break
                brain.turret_actions+=1
                brain.last_turret_at=time.monotonic()
                price_green=0
                log('TURRET_Z_SENT_UNVERIFIED count='+str(brain.turret_actions))
                continue
            if now-stage_since>180:
                halt_reason='STATE_TIMEOUT_'+stage;break
        if halt_reason is None:
            halt_reason='SESSION_LIMIT_OR_GAME_CLOSED'
        log('AUTOPILOT_STOP '+halt_reason+' matches='+str(brain.match_index)+
            ' turret_presses='+str(brain.turret_actions))
        if halt_reason!='USER_F10' and last_live_frame is not None:
            try:
                image=cv2.resize(last_live_frame,(960,540),interpolation=cv2.INTER_AREA)
                name=root/'AUTOPILOT_LAST_STATE.jpg'
                cv2.imwrite(str(name),image,[cv2.IMWRITE_JPEG_QUALITY,60])
                log('LAST_STATE_IMAGE='+str(name))
            except Exception as exc:
                log('LAST_STATE_IMAGE_FAILED '+type(exc).__name__)
        return 0 if halt_reason=='USER_F10' else 2
    except Exception:
        log('AUTOPILOT_EXCEPTION '+traceback.format_exc())
        return 2
    finally:
        stop.set()
        if controller is not None:
            try:controller.stop()
            except Exception:pass
        autopilot_restore_console(console_hwnd)
# === End ROBLOX V3.5 AUTOPILOT ===





def run_mode_prompt():
    print("")
    print("ROBLOX V"+VERSION+" - choose mode:")
    print("  1 = monitor 120 seconds (no screenshots)")
    print("  2 = LEARN human gameplay (5-second JPEGs, ZIP parts)")
    print("  3 = LOBBY assistant (observe / confirmed foreground clicks)")
    print("  4 = BATTLE movement pilot (in-match F8, brief WASD, evidence)")
    print("  5 = ONE-TURRET pilot (F8, wait for green Z price, one Z attempt)")
    print("  6 = ROUTE demo (you walk once from spawn to the safe corner; keys+frames)")
    print("  7 = ROUTE VISION (F10 marks defensive corner; NO game input)")
    print("  8 = GUARDED TURRET (calibrated corner + green Z, one build attempt)")
    print("  9 = LOBBY PAD demo (F8 route, F10 arrival; NO WAIT on pad)")
    print(" 10 = LIFECYCLE observer (guarded phases; no game input)")
    print(" 11 = OFFLINE replay of existing OBS MP4 (no Roblox or game input)")
    print(" 12 = PAD SCOUT: offline portal geometry from old video; no game input")
    print(" 13 = PAD SIGN REPLAY: read old PAD SCOUT ZIP, identify signs offline")
    print(" 14 = PAD SIGNS LIVE: read-only lobby sign observer; NO movement")
    print(" 15 = AUTOPILOT: lobby -> match -> corner -> turrets -> return (YES/F10)")
    try:
        choice = input("Choose mode 1-15 [1]: ").strip()
    except EOFError:
        choice = "1"
    return choice

selected_mode = run_mode_prompt()
if selected_mode == "2":
    raise SystemExit(training_mode())
if selected_mode == "3":
    raise SystemExit(lobby_helper())
if selected_mode == "4":
    raise SystemExit(battle_pilot())
if selected_mode == "5":
    raise SystemExit(battle_pilot(build_once=True))
if selected_mode == "6":
    raise SystemExit(route_demo())
if selected_mode == "7":
    raise SystemExit(route_visual_observer())
if selected_mode == "8":
    raise SystemExit(battle_pilot(build_once=True,require_corner=True))
if selected_mode == "9":
    raise SystemExit(route_demo(destination="lobby"))
if selected_mode == "10":
    raise SystemExit(lifecycle_observer())
if selected_mode == "11":
    raise SystemExit(replay_obs_video())
if selected_mode == "12":
    raise SystemExit(pad_scout_offline())
if selected_mode == "13":
    raise SystemExit(pad_sign_replay())
if selected_mode == "14":
    raise SystemExit(pad_sign_live_observer())
if selected_mode == "15":
    raise SystemExit(autopilot_mode())

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

stats = {"received": 0, "analyzed": 0, "changes": 0, "last": 0.0, "errors": 0, "left": 0.0, "center": 0.0, "right": 0.0, "possible_match": 0, "hud_mode": "UNCONFIRMED", "hud_strength": 0.0, "turret_price_signal":"UNKNOWN","turret_color_samples":{"RED":0,"GREEN":0,"UNKNOWN":0}}
lock = threading.Lock()
start = time.monotonic()
previous = None
last_sample = 0.0
stopping = threading.Event()
with CSV.open("w", encoding="utf-8") as f:
    f.write("elapsed_sec,frames,motion_score,changed,left_motion,center_motion,right_motion,hud_mode,hud_strength,turret_price_color,red_fraction,green_fraction\n")

capture = WindowsCapture(cursor_capture=None, draw_border=None,
                         monitor_index=None, window_hwnd=verified_roblox_hwnd())

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
        turret_color,price_red,price_green=turret_price_color_signal(frame.frame_buffer)
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
            stats["turret_color_samples"][turret_color] += 1
            stats["turret_price_signal"] = turret_color
            count = stats["received"]
        with CSV.open("a", encoding="utf-8") as f:
            f.write(f"{now-start:.1f},{count},{motion:.3f},{changed},{region_motion[0]:.3f},{region_motion[1]:.3f},{region_motion[2]:.3f},{hud_mode},{hud_strength:.3f},{turret_color},{price_red:.3f},{price_green:.3f}\n")
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
              f"Turret Z price affordability (color only): {stats['turret_price_signal']}\n"
              f"Turret affordability samples: {stats['turret_color_samples']}\n"
              f"Prices are dynamic; no automatic purchases in this release.\n"
              f"Input test: {'enabled' if os.environ.get('ROBLOX_BG_CONTROL_TEST') == '1' else 'disabled'}\n"
              f"Errors: {stats['errors']}\n"
              f"Screenshots saved: 0\n")
    if stats["received"] == 0:
        report += "WARNING: zero frames received. Keep Roblox restored.\n"
    SUMMARY.write_text(report, encoding="utf-8")
    note(report.replace("\n", " | "))
    note("Results folder: " + str(ROOT))
