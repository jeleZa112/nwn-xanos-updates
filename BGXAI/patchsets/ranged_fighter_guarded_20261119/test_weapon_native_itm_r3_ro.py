"""Portable source-only unit tests for R3 native resource reader."""
import base64
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zipfile
import zlib

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('r3',HERE/'BGXAI_WEAPON_NATIVE_ITM_R3_RO.py')
r3=importlib.util.module_from_spec(spec)
spec.loader.exec_module(r3)

# Base64 of actual game-archive resources, embedded for portable tests.
SW1H04 = base64.b64decode('SVRNIFYxICBNCwAAVRoAAE1JU0M1NgAALAAAABQAgNcEQFMxAAAGAAAAAAIAAAAAAFoAAA8AAAABAElTVzFIMDQAAABHU1cxSDAxAAQAAABWGgAA/////0NTVzFIMDQAAAAAAHIAAAABAKoAAAAAAAMAAQABAElTVzFIMDQAAQABAAAABQAAAAgAAQAAAAMAAQADAAAAAgADAAAAAQAyADIAAAAAAAAAAAAHAAEAFgAAABQAAAACAAAAAABkAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHAAEA+AAAABUAAAACAAAAAABkAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHAAEAYwAAABAAAAACAAAAAABkAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACSAAEAAQAAAAEAAAABAAAAAAABAFNXMUgwNAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=')
STAF01 = base64.b64decode('SVRNIFYxICDPGAAAShoAAAAAAAAsFUAALgAAABoAAAAAIFFTAAAFAAAAAAAAAAAAAGYAAAQAAAABAElTVEFGMDEAAABHU1RBRjAxAAQAAABLGgAA/////0NTVEFGMDEAAAAAAHIAAAABAKoAAAAAAAUAAQABAElTVEFGMDEAAQACAAAABAAAAAYAAQAAAAIAAAAEAAAAAQABAAAAAQAKAEYAFAAAAAAAAAAHAAEAGAAAABQAAAACAAAAAABkAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHAAEAGAAAABUAAAACAAAAAABkAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHAAEAcwAAABEAAAACAAAAAABkAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHAAEAGAAAABIAAAACAAAAAABkAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHAAEAGAAAABAAAAACAAAAAABkAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=')
SW1H04_SPL=base64.b64decode('U1BMIFYxICD//////////wAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEAAAABAGVuY2hsc3djAAAAAAAAAAAAAAAAAAD//////////wAAAAAAAAAAAAAAAHIAAAABAJoAAAAAAAAAAwACAGVuY2hsc3diBwAAAAEAAAAAAAYAAAAAAAEABAAAAAEAAQABAD4BAgAGAAAAiAAAAAAAAQAAAGQAU1cxSDA0AAAAAAAAAAAAAAAAAAAAAAAAAAAAAHAAAgABAAAAAAAAAAEAAAAAAGQAc3cxaDA0AAAAAAAAAAAAAAAAAAAAAAAAAAAAAHoAAgAAAAAAAAAAAAEAAAAAAGQATUlTQzU2XwAAAAAAAAAAAAAAAAAAAAAAAAAAAIsAAgBMNwAAAAAAAAEAAAAAAGQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA==')


def fixture_biff(entries):
    start=20+len(entries)*16
    tab=bytearray();payload=bytearray()
    for idx,typ,data in entries:
        tab+=struct.pack('<IIIHH',idx,start+len(payload),len(data),typ,0)
        payload.extend(data)
    return b'BIFFV1  '+struct.pack('<III',len(entries),0,20)+tab+payload


def fixture_key(biff_data,entries,filename='data\\weapons.bif'):
    table_offset=24;fname=filename.encode('ascii')+b'\0';name_off=table_offset+12
    res_off=name_off+len(fname)
    bif=struct.pack('<IIHH',len(biff_data),name_off,len(fname),1)
    table=b''.join(name.encode('ascii').ljust(8,b'\0')+
                   struct.pack('<HI',typ,loc) for name,typ,loc in entries)
    return b'KEY V1  '+struct.pack('<IIII',1,len(entries),table_offset,res_off)+bif+fname+table


