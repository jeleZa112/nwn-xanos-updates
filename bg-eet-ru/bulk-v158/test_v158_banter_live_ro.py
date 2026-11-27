import hashlib
import os
import struct
import pathlib
import shutil
import sys
import tempfile
import unittest
import zipfile

ROOT=pathlib.Path(__file__).parent
sys.path.insert(0,str(ROOT))
import v158_banter_live_ro as m
ARCHIVE=pathlib.Path(__file__).parent/'REAL_SNAPSHOT_OPTIONAL.zip'


def contents(game):
    return {str(p.relative_to(game)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in game.rglob('*') if p.is_file()}

class TestV158Live(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.z=zipfile.ZipFile(ARCHIVE) if ARCHIVE.exists() else None

    @classmethod
    def tearDownClass(cls):
        if cls.z is not None:cls.z.close()

    @classmethod
    def dlg_fixture(cls,name):
        if cls.z is not None:
            return cls.z.read(f'09_IWD_BANTER_DLG/{name}.DLG')
        anchors=[x for x in m.EXPECTED if x[1]==name]
        count=max(x[2] for x in anchors)+2
        st_offset=52;tr_count=80;tr_offset=st_offset+count*16
        raw=bytearray(tr_offset+tr_count*32)
        raw[:8]=b'DLG V1.0'
        struct.pack_into('<IIII',raw,8,count,st_offset,tr_count,tr_offset)
        for id,_,state,ref in anchors:
            struct.pack_into('<IIII',raw,st_offset+state*16,ref,0,1,0)
        return bytes(raw)

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.game=pathlib.Path(self.tmp.name)
        (self.game/'override').mkdir()
        (self.game/'chitin.key').write_bytes(b'test-key')
        for name in m.DLG_BASELINE:
            (self.game/'override'/f'{name}.DLG').write_bytes(self.dlg_fixture(name))
        (self.game/'WeiDU.log').write_text('~IWD1_EET/SETUP-IWD1_EET.TP2~ #0 #0 // 1\n~IWD2_EET/SETUP-IWD2_EET.TP2~ #0 #0 // only 0\n',encoding='utf-8')
        (self.game/'dialog.tlk').write_bytes(b'male')
        (self.game/'dialogf.tlk').write_bytes(b'female')

    def test_exact_five_archived_dlgs(self):
        r=m.audit_game(self.game)
        self.assertEqual(r['status'],'V158_READONLY_PROVENANCE_CAPTURE')
        self.assertEqual(len(r['dlgs']),5)
        self.assertEqual(r['dlg_baseline_equal_count'],5 if self.z is not None else 0)
        self.assertEqual(sum(len(x['tracked_states']) for x in r['dlgs']),10)
        self.assertTrue(r['dlg_all_state_anchors_unchanged'])
        self.assertFalse(any(x['isolated_compiled_sha_equal'] for x in r['dlgs']))

    def test_component_zero_is_not_component_one(self):
        w=m.parse_weidu((self.game/'WeiDU.log').read_bytes())
        self.assertEqual(w['groups']['IWD2_EET'],[0])
        self.assertFalse(w['main_branch_component_prerequisites_in_this_log'])

    def test_component_one_and_zero_match(self):
        with (self.game/'WeiDU.log').open('ab') as f:f.write(b'~IWD2_EET/SETUP-IWD2_EET.TP2~ #0 #1 // iwd2\n')
        w=m.audit_game(self.game)['weidu'];self.assertTrue(w['main_branch_component_prerequisites_in_this_log'])

    def test_component_one_without_iwd1_is_not_proof(self):
        (self.game/'WeiDU.log').write_bytes(b'~IWD2_EET/IWD2_EET.TP2~ #0 #1\n')
        self.assertFalse(m.audit_game(self.game)['weidu']['main_branch_component_prerequisites_in_this_log'])

    def test_similar_name_cannot_impersonate_component(self):
        s=b'~FOO-IWD2_EET_EXTRA.TP2~ #0 #1\n~SETUP-WEIdu2_eet.TP2~ #0 #1\n'
        self.assertEqual(m.parse_weidu(s)['groups']['IWD2_EET'],[])

    def test_backslash_separator_and_banter_alias(self):
        s=b'~mods\\IWD1_EET\\SETUP-IWD1_EET.TP2~ #0 #0\n~setup-IWD_EET-PARTY-BANTER.tp2~ #0 #0\n'
        r=m.parse_weidu(s)
        self.assertEqual(r['groups']['IWD1_EET'],[0]);self.assertEqual(r['groups']['IWD_PARTY_BANTER'],[0])

    def test_unparsed_relevant_line_flag(self):
        s=b'NOT A WEIDU RECORD IWD2_EET #1\n'
        self.assertEqual(m.parse_weidu(s)['unparsed_relevant_line_numbers'],[1])

    def test_no_read_mutates_game_files(self):
        a=contents(self.game);m.audit_game(self.game);b=contents(self.game)
        self.assertEqual(a,b)

    def test_missing_current_weidu_is_source_hold(self):
        (self.game/'WeiDU.log').unlink()
        r=m.audit_game(self.game)
        self.assertEqual(r['status'],'V158_READONLY_SOURCE_HOLD')
        self.assertEqual(len(r['dlgs']),5)

    def test_symlinked_weidu_rejected(self):
        (self.game/'WeiDU.log').unlink()
        try:(self.game/'WeiDU.log').symlink_to(self.game/'chitin.key')
        except (OSError,NotImplementedError):self.skipTest('Windows symlink privileges unavailable')
        r=m.audit_game(self.game)
        self.assertEqual(r['status'],'V158_READONLY_SOURCE_HOLD')
        self.assertEqual(r['game_files_written'],0)

    def test_duplicate_case_name_is_hold(self):
        if os.name=='nt':self.skipTest('NTFS case-insensitive filenames cannot coexist')
        original=self.game/'override'/'DDAMIEN.DLG'
        (self.game/'override'/'ddamien.dlg').write_bytes(original.read_bytes())
        self.assertEqual(m.audit_game(self.game)['status'],'V158_READONLY_SOURCE_HOLD')

    def test_header_corruption_rejected(self):
        p=self.game/'override'/'DDAMIEN.DLG';v=bytearray(p.read_bytes());v[:8]=b'BAD V1.0';p.write_bytes(v)
        self.assertEqual(m.audit_game(self.game)['status'],'V158_READONLY_SOURCE_HOLD')

    def test_valid_dlg_content_change_marked_drift(self):
        p=self.game/'override'/'DDAMIEN.DLG';v=bytearray(p.read_bytes());v[-1]^=1;p.write_bytes(v)
        r=m.audit_game(self.game)
        self.assertFalse(next(x for x in r['dlgs'] if x['dlg']=='DDAMIEN')['snapshot_baseline_equal'])
        self.assertTrue(r['dlg_all_state_anchors_unchanged'])
        self.assertFalse(r['weidu_main_branch_installed_proven'])

    def test_bad_state_table_raises_hold(self):
        p=self.game/'override'/'DDAMIEN.DLG';v=bytearray(p.read_bytes());v[12:16]=(10**9).to_bytes(4,'little');p.write_bytes(v)
        self.assertEqual(m.audit_game(self.game)['status'],'V158_READONLY_SOURCE_HOLD')

    def test_missing_target_dlg_is_hold(self):
        (self.game/'override'/'DHERMIT.DLG').unlink()
        self.assertEqual(m.audit_game(self.game)['status'],'V158_READONLY_SOURCE_HOLD')

    def test_status_never_claims_install_or_gameplay(self):
        (self.game/'WeiDU.log').write_bytes(b'~IWD1_EET.TP2~ #0 #0\n~IWD2_EET.TP2~ #0 #1\n')
        r=m.audit_game(self.game)
        self.assertFalse(r['install_allowed']);self.assertFalse(r['weidu_main_branch_installed_proven']);self.assertFalse(r['banter_runtime_visibility_proven'])

    def test_empty_weidu_is_hold(self):
        (self.game/'WeiDU.log').write_bytes(b'')
        self.assertEqual(m.audit_game(self.game)['status'],'V158_READONLY_SOURCE_HOLD')

    def test_non_game_root_is_hold(self):
        self.assertEqual(m.audit_game(self.game/'missing')['status'],'V158_READONLY_SOURCE_HOLD')

if __name__=='__main__':unittest.main(verbosity=2)
