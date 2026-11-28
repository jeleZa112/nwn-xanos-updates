"""Bounded module180 system batch: original GAM and original R3 reused."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
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

if __name__=='__main__':unittest.main(verbosity=2)
