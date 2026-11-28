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
            weidu=game/'WeiDU.log';weidu.write_bytes(b'current weidu changed')
            pin=game/'UI.MENU';pin.write_bytes(b'original pinned UI')
            gamepin={'UI.MENU':pilot.digest(pin.read_bytes())}
            dllpins={}
            for name in ('EEex.dll','LuaBindings.dll'):
                dll=game/name
                dll.write_bytes(('mock-'+name).encode('ascii'))
                dllpins[name]=pilot.digest(dll.read_bytes())
            oldlog='f'*64
            old_items={f'ITM{i:05}':{'sha256':'a'*64,'origin':'CURRENT_GAME_BIFF'}
                       for i in range(123)}
            state=work/pilot.STATE
            second=work/'v163_state.json'
            second.write_text(json.dumps({'phase':'INSTALLED','itemPins':old_items}))
            oldsha=pilot.digest(BASE)
            payload={'schema':pilot.SCHEMA,'phase':'PREPARED',
                     'baselineSha':oldsha,'candidateSha':'a'*64,
                     'backup':str(saved),
                     'weiduSha256HistoricalV162':oldlog,
                     'weiduSha256Current':pilot.digest(weidu.read_bytes()),
                     'secondStateSha':pilot.digest(second.read_bytes())}
            state.write_text(json.dumps(payload))
            class Batch:
                @staticmethod
                def _check_game_closed():return None
                @staticmethod
                def file_sha(p,limit=1000000):return pilot.digest(pathlib.Path(p).read_bytes())
            class Cumulative:
                SECOND_STATE='v163_state.json'
                @staticmethod
                def _read_first_state(*_):return {'gamePins':gamepin,'weiduSha':oldlog},b'FIRST'
                @staticmethod
                def _verify_pins(*_):raise AssertionError('must not call old historic WeiDU check')
            with patch.object(pilot,'EXPECTED_V163_SHA',oldsha), patch.object(
                    pilot,'EXPECTED_DLL',dllpins):
                result=pilot.run('rollback',game,work,Batch,Cumulative,None,
                                 typed=pilot.APPROVE_ROLLBACK,allow_non_windows_test=True)
                self.assertEqual(result['status'],'V165_ROLLED_BACK_TO_V163_123',result)
                self.assertEqual(result['gameFilesWritten'],0)
                self.assertEqual(target.read_bytes(),BASE)
                self.assertEqual(json.loads(state.read_text())['phase'],'ROLLED_BACK')
                status=pilot.run('status',game,work,Batch,Cumulative,None)
                self.assertEqual(status['status'],'V165_ROLLED_BACK_TO_V163_123')

    def test_scoped_weidu_drift_full_123_current_itm_revalidation(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d)
            (root/'core').write_bytes(b'untouched')
            (root/'WeiDU.log').write_bytes(b'new harmless downstream install log')
            pins={'core':pilot.digest((root/'core').read_bytes())}
            first={'gamePins':pins,'weiduSha':'0'*64}
            items={f'ITEM{i:04}':{'sha256':pilot.digest(b'original'),
                                'origin':'CURRENT_GAME_BIFF'} for i in range(123)}
            second={'itemPins':items}
            seen=[]
            class Batch:
                @staticmethod
                def file_sha(p,limit=1000000):return pilot.digest(pathlib.Path(p).read_bytes())
            class Cum:
                @staticmethod
                def _verify_item(resolver,ref,pin,batch):
                    raw,meta=resolver.get(ref,'.ITM')
                    if pilot.digest(raw)!=pin['sha256'] or meta['origin']!=pin['origin']:
                        raise pilot.Hold('CURRENT_GAME_ITM_SHA_OR_ORIGIN_CHANGED:'+ref)
                    seen.append(ref)
            class Resolver:
                @staticmethod
                def get(ref,ext):return b'original',{'origin':'CURRENT_GAME_BIFF'}
            p=pilot.verify_scoped_pins(root,first,second,Batch,Cum,Resolver)
            self.assertTrue(p['weiduHistoricalDrift'])
            self.assertTrue(p['all123HistoricalItemPinsRechecked'])
            self.assertEqual(p['priorItemsChecked'],123)
            self.assertEqual(len(seen),123)
            self.assertEqual(p['weiduSha256Current'],pilot.digest((root/'WeiDU.log').read_bytes()))
            (root/'WeiDU.log').write_bytes(b'changed again during approval')
            with self.assertRaisesRegex(pilot.Hold,'WEIDU_CHANGED_SINCE_V165_PREFLIGHT'):
                pilot.verify_scoped_pins(root,first,second,Batch,Cum,Resolver,
                                          expected_current_weidu=p['weiduSha256Current'])
            (root/'WeiDU.log').write_bytes(b'new harmless downstream install log')
            (root/'core').write_bytes(b'changed game resource')
            with self.assertRaisesRegex(pilot.Hold,'V162_GAME_PIN_DRIFT'):
                pilot.verify_scoped_pins(root,first,second,Batch,Cum,Resolver)
            (root/'core').write_bytes(b'untouched')
            class MutatedResolver:
                @staticmethod
                def get(ref,ext):return b'modified',{'origin':'CURRENT_GAME_BIFF'}
            with self.assertRaisesRegex(pilot.Hold,'CURRENT_GAME_ITM_SHA_OR_ORIGIN_CHANGED'):
                pilot.verify_scoped_pins(root,first,second,Batch,Cum,MutatedResolver)

    def test_scoped_weidu_drift_without_all_123_receipts_fails_closed(self):
        class FakeBatch:
            @staticmethod
            def file_sha(*args):return '0'*64
        with self.assertRaisesRegex(pilot.Hold,'V163_123_ITEM_PINS_MISSING'):
            pilot.verify_scoped_pins(pathlib.Path('/not-real'),
                {'gamePins':{'Baldur.exe':'0'*64},'weiduSha':'0'*64},
                {'itemPins':{}},FakeBatch,None)

    def test_v166_published_onefile_backend_and_manifest_exact(self):
        import json
        base=ROOT.parent/'onefile'
        cmd=(base/'BG_EET_RU_UPDATE.cmd').read_bytes()
        manifest=json.loads((base/'release.json').read_text('utf-8'))
        # Windows checkout may apply core.autocrlf. The immutable GitHub RAW
        # download pin hashes LF-normalized Git bytes, NOT checkout CRLF.
        backend_bytes=P.read_bytes().replace(b'\r\n',b'\n')
        self.assertNotIn(b'\r',backend_bytes)
        backend_sha=pilot.digest(backend_bytes)
        self.assertEqual(manifest['version'],166)
        self.assertEqual(manifest['sha256'],pilot.digest(cmd))
        self.assertEqual(len(cmd),747154)
        self.assertLessEqual(len(cmd),750000)
        self.assertEqual(manifest['v165_backend_sha256'],backend_sha)
        self.assertIn(b'SELF_VERSION = 166',cmd)
        self.assertIn(('V165_PIN=\''+backend_sha+'\'').encode('ascii'),cmd)
        self.assertIn(b'14=dual',cmd)
        self.assertIn(b'V166 AROW01:1=status 2=check 3=install 4=undo',cmd)
        self.assertIn(b'V165_ONE_ITEM_DUAL_PILOT.py',cmd)
        self.assertIn(b'ad4e7f9f8eb234aa9b8f707104355628555d43df',cmd)
        self.assertIs(manifest['default_game_writes_allowed'],False)

    def test_v167_actual_immutable_legacy_bridge_mismatch_and_verified_dual_loader(self):
        """Real published source, not a mock with the missing method invented."""
        current=(ROOT/'BG_EET_RU_ITEM_NAMES_FROM_BGXAI_R3_RO.py').read_bytes().replace(b'\r\n',b'\n')
        self.assertEqual(pilot.digest(current),pilot.V167_DUAL_BRIDGE_SHA)
        self.assertIn(b'def dual_russian_names_source_only(catalog: dict) -> dict:',current)
        legacy=current.split(b'def dual_russian_names_source_only(catalog: dict) -> dict:')[0]
        self.assertNotIn(b'def dual_russian_names_source_only',legacy)
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d)
            cached=root/'V167_DUAL_NAMES_BRIDGE_R3_RO.py'
            cached.write_bytes(legacy)
            with self.assertRaisesRegex(pilot.Hold,'V165_PINNED_CACHE_CHANGED'):
                pilot.load_pinned_dual_bridge(root,offline=True)
            cached.write_bytes(current)
            dual=pilot.load_pinned_dual_bridge(root,offline=True)
            self.assertTrue(callable(dual.dual_russian_names_source_only))
            sha=pilot.digest(b'ITM_V1_ARROW_MOCK')
            hashes={'dialog.tlk':'0'*64,'dialogf.tlk':'1'*64}
            catalog={
                'schema':'BG_EET_RU_REUSE_BGXAI_R3_V111_NAMES_RO_V1',
                'status':'READ_ONLY_SOURCE_CATALOG',
                'gameFilesWritten':0,'engineListenersAdded':0,
                'tlkSha256':hashes,
                'items':{'AROW01':{
                    'status':'NAME_OR_IDENTIFICATION_HOLD',
                    'autoDisplayName':None,
                    'itemTypeRaw':5,
                    'resourceSha256':sha,
                    'origin':'CURRENT_GAME_BIFF',
                    'unidentifiedStrref':6328,
                    'identifiedStrref':6759,
                    'unidentifiedRuByTlk':{
                        'dialog.tlk':'Отличная стрела',
                        'dialogf.tlk':'Отличная стрела'},
                    'identifiedRuByTlk':{
                        'dialog.tlk':'Стрела',
                        'dialogf.tlk':'Стрела'}}}}
            names,item=pilot.pairs_from_current(catalog,dual,hashes)
            self.assertEqual(names,PAIR)
            self.assertEqual(item['itmSha256'],sha)
            self.assertEqual(item['itmOrigin'],'CURRENT_GAME_BIFF')
            self.assertEqual(item['identificationEvidence'],'NOT_PROVEN_FOR_CURRENT_X64_EEEX')
            self.assertFalse(dual.dual_russian_names_source_only(catalog)['installAllowed'])
            # Female TLK drift: the real function must not mint a verified pair.
            catalog['items']['AROW01']['identifiedRuByTlk']['dialogf.tlk']='Стрела!подмена'
            with self.assertRaisesRegex(pilot.Hold,'AROW01_NOT_CURRENT_TWO_RU_NAMES'):
                pilot.pairs_from_current(catalog,dual,hashes)
            cached.write_bytes(current+b'!')
            with self.assertRaisesRegex(pilot.Hold,'V165_PINNED_CACHE_CHANGED'):
                pilot.load_pinned_dual_bridge(root,offline=True)

    def test_v167_real_import_contract_old_v162_vs_pr129_extractor(self):
        """Precisely the missing AttributeError from user's V166 14->2."""
        import ast
        v162=ROOT.parent/'hit-only-v160/weapon_names_onefile_dispatch.py'
        v163=ROOT.parent/'hit-only-v160/weapon_names_cumulative_onefile_dispatch.py'
        legacy=v162.read_text('utf-8')
        newer=(ROOT/'BG_EET_RU_ITEM_NAMES_FROM_BGXAI_R3_RO.py').read_text('utf-8')
        self.assertIn("COMMIT = '26a3a792af22257edf85da0877f306199d15ea43'",legacy)
        self.assertIn("'bridge': ('bg-eet-ru/weapon-identity/BG_EET_RU_ITEM_NAMES_FROM_BGXAI_R3_RO.py'",legacy)
        self.assertIn("V162_ORIGINAL_BUNDLE",v163.read_text('utf-8'))
        node=ast.parse(newer)
        self.assertIn('dual_russian_names_source_only',
                      {f.name for f in node.body if isinstance(f,ast.FunctionDef)})
        # The old source prefix matches all old bridge logic but has no
        # getter function; the installed core chain must remain untouched.
        self.assertIn("dual_bridge=load_pinned_dual_bridge(cache,offline)",
                      P.read_text('utf-8'))
        self.assertNotIn("bridge=base._module(base._pinned_source(cache,'bridge',offline),'bridge')",
                         P.read_text('utf-8'))

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