class NativeFixture(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);(self.root/'data').mkdir();(self.root/'override').mkdir()
        self.entries=[(35,0x03ed,SW1H04),(36,0x03ee,SW1H04_SPL),
                      (37,0x03f4,b'2DA V1.0\r\n0\r\nLEVEL PIP\r\n'),
                      (38,0x03ed,STAF01)]
        self.write_bif('plain')
    def write_bif(self,kind):
        plain=fixture_biff(self.entries)
        path=self.root/'data'/'weapons.bif'
        if kind=='plain':b=plain
        elif kind=='bif':
            name=b'weapons.bif\0';z=zlib.compress(plain)
            b=b'BIF V1.0'+struct.pack('<I',len(name))+name+struct.pack('<II',len(plain),len(z))+z
        elif kind=='bifc':
            z=zlib.compress(plain)
            b=b'BIFCV1.0'+struct.pack('<I',len(plain))+struct.pack('<II',len(plain),len(z))+z
        path.write_bytes(b)
        ent=[('SW1H04',0x03ed,35),('SW1H04',0x03ee,36),('WSPATCK',0x03f4,37),('STAF01',0x03ed,38)]
        (self.root/'chitin.key').write_bytes(fixture_key(b,ent))
    def test_actual_sword_item_dice(self):
        it=r3.parse_itm(SW1H04)
        self.assertEqual((it['abilities'][0]['diceCountRaw'],it['abilities'][0]['diceSidesRaw']),(1,8))
        self.assertEqual(it['abilities'][0]['baseDamageMeanBeforeEffects'],4.5)
        self.assertEqual(it['abilities'][0]['rangeRaw'],1)
        self.assertEqual(it['abilities'][0]['speedRaw'],5)
    def test_actual_staff_item_dice_and_reach(self):
        it=r3.parse_itm(STAF01)
        self.assertEqual((it['abilities'][0]['diceCountRaw'],it['abilities'][0]['diceSidesRaw']),(1,6))
        self.assertEqual(it['abilities'][0]['rangeRaw'],2)
        self.assertEqual(it['abilities'][0]['baseDamageMeanBeforeEffects'],3.5)
    def test_actual_sword_spells_on_hit(self):
        sw=r3.parse_itm(SW1H04)
        self.assertEqual([e['opcodeRaw'] for e in sw['abilities'][0]['effects']],[146])
        self.assertEqual(sw['abilities'][0]['effects'][0]['resourceRaw'],'SW1H04')
        spl=r3.parse_spl(SW1H04_SPL)
        self.assertEqual([e['opcodeRaw'] for e in spl['abilities'][0]['effects']],[318,112,122,139])
        self.assertFalse(spl['effectSemanticsVerified'])
    def test_equipped_effects_are_retained(self):
        self.assertEqual([e['opcodeRaw'] for e in r3.parse_itm(STAF01)['equippedEffects']],[7]*5)
        self.assertEqual(len(r3.parse_itm(SW1H04)['equippedEffects']),3)
    def test_bad_itm_signature(self):
        with self.assertRaisesRegex(r3.Hold,'ITM_FORMAT'):
            r3.parse_itm(b'bad'+SW1H04[3:])
    def test_bad_itm_offset(self):
        b=bytearray(SW1H04);struct.pack_into('<I',b,0x64,999999)
        with self.assertRaisesRegex(r3.Hold,'RESOURCE_OFFSET_OUTSIDE'):r3.parse_itm(b)
    def test_bad_itm_effect_index(self):
        b=bytearray(SW1H04);struct.pack_into('<H',b,0x6e,4444)
        with self.assertRaisesRegex(r3.Hold,'RESOURCE_OFFSET_OUTSIDE'):r3.parse_itm(b)
    def test_bad_spl_truncated(self):
        with self.assertRaisesRegex(r3.Hold,'SPL_FORMAT'):r3.parse_spl(SW1H04_SPL[:50])
    def test_native_bif_resource_lookup_index_not_ordinal(self):
        src=r3.NativeSource(self.root)
        b,proof=src.get('SW1H04','.ITM')
        self.assertEqual(b,SW1H04)
        self.assertEqual(proof['resourceIndexRaw'],35)
        self.assertEqual(proof['origin'],'CURRENT_GAME_BIFF')
    def test_native_spl_lookup(self):
        src=r3.NativeSource(self.root)
        self.assertEqual(src.get('SW1H04','.SPL')[0],SW1H04_SPL)
    def test_bif_wrapper(self):
        self.write_bif('bif')
        self.assertEqual(r3.NativeSource(self.root).get('STAF01','.ITM')[0],STAF01)
    def test_bifc_wrapper(self):
        self.write_bif('bifc')
        self.assertEqual(r3.NativeSource(self.root).get('SW1H04','.ITM')[0],SW1H04)
    def test_override_precedence(self):
        p=self.root/'override'/'SW1H04.ITM'
        p.write_bytes(STAF01)
        got,proof=r3.NativeSource(self.root).get('SW1H04','.ITM')
        self.assertEqual(got,STAF01)
        self.assertEqual(proof['origin'],'CURRENT_GAME_OVERRIDE')
    def test_key_resource_not_found(self):
        with self.assertRaisesRegex(r3.Hold,'RESOURCE_NOT_IN_CHITIN_KEY'):
            r3.NativeSource(self.root).get('NOTREAL','.ITM')
    def test_key_path_escape(self):
        b=(self.root/'data'/'weapons.bif').read_bytes()
        (self.root/'chitin.key').write_bytes(fixture_key(b,[('SW1H04',0x03ed,35)],'..\\evil.bif'))
        with self.assertRaisesRegex(r3.Hold,'KEY_BIF_PATH_UNSAFE'):
            r3.NativeSource(self.root).get('SW1H04','.ITM')
    def test_key_symlink_stop(self):
        other=self.root/'z.key';other.write_bytes((self.root/'chitin.key').read_bytes())
        (self.root/'chitin.key').unlink();(self.root/'chitin.key').symlink_to(other)
        with self.assertRaisesRegex(r3.Hold,'CHITIN_KEY_UNSAFE'):r3.NativeSource(self.root)
    def test_bif_unknown(self):
        (self.root/'data'/'weapons.bif').write_bytes(b'NOTABIF!'+b'\0'*10)
        with self.assertRaisesRegex(r3.Hold,'BIF_FORMAT_UNSUPPORTED'):
            r3.NativeSource(self.root).get('SW1H04','.ITM')
    def test_bifc_corrupted_zlib(self):
        self.write_bif('bifc');p=self.root/'data'/'weapons.bif';a=bytearray(p.read_bytes());a[28]=0xff;p.write_bytes(a)
        with self.assertRaises(r3.Hold):r3.NativeSource(self.root).get('SW1H04','.ITM')
    def test_table_read_from_biff(self):
        data,proof=r3.NativeSource(self.root).get('WSPATCK','.2DA')
        self.assertTrue(data.startswith(b'2DA V1.0'))
    def test_full_audit_keeps_switch_off(self):
        r=r3.audit(r3.NativeSource(self.root),['SW1H04','STAF01'])
        self.assertEqual(r['status'],'ITM_NATIVE_ALL_ITEMS_RAW_READ')
        self.assertEqual([e['opcodeRaw'] for e in r['linkedSpells']['SW1H04']['spell']['abilities'][0]['effects']],[318,112,122,139])
        self.assertFalse(r['dispatchAuthorized']);self.assertFalse(r['aprPerSlotVerified'])
    def test_partial_audit_unknown_not_filled(self):
        r=r3.audit(r3.NativeSource(self.root),['SW1H04','BOW05','AROW01'])
        self.assertEqual(r['status'],'ITM_NATIVE_PARTIAL_HOLD')
        self.assertEqual(set(r['items']),{'SW1H04'})
        self.assertEqual({x['resource'] for x in r['missingItemsOrLinkedSpells']},{'BOW05.ITM','AROW01.ITM'})
    def test_2da_override(self):
        (self.root/'override'/'CLSWPBON.2DA').write_text('2DA V1.0\n0\nGETS_PROF_APR\nFIGHTER 1\n')
        r=r3.audit(r3.NativeSource(self.root),['SW1H04'])
        self.assertEqual(r['aprtables']['CLSWPBON']['provenance']['origin'],'CURRENT_GAME_OVERRIDE')
        self.assertTrue(r['aprtables']['CLSWPBON']['contentsParsed'])

