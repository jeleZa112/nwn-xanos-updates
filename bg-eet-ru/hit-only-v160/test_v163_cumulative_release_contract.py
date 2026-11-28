# -*- coding: utf-8 -*-
"""Publisher contract for V163 cumulative menu; no game writes."""
from pathlib import Path
import hashlib
import json
import re
import unittest

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'bg-eet-ru'
ONEFILE=BASE/'onefile/BG_EET_RU_UPDATE.cmd'
RELEASE=BASE/'onefile/release.json'
DISPATCH=Path(__file__).with_name('weapon_names_cumulative_onefile_dispatch.py')
CUMULATIVE=Path(__file__).with_name('weapon_names_cumulative_source.py')
FIRST=Path(__file__).with_name('weapon_names_batch_source.py')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

class V163CumulativePublisher(unittest.TestCase):
    def test_exact_release_contract(self):
        blob=ONEFILE.read_bytes()
        manifest=json.loads(RELEASE.read_text(encoding='utf-8'))
        self.assertEqual(manifest['version'],165)
        self.assertEqual(sha(ONEFILE),manifest['sha256'])
        self.assertEqual(len(blob),747154)
        self.assertLessEqual(len(blob),750000)
        self.assertIn(b'SELF_VERSION = 165',blob)
        self.assertIs(manifest['game_writes_allowed'],False)
        self.assertIs(manifest['default_game_writes_allowed'],False)

    def test_old_12_menu_items_and_new_13_are_present(self):
        code=ONEFILE.read_text(encoding='utf-8')
        for s in ("if a=='12':","if a=='13':","def v162_dispatch(","def v163_dispatch(",
                  "11=bulk 12=names 13=next","80_V163_CUMULATIVE_NAMES.json",
                  "79_V162_WEAPON_NAMES_BATCH.json","'3':'install'","'4':'rollback'",
                  ".get(b,'status'),args.offline"):
            self.assertIn(s,code)
        self.assertEqual(code.count("def v162_dispatch("),1)
        self.assertEqual(code.count("def v163_dispatch("),1)

    def test_sha_pinned_source_before_exec(self):
        code=ONEFILE.read_text(encoding='utf-8')
        pin=re.search(r"(?m)^V163_PIN='([0-9a-f]{64})'$",code)
        self.assertIsNotNone(pin)
        self.assertEqual(pin.group(1),sha(DISPATCH))
        self.assertIn('8ea2895b2e1167e7be8a226367e4b4af37968425',code)
        self.assertIn("if digest(source)!=V163_PIN:raise RuntimeError('V163_PIN_CHANGED_BEFORE_EXEC')",code)
        self.assertIn("if digest(data)!=V163_PIN:raise RuntimeError('V163_SOURCE_SHA_HOLD')",code)
        self.assertNotIn('XEquipItem(',DISPATCH.read_text('utf-8'))
        self.assertNotIn('EEex_Sprite_AddAlterBaseWeaponDamageListener(',DISPATCH.read_text('utf-8'))

    def test_cumulative_source_and_old_batch_immutable(self):
        source=DISPATCH.read_text(encoding='utf-8')
        self.assertIn("SECOND_REF = 'b447162812c3cc0461052034834f3d27bee8875f'",source)
        self.assertIn("SECOND_SHA = '"+sha(CUMULATIVE)+"'",source)
        self.assertIn("BASE_SHA = 'b46a01274479fbe3c7e83cf847ef299ba41d12f4a1f051ac26cf7495b7e2ab00'",source)
        self.assertIn("EXPECTED_FIRST_INSTALLED_SHA = 'a2e79fab744bcd8f66260d90a5a5cfd66e7ef0f05acb538505008820991e453f'",CUMULATIVE.read_text('utf-8'))
        self.assertIn("FIRST_STATE = 'BG_EET_RU_WEAPON_NAMES_BATCH_STATE.json'",CUMULATIVE.read_text('utf-8'))
        self.assertIn("SECOND_STATE = 'BG_EET_RU_WEAPON_NAMES_CUMULATIVE_STATE.json'",CUMULATIVE.read_text('utf-8'))
        self.assertIn('BATCH_EXISTING_STATE',FIRST.read_text('utf-8'))

if __name__ == '__main__':unittest.main()
