import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import BGXWP_OBSERVER_GUARDED as c


def source(seq=1, actor=77, haste=1):
 return {'type':'ACTION','sequence':seq,'partyIndex':2,'actor':actor,'action':3,
  'aprRaw':-2,'improvedHasteRaw':haste,'weaponAbilityVerified':False,
  'actualPerSlotAPRVerified':False,'buffsExhaustivelyObserved':False,
  'manualOrderOriginVerified':False,'epsQueueVerified':False,
  'weaponSwitchAuthorized':False}

SESSION={'type':'SESSION','schema':c.SCHEMA_NAME,'readOnly':True,'noActionsIssued':True,'rawOnly':True}
READY={'type':'READY','schema':c.SCHEMA_NAME,'observerRegistered':True}

class ConsoleCollector(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.folder=Path(self.temp.name)/'reports';self.folder.mkdir()
  self.log=self.folder/'BGXAI_WEAPON_CONSOLE_20261121000000000000Z.log'
 def log_events(self,*records):
  with self.log.open('w',encoding='utf-8') as f:
   for e in records:
    f.write('Infinity: [BGXWP] '+json.dumps(e)+'\n')
 def test_direct_file_sink_without_console_log(self):
  path=self.folder/c.RAW_FILENAME
  path.write_text('\n'.join(json.dumps(e) for e in (SESSION,READY,source()))+'\n')
  out=c.collect_capture(self.folder)
  self.assertEqual(out['status'],'WEAPON_RAW_DIRECT_FILE_READY')
  self.assertEqual(out['actions'],1)
 def test_no_console_log(self):
  self.assertEqual(c.collect_capture(self.folder)['status'],'WEAPON_CONSOLE_CAPTURE_ABSENT')
 def test_valid_duplicate_two_channel(self):
  self.log_events(SESSION, SESSION, READY, READY, source(), source(), source(2), source(2))
  out=c.collect_capture(self.folder)
  self.assertEqual(out['status'],'WEAPON_RAW_CONSOLE_CAPTURE_COLLECTED')
  self.assertEqual(out['actions'],2)
  lines=[json.loads(x) for x in (self.folder/c.RAW_FILENAME).read_text().splitlines()]
  self.assertEqual([x['type'] for x in lines],['SESSION','READY','ACTION','ACTION'])
  self.assertEqual([x['sequence'] for x in lines[2:]],[1,2])
 def test_empty_session_does_not_mark_live(self):
  self.log_events(SESSION,READY)
  self.assertEqual(c.collect_capture(self.folder)['status'],'WEAPON_CONSOLE_READY_NO_PARTY_ACTIONS')
  self.assertFalse((self.folder/c.RAW_FILENAME).exists())
 def test_no_ready_does_not_mark_live(self):
  self.log_events(SESSION,source())
  self.assertEqual(c.collect_capture(self.folder)['status'],'WEAPON_CONSOLE_SESSION_OR_READY_NOT_CONFIRMED')
 def test_no_session_does_not_mark_live(self):
  self.log_events(READY,source())
  self.assertEqual(c.collect_capture(self.folder)['status'],'WEAPON_CONSOLE_SESSION_OR_READY_NOT_CONFIRMED')
 def test_new_session_resets_old_actions(self):
  self.log_events(SESSION,READY,source(),SESSION,READY,source(10))
  out=c.collect_capture(self.folder);self.assertEqual(out['actions'],1)
 def test_collision_stop(self):
  self.log_events(SESSION,READY,source(),source(1,actor=88))
  with self.assertRaisesRegex(ValueError,'CONFLICTING_CONSOLE_SEQUENCE'):
   c.collect_capture(self.folder)
 def test_bogus_dispatch_flag_rejected(self):
  e=source();e['weaponSwitchAuthorized']=True
  self.log_events(SESSION,READY,e)
  self.assertEqual(c.collect_capture(self.folder)['status'],'WEAPON_CONSOLE_READY_NO_PARTY_ACTIONS')
 def test_report_existing_preserved(self):
  self.log_events(SESSION,READY,source())
  raw=self.folder/c.RAW_FILENAME;raw.write_text('ORIGINAL')
  out=c.collect_capture(self.folder);self.assertEqual(out['status'],'WEAPON_RAW_DIRECT_PRESERVED_CONSOLE_ALSO_SEEN')
  self.assertEqual(raw.read_text(),'ORIGINAL')
 def test_log_oversize_bounded(self):
  self.log.write_bytes(b'x'*(c.MAX_LOG_BYTES+1))
  self.assertEqual(c.collect_capture(self.folder)['status'],'WEAPON_CONSOLE_CAPTURE_EMPTY_OR_OVERSIZED')
 def test_symlink_log_not_followed(self):
  target=self.folder/'secret.txt';target.write_text('PRIVATE')
  self.log.symlink_to(target)
  self.assertEqual(c.collect_capture(self.folder)['status'],'WEAPON_CONSOLE_CAPTURE_ABSENT')
 def test_symlink_report_not_followed(self):
  self.log_events(SESSION,READY,source());dest=self.folder/c.RAW_FILENAME
  dest.symlink_to(self.folder/'secret.txt')
  with self.assertRaisesRegex(ValueError,'RAW_REPORT_SYMLINK'):c.collect_capture(self.folder)
 def test_malformed_ignored(self):
  self.log.write_text('[BGXWP] THIS IS NOT JSON\n[BGXWP] '+json.dumps(SESSION)+'\n[BGXWP] '+json.dumps(READY)+'\n[BGXWP] '+json.dumps(source())+'\n')
  out=c.collect_capture(self.folder);self.assertEqual(out['actions'],1)
 def test_false_not_integer(self):
  e=source();e['sequence']=True
  self.log_events(SESSION,READY,e)
  self.assertEqual(c.collect_capture(self.folder)['status'],'WEAPON_CONSOLE_READY_NO_PARTY_ACTIONS')

class CaptureLaunch(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.root=Path(self.temp.name)/'game';self.root.mkdir()
  self.out=Path(self.temp.name)/'report'
  (self.root/'InfinityLoader.exe').write_bytes(b'MZ'+b'APP')
 def test_launch_normal_loader_redirect(self):
  with mock.patch.object(c.subprocess,'Popen',return_value=mock.Mock(pid=123)) as popen:
   result=c.launch_capture(self.root,self.out)
  self.assertEqual(result['status'],'WEAPON_CONSOLE_CAPTURE_LAUNCHED_UNVERIFIED')
  self.assertEqual(result['pid'],123)
  self.assertEqual(len(list(self.out.glob('BGXAI_WEAPON_CONSOLE_*.log'))),1)
  self.assertEqual(popen.call_args.kwargs['cwd'],self.root)
 def test_bad_launcher_refused(self):
  (self.root/'InfinityLoader.exe').write_bytes(b'NOTPE')
  with self.assertRaisesRegex(ValueError,'PE_HEADER'):c.launch_capture(self.root,self.out)
 def test_launch_failure_stop(self):
  with mock.patch.object(c.subprocess,'Popen',side_effect=OSError('failed')):
   with self.assertRaisesRegex(ValueError,'CAPTURE_LAUNCH_FAILED'):
    c.launch_capture(self.root,self.out)

if __name__=='__main__':unittest.main(verbosity=2)
