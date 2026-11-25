"""R32: source-only, READ ONLY audit of installed EET APR resource tables.

Reads only two explicit override/ files. If either table resides in BIFF/KEY
rather than override, STOP (no guessing or extraction). Never assumes that
a row lookup proves the character's kit, active dual class, weapon mapping,
equipment bonuses, buffs, or effective alternate-slot APR.

WSPATCK values encode ADDITIONAL attacks, not final attacks:
0 -> +0, -1 -> +0.5, 1 -> +1, -2 -> +1.5, etc.
CLSWPBON.GETS_PROF_APR controls class eligibility in the installed table.
This is a table-data interpretation only, NEVER weapon switch authorization.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import sys

MAX_FILE_BYTES = 1_000_000
MAX_LINES = 250
MAX_COLUMNS = 65
MAX_ROWS = 120
NAME = re.compile(r"^[A-Z0-9_]{1,80}$")
LEVEL = re.compile(r"^(?:LEVEL)?([1-9][0-9]*)$")
SIGNED_INT = re.compile(r"^-?[0-9]+$")
TWO_DA = re.compile(r"^2DA[ \t]+V1\.0$", re.I)
R32_SCHEMA = "BGXAI_R32_INSTALLED_APR_TABLES_SOURCE_ONLY_V1"


class Hold(ValueError):
    pass


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class Table:
    default: str
    columns: tuple[str, ...]
    rows: dict[str, tuple[str, ...]]


def parse_2da(raw: bytes) -> Table:
    """Strict 2DA grammar: reject ambiguous/default-filled/misaligned entries."""
    try:
        data = raw.decode("ascii-sig") if False else raw.decode("ascii")
    except UnicodeError as exc:
        raise Hold("NOT_ASCII_2DA") from exc
    if data.startswith("\ufeff"):
        data = data[1:]
    lines = [line.split("//", 1)[0].strip()
             for line in data.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    lines = [line for line in lines if line]
    if len(lines) < 4 or len(lines) > MAX_LINES:
        raise Hold("2DA_LINE_COUNT")
    if not TWO_DA.fullmatch(lines[0]):
        raise Hold("2DA_VERSION_INVALID")
    default_words = lines[1].split()
    if len(default_words) != 1:
        raise Hold("2DA_DEFAULT_INVALID")
    columns = tuple(x.upper() for x in lines[2].split())
    if not columns or len(columns) > MAX_COLUMNS or len(set(columns)) != len(columns):
        raise Hold("2DA_COLUMNS_INVALID")
    if any(not NAME.fullmatch(col) for col in columns):
        raise Hold("2DA_COLUMN_NAME_INVALID")
    rows: dict[str, tuple[str, ...]] = {}
    if len(lines) - 3 > MAX_ROWS:
        raise Hold("2DA_ROWS_TOO_MANY")
    for line in lines[3:]:
        parts = line.split()
        if len(parts) != len(columns) + 1:
            raise Hold("2DA_ROW_WIDTH_MISMATCH")
        key = parts[0].upper()
        if not NAME.fullmatch(key) or key in rows:
            raise Hold("2DA_ROW_KEY_INVALID_OR_DUPLICATE")
        rows[key] = tuple(parts[1:])
    if not rows:
        raise Hold("2DA_NO_ROWS")
    return Table(default_words[0], columns, rows)


def wspatck_levels(table: Table) -> tuple[int, ...]:
    levels = []
    for col in table.columns:
        match = LEVEL.fullmatch(col)
        if not match:
            raise Hold("WSPATCK_LEVEL_HEADER_INVALID")
        levels.append(int(match.group(1)))
    if not 1 <= len(levels) <= 50 or levels != list(range(1, len(levels) + 1)):
        raise Hold("WSPATCK_LEVELS_NONCONTIGUOUS")
    if set(table.rows) != {str(i) for i in range(6)}:
        raise Hold("WSPATCK_PROFICIENCY_ROWS_UNKNOWN")
    for values in table.rows.values():
        if any(not SIGNED_INT.fullmatch(v) or not -10 <= int(v) <= 10 for v in values):
            raise Hold("WSPATCK_NONINTEGER_OR_OUT_OF_RANGE")
    return tuple(levels)


def clswpbon_rows(table: Table) -> None:
    needed = {"GETS_PROF_APR", "UNARMED_DIVISOR", "ZERO_SKILL_THAC0"}
    if not needed.issubset(table.columns):
        raise Hold("CLSWPBON_REQUIRED_COLUMNS_MISSING")
    idx = table.columns.index("GETS_PROF_APR")
    for row, values in table.rows.items():
        if not NAME.fullmatch(row) or not SIGNED_INT.fullmatch(values[idx]):
            raise Hold("CLSWPBON_CLASS_OR_APR_FLAG_INVALID")
        if values[idx] not in ("0", "1"):
            raise Hold("CLSWPBON_PROF_APR_FLAG_NOT_BOOLEAN")
        for key in needed - {"GETS_PROF_APR"}:
            v = values[table.columns.index(key)]
            if not SIGNED_INT.fullmatch(v) or not 0 <= int(v) <= 100:
                raise Hold("CLSWPBON_NUMERIC_COLUMN_INVALID")


def decode_extra_apr(raw: int) -> float:
    """WSPATCK uses 1 -> +1, -1 -> +0.5, -2 -> +1.5."""
    if type(raw) is not int or not -10 <= raw <= 10:
        raise Hold("WSPATCK_ENCODING_INVALID")
    return float(raw if raw >= 0 else -raw - 0.5)


def read_override(root: Path, name: str) -> tuple[Table, str]:
    if root.is_symlink() or not root.is_dir():
        raise Hold("GAME_ROOT_NOT_REGULAR")
    folder = root / "override"
    if folder.is_symlink() or not folder.is_dir():
        raise Hold("OVERRIDE_NOT_REGULAR")
    # Explicit override files only: never claim a KEY/BIF resource was resolved.
    path = folder / name
    if path.is_symlink() or not path.is_file():
        raise Hold(name + "_NOT_IN_OVERRIDE_NO_BIF_FALLBACK")
    before = path.stat()
    if not 1 <= before.st_size <= MAX_FILE_BYTES:
        raise Hold(name + "_BAD_SIZE")
    raw = path.read_bytes()
    after = path.stat()
    if (len(raw) != before.st_size or before.st_size != after.st_size
            or before.st_mtime_ns != after.st_mtime_ns):
        raise Hold(name + "_CHANGED_DURING_READ")
    return parse_2da(raw), sha256(raw)


def audit(root: Path, class_row: str, rank: int, level: int) -> dict:
    """Resource table LOOKUP, not a binding to a verified live actor."""
    core = {"schema": R32_SCHEMA, "readOnly": True, "gameModified": False,
            "ordersSent": 0, "dispatchAuthorized": False,
            "weaponSwitchAuthorized": False, "sourceOnly": True,
            "liveActorIdentityVerified": False,
            "activeDualMultiClassVerified": False,
            "proficiencyWeaponGroupVerified": False,
            "selectedEngineAprVerified": False,
            "alternateEffectiveAprVerified": False,
            "allTemporaryEffectsVerified": False,
            "resolvedBifResourcesVerified": False,
            "gameplayWeaponPriorityVerified": False}
    if (type(class_row) is not str or not NAME.fullmatch(class_row.upper())
            or type(rank) is not int or not 0 <= rank <= 5
            or type(level) is not int or not 1 <= level <= 50):
        return {**core, "status": "HOLD", "reason": "QUERY_CLASS_PIPS_LEVEL_INVALID"}
    try:
        wsp, wsp_hash = read_override(root, "WSPATCK.2DA")
        cls, cls_hash = read_override(root, "CLSWPBON.2DA")
        levels = wspatck_levels(wsp)
        clswpbon_rows(cls)
        row = class_row.upper()
        if level not in levels:
            raise Hold("LEVEL_NOT_EXPLICITLY_IN_WSPATCK")
        if row not in cls.rows:
            raise Hold("CLASS_NOT_EXPLICITLY_IN_CLSWPBON")
        class_flag = int(cls.rows[row][cls.columns.index("GETS_PROF_APR")])
        value = int(wsp.rows[str(rank)][levels.index(level)])
        extra = decode_extra_apr(value)
        return {**core, "status": "SOURCE_TABLE_LOOKUP_PASS_NO_ENGINE_APR",
                "wspatckSha256": wsp_hash, "clswpbonSha256": cls_hash,
                "inputSource": "TWO_EXPLICIT_INSTALLED_OVERRIDE_FILES_ONLY",
                "wspatckRows": 6, "wspatckLevels": len(levels),
                "clswpbonClassCount": len(cls.rows),
                "requestedClassRowUnverified": row,
                "requestedProficiencyRankUnverified": rank,
                "requestedClassLevelUnverified": level,
                "getsProfAprTableFlag": bool(class_flag),
                "wspatckRawValue": value, "wspatckDecodedBonusAPR": extra,
                "tableBonusAPRIfActorClassVerified": extra if class_flag else 0.0,
                "bonusIsAdditiveNotFinalAPR": True,
                "finalApr": None}
    except (Hold, OSError, UnicodeError) as ex:
        return {**core, "status": "HOLD",
                "reason": str(ex) if isinstance(ex, Hold) else type(ex).__name__}


def main() -> int:
    arg = argparse.ArgumentParser()
    arg.add_argument("--game", required=True, type=Path)
    arg.add_argument("--class-row", required=True)
    arg.add_argument("--pips", required=True, type=int)
    arg.add_argument("--level", required=True, type=int)
    a = arg.parse_args()
    result = audit(a.game, a.class_row, a.pips, a.level)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if result["status"].startswith("SOURCE_TABLE_LOOKUP_PASS") else 2


if __name__ == "__main__":
    sys.exit(main())
