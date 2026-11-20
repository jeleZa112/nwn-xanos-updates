#!/usr/bin/env python3
"""Launch the usual InfinityLoader with redirected console, without INI changes.

A documented EEex debugging method is to redirect InfinityLoader console output.
This script starts the normal loader and returns; the redirection stays alive in
the child until the game exits. Report 135 reads the resulting log afterwards.
"""
from __future__ import annotations
import argparse,datetime,json,os,pathlib,subprocess,sys
import BGX_FRIEND_TRACE_GUARDED as V1
import BGXFTRACE_V2_GUARDED as V2
import BGXRANGED_V3_GUARDED_INSTALL as V3

ROOT=V2.ROOT
def start(root):
    V3.V2.V1.processes()
    current=V2.status(root)
    if current.get("status")!="BGXF2_INSTALLED_VERIFIED":
        raise ValueError("V2_OBSERVER_NOT_VERIFIED")
    exe=root/"InfinityLoader.exe";V2.guard(exe)
    if not exe.is_file() or exe.is_symlink() or exe.read_bytes()[:2]!=b"MZ":
        raise ValueError("INFINITYLOADER_EXE_NOT_FOUND")
    output=pathlib.Path(os.environ.get("USERPROFILE",str(pathlib.Path.home())))/"Documents"/"BGXAI_LIVE_REPORTS"
    V2.guard(output);output.mkdir(parents=True,exist_ok=True)
    path=output/("BGXAI_FRIEND_CONSOLE_"+datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")+".log")
    V2.guard(path)
    # This file is exclusively diagnostic; the source is never installed as
    # a game script and never overwrites a previous report or any save.
    try:
        with path.open("xb") as f:
            p=subprocess.Popen([str(exe)],cwd=root,stdin=subprocess.DEVNULL,
                               stdout=f,stderr=subprocess.STDOUT,close_fds=True)
    except (OSError,ValueError):
        raise ValueError("INFINITYLOADER_START_FAILED_CHECK_CAPTURE")
    return {"status":"INFINITYLOADER_CAPTURE_LAUNCH_REQUESTED",
            "child_pid":p.pid,"console_log":str(path),"game_modified":False,
            "runtime_hook_verified":False,
            "next_step":"Play normally, exit game, run existing menu 135 to inspect console trace"}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--game",default=str(ROOT))
    root=pathlib.Path(ap.parse_args().game)
    try:
        print(json.dumps(start(root),ensure_ascii=False,indent=2));return 0
    except Exception as e:
        print("BGXF2_CAPTURE_STOP:"+str(e));return 1
if __name__=="__main__":sys.exit(main())