class Tables(unittest.TestCase):
    def test_real_clswpbon_from_user_archive(self):
        # Portable miniature of real archive content; no library file dependency.
        data=b'2DA                 V1.0\n0\n GETS_PROF_APR UNARMED_DIVISOR ZERO_SKILL_THAC0\nMAGE 0 0 5\nFIGHTER 1 0 2\n'
        r=r3.parse_2da(data)
        self.assertEqual(r['rows']['FIGHTER']['GETS_PROF_APR'],'1')
        self.assertEqual(r['rows']['MAGE']['ZERO_SKILL_THAC0'],'5')
        self.assertFalse(r['semanticsAndCharacterRowVerified'])
    def test_table_negative_wspatck_preserved_not_added_to_apr(self):
        d=b'2DA V1.0\n0\n LVL1 LVL2 LVL3\nONE -1 -2 3\n'
        r=r3.parse_2da(d)
        self.assertEqual(r['rows']['ONE']['LVL2'],'-2')
    def test_duplicate_table_row_fails(self):
        with self.assertRaisesRegex(r3.Hold,'DUPLICATE_ROW'):
            r3.parse_2da(b'2DA V1.0\n0\n A\nONE 1\nONE 2\n')
    def test_unknown_2da_encoding_fails(self):
        with self.assertRaisesRegex(r3.Hold,'ENCODING'):
            r3.parse_2da(b'\xff\xfd')

