# -*- coding: utf-8 -*-
"""Pure fixture + guarded game-write simulator. Never touches installed EET."""
import importlib.util
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent

def load(name):
    p=HERE/name
    spec=importlib.util.spec_from_file_location(name[:-3],p)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod

batch=load('weapon_names_batch_source.py')
cumulative=load('weapon_names_cumulative_source.py')
sha=lambda raw:hashlib.sha256(raw).hexdigest()

FIRST_LUA=(
    "-- Synthetic V160 fixture; no real user game files\n"
    +batch.OLD_NAMES
    +batch.END_NAMES
    +"\nfunction on_hit(context) return BG_EET_RU_V160_names.SW1H04 end\n"
    +"-- callback line unchanged: EEex_Sprite_AddAlterBaseWeaponDamageListener(\n"
).encode('utf-8')

class FakeItems:
    def __init__(self, resources):self.resources=dict(resources)
    def get(self,ref,ext):
        if ext!='.ITM' or ref not in self.resources:raise ValueError('FAKE_ITM_NOT_FOUND')
        return self.resources[ref],{'origin':'CURRENT_GAME_OVERRIDE'}

class CumulativeTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.game=self.root/'game';self.game.mkdir()
        self.work=self.root/'documents';self.work.mkdir()
        self.target=self.game/cumulative.MODULE_REL
        self.target.parent.mkdir(parents=True)
        (self.game/'chitin.key').write_bytes(b'KEY V1  TEST')
        self.first_entries={}
        self.resources={}
        for i in range(64):
            ref='S'+str(i).zfill(7)
            raw=('CURRENT_ITEM_BYTES_'+ref).encode('utf8')
            self.resources[ref]=raw
            self.first_entries[ref]={'name':'Боевой посох','origin':'CURRENT_GAME_OVERRIDE','sha256':sha(raw)}
        self.first_lua=batch.candidate_bytes(FIRST_LUA,self.first_entries,sha(FIRST_LUA))
        self.target.write_bytes(self.first_lua)
        first_backup_dir=self.work/'BG_EET_RU_V160_SAFE_BACKUP'/'FIRST_BATCH';first_backup_dir.mkdir(parents=True)
        self.first_backup=first_backup_dir/'BG_EET_RU_WeaponObserver.lua.before'
        self.first_backup.write_bytes(FIRST_LUA)
        self.extra={
            'BDASDAG1':('Кинжал',b'CURRENT_NEW_KNIFE'),
            'Z0CWBOWA':('Короткий лук',b'CURRENT_NEW_BOW'),
        }
        for ref,(name,raw) in self.extra.items():self.resources[ref]=raw
        self.reader=FakeItems(self.resources)
        pins={}
        for rel,data in [
          ('Baldur.exe',b'EXE_2.6.6'),('EEex.dll',b'EEex'),
          ('InfinityLoader.exe',b'loader'),('override/UI.MENU',b'UI MENU'),
          ('lang/ru_RU/dialog.tlk',b'RU_CURRENT_MALE'),
          ('lang/ru_RU/dialogf.tlk',b'RU_CURRENT_FEMALE')]:
            path=self.game/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data);pins[rel]=sha(data)
        weidu=b'WeiDU components frozen';(self.game/'WeiDU.log').write_bytes(weidu)
        self.first_state={
          'schema':cumulative.FIRST_STATE_SCHEMA,'phase':'INSTALLED',
          'backup':str(self.first_backup),'baselineSha':sha(FIRST_LUA),
          'candidateSha':sha(self.first_lua),'gamePins':pins,
          'weiduSha':sha(weidu),'itemPins':self.first_entries,
          'tlkSha256':{'dialog.tlk':pins['lang/ru_RU/dialog.tlk'],
                       'dialogf.tlk':pins['lang/ru_RU/dialogf.tlk']},
        }
        self.first_state_path=self.work/cumulative.FIRST_STATE
        self.first_state_path.write_text(json.dumps(self.first_state,ensure_ascii=False),encoding='utf8')
        self.first_state_bytes=self.first_state_path.read_bytes()
        self.catalog=self.catalog_for(self.extra)
        for obj,name,val in [(cumulative,'EXPECTED_FIRST_STATE_SHA',sha(self.first_state_bytes)),
                              (cumulative,'EXPECTED_FIRST_INSTALLED_SHA',sha(self.first_lua)),
                              (cumulative,'EXPECTED_V160_BASELINE_SHA',sha(FIRST_LUA))]:
            p=patch.object(obj,name,val);p.start();self.addCleanup(p.stop)
        p=patch.object(batch,'_check_game_closed',return_value=None);p.start();self.addCleanup(p.stop)

    def catalog_for(self, entries):
        items={}
        for ref,(name,raw) in entries.items():
            items[ref]={
              'status':'COMMON_RU_NAME_VERIFIED','autoDisplayName':name,
              'resourceSha256':sha(raw),'origin':'CURRENT_GAME_OVERRIDE',
              'itemTypeRaw':15,
              'unidentifiedRuByTlk':{'dialog.tlk':name,'dialogf.tlk':name},
              'identifiedRuByTlk':{'dialog.tlk':name,'dialogf.tlk':name},
            }
        pins=self.first_state['tlkSha256']
        return {'schema':'BG_EET_RU_REUSE_BGXAI_R3_V111_NAMES_RO_V1',
                'status':'READ_ONLY_SOURCE_CATALOG','gameFilesWritten':0,
                'engineListenersAdded':0,'combatLogRowJoinVerified':False,
                'tlkSha256':pins,'items':items}

    def call(self,mode,typed=None,catalog=None):
        return cumulative.run(mode,self.game,self.work,batch,
                              self.catalog if catalog is None else catalog,
                              self.reader,typed=typed,allow_non_windows_test=True)

    def install(self):
        return self.call('install',cumulative.APPROVE_INSTALL)

    def test_seed_64_disjoint_from_deployed_fixture(self):
        refs=cumulative.HISTORICAL_SECOND_SEEDS_64
        self.assertEqual(len(refs),64)
        self.assertEqual(len(set(refs)),64)
        self.assertIn('BDASDAG1',refs)
        self.assertIn('Z0CWBOWA',refs)
        self.assertFalse(set(refs)&set(batch.HISTORICAL_WEAPON_SEEDS_64))
        for ref in refs:self.assertRegex(ref,cumulative.REF_RE)

    def test_candidate_byte_exact_only_adds_two_lines(self):
        new=batch.validate_catalog(self.catalog)['entries']
        candidate=cumulative.compose_next(self.first_lua,self.first_state,new,batch)
        lines=b''.join(cumulative._line(k,new[k]['name']) for k in sorted(new))
        self.assertEqual(candidate.replace(lines,b'',1),self.first_lua)
        self.assertIn(b'BG_EET_RU_V160_names',candidate)
        self.assertEqual(candidate.count(b'EEex_Sprite_AddAlterBaseWeaponDamageListener('),1)

    def test_preflight_has_zero_file_writes(self):
        prev=self.first_lua
        report=self.call('preflight')
        self.assertEqual(report['status'],'CUMULATIVE_PREFLIGHT_PASS')
        self.assertEqual(report['newCount'],2)
        self.assertEqual(report['oldCount'],64)
        self.assertEqual(report['totalExtendedNames'],66)
        self.assertEqual(report['gameFilesWritten'],0)
        self.assertEqual(self.target.read_bytes(),prev)
        self.assertEqual(self.first_state_path.read_bytes(),self.first_state_bytes)
        self.assertFalse((self.work/cumulative.SECOND_STATE).exists())

    def test_status_not_installed(self):
        self.assertEqual(self.call('status')['status'],'CUMULATIVE_NOT_INSTALLED')

    def test_no_typed_word_no_writes(self):
        result=self.call('install','NOT_APPROVED')
        self.assertEqual(result['status'],'CUMULATIVE_SAFE_STOP')
        self.assertEqual(self.target.read_bytes(),self.first_lua)
        self.assertFalse((self.work/cumulative.SECOND_STATE).exists())

    def test_install_writes_one_lua_and_keeps_old_receipt(self):
        result=self.install()
        self.assertEqual(result['status'],'CUMULATIVE_INSTALLED_AWAITING_GAMEPLAY')
        self.assertEqual(result['newNamesAdded'],2)
        self.assertEqual(result['gameFilesWritten'],1)
        self.assertEqual(result['newNativeHooks'],0)
        self.assertEqual(result['retainedPriorNames'],64)
        self.assertEqual(self.first_state_path.read_bytes(),self.first_state_bytes)
        self.assertEqual(self.first_backup.read_bytes(),FIRST_LUA)
        second=json.loads((self.work/cumulative.SECOND_STATE).read_text('utf8'))
        self.assertEqual(second['phase'],'INSTALLED')
        self.assertEqual(second['baselineSha'],sha(self.first_lua))
        self.assertEqual(second['candidateSha'],sha(self.target.read_bytes()))
        self.assertEqual(len(second['itemPins']),66)
        self.assertEqual(Path(second['backup']).read_bytes(),self.first_lua)

    def test_rollback_restores_first_64_not_original_v160(self):
        self.install()
        result=self.call('rollback',cumulative.APPROVE_ROLLBACK)
        self.assertEqual(result['status'],'CUMULATIVE_ROLLED_BACK_TO_FIRST64')
        self.assertEqual(result['gameFilesWritten'],1)
        self.assertEqual(self.target.read_bytes(),self.first_lua)
        self.assertNotEqual(self.target.read_bytes(),FIRST_LUA)
        self.assertEqual(self.first_state_path.read_bytes(),self.first_state_bytes)
        self.assertEqual(json.loads((self.work/cumulative.SECOND_STATE).read_text(encoding='utf-8'))['phase'],'ROLLED_BACK')

    def test_no_repeat_after_first_install(self):
        self.install()
        second=self.install()
        self.assertEqual(second['status'],'CUMULATIVE_SAFE_STOP')
        self.assertIn('SECOND_STATE_ALREADY_EXISTS',second['reason'])

    def test_state_prepared_before_swap_rollback_changes_zero(self):
        self.install()
        state_path=self.work/cumulative.SECOND_STATE
        state=json.loads(state_path.read_text('utf8'))
        state['phase']='PREPARED';state_path.write_text(json.dumps(state),encoding='utf8')
        self.target.write_bytes(self.first_lua)
        report=self.call('rollback',cumulative.APPROVE_ROLLBACK)
        self.assertEqual(report['status'],'CUMULATIVE_ROLLED_BACK_TO_FIRST64')
        self.assertEqual(report['gameFilesWritten'],0)

    def test_state_prepared_after_swap_rollback_changes_one(self):
        self.install()
        state_path=self.work/cumulative.SECOND_STATE
        state=json.loads(state_path.read_text('utf8'))
        state['phase']='PREPARED';state_path.write_text(json.dumps(state),encoding='utf8')
        report=self.call('rollback',cumulative.APPROVE_ROLLBACK)
        self.assertEqual(report['gameFilesWritten'],1)
        self.assertEqual(self.target.read_bytes(),self.first_lua)

    def test_changed_first_receipt_halts(self):
        self.first_state_path.write_bytes(self.first_state_bytes+b' ')
        self.assertIn('FIRST_V162_STATE_SHA_CHANGED',self.call('preflight')['reason'])

    def test_changed_old_itm_halts(self):
        self.reader.resources['S0000003']=b'ATTACKER_REPLACED_OLD_ITM'
        self.assertIn('CURRENT_GAME_ITM_SHA_OR_ORIGIN_CHANGED',self.call('preflight')['reason'])

    def test_changed_new_itm_halts(self):
        self.reader.resources['BDASDAG1']=b'ATTACKER_REPLACED_NEW_ITM'
        self.assertIn('CURRENT_GAME_ITM_SHA_OR_ORIGIN_CHANGED',self.call('preflight')['reason'])

    def test_changed_tlk_halts(self):
        (self.game/'lang/ru_RU/dialogf.tlk').write_bytes(b'ENGLISH')
        self.assertIn('FIRST_GAME_PIN_DRIFT',self.call('preflight')['reason'])

    def test_changed_weidu_halts(self):
        (self.game/'WeiDU.log').write_bytes(b'REORDERED COMPONENTS')
        self.assertIn('FIRST_WEIDU_LOG_CHANGED',self.call('preflight')['reason'])

    def test_changed_game_pin_halts(self):
        (self.game/'EEex.dll').write_bytes(b'DRIFTED')
        self.assertIn('FIRST_GAME_PIN_DRIFT',self.call('preflight')['reason'])

    def test_changed_installed_lua_halts(self):
        self.target.write_bytes(self.first_lua+b'-- DRIFT')
        self.assertIn('CURRENT_GAME_LUA_NOT_FIRST64',self.call('preflight')['reason'])

    def test_first64_overlap_halts(self):
        raw=self.reader.resources['S0000001']
        test=self.catalog_for({'S0000001':('Боевой посох',raw)})
        self.assertIn('NEW_BATCH_REPEATS_FIRST64',self.call('preflight',catalog=test)['reason'])

    def test_ru_lua_syntax_injection_halts(self):
        test=self.catalog_for({'BDASDAG1':("Кинжал'; os.execute('bad')",b'CURRENT_NEW_KNIFE')})
        self.assertEqual(self.call('preflight',catalog=test)['status'],'CUMULATIVE_SAFE_STOP')

    def test_missing_first_v160_backup_halts(self):
        self.first_backup.unlink()
        self.assertIn('FIRST_V162_EXTERNAL_BACKUP_MISSING',self.call('preflight')['reason'])

    def test_rollback_must_be_last_only(self):
        self.install()
        self.target.write_bytes(self.target.read_bytes()+b'--newer third-party module')
        self.assertIn('CUMULATIVE_NOT_LAST_MODIFICATION',self.call('rollback',cumulative.APPROVE_ROLLBACK)['reason'])

    def test_rollback_rejects_replaced_backup(self):
        self.install()
        state=json.loads((self.work/cumulative.SECOND_STATE).read_text('utf8'))
        Path(state['backup']).write_bytes(b'WRONG BACKUP')
        self.assertIn('CUMULATIVE_BACKUP_SHA_DRIFT',self.call('rollback',cumulative.APPROVE_ROLLBACK)['reason'])

    def test_rollback_without_typed_approval_never_rewrites(self):
        self.install()
        before=self.target.read_bytes()
        self.assertIn('CUMULATIVE_ROLLBACK_APPROVAL_REQUIRED',self.call('rollback','')['reason'])
        self.assertEqual(before,self.target.read_bytes())

    def test_new_state_schema_drift_blocks_rollback(self):
        self.install()
        p=self.work/cumulative.SECOND_STATE
        d=json.loads(p.read_text(encoding='utf-8'));d['schema']='FAKE';p.write_text(json.dumps(d))
        self.assertIn('CUMULATIVE_ROLLBACK_RECEIPT_DRIFT',self.call('rollback',cumulative.APPROVE_ROLLBACK)['reason'])

    def test_second_state_symlink_blocks_preflight(self):
        p=self.work/cumulative.SECOND_STATE
        dest=self.work/'other';dest.write_text('safe')
        try:p.symlink_to(dest)
        except OSError:self.skipTest('Windows symlink privileges not granted')
        self.assertIn('SECOND_STATE_ALREADY_EXISTS',self.call('preflight')['reason'])

    def test_first_lua_old_names_unchanged(self):
        self.install()
        self.assertEqual(self.target.read_bytes().count(batch.OLD_NAMES.encode('utf8')),1)
        self.assertEqual(self.first_state_path.read_bytes(),self.first_state_bytes)

if __name__=='__main__':unittest.main()