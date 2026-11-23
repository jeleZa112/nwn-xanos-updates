"""R25 synthetic tests; no real user logs in the repo."""
import json
import unittest
from BGXAI_R25_CAPTURE_SEGMENT_RO import inspect

R2 = 'BGXAI_WEAPON_SLOTS_RAW_R2'
R4 = 'BGXAI_WEAPON_ACTIVE_R4'

def event(schema, typ, **extra):
    return json.dumps({'schema':schema,'type':typ,**extra},separators=(',',':'))

def r2():
    return [event(R2,'SESSION',readOnly=True,utc='UNKNOWN'),
            event(R2,'READY',hookRegistered=True),
            event(R2,'SLOTS',seq=1,actor=100,switchAuthorized=False)]

def r4():
    return [event(R4,'SESSION',readOnly=True),
            event(R4,'READY',hookRegistered=True),
            event(R4,'ACTIVE',seq=1,actor=100,weaponSwitchAuthorized=False,dispatchAuthorized=False)]

def console(lines,channel='LUA',tag='BGXW2'):
    return '\n'.join(f'INFO: {channel}: [{tag}] {line}' for line in lines)+'\n'

class SourceOnlySessions(unittest.TestCase):
    def ok(self, res):
        self.assertEqual(res['status'],'OFFLINE_LOG_SEGMENTS_VERIFIED_NO_RUNTIME_AUTH',res)
        self.assertFalse(res['dispatchAuthorized'])
        self.assertFalse(res['sessionIdEngineAuthenticated'])
        self.assertEqual(res['ordersSent'],0)
    def hold(self, res):
        self.assertEqual(res['status'],'HOLD_UNTRUSTED_OR_AMBIGUOUS_CAPTURE',res)
        self.assertFalse(res['weaponSwitchAuthorized'])
    def test_r2_jsonl(self):
        x=inspect(('\n'.join(r2())+'\n').encode(),source_type='r2-jsonl')
        self.ok(x);self.assertEqual(x['recordsBySource'],{'BGXW2':1})
    def test_r4_jsonl(self):
        x=inspect(('\n'.join(r4())+'\n').encode(),source_type='r4-jsonl')
        self.ok(x);self.assertEqual(x['recordsBySource'],{'BGXW4':1})
    def test_mirror_exact(self):
        inp=''.join(f'INFO: LUA: [BGXW2] {line}\nINFO: LPRINT: [BGXW2] {line}\n' for line in r2())
        x=inspect(inp.encode(),source_type='console');self.ok(x)
        self.assertEqual(x['mirroredPairsRemoved'],3)
        self.assertEqual(x['normalizedEventCount'],3)
    def test_mixed_channels_and_modules(self):
        lines=''.join(f'INFO: LUA: [BGXW2] {l}\nINFO: LPRINT: [BGXW2] {l}\n' for l in r2())
        lines+=console(r4(),tag='BGXW4')
        x=inspect(lines.encode(),source_type='console');self.ok(x)
        self.assertEqual(x['recordsBySource'],{'BGXW2':1,'BGXW4':1})
    def test_unmatched_second_ready_holds(self):
        x=inspect(('\n'.join(r2()[:2]+r2()[1:])+'\n').encode(),source_type='r2-jsonl')
        self.hold(x)
    def test_unmatched_duplicate_seq_holds(self):
        x=inspect(('\n'.join(r2()+r2()[-1:])+'\n').encode(),source_type='r2-jsonl')
        self.hold(x)
    def test_second_session_before_ready_holds(self):
        x=inspect(('\n'.join([r2()[0],r2()[0]]+r2()[1:])+'\n').encode(),source_type='r2-jsonl')
        self.hold(x)
    def test_unsupported_format_holds(self):
        self.hold(inspect(b'{}',source_type='game-live'))
    def test_bad_json_holds(self):
        self.hold(inspect(b'{bad json}\n',source_type='r2-jsonl'))
    def test_utf8_holds(self):
        self.hold(inspect(b'\xff\xff',source_type='r2-jsonl'))
    def test_tagged_malformed_console_holds(self):
        self.hold(inspect(b'INFO: LUA: [BGXW2] incomplete\n',source_type='console'))
    def test_other_console_lines_ignored(self):
        s='INFO: unrelated text\n'+console(r2())
        self.ok(inspect(s.encode(),source_type='console'))
    def test_wrong_permissions_holds(self):
        s=r2();s[-1]=event(R2,'SLOTS',seq=1,actor=100,switchAuthorized=True)
        self.hold(inspect(('\n'.join(s)+'\n').encode(),source_type='r2-jsonl'))
    def test_nonadjacent_mirror_holds(self):
        s=r2()
        payload=''.join(f'INFO: LUA: [BGXW2] {l}\nINFO: unrelated\nINFO: LPRINT: [BGXW2] {l}\n' for l in s)
        self.hold(inspect(payload.encode(),source_type='console'))
    def test_conflicting_mirror_holds(self):
        s=r2()
        payload=''.join(f'INFO: LUA: [BGXW2] {l}\nINFO: LPRINT: [BGXW2] {l}\n' for l in s[:2])
        payload+=f'INFO: LUA: [BGXW2] {s[2]}\nINFO: LPRINT: [BGXW2] '+event(R2,'SLOTS',seq=1,actor=100,switchAuthorized=False,selectedWeaponRaw=35)+'\n'
        self.hold(inspect(payload.encode(),source_type='console'))
    def test_tokens_change_with_file_not_clock(self):
        s='\n'.join(r2())+'\n'
        a=inspect(s.encode(),source_type='r2-jsonl')
        b=inspect(s.replace('\"hookRegistered\":true}', '\"hookRegistered\":true,\"source\":\"TEST\"}').encode(),source_type='r2-jsonl')
        self.ok(a);self.ok(b)
        self.assertNotEqual(a['segments'][0]['offlineCaptureToken'],b['segments'][0]['offlineCaptureToken'])
        self.assertEqual(a['segments'][0]['offlineCaptureToken'],inspect(s.encode(),source_type='r2-jsonl')['segments'][0]['offlineCaptureToken'])
    def test_multiactor_join_holds(self):
        s=r2()+[event(R2,'SLOTS',seq=2,actor=200,switchAuthorized=False)]
        self.hold(inspect(('\n'.join(s)+'\n').encode(),source_type='r2-jsonl'))
    def test_cross_schema_event_holds(self):
        s=r2()[:-1]+[event(R4,'SLOTS',seq=1,actor=100,switchAuthorized=False)]
        self.hold(inspect(('\n'.join(s)+'\n').encode(),source_type='r2-jsonl'))
    def test_file_not_authorized_to_be_session_source(self):
        x=inspect(('\n'.join(r2())+'\n').encode(),source_type='r2-jsonl')
        self.ok(x)
        self.assertFalse(x['manualEpsQueueVerified'])
        self.assertFalse(x['sessionIdEngineAuthenticated'])

if __name__=='__main__':unittest.main()