class ReportInput(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.p=Path(self.tmp.name)/'report.jsonl'
    def write(self,ready=True,seq=1):
        items={'type':'SLOTS','schema':'BGXAI_WEAPON_SLOTS_RAW_R2',
               'seq':seq,'actor':139135050,'quickWeapons':[{'index':35,'resrefRaw':'SW1H04'},
                   {'index':36,'resrefRaw':'BOW05'},{'index':37,'resrefRaw':None}],
               'quivers':[{'index':12,'resrefRaw':'AROW01'}],
               'offhand':{'index':9,'resrefRaw':'SHLD03A'}}
        lines=[{'type':'SESSION','schema':'BGXAI_WEAPON_SLOTS_RAW_R2'}]
        if ready:lines.append({'type':'READY','hookRegistered':True})
        lines.append(items)
        self.p.write_text('\n'.join(map(json.dumps,lines))+'\n')
    def test_realistic_report_drives_resrefs(self):
        self.write();names,ctx=r3._read_r2(self.p)
        self.assertEqual(names,['AROW01','BOW05','SHLD03A','SW1H04'])
        self.assertEqual(ctx['lastActor'],139135050)
    def test_no_ready_fails_closed(self):
        self.write(ready=False)
        with self.assertRaisesRegex(r3.Hold,'R2_REPORT_NO_VALID_SLOTS'):
            r3._read_r2(self.p)
    def test_invalid_sequence_rejected(self):
        self.write(seq='a')
        with self.assertRaisesRegex(r3.Hold,'R2_REPORT_NO_VALID_SLOTS'):
            r3._read_r2(self.p)
    def test_symlink_report_refused(self):
        self.write();q=self.p.with_suffix('.link.jsonl');q.symlink_to(self.p)
        with self.assertRaisesRegex(r3.Hold,'R2_REPORT_MISSING_UNSAFE'):
            r3._read_r2(q)

if __name__=='__main__':unittest.main(verbosity=2)
