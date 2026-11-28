# -*- coding: utf-8 -*-
"""SOURCE ONLY tests for dormant V107 CItem IDENTIFIED bit-0 probe.

This exercises Lua behavior using synthetic Python userdata. It is NOT a
Windows EEex x64 runtime proof and never loads native game pointers.
"""
from pathlib import Path
import unittest
from lupa import LuaRuntime

LUA = Path(__file__).with_name('BG_EET_RU_V107_GUARDED_CALLBACK_SOURCE_ONLY.lua')

class FakeRef:
    def get(self, *args):
        return 'SW1H04'

class FakeItem:
    def __init__(self, value=1, throws=False):
        self.value=value
        self.throws=throws
        self.flag_reads=0
        self.cResRef=FakeRef()
    @property
    def m_flags(self):
        self.flag_reads+=1
        if self.throws:
            raise RuntimeError('Synthetic binding fault')
        return self.value

class IdentificationSourceTests(unittest.TestCase):
    def setUp(self):
        self.lua=LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute("EEex_IsBitSet=function(value, bit) return (value % (2 ^ (bit+1))) >= (2 ^ bit) end")
        self.lua.execute(LUA.read_text(encoding='utf-8'))
        self.state=self.lua.globals().BG_EET_RU_V107_GUARD
        self.observe=self.lua.globals().BG_EET_RU_V107_GuardedObserve
    def context(self,item):
        return self.lua.table_from({'weapon':item,'attackRoll':12,'isCritical':False})
    def all_gates(self):
        for key in ('enabled','native_abi_verified','explicit_native_read_consent',
                    'identification_probe_enabled','current_x64_item_flags_binding_verified',
                    'callback_citem_flag_lifetime_verified','explicit_identification_read_consent'):
            self.state[key]=True

    def test_default_is_inert_even_with_fake_userdata(self):
        item=FakeItem()
        self.assertIsNone(self.observe(self.context(item)))
        self.assertEqual(self.state['seen'],0)
        self.assertEqual(item.flag_reads,0)
        self.assertFalse(self.state['enabled'])
        self.assertFalse(self.state['identification_probe_enabled'])
        self.assertFalse(self.state['native_abi_verified'])
        self.assertEqual(self.lua.globals().BG_EET_RU_V107_GuardStatus()['event_count'],0)

    def test_independent_gate_prevents_native_flag_read(self):
        required=('native_abi_verified','explicit_native_read_consent',
                  'identification_probe_enabled','current_x64_item_flags_binding_verified',
                  'callback_citem_flag_lifetime_verified','explicit_identification_read_consent')
        for missing in required:
            with self.subTest(gate=missing):
                # Fresh state limits and events for each gate.
                self.state['recorded']=0
                self.state['events']=self.lua.table()
                self.all_gates()
                self.state[missing]=False
                item=FakeItem()
                self.observe(self.context(item))
                self.assertEqual(item.flag_reads,0)
                self.assertEqual(self.state['events'][1]['weapon_identification'],
                                 'IDENTIFICATION_RUNTIME_HOLD')

    def test_identified_and_unidentified_are_distinct(self):
        self.all_gates()
        item1=FakeItem(1)
        item0=FakeItem(0)
        self.observe(self.context(item1))
        self.observe(self.context(item0))
        self.assertEqual(self.state['events'][1]['weapon_identification'],'IDENTIFIED_BIT0')
        self.assertEqual(self.state['events'][2]['weapon_identification'],'UNIDENTIFIED_BIT0')
        self.assertEqual(item1.flag_reads,1)
        self.assertEqual(item0.flag_reads,1)
        self.assertEqual(self.state['events'][1]['weapon_resref'],'SW1H04')
        self.assertFalse(self.lua.globals().BG_EET_RU_V107_GuardStatus()['live_identification_verified'])
        self.assertFalse(self.lua.globals().BG_EET_RU_V107_GuardStatus()['dual_ru_name_selected'])

    def test_bit_zero_only_never_uses_header_identification(self):
        self.all_gates()
        for flags,expected in ((0,'UNIDENTIFIED_BIT0'),(1,'IDENTIFIED_BIT0'),
                               (2,'UNIDENTIFIED_BIT0'),(3,'IDENTIFIED_BIT0'),
                               (4294967294,'UNIDENTIFIED_BIT0'),(4294967295,'IDENTIFIED_BIT0')):
            with self.subTest(flags=flags):
                self.state['recorded']=0
                self.state['events']=self.lua.table()
                self.observe(self.context(FakeItem(flags)))
                self.assertEqual(self.state['events'][1]['weapon_identification'],expected)

    def test_invalid_uint32_and_binding_fault_never_guess(self):
        self.all_gates()
        for value in (None, 'true', -1, 0.5, 4294967296, float('nan'), float('inf')):
            with self.subTest(value=value):
                self.state['recorded']=0
                self.state['events']=self.lua.table()
                self.observe(self.context(FakeItem(value)))
                self.assertEqual(self.state['events'][1]['weapon_identification'],'ITEM_FLAGS_NOT_UINT32')
        self.state['recorded']=0
        self.state['events']=self.lua.table()
        self.observe(self.context(FakeItem(throws=True)))
        self.assertEqual(self.state['events'][1]['weapon_identification'],'ITEM_FLAGS_LUA_READ_ERROR')

    def test_missing_eeex_bit_helper_holds(self):
        self.all_gates()
        self.lua.globals().EEex_IsBitSet=None
        self.observe(self.context(FakeItem(1)))
        self.assertEqual(self.state['events'][1]['weapon_identification'],
                         'IDENTIFICATION_BIT_API_MISSING')

    def test_no_new_hook_or_game_mutations_and_bounded_records(self):
        code=LUA.read_text(encoding='utf-8')
        executable='\n'.join(line for line in code.splitlines() if not line.lstrip().startswith('--'))
        for forbidden in ('EEex_Sprite_AddAlterBaseWeaponDamageListener(',
                          'Infinity_DisplayString(', 'EEex_Hook', 'io.open(',
                          'os.execute(', 'XEquipItem(', 'Infinity_Set'):
            self.assertNotIn(forbidden,executable)
        self.all_gates()
        self.state['max_events']=2
        for _ in range(8):
            self.observe(self.context(FakeItem(1)))
        self.assertEqual(self.state['recorded'],2)
        self.assertEqual(self.lua.globals().BG_EET_RU_V107_GuardStatus()['event_count'],2)
        for k,v in self.state['events'][1].items():
            self.assertIn(type(v),(str,int,float,bool),f'user data retained: {k}')

    def test_dual_russian_name_selects_only_with_all_current_proof_gates(self):
        self.all_gates()
        item1=FakeItem(1)
        item0=FakeItem(0)
        pairs=self.lua.table()
        pairs['SW1H04']=self.lua.table_from({
            'current_itm_and_tlks_verified':True,
            'identified':'Проверенное опознанное имя',
            'unidentified':'Проверенное неопознанное имя'
        })
        self.state['verified_dual_pairs']=pairs
        self.observe(self.context(item1))
        self.assertEqual(self.state['events'][1]['weapon_dual_name'],
                         'DUAL_NAME_CATALOG_HOLD')
        self.assertEqual(item1.flag_reads,1)
        self.state['dual_name_catalog_verified']=True
        self.state['recorded']=0
        self.state['events']=self.lua.table()
        self.observe(self.context(FakeItem(1)))
        self.assertEqual(self.state['events'][1]['weapon_dual_name'],
                         'DUAL_NAME_CATALOG_HOLD')
        self.state['explicit_dual_name_consent']=True
        self.state['recorded']=0
        self.state['events']=self.lua.table()
        self.observe(self.context(FakeItem(1)))
        self.observe(self.context(item0))
        self.assertEqual(self.state['events'][1]['weapon_dual_name'],
                         'Проверенное опознанное имя')
        self.assertEqual(self.state['events'][2]['weapon_dual_name'],
                         'Проверенное неопознанное имя')
        self.assertEqual(item0.flag_reads,1)
        self.assertFalse(self.lua.globals().BG_EET_RU_V107_GuardStatus()['dual_ru_name_selected'])

    def test_dual_name_ref_and_current_itm_tlk_fail_closed(self):
        self.all_gates()
        self.state['dual_name_catalog_verified']=True
        self.state['explicit_dual_name_consent']=True
        item=FakeItem(1)
        self.observe(self.context(item))
        self.assertEqual(self.state['events'][1]['weapon_dual_name'],
                         'DUAL_NAME_CURRENT_ITM_TLK_HOLD')
        self.state['recorded']=0
        self.state['events']=self.lua.table()
        self.state['verified_dual_pairs']=self.lua.table_from({
            'SW1H04': self.lua.table_from({
                'current_itm_and_tlks_verified':False,
                'identified':'Неверная подмена',
                'unidentified':'Неопознанное имя',
            })
        })
        self.observe(self.context(FakeItem(1)))
        self.assertEqual(self.state['events'][1]['weapon_dual_name'],
                         'DUAL_NAME_CURRENT_ITM_TLK_HOLD')
        self.state['verified_dual_pairs']['SW1H04']['current_itm_and_tlks_verified']=True
        self.state['verified_dual_pairs']['SW1H04']['identified']='Многострочный\nввод'
        self.state['recorded']=0
        self.state['events']=self.lua.table()
        self.observe(self.context(FakeItem(1)))
        self.assertEqual(self.state['events'][1]['weapon_dual_name'],
                         'DUAL_NAME_VALUE_HOLD')
        self.state['recorded']=0
        self.state['events']=self.lua.table()
        self.observe(self.context(FakeItem(-1)))
        self.assertEqual(self.state['events'][1]['weapon_dual_name'],
                         'DUAL_NAME_IDENTIFICATION_HOLD')

if __name__ == '__main__':
    unittest.main()
