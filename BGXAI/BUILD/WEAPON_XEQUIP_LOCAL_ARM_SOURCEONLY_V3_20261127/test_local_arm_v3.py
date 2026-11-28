#!/usr/bin/env python3
"""Offline negative/positive source-only tests; no installed game/runtime.

An optional --gam fixture path (or BGXAI_TEST_GAM) supplies the user's original
BALDUR.GAM but is never copied into this test package or written.
"""
from __future__ import annotations
import copy
import hashlib
import json
import os
import struct
import sys
import tempfile
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import BGXAI_XEQUIP_LOCAL_ARM_SOURCE_V3 as m
MANIFEST=json.loads((HERE/'BGXAI_REAL_JAGAN_MANIFEST_V3.json').read_text(encoding='utf-8'))


def changed(**kwargs):
    d=copy.deepcopy(MANIFEST);d.update(kwargs);return d


class SourceOnlyV3(unittest.TestCase):
    def test_exact_schema_good(self):self.assertIs(m.validate_manifest(MANIFEST),MANIFEST)
    def test_no_actorid_fake_claim(self):
        self.assertNotIn('actorId',MANIFEST)
        self.assertNotIn('actorId',m.render(MANIFEST))
    def test_one_actor_scoped_arm(self):
        s=m.render(MANIFEST)
        self.assertIn('Global("BGXW3ARM","LOCALS",1)',s)
        self.assertIn('Global("BGXW3TAG","LOCALS",',s)
        self.assertIn('Global("BGXW3TRY","LOCALS",0)',s)
        self.assertNotIn('"GLOBAL"',s)
    def test_party_pos_and_true_backpack_and_empty_quick(self):
        s=m.render(MANIFEST)
        self.assertIn('InPartySlot(Myself,1)',s)
        self.assertIn('CheckItemSlot(Myself,"STAF01",SLOT_MISC5)',s)
        self.assertIn('!HasItemSlot(Myself,SLOT_WEAPON0)',s)
    def test_does_not_arm_itself(self):
        s=m.render(MANIFEST)
        self.assertNotIn('SetGlobal("BGXW3ARM","LOCALS",1)',s)
        self.assertNotIn('SetGlobal("BGXW3TAG","LOCALS",2110908191)',s)
    def test_burn_before_exactly_one_action(self):
        s=m.render(MANIFEST)
        a=s.index('XEquipItem("STAF01",Myself,SLOT_WEAPON0,EQUIP)')
        for required in ('SetGlobal("BGXW3ARM","LOCALS",2)',
                         'SetGlobal("BGXW3TRY","LOCALS",1)',
                         'SetGlobal("BGXW3TAG","LOCALS",0)'):
            self.assertLess(s.index(required),a)
        self.assertEqual(s.count('XEquipItem('),1)
    def test_inactive_and_idle_guards(self):
        s=m.render(MANIFEST)
        for v in ('ActionListEmpty()','CombatCounter(0)','ModalState(NONE)',
                  '!StateCheck(Myself,STATE_PANIC)',
                  '!StateCheck(Myself,STATE_HELPLESS)',
                  '!GlobalTimerNotExpired("MO_SpellCast","LOCALS")'):
            self.assertIn(v,s)
    def test_dangerous_commands_absent(self):
        s=m.render(MANIFEST)
        for v in ('Stop(', 'ClearActions(', 'FillSlot(', 'Attack(',
                  'CreateItem(', 'SelectWeaponAbility(', 'MoveToObject('):
            self.assertNotIn(v,s)
    def test_deterministic_witness(self):
        self.assertEqual(m.witness(MANIFEST),2110908191)
        self.assertEqual(m.render(MANIFEST),m.render(copy.deepcopy(MANIFEST)))
    def test_witness_not_actor_proof(self):
        self.assertEqual(m.render(MANIFEST).count('BGXW3TAG'),2)
        self.assertNotIn('GetActor',m.render(MANIFEST))
    def test_script_is_single_baf_block(self):
        s=m.render(MANIFEST)
        self.assertEqual(s.count('\nIF\n'),1)
        self.assertEqual(s.count('\nTHEN\n'),1)
        self.assertEqual(s.count('RESPONSE #100'),1)
        self.assertEqual(s.count('\nEND\n'),1)
    def test_missing_and_extra_fields_hold(self):
        for k in MANIFEST:
            d=copy.deepcopy(MANIFEST);del d[k]
            with self.subTest(k=k), self.assertRaises(m.Hold):m.validate_manifest(d)
        with self.assertRaises(m.Hold):m.validate_manifest(changed(actorId=123))
        with self.assertRaises(m.Hold):m.validate_manifest(changed(userApproved=True))
    def test_wrong_party_or_pc_hold(self):
        for v in (0,-1,6,'1',True,None,2.0):
            with self.subTest(v=v),self.assertRaises(m.Hold):m.render(changed(partyIndexSnapshot=v))
    def test_wrong_actor_or_class_hold(self):
        for n in ('KHALID','JAGAN','*GCLERIX','',None):
            with self.subTest(n=n),self.assertRaises(m.Hold):m.render(changed(savedActorName=n))
        for n in (False,0,1,4,99):
            with self.subTest(n=n),self.assertRaises(m.Hold):m.render(changed(savedClassRaw=n))
    def test_source_target_lock(self):
        for src in (18,19,21,34,35,'20',20.0):
            with self.subTest(src=src),self.assertRaises(m.Hold):m.render(changed(sourceSlot=src))
        for dst in (34,36,37,38,39,'35'):
            with self.subTest(dst=dst),self.assertRaises(m.Hold):m.render(changed(targetSlot=dst))
        for rr in ('STAF02','staf01','BOW05','',None,'\n'):
            with self.subTest(rr=rr),self.assertRaises(m.Hold):m.render(changed(sourceResref=rr))
    def test_charges_flags_expiry_enforced(self):
        for flags in (-1,True,'1',2**32):
            with self.subTest(flags=flags),self.assertRaises(m.Hold):m.render(changed(sourceFlags=flags))
        for charges in (None,[],[0,0],[0,0,0,0],[0,False,0],[0,-1,0],[0,65536,0]):
            with self.subTest(charges=charges),self.assertRaises(m.Hold):m.render(changed(sourceCharges=charges))
        for expiry in (-1,True,'0',65536):
            with self.subTest(expiry=expiry),self.assertRaises(m.Hold):m.render(changed(sourceExpiry=expiry))
    def test_hash_rejected(self):
        for v in ('a'*64,'Z'*64,'z'*64,'a'*63,'',None):
            with self.subTest(v=v),self.assertRaises(m.Hold):
                m.verify_against_gam(changed(gamSha256=v),b'')
    def test_no_input_mutation(self):
        d=copy.deepcopy(MANIFEST);old=copy.deepcopy(d)
        m.render(d);self.assertEqual(d,old)
    def test_untrusted_propose_rejects_multiple_matched_candidates(self):
        d=copy.deepcopy(MANIFEST)
        from unittest.mock import patch
        c={'actor':{'partyIndexSnapshot':1,'internalNameFromGAM':'*GCLERIC','classRaw':3},
           'source':{'resref':'STAF01','slot':20,'flags':1,'charges':[0,0,0],'expiry':0},
           'target':{'slot':35,'statusInSave':'EMPTY'},
           'actorHasUniqueResrefInSavedTopLevelSlots':True}
        gam=b'foo'
        d['gamSha256']=hashlib.sha256(gam).hexdigest()
        with patch.object(m,'propose',return_value={'candidates':[c,c]}):
            with self.assertRaisesRegex(m.Hold,'HOLD_NO_UNIQUE'):
                m.verify_against_gam(d,gam)
    def test_no_item_hold(self):
        gam=b'foo';d=changed(gamSha256=hashlib.sha256(gam).hexdigest())
        from unittest.mock import patch
        with patch.object(m,'propose',return_value={'candidates':[]}):
            with self.assertRaisesRegex(m.Hold,'HOLD_NO_UNIQUE'):
                m.verify_against_gam(d,gam)
    def test_no_flags_declare_live_in_audit(self):
        gam = get_gam()
        if gam is None:self.skipTest('No real GAM available; offline logic still tested')
        audit,_=m.build(MANIFEST,gam)
        for key in ('runtimeActorIdentityVerified','currentSessionMatchesSaveVerified',
                    'classKitItmUsabilityVerified','safeActionBoundaryVerified',
                    'manualEpsOriginVerified','eetNativeActiveBafCompileVerified',
                    'legacyBcsBytePreservationVerified','installAuthorizationReceived',
                    'dispatchAuthorized','installed','gameModified'):
            self.assertIs(audit[key],False)
        self.assertEqual(audit['ordersSent'],0)
        self.assertTrue(audit['savedCandidateVerified'])
    def test_real_gam_save_untouched(self):
        gam=get_gam()
        if gam is None:self.skipTest('No real GAM available; no original bundled')
        old=hashlib.sha256(gam).hexdigest()
        self.assertEqual(old,MANIFEST['gamSha256'])
        audit,baf=m.build(MANIFEST,gam)
        self.assertEqual(hashlib.sha256(gam).hexdigest(),old)
        self.assertEqual(audit['bafSha256'],hashlib.sha256(baf.encode('ascii')).hexdigest())
        self.assertIn('STAF01',baf)
    def test_modified_real_save_hold(self):
        gam=get_gam()
        if gam is None:self.skipTest('No real GAM available')
        mutated=bytearray(gam);mutated[-1]^=1
        with self.assertRaisesRegex(m.Hold,'HOLD_GAM_SHA_MISMATCH'):
            m.build(MANIFEST,bytes(mutated))
    def test_modified_manifest_with_new_sha_but_old_candidate_hold(self):
        gam=get_gam()
        if gam is None:self.skipTest('No real GAM available')
        with self.assertRaises(m.Hold):m.build(changed(sourceCharges=[1,0,0]),gam)


