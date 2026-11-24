"""BG_EET_RU V126: guarded *visible-row* UI observer, NOT a native Hit hook.

Only one game file may be changed, override/UI.MENU, after explicit typed
approval and exact V125 live SHA. Every write gets an external SHA backup.
Output is renderer-level evidence, never a native message/attack identity.
"""
from __future__ import annotations
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import zipfile

SCHEMA="BG_EET_RU_V126_VISIBLE_ROW_OBSERVER_GUARDED"
ENTRY="63_V126_VISIBLE_ROW_OBSERVER.json"
UI_PIN="86ba0c4c36b33a97c4dd57f07ee344df6c2198f46f444f574c798791ad6f7a09"
APPROVE_INSTALL="INSTALL_BG_EET_RU_V126_VISIBLE_ROW_OBSERVER"
APPROVE_ROLLBACK="ROLLBACK_BG_EET_RU_V126_VISIBLE_ROW_OBSERVER"
MARK="BG_EET_RU_V126_RowRecord"
MAX_CAPTURE=256_000

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def external(game:Path,path:Path):
    if path.resolve().is_relative_to(game.resolve()):
        raise RuntimeError("EXTERNAL_PATH_INSIDE_GAME_FORBIDDEN")

def regular(path:Path):
    if path.is_symlink() or not path.is_file():
        raise RuntimeError("REQUIRED_REGULAR_FILE_MISSING:"+path.name)

def closed():
    if os.name!="nt":return False,"NOT_WINDOWS"
    try:
        proc=subprocess.run(["tasklist.exe","/FO","CSV","/NH"],capture_output=True,timeout=15,check=False)
        if proc.returncode:return False,"TASKLIST_FAILURE"
        names={x[0].strip().casefold() for x in csv.reader(io.StringIO(proc.stdout.decode("utf-8-sig","replace"))) if x}
        busy=names.intersection({"baldur.exe","infinityloader.exe","weidu.exe"})
        return (not busy),",".join(sorted(busy)) if busy else "CLOSED"
    except (OSError,ValueError,subprocess.TimeoutExpired) as e:
        return False,type(e).__name__

def ui_file(game:Path):
    path=game/"override"/"UI.MENU"
    external(game,game.parent/"BG_EET_RU_NOT_USED") if False else None
    regular(path)
    if path.stat().st_size>1_500_000:raise RuntimeError("UI_FILE_TOO_LARGE")
    return path

def state_file(work:Path):
    return work/"BG_EET_RU_V126_ROW_OBSERVER_STATE.json"

def load_state(work:Path):
    path=state_file(work)
    if not path.exists():return None
    regular(path)
    if path.stat().st_size>16000:raise RuntimeError("STATE_TOO_LARGE")
    state=json.loads(path.read_text("utf8"))
    if state.get("schema")!=SCHEMA or state.get("phase") not in ("PREPARED","INSTALLED","ROLLED_BACK"):
        raise RuntimeError("UNKNOWN_STATE_HOLD")
    return state

def save_json_atomic(path:Path, obj:dict):
    if path.is_symlink():raise RuntimeError("STATE_SYMLINK_DENIED")
    temp=path.with_name(path.name+".stage")
    if temp.exists():raise RuntimeError("STATE_TEMP_COLLISION")
    try:
        with temp.open("x",encoding="utf8") as f:
            json.dump(obj,f,ensure_ascii=False,indent=2)
            f.flush();os.fsync(f.fileno())
        if json.loads(temp.read_text("utf8"))!=obj:raise RuntimeError("STATE_STAGE_VERIFY")
        os.replace(temp,path)
    finally:
        if temp.exists():temp.unlink()

def lua_observer(log:Path)->str:
    # JSON quoting is valid in Lua string literals for normal ASCII Win10 paths.
    quoted=json.dumps(str(log),ensure_ascii=True)
    return r'''
-- BG_EET_RU V126 SOURCE: passive UI-rendered-row probe, no native message pointer.
BG_EET_RU_V126_RowState = {count=0,seen={},failures=0,max=160}
function BG_EET_RU_V126_RowRecord(row,value)
  local state=BG_EET_RU_V126_RowState
  local ok = pcall(function()
    if type(row)~='number' or row~=row or row%1~=0 or row<0 then return end
    if type(value)~='string' or #value>12000 then return end
    if state.count>=state.max then return end
    local compact=value:sub(1,1000):gsub('[\t\r\n]',' ')
    local key=tostring(row)..'\t'..compact
    if state.seen[key] then return end
    -- Base EE does not open the io library. Engine print() is the primary
    -- capture channel; io.open is only a guarded optional EEex extension.
    if type(print)=='function' then
      pcall(print,'BG_EET_RU_V126_ROW\t'..tostring(row)..'\t'..compact)
    end
    if type(io)=='table' and type(io.open)=='function' then
      pcall(function()
        local f=io.open(__V126_LOG_PATH__,'ab')
        if f then f:write('ROW\t',tostring(row),'\t',compact,'\n');f:close() end
      end)
    end
    state.seen[key]=true
    state.count=state.count+1
  end)
  if not ok then state.failures=state.failures+1 end
  return value -- identical display value, no text modifications
end
'''.replace("__V126_LOG_PATH__",quoted)

