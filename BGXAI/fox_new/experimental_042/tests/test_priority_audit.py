from pathlib import Path
import importlib.util,sys,unittest,hashlib
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('scan',ROOT/'scan_eps_bcs.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

def block(terms,acts):
    trigger=''.join('TR\n'+str(n)+' 0 0 0 0 "'+str(label)+'" "" OB\n0 0 0 0 0 0 0 0 0 0 0 0 ""OB\nTR\n' for n,label in terms)
    action=''.join('AC\n'+str(n)+'OB\n0 0 0 0 0 0 0 0 0 0 0 0 ""OB\n0 0 0 0 0 "" "" AC\n' for n in acts)
    return 'CR\nCO\n'+trigger+'CO\nRS\nRE\n100'+action+'RE\nRS\nCR\n'

class Audit(unittest.TestCase):
 def test_bcs_inventory(self):
    payload=('SC\n'+block([(16427,''),(16399,'LOCALSBDAI_ATTACK_MODE')],[134])+block([(16399,'LOCALSBGX38_GUARD')],[87])+'SC\n').encode()
    report=mod.inspect(payload)
    self.assertEqual(report['complete_blocks'],2)
    self.assertEqual(report['attack_mode_blocks'],1)
    self.assertEqual(report['guard_flag_blocks'],1)
    self.assertTrue(report['all_attack_mode_gated_by_idle'])
    self.assertEqual(report['actions']['AttackReevaluate'],1)
    self.assertEqual(report['actions']['ProtectObject'],1)
    self.assertEqual(report['sha256'],hashlib.sha256(payload).hexdigest())
 def test_invalid_bcs(self):
    for raw in (b'',b'no script',b'SC\nempty',b'SC\n'+b'x'*8000001):
        with self.assertRaises(ValueError):mod.inspect(raw)
 def test_no_autoattack_returns_unknown_idle(self):
    raw=('SC\n'+block([(16399,'LOCALSBGX38_GUARD')],[87])+'SC\n').encode()
    self.assertIsNone(mod.inspect(raw)['all_attack_mode_gated_by_idle'])
 def test_weidu_state(self):
    state=mod.weidu_state(b'~A/BGX40.TP2~ #0 #0\n~BGX41/SETUP-BGX41.TP2~ #0 #0\n')
    self.assertTrue(state['bgxai_installed']['41'])
    self.assertTrue(state['last_is_041'])
 def test_genuine_archived_eps_bcs(self):
    # ONLY if original user archive exists: preserve sample as a fixture reference, never distribute it.
    import zipfile
    f=Path('/mnt/data/BG_EET_AUDIT_02_QUESTS_AI.zip')
    if not f.is_file():self.skipTest('No historical user sample')
    with zipfile.ZipFile(f) as z:real=z.read('BDDEFAI.BCS')
    s=mod.inspect(real)
    self.assertGreater(s['complete_blocks'],250)
    self.assertGreater(s['attack_mode_blocks'],0)
    self.assertFalse(s['contains_038_guard_flag'])

if __name__=='__main__': unittest.main()
