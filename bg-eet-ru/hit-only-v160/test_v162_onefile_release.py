# -*- coding: utf-8 -*-
"""Static source and publisher contract tests; never touch installed game."""
from pathlib import Path
import hashlib
import json
import re
import base64
import zlib
import unittest

ROOT=Path(__file__).resolve().parents[2]
CMD=ROOT/'bg-eet-ru/onefile/BG_EET_RU_UPDATE.cmd'
RELEASE=ROOT/'bg-eet-ru/onefile/release.json'
DISPATCH=Path(__file__).with_name('weapon_names_onefile_dispatch.py')

class OnefileV162ReleaseContract(unittest.TestCase):
    def test_onefile_published_sha_and_size(self):
        cmd=CMD.read_bytes()
        release=json.loads(RELEASE.read_text(encoding='utf-8'))
        self.assertEqual(release['version'],164)
        self.assertEqual(hashlib.sha256(cmd).hexdigest(),release['sha256'])
        self.assertLessEqual(len(cmd),750000)
        self.assertGreater(len(cmd),700000)
        self.assertTrue(cmd.startswith(b'@echo off & py -3 -x'))
    def test_exact_pinned_backend_and_original_v160(self):
        cmd=CMD.read_text(encoding='utf-8')
        m=re.search(r"(?m)^V162_PIN='([0-9a-f]{64})'$",cmd)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1),hashlib.sha256(DISPATCH.read_bytes()).hexdigest())
        self.assertIn('ca6fa6bbc29f74ebe2884de39eb0e970813a1d3a',cmd)
        self.assertIn('V160_HIT_ONLY',cmd)
        self.assertIn('11=bulk',cmd)
        self.assertIn('12=names',cmd)
        self.assertIn('def v153_dispatch',cmd)
        self.assertIn("if digest(source)!=V162_PIN:raise RuntimeError('V162_PIN_CHANGED_BEFORE_EXEC')",cmd)
        self.assertEqual(cmd.count('def v162_dispatch('),1)
    def test_static_v69_byte_exact_compression_contract(self):
        cmd=CMD.read_text(encoding='utf-8')
        m=re.search(r"(?m)^V69_PROOF_DATA=zlib.decompress\(base64.b64decode\('([^']+)'\)\).decode\('utf8'\)$",cmd)
        self.assertIsNotNone(m)
        raw=zlib.decompress(base64.b64decode(m.group(1)))
        self.assertLess(len(raw),150000)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),'f2df72bf727d7263056197d985b057e0917119a82906c792aed995de1b06ce9f')
        self.assertIsInstance(json.loads(raw),dict)
    def test_no_new_installs_in_default_menu(self):
        code=CMD.read_text(encoding='utf-8')
        self.assertIn("if a=='12':",code)
        self.assertIn(".get(b,'status'),args.offline",code)
        self.assertIn("'79_V162_WEAPON_NAMES_BATCH.json'",code)
        self.assertIn("'UNKNOWN_AFTER_EXCEPTION' if mode in ('install','rollback') else 0",code)
if __name__=='__main__':unittest.main(verbosity=2)