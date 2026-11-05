# Roblox background monitor - release 2.1.3
# Uses Windows Graphics Capture, processes frames only in RAM.
import os, sys, time, threading, traceback
from pathlib import Path

VERSION = "2.1.3"
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
    print("\nROBLOX LOBBY BOT V2.1.3")
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
    last_update = 0.
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
    log("Lobby v2.1.3 start; armed="+str(enabled))
    log("Strict sequence CITY -> ONE -> HARD(RED BORDER) -> CREATE")
    log("SYNTHETIC retries: up to 3 verified attempts for ONE, 2 for HARD; "+
        "CREATE strictly once. Alternate safe points inside the same tile.")
    log("HARD_CHECK requires red hard border + normal green not selected")
    log("Before/after click evidence in "+str(evidence_dir)+"; JPEG overwritten per step.")
    try:
        controller=capture.start_free_threaded()
        while not stop.is_set() and time.monotonic()-start < 150:
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
                if step_index==3 and awaiting_confirmation:
                    menu_absent_count+=1
                    if menu_absent_count>=4:
                        completed=True
                        log("CREATE_DIALOG_CLOSED: possible success; verify countdown in Roblox")
                        break
                continue
            menu_absent_count=0
            menu_present_count+=1
            if menu_present_count<4:
                continue
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
                if time.monotonic()-last_click>7:
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
    print("ROBLOX V2.1.3 - choose mode:")
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
    note("Run: py -3 -m pip install --user windows-capture==2.1.3 numpy opencv-python")
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
