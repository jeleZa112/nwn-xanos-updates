"""Source-only 064 Lua delta for exact installed BGXAI 061 (no game writes).

Patch ONLY the existing BGX52Bridge.prepare single-guardian selection.
Never adds a second election / new listener / engine combat commands.
Default source pin is verified user-installed 061 Lua SHA256.
"""
from __future__ import annotations
from hashlib import sha256

PIN_061='fd39d23dc722b549c2af1eaf065541b2ed358a9714f2636b8cab4e45fe7dcec5'
# SHA of the byte-exact candidate independently built from GitHub 056+061.
PIN_064='bfee5278b5b69b1fb4a02e3fea321082b0238407789df83ec6bd2f78d7e19f4b'

REPLACEMENTS = (
    ('''P.version = "0.3.22-056-ACTIVE-GUARD-OPTIN"''',
     '''P.version = "0.3.29-064-061-SAME-AREA-GUARD-SOURCE"'''),
    ('''    if type(vx)~="number" or type(vy)~="number" then return reject("unknown_position") end
    local options={}''',
     '''    if type(vx)~="number" or type(vy)~="number" then return reject("unknown_position") end
    -- 064: never select a defender in a different loaded ARE.
    local victimArea=safe(function()return victim.m_pArea end)
    if not victimArea or type(EEex_UDEqual)~="function" then return reject("area_comparison_unavailable") end
    local options={}'''),
    ('''             local yy=safe(function()return obj.m_pos.y end)
             if guard==1 and modal==0 and type(xx)=="number" and type(yy)=="number" then''',
     '''             local yy=safe(function()return obj.m_pos.y end)
             local guardArea=safe(function()return obj.m_pArea end)
             local sameArea=guardArea and safe(function()return EEex_UDEqual(guardArea,victimArea)end)==true
             if guard==1 and modal==0 and sameArea and type(xx)=="number" and type(yy)=="number" then'''),
    ('''if #options==0 then return reject("no_guardian_with_f_mode") end''',
     '''if #options==0 then return reject("no_guardian_with_f_mode_in_same_area") end'''),
)

def digest(raw:bytes)->str:
    return sha256(raw).hexdigest()

def build_candidate(raw:bytes, *, baseline_sha:str=PIN_061, candidate_sha:str|None=PIN_064):
    """Pure deterministic patch; expected_sha override reserved for synthetic unit fixtures.

    The only production call is with both default pins. Fails closed on drift.
    """
    if not isinstance(raw,bytes):
        raise TypeError('SOURCE_BYTES_REQUIRED')
    if digest(raw)!=baseline_sha:
        raise ValueError('SOURCE_061_SHA256_MISMATCH_STOP')
    try:
        original=raw.decode('utf-8')
    except UnicodeError as exc:
        raise ValueError('SOURCE_061_NOT_UTF8') from exc
    if original.count('function B.prepare(advisory)')!=1:
        raise ValueError('BRIDGE_ENTRY_DRIFT_STOP')
    new=original
    for idx,(a,b) in enumerate(REPLACEMENTS,1):
        if new.count(a)!=1 or b in new:
            raise ValueError(f'PATCH_ANCHOR_{idx}_DRIFT_STOP')
        new=new.replace(a,b,1)
    candidate=new.encode('utf-8')
    if candidate_sha is not None and digest(candidate)!=candidate_sha:
        raise ValueError('CANDIDATE_064_SHA256_MISMATCH_STOP')
    if not candidate.count(b'local best=options[1]')==1:
        raise ValueError('DUPLICATE_OR_MISSING_GUARDIAN_SELECTOR')
    if candidate.count(b'function B.prepare(advisory)')!=1:
        raise ValueError('DUPLICATE_BRIDGE')
    if not (candidate.count(b'BGX52_REQ_SLOT')==raw.count(b'BGX52_REQ_SLOT')
            and candidate.count(b'set("BGX52_REQ_SLOT",slot)')==1):
        raise ValueError('BRIDGE_REQUEST_WRITE_CHANGED_STOP')
    # Exact reversibility proves only the 4 intentional replacements happened.
    restored=new
    for a,b in reversed(REPLACEMENTS):
        if restored.count(b)!=1: raise ValueError('REVERSE_ANCHOR_DRIFT')
        restored=restored.replace(b,a,1)
    if restored!=original:
        raise ValueError('UNEXPECTED_SOURCE_CHANGE_STOP')
    return candidate, {'source_sha256':digest(raw),'candidate_sha256':digest(candidate),
                       'changed_anchors':4, 'other_code_unchanged':True,
                       'single_existing_selector':True,'game_written':False}