"""R33 one-file menu172 candidate builder. ZERO installed game mutations.

Only compacts already-existing native PowerShell cmdlet syntax *before* switch.
Every existing switch dispatch 1..171 stays EXACTLY byte-for-byte unchanged.
The original immutable bootstrap CMD is never changed; 80 KB hard cap retained.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
LIVE = REPO / "BGXAI/BGXAI_SYNC.ps1"
GUARD = HERE / "R33_GUARDED_SOURCE_ONLY.py"
CANDIDATE = HERE / "M_BGXR27_R33_SOURCE_ONLY.lua"
R31_PIN = "c998ff6607ee3915b9cbb3c9b31955f715bee425b5ed882e04e1af1d515ed4aa"
R33_LUA_SHA = "1420ef723df1090d56f8f6590fd82e5c69107ba97a39b2ca2ba73f93e0e77069"
MENU = "BGXAI/BUILD/R33_R31_REUSE_PROF_SNAPSHOT_RO_20261125/"
MAX = 80000


class Hold(ValueError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def dispatches(src: str) -> list[str]:
    return re.findall(r"(?m)^'([1-9][0-9]*)' \{[^\n]+\}$", src)


def source_bytes() -> tuple[bytes, bytes]:
    g,b = GUARD.read_bytes(), CANDIDATE.read_bytes()
    if not 15000 < len(g) < 35000 or digest(b) != R33_LUA_SHA or len(b) != 49438:
        raise Hold("R33_IMMUTABLE_INPUT_DRIFT")
    if b.count(b"EEex_Action_AddSpriteStartedActionListener,pilot.listener")!=1:
        raise Hold("R33_SECOND_LISTENER")
    return g,b


def build(base: bytes | None = None) -> bytes:
    g,b = source_bytes()
    current = LIVE.read_bytes() if base is None else base
    if len(current)!=79941 or digest(current)!=R31_PIN:
        raise Hold("R31_PINNED_UPDATER_BASELINE_SHA_DRIFT")
    old = current.decode("utf-8")
    marker = "switch($choice){\n"
    if old.count(marker)!=1:
        raise Hold("R31_MENU_DISPATCH_ANCHOR_DRIFT")
    before,after=old.split(marker,1)
    d=dispatches(marker+after)
    if d!=[str(i) for i in range(1,172)]:
        raise Hold("R31_DISPATCH_1_171_CHANGED")
    if before.count("Set-Alias wh Write-Host -Scope Script\n")!=1:
        raise Hold("R31_WRITEHOST_ALIAS_DRIFT")
    if before.count("Join-Path ")<140 or before.count("Test-Path ")<35:
        raise Hold("R31_COMPACTION_TOKEN_COUNTS_CHANGED")
    # Exact aliasing to the ORIGINAL native cmdlets, never deleting any logic.
    before=before.replace("Join-Path ","jp ").replace("Test-Path ","tp ")
    before=before.replace("Set-Alias wh Write-Host -Scope Script\n",
         "Set-Alias wh Write-Host -Scope Script\nSet-Alias jp Join-Path -Scope Script\nSet-Alias tp Test-Path -Scope Script\n",1)
    before=before.replace("171 R31 V3\n", "171 R31 V3 | 172 R33\n",1)
    gh=digest(g)
    handler=(
        "'172' {$p='"+MENU+"';"
        "$a=Get-PinnedBytes ($p+'R33_GUARDED_SOURCE_ONLY.py');"
        "$b=Get-PinnedBytes ($p+'M_BGXR27_R33_SOURCE_ONLY.lua');"
        "if($a.Length -ne "+str(len(g))+" -or (HashBytes $a) -cne '"+gh+
        "' -or $b.Length -ne 49438 -or (HashBytes $b) -cne '"+R33_LUA_SHA+
        "'){throw 'R33 PIN STOP'};"
        "ANR $zcd;"
        "$f=jp $zcd ('r33_'+[guid]::NewGuid().ToString('N')+'.py');"
        "$c=jp $zcd ('r33_'+[guid]::NewGuid().ToString('N')+'.lua');"
        "try{[IO.File]::WriteAllBytes($f,$a);[IO.File]::WriteAllBytes($c,$b);"
        "if((HashFile $f)-cne '"+gh+"' -or (HashFile $c)-cne '"+R33_LUA_SHA+
        "'){throw 'R33 STAGE SHA'};"
        "$n=Read-Host 'R33 1=RO 2=install 3=status 4=rollback 5=capture [1]';"
        "if(!$n){$n='1'};if($n -eq '0'){break};"
        "$m=@{'1'='preflight';'2'='install';'3'='status';'4'='rollback';'5'='capture'}[$n];"
        "if(!$m){throw 'R33 BAD CHOICE'};"
        "& py -3 $f --game $gr --candidate $c --mode $m;"
        "if($LASTEXITCODE){throw 'R33 STOP'}}finally{"
        "Remove-Item -LiteralPath $f,$c -Force -ErrorAction SilentlyContinue};break}"
    )
    if after.count("'171' {")!=1:
        raise Hold("EXISTING_R31_MENU171_DRIFT")
    old_line = next((line for line in after.splitlines() if line.startswith("'171' {")),None)
    if not old_line or after.count(old_line+"\n")!=1:
        raise Hold("R31_MENU171_LINE_NOT_EXACT")
    after=after.replace(old_line+"\n",old_line+"\n"+handler+"\n",1)
    result=(before+marker+after).encode("utf-8")
    if dispatches(result.decode())!=[str(i) for i in range(1,173)]:
        raise Hold("DISPATCH_172_SEQUENCE_FAILED")
    if not 50000<len(result)<=MAX:
        raise Hold("EIGHTY_KB_BOOTSTRAP_CAP:" + str(len(result)))
    # Last 171 cases are intentionally unchanged, so no old action can drift.
    old_lines=re.findall(r"(?m)^'[1-9][0-9]*' \{[^\n]+\}$",old)
    new_lines=re.findall(r"(?m)^'[1-9][0-9]*' \{[^\n]+\}$",result.decode())
    if new_lines[:171]!=old_lines:
        raise Hold("OLDER_MENU_DISPATCH_CHANGED")
    return result


def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    script=build()
    if a.output:
        if a.output.name!="BGXAI_SYNC_R33_MENU172_SOURCE_ONLY.ps1" or "override" in [v.lower() for v in a.output.parts]:
            raise Hold("SOURCE_ONLY_OUTPUT_PATH_INVALID")
        a.output.write_bytes(script)
    g,b=source_bytes()
    print(json.dumps({"status":"R33_UPDATER_CANDIDATE_SOURCE_ONLY_UNPINNED",
       "bytes":len(script),"sha256":digest(script),"guardBytes":len(g),
       "guardSha256":digest(g),"luaSha256":digest(b),"preservedExistingDispatches":171,
       "gameModified":False},sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
