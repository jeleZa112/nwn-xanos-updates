# -*- coding: utf-8 -*-
"""No real game, no native DLL load; exact Lua+Python synthetic pilot gates."""
import hashlib
import importlib.util
import pathlib
import tempfile
import unittest
from unittest.mock import patch
from lupa import LuaRuntime

ROOT=pathlib.Path(__file__).parent
P=ROOT/'V165_ONE_ITEM_DUAL_PILOT.py'
SPEC=importlib.util.spec_from_file_location('v165_dual',P)
pilot=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pilot)
V107=(ROOT/'BG_EET_RU_V107_GUARDED_CALLBACK_SOURCE_ONLY.lua').read_bytes()

BASE="""local BG_EET_RU_V160_names={ AROW01='Стрела', BOW05='Короткий лук' }
local function BG_EET_RU_V160_ref(item)
 if not item then return nil end
 return item.cResRef:get()
end
local function BG_EET_RU_V160_name(ref)
 return BG_EET_RU_V160_names[ref] or ('код '..tostring(ref))
end
function BG_EET_RU_WEAPON_EVENT_OBSERVER_V1_OnBaseDamage(context)
 local weapon=BG_EET_RU_V160_ref(context.weapon)
 local launcher=BG_EET_RU_V160_ref(context.launcher)
 local label='Оружие при попадании: '..BG_EET_RU_V160_name(weapon)
 if launcher then label=label..' ('..BG_EET_RU_V160_name(launcher)..')' end
 return label
end
""".encode('utf-8')
PAIR={'identified':'Стрела','unidentified':'Отличная стрела'}


class Ref:
    def __init__(self,val):self.val=val
    def get(self,*args):return self.val

class Item:
    def __init__(self,ref,flags):
        self.cResRef=Ref(ref)
        self.m_flags=flags


