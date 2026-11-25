"""R33 source-only extension of *existing* R31 R4 prof data. No game install.

R31 already reads m_nLevel1/2/3, m_nKit and WPROF-derived fields 89..134
twice per single EEex callback. R33 emits these existing raw values with
clear non-authenticated provenance; no secondary observer and no stat rewrite.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
R31 = HERE.parent / "R31_R27V3_PASSIVE_SOURCE_20261125" / "M_BGXR27_R31_SOURCE_ONLY.lua"
R31_SHA256 = "5a1f6b32db920a005161734605c8b3273614a1318d8b1b57dac79ed022a00f38"
SCHEMA = "BGXAI_R27_SINGLE_CALLBACK_SELECTED_RO_V1"
NAME = "M_BGXR27_R33_SOURCE_ONLY.lua"


def exact(source: str, old: str, new: str) -> str:
    if source.count(old) != 1:
        raise ValueError("R31_ANCHOR_NOT_EXACT_OR_ALREADY_PATCHED")
    return source.replace(old, new, 1)


def generate(source: str) -> str:
    s = exact(source,
""" local ability=scalar(eq,'m_selectedWeaponAbility',0,65535)
 return {actor=actor,action=aid,weapon=weapon,ability=ability}""",
""" local ability=scalar(eq,'m_selectedWeaponAbility',0,65535)
 -- An AI object class is only a RAW candidate; it is not an authenticated
 -- active dual/multiclass row or KITLIST / CLASS.IDS mapping.
 local okClass,typeAI=pcall(function()return sprite.m_typeAI end)
 local aiClass=okClass and scalar(typeAI,'m_Class',0,255) or nil
 return {actor=actor,action=aid,weapon=weapon,ability=ability,
  aiClass=aiClass}""")
    s = exact(s,
"""   a.weapon==b.weapon and a.ability==b.ability
end""",
"""   a.weapon==b.weapon and a.ability==b.ability and
   a.aiClass==b.aiClass
end""")
    s = exact(s,
""" -- Observe but never turn a selected-only APR into alternative-slot evidence.
 -- The R2 slot data are still only raw candidates, not validated items.
 return {schema=R27.schema""",
"""  -- Reuse the EXACT existing R4 double-read for 46 WPROF raw stat slots.
  -- No additional getActiveStats call or listener. False -> JSON null.
  local profRaw={}
  for id=89,134 do
   local field=R4_CORE.proficiencyFieldById[id]
   local v=field and f[field] or nil
   profRaw[#profRaw+1]=int(v,-2147483648,2147483647) and v or false
  end
  -- These are raw values, not actual pips, weapon-to-group mapping or
  -- live-class rights. They must NEVER unlock the existing V5 dispatch.
  -- Observe but never turn a selected-only APR into alternative-slot evidence.
  -- The R2 slot data are still only raw candidates, not validated items.
  return {schema=R27.schema""")
    s = exact(s,
"""   m_nHitBonus=f.m_nHitBonus},
  selectedDerivedStatsDoubleReadConsistent=true,""",
"""   m_nHitBonus=f.m_nHitBonus,m_nLevel1=f.m_nLevel1,
   m_nLevel2=f.m_nLevel2,m_nLevel3=f.m_nLevel3,m_nKit=f.m_nKit},
  rawProficiencyStat89to134=profRaw,aiClassRawCandidate=b.aiClass,
  selectedDerivedStatsDoubleReadConsistent=true,""")
    s = exact(s,
"""function R27.toConsoleJson(sample)""",
"""-- JSON payload emits existing R4 evidence; never infer actor proficiency rank.
local function jrawprof(values)
 if type(values)~='table' or #values~=46 then return 'null' end
 local t={}
 for i=1,46 do t[i]=jnum(values[i],-2147483648,2147483647) end
 return '['..table.concat(t,',')..']'
end
local function jlevels(s)
 if type(s)~='table' then return 'null' end
 return '{"level1":'..jnum(s.m_nLevel1,0,50)..
  ',"level2":'..jnum(s.m_nLevel2,0,50)..
  ',"level3":'..jnum(s.m_nLevel3,0,50)..
  ',"kitRaw":'..jnum(s.m_nKit,0,4294967295)..'}'
end
function R27.toConsoleJson(sample)""")
    s = exact(s,
"""  ',"selectedStatsRaw":'..jstats(sample.sampledStatsRaw)..
  ',"sameLuaListenerInvocation":'""",
"""  ',"selectedStatsRaw":'..jstats(sample.sampledStatsRaw)..
  ',"levelsAndKitRaw":'..jlevels(sample.sampledStatsRaw)..
  ',"aiObjectClassRawCandidate":'..jnum(sample.aiClassRawCandidate,0,255)..
  ',"proficiencyStat89to134Raw":'..jrawprof(sample.rawProficiencyStat89to134)..
  ',"classRowVerified":false,"weaponToProficiencyVerified":false,'..
  '"activeDualMultiClassVerified":false,"actorPipsVerified":false'..
  ',"sameLuaListenerInvocation":'""")
    s = exact(s, "BGXAI_R31_R27V3_PASSIVE_CANDIDATE",
                 "BGXAI_R33_R27V3_PASSIVE_PROF_CANDIDATE")
    s = exact(s, '"observerCandidate":"R31_R27V3_PASSIVE"',
                 '"observerCandidate":"R33_R27V3_PASSIVE_PROF_RO"')
    s = exact(s, "-- R31 SOURCE ONLY: derived from exact V3, not installed.",
                 "-- R33 SOURCE ONLY, reused verified installed R31 R4 fields; not installed.")
    return s


def build() -> tuple[str, str]:
    data = R31.read_bytes()
    if len(data) != 47550 or hashlib.sha256(data).hexdigest() != R31_SHA256:
        raise ValueError("R31_SOURCE_SHA_OR_BYTES_MISMATCH_STOP")
    s = data.decode("utf-8")
    out = generate(s)
    if s.count("EEex_Action_AddSpriteStartedActionListener") != out.count("EEex_Action_AddSpriteStartedActionListener"):
        raise ValueError("SECOND_LISTENER_FORBIDDEN")
    for forbidden in ("SelectWeaponAbility(", "ClearActions(", "AttackOneRound(", "SetGlobal("):
        if s.count(forbidden) != out.count(forbidden):
            raise ValueError("ENGINE_COMMAND_ADDED_STOP")
    if SCHEMA not in out or "dispatchAuthorized=false" not in out:
        raise ValueError("SAFETY_CONTRACT_MISSING")
    return out, hashlib.sha256(out.encode("utf-8")).hexdigest()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, help="For source-only temp CI output; never game root")
    a = p.parse_args()
    out, digest = build()
    if a.output:
        # No filesystem access beyond the explicitly chosen temp output.
        # Deliberately disallow writing into any game 'override' or 'EEex' tree.
        if a.output.name != NAME or any(x.lower() in ("override", "eeex") for x in a.output.parts):
            raise ValueError("SOURCE_ONLY_OUTPUT_PATH_INVALID")
        a.output.write_text(out, encoding="utf-8", newline="\n")
    print("R33_SOURCE_ONLY_PASS sourceBytes=", len(out.encode()), "sha256=", digest,
          "installed=false ordersSent=0 actorPipsVerified=false", sep="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
