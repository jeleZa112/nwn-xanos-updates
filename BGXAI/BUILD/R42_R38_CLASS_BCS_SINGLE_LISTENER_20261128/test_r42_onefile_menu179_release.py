"""R42 menu179 static contract; never runs PowerShell or touches EET."""
from pathlib import Path
import hashlib
import re
import unittest

ROOT=Path(__file__).resolve().parents[3]
SYNC=ROOT/'BGXAI/BGXAI_SYNC.ps1'
BOOT=ROOT/'BGXAI_UPDATE.cmd'
HELPER=ROOT/'BGXAI/BUILD/R42_R38_CLASS_BCS_SINGLE_LISTENER_20261128/BGXAI_R42_ONEFILE_SOURCE_RO.py'
OLD175='d6fa98f19bb693e4f2cb43216307805ba427a4accefa703d03f33c299df21a3c'
NEW179='737cbbc5fbb00e2570bdf9f2769600cd9022dac1e3ee8b84784d512fd376920f'
HELPER_PATH='BGXAI/BUILD/R42_R38_CLASS_BCS_SINGLE_LISTENER_20261128/BGXAI_R42_ONEFILE_SOURCE_RO.py'
LIMIT=80000

class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=SYNC.read_bytes()
        cls.src=cls.raw.decode('utf-8')
        cls.lines=cls.src.splitlines()
        cls.routes=[line for line in cls.lines if line.startswith("{$_ -match '^17[569]$'}")]

    def test_limit_with_margin(self):
        self.assertLessEqual(len(self.raw),LIMIT)
        self.assertEqual(len(self.raw),79792)

    def test_ascii_exact_onefile(self):
        self.assertTrue(self.raw.isascii())
        self.assertFalse(self.raw.startswith(b'\xef\xbb\xbf'))

    def test_one_unambiguous_router(self):
        self.assertEqual(len(self.routes),1)
        self.assertEqual(self.routes[0].count("if($choice -eq '179')"),1)
        self.assertEqual(self.src.count("179 R42 RO"),1)

    def test_keep_existing_175_176_stage_and_native_flag(self):
        r=self.routes[0]
        self.assertIn('BGXAI_XEQUIP_ONEFILE_175_RO_V1.py',r)
        self.assertIn(OLD175,r)
        self.assertIn('$n=21120',r)
        self.assertIn("if($choice -eq '176')",r)
        self.assertIn("$extra=@('--v3')",r)
        self.assertIn('--native-readonly @extra',r)

    def test_new179_pin_is_exact(self):
        r=self.routes[0]
        self.assertIn(NEW179,r)
        self.assertIn('$n=8351',r)
        self.assertIn(HELPER_PATH,r)
        self.assertEqual(hashlib.sha256(HELPER.read_bytes()).hexdigest(),NEW179)

    def test_allowlist_is_finite(self):
        self.assertIn('|BUILD/R42_R38_CLASS_BCS_SINGLE_LISTENER_20261128)',self.src)
        self.assertIn("or $zrp.Contains('..')",self.src)
        self.assertIn("Get-PinnedBytes $p",self.routes[0])
        self.assertNotIn("$p='http",self.routes[0])

    def test_only_one_batch_bootstrap(self):
        b=BOOT.read_text(encoding='utf-8')
        self.assertIn('BGXAI_SYNC.current.ps1',b)
        self.assertIn('BGXAI/fox_new/BOOTSTRAP_PIN.json',b)
        self.assertIn('80000',b)
        self.assertIn('BGXAI_SYNC.ps1',b)

    def test_original_entrypoint_179_not_installer(self):
        self.assertIn('--native-readonly @extra',self.routes[0])
        self.assertNotIn('--install',self.routes[0])
        self.assertNotIn('--rollback',self.routes[0])

    def test_source_has_no_unexpected_auto_action(self):
        h=HELPER.read_text(encoding='utf-8')
        self.assertNotIn('XEquipItem(',h)
        self.assertNotIn('SetGlobal(',h)
        self.assertNotIn('InfinityLoader.exe',h)

    def test_no_other_dynamic_menu_179(self):
        self.assertEqual(self.src.count("if($choice -eq '179')"),1)
        self.assertNotIn("'179' {",self.src)

    def test_main_menu_cancellation_remains_zero(self):
        self.assertIn("if($choice -eq '0'){wh 'No changes.';exit 0}",self.src)

    def test_updater_has_no_runtime_overflow(self):
        self.assertLessEqual(len(self.raw),LIMIT)
        self.assertGreaterEqual(LIMIT-len(self.raw),100)


    def test_published_onefile_channel_pin_exact_bytes(self):
        import json
        channel=json.loads((ROOT/'BGXAI/fox_new/BOOTSTRAP_PIN.json').read_text(encoding='utf-8'))
        self.assertEqual(channel['channel'],'bgxai-fox-new-onefile')
        self.assertEqual(channel['script_path'],'BGXAI/BGXAI_SYNC.ps1')
        self.assertEqual(channel['script_size'],len(self.raw))
        self.assertEqual(channel['script_sha256'],hashlib.sha256(self.raw).hexdigest())
        self.assertEqual(channel['commit'],'6ae745332d314d6bacd8ad883cdf808ae7a866f5')

    def test_published_source_only_claim_is_accurate(self):
        import json
        channel=json.loads((ROOT/'BGXAI/fox_new/BOOTSTRAP_PIN.json').read_text(encoding='utf-8'))
        self.assertIn('source-only',channel['description'])
        self.assertIn('179',channel['description'])
        self.assertIn('175/176',channel['description'])
        self.assertLess(channel['script_size'],80000)

if __name__=='__main__':unittest.main()
