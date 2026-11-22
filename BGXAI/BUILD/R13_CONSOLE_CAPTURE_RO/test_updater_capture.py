"""CI checkout invariant: capture exposes one new, consent-free read-only path."""
from pathlib import Path
import hashlib,json,re,unittest

REPO=Path(__file__).resolve().parents[3]
BASE=REPO/'BGXAI/BUILD/R13_SHORTNAME_REPAIR_SOURCE_ONLY/BGXAI_SYNC_162_CANDIDATE.ps1'
UPDATED=REPO/'BGXAI/BGXAI_SYNC.ps1'
GUARD=Path(__file__).with_name('BGXAI_R13_SHORTNAME_GUARDED.py')
LUA=Path(__file__).with_name('M_BGXD13.lua')
MANIFEST=Path(__file__).with_name('BGXAI_R13_SHORTNAME_MANIFEST_V1.json')
OLD_VERSION="version='0.3.86-R13-SHORTNAME-RO'"
NEW_VERSION="version='0.3.87-R13-CONSOLE-CAPTURE-RO'"

class Invariants(unittest.TestCase):
    def test_original_commands_1_through_162_untouched(self):
        old=BASE.read_bytes().decode('utf-8');new=UPDATED.read_bytes().decode('utf-8')
        self.assertEqual(new.replace(NEW_VERSION,OLD_VERSION),old)
        old_ids=re.findall(r"(?m)^'(\d+)' \{",old)
        new_ids=re.findall(r"(?m)^'(\d+)' \{",new)
        self.assertEqual(new_ids,old_ids)
        self.assertEqual([int(x) for x in new_ids],list(range(1,163)))
    def test_no_new_installer_action_or_game_write(self):
        source=GUARD.read_text()
        capture=source.split('def capture_console(')[1].split('\ndef main(')[0]
        self.assertNotIn('run_weidu(',capture)
        self.assertNotIn('copy2(',capture)
        self.assertNotIn('write_text(',capture)
        self.assertIn('stdout=handle',capture)
        self.assertIn('subprocess.STDOUT',capture)
        self.assertIn('close_fds=True',capture)
    def test_current_lua_untouched_and_pinned(self):
        manifest=json.loads(MANIFEST.read_text())
        self.assertEqual(manifest['version'],'0.3.87-R13-CONSOLE-CAPTURE-RO')
        for item in manifest['files']:
            b=(Path(__file__).parent/item['dest']).read_bytes()
            self.assertEqual(len(b),item['size'])
            self.assertEqual(hashlib.sha256(b).hexdigest(),item['sha256'])
        self.assertEqual(hashlib.sha256(LUA.read_bytes()).hexdigest(),'c0fb928001d5fb042a935302270df73130bed9576d331b2e4b41f27ee0244511')
    def test_single_menu_no_replacement_of_existing_options(self):
        source=GUARD.read_text()
        self.assertIn("'5':'capture'",source)
        self.assertIn("'1':'status'",source)
        self.assertIn("'2':'preflight'",source)
        self.assertIn("'3':'install'",source)
        self.assertIn("'4':'rollback'",source)
        self.assertIn("if args.mode=='status':out=status(root)",source)
        self.assertIn("elif args.mode=='capture'",source)
    def test_script_budget(self):
        self.assertLessEqual(UPDATED.stat().st_size,80000)

if __name__=='__main__':unittest.main(verbosity=2)