def candidate(original:bytes,log:Path)->bytes:
    if original.startswith(b"\xef\xbb\xbf"):
        raise RuntimeError("UI_BOM_UNEXPECTED_HOLD")
    try:s=original.decode("utf8")
    except UnicodeDecodeError as e:raise RuntimeError("UI_UTF8_REQUIRED") from e
    if MARK in s:raise RuntimeError("V126_ALREADY_PRESENT_OR_CONFLICT")
    exprs=list(re.finditer(r'text lua "([^"\r\n]*combatLog\[rowNumber\][^"\r\n]*)"',s))
    if len(exprs)!=1:raise RuntimeError("RENDERER_MATCH_NOT_UNIQUE")
    expr=exprs[0].group(1)
    if expr not in ("clean(combatLog[rowNumber])","BG_EET_RU_LogView(clean(combatLog[rowNumber]))"):
        raise RuntimeError("RENDERER_EXPRESSION_UNEXPECTED")
    marker="function clean(str)"
    if s.count(marker)!=1:raise RuntimeError("CLEAN_LUA_INJECTION_NOT_UNIQUE")
    # Insert into existing top-level Lua area immediately before clean(). Never touch MENU grammar.
    s=s.replace(marker,lua_observer(log).replace("\n","\r\n" if "\r\n" in s else "\n")+
                ("\r\n" if "\r\n" in s else "\n")+marker,1)
    old='text lua "'+expr+'"'
    replacement='text lua "'+MARK+'(rowNumber, '+expr+')"'
    if s.count(old)!=1:raise RuntimeError("RENDERER_SOURCE_DRIFT")
    s=s.replace(old,replacement,1)
    if s.count(MARK+'(rowNumber,')!=1 or s.count("function "+MARK+"(")!=1:
        raise RuntimeError("CANDIDATE_INJECTION_ASSERTION_FAILED")
    new=s.encode("utf8")
    if len(new)>len(original)+4500:raise RuntimeError("CANDIDATE_SIZE_DRIFT")
    return new

def write_ui_atomic(ui:Path,source:bytes,expected_before:str,expected_after:str,tag:str):
    if sha(ui.read_bytes())!=expected_before:raise RuntimeError("UI_SOURCE_SHA_RACE")
    temp=ui.with_name("UI.MENU."+tag+".stage")
    if temp.exists():raise RuntimeError("UI_TEMP_COLLISION")
    try:
        with temp.open("xb") as f:
            f.write(source);f.flush();os.fsync(f.fileno())
        if sha(temp.read_bytes())!=expected_after or sha(ui.read_bytes())!=expected_before:
            raise RuntimeError("UI_STAGED_OR_SOURCE_SHA_DRIFT")
        os.replace(temp,ui)
        if sha(ui.read_bytes())!=expected_after:raise RuntimeError("UI_SWAP_VERIFY_FAILED")
    finally:
        if temp.exists():temp.unlink()

def backup_external(game:Path,work:Path,raw:bytes):
    folder=work/"SAFE_BACKUPS"
    external(game,folder)
    if folder.is_symlink():raise RuntimeError("BACKUP_FOLDER_SYMLINK")
    folder.mkdir(parents=True,exist_ok=True)
    path=folder/("UI_MENU_V126_"+sha(raw)[:20]+".bak")
    if path.exists():
        regular(path)
        if sha(path.read_bytes())!=sha(raw):raise RuntimeError("BACKUP_COLLISION_HOLD")
    else:
        with path.open("xb") as f:f.write(raw);f.flush();os.fsync(f.fileno())
    if sha(path.read_bytes())!=sha(raw):raise RuntimeError("BACKUP_SHA_FAIL")
    return path

