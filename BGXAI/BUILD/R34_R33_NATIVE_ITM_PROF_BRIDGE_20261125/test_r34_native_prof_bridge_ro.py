"""R34 static and fail-closed Python tests using only SYNTHETIC actor/resource data."""
import copy
import hashlib
import importlib.util
import json
import pathlib
import struct
import unittest

HERE=pathlib.Path(__file__).resolve().parent
modspec=importlib.util.spec_from_file_location("r34",HERE/"BGXAI_R34_NATIVE_PROF_BRIDGE_RO.py")
r34=importlib.util.module_from_spec(modspec)
modspec.loader.exec_module(r34)
R3=HERE.parents[1]/"patchsets/ranged_fighter_guarded_20261119/BGXAI_WEAPON_NATIVE_ITM_R3_RO.py"
# parent[0]=BUILD, parent[1]=BGXAI
assert R3.is_file(), str(R3)
r3=r34.load_r3(R3)

def itm(pid,attack,damage=0):
    x=bytearray(170)
    x[:8]=b"ITM V1  "
    x[0x31]=pid
    struct.pack_into("<I",x,0x64,114)
    struct.pack_into("<H",x,0x68,1)
    struct.pack_into("<I",x,0x6a,170)
    p=114
    x[p]=attack
    x[p+0x16]=6
    x[p+0x18]=1
    struct.pack_into("<h",x,p+0x1a,damage)
    return bytes(x)

ITEMS={
 "SW1H04":itm(90,1),
 "BOW05":itm(105,4),
 "STAF01":itm(102,1),
 "AROW01":itm(0,2),
 "SHLD03A":itm(0,0)
}
class FakeSource:
    def __init__(self,records=None):
        self.records=records or ITEMS
        self.calls=[]
    def get(self,ref,typ):
        assert typ==".ITM"
        self.calls.append(ref)
        raw=self.records[ref]
        return raw,{"origin":"CURRENT_GAME_BIFF","sha256":hashlib.sha256(raw).hexdigest()}

def fixture(n=8):
    prof=[0]*46
    prof[90-89]=2
    prof[92-89]=1
    prof[104-89]=1
    base={"schema":"BGXAI_R27_SINGLE_CALLBACK_SELECTED_RO_V1",
          "type":"R27_SINGLE_CALLBACK",
          "status":"CURRENT_SELECTED_SAME_CALLBACK_SOURCE_CANDIDATE",
          "actor":10012,"partyIndex":2,"actionRaw":23,
          "selectedAprKeyRaw":2,
          "quickWeaponsRaw":[{"slot":i,"resrefRaw":ref} for i,ref in
             ((35,"SW1H04"),(36,"BOW05"),(37,None),(38,"STAF01"))],
          "quiversRaw":[{"slot":i,"resrefRaw":ref} for i,ref in
             ((11,None),(12,"AROW01"),(13,None),(14,None))],
          "offhandRaw":[{"slot":9,"resrefRaw":"SHLD03A"}],
          "proficiencyStat89to134Raw":prof,
          "levelsAndKitRaw":{"level1":1,"level2":1,"level3":1,"kitRaw":16384},
          "rawInventoryDoubleReadConsistent":True,
          "selectedDerivedStatsDoubleReadConsistent":True,
          "queueSnapshotStable":True,"actionContextSnapshotStable":True,
          "sameLuaListenerInvocation":True,"ordersSent":0,"localsWritten":0,
          "dispatchAuthorized":False,"weaponSwitchAuthorized":False,"readOnly":True}
    session={"schema":"BGXAI_R27_SINGLE_CALLBACK_SELECTED_RO_V1",
             "type":"SESSION","observerCandidate":"R33_R27V3_PASSIVE_PROF_RO",
             "ordersSent":0,"readOnly":True,"dispatchAuthorized":False,
             "weaponSwitchAuthorized":False}
    rows=[]
    for i in range(n):
        x=copy.deepcopy(base)
        x["seq"]=i+1
        if i==n-3:
            x["actionRaw"]=3
        rows.append(x)
    return session,rows

def raw(session,events):
    return ("\n".join(
      ["INFO: LUA: [BGXR27] "+json.dumps(x,separators=(",",":"))
         for x in [session]+events])+"\n").encode()

