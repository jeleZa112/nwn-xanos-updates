import copy, json, os, unittest
from pathlib import Path
from BGXAI_R28_EFFECT_GATES_RO import evaluate, Hold, read
DATA=json.loads(Path(__file__).with_name('R28_SANITIZED_SYNTHETIC_FIXTURE.json').read_text(encoding='utf-8'))
class TestGates(unittest.TestCase):
 def test_real(self):
  o=evaluate(DATA);self.assertEqual(o['actualInstalledItemCount'],4);self.assertEqual(o['r27Callbacks'],24)
  self.assertFalse(o['dispatchAuthorized']);self.assertFalse(o['mayCompareEffectiveDps'])
  b=next(x for x in o['observations'] if x['resource']=='BOW05')
  self.assertEqual(b['aprEffectOverridesRaw'][0]['typeRaw'],1)
  s=next(x for x in o['observations'] if x['resource']=='SW1H04')
  self.assertEqual(s['linkedItemMutationOpcodesRaw'],[112,122])
 def fail(self,change):
  d=copy.deepcopy(DATA);change(d)
  with self.assertRaises(Hold):evaluate(d)
 def test_bad_status(self):self.fail(lambda d:d.update(status='PASS_SWITCH'))
 def test_capture_hash(self):self.fail(lambda d:d.update(captureSha256='b'*64))
 def test_missing_event(self):self.fail(lambda d:d['liveR27Evidence']['samplesSelectedOnly'].pop())
 def test_wrong_seq(self):self.fail(lambda d:d['liveR27Evidence']['samplesSelectedOnly'][1].update(sequence=100))
 def test_unknown_item(self):self.fail(lambda d:d['nativeAudit']['items'].pop('BOW05'))
 def test_not_current(self):self.fail(lambda d:d['nativeAudit'].update(sourceKind='ARCHIVE'))
 def test_missing_resource(self):self.fail(lambda d:d['nativeAudit'].update(missingItemsOrLinkedSpells=['x']))
 def test_permission_mutation(self):self.fail(lambda d:d.update(weaponSwitchAuthorized=True))
 def test_wei_du_mutation(self):self.fail(lambda d:d.update(gameModified=True))
 def test_unverified_provenance(self):self.fail(lambda d:d['nativeAudit']['items']['SW1H04']['provenance'].update(origin='UNKNOWN'))
 def test_missing_link(self):self.fail(lambda d:d['nativeAudit']['linkedSpells'].pop('SW1H04'))
 def test_apr_table_claim(self):self.fail(lambda d:d['nativeAudit']['aprtables']['WSPATCK']['table'].update(semanticsAndCharacterRowVerified=True))
 def test_unknown_queue_claim(self):self.fail(lambda d:d.update(manualAndEPSQueueVerified=True))
 def test_ability_effect_corruption(self):self.fail(lambda d:d['nativeAudit']['items']['SW1H04']['item']['abilities'][0].update(effects='???'))
 def test_local_provenance(self):
  out,sha=read(Path(__file__).with_name('R28_SANITIZED_SYNTHETIC_FIXTURE.json'))
  self.assertEqual(len(sha),64);self.assertEqual(out['observations'][0]['resource'],'AROW01')
 def test_private_real_if_available(self):
  path=os.environ.get('BGXAI_R28_REAL_REPORT')
  if not path:self.skipTest('private report not uploaded to CI')
  out,sha=read(Path(path));self.assertEqual(out['r27Callbacks'],24);self.assertEqual(out['actualInstalledItemCount'],4)
if __name__=='__main__':unittest.main(verbosity=2)
