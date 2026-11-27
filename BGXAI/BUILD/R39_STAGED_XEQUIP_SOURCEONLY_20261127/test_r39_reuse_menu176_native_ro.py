"""Purely offline safety tests; cannot claim native Windows EET compile."""
from pathlib import Path
import hashlib
import tempfile
import unittest
from unittest.mock import patch
import BGXAI_R39_NATIVE_EET_COMPILE_RO_V1 as p


class NativeReuse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=Path(__file__).with_name(p.BAF_NAME)

    def test_exact_published_baf(self):
        s=p.exact_source(self.source)
        self.assertEqual(len(s),2303)
        self.assertEqual(hashlib.sha256(s).hexdigest(),p.BAF_SHA)

    def test_native_missing_sources_fails_closed(self):
        self.assertEqual(p.main(['--native-readonly','--source',str(self.source)]),3)

    def test_source_only_never_native_pass(self):
        v=p.source_only(self.source)
        self.assertEqual(v['status'],'EXACT_R39_BAF_PIN_PASS_NO_NATIVE')
        self.assertIs(v['nativeWeiDUCompileVerified'],False)
        self.assertFalse(v['gameModified'])
        self.assertFalse(v['dispatchAuthorized'])

    def test_invalid_source_baf_does_not_pass(self):
        with tempfile.TemporaryDirectory() as d:
            x=Path(d)/p.BAF_NAME;x.write_bytes(self.source.read_bytes()[:-1])
            with self.assertRaises(p.Hold):p.exact_source(x)

    def test_baf_name_guard(self):
        with tempfile.TemporaryDirectory() as d:
            x=Path(d)/'R39_OTHER.baf';x.write_bytes(self.source.read_bytes())
            with self.assertRaises(p.Hold):p.exact_source(x)

    def test_no_v3_helper_incorrect_sha(self):
        with tempfile.TemporaryDirectory() as d:
            x=Path(d)/p.V3_HELPER_NAME;x.write_text('broken')
            with self.assertRaises(p.Hold):p.exact_v3_helper(x)

    def test_v3_known_exact_pinned_source_import(self):
        historical=Path('/mnt/data/bgxai_audit/current/BGXAI_XEQUIP_V3_NATIVE_COMPILE_RO.py')
        if not historical.is_file():
            self.skipTest('Historical private helper is not bundled with published source-only tests')
        raw=historical.read_bytes()
        if len(raw)==p.V3_HELPER_BYTES+1 and raw.endswith(b'\n'): raw=raw[:-1]
        with tempfile.TemporaryDirectory() as d:
            x=Path(d)/p.V3_HELPER_NAME;x.write_bytes(raw)
            mod=p.exact_v3_helper(x)
            self.assertTrue(callable(mod.close_game_proof))

    def test_source_does_not_install(self):
        src=Path(p.__file__).read_text('utf-8')
        for forbidden in ('--force-install','--force-uninstall',
                          'setup-BGXR41',
                          'SetGlobal("BGXW3ARM","LOCALS",1)',
                          'shutil.copy2('):
            with self.subTest(forbidden=forbidden): self.assertNotIn(forbidden,src)

    def test_source_only_does_not_need_game(self):
        v=p.source_only(self.source)
        self.assertEqual(v['sourceBytes'],2303)
        self.assertNotIn('compiledBcsSha256',v)

    def test_backend_reuse_contract(self):
        src=Path(p.__file__).read_text('utf-8')
        for token in ('v3.close_game_proof()', 'v3.pinned_compiler(game)',
                      'v3.load_backend(backend_path)',
                      'backend.compile_readonly(game,candidate,compiler)',
                      'backend.source_check=orig_check'):
            self.assertIn(token,src)

    def test_itm_exact_checksum_and_header_flags(self):
        with tempfile.TemporaryDirectory() as d:
            game=Path(d); root=game/'override';root.mkdir()
            item=bytearray(114)
            item[:8]=b'ITM V1  '
            item[0x18:0x1c]=(46).to_bytes(4,'little')
            item[0x1c:0x1e]=(26).to_bytes(2,'little')
            item[0x26:0x28]=(5).to_bytes(2,'little')
            f=root/'STAF01.ITM';f.write_bytes(item)
            with patch.object(p,'ITM_SHA',p.digest(bytes(item))):
                out=p.static_item_preflight(game)
                self.assertTrue(out['staticItemClassKitHeaderAllowed'])
                self.assertFalse(out['engineCanEquipVerified'])
                self.assertFalse(out['currentSessionActorKitVerified'])

    def test_itm_cleric_restriction(self):
        with tempfile.TemporaryDirectory() as d:
            game=Path(d);root=game/'override';root.mkdir()
            item=bytearray(114);item[:8]=b'ITM V1  '
            item[0x18:0x1c]=(46).to_bytes(4,'little')
            item[0x1c:0x1e]=(26).to_bytes(2,'little')
            item[0x26:0x28]=(5).to_bytes(2,'little')
            item[0x1e]=0x80; (root/'STAF01.ITM').write_bytes(item)
            with patch.object(p,'ITM_SHA',p.digest(bytes(item))):
                with self.assertRaisesRegex(p.Hold,'HOLD_ITM_RESTRICTS_CLERIC'):
                    p.static_item_preflight(game)

    def test_itm_trueclass_restriction(self):
        with tempfile.TemporaryDirectory() as d:
            game=Path(d);root=game/'override';root.mkdir()
            item=bytearray(114);item[:8]=b'ITM V1  '
            item[0x18:0x1c]=(46).to_bytes(4,'little')
            item[0x1c:0x1e]=(26).to_bytes(2,'little')
            item[0x26:0x28]=(5).to_bytes(2,'little')
            item[0x2d]=0x40; (root/'STAF01.ITM').write_bytes(item)
            with patch.object(p,'ITM_SHA',p.digest(bytes(item))):
                with self.assertRaisesRegex(p.Hold,'HOLD_ITM_RESTRICTS_TRUECLASS'):
                    p.static_item_preflight(game)

    def test_itm_unknown_race_restrictions_fail(self):
        with tempfile.TemporaryDirectory() as d:
            game=Path(d);root=game/'override';root.mkdir()
            item=bytearray(114);item[:8]=b'ITM V1  '
            item[0x18:0x1c]=(46).to_bytes(4,'little')
            item[0x1c:0x1e]=(26).to_bytes(2,'little')
            item[0x26:0x28]=(5).to_bytes(2,'little')
            item[0x21]=0x08; (root/'STAF01.ITM').write_bytes(item)
            with patch.object(p,'ITM_SHA',p.digest(bytes(item))):
                with self.assertRaisesRegex(p.Hold,'HOLD_ITM_RACE_RESTRICTIONS_UNVERIFIED'):
                    p.static_item_preflight(game)

    def test_itm_monk_or_druid_bits_are_not_races(self):
        # IESDP: 0x21 0x20=Monk, 0x40=Druid/Shaman, not racial bans.
        for byte in (0x20,0x40,0x60):
            with self.subTest(restrictions=hex(byte)),tempfile.TemporaryDirectory() as d:
                game=Path(d); root=game/'override';root.mkdir()
                item=bytearray(114);item[:8]=b'ITM V1  '
                item[0x18:0x1c]=(46).to_bytes(4,'little')
                item[0x1c:0x1e]=(26).to_bytes(2,'little')
                item[0x26:0x28]=(5).to_bytes(2,'little')
                item[0x21]=byte;(root/'STAF01.ITM').write_bytes(item)
                with patch.object(p,'ITM_SHA',p.digest(bytes(item))):
                    out=p.static_item_preflight(game)
                    self.assertTrue(out['staticItemClassKitHeaderAllowed'])
                    self.assertEqual(out['observedUnrelatedMonkDruidRestrictionMask'],byte)
                    self.assertFalse(out['engineCanEquipVerified'])

    def test_itm_real_racial_bits_still_hold_even_with_monk_druid(self):
        # All six 4th-byte races stay denied as long as actor race is unknown.
        for byte in (0x01,0x02,0x04,0x08,0x10,0x80,0xa0,0x41):
            with self.subTest(restrictions=hex(byte)),tempfile.TemporaryDirectory() as d:
                game=Path(d);root=game/'override';root.mkdir()
                item=bytearray(114);item[:8]=b'ITM V1  '
                item[0x18:0x1c]=(46).to_bytes(4,'little')
                item[0x1c:0x1e]=(26).to_bytes(2,'little')
                item[0x26:0x28]=(5).to_bytes(2,'little')
                item[0x21]=byte;(root/'STAF01.ITM').write_bytes(item)
                with patch.object(p,'ITM_SHA',p.digest(bytes(item))):
                    with self.assertRaisesRegex(p.Hold,'HOLD_ITM_RACE_RESTRICTIONS_UNVERIFIED'):
                        p.static_item_preflight(game)

    def test_itm_elf_race_restriction_in_byte3_still_holds(self):
        with tempfile.TemporaryDirectory() as d:
            game=Path(d);root=game/'override';root.mkdir()
            item=bytearray(114);item[:8]=b'ITM V1  '
            item[0x18:0x1c]=(46).to_bytes(4,'little')
            item[0x1c:0x1e]=(26).to_bytes(2,'little')
            item[0x26:0x28]=(5).to_bytes(2,'little')
            item[0x20]=0x80; (root/'STAF01.ITM').write_bytes(item)
            with patch.object(p,'ITM_SHA',p.digest(bytes(item))):
                with self.assertRaisesRegex(p.Hold,'HOLD_ITM_RACE_RESTRICTIONS_UNVERIFIED'):
                    p.static_item_preflight(game)

    def test_itm_unknown_alignment_restrictions_fail(self):
        with tempfile.TemporaryDirectory() as d:
            game=Path(d);root=game/'override';root.mkdir()
            item=bytearray(114);item[:8]=b'ITM V1  '
            item[0x18:0x1c]=(46).to_bytes(4,'little')
            item[0x1c:0x1e]=(26).to_bytes(2,'little')
            item[0x26:0x28]=(5).to_bytes(2,'little')
            item[0x1e]=0x02; (root/'STAF01.ITM').write_bytes(item)
            with patch.object(p,'ITM_SHA',p.digest(bytes(item))):
                with self.assertRaisesRegex(p.Hold,'HOLD_ITM_ALIGNMENT_RESTRICTIONS_UNVERIFIED'):
                    p.static_item_preflight(game)

    def test_itm_rejects_nonbase_sha_and_demands_level_knowledge(self):
        with tempfile.TemporaryDirectory() as d:
            game=Path(d);root=game/'override';root.mkdir()
            item=bytearray(114);item[:8]=b'ITM V1  '
            item[0x18:0x1c]=(46).to_bytes(4,'little')
            item[0x1c:0x1e]=(26).to_bytes(2,'little')
            item[0x26:0x28]=(5).to_bytes(2,'little')
            f=root/'STAF01.ITM';f.write_bytes(item)
            with self.assertRaisesRegex(p.Hold,'SHA_DRIFT'):
                p.static_item_preflight(game)
            item[0x24]=1;f.write_bytes(item)
            with patch.object(p,'ITM_SHA',p.digest(bytes(item))):
                with self.assertRaisesRegex(p.Hold,'OTHER_STATS_OR_LEVEL'):
                    p.static_item_preflight(game)

    def test_itm_rejects_symlink_and_incomplete(self):
        with tempfile.TemporaryDirectory() as d:
            game=Path(d);root=game/'override';root.mkdir()
            (root/'STAF01.ITM').write_bytes(b'ITM V1  ')
            with self.assertRaises(p.Hold):p.static_item_preflight(game)

    def test_itm_static_only_never_grants_live(self):
        src=Path(p.__file__).read_text('utf-8')
        for key in ('engineCanEquipVerified=False',
                    'currentSessionActorKitVerified=False',
                    'HOLD_ITM_RESTRICTS_CLERIC',
                    'HOLD_ITM_RESTRICTS_TRUECLASS',
                    'HOLD_ITM_CURRENT_RESOURCE_SHA_DRIFT'):
            self.assertIn(key,src)

    def test_native_mock_result_never_claims_install(self):
        with tempfile.TemporaryDirectory() as d:
            game=Path(d)/'game';game.mkdir()
            class FakeBackend:
                TEMP_SOURCE_NAME='old.baf'
                def source_check(self,src,root): return None
                def checked_file(self,path,required=False):return path.read_bytes()
                class Hold(ValueError):pass
                def compile_readonly(self,root,src,compiler):
                    assert src.name=='BGXW39.baf'
                    assert self.TEMP_SOURCE_NAME==src.name
                    assert self.source_check(src,root)['blocks']==3
                    return {'status':'NATIVE_WEIDU_COMPILED_TEMP_ONLY',
                            'nativeSymbolsAcceptedByCompiler':True,
                            'watchedFilesChanged':False,'temporaryOutputRemoved':True,
                            'compiledSha256':'FAKE_TEST_ONLY','compilerSha256':'FAKE_TEST_ONLY'}
            backend=FakeBackend()
            class FakeHelper:
                def close_game_proof(self): pass
                def pinned_compiler(self,game):return game/'fake.exe'
                def load_backend(self,src):return backend
            with patch.object(p,'exact_v3_helper',return_value=FakeHelper()),\
                 patch.object(p,'static_item_preflight',return_value={'staticItemClassKitHeaderAllowed':True}):
                out=p.native_readonly(game,self.source,game/'helper',game/'backend')
            self.assertEqual(out['status'],'R39_NATIVE_EET_TEMP_COMPILE_PASS_NO_INSTALL')
            self.assertFalse(out['installed']);self.assertFalse(out['gameModified'])
            self.assertFalse(out['dispatchAuthorized']);self.assertFalse(out['liveXEquipTransferVerified'])
            self.assertEqual(backend.TEMP_SOURCE_NAME,'old.baf')

    def test_native_mock_compiles_even_if_item_race_unverified(self):
        with tempfile.TemporaryDirectory() as d:
            game=Path(d)/'game'; game.mkdir()
            class FakeBackend:
                TEMP_SOURCE_NAME='old.baf'
                class Hold(ValueError): pass
                def source_check(self,src,root):return None
                def checked_file(self,path,required=False):return path.read_bytes()
                def compile_readonly(self,root,src,compiler):
                    assert self.source_check(src,root)['blocks']==3
                    return {'status':'NATIVE_WEIDU_COMPILED_TEMP_ONLY',
                            'nativeSymbolsAcceptedByCompiler':True,
                            'watchedFilesChanged':False,'temporaryOutputRemoved':True}
            class FakeHelper:
                def close_game_proof(self):pass
                def pinned_compiler(self,game):return game/'fake.exe'
                def load_backend(self,src):return FakeBackend()
            with patch.object(p,'exact_v3_helper',return_value=FakeHelper()),\
                 patch.object(p,'static_item_preflight',side_effect=p.Hold('HOLD_ITM_RACE_RESTRICTIONS_UNVERIFIED:BYTE4_RACES=0x01')):
                out=p.native_readonly(game,self.source,game/'helper',game/'backend')
            self.assertEqual(out['status'],'R39_NATIVE_EET_TEMP_COMPILE_PASS_ITEM_HOLD_NO_INSTALL')
            self.assertTrue(out['nativeWeiDUCompileVerified'])
            self.assertFalse(out['itemStaticHeaderVerified'])
            self.assertFalse(out['armAuthorized'])
            self.assertFalse(out['dispatchAuthorized'])

    def test_native_mock_does_not_compile_if_itm_hash_changed(self):
        with tempfile.TemporaryDirectory() as d:
            game=Path(d)/'game';game.mkdir()
            class FakeHelper:
                def close_game_proof(self):pass
                def pinned_compiler(self,game):raise AssertionError('MUST_NOT_COMPILE')
                def load_backend(self,src):raise AssertionError('MUST_NOT_COMPILE')
            with patch.object(p,'exact_v3_helper',return_value=FakeHelper()),\
                 patch.object(p,'static_item_preflight',side_effect=p.Hold('HOLD_ITM_CURRENT_RESOURCE_SHA_DRIFT')):
                with self.assertRaisesRegex(p.Hold,'HOLD_ITM_CURRENT_RESOURCE_SHA_DRIFT'):
                    p.native_readonly(game,self.source,game/'helper',game/'backend')

    def test_native_mock_rejects_bad_report(self):
        with tempfile.TemporaryDirectory() as d:
            game=Path(d)/'game';game.mkdir()
            class FakeBackend:
                TEMP_SOURCE_NAME='old.baf'
                def source_check(self,src,root):return None
                def checked_file(self,path,required=False):return path.read_bytes()
                def compile_readonly(self,root,src,compiler):
                    return {'status':'NATIVE_WEIDU_COMPILED_TEMP_ONLY',
                            'nativeSymbolsAcceptedByCompiler':True,
                            'watchedFilesChanged':True,'temporaryOutputRemoved':True}
                class Hold(ValueError):pass
            class FakeHelper:
                def close_game_proof(self):pass
                def pinned_compiler(self,game):return game/'fake.exe'
                def load_backend(self,src):return FakeBackend()
            with patch.object(p,'exact_v3_helper',return_value=FakeHelper()),\
                 patch.object(p,'static_item_preflight',return_value={'staticItemClassKitHeaderAllowed':True}):
                out=p.native_readonly(game,self.source,game/'helper',game/'backend')
            self.assertEqual(out['status'],'HOLD_R39_NATIVE_EET_COMPILER')
            self.assertFalse(out['nativeWeiDUCompileVerified'])


if __name__=='__main__':unittest.main()
