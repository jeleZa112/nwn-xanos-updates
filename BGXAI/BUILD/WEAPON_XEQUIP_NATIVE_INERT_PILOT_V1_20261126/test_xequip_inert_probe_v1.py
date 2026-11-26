import copy
import importlib.util
import json
from pathlib import Path
import unittest

SRC = Path("BGXAI/BUILD/WEAPON_XEQUIP_NATIVE_INERT_PILOT_V1_20261126/BGXAI_XEQUIP_INERT_PROBE_V1.py")
spec = importlib.util.spec_from_file_location("inert", SRC)
inert = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inert)

def manifest(**kw):
    d={"schema":inert.SCHEMA,"actorId":123,"partyIndex":2,
       "sourceSlot":18,"targetSlot":36,"resref":"HAMM01",
       "weaponSlotCapacity":4}
    d.update(kw)
    return d

class TestInertBAF(unittest.TestCase):
    def test_known_18_to_36(self):
        r=inert.report(manifest())
        s=r["baf_source_only"]
        self.assertIn('CheckItemSlot(Myself,"HAMM01",SLOT_MISC3)',s)
        self.assertIn('!HasItemSlot(Myself,SLOT_WEAPON1)',s)
        self.assertIn('XEquipItem("HAMM01",Myself,SLOT_WEAPON1,EQUIP)',s)
        self.assertIn("False()\n  InParty(Myself)",s)
        self.assertIn("CombatCounter(0)",s)
        self.assertTrue(r["installed"] is False and
                        r["nativeWeiDUCompileVerified"] is False)
        self.assertEqual(r["ordersSent"],0)
    def test_last_backpack_to_last_weapon(self):
        s=inert.render(manifest(sourceSlot=33,targetSlot=38))
        self.assertIn("SLOT_MISC18",s)
        self.assertIn("SLOT_WEAPON3",s)
        self.assertEqual(s.count("XEquipItem("),1)
    def test_all_slots_correct(self):
        for slot in range(18,34):
            s=inert.render(manifest(sourceSlot=slot))
            self.assertIn(f'SLOT_MISC{slot-15})',s)
            self.assertIn("\n  False()\n",s)
        for slot in range(35,39):
            s=inert.render(manifest(targetSlot=slot))
            self.assertIn(f'SLOT_WEAPON{slot-35},EQUIP)',s)
    def test_reject_quick_item_source(self):
        for slot in (0,14,15,16,17,34,35,38,39):
            with self.assertRaises(inert.Hold):
                inert.render(manifest(sourceSlot=slot))
    def test_reject_unknown_destination(self):
        for slot in (0,17,18,33,34,39,40):
            with self.assertRaises(inert.Hold):
                inert.render(manifest(targetSlot=slot))
    def test_reject_class_capacity(self):
        for slot in (37,38):
            with self.assertRaises(inert.Hold):
                inert.render(manifest(targetSlot=slot,weaponSlotCapacity=2))
    def test_reject_protagonist_and_outparty(self):
        for i in (-1,0,6,100,True):
            with self.assertRaises(inert.Hold):
                inert.render(manifest(partyIndex=i))
    def test_resref_injection(self):
        for name in ('', 'TOOLONG99','HAMM01")\n DestroyItem(', 'HÖMM01', "A/B",
                     "A\n", "hamM01", None, "HAMM01\x00"):
            with self.assertRaises(inert.Hold):
                inert.render(manifest(resref=name))
    def test_disallow_extra_manifest_trust_flags(self):
        x=manifest(safeActionBoundaryVerified=True)
        with self.assertRaises(inert.Hold):
            inert.render(x)
    def test_all_actions_really_in_false_guard(self):
        s=inert.render(manifest())
        self.assertEqual(s.count("IF\n"),1)
        self.assertEqual(s.count("THEN\n"),1)
        self.assertIn("  False()\n",s.split("THEN")[0])
        self.assertNotIn("  False()\n",s.split("THEN")[1])
        self.assertNotIn("ClearActions(",s)
        self.assertNotIn("Stop(",s)
        self.assertNotIn("FillSlot(",s)
        self.assertNotIn("CreateItem(",s)
    def test_hard_refuse_dispatch(self):
        r=inert.report(manifest())
        for k in ("dispatchAuthorized","weaponSwitchAuthorized",
                  "inventoryMoveAuthorized","realItemIdentityVerified",
                  "safeActionBoundaryVerified","manualEpsOriginVerified",
                  "postTransferConservationVerified"):
            self.assertIs(r[k],False)

if __name__ == "__main__":
    unittest.main(verbosity=2)
