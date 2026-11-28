# -*- coding: utf-8 -*-
"""Guard V160 release, pinned dispatch and the single-updater 750k limit."""
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'bg-eet-ru'
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

class V160ReleaseContract(unittest.TestCase):
    def test_exact_onefile_release_pin_and_size(self):
        cmd = BASE / 'onefile/BG_EET_RU_UPDATE.cmd'
        release = json.loads((BASE / 'onefile/release.json').read_text('utf-8'))
        blob = cmd.read_bytes()
        self.assertEqual(release['version'], 163)
        self.assertEqual(release['sha256'], sha(cmd))
        self.assertLessEqual(len(blob), 750000)
        self.assertEqual(len(blob), 749793)
        self.assertIn(b'SELF_VERSION = 163', blob)
        self.assertIs(release['default_game_writes_allowed'], False)
        self.assertIs(release['game_writes_allowed'], False)
        self.assertIs(release['typed_game_write_mode_available'], True)
        self.assertIs(release['weidu_native_component'], False)

    def test_reuses_v159_v153_same_dispatcher_and_menu(self):
        cmd = (BASE / 'onefile/BG_EET_RU_UPDATE.cmd').read_bytes()
        combined = BASE / 'bulk-v159/v159_combined.py'
        pin = sha(combined)
        self.assertEqual(pin, 'c7118f29cc62cc59da130afd3206b811d06aa3bf2f3a166bbc1b324a616ea231')
        self.assertIn(("V153_PIN='"+pin+"'").encode('ascii'),cmd)
        self.assertIn(b"if b in ('9','10','11','12')",cmd)
        self.assertIn(b"mode.startswith('hit160_')",cmd)
        self.assertIn(b'78_V160_HIT_ONLY.json',cmd)
        self.assertIn(b'77_V159_BATCH.json',cmd)
        self.assertIn(b'76_V158_BANTER_LIVE_RO.json',cmd)
        self.assertIn(b'75_V157_BULK_ONE_BATCH.json',cmd)
        source=combined.read_bytes()
        self.assertIn(b"mode.startswith('hit160_')",source)
        self.assertIn(b'read_pinned_cached',source)
        self.assertIn(b'BG_EET_RU_V160_CODE_CACHE',source)
        self.assertIn(b"mode.startswith('batch159_')",source)
        self.assertIn(b"_V158_RUN_UNCHANGED",source)
        self.assertIn(b'INSTALL_BG_EET_RU_V160_HIT_ONLY', (BASE/'hit-only-v160/v160_guarded.py').read_bytes())

    def test_pinned_lua_and_installer_immutable(self):
        src=BASE/'hit-only-v160'
        self.assertEqual(sha(src/'v160_guarded.py'), 'ccf02f4892bf0ed434ac97a1f0bb7d7da2a9abdde8fafe7a64b422386e82b2de')
        self.assertEqual(sha(src/'BG_EET_RU_V160_HIT_ONLY_APPEND.lua'), 'ad76b46df1359bfdeeb9400f6b10f2ecd104059bd17a12d737fa60dcd733445c')
        attrs=(ROOT/'.gitattributes').read_text('utf-8')
        self.assertIn('bg-eet-ru/hit-only-v160/*.lua text eol=lf',attrs)
        self.assertIn('bg-eet-ru/onefile/BG_EET_RU_UPDATE.cmd text eol=lf',attrs)

if __name__ == '__main__':
    unittest.main()