def capture(work:Path)->dict:
    lines=[]
    sources=[]
    raw_tsv=work/"BG_EET_RU_V126_VISIBLE_ROWS.tsv"
    logs=sorted(work.glob("BG_EET_RU_V126_CONSOLE_*.log"),key=lambda p:p.stat().st_mtime,reverse=True)
    for path in ([raw_tsv] if raw_tsv.is_file() else [])+logs[:1]:
        regular(path)
        limit=8_000_000 if path.suffix==".log" else MAX_CAPTURE
        if path.stat().st_size>limit:return {"status":"ROW_CAPTURE_OVERSIZE_HOLD","path":str(path)}
        raw=path.read_bytes()
        if len(raw)>limit:return {"status":"ROW_CAPTURE_OVERSIZE_HOLD","path":str(path)}
        sources.append({"name":path.name,"bytes":len(raw),"sha256":sha(raw)})
        for line in raw.decode("utf8","replace").splitlines():
            if path.suffix==".log":
                pos=line.find("BG_EET_RU_V126_ROW\t")
                if pos<0:continue
                line="ROW\t"+line[pos+len("BG_EET_RU_V126_ROW\t"):]
            parts=line.split("\t",2)
            if len(parts)==3 and parts[0]=="ROW" and parts[1].isdigit():
                lines.append((int(parts[1]),parts[2][:1000]))
    unique=list(dict.fromkeys(lines))[:160]
    return {"status":"UI_RENDER_ROWS_CAPTURED_NO_MESSAGE_JOIN" if unique else "NO_UI_ROW_CAPTURE_YET",
            "rows":len(unique),"sources":sources,
            "samples":[{"ui_row_number":n,"rendered_text":t} for n,t in unique],
            "native_message_pointer_verified":False,"attack_sequence_verified":False,
            "row_to_weapon_join_verified":False}

def launch_capture(game:Path,work:Path):
    state=load_state(work)
    if not state or state["phase"]!="INSTALLED":
        raise RuntimeError("V126_NOT_INSTALLED_FOR_CONSOLE_CAPTURE")
    ui=ui_file(game)
    if sha(ui.read_bytes())!=state["new_sha"]:
        raise RuntimeError("V126_CAPTURE_UI_SHA_DRIFT")
    ok,why=closed()
    if not ok:raise RuntimeError("CLOSE_GAME_AND_LOADER_BEFORE_CAPTURE:"+why)
    loader=game/"InfinityLoader.exe"
    regular(loader)
    with loader.open("rb") as f:
        if f.read(2)!=b"MZ":raise RuntimeError("INFINITYLOADER_NOT_WINDOWS_EXE")
    from datetime import datetime,timezone
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    path=work/("BG_EET_RU_V126_CONSOLE_"+stamp+".log")
    if path.exists():raise RuntimeError("CONSOLE_CAPTURE_COLLISION")
    with path.open("xb") as output:
        proc=subprocess.Popen([str(loader)],cwd=game,stdin=subprocess.DEVNULL,
                              stdout=output,stderr=subprocess.STDOUT,close_fds=True)
        exit_code=proc.wait()
    result=_status(game,work,"status",UI_PIN,lambda _:False)
    result["mode"]="capture"
    result["capture_exit_code"]=exit_code
    result["console_log"]=str(path)
    result["captured"]=capture(work)
    result["status"]=("V126_CAPTURED_RENDERED_ROWS_UNCORRELATED" if
                      result["captured"]["rows"] else "V126_CAPTURE_FINISHED_NO_ROWS_HOLD")
    return result

def _approval(expected:str):
    answer=input("Type "+expected+" exactly; ENTER cancels: ").strip()
    return answer==expected

