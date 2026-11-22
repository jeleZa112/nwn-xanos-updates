"""BGXW4 guarded source/collector OFFLINE tests. Uses no actual EET files."""
from __future__ import annotations
import importlib.util,json,tempfile,unittest,hashlib,contextlib,io
from pathlib import Path
from unittest.mock import patch

FILE=Path(__file__).with_name('BGXW2_OBSERVER_GUARDED_R4_MENU.py')
spec=importlib.util.spec_from_file_location('guarded_r4_test',FILE)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)


def session():return {'schema':mod.R4_SCHEMA,'type':'SESSION','readOnly':True}
def ready():return {'schema':mod.R4_SCHEMA,'type':'READY','hookRegistered':True}
def example(seq=1,apr=2):
 return {'schema':mod.R4_SCHEMA,'type':'ACTIVE','seq':seq,
  'actor':139135050,'partyIndex':2,'actionRaw':30,'selectedWeaponRaw':12,
  'selectedAbilityRaw':0,'presentCount':len(mod.R4_FIELDS),'missingCount':0,
  'status':'RAW_CURRENT_SELECTED_STATS_OBSERVED_NOT_COMPLETE_EFFECTS',
  'statsRaw':{key:apr if key=='m_nNumberOfAttacks' else 0 for key in mod.R4_FIELDS},
  **{k:False for k in ('allBuffsObserved','allEffectsObserved','alternateSlotAPRVerified',
   'manualOrderProven','epsQueueProven','weaponSwitchAuthorized','dispatchAuthorized')}}

