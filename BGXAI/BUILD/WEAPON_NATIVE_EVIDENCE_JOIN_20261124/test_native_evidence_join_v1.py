#!/usr/bin/env python3
"""Offline contracts for joining REAL EET WeiDU evidence to existing R27/R28.

Synthetic fixtures below are deliberate test data, NEVER mislabeled as live.
This test never reads or modifies the user's EET or installs anything.
"""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
import BGXAI_NATIVE_EVIDENCE_JOIN_V1 as mod

CAPTURE_SHA='a'*64

def fixtures():
    native={
        'schema':mod.NATIVE_SCHEMA,'status':'NATIVE_WEIDU_COMPILED_TEMP_ONLY',
        'source':{'sha256':mod.EXPECTED_BAF_SHA,'size':6763,'blocks':8,'actionCount':8},
        'compilerSha256':'b'*64,'compiledSha256':mod.EXPECTED_BCS_SHA_FROM_REAL_EET,
        'compiledSize':10550,'exitCode':0,'compilerOutputTail':'[temp\\weidu.exe] WeiDU version 25100',
        'nativeSymbolsAcceptedByCompiler':True,'watchedFilesChanged':False,
        'temporaryOutputRemoved':True,'engineBehaviorVerified':False,
        'wholeGameTreeChecked':False,'gameplayLiveVerified':False,
        'installPerformed':False,'dispatchAuthorized':False,'weaponSwitchAuthorized':False,
        'ordersSent':0,
    }
    r27={
        'schema':mod.R27_SCHEMA,
        'R27LiveStatus':'PASS_REGISTERED_AND_EMITTED_SELECTED_STATE',
        'r27ActionCallbacks':24,'r27SequencesContinuousFrom1':True,'r27ErrorsObserved':0,
        'rawLogSha256':CAPTURE_SHA,
        'comparators':{'matchedR27_R2_R4':24,'mismatches':[]},
        'gameModifiedByAnalysis':False,'allR27OrdersSentZero':True,
        'allR27LocalsWrittenZero':True,'allR27DispatchAuthorizedFalse':True,
        'allR27WeaponSwitchAuthorizedFalse':True,
        'allR27RemainingProofFlagsFalse':True,
        'selectedSlots':[{'slot':12,'observations':22},{'slot':35,'observations':2}],
    }
    r28={
        'schema':mod.R28_SCHEMA,'status':'R28_NATIVE_ITEMS_RAW_READ_AWAITING_REVIEW',
        'captureSha256':CAPTURE_SHA,
        'liveR27Evidence':{'sourceSha256':CAPTURE_SHA,'r27ConfirmedCallbacks':24,
                           'observedRawItemResrefs':['AROW01','BOW05','STAF01','SW1H04']},
        'nativeAudit':{'schema':'BGXAI_WEAPON_NATIVE_ITM_R3_READONLY',
            'status':'ITM_NATIVE_ALL_ITEMS_RAW_READ','sourceKind':'CURRENT_GAME',
            'items':{'AROW01':{},'BOW05':{},'STAF01':{},'SW1H04':{}},
            'missingItemsOrLinkedSpells':[],
            'aprPerSlotVerified':False,'currentCharacterBuffsVerified':False,
            'launcherAmmoPairVerified':False,'fullWeaponEffectsVerified':False,
            'targetImmuneOrResistantVerified':False,'manualAndEPSQueueVerified':False,
            'dispatchAuthorized':False,'weaponSwitchAuthorized':False,'gameModified':False},
        'gameModified':False,'gameplayActionOriginVerified':False,
        'manualAndEPSQueueVerified':False,'effectiveAlternateAPRVerified':False,
        'launcherAmmoPairVerified':False,'weaponSwitchAuthorized':False,
        'dispatchAuthorized':False,'ordersSent':0,
    }
    return native,r27,r28