def _status(game:Path,work:Path,mode:str,expected_ui_sha:str,request_approval):
    game=Path(game);work=Path(work)
    external(game,work)
    work.mkdir(parents=True,exist_ok=True)
    ui=ui_file(game)
    original=ui.read_bytes()
    actual=sha(original)
    current=load_state(work)
    report={"schema":SCHEMA,"mode":mode,"status":"HOLD","ui_sha256":actual,
            "expected_baseline_sha256":expected_ui_sha,"game_files_written":0,
            "native_hooks_installed":False,"native_abi_verified":False,
            "miss_weapon_verified":False,"combat_row_join_verified":False,
            "display_text_unchanged_by_probe":True,"captured":capture(work)}
    if current and current["phase"] in ("INSTALLED","PREPARED"):
        if actual not in (current["old_sha"],current["new_sha"]):
            raise RuntimeError("UI_CHANGED_SINCE_V126_STATE")
        if mode=="install":
            report["status"]="ALREADY_INSTALLED_OR_PREPARED_NO_WRITE";return report
        if mode=="status":
            report["status"]="INSTALLED_AWAITING_UI_ROW_CAPTURE" if (current["phase"]=="INSTALLED" and actual==current["new_sha"]) else "PREPARED_RECOVERY_HOLD"
            return report
        # Rollback only our exact candidate; NEVER touch a foreign UI modification.
        ok,why=closed()
        if not ok:raise RuntimeError("CLOSE_GAME_AND_LOADER_FOR_ROLLBACK:"+why)
        backup=Path(current["backup"])
        external(game,backup);regular(backup)
        data=backup.read_bytes()
        if sha(data)!=current["old_sha"]:raise RuntimeError("ORIGINAL_BACKUP_SHA_FAILED")
        if not request_approval(APPROVE_ROLLBACK):
            report["status"]="ROLLBACK_NOT_APPROVED";return report
        ok,why=closed()
        if not ok:raise RuntimeError("GAME_RESTARTED_DURING_ROLLBACK:"+why)
        if actual==current["new_sha"]:
            write_ui_atomic(ui,data,current["new_sha"],current["old_sha"],"v126restore")
            report["game_files_written"]=1
        current["phase"]="ROLLED_BACK"
        save_json_atomic(state_file(work),current)
        report["status"]="V126_RESTORED_ORIGINAL_UI_EXACT_SHA";return report
    if mode=="rollback":
        report["status"]="V126_NOT_INSTALLED_NO_ROLLBACK";return report
    if current and current["phase"]!="ROLLED_BACK":
        raise RuntimeError("V126_UNRECOGNIZED_STATE")
    if actual!=expected_ui_sha:
        raise RuntimeError("LIVE_UI_SHA_NOT_V125_PINNED")
    patch=candidate(original,work/"BG_EET_RU_V126_VISIBLE_ROWS.tsv")
    patchsha=sha(patch)
    report["candidate_sha256"]=patchsha
    if mode=="status":
        report["status"]="V126_GUARDED_PREFLIGHT_READY_NOT_INSTALLED";return report
    if mode!="install":raise RuntimeError("UNKNOWN_MODE")
    ok,why=closed()
    if not ok:raise RuntimeError("CLOSE_GAME_AND_LOADER_FOR_INSTALL:"+why)
    if not request_approval(APPROVE_INSTALL):
        report["status"]="INSTALL_NOT_APPROVED";return report
    ok,why=closed()
    if not ok:raise RuntimeError("GAME_RESTARTED_DURING_APPROVAL:"+why)
    if sha(ui.read_bytes())!=actual:raise RuntimeError("UI_CHANGED_DURING_APPROVAL")
    backup=backup_external(game,work,original)
    state={"schema":SCHEMA,"phase":"PREPARED","old_sha":actual,"new_sha":patchsha,
           "backup":str(backup),"ui_path":str(ui)}
    save_json_atomic(state_file(work),state)
    write_ui_atomic(ui,patch,actual,patchsha,"v126install")
    state["phase"]="INSTALLED"
    save_json_atomic(state_file(work),state)
    report["game_files_written"]=1
    report["status"]="V126_VISIBLE_ROW_OBSERVER_INSTALLED_AWAITING_RUNTIME_UI_TEST"
    return report

def zip_report(game:Path,path:Path,result:dict):
    external(game,path)
    regular(path)
    with zipfile.ZipFile(path) as src:
        names=src.namelist()
        if src.testzip() is not None or len(names)!=len(set(names)):
            raise RuntimeError("PRIOR_ZIP_INVALID")
        if ENTRY in names and json.loads(src.read(ENTRY))==result:return
    with tempfile.NamedTemporaryFile(dir=path.parent,suffix=".zip",prefix=".v126_",delete=False) as out:
        temp=Path(out.name)
    try:
        with zipfile.ZipFile(path) as src,zipfile.ZipFile(temp,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=7) as dst:
            for member in src.infolist():
                if member.filename!=ENTRY:dst.writestr(member,src.read(member))
            dst.writestr(ENTRY,json.dumps(result,ensure_ascii=False,indent=2).encode("utf8"))
        with zipfile.ZipFile(temp) as z:
            if z.testzip() is not None or z.namelist().count(ENTRY)!=1:
                raise RuntimeError("RESULT_ZIP_VERIFY_FAILED")
        os.replace(temp,path)
    finally:
        if temp.exists():temp.unlink()

def run(game,report_path,mode="status"):
    game=Path(game).resolve();report_path=Path(report_path).resolve()
    work=report_path.parent
    result={"schema":SCHEMA,"mode":mode,"game_files_written":0,
            "native_hooks_installed":False,"gameplay_verified":False,
            "status":"V126_PREFLIGHT_HOLD"}
    try:
        if mode not in ("status","install","rollback","capture"):raise RuntimeError("UNKNOWN_MODE")
        result=launch_capture(game,work) if mode=="capture" else _status(game,work,mode,UI_PIN,_approval)
    except (OSError,RuntimeError,ValueError,UnicodeError,json.JSONDecodeError) as e:
        result["status"]="V126_SAFE_STOP"
        result["hold_reason"]=type(e).__name__+":"+str(e)[:180]
    try:zip_report(game,report_path,result)
    except Exception as e:
        print("V126 ZIP SAFE STOP",type(e).__name__,str(e)[:140]);return 2
    print("V126:",result["status"],"game writes:",result["game_files_written"])
    print("One ZIP:",report_path)
    return 2 if result["status"]=="V126_SAFE_STOP" else 0
