import hashlib
import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

SRC=Path(__file__).with_name('BG_EET_RU_ITEM_NAMES_FROM_BGXAI_R3_RO.py')
spec=importlib.util.spec_from_file_location('catalog', SRC)
catalog=importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog)


def itm(a,b,itype=5):
    raw=bytearray(114);raw[:8]=b'ITM V1  '
    struct.pack_into('<II',raw,8,a,b)
    struct.pack_into('<H',raw,0x1c,itype)
    return bytes(raw)

class FakeSource:
    def __init__(self, resources):self.resources=resources
    def get(self,name,ext):
        if name not in self.resources:raise ValueError('ITM_MISSING')
        return self.resources[name],{'origin':'CURRENT_GAME_BIFF'}

class ExistingV111:
    @staticmethod
    def v111_parse_itm(raw):
        if len(raw)<114 or raw[:8]!=b'ITM V1  ':raise ValueError('ITM_INVALID')
        a,b=struct.unpack_from('<II',raw,8)
        return {'unidentified_name_strref':a,'identified_name_strref':b,
                'item_type_id':struct.unpack_from('<H',raw,0x1c)[0],
                'item_type_category':'ARROWS'}
    def __init__(self,dialog=None,dialogf=None):
        self.name_map={'dialog.tlk':dialog or {},'dialogf.tlk':dialogf or {}}
    def v111_tlk_names(self,game,refs,name):
        rows=self.name_map[name]
        return {'status':'V111_TLK_READ_ONLY','tlk_sha256':'0123'*16,
                'entries':{str(n): {'status':'TEXT_READ','text':rows[n]} if n in rows else
                            {'status':'TLK_NO_TEXT'} for n in refs}}

class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.v111=ExistingV111(
            {10:'Стрела',11:'Отличная стрела',12:'Короткий лук',13:'Длинный меч'},
            {10:'Стрела',11:'Отличная стрела',12:'Короткий лук',13:'Длинный меч'})
        self.src=FakeSource({'AROW01':itm(11,10),'BOW05':itm(12,12,15),
                            'SW1H04':itm(13,13,20)})
    def run_catalog(self,names=None,v111=None,source=None):
        return catalog.catalog_from_modules(self.root,(['AROW01','BOW05','SW1H04'] if names is None else names),
              SimpleNamespace(),v111 or self.v111,source or self.src)
    def test_arrow_identified_ambiguity_fails_closed(self):
        r=self.run_catalog();a=r['items']['AROW01']
        self.assertEqual(a['status'],'NAME_OR_IDENTIFICATION_HOLD')
        self.assertIsNone(a['autoDisplayName'])
        self.assertEqual(a['identifiedRuByTlk']['dialog.tlk'],'Стрела')
        self.assertEqual(a['unidentifiedRuByTlk']['dialog.tlk'],'Отличная стрела')
    def test_common_russian_item_name_allowed(self):
        r=self.run_catalog()
        self.assertEqual(r['items']['BOW05']['autoDisplayName'],'Короткий лук')
        self.assertEqual(r['items']['SW1H04']['autoDisplayName'],'Длинный меч')
        self.assertEqual(r['autoDisplayNamesReady'],2)
        self.assertFalse(r['combatLogRowJoinVerified'])
        self.assertEqual(r['engineListenersAdded'],0)
        self.assertEqual(r['gameFilesWritten'],0)
    def test_tlk_gender_variants_not_collapsed(self):
        v=ExistingV111({12:'Короткий лук'},{12:'Короткая лука'})
        self.assertIsNone(self.run_catalog(['BOW05'],v)['items']['BOW05']['autoDisplayName'])
    def test_non_russian_label_not_assumed_ru(self):
        v=ExistingV111({12:'Short Bow'},{12:'Short Bow'})
        self.assertIsNone(self.run_catalog(['BOW05'],v)['items']['BOW05']['autoDisplayName'])
    def test_missing_resource_isolated(self):
        r=self.run_catalog(['SW1H04','MISSING'])
        self.assertEqual(r['items']['MISSING']['status'],'ITEM_HOLD')
        self.assertEqual(r['items']['SW1H04']['status'],'COMMON_RU_NAME_VERIFIED')
    def test_corrupted_itm_fails_closed(self):
        src=FakeSource({'BOW05':b'INVALID'})
        self.assertEqual(self.run_catalog(['BOW05'],source=src)['items']['BOW05']['status'],'ITEM_HOLD')
    def test_count_and_resref_guard(self):
        for refs in ([],['AROW01']*65,['../ITM'],['lowcase'],['AROW-01'],[None]):
            with self.subTest(refs=refs[:2]):
                with self.assertRaises(catalog.SourceHold):self.run_catalog(refs)
    def test_names_are_deduplicated(self):
        self.assertEqual(len(self.run_catalog(['BOW05','BOW05'])['items']),1)
    def test_no_control_in_display(self):
        v=ExistingV111({12:'Лук\nподмена'},{12:'Лук\nподмена'})
        self.assertIsNone(self.run_catalog(['BOW05'],v)['items']['BOW05']['autoDisplayName'])
    def test_blob_integrity_before_code_execution(self):
        p=self.root/'safe.py';p.write_text('MARK = 42\n')
        data=p.read_bytes()
        sha=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        self.assertEqual(catalog.verified_module(self.root,'safe.py',sha).MARK,42)
        with self.assertRaises(catalog.SourceHold):catalog.verified_module(self.root,'safe.py','0'*40)
    def test_symlink_rejected(self):
        p=self.root/'safe.py';p.write_text('MARK = 42\n')
        alias=self.root/'alias.py';alias.symlink_to(p)
        with self.assertRaises(catalog.SourceHold):catalog.verified_module(self.root,'alias.py','0'*40)
    def test_source_has_no_game_mutation_api(self):
        code=SRC.read_text(encoding='utf-8')
        for forbidden in ('Infinity_DisplayString','XEquipItem(','.write_bytes(','.write_text(',"open('w'", "open('a'"):
            self.assertNotIn(forbidden,code)

if __name__=='__main__':unittest.main()