class SavedBCSFromCRE(unittest.TestCase):
    """IESDP CRE V1.0 offsets: source-only script refs, never script execution."""

    @staticmethod
    def make_saved_gam(override=b'BDDEFAI', class_script=b'PRIEST1'):
        from verify_candidate_ro import SLOTS_TO_RUNTIME
        cre=bytearray(0x390)
        cre[:8]=b'CRE V1.0'
        cre[0x273]=3
        cre[0x280:0x288]=b'GCLERIC\x00'
        for off, name in ((0x248,override),(0x250,class_script),
                          (0x258,b''),(0x260,b''),(0x268,b'DEFAULT')):
            cre[off:off+8]=name.ljust(8,b'\x00')
        struct.pack_into('<III',cre,0x2b8,0x2d4,0x324,1)
        cre[0x2d4:0x324]=b'\xff'*80
        struct.pack_into('<H',cre,0x2d4+SLOTS_TO_RUNTIME.index(20)*2,0)
        cre[0x324:0x32c]=b'STAF01\x00\x00'
        struct.pack_into('<I',cre,0x324+16,1)
        gam=bytearray(0x260+len(cre))
        gam[:8]=b'GAMEV2.0'
        struct.pack_into('<II',gam,0x20,0x100,1)
        struct.pack_into('<HII',gam,0x102,1,0x260,len(cre))
        gam[0x10c:0x114]=b'*GCLERIC'
        gam[0x260:]=cre
        return bytes(gam)

    def test_saved_cre_scripts_exact_with_Jagan_STAF01(self):
        from verify_candidate_ro import propose
        original=self.make_saved_gam()
        before=hashlib.sha256(original).hexdigest()
        result=propose(original)
        self.assertEqual(len(result['candidates']),1)
        actor=result['candidates'][0]['actor']
        self.assertEqual(actor['savedCreScriptResrefs'],
                         {'0':'BDDEFAI','4':'PRIEST1','5':'',
                          '6':'','7':'DEFAULT'})
        self.assertEqual(actor['scriptAssignmentEvidence'],
                         'SAVED_CRE_V1_ONLY_NOT_LIVE_EEEX')
        self.assertEqual(result['status'],'HOLD_RUNTIME_IDENTITY_AND_GAME_PREFLIGHT')
        self.assertFalse(result['pilotExecutable'])
        self.assertFalse(result['gameModified'])
        self.assertEqual(result['ordersSent'],0)
        self.assertEqual(hashlib.sha256(original).hexdigest(),before)

    def test_saved_refs_do_not_invent_EEex_area_or_specifics(self):
        from verify_candidate_ro import read_party
        data=self.make_saved_gam(b'PRIEST1',b'BDDEFAI')
        scripts=read_party(data)[0]['savedCreScriptResrefs']
        self.assertEqual(scripts['0'],'PRIEST1')
        self.assertEqual(scripts['4'],'BDDEFAI')
        self.assertEqual(set(scripts),{'0','4','5','6','7'})
        self.assertNotIn('1',scripts)
        self.assertNotIn('2',scripts)

    def test_illegal_script_resref_HOLD_not_false_ownership(self):
        from verify_candidate_ro import propose,Hold
        with self.assertRaisesRegex(Hold,'HOLD_BAD_NAME_BYTES'):
            propose(self.make_saved_gam(override=b'BAD!.BCS'))


def get_gam():
    p=os.environ.get('BGXAI_TEST_GAM','')
    if not p:return None
    f=Path(p)
    return f.read_bytes() if f.is_file() else None


if __name__=='__main__':unittest.main(verbosity=2)