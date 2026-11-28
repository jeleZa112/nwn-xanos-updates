"""Bounded module180 system batch: original GAM and original R3 reused."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch
import struct
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod
mod=load('BGXAI/UPDATER_V2/BGXAI_MODULE180_SAVED_PARTY_CATALOG_RO.py','bgx180')
gam=load('BGXAI/BUILD/WEAPON_SAVE_GAM_INVENTORY_RO_V1_20261126/BGXAI_GAM_INVENTORY_RO_V1.py','bgxgam')
r3=load('BGXAI/patchsets/ranged_fighter_guarded_20261119/BGXAI_WEAPON_NATIVE_ITM_R3_RO.py','bgxr3')
gamtest=load('BGXAI/BUILD/WEAPON_SAVE_GAM_INVENTORY_RO_V1_20261126/test_gam_inventory_ro_v1.py','bgxgam_fixture')
r3test=load('BGXAI/patchsets/ranged_fighter_guarded_20261119/test_weapon_native_itm_r3_ro.py','bgxr3_fixture')

def saved_gam_with_existing_itm_resources():
    raw=bytearray(gamtest.make_gam())
    # These are genuine R3 real-format BIF fixture item resrefs, not invented.
    a=raw.find(b'BOW05')
    b=raw.find(b'SHLD03A')
    assert a>=0 and b>=0 and a!=b
    raw[a:a+8]=b'STAF01\0\0'
    raw[b:b+8]=b'SW1H04\0\0'
    return bytes(raw)

class CatalogStage(unittest.TestCase):
 def setUp(self):
    self.r3fixture=r3test.NativeFixture(methodName='test_full_audit_keeps_switch_off')
    self.r3fixture.setUp()
    self.addCleanup(self.r3fixture.doCleanups)
    self.game=self.r3fixture.root
    self.temp=tempfile.TemporaryDirectory()
    self.addCleanup(self.temp.cleanup)
    self.root=Path(self.temp.name)
    self.docs=self.root/'docs'
    self.reports=self.root/'reports'
    self.saves=self.docs/"Baldur's Gate II - Enhanced Edition"/'save'/'000000001-Quicksave'
    self.saves.mkdir(parents=True)
    self.gam=self.saves/'BALDUR.GAM'
    self.raw=saved_gam_with_existing_itm_resources()
    self.gam.write_bytes(self.raw)

 def test_existing_gam_and_r3_build_full_inert_data_catalog(self):
    result=mod.run(self.game,self.docs,self.reports,game_required=False)
    self.assertEqual(result['status'],'SOURCE_CATALOG_READY_OUTSIDE_GAME',result)
    self.assertEqual(result['partyCount'],1)
    self.assertEqual(result['uniqueItemResources'],2)
    payload=Path(result['catalogPath']).read_text(encoding='ascii')
    self.assertIn('["SW1H04"]',payload)
    self.assertIn('["STAF01"]',payload)
    self.assertIn('["sourceKind"]="SAVED_GAM_WITH_CURRENT_GAME_RESOURCE_BYTES"',payload)
    self.assertIn('["dispatchAuthorized"]=false',payload)
    self.assertIn('["alternateSlotEffectiveAprVerified"]=false',payload)
    self.assertNotIn('XEquipItem(',payload)
    self.assertFalse(result['gameModified'])
    self.assertTrue(Path(result['catalogPath']).is_relative_to(self.reports))
    self.assertEqual(result['catalogHash'],hashlib.sha256(
        Path(result['catalogPath']).read_bytes()).hexdigest())

 def test_moded_hash_and_dash_saved_items_join_existing_r3_without_game_writes(self):
    # End-to-end using the original CRE/GAM + R3 native KEY/BIFF fixture.
    # Names are legal in BOTH parsers; no separate reader or game action.
    raw=bytearray(self.raw)
    self.assertIn(b'STAF01\\0\\0',raw)
    self.assertIn(b'SW1H04\\0\\0',raw)
    raw=raw.replace(b'STAF01\\0\\0',b'C#GRTOO0',1)
    raw=raw.replace(b'SW1H04\\0\\0',b'C-ITEM01',1)
    self.gam.write_bytes(raw)
    override=self.game/'override'
    (override/'C#GRTOO0.ITM').write_bytes(r3test.STAF01)
    (override/'C-ITEM01.ITM').write_bytes(r3test.STAF01)
    before_save=self.gam.read_bytes()
    before_resources={
       name:(override/name).read_bytes()
       for name in ('C#GRTOO0.ITM','C-ITEM01.ITM')}
    result=mod.run(self.game,self.docs,self.reports,game_required=False)
    self.assertEqual(result['status'],'SOURCE_CATALOG_READY_OUTSIDE_GAME',result)
    self.assertIn(result['uniqueItemResources'],(3,))
    lua=Path(result['catalogPath']).read_text(encoding='ascii')
    self.assertIn('["C#GRTOO0"]',lua)
    self.assertIn('["C-ITEM01"]',lua)
    self.assertIn('["dispatchAuthorized"]=false',lua)
    self.assertFalse(result['inventoryMoveAuthorized'])
    self.assertFalse(result['gameModified'])
    self.assertEqual(result['ordersSent'],0)
    self.assertEqual(self.gam.read_bytes(),before_save)
    for name,data in before_resources.items():
      self.assertEqual((override/name).read_bytes(),data)

 def test_same_source_idempotent_not_overwritten(self):
    first=mod.run(self.game,self.docs,self.reports,game_required=False)
    self.assertEqual(first['status'],'SOURCE_CATALOG_READY_OUTSIDE_GAME')
    before=Path(first['catalogPath']).stat().st_mtime_ns
    after=mod.run(self.game,self.docs,self.reports,game_required=False)
    self.assertEqual(after['status'],'SOURCE_CATALOG_READY_OUTSIDE_GAME')
    self.assertEqual(Path(after['catalogPath']).stat().st_mtime_ns,before)

 def test_reports_inside_eet_game_never_written(self):
    ret=mod.run(self.game,self.docs,self.game/'override',game_required=False)
    self.assertEqual(ret['status'],'HOLD_SAVED_PARTY_CATALOG_PREPARATION')
    self.assertEqual(ret['reason'],'HOLD_REPORT_DIRECTORY_INSIDE_GAME')

 def test_saved_version_21_safely_holds(self):
    b=bytearray(self.raw);b[:8]=b'GAMEV2.1'
    self.gam.write_bytes(b)
    ret=mod.run(self.game,self.docs,self.reports,game_required=False)
    self.assertEqual(ret['status'],'HOLD_SAVED_PARTY_CATALOG_PREPARATION')
    self.assertFalse(ret['dispatchAuthorized'])

 def test_no_saves_no_game_actions(self):
    self.gam.unlink()
    ret=mod.run(self.game,self.docs,self.reports,game_required=False)
    self.assertEqual(ret['reason'],'HOLD_NO_EXISTING_BALDUR_GAM')
    self.assertEqual(ret['ordersSent'],0)

 def test_chitin_path_corrupt_holds_without_catalog(self):
    (self.game/'chitin.key').write_bytes(b'corrupt')
    ret=mod.run(self.game,self.docs,self.reports,game_required=False)
    self.assertEqual(ret['status'],'HOLD_SAVED_PARTY_CATALOG_PREPARATION')
    self.assertFalse(self.reports.exists() and list(self.reports.glob('*.lua')))

 def test_missing_item_resref_cannot_be_synthesized(self):
    a=bytearray(self.raw);index=a.find(b'STAF01')
    a[index:index+8]=b'FAKE01\0\0'
    self.gam.write_bytes(a)
    ret=mod.run(self.game,self.docs,self.reports,game_required=False)
    self.assertEqual(ret['reason'],'HOLD_R3_CURRENT_GAME_RESOURCE_COVERAGE')

 def test_duplicate_item_resref_same_party_resource_is_not_instance_identity(self):
    ret=mod.run(self.game,self.docs,self.reports,game_required=False)
    self.assertEqual(ret['status'],'SOURCE_CATALOG_READY_OUTSIDE_GAME')
    payload=Path(ret['catalogPath']).read_text(encoding='ascii')
    self.assertIn('["liveItemInstancesVerified"]=false',payload)

 def test_tampered_output_blocks_no_overwrite(self):
    ret=mod.run(self.game,self.docs,self.reports,game_required=False)
    path=Path(ret['catalogPath'])
    path.write_text('tampered',encoding='ascii')
    second=mod.run(self.game,self.docs,self.reports,game_required=False)
    self.assertEqual(second['reason'],'HOLD_REPORT_OUTPUT_CONFLICT')
    self.assertEqual(path.read_text(encoding='ascii'),'tampered')

 def test_unknown_eet_member_slot_fails_closed(self):
    parsed=gam.parse(self.raw)
    parsed['partyMembers'][0]['topLevelSlots'][18]['slot']=3
    with self.assertRaisesRegex(mod.Hold,'HOLD_GAM_SLOT_INDEX_UNTRUSTED'):
        mod.saved_names(parsed)


 def test_unexpected_source_error_reports_stage_without_disclosing_private_error(self):
    cases=(
      ("load",TypeError("PRIVATE: game user's Documents path"),"LOAD_EXISTING_GAM_READER","TypeError"),
      ("choose_gam",OSError("PRIVATE: save folder name"),"LOCATE_EXISTING_SAVE","OSError"),
      ("saved_names",KeyError("PRIVATE: inventory"),"VALIDATE_SAVED_PARTY_ITEMS","KeyError"),
      ("build_source",ValueError("PRIVATE: item path"),"BUILD_INERT_LUA_CATALOG","ValueError"),
    )
    for func,exc,stage,error_class in cases:
      with self.subTest(func=func), patch.object(mod,func,side_effect=exc):
        result=mod.run(self.game,self.docs,self.reports,game_required=False)
        self.assertEqual(result["status"],"HOLD_SAVED_PARTY_CATALOG_PREPARATION")
        self.assertEqual(result["reason"],"HOLD_MODULE180_UNEXPECTED_SOURCE_STAGE")
        self.assertEqual(result["failureStage"],stage)
        self.assertEqual(result["exceptionType"],error_class)
        self.assertTrue(result["noAutoRetry"])
        self.assertFalse(result["gameModified"])
        self.assertFalse(result["dispatchAuthorized"])
        self.assertEqual(result["ordersSent"],0)
        self.assertNotIn("PRIVATE",json.dumps(result))
        self.assertFalse(list(self.reports.glob("*.lua")))

 def test_original_gam_and_r3_parser_hold_is_not_hidden_or_leaked(self):
    # These are the exact already-imported native parser classes, NOT a
    # fabricated new reader. The prefix is needed to avoid another game test.
    installed_gam=mod.load(mod.GAM_PATH,"bgxai_existing_saved_gam_parser_v1")
    installed_r3=mod.load(mod.R3_PATH,"bgxai_existing_r3_itm_parser_v3")
    tests=(
       ("saved_names",installed_gam.Hold("HOLD_UNSUPPORTED_GAM_VERSION_NOT_GUESSING"),
        "VALIDATE_SAVED_PARTY_ITEMS",
        "HOLD_EXISTING_READER_HOLD_UNSUPPORTED_GAM_VERSION_NOT_GUESSING"),
       ("build_source",installed_r3.Hold("CHITIN_KEY_DUPLICATE_RESOURCE:PRIVATE_ITEM_NAME"),
        "BUILD_INERT_LUA_CATALOG",
        "HOLD_EXISTING_READER_CHITIN_KEY_DUPLICATE_RESOURCE"),
    )
    for function,exc,stage,want in tests:
      with self.subTest(function=function),patch.object(mod,function,side_effect=exc):
        result=mod.run(self.game,self.docs,self.reports,game_required=False)
        self.assertEqual(result["reason"],want)
        self.assertEqual(result["failureStage"],stage)
        self.assertEqual(result["exceptionType"],"KNOWN_READER_HOLD")
        self.assertTrue(result["noAutoRetry"])
        self.assertEqual(result["ordersSent"],0)
        self.assertFalse(result["gameModified"])
        self.assertNotIn("PRIVATE",json.dumps(result))
        self.assertFalse(list(self.reports.glob("*.lua")))

 def test_existing_specific_hold_still_reports_original_reason_without_retries(self):
    self.gam.unlink()
    result=mod.run(self.game,self.docs,self.reports,game_required=False)
    self.assertEqual(result["reason"],"HOLD_NO_EXISTING_BALDUR_GAM")
    self.assertEqual(result["failureStage"],"LOCATE_EXISTING_SAVE")
    self.assertNotIn("exceptionType",result)
    self.assertTrue(result["noAutoRetry"])


if __name__=='__main__':unittest.main(verbosity=2)
