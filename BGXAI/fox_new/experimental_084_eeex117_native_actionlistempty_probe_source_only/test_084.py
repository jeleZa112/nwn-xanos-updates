import pathlib, unittest, json, hashlib
P=pathlib.Path(__file__).parent
SOURCE=(P/'BGXAI084_NATIVE_QUEUE_PROBE.lua').read_text(encoding='utf-8')
class SourceOnlySafety(unittest.TestCase):
    def test_trigger_literal(self):
        self.assertIn("local TRIGGER='ActionListEmpty()'",SOURCE)
    def test_engine_entry_point_only_explicit(self):
        self.assertIn('function M.sample_from_eeex(sprite)',SOURCE)
        self.assertIn("rawget(_G,'EEex_Trigger_EvalConditionalStringAsAIBase')",SOURCE)
    def test_no_listener_registration(self):
        self.assertNotIn('EEex_Action_AddSpriteStartedActionListener(',SOURCE)
        self.assertNotIn('EEex_Action_AddSpriteStartedNextActionListener(',SOURCE)
    def test_no_engine_orders(self):
        for token in ('virtual_InsertAction(', 'virtual_ExecuteAction(', 'EEex_Action_QueueResponseStringOnAIBase(', 'ActionOverride(', 'ClearAllActions('):
            self.assertNotIn(token,SOURCE)
    def test_no_globals_writes(self):
        self.assertNotIn('SetGlobal(',SOURCE)
        self.assertNotIn('SetGlobalTimer(',SOURCE)
    def test_never_authorize(self):
        self.assertIn('safe_to_dispatch=false',SOURCE)
        self.assertNotIn('safe_to_dispatch=true',SOURCE)
    def test_queue_sample_not_verification(self):
        self.assertIn('queue_empty_sample=answer',SOURCE)
        self.assertIn('queue_empty_verified=false',SOURCE)
        self.assertNotIn('queue_empty_verified=true',SOURCE)
    def test_no_game_install(self):
        for name in ('INSTALL_BGXAI_084','WeiDU','override\\','--out'):
            self.assertNotIn(name,SOURCE)
    def test_eeex_sha_evidence(self):
        d=json.loads((P/'evidence_084.json').read_text(encoding='utf-8'))
        self.assertEqual(d['upstream']['EEex_Trigger.lua']['git_blob_sha'],'80da96ed5dc7cbcaa726631a3542ecafa533ec6f')
        self.assertEqual(d['upstream']['EEex_Action.lua']['git_blob_sha'],'e7543274ed066b5abe3c58262105212f208d1595')
    def test_install_status(self):
        self.assertIn('installed=false',SOURCE)
    def test_manifest_hashes(self):
        m=json.loads((P/'manifest_sha256.json').read_text(encoding='utf-8'))
        for fn,expected in m['files'].items():
            self.assertEqual(hashlib.sha256((P/fn).read_bytes()).hexdigest(),expected,fn)
if __name__=='__main__':unittest.main()
