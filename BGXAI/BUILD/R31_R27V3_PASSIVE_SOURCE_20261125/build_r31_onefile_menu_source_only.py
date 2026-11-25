"""R31 one-CMD menu171 candidate composer; NO game writes or updater mutation.

Preserves every switch dispatch 1..170, PowerShell 5.1 parser contract, and the
immutable existing CMD size cap (80,000 bytes). Prints audit only.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
import re
import sys
import json

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BACKEND = REPO / "BGXAI" / "BGXAI_SYNC.ps1"
GUARD = HERE / "R31_GUARDED_SOURCE_ONLY.py"
LUA = HERE / "M_BGXR27_R31_SOURCE_ONLY.lua"
ORIGINAL_SHA = "10c9a7651096a45c3a5a694acf9800e9f651843321716438a4e37b6015245e42"
MAX_BYTES = 80000
LUA_SHA = "5a1f6b32db920a005161734605c8b3273614a1318d8b1b57dac79ed022a00f38"
PREFIX = "BGXAI/BUILD/R31_R27V3_PASSIVE_SOURCE_20261125/"
ALLOW_OLD = "BUILD/R30_QUEUE_DEPLOY_PREFLIGHT_RO_20261125|BUILD/R27_SINGLE_CALLBACK_SELECTED_RO_20261123"
ALLOW_NEW = "BUILD/R30_QUEUE_DEPLOY_PREFLIGHT_RO_20261125|BUILD/R31_R27V3_PASSIVE_SOURCE_20261125|BUILD/R27_SINGLE_CALLBACK_SELECTED_RO_20261123"


class Hold(ValueError):
    pass


def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def dispatches(src: str) -> list[str]:
    return re.findall(r"(?m)^'([1-9][0-9]*)' \{[^\n]+\}$", src)


def produce(base: bytes, guard: bytes, candidate: bytes) -> bytes:
    if digest(candidate) != LUA_SHA or len(candidate) != 47550:
        raise Hold("R31_LUA_SOURCE_PIN_DRIFT")
    if not guard or len(guard) > 500000:
        raise Hold("R31_GUARD_MISSING_OR_OVERSIZE")
    raw = base.decode("utf-8")
    if b"'171' {" in base:
        if "Set-Alias wh Write-Host -Scope Script" not in raw or digest(guard) not in raw or LUA_SHA not in raw:
            raise Hold("EXISTING_R31_MENU_DRIFT")
        if len(base) > MAX_BYTES:
            raise Hold("EXISTING_R31_BOOTSTRAP_CAP_EXCEEDED")
        return base
    if digest(base) != ORIGINAL_SHA or len(base) != 79979:
        raise Hold("BASELINE_BACKEND_SHA_DRIFT")
    if raw.count("param([string]$GameRoot='.')\n") != 1:
        raise Hold("PS5_1_PARAM_HEADER_DRIFT")
    if raw.count(ALLOW_OLD) != 1 or raw.count("169 R29 | 170 R30 RO") != 1 or raw.count("'170' {RunR30ReadOnly;break}") != 1:
        raise Hold("R30_MENU_OR_ALLOWLIST_DRIFT")
    old_dispatch = dispatches(raw)
    if len(old_dispatch) != 170 or old_dispatch != [str(i) for i in range(1,171)]:
        raise Hold("EXISTING_DISPATCH_COUNT_OR_ORDER_DRIFT")
    # PowerShell Write-Host alias resolves to the SAME cmdlet; no handlers are
    # deleted or changed. Insert directly after param, before any runtime output.
    compact,n = re.subn(r"(?m)^Write-Host ", "wh ", raw)
    if n < 160:
        raise Hold("SAFE_OUTPUT_ALIAS_COMPACTION_UNEXPECTED")
    compact=compact.replace("param([string]$GameRoot='.')\n",
                            "param([string]$GameRoot='.')\nSet-Alias wh Write-Host -Scope Script\n", 1)
    compact=compact.replace(ALLOW_OLD,ALLOW_NEW,1)
    compact=compact.replace("169 R29 | 170 R30 RO","169 R29 | 170 R30 RO | 171 R31 V3",1)
    guard_hash=digest(guard)
    handler=(
        "'171' {$p='"+PREFIX+"';"
        "$a=Get-PinnedBytes ($p+'R31_GUARDED_SOURCE_ONLY.py');"
        "$b=Get-PinnedBytes ($p+'M_BGXR27_R31_SOURCE_ONLY.lua');"
        "if($a.Length -ne "+str(len(guard))+" -or (HashBytes $a) -cne '"+guard_hash+
        "' -or $b.Length -ne 47550 -or (HashBytes $b) -cne '"+LUA_SHA+
        "'){throw 'R31 PIN STOP'};"
        "ANR $zcd;"
        "$f=Join-Path $zcd ('r31_'+[guid]::NewGuid().ToString('N')+'.py');"
        "$c=Join-Path $zcd ('r31_'+[guid]::NewGuid().ToString('N')+'.lua');"
        "try{[IO.File]::WriteAllBytes($f,$a);[IO.File]::WriteAllBytes($c,$b);"
        "if((HashFile $f)-cne '"+guard_hash+"' -or (HashFile $c)-cne '"+LUA_SHA+
        "'){throw 'R31 STAGE SHA'};"
        "$n=Read-Host 'R31 1=RO 2=install 3=status 4=rollback 5=capture [1]';"
        "if(!$n){$n='1'};if($n -eq '0'){break};"
        "$m=@{'1'='preflight';'2'='install';'3'='status';'4'='rollback';'5'='capture'}[$n];"
        "if(!$m){throw 'R31 BAD CHOICE'};"
        "& py -3 $f --game $gr --candidate $c --mode $m;"
        "if($LASTEXITCODE){throw 'R31 STOP'}}finally{"
        "Remove-Item -LiteralPath $f,$c -Force -ErrorAction SilentlyContinue};break}"
    )
    compact=compact.replace("'170' {RunR30ReadOnly;break}",
                            "'170' {RunR30ReadOnly;break}\n"+handler,1)
    if dispatches(compact) != old_dispatch + ["171"]:
        raise Hold("DISPATCH_REGRESSION")
    original_lines = re.findall(r"(?m)^'[1-9][0-9]*' \\{[^\\n]+\\}$", raw)
    updated_lines = re.findall(r"(?m)^'[1-9][0-9]*' \\{[^\\n]+\\}$", compact)
    if len(original_lines) != 170 or updated_lines[:170] != original_lines:
        raise Hold("DISPATCH_1_TO_170_BYTE_FOR_BYTE_CHANGED")
    new=compact.encode("utf-8")
    if len(new)>MAX_BYTES:
        raise Hold("BOOTSTRAP_80K_CAP_EXCEEDED:"+str(len(new)))
    if "Set-Alias wh Write-Host -Scope Script" not in compact or "'170' {RunR30ReadOnly;break}" not in compact:
        raise Hold("R30_OR_ALIAS_NOT_PRESERVED")
    return new


def build() -> bytes:
    return produce(BACKEND.read_bytes(), GUARD.read_bytes(), LUA.read_bytes())


if __name__ == "__main__":
    result=build()
    print(json.dumps({"status":"R31_ONEFILE_SOURCE_READY_NOT_PINNED_NOT_DEPLOYED",
                      "bytes":len(result),"sha256":digest(result),
                      "guardBytes":len(GUARD.read_bytes()),
                      "guardSha256":digest(GUARD.read_bytes()),
                      "luaSha256":LUA_SHA,"preservedChoices":170,
                      "gameModified":False}, indent=2))
