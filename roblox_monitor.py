# Roblox background monitor - release 3.2.1
# Uses Windows Graphics Capture, processes frames only in RAM.
import os, sys, time, threading, traceback
from pathlib import Path

VERSION = "3.2.1"
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
                           monitor_index=None,window_name="Roblox")
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
                       monitor_index=None,window_name="Roblox")
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
                       monitor_index=None,window_name="Roblox")
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
                       monitor_index=None,window_name="Roblox")
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
                             monitor_index=None,window_name="Roblox")

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
    try:
        choice = input("Choose mode 1-11 [1]: ").strip()
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