class GuardedR4(unittest.TestCase):
 def test_source_exact_sha(self):
  self.assertEqual(mod.digest(mod.R4_SOURCE),mod.R4_SHA)
  mod.r4_check_source()
 def test_no_engine_actions_or_weidu_in_observer(self):
  s=mod.R4_SOURCE.read_text()
  for token in ('ClearActions(', 'SelectWeaponAbility(', 'Attack(', 'SetGlobal(', 'XEquipItem('):
   self.assertNotIn(token,s)
  self.assertIn('EEex_Action_AddSpriteStartedActionListener',s)
 def test_existing_onefile_menu_options_1_to_6_intact(self):
  text=FILE.read_text()
  self.assertIn("'1':'preflight','2':'install','3':'status','4':'rollback','5':'collect','6':'native_itm'",text)
  self.assertIn("'7':'r4_preflight','8':'r4_install'",text)
 def test_r4_typed_install_token_enforced_without_running_install(self):
  with patch.object(mod,'r4_install',side_effect=AssertionError('install happened!')):
   with patch('builtins.input',side_effect=['8','WRONG']):
    with patch.object(mod,'report') as writer:
     with contextlib.redirect_stdout(io.StringIO()):
      self.assertEqual(mod.menu(),2)
      self.assertEqual(writer.call_args.args[1],'BGXW4_SETUP_R4.json')
 def test_r4_typed_rollback_token_enforced(self):
  with patch.object(mod,'r4_rollback',side_effect=AssertionError('rollback happened!')):
   with patch('builtins.input',side_effect=['11','NO']):
    with patch.object(mod,'report') as writer:
     with contextlib.redirect_stdout(io.StringIO()):self.assertEqual(mod.menu(),2)
 def test_r4_menu_status_does_not_install(self):
  with patch.object(mod,'r4_status',return_value={'status':'BGXW4_NOT_INSTALLED'}) as st:
   with patch('builtins.input',return_value='9'):
    with patch.object(mod,'report') as writer:
     with contextlib.redirect_stdout(io.StringIO()):self.assertEqual(mod.menu(),0)
     st.assert_called_once();self.assertEqual(writer.call_args.args[1],'BGXW4_SETUP_R4.json')
 def test_last_only_preflight_when_not_r2_last(self):
  with patch.object(mod,'guard_root'),patch.object(mod,'check_processes'),patch.object(mod,'r4_assert_r2'):
   with patch.object(mod,'last',return_value='~OTHER/SETUP-OTHER.TP2~ #0 #0'):
    with self.assertRaisesRegex(ValueError,'R4_REQUIRES_R2_LAST_WEIDU'):
     mod.r4_preflight(Path('/safe'))
 def test_r4_preflight_path_collision(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t); (root/mod.R4_MODULE).parent.mkdir()
   (root/mod.R4_MODULE).write_bytes(b'collision')
   with patch.object(mod,'guard_root'),patch.object(mod,'check_processes'),patch.object(mod,'r4_assert_r2'):
    with patch.object(mod,'last',return_value='~BGXW2/SETUP-BGXW2.TP2~ #0 #0'):
     with patch.object(mod,'weidu_binary',return_value=root/'weidu'):
      with self.assertRaisesRegex(ValueError,'R4_PATH_ALREADY_EXISTS'):
       mod.r4_preflight(root)
 def test_r4_preflight_no_change_even_when_pass(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)
   with patch.object(mod,'guard_root'),patch.object(mod,'check_processes'),patch.object(mod,'r4_assert_r2'):
    with patch.object(mod,'last',return_value='~BGXW2/SETUP-BGXW2.TP2~ #0 #0'):
     with patch.object(mod,'weidu_binary',return_value=root/'weidu'):
      out=mod.r4_preflight(root)
   self.assertEqual(out['status'],'BGXW4_SOURCE_PREFLIGHT_PASS_NO_INSTALL')
   self.assertFalse(any(root.iterdir()))
 def test_backup_missing_critical_manifest_file_holds(self):
  with tempfile.TemporaryDirectory() as t:
   with patch.object(mod,'backup_root',return_value=Path(t)/'backups'):
    with self.assertRaisesRegex(ValueError,'R4_BACKUP_INPUT_INVALID'):
     mod.r4_external_backup(Path(t)/'no_game_files')
 def test_r4_guarded_install_backup_then_proof_before_native(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)/'game';root.mkdir();weidu=root/mod.WEIDU
   weidu.write_bytes(b'MZ_fake_weidu');(root/'WeiDU.log').write_text('~BGXW2/SETUP-BGXW2.TP2~ #0 #0 ~OK~\n')
   (root/mod.MODULE).parent.mkdir(exist_ok=True)
   (root/mod.MODULE).write_bytes(Path(__file__).with_name('M_BGXW2.lua').read_bytes())
   stage_event=[]
   def native(root,uninstall=False):
    assert not uninstall
    self.assertTrue((root/mod.R4_PROOF).is_file())
    proof=json.loads((root/mod.R4_PROOF).read_text())
    self.assertEqual(proof['status'],'BGXW4_INSTALL_PENDING_WEIDU')
    self.assertTrue(Path(proof['external_backup'],'SHA256.json').is_file())
    (root/mod.R4_MODULE).parent.mkdir(exist_ok=True)
    (root/mod.R4_MODULE).write_bytes(mod.R4_SOURCE.read_bytes())
    (root/'WeiDU.log').write_text('~BGXW4/SETUP-BGXW4.TP2~ #0 #0 ~OK~\n')
    stage_event.append('installed')
   with patch.object(mod,'guard_root'),patch.object(mod,'check_processes'),patch.object(mod,'r4_assert_r2'),patch.object(mod,'baseline',return_value={}):
    with patch.object(mod,'weidu_binary',return_value=weidu):
     with patch.object(mod,'last',side_effect=lambda root:(root/'WeiDU.log').read_text().strip()):
      with patch.object(mod,'r4_external_backup') as backup:
       def makebackup(root):
        folder=Path(t)/'external';folder.mkdir();(folder/'SHA256.json').write_text('{}')
        return folder
       backup.side_effect=makebackup
       with patch.object(mod,'report_dir',return_value=Path(t)/'reports'):
        with patch.object(mod,'r4_weidu',side_effect=native):
         out=mod.r4_install(root)
         self.assertEqual(out['status'],'BGXW4_PASSIVE_INSTALLED_AWAITING_RUNTIME_TEST')
         self.assertEqual(stage_event,['installed'])
 def test_r4_explicit_rollback_requires_last(self):
  with patch.object(mod,'guard_root'),patch.object(mod,'check_processes'):
   with patch.object(mod,'last',return_value='~NEW_MOD/SETUP-NEW.TP2~ #0 #0'):
    with self.assertRaisesRegex(ValueError,'R4_NOT_LAST_WEIDU'):
     mod.r4_rollback(Path('/safe'))
 def test_active_field_count_exact(self):self.assertEqual(len(mod.R4_FIELDS),68)
 def test_all_known_and_extra_weapon_fields_present(self):
  self.assertIn('m_nProficiencyDart',mod.R4_FIELDS)
  self.assertIn('m_nProficiencySling',mod.R4_FIELDS)
  self.assertIn('m_nProficiencyAxe',mod.R4_FIELDS)
  self.assertIn('m_nProficiencyCrossbow',mod.R4_FIELDS)
  self.assertIn('m_nExtraProficiency2',mod.R4_FIELDS)
  self.assertIn('m_nExtraProficiency20',mod.R4_FIELDS)
 def test_missing_extra_mod_proficiency_rejected(self):
  e=example();e['statsRaw'].pop('m_nExtraProficiency19')
  self.assertFalse(mod.r4_valid_active(e))
 def test_unknown_nonstandard_extra_field_rejected(self):
  e=example();e['statsRaw']['m_nExtraProficiency21']=0
  self.assertFalse(mod.r4_valid_active(e))
 def test_valid_active_sample(self):self.assertTrue(mod.r4_valid_active(example()))
 def test_apr7_valid_raw_not_seven_attacks_claim(self):self.assertTrue(mod.r4_valid_active(example(apr=7)))
 def test_forged_dispatch_rejected(self):
  x=example();x['dispatchAuthorized']=True;self.assertFalse(mod.r4_valid_active(x))
 def test_forged_buff_completion_rejected(self):
  x=example();x['allBuffsObserved']=True;self.assertFalse(mod.r4_valid_active(x))
 def test_invalid_apr_rejected(self):self.assertFalse(mod.r4_valid_active(example(apr=12)))
 def test_surplus_field_rejected(self):
  x=example();x['statsRaw']['invented']=45;self.assertFalse(mod.r4_valid_active(x))
 def test_missing_prof_field_rejected(self):
  x=example();x['statsRaw'].pop('m_nProficiencyShortBow');self.assertFalse(mod.r4_valid_active(x))
 def test_boolean_apr_forgery_rejected(self):self.assertFalse(mod.r4_valid_active(example(apr=True)))
 def test_direct_file_collect(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);p=root/mod.R4_LOG
   p.write_text('\n'.join(json.dumps(x) for x in (session(),ready(),example()))+'\n')
   result=mod.r4_extract_report(root)
   self.assertEqual(result['status'],'BGXW4_ACTIVE_RAW_COLLECTED_READONLY')
   self.assertEqual(result['actions'],1)
 def test_console_capture_collect_dedup(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)
   events=[session(),ready(),example(),example(),example(2,apr=7)]
   (root/'BGXAI_WEAPON_CONSOLE_20261122T100000Z.log').write_text('\n'.join('INFO: LUA: [BGXW4] '+json.dumps(v) for v in events))
   result=mod.r4_extract_report(root)
   self.assertEqual(result['actions'],2)
   raw=(root/mod.R4_LOG).read_text().splitlines()
   self.assertEqual(len(raw),4)
 def test_conflicting_duplicate_event_must_stop(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)
   (root/mod.R4_LOG).write_text('\n'.join(json.dumps(v) for v in (session(),ready(),example(),example(1,apr=7))))
   with self.assertRaisesRegex(ValueError,'R4_SEQ_CONFLICT'):
    mod.r4_extract_report(root)
 def test_no_session_holds(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);(root/mod.R4_LOG).write_text(json.dumps(example()))
   with self.assertRaisesRegex(ValueError,'R4_ACTION_MALFORMED_OR_UNAUTHORIZED'):
    mod.r4_extract_report(root)
 def test_no_actions_holds(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);(root/mod.R4_LOG).write_text(json.dumps(session())+'\n'+json.dumps(ready()))
   self.assertEqual(mod.r4_extract_report(root)['status'],'R4_CAPTURE_INCOMPLETE_HOLD')
 def test_last_session_only(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);(root/mod.R4_LOG).write_text('\n'.join(json.dumps(v) for v in (session(),ready(),example(),session(),ready(),example(1,7))))
   result=mod.r4_extract_report(root)
   self.assertEqual(result['actions'],1)
 def test_seq_gap_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);(root/mod.R4_LOG).write_text('\n'.join(json.dumps(v) for v in (session(),ready(),example(2))))
   with self.assertRaisesRegex(ValueError,'R4_SEQ_GAPS_OR_REORDER'):
    mod.r4_extract_report(root)

if __name__=='__main__':unittest.main()