class Bridge(unittest.TestCase):
    def setUp(self):
        self.s,self.events=fixture()
        self.source=FakeSource()
    def test_real_native_parser_and_skill_group(self):
        result=r34.join(raw(self.s,self.events),self.source,r3.parse_itm)
        self.assertEqual(result["status"],"CURRENT_NATIVE_ITM_PROF_GROUPS_JOINED_RO_NO_SWITCH")
        self.assertEqual(result["r33EventCount"],8)
        self.assertEqual(result["nativeResourceCount"],5)
        rows={x["resref"]:x for x in result["resourceItems"]}
        self.assertEqual(rows["BOW05"]["proficiencyStatIdRaw"],105)
        self.assertEqual(rows["BOW05"]["proficiencyLowThreeBitsObserved"],0)
        self.assertTrue(rows["BOW05"]["noProficiencyInLiveActor"])
        self.assertEqual(rows["SW1H04"]["proficiencyLowThreeBitsObserved"],2)
        self.assertEqual(rows["STAF01"]["proficiencyLowThreeBitsObserved"],0)
        self.assertEqual(rows["BOW05"]["abilityHeadersRaw"][0]["attackTypeRaw"],4)
        self.assertEqual(len(result["proficiencyMismatches"]),2)  # BOW05 and STAFF
        self.assertEqual(result["observedActionIdsRaw"],[3,23])
        self.assertFalse(result["alternateEffectiveAPRVerified"])
        self.assertFalse(result["weaponSwitchAuthorized"])
        self.assertFalse(result["manualAndEPSOriginVerified"])
    def test_no_user_identifying_actor_or_paths_in_joined_report(self):
        result=r34.join(raw(self.s,self.events),self.source,r3.parse_itm)
        blob=json.dumps(result)
        self.assertNotIn("10012",blob)
        self.assertNotIn("C:\\",blob)
        self.assertNotIn("Drevo",blob)
    def test_unknown_weapon_group_not_treated_as_zero_pips(self):
        self.source=FakeSource({**ITEMS,"BOW05":itm(200,4)})
        result=r34.join(raw(self.s,self.events),self.source,r3.parse_itm)
        row=next(x for x in result["resourceItems"] if x["resref"]=="BOW05")
        self.assertIsNone(row["proficiencyLowThreeBitsObserved"])
        self.assertIsNone(row["noProficiencyInLiveActor"])
        self.assertFalse(any(x["resref"]=="BOW05" for x in result["proficiencyMismatches"]))
    def test_proficiency_high_bits_only_three_low_bits(self):
        for x in self.events:
            x["proficiencyStat89to134Raw"][105-89]=0x202
        result=r34.join(raw(self.s,self.events),self.source,r3.parse_itm)
        row=next(x for x in result["resourceItems"] if x["resref"]=="BOW05")
        self.assertEqual(row["rawStatForProficiency"],0x202)
        self.assertEqual(row["proficiencyLowThreeBitsObserved"],2)
    def test_cross_actor_rejected(self):
        self.events[2]["actor"]=777
        with self.assertRaisesRegex(r34.Hold,"CROSS_ACTOR"):
            r34.read_session(raw(self.s,self.events))
    def test_duplicate_session_rejected(self):
        with self.assertRaisesRegex(r34.Hold,"R33_SESSION_COUNT_NOT_ONE"):
            r34.read_session(raw(self.s,[self.s]+self.events))
    def test_order_violation_rejected(self):
        self.events[3]["ordersSent"]=1
        with self.assertRaisesRegex(r34.Hold,"R33_EVENT_CONTRACT"):
            r34.read_session(raw(self.s,self.events))
    def test_switch_flag_rejected(self):
        self.events[0]["weaponSwitchAuthorized"]=True
        with self.assertRaisesRegex(r34.Hold,"R33_EVENT_CONTRACT"):
            r34.read_session(raw(self.s,self.events))
    def test_queue_snapshot_unstable_rejected(self):
        self.events[5]["queueSnapshotStable"]=False
        with self.assertRaisesRegex(r34.Hold,"R33_SNAPSHOT_UNSTABLE"):
            r34.read_session(raw(self.s,self.events))
    def test_prof_stats_changed_rejected(self):
        self.events[6]["proficiencyStat89to134Raw"][1]=4
        with self.assertRaisesRegex(r34.Hold,"PROFICIENCY_CHANGED"):
            r34.read_session(raw(self.s,self.events))
    def test_inventory_drift_rejected(self):
        self.events[-1]["quickWeaponsRaw"][1]["resrefRaw"]="BOW01"
        with self.assertRaisesRegex(r34.Hold,"EQUIPMENT_CHANGED"):
            r34.read_session(raw(self.s,self.events))
    def test_malformed_slot_rejected(self):
        self.events[1]["quiversRaw"][1]["slot"]=30
        with self.assertRaisesRegex(r34.Hold,"SLOT_INDEX_DRIFT"):
            r34.read_session(raw(self.s,self.events))
    def test_missing_itm_fails_not_fabricated(self):
        self.source=FakeSource({"BOW05":ITEMS["BOW05"]})
        with self.assertRaises(KeyError):
            r34.join(raw(self.s,self.events),self.source,r3.parse_itm)
    def test_invalid_json_rejected(self):
        with self.assertRaisesRegex(r34.Hold,"R33_EVENT_INVALID_JSON"):
            r34.read_session(b"INFO: LUA: [BGXR27] {broken\n")
    def test_no_events_rejected(self):
        with self.assertRaisesRegex(r34.Hold,"R33_NO_SELECTED_EVENTS"):
            r34.read_session(raw(self.s,[]))
    def test_log_never_falsely_confirms_executability(self):
        out=r34.join(raw(self.s,self.events),self.source,r3.parse_itm)
        for key in ("dispatchAuthorized","weaponSwitchAuthorized",
                    "safeDispatchTimeVerified","alternateEffectiveAPRVerified",
                    "actorClassRowVerified","targetProtectionsVerified",
                    "allBuffsAndEffectsVerified","ammoLauncherEngineBindingVerified"):
            self.assertIs(out[key],False)

if __name__=="__main__":
    unittest.main()
