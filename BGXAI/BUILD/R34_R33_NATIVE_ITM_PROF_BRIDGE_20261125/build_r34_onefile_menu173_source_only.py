"""Deterministically construct R34 menu173 from immutable R33 menu172 baseline.

SOURCE ONLY: no Windows game change, one original CMD unchanged. Existing
dispatch handlers 1..172 remain byte identical; new source is SHA-pinned.
"""
from __future__ import annotations
from pathlib import Path
import hashlib
import json
import re
import sys

HERE=Path(__file__).resolve().parent
BASE=HERE.parent/"R33_R31_REUSE_PROF_SNAPSHOT_RO_20261125"/"BGXAI_SYNC_R33_MENU172_SOURCE_ONLY.ps1"
STAGE=HERE/"BGXAI_SYNC_R34_MENU173_SOURCE_ONLY.ps1"
R34=HERE/"BGXAI_R34_NATIVE_PROF_BRIDGE_RO.py"
R3=HERE.parents[1]/"patchsets"/"ranged_fighter_guarded_20261119"/"BGXAI_WEAPON_NATIVE_ITM_R3_RO.py"
R33_BASE_SHA="7e3c3cc69ce865ff197a5238564757a2c01df71950f56018590f5fa2c38b2417"
R34_SOURCE_SHA="66cc118840418691e49a8b16fe190c3facab6dccc6f89bcecfe07686d7225208"
R3_SOURCE_SHA="ed87a7a6618826c6d3901d2579a39bf280fcaeb09cd18b7b6ee159b9ebfcc74a"
R34_STAGE_SHA="68dadff31059cec588cb1e85e0b53f96493c1f4f87661261d9c920d2a0e324a8"
HANDLER = "'173' {$p='BGXAI/BUILD/R34_R33_NATIVE_ITM_PROF_BRIDGE_20261125/BGXAI_R34_NATIVE_PROF_BRIDGE_RO.py';$q='BGXAI/patchsets/ranged_fighter_guarded_20261119/BGXAI_WEAPON_NATIVE_ITM_R3_RO.py';$a=Get-PinnedBytes $p;$b=Get-PinnedBytes $q;if((HashBytes $a)-cne '66cc118840418691e49a8b16fe190c3facab6dccc6f89bcecfe07686d7225208' -or (HashBytes $b)-cne 'ed87a7a6618826c6d3901d2579a39bf280fcaeb09cd18b7b6ee159b9ebfcc74a'){throw 'R34 SOURCE PIN STOP'};ANR $zcd;$f=jp $zcd ('r34_'+[guid]::NewGuid().ToString('N')+'.py');$g=jp $zcd ('r3_'+[guid]::NewGuid().ToString('N')+'.py');try{[IO.File]::WriteAllBytes($f,$a);[IO.File]::WriteAllBytes($g,$b);$d=jp $env:USERPROFILE 'Documents\\BGXAI_LIVE_REPORTS';ANR $d;$o=jp $d ('BGXAI_R34_NATIVE_PROF_'+(Get-Date -Format 'yyyyMMddTHHmmssfff')+'.json');& py -3 $f --game $gr --reports-dir $d --r3-source $g | Out-File -LiteralPath $o -Encoding utf8;$r=$LASTEXITCODE;Get-Content -LiteralPath $o;wh ('REPORT_FILE='+$o);if($r){throw 'R34 READONLY STOP'}}finally{Remove-Item -LiteralPath $f,$g -Force -ErrorAction SilentlyContinue};break}"

def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def dispatches(src: str) -> list[str]:
    return re.findall(r"(?m)^'[0-9]+' \{[^\n]+\}$",src)

def build() -> bytes:
    prev=BASE.read_bytes()
    assert len(prev)==79920 and sha(prev)==R33_BASE_SHA, "R33 source baseline changed"
    assert len(R3.read_bytes())==18641 and sha(R3.read_bytes())==R3_SOURCE_SHA
    assert sha(R34.read_bytes())==R34_SOURCE_SHA, "R34 source changed"
    s=prev.decode("ascii")
    marker="switch($choice){"
    assert s.count(marker)==1
    pre,post=s.split(marker,1)
    older=dispatches(s)
    assert len(older)==172
    for old,new in [
        ("Write-Host ","wh "),
        ("HashFile ","hf "),
        ("HashBytes ","hb "),
        ("Get-Content ","gc "),
        ("Read-Host ","rh "),
        ("-LiteralPath ","-Lit "),
        ("-ErrorAction ","-Ea "),
        ("-PathType ","-PathT "),
    ]:
        pre=pre.replace(old,new)
    # Fix self-referential alias accidentally introduced when compressing
    # occurrences of Write-Host into wh. Do not globally rewrite alias targets.
    self_alias="Set-Alias wh wh -Scope Script\n"
    assert pre.count(self_alias)==1, "WH_ALIAS_SOURCE_ANCHOR_DRIFT"
    pre=pre.replace(self_alias,"Set-Alias wh Write-Host -Scope Script\n",1)
    assert "Set-Alias wh wh " not in pre
    anchor="Set-Alias tp Test-Path -Scope Script\n"
    assert pre.count(anchor)==1
    pre=pre.replace(anchor,anchor+
        "Set-Alias hf HashFile -Scope Script\n"+
        "Set-Alias hb HashBytes -Scope Script\n"+
        "Set-Alias rh Read-Host -Scope Script\n",1)
    # 'gc' is a read-only BUILT-IN Windows PowerShell alias. Do NOT set it.
    assert "Set-Alias gc " not in pre
    old="|BUILD/R33_R31_REUSE_PROF_SNAPSHOT_RO_20261125|BUILD/R27_SINGLE_CALLBACK_SELECTED_RO_20261123)"
    new="|BUILD/R33_R31_REUSE_PROF_SNAPSHOT_RO_20261125|BUILD/R34_R33_NATIVE_ITM_PROF_BRIDGE_20261125|BUILD/R27_SINGLE_CALLBACK_SELECTED_RO_20261123)"
    assert pre.count(old)==1
    pre=pre.replace(old,new,1)
    banner=" | 172 R33\n0 Exit"
    assert pre.count(banner)==1
    pre=pre.replace(banner," | 172 R33 | 173 R34 RO\n0 Exit",1)
    target=next((line for line in post.splitlines()
                 if line.startswith("'172' {")),None)
    assert target and post.count(target+"\n")==1
    post=post.replace(target+"\n",target+"\n"+HANDLER+"\n",1)
    out=(pre+marker+post).encode("ascii")
    assert len(out)==79775, len(out)
    assert sha(out)==R34_STAGE_SHA
    assert dispatches(out.decode())[:172]==older
    assert len(dispatches(out.decode()))==173
    assert out==STAGE.read_bytes(), "R34 staged bytes mismatch"
    return out

if __name__=="__main__":
    result=build()
    print(json.dumps({"status":"R34_SOURCE_ONLY_REPRODUCIBLE",
        "scriptBytes":len(result),"sha256":sha(result),
        "unchangedPriorDispatches":172,"gameModified":False}))
