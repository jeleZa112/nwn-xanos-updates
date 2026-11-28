# -*- coding: utf-8 -*-
"""SOURCE-ONLY model tests: no writes to a real game or to user's CMD."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SRC=Path(__file__).with_name('weapon_names_batch_source.py')
spec=importlib.util.spec_from_file_location('names_batch',SRC)
batch=importlib.util.module_from_spec(spec);spec.loader.exec_module(batch)


def sha(x):return hashlib.sha256(x).hexdigest()

ORIGINAL=(
    "-- V108 installed and V160 LIVE observer\n"
    "local BG_EET_RU_V160_names = {\n"
    "    SW1H04='Длинный меч',\n"
    "    AROW01='Стрела',\n"
    "    BOW05='Короткий лук',\n"
    "}\n"
    "local function BG_EET_RU_V160_ref(item) return nil end\n"
    "function BG_EET_RU_WEAPON_EVENT_OBSERVER_V1_OnBaseDamage(context)\n"
    "  local weapon = BG_EET_RU_V160_names['BOW05']\n"
    "  return weapon\n"
    "end\n"
).encode('utf-8')

class FakeItems:
    def __init__(self, resources):self.resources=resources
    def get(self,ref,ext):
        if ext!='.ITM' or ref not in self.resources:raise ValueError('ITM_MISSING')
        return self.resources[ref],{'origin':'CURRENT_GAME_OVERRIDE'}


def catalog(items):
    names={}
    for key,(data,ru,origin) in items.items():
        names[key]={
            'status':'COMMON_RU_NAME_VERIFIED','autoDisplayName':ru,
            'resourceSha256':sha(data),'origin':origin,
            'itemTypeRaw':26 if key == 'STAF01' else 25,
            'unidentifiedRuByTlk':{'dialog.tlk':ru,'dialogf.tlk':ru},
            'identifiedRuByTlk':{'dialog.tlk':ru,'dialogf.tlk':ru}}
    return {
        'schema':'BG_EET_RU_REUSE_BGXAI_R3_V111_NAMES_RO_V1',
        'status':'READ_ONLY_SOURCE_CATALOG','gameFilesWritten':0,
        'engineListenersAdded':0,'combatLogRowJoinVerified':False,
        'autoDisplayNamesReady':len(names),
        'tlkSha256':{'dialog.tlk':'0'*64,'dialogf.tlk':'1'*64},
        'items':names}

class BatchTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.game=self.root/'game';self.game.mkdir()
        self.work=self.root/'documents';self.work.mkdir()
        self.target=self.game/batch.MODULE_REL
        self.target.parent.mkdir(parents=True)
        self.target.write_bytes(ORIGINAL)
        (self.game/'chitin.key').write_bytes(b'KEYV1')
        (self.game/'WeiDU.log').write_bytes(b'// previous mod install\n'*30)
        self.data={'STAF01':(b'ITM-current-game-sha-bytes','Боевой посох','CURRENT_GAME_OVERRIDE'),
                   'AX1H01':(b'ITM-historical-current','Боевой топор','CURRENT_GAME_OVERRIDE')}
        self.catalog=catalog(self.data)
        self.reader=FakeItems({ref:entry[0] for ref,entry in self.data.items()})
        for name,value in [('dialog.tlk',b'CURRENT_RU_MALE'),('dialogf.tlk',b'CURRENT_RU_FEMALE')]:
            p=self.game/'lang'/'ru_RU'/name
            p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(value)
            self.catalog['tlkSha256'][name]=sha(value)
        pins={}
        for rel in ['Baldur.exe','EEex.dll','InfinityLoader.exe']:
            p=self.game/rel;p.write_bytes(rel.encode('utf8'));pins[rel]=sha(p.read_bytes())
        self.pins=pins
        self.v160_state=self.work/batch.V160_STATE
        self.v160_state.write_text(json.dumps({
          'schema':'BG_EET_RU_V160_HIT_ONLY_GUARDED_V1',
          'phase':'INSTALLED','candidate_sha256':sha(ORIGINAL),
          'pinned_game_hashes':self.pins}),encoding='utf-8')
        p=patch.object(batch,'EXPECTED_USER_V160_SHA',sha(ORIGINAL));p.start();self.addCleanup(p.stop)

    def call(self,mode,typed=None):
        return batch.run(mode,self.game,self.work,self.catalog,self.reader,self.pins,typed)

    def test_real_v160_append_anchor_without_new_hook(self):
        # Do not replace the pinned file; only check its existing dictionary.
        original_src = Path(__file__).with_name('BG_EET_RU_V160_HIT_ONLY_APPEND.lua')
        if not original_src.is_file():
            self.skipTest('Original V160 source absent in standalone fixture')
        raw=original_src.read_bytes().replace(b'\r\n',b'\n')
        self.assertEqual(raw.count(batch.OLD_NAMES.encode('utf8')),1)
        self.assertEqual(raw.count(batch.END_NAMES.encode('utf8')),1)
        self.assertEqual(raw.count(b'BG_EET_RU_V160_names'),2)
        x=batch.candidate_bytes(raw,batch.validate_catalog(self.catalog)['entries'],sha(raw))
        self.assertEqual(x.count(b'EEex_Sprite_AddAlterBaseWeaponDamageListener('),
                         raw.count(b'EEex_Sprite_AddAlterBaseWeaponDamageListener('))
        self.assertIn('Боевой посох'.encode('utf-8'),x)

    def test_more_than_64_items_holds(self):
        x=catalog(self.data)
        for i in range(63):
            key=f'A{i:07d}'
            x['items'][key]={**x['items']['STAF01']}
        with self.assertRaisesRegex(batch.SafeStop,'CATALOG_ITEM_COUNT_UNSAFE'):
            batch.validate_catalog(x)

    def test_historical_seed_candidates_are_not_names_or_runtime_proof(self):
        seeds=batch.HISTORICAL_WEAPON_SEEDS_64
        self.assertEqual(len(seeds),64)
        self.assertEqual(len(set(seeds)),64)
        self.assertIn('STAF01',seeds)
        self.assertIn('DAGG01',seeds)
        self.assertIn('AROW02',seeds)
        for ref in seeds:
            self.assertRegex(ref,batch.RESREF_RE)
        # Seed list never unlocks any Lua insertion without current catalog.
        with self.assertRaises(batch.SafeStop):
            batch.validate_catalog({'items':{ref:{} for ref in seeds}})

    def test_patch_preserves_all_existing_code(self):
        names=batch.validate_catalog(self.catalog)
        x=batch.candidate_bytes(ORIGINAL,names['entries'],sha(ORIGINAL))
        self.assertIn(b"    STAF01='"+'Боевой посох'.encode()+b"',",x)
        self.assertIn(b"    AX1H01='"+'Боевой топор'.encode()+b"',",x)
        self.assertEqual(x.replace(b"    AX1H01='"+'Боевой топор'.encode()+b"',\n",b'').replace(b"    STAF01='"+'Боевой посох'.encode()+b"',\n",b''),ORIGINAL)
        self.assertEqual(x.count(b'BG_EET_RU_V160_names'),ORIGINAL.count(b'BG_EET_RU_V160_names'))

    def test_preflight_has_zero_writes(self):
        original=self.target.read_bytes()
        result=self.call('preflight')
        self.assertEqual(result['status'],'BATCH_PREFLIGHT_PASS')
        self.assertEqual(result['namesToAdd'],['AX1H01','STAF01'])
        self.assertEqual(self.target.read_bytes(),original)
        self.assertFalse((self.work/batch.STATE_NAME).exists())

    def test_install_untyped_blocked_without_external_backup(self):
        r=self.call('install','NO')
        self.assertEqual(r['status'],'BATCH_SAFE_STOP')
        self.assertEqual(self.target.read_bytes(),ORIGINAL)
        self.assertFalse((self.work/batch.STATE_NAME).exists())
        self.assertFalse((self.work/'BG_EET_RU_V160_SAFE_BACKUP').exists())

    def test_install_and_rollback_restore_v160_and_original_v160_state(self):
        v160state=self.v160_state.read_bytes()
        self.assertEqual(self.call('install',batch.APPROVE_INSTALL)['status'],'BATCH_INSTALLED_AWAITING_GAMEPLAY')
        installed=self.target.read_bytes()
        self.assertNotEqual(installed,ORIGINAL)
        self.assertEqual(self.call('status')['status'],'BATCH_INSTALLED_SOURCE_ONLY')
        self.assertEqual(self.v160_state.read_bytes(),v160state)
        self.assertEqual(self.call('rollback','WRONG')['status'],'BATCH_SAFE_STOP')
        self.assertEqual(self.target.read_bytes(),installed)
        self.assertEqual(self.call('rollback',batch.APPROVE_ROLLBACK)['status'],'BATCH_ROLLED_BACK_TO_V160')
        self.assertEqual(self.target.read_bytes(),ORIGINAL)
        self.assertEqual(self.v160_state.read_bytes(),v160state)

    def test_refuse_v160_wrong_installed_sha(self):
        self.target.write_bytes(ORIGINAL+b'CHANGED')
        self.assertEqual(self.call('preflight')['status'],'BATCH_SAFE_STOP')

    def test_refuse_v160_uninstalled_or_wrong_state(self):
        self.v160_state.write_text(json.dumps({'schema':'BAD','phase':'INSTALLED'}),encoding='utf-8')
        self.assertEqual(self.call('preflight')['status'],'BATCH_SAFE_STOP')

    def test_tlk_drift_rejected_before_backup(self):
        (self.game/'lang'/'ru_RU'/'dialog.tlk').write_bytes(b'new')
        self.assertEqual(self.call('install',batch.APPROVE_INSTALL)['status'],'BATCH_SAFE_STOP')
        self.assertEqual(self.target.read_bytes(),ORIGINAL)
        self.assertFalse((self.work/batch.STATE_NAME).exists())

    def test_item_drift_rejected_before_backup(self):
        self.reader.resources['STAF01']=b'NEW_GAME_ITEM'
        self.assertEqual(self.call('install',batch.APPROVE_INSTALL)['status'],'BATCH_SAFE_STOP')
        self.assertFalse((self.work/batch.STATE_NAME).exists())

    def test_rollback_last_only_catches_drift(self):
        self.assertEqual(self.call('install',batch.APPROVE_INSTALL)['status'],'BATCH_INSTALLED_AWAITING_GAMEPLAY')
        self.target.write_bytes(self.target.read_bytes()+b'CHANGED_BY_ANOTHER_MOD')
        self.assertEqual(self.call('rollback',batch.APPROVE_ROLLBACK)['status'],'BATCH_SAFE_STOP')
        self.assertIn(b'CHANGED',self.target.read_bytes())

    def test_roll_back_weidu_drift_blocked(self):
        self.assertEqual(self.call('install',batch.APPROVE_INSTALL)['status'],'BATCH_INSTALLED_AWAITING_GAMEPLAY')
        self.game.joinpath('WeiDU.log').write_bytes(b'CHANGED')
        self.assertEqual(self.call('rollback',batch.APPROVE_ROLLBACK)['status'],'BATCH_SAFE_STOP')

    def test_no_second_stateful_install(self):
        self.assertEqual(self.call('install',batch.APPROVE_INSTALL)['status'],'BATCH_INSTALLED_AWAITING_GAMEPLAY')
        self.assertEqual(self.call('install',batch.APPROVE_INSTALL)['status'],'BATCH_SAFE_STOP')

    def test_false_russian_identifier_and_lua_injection_rejected(self):
        for bad in ("Игла\\' os.execute('x')", 'AX\n1', 'A'*120, 'Knife', 'кинжал; io.open'):
            mutated=catalog(self.data)
            mutated['items']['STAF01']['autoDisplayName']=bad
            mutated['items']['STAF01']['unidentifiedRuByTlk']={'dialog.tlk':bad,'dialogf.tlk':bad}
            mutated['items']['STAF01']['identifiedRuByTlk']={'dialog.tlk':bad,'dialogf.tlk':bad}
            with self.subTest(bad=bad),self.assertRaises(batch.SafeStop):batch.validate_catalog(mutated)

    def test_identification_or_gender_mismatch_rejected(self):
        for variant in ('identifiedRuByTlk','unidentifiedRuByTlk'):
            mutated=catalog(self.data)
            mutated['items']['STAF01'][variant]['dialogf.tlk']='Посох'
            with self.subTest(variant=variant),self.assertRaises(batch.SafeStop):batch.validate_catalog(mutated)

    def test_non_weapon_item_type_not_added(self):
        x=catalog(self.data)
        x['items']['STAF01']['itemTypeRaw']=10  # non-weapon in fixture
        with self.assertRaisesRegex(batch.SafeStop,'CATALOG_NOT_A_WEAPON_OR_AMMO'):
            batch.validate_catalog(x)

    def test_arrow_original_mapping_unchanged(self):
        x=catalog({**self.data,'AROW01':(b'arrows','Стрела','CURRENT_GAME_OVERRIDE')})
        names=batch.validate_catalog(x)
        self.assertNotIn('AROW01',names['entries'])

    def test_64_item_and_current_tlk_requirements(self):
        self.catalog['tlkSha256']['dialogf.tlk']='bad'
        with self.assertRaises(batch.SafeStop):batch.validate_catalog(self.catalog)
        self.assertEqual(self.call('preflight')['status'],'BATCH_SAFE_STOP')


    def test_v160_pin_subset_rejected(self):
        state=json.loads(self.v160_state.read_text(encoding='utf8'))
        state['pinned_game_hashes']={'Baldur.exe':self.pins['Baldur.exe']}
        self.v160_state.write_text(json.dumps(state),encoding='utf8')
        self.assertEqual(self.call('preflight')['status'],'BATCH_SAFE_STOP')

    def test_prepared_state_can_be_cancelled_without_touching_game(self):
        self.assertEqual(self.call('install',batch.APPROVE_INSTALL)['status'],'BATCH_INSTALLED_AWAITING_GAMEPLAY')
        state_path=self.work/batch.STATE_NAME
        row=json.loads(state_path.read_text(encoding='utf8'))
        row['phase']='PREPARED'
        state_path.write_text(json.dumps(row),encoding='utf8')
        # Simulate crash before swap: V160 still installed.
        self.target.write_bytes(ORIGINAL)
        result=self.call('rollback',batch.APPROVE_ROLLBACK)
        self.assertEqual(result['status'],'BATCH_ROLLED_BACK_TO_V160')
        self.assertEqual(result['gameFilesWritten'],0)
        self.assertEqual(self.target.read_bytes(),ORIGINAL)

    def test_prepared_after_swap_recovers_exact_v160(self):
        self.assertEqual(self.call('install',batch.APPROVE_INSTALL)['status'],'BATCH_INSTALLED_AWAITING_GAMEPLAY')
        state_path=self.work/batch.STATE_NAME
        row=json.loads(state_path.read_text(encoding='utf8'))
        row['phase']='PREPARED'
        state_path.write_text(json.dumps(row),encoding='utf8')
        result=self.call('rollback',batch.APPROVE_ROLLBACK)
        self.assertEqual(result['status'],'BATCH_ROLLED_BACK_TO_V160')
        self.assertEqual(result['gameFilesWritten'],1)
        self.assertEqual(self.target.read_bytes(),ORIGINAL)

    def test_no_game_cli_or_new_listener(self):
        source=SRC.read_text(encoding='utf-8')
        self.assertIn('SOURCE_ONLY:',source)
        self.assertNotIn('def main(',source)
        self.assertEqual(source.count('EEex_Sprite_AddAlterBaseWeaponDamageListener('),2)  # string-only invariant checks
        self.assertIn('EXTERNAL_WORKDIR_REQUIRED',source)

if __name__ == '__main__':unittest.main(verbosity=2)