class PilotTests(unittest.TestCase):
    def make(self,pair=None,source=BASE):
        with patch.object(pilot,'EXPECTED_V163_SHA',hashlib.sha256(source).hexdigest()):
            return pilot.compose(source,PAIR if pair is None else pair,V107)

    def test_exact_v107_reuse_one_existing_callback_and_cyrillic_names(self):
        raw=self.make()
        self.assertIn(b'BG_EET_RU_V107_ResolveName',raw)
        self.assertEqual(raw.count(b'function BG_EET_RU_WEAPON_EVENT_OBSERVER_V1_OnBaseDamage(context)'),1)
        executable=b'\n'.join(line for line in raw.splitlines() if not line.lstrip().startswith(b'--'))
        self.assertNotIn(b'EEex_Sprite_AddAlterBaseWeaponDamageListener(',executable)
        lua=LuaRuntime(unpack_returned_tuples=True)
        lua.execute('EEex_IsBitSet=function(flags,n) return (flags % (2^(n+1))) >= (2^n) end')
        lua.execute(raw.decode('utf-8'))
        cb=lua.globals().BG_EET_RU_WEAPON_EVENT_OBSERVER_V1_OnBaseDamage
        def call(ref,flags,launcher=None):
            return cb(lua.table_from({'weapon':Item(ref,flags),'launcher':launcher}))
        self.assertEqual(call('AROW01',0),'Оружие при попадании: Отличная стрела')
        self.assertEqual(call('AROW01',1),'Оружие при попадании: Стрела')
        self.assertEqual(call('AROW01',2),'Оружие при попадании: Отличная стрела')
        self.assertEqual(call('AROW01',3),'Оружие при попадании: Стрела')
        self.assertEqual(call('AROW01',None),'Оружие при попадании: Стрела')
        self.assertEqual(call('BOW05',0),'Оружие при попадании: Короткий лук')
        self.assertEqual(call('AROW01',0,Item('BOW05',1)),
                         'Оружие при попадании: Отличная стрела (Короткий лук)')

    def test_modifying_prior_v163_lua_must_stop(self):
        with self.assertRaises(pilot.Hold):
            pilot.compose(BASE+b'--drift',PAIR,V107)
        with patch.object(pilot,'EXPECTED_V163_SHA',pilot.digest(BASE)):
            with self.assertRaises(pilot.Hold):
                pilot.compose(BASE.replace(b'BG_EET_RU_V160_name(weapon)',b'NEW_NAME(weapon)'),PAIR,V107)
            with self.assertRaises(pilot.Hold):
                pilot.compose(BASE,PAIR,b'-- fake')
            with self.assertRaises(pilot.Hold):
                pilot.compose(BASE.replace(b'BG_EET_RU_V160_name(launcher)',
                                           b'BG_EET_RU_V160_name(launcher) '*2),PAIR,V107)

    def test_no_name_guess_missing_current_itm_tlk(self):
        catalog={'schema':'BG_EET_RU_REUSE_BGXAI_R3_V111_NAMES_RO_V1',
                 'status':'READ_ONLY_SOURCE_CATALOG',
                 'gameFilesWritten':0,'engineListenersAdded':0,
                 'tlkSha256':{'dialog.tlk':'0'*64,'dialogf.tlk':'1'*64},
                 'items':{'AROW01':{'itemTypeRaw':5,'resourceSha256':'2'*64}}}
        class Bridge:
            @staticmethod
            def dual_russian_names_source_only(cat):
                return {'gameFilesWritten':0,'engineListenersAdded':0,
                        'tlkSha256':cat['tlkSha256'],'pairs':{}}
        with self.assertRaisesRegex(pilot.Hold,'AROW01_NOT_CURRENT_TWO_RU_NAMES'):
            pilot.pairs_from_current(catalog,Bridge,catalog['tlkSha256'])
        with self.assertRaisesRegex(pilot.Hold,'CURRENT_RU_TLK_SHA_DRIFT'):
            pilot.pairs_from_current(catalog,Bridge,{'dialog.tlk':'X'})

    def test_pair_current_gender_tlk_and_itm_sha_only(self):
        hashes={'dialog.tlk':'0'*64,'dialogf.tlk':'1'*64}
        catalog={'schema':'BG_EET_RU_REUSE_BGXAI_R3_V111_NAMES_RO_V1',
                 'status':'READ_ONLY_SOURCE_CATALOG',
                 'gameFilesWritten':0,'engineListenersAdded':0,
                 'tlkSha256':hashes,
                 'items':{'AROW01':{'itemTypeRaw':5,'resourceSha256':'2'*64}}}
        class Bridge:
            @staticmethod
            def dual_russian_names_source_only(cat):
                return {'gameFilesWritten':0,'engineListenersAdded':0,
                        'tlkSha256':cat['tlkSha256'],
                        'pairs':{'AROW01':{
                           'identified':{'name':'Стрела'},
                           'unidentified':{'name':'Отличная стрела'},
                           'itmOrigin':'CURRENT_GAME_BIFF','itmSha256':'2'*64}}}
        names,item=pilot.pairs_from_current(catalog,Bridge,hashes)
        self.assertEqual(names,PAIR)
        catalog['items']['AROW01']['itemTypeRaw']=20
        with self.assertRaisesRegex(pilot.Hold,'AROW01_ITEM_TYPE_OR_SHA_HOLD'):
            pilot.pairs_from_current(catalog,Bridge,hashes)

    def test_no_game_files_modified_by_default(self):
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d);(p/'work').mkdir()
            result=pilot.run_from_onefile(p/'game',p/'work','install',offline=True)
            self.assertEqual(result['status'],'V165_SAFE_STOP')
            self.assertFalse((p/'game').exists())

    def test_prepared_rollback_without_swap_finalizes_external_receipt(self):
        import json
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d);game=root/'game';work=root/'external'
            game.mkdir();work.mkdir();(game/'chitin.key').write_bytes(b'KEY')
            target=game/pilot.GAME_REL;target.parent.mkdir()
            target.write_bytes(BASE)
            backup=work/'safe';backup.mkdir()
            saved=backup/'prior.lua';saved.write_bytes(BASE)
            state=work/pilot.STATE
            second=work/'v163_state.json';second.write_text('{"phase":"INSTALLED"}')
            oldsha=pilot.digest(BASE)
            payload={'schema':pilot.SCHEMA,'phase':'PREPARED',
                     'baselineSha':oldsha,'candidateSha':'a'*64,
                     'backup':str(saved),
                     'secondStateSha':pilot.digest(second.read_bytes())}
            state.write_text(json.dumps(payload))
            class Batch:
                @staticmethod
                def _check_game_closed():return None
            class Cumulative:
                SECOND_STATE='v163_state.json'
                @staticmethod
                def _read_first_state(*_):return {},b'FIRST'
                @staticmethod
                def _verify_pins(*_):return None
            with patch.object(pilot,'EXPECTED_V163_SHA',oldsha):
                result=pilot.run('rollback',game,work,Batch,Cumulative,None,
                                 typed=pilot.APPROVE_ROLLBACK,allow_non_windows_test=True)
                self.assertEqual(result['status'],'V165_ROLLED_BACK_TO_V163_123',result)
                self.assertEqual(result['gameFilesWritten'],0)
                self.assertEqual(target.read_bytes(),BASE)
                self.assertEqual(json.loads(state.read_text())['phase'],'ROLLED_BACK')
                status=pilot.run('status',game,work,Batch,Cumulative,None)
                self.assertEqual(status['status'],'V165_ROLLED_BACK_TO_V163_123')

    def test_pins_and_typed_windows_barrier(self):
        self.assertEqual(len(pilot.V163_DISPATCH_SHA),64)
        self.assertEqual(len(pilot.V107_SOURCE_SHA),64)
        self.assertEqual(pilot.USER_SEED,'AROW01')
        self.assertEqual(len(pilot.EXPECTED_V163_SHA),64)
        self.assertNotEqual(pilot.APPROVE_INSTALL,pilot.APPROVE_ROLLBACK)
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d)
            with self.assertRaises(pilot.Hold):
                pilot._pinned(root,'x','https://invalid','f'*64,True)


if __name__=='__main__':unittest.main()