class NativeEvidenceJoin(unittest.TestCase):
    def test_actual_evidence_shape_keeps_dispatch_off(self):
        result=mod.join(*fixtures())
        self.assertEqual(result['status'],'NATIVE_BAF_COMPILED_R27_R28_LINKED_NO_DISPATCH')
        self.assertEqual(result['nativeWeiDU']['compiledBcsSize'],10550)
        self.assertEqual(result['R27']['gameCallbacksVerified'],24)
        self.assertEqual(result['R28']['nativeItemCountVerified'],4)
        self.assertEqual(len(result['missingGates']),7)
        for field in ('installPerformed','dispatchAuthorized','weaponSwitchAuthorized'):
            self.assertIs(result[field],False)
        self.assertEqual(result['ordersSent'],0)
    def test_no_user_paths_or_raw_logs_in_output(self):
        native,r27,r28=fixtures()
        native['compilerOutputTail']='C:\\Users\\Somebody\\Temp\\weidu.exe WeiDU version 25100'
        result=json.dumps(mod.join(native,r27,r28))
        for forbidden in ('Somebody','C:\\','compilerOutputTail','rawLogSha256','selectedAprKeyRaw'):
            self.assertNotIn(forbidden,result)
    def test_utf8_bom_is_supported_without_game_data_writes(self):
        native,r27,r28=fixtures()
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'report.json'
            path.write_bytes(b'\xef\xbb\xbf'+json.dumps(native).encode())
            self.assertEqual(mod.load_json(path)['status'],'NATIVE_WEIDU_COMPILED_TEMP_ONLY')
    def test_missing_input_is_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(mod.EvidenceHold):mod.load_json(Path(tmp)/'missing.json')
    def test_bad_inputs_are_closed_matrix(self):
        cases=[
            (0,('status',),'COMPILED_FAKE'),
            (0,('source','sha256'),'0'*64),
            (0,('source','size'),6764),
            (0,('source','blocks'),7),
            (0,('source','actionCount'),9),
            (0,('nativeSymbolsAcceptedByCompiler',),False),
            (0,('exitCode',),1),
            (0,('exitCode',),True),
            (0,('watchedFilesChanged',),True),
            (0,('temporaryOutputRemoved',),False),
            (0,('compiledSha256',),'2'*64),
            (0,('compiledSize',),10549),
            (0,('compilerSha256',),'bad'),
            (0,('compilerOutputTail',),'script compiler without version'),
            (0,('engineBehaviorVerified',),True),
            (0,('wholeGameTreeChecked',),True),
            (0,('gameplayLiveVerified',),True),
            (0,('installPerformed',),True),
            (0,('dispatchAuthorized',),True),
            (0,('weaponSwitchAuthorized',),True),
            (0,('ordersSent',),1),
            (1,('R27LiveStatus',),'PASS_FAKE'),
            (1,('r27ActionCallbacks',),23),
            (1,('r27ErrorsObserved',),1),
            (1,('r27SequencesContinuousFrom1',),False),
            (1,('rawLogSha256',),'short'),
            (1,('comparators','matchedR27_R2_R4'),23),
            (1,('comparators','mismatches'),['error']),
            (1,('gameModifiedByAnalysis',),True),
            (1,('allR27OrdersSentZero',),False),
            (1,('allR27LocalsWrittenZero',),False),
            (1,('allR27DispatchAuthorizedFalse',),False),
            (1,('allR27WeaponSwitchAuthorizedFalse',),False),
            (1,('allR27RemainingProofFlagsFalse',),False),
            (1,('selectedSlots',),[]),
            (2,('status',),'R28_FAKE'),
            (2,('captureSha256',),'f'*64),
            (2,('liveR27Evidence','sourceSha256'),'e'*64),
            (2,('liveR27Evidence','r27ConfirmedCallbacks'),23),
            (2,('liveR27Evidence','observedRawItemResrefs'),['SW1H04']),
            (2,('nativeAudit','sourceKind'),'OLDER_USER_ZIP_NOT_CURRENT'),
            (2,('nativeAudit','status'),'ITM_NATIVE_PARTIAL_HOLD'),
            (2,('nativeAudit','items'),{'BOW05':{}}),
            (2,('nativeAudit','missingItemsOrLinkedSpells'),['MISSING']),
            (2,('nativeAudit','aprPerSlotVerified'),True),
            (2,('nativeAudit','targetImmuneOrResistantVerified'),True),
            (2,('nativeAudit','manualAndEPSQueueVerified'),True),
            (2,('gameModified',),True),
            (2,('ordersSent',),1),
            (2,('dispatchAuthorized',),True),
            (2,('effectiveAlternateAPRVerified',),True),
            (2,('manualAndEPSQueueVerified',),True),
        ]
        for i,(slot,path,value) in enumerate(cases,1):
            with self.subTest(i=i,case=str(path)):
                z=list(copy.deepcopy(fixtures()))
                obj=z[slot]
                for k in path[:-1]:obj=obj[k]
                obj[path[-1]]=value
                with self.assertRaises(mod.EvidenceHold):mod.join(*z)
    def test_redacted_real_result_committed_with_same_limits(self):
        proof=Path(__file__).with_name('BGXAI_NATIVE_EVIDENCE_JOIN_20261124.json')
        if proof.is_file():
            data=json.loads(proof.read_text(encoding='utf-8-sig'))
            self.assertEqual(data['status'],'NATIVE_BAF_COMPILED_R27_R28_LINKED_NO_DISPATCH')
            self.assertEqual(data['nativeWeiDU']['compiledBcsSha256'],mod.EXPECTED_BCS_SHA_FROM_REAL_EET)
            self.assertEqual(len(data['missingGates']),7)
            self.assertFalse(data['dispatchAuthorized'])
            self.assertEqual(data['ordersSent'],0)
            for private in ('C:\\\\','Drevo','\\\\Users\\\\','actorRaw','captureFileName'):
                self.assertNotIn(private,json.dumps(data))
    def test_boolean_as_zero_not_accepted(self):
        z=list(fixtures());z[2]['ordersSent']=False
        with self.assertRaises(mod.EvidenceHold):mod.join(*z)
    def test_untrusted_object_not_accepted(self):
        for bad in (None,True,[],123,'status'):
            with self.subTest(bad=bad):
                with self.assertRaises(mod.EvidenceHold):mod.join(bad,*fixtures()[1:])

if __name__=='__main__':
    unittest.main(verbosity=2)