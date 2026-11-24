"""Adversarial mock tests for the real Windows-only read-only inventory adapter.

This does not pretend to test ReadProcessMemory itself. The CI selftest calls
real kernel32 APIs independently on a Windows GitHub runner.
"""
from __future__ import annotations
import random, unittest, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import v133_live_hit_inventory_ro as W
BASE=0x140000000

class FakeMemory:
    def __init__(self):
        self.mem={};self.calls=0;self.fail_on=None;self.flip=None
        for r,b in W.EXPECTED.values():self.put(BASE+r,b)
        self.put(BASE+W.FIRST,bytes.fromhex('e9'+'10000000'))
        # Seven nonzero pointer-sized entries; structural evidence only.
        self.put(BASE+W.VTABLE,b''.join((BASE+r).to_bytes(8,'little') for r in W.VTABLE_METHODS))
    def put(self,a,buf):
        for i,b in enumerate(buf):self.mem[a+i]=b
    def get(self,a,n):
        self.calls+=1
        if self.fail_on==self.calls:raise OSError('fake read failure')
        if self.flip and self.calls==self.flip[0]:
            addr=self.flip[1]
            self.mem[addr]^=1
        return bytes(self.mem.get(a+i,0) for i in range(n))

class TestWindowsReader(unittest.TestCase):
    def setUp(self):self.memory=FakeMemory()
    def audit(self):return W.audit_memory(self.memory.get,BASE)
    def held(self,x):
        self.assertEqual(x['status'],'RUNTIME_MEMORY_HOLD')
        self.assertEqual(x['game_writes'],0)
        self.assertFalse(x['native_hooks_installed'])
        self.assertFalse(x['gameplay_verified'])
    def test_good_is_still_not_gameplay(self):
        r=self.audit()
        self.assertEqual(r['status'],'LIVE_SITES_MATCH_OWNER_UNVERIFIED_RUNTIME_HOLD')
        self.assertFalse(r['firstcall_owner_verified'])
        self.assertTrue(r['memory_read_twice'])
        self.assertEqual(r['post_prologue_rva'],'0x39DA6F')
        self.assertFalse(r['firstcall_owner_verified'])
        self.assertFalse(r['native_registers_preserved_proven'])
        self.assertEqual(r['sites_checked'],7)
        self.assertEqual(len(r['checks']),9)
        self.assertTrue(all(r['checks'].values()))
    def test_each_byte_of_5_sites(self):
        tested=0
        for rva,bytestr in W.EXPECTED.values():
            for i in range(len(bytestr)):
                mem=FakeMemory();a=BASE+rva+i;mem.mem[a]^=0x1
                x=W.audit_memory(mem.get,BASE)
                self.held(x)
                tested+=1
        self.assertEqual(tested,30)
    def test_all_missing_byte_and_mismatched_len(self):
        for k,(rva,s) in W.EXPECTED.items():
            mem=FakeMemory()
            def damaged(addr,n):
                data=mem.get(addr,n)
                return data[:-1] if addr==BASE+rva else data
            self.held(W.audit_memory(damaged,BASE))
    def test_no_write_functions_in_module(self):
        s=Path(W.__file__).read_text()
        for marker in ('WriteProcessMemory(', 'VirtualProtectEx(', 'CreateRemoteThread(',
                       'DebugActiveProcess(', 'SuspendThread(', 'SetThreadContext('):
            self.assertNotIn(marker,s)
        self.assertIn('ReadProcessMemory',s)
    def test_nonatomic_jmp_snapshot(self):
        self.memory.flip=(8,BASE+W.FIRST+1)
        r=self.audit();self.held(r)
        self.assertEqual(r['reason'],'MEMORY_CHANGED_DURING_READ')
    def test_nonatomic_vtable_snapshot(self):
        self.memory.flip=(8,BASE+W.VTABLE)
        r=self.audit();self.held(r)
        self.assertEqual(r['reason'],'MEMORY_CHANGED_DURING_READ')
    def test_read_error_every_stage(self):
        for fail in range(1,15):
            mem=FakeMemory();mem.fail_on=fail
            x=W.audit_memory(mem.get,BASE)
            self.held(x)
    def test_firstcall_unpatched(self):
        self.memory.mem[BASE+W.FIRST]=0xe8
        self.held(self.audit())
    def test_firstcall_invalid_target(self):
        self.memory.put(BASE+W.FIRST,bytes.fromhex('e97525c6ff'))
        self.held(self.audit())
    def test_empty_vtable(self):
        self.memory.put(BASE+W.VTABLE,bytes(56))
        self.held(self.audit())
    def test_invalid_module_bases(self):
        for base in (0,0x10000000,0x140000001,-1,None,0x1000):
            self.held(W.audit_memory(self.memory.get,base))
    def test_bad_reader(self):
        self.held(W.audit_memory(None,BASE))
    def test_wrong_call_targets(self):
        for key in ('message','exit'):
            r,b=W.EXPECTED[key]
            mem=FakeMemory();mem.mem[BASE+r+1]^=1
            self.held(W.audit_memory(mem.get,BASE))
    def test_randomized_site_corruptions(self):
        rng=random.Random(20261124)
        keys=list(W.EXPECTED)
        for _ in range(500):
            k=keys[rng.randrange(len(keys))]
            r,raw=W.EXPECTED[k]
            offset=rng.randrange(len(raw));bit=1<<rng.randrange(8)
            mem=FakeMemory();mem.mem[BASE+r+offset]^=bit
            self.held(W.audit_memory(mem.get,BASE))
    def test_x86_or_nonwindows_holds_without_importing_win_dll(self):
        if sys.platform!='win32':
            with self.assertRaisesRegex(RuntimeError,'WINDOWS_X64_PYTHON_REQUIRED'):
                W.get_windows_api()

if __name__=='__main__':unittest.main(verbosity=2)